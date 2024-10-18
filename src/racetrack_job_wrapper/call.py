import os
from typing import Dict, Any, Optional, Union

import httpx
from fastapi import Request

from racetrack_job_wrapper.log.logs import get_logger
from racetrack_job_wrapper.entrypoint import JobEntrypoint
from racetrack_job_wrapper.recordkeeper import set_rk_headers

logger = get_logger(__name__)


def call_job(
    entrypoint: JobEntrypoint,
    job_name: str,
    path: str = '/api/v1/perform',
    payload: Optional[Dict] = None,
    version: str = 'latest',
    method: str = 'POST',
    timeout: Optional[float] = 10,
) -> Any:
    """
    Call another job's endpoint.
    :param entrypoint: entrypoint object of the job that calls another job
    :param job_name: name of the job to call
    :param path: endpoint path to call, default is /api/v1/perform
    :param payload: payload to send: dictionary with parameters or None
    :param version: version of the job to call. Use exact version or alias, like "latest"
    :param method: HTTP method: GET, POST, PUT, DELETE, etc.
    :param timeout: seconds of network inactivity that raises a timeout exception. None disables all timeouts
    :return: result object returned by the called job
    """
    src_job = os.environ.get('JOB_NAME')
    try:
        with httpx.Client(timeout=timeout) as client:
            request: httpx.Request = _prepare_request(client, entrypoint, job_name, path, payload, version, method)
            response = client.send(request)
        response.raise_for_status()
        return response.json()

    except httpx.HTTPStatusError as e:
        raise RuntimeError(f'failed to call job "{job_name} {version}" by {src_job}: {e}: {e.response.text}') from e
    except BaseException as e:
        raise RuntimeError(f'failed to call job "{job_name} {version}" by {src_job}: {e}') from e


async def call_job_coroutine(
    entrypoint: JobEntrypoint,
    job_name: str,
    path: str = '/api/v1/perform',
    payload: Optional[Dict] = None,
    version: str = 'latest',
    method: str = 'POST',
    timeout: Optional[float] = 10,
) -> Any:
    """
    Call another job's endpoint in async coroutine context.
    :param entrypoint: entrypoint object of the job that calls another job
    :param job_name: name of the job to call
    :param path: endpoint path to call, default is /api/v1/perform
    :param payload: payload to send: dictionary with parameters or None
    :param version: version of the job to call. Use exact version or alias, like "latest"
    :param method: HTTP method: GET, POST, PUT, DELETE, etc.
    :param timeout: seconds of network inactivity that raises a timeout exception. None disables all timeouts
    :return: result object returned by the called job
    """
    src_job = os.environ.get('JOB_NAME')
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            request: httpx.Request = _prepare_request(client, entrypoint, job_name, path, payload, version, method)
            response = await client.send(request)
        response.raise_for_status()
        return response.json()

    except httpx.HTTPStatusError as e:
        raise RuntimeError(f'failed to call job "{job_name} {version}" by {src_job}: {e}: {e.response.text}') from e
    except BaseException as e:
        raise RuntimeError(f'failed to call job "{job_name} {version}" by {src_job}: {e}') from e


def async_job_call(
    entrypoint: JobEntrypoint,
    job_name: str,
    path: str = '/api/v1/perform',
    payload: Optional[Dict] = None,
    version: str = 'latest',
    method: str = 'POST'
) -> Any:
    """
    Call another job's endpoint using Async Job Call.
    :param entrypoint: entrypoint object of the job that calls another job
    :param job_name: name of the job to call
    :param path: endpoint path to call, default is /api/v1/perform
    :param payload: payload to send: dictionary with parameters or None
    :param version: version of the job to call. Use exact version or alias, like "latest"
    :param method: HTTP method: GET, POST, PUT, DELETE, etc.
    :return: result object returned by the called job
    """
    src_job = os.environ.get('JOB_NAME')
    try:
        assert src_job, 'JOB_NAME env var is not set'
        assert 'PUB_URL' in os.environ, 'PUB_URL env var is not set'
        internal_pub_url = os.environ['PUB_URL']

        # Start async task
        tracing_header = os.environ.get('REQUEST_TRACING_HEADER', 'X-Request-Tracing-Id')
        caller_header = os.environ.get('CALLER_NAME_HEADER', 'X-Caller-Name')
        outgoing_headers = {
            'X-Racetrack-Auth': os.environ['AUTH_TOKEN'],
        }
        if hasattr(entrypoint, 'request_context'):
            request: Request = getattr(entrypoint, 'request_context').get()
            outgoing_headers[tracing_header] = request.headers.get(tracing_header) or ''
            outgoing_headers[caller_header] = request.headers.get(caller_header) or ''
        set_rk_headers(outgoing_headers, entrypoint)

        url = f'{internal_pub_url}/async/new/job/{job_name}/{version}{path}'
        response = httpx.request(method.upper(), url, json=payload, headers=outgoing_headers)
        response.raise_for_status()
        task_id: str = response.json()['task_id']

        # Poll the result
        while True:
            try:
                response = httpx.get(f'{internal_pub_url}/async/task/{task_id}/poll', timeout=httpx.Timeout(5, read=60))
            except httpx.ReadTimeout:
                continue
            if response.status_code == 200:
                break
            elif response.status_code in {202, 408, 504}:
                continue
            else:
                raise RuntimeError(f'Response error: {response}')

        return response.json()

    except httpx.HTTPStatusError as e:
        raise RuntimeError(f'failed to call job "{job_name} {version}" by {src_job}: {e}: {e.response.text}') from e
    except BaseException as e:
        raise RuntimeError(f'failed to call job "{job_name} {version}" by {src_job}: {e}') from e


def _prepare_request(
    http_client: Union[httpx.Client, httpx.AsyncClient],
    entrypoint: JobEntrypoint,
    job_name: str,
    path: str,
    payload: Optional[Dict],
    version: str,
    method: str,
) -> httpx.Request:
    src_job = os.environ.get('JOB_NAME')
    assert src_job, 'JOB_NAME env var is not set'
    assert 'PUB_URL' in os.environ, 'PUB_URL env var is not set'
    internal_pub_url = os.environ['PUB_URL']
    url = f'{internal_pub_url}/job/{job_name}/{version}{path}'

    tracing_header = os.environ.get('REQUEST_TRACING_HEADER', 'X-Request-Tracing-Id')
    caller_header = os.environ.get('CALLER_NAME_HEADER', 'X-Caller-Name')
    outgoing_headers = {
        'X-Racetrack-Auth': os.environ['AUTH_TOKEN'],
    }

    if hasattr(entrypoint, 'request_context'):
        request: Request = getattr(entrypoint, 'request_context').get()
        outgoing_headers[tracing_header] = request.headers.get(tracing_header) or ''
        outgoing_headers[caller_header] = request.headers.get(caller_header) or ''
    set_rk_headers(outgoing_headers, entrypoint)

    request: httpx.Request = http_client.build_request(method.upper(), url, json=payload, headers=outgoing_headers)
    return request
