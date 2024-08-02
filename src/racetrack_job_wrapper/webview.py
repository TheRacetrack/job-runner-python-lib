from typing import Optional, Callable
import os
from pathlib import Path
from inspect import signature
import re

from fastapi import APIRouter, FastAPI
from fastapi.staticfiles import StaticFiles
from a2wsgi import WSGIMiddleware

from racetrack_job_wrapper.api.asgi.proxy import TrailingSlashForwarder, mount_at_base_path
from racetrack_job_wrapper.log.logs import get_logger
from racetrack_job_wrapper.entrypoint import JobEntrypoint

logger = get_logger(__name__)


def setup_webview_endpoints(
    entrypoint: JobEntrypoint,
    base_url: str,
    fastapi_app: FastAPI,
    api: APIRouter,
):
    webview_base_url = base_url + '/api/v1/webview'

    webview_app = instantiate_webview_app(entrypoint, webview_base_url)
    if webview_app is None:
        return

    # Determine whether webview app is WSGI or ASGI
    sig = signature(webview_app)
    if len(sig.parameters) == 2:
        webview_app = PathPrefixerWSGIMiddleware(webview_app, webview_base_url)
        webview_app = WSGIMiddleware(webview_app)
        logger.debug(f'Webview app recognized as a WSGI app')
    else:
        assert len(sig.parameters) == 3, 'ASGI app should have 3 arguments: Scope, Receive, Send'
        logger.debug(f'Webview app recognized as an ASGI app')

    # serve static resources
    static_path = Path(os.getcwd()) / 'static'
    if static_path.is_dir():
        fastapi_app.mount('/api/v1/webview/static', StaticFiles(directory=str(static_path)), name="webview_static")
        logger.debug(f'Static Webview directory found and mounted at /api/v1/webview/static')

    webview_app = mount_at_base_path(webview_app, webview_base_url)
    TrailingSlashForwarder.mount_path(webview_base_url)
    fastapi_app.mount('/api/v1/webview', webview_app)

    logger.info(f'Webview app mounted at {webview_base_url}')

    @api.get('/webview/{path:path}')
    def _job_webview_endpoint(path: Optional[str]):
        """Call custom Webview UI pages"""
        pass  # just register endpoint in swagger, it's handled by ASGI


def instantiate_webview_app(entrypoint: JobEntrypoint, base_url: str) -> Optional[Callable]:
    if not hasattr(entrypoint, 'webview_app'):
        return None
    webview_app_function = getattr(entrypoint, 'webview_app')
    return webview_app_function(base_url)


class PathPrefixerWSGIMiddleware:
    def __init__(self, app, base_path: str):
        self.app = app
        self.base_path = base_path
        self.prefix_path_regex = re.compile(r'^/pub/job/(.+?)/(.+?)/(.*)$')
        self.root_path_regex = re.compile(r'^/pub/job/(.+?)/(.+?)$')

    def __call__(self, environ, start_response):
        path = environ.get("PATH_INFO", "")
        match_prefix = self.prefix_path_regex.match(path)
        match_root = self.root_path_regex.match(path)
        if match_prefix:
            job_path = match_prefix.group(3)
            path = f"{self.base_path}/{job_path}"
            environ['PATH_INFO'] = path
            environ['REQUEST_URI'] = path
            environ['RAW_URI'] = path

        elif match_root:
            path = f"{self.base_path}/"
            environ['PATH_INFO'] = path
            environ['REQUEST_URI'] = path
            environ['RAW_URI'] = path

        elif not path.startswith(self.base_path):
            path = self.base_path + path
            environ['PATH_INFO'] = path
            environ['REQUEST_URI'] = path
            environ['RAW_URI'] = path

        return self.app(environ, start_response)
