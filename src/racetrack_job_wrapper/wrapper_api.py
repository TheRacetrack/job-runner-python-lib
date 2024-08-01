import inspect
import mimetypes
import os
import threading
from dataclasses import dataclass

import time
from pathlib import Path
from typing import Any, Callable, Dict, Tuple, Union, Optional
from contextvars import ContextVar

from fastapi import Body, FastAPI, APIRouter, Request, Response, HTTPException
from fastapi.responses import RedirectResponse

from racetrack_job_wrapper.webview import setup_webview_endpoints
from racetrack_job_wrapper.concurrency import AtomicInteger
from racetrack_job_wrapper.docs import get_input_example, get_perform_docs
from racetrack_job_wrapper.entrypoint import (
    JobEntrypoint,
    list_entrypoint_parameters,
    list_auxiliary_endpoints,
    list_static_endpoints,
)
from racetrack_job_wrapper.health import setup_health_endpoints, HealthState
from racetrack_job_wrapper.metrics import (
    metric_request_duration,
    metric_request_internal_errors,
    metric_requests_started,
    metric_endpoint_requests_started,
    metric_requests_done,
    metric_last_call_timestamp,
    setup_entrypoint_metrics,
)
from racetrack_job_wrapper.response import to_json_serializable
from racetrack_job_wrapper.log.logs import get_logger
from racetrack_job_wrapper.api.asgi.fastapi import create_fastapi
from racetrack_job_wrapper.api.asgi.proxy import mount_at_base_path
from racetrack_job_wrapper.api.metrics import setup_metrics_endpoint
from racetrack_job_wrapper.auth.methods import get_racetrack_authorizations_methods

logger = get_logger(__name__)


@dataclass
class EndpointOptions:
    api: APIRouter
    entrypoint: JobEntrypoint
    jobtype_extra: Dict[str, Any]
    active_requests_counter: AtomicInteger
    concurrency_runner: Callable[[Callable[..., Any]], Any] = lambda f: f()


def create_health_app(health_state: HealthState) -> FastAPI:
    """
    Create temporary app serving liveness & readiness endpoints until the actual Job entrypoint loads up.
    """
    job_name = os.environ.get('JOB_NAME', '')
    job_version = os.environ.get('JOB_VERSION', '')
    base_url = f'/pub/job/{job_name}/{job_version}'

    fastapi_app = create_fastapi(
        title=f'Job - {job_name}',
        description='Job Module wrapped in a REST server',
        base_url=base_url,
        version=job_version,
        request_access_log=True,
        docs_url='/docs',
    )

    setup_health_endpoints(fastapi_app, health_state, job_name)

    return mount_at_base_path(fastapi_app, '/pub/job/{job_name}/{version}', '/pub/fatman/{job_name}/{version}')


def create_api_app(
    entrypoint: JobEntrypoint,
    health_state: HealthState,
    manifest_dict: Dict[str, Any] = {},
) -> FastAPI:
    """Create FastAPI app and register all endpoints without running a server"""
    job_name = os.environ.get('JOB_NAME', '')
    job_version = os.environ.get('JOB_VERSION', '')
    base_url = f'/pub/job/{job_name}/{job_version}'
    jobtype_extra: Dict[str, Any] = manifest_dict.get('jobtype_extra') or {}
    home_page = jobtype_extra.get('home_page') or '/docs'

    fastapi_app = create_fastapi(
        title=f'Job - {job_name}',
        description='Job Module wrapped in a REST server',
        base_url=base_url,
        version=job_version,
        authorizations=get_racetrack_authorizations_methods(),
        request_access_log=True,
        response_access_log=True,
        docs_url='/docs',
    )

    setup_health_endpoints(fastapi_app, health_state, job_name)
    setup_entrypoint_metrics(entrypoint)
    setup_metrics_endpoint(fastapi_app)

    api_router = APIRouter(tags=['API'])
    options = EndpointOptions(
        api=api_router,
        entrypoint=entrypoint,
        jobtype_extra=jobtype_extra,
        active_requests_counter=AtomicInteger(0),
    )
    options.concurrency_runner = make_concurrency_runner(options)
    _setup_api_endpoints(api_router, entrypoint, fastapi_app, base_url, options)
    _setup_request_context(entrypoint, fastapi_app)
    fastapi_app.include_router(api_router, prefix="/api/v1")

    @fastapi_app.get('/')
    def _root_endpoint():
        return RedirectResponse(f"{base_url}{home_page}")

    return mount_at_base_path(fastapi_app, '/pub/job/{job_name}/{version}', '/pub/fatman/{job_name}/{version}')


def _setup_api_endpoints(
    api: APIRouter,
    entrypoint: JobEntrypoint,
    fastapi_app: FastAPI,
    base_url: str,
    options: EndpointOptions,
):
    _setup_perform_endpoint(options)
    _setup_auxiliary_endpoints(options)
    _setup_static_endpoints(api, entrypoint)
    setup_webview_endpoints(entrypoint, base_url, fastapi_app, api)


def _setup_perform_endpoint(options: EndpointOptions):
    example_input = get_input_example(options.entrypoint, endpoint='/perform')
    endpoint_path = '/perform'
    summary = "Call main action"
    description = "Call main action"
    perform_docs = get_perform_docs(options.entrypoint)
    if perform_docs:
        description = f"Call main action: {perform_docs}"

    @options.api.post(
        '/perform',
        summary=summary,
        description=description,
    )
    def _perform_endpoint(payload: Dict[str, Any] = Body(default=example_input)) -> Any:
        """Call main action"""
        if not hasattr(options.entrypoint, 'perform'):
            raise ValueError("entrypoint doesn't have 'perform' method implemented")
        endpoint_method = options.entrypoint.perform
        return _call_job_endpoint(endpoint_method, endpoint_path, payload, options)

    @options.api.get('/parameters')
    def _get_parameters():
        """Return required arguments & optional parameters that model accepts"""
        return list_entrypoint_parameters(options.entrypoint)


def _setup_auxiliary_endpoints(options: EndpointOptions):
    """Configure custom auxiliary endpoints defined by user in an entypoint"""
    auxiliary_endpoints = list_auxiliary_endpoints(options.entrypoint)
    for endpoint_path in sorted(auxiliary_endpoints.keys()):

        endpoint_method: Callable = auxiliary_endpoints[endpoint_path]
        endpoint_name = endpoint_path.replace('/', '_')
        example_input = get_input_example(options.entrypoint, endpoint=endpoint_path)
        if not endpoint_path.startswith('/'):
            endpoint_path = '/' + endpoint_path

        # keep these variables inside closure as next loop cycle will overwrite it
        def _add_endpoint(_endpoint_path: str, _endpoint_method: Callable):
            summary = f"Call auxiliary endpoint: {_endpoint_path}"
            description = "Call auxiliary endpoint"
            endpoint_docs = inspect.getdoc(_endpoint_method)
            if endpoint_docs:
                description = f"Call auxiliary endpoint: {endpoint_docs}"

            @options.api.post(
                _endpoint_path,
                operation_id=f'auxiliary_endpoint_{endpoint_name}',
                summary=summary,
                description=description,
            )
            def _auxiliary_endpoint(payload: Dict[str, Any] = Body(default=example_input)) -> Any:
                return _call_job_endpoint(_endpoint_method, _endpoint_path, payload, options)

        _add_endpoint(endpoint_path, endpoint_method)
        logger.info(f'configured auxiliary endpoint: {endpoint_path}')


def _call_job_endpoint(
    endpoint_method: Callable,
    endpoint_path: str,
    payload: Dict[str, Any],
    options: EndpointOptions,
) -> Any:
    metric_requests_started.inc()
    metric_endpoint_requests_started.labels(endpoint=endpoint_path).inc()
    start_time = time.time()
    try:
        assert payload is not None, 'payload is empty'

        def _endpoint_caller() -> Any:
            return endpoint_method(**payload)

        result = options.concurrency_runner(_endpoint_caller)
        return to_json_serializable(result)

    except TypeError as e:
        metric_request_internal_errors.labels(endpoint=endpoint_path).inc()
        raise ValueError(f'failed to call a function: {e}')
    except BaseException as e:
        metric_request_internal_errors.labels(endpoint=endpoint_path).inc()
        raise e
    finally:
        metric_request_duration.labels(endpoint=endpoint_path).observe(time.time() - start_time)
        metric_requests_done.inc()
        metric_last_call_timestamp.set(time.time())


def _setup_static_endpoints(api: APIRouter, entrypoint: JobEntrypoint):
    """Configure custom static endpoints defined by user in an entypoint"""
    static_endpoints = list_static_endpoints(entrypoint)
    for endpoint_path in sorted(static_endpoints.keys()):
        static_file = static_endpoints[endpoint_path]
        _setup_static_endpoint(api, entrypoint, endpoint_path, static_file)


def _setup_static_endpoint(
    api: APIRouter,
    entrypoint: JobEntrypoint,
    endpoint_path: str,
    static_file: Union[Tuple, str],
):
    """
    Configure custom static endpoints defined by user in an entypoint
    :param api: FastAPI API namespace
    :param entrypoint: Job entrypoint instance
    :param endpoint_path: endpoint path, eg. /ui/index
    :param static_file: static file path or tuple of (path, mimetype)
    """
    # in case of directory, serve subfiles recursively
    if isinstance(static_file, str):
        static_file_path = Path(static_file)
        if static_file_path.is_dir():
            for subfile in static_file_path.iterdir():
                endpoint_subpath = endpoint_path + '/' + subfile.name
                _setup_static_endpoint(api, entrypoint, endpoint_subpath, str(subfile))
            return

    filepath, mimetype = _get_static_file_with_mimetype(static_file)

    if not endpoint_path.startswith('/'):
        endpoint_path = '/' + endpoint_path

    @api.get(endpoint_path, operation_id=f'static_endpoint_{endpoint_path}')
    def _static_endpoint():
        """Fetch static file"""
        content = filepath.read_bytes()
        return Response(content=content, media_type=mimetype)

    logger.info(f'configured static endpoint: {endpoint_path} -> {filepath} ({mimetype})')


def _get_static_file_with_mimetype(static_file: Union[Tuple, str]) -> Tuple[Path, str]:
    if isinstance(static_file, tuple):
        filename = static_file[0]
        mimetype = static_file[1]
    elif isinstance(static_file, str):
        filename = static_file
        mimetype = None
    else:
        raise RuntimeError('static endpoint value should be string or tuple')
    path = Path(filename)
    assert path.is_file(), f"static file doesn't exist: {filename}"
    if not mimetype:
        mimetype, encoding = mimetypes.guess_type(path, strict=False)
        if not mimetype:
            mimetype = 'text/plain'
            logger.warning(f"Can't detect mimetype of static file {filename}, applying default {mimetype}")
    return path, mimetype


def _setup_request_context(entrypoint: JobEntrypoint, fastapi_app: FastAPI):
    request_context: ContextVar[Request] = ContextVar('request_context')
    setattr(entrypoint, 'request_context', request_context)

    request_extra: ContextVar[Dict[str, Any]] = ContextVar('request_extra')
    setattr(entrypoint, 'request_extra', request_extra)

    @fastapi_app.middleware('http')
    async def request_context_middleware(request: Request, call_next) -> Response:
        request_context_token = request_context.set(request)
        request_extra_token = request_extra.set({})
        response = await call_next(request)
        request_context.reset(request_context_token)
        request_extra.reset(request_extra_token)
        return response


def jobtype_extra_int(jobtype_extra: Dict[str, Any], field_name: str) -> Optional[int]:
    str_val = jobtype_extra.get(field_name)
    if str_val is None:
        return None
    assert str(str_val).isdigit(), f'Expected integer in {field_name}, but got: {str_val}'
    return int(str_val)


def make_concurrency_runner(options: EndpointOptions) -> Callable[[Callable[..., Any]], Any]:
    max_concurrency: Optional[int] = jobtype_extra_int(options.jobtype_extra, 'max_concurrency')
    if not max_concurrency:
        return lambda f: f()
    max_concurrency_queue: Optional[int] = jobtype_extra_int(options.jobtype_extra, 'max_concurrency_queue')
    concurrency_semaphore = threading.BoundedSemaphore(value=max_concurrency)

    def concurrency_wrapper(f: Callable[..., Any]) -> Any:
        queue_size: int = options.active_requests_counter.value - max_concurrency
        if max_concurrency_queue is not None and queue_size >= max_concurrency_queue:
            # Too Many Requests
            raise HTTPException(429, f'too many requests waiting in a queue. Job is set to process {max_concurrency}'
                                     f' requests concurrently with a queue of max size {max_concurrency_queue}')
        try:
            options.active_requests_counter.inc()
            with concurrency_semaphore:
                return f()
        finally:
            options.active_requests_counter.dec()

    return concurrency_wrapper
