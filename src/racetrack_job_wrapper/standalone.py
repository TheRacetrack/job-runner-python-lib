import threading
from typing import Type

from racetrack_client.log.logs import configure_logs, get_logger
from racetrack_commons.api.asgi.asgi_server import serve_asgi_app
from racetrack_job_wrapper.entrypoint import JobEntrypoint
from racetrack_job_wrapper.api import create_api_app
from racetrack_job_wrapper.health import HealthState
from racetrack_job_wrapper.wrapper import read_job_manifest
from racetrack_commons.api.asgi.asgi_reloader import ASGIReloader
from racetrack_job_wrapper.api import create_health_app
from racetrack_client.log.context_error import ContextError
from racetrack_client.log.exception import short_exception_details, log_exception

logger = get_logger(__name__)


def serve_job_class(entrypoint_class: Type[JobEntrypoint]):
    """
    Instantiate job entrypoint class and serve it with an API server.
    While loading the job (creating its instance), it responds to liveness and readiness probes.
    This function blocks further execution,
    handling requests at http://0.0.0.0:7000.
    """
    configure_logs(log_level='debug')

    health_state = HealthState()
    health_app = create_health_app(health_state)
    app_reloader = ASGIReloader()
    app_reloader.mount(health_app)

    threading.Thread(
        target=_late_init,
        args=(entrypoint_class, health_state, app_reloader),
        daemon=True,
    ).start()

    serve_asgi_app(app_reloader, http_addr='0.0.0.0', http_port=7000)


def serve_job_instance(entrypoint: JobEntrypoint):
    """
    Serve a job entrypoint instance with an API server.
    This function blocks further execution,
    handling requests at http://0.0.0.0:7000.

    Usually, you just need:
        job = Job()
        serve_job_instance(job)

    but if your job initialization takes some time, use `serve_job_class` instead.
    """
    health_state = HealthState(live=True, ready=True)
    manifest_dict = read_job_manifest()
    app = create_api_app(entrypoint, health_state, manifest_dict)
    serve_asgi_app(app, http_addr='0.0.0.0', http_port=7000)


def _late_init(
    entrypoint_class: Type[JobEntrypoint],
    health_state: HealthState,
    app_reloader: ASGIReloader,
):
    try:
        logger.debug('Creating a Job instance...')
        entrypoint = entrypoint_class()
        logger.info('Job instance created')

        health_state = HealthState(live=True, ready=True)
        manifest_dict = read_job_manifest()
        fastapi_app = create_api_app(entrypoint, health_state, manifest_dict)

        app_reloader.mount(fastapi_app)

    except BaseException as e:
        error_details = short_exception_details(e)
        health_state.set_error(error_details)
        log_exception(ContextError('Initialization error', e))
    else:
        health_state.set_ready()
        logger.info('Server is ready')
