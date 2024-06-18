import os
from typing import List
from fastapi import FastAPI

from fastapi.testclient import TestClient
import pytest
from starlette.routing import Mount

from racetrack_job_wrapper.wrapper import create_entrypoint_app


@pytest.fixture(scope="function")
def revert_workdir():
    workdir = os.getcwd()
    yield
    os.chdir(workdir)


def test_requesting_webview_wsgi_pages(revert_workdir):
    os.chdir('sample/webview')
    os.environ['JOB_NAME'] = 'skynet'
    os.environ['JOB_VERSION'] = '0.0.1'
    api_app = create_entrypoint_app('webview_wsgi_model.py', class_name='JobEntrypoint', manifest_dict={})

    _fix_app_middleware(api_app)
    client = TestClient(api_app)

    response = client.get('/pub/job/skynet/0.0.1/api/v1/webview')
    assert response.status_code == 200, f'webview without a slash is forwarded automatically, response: {response.text}'
    html = response.text
    assert 'Hello world. Here\'s a webview' in html, 'webview returns HTML'

    response = client.get('/pub/job/skynet/0.0.1/api/v1/webview/')
    assert response.status_code == 200
    html = response.text
    assert 'Hello world. Here\'s a webview' in html, 'webview returns HTML'
    assert 'href="/pub/job/skynet/0.0.1/api/v1/webview/static/style.css"' in html, 'links in HTML have valid prefixes'

    response = client.get('/pub/job/skynet/latest/api/v1/webview/')
    assert response.status_code == 200
    html = response.text
    assert 'Hello world. Here\'s a webview' in html, 'webview can be called by latest version'

    response = client.get('/pub/job/skynet/latest/api/v1/webview/static/style.css')
    assert response.status_code == 200
    content = response.text
    assert 'background-color' in content, 'static resources are served'


def test_requesting_webview_asgi_pages(revert_workdir):
    os.chdir('sample/webview')
    os.environ['JOB_NAME'] = 'skynet'
    os.environ['JOB_VERSION'] = '0.0.1'
    api_app = create_entrypoint_app('webview_asgi_model.py', class_name='JobEntrypoint')

    _fix_app_middleware(api_app)
    client = TestClient(api_app)

    response = client.get('/pub/job/skynet/0.0.1/api/v1/webview')
    assert response.status_code == 200, 'webview without a slash is forwarded automatically'
    html = response.text
    assert 'Hello world. Here\'s a webview' in html, 'webview returns HTML'

    response = client.get('/pub/job/skynet/0.0.1/api/v1/webview/')
    assert response.status_code == 200
    html = response.text
    assert 'Hello world. Here\'s a webview' in html, 'webview returns HTML'
    assert 'href="/pub/job/skynet/0.0.1/api/v1/webview/static/style.css"' in html, 'links in HTML have valid prefixes'

    response = client.get('/pub/job/skynet/latest/api/v1/webview/')
    assert response.status_code == 200
    html = response.text
    assert 'Hello world. Here\'s a webview' in html, 'webview can be called by latest version'

    response = client.get('/pub/job/skynet/latest/api/v1/webview/static/style.css')
    assert response.status_code == 200
    content = response.text
    assert 'background-color' in content, 'static resources are served'

    response = client.get('/pub/job/skynet/0.0.1', follow_redirects=False)
    assert response.status_code == 307, 'root endpoint should append slash'
    assert response.headers['location'] == '/pub/job/skynet/0.0.1/', 'root endpoint should append slash'

    response = client.get('/pub/job/skynet/0.0.1/', follow_redirects=False)
    assert response.status_code == 307, 'root endpoint should redirect to a home page'
    assert response.headers['location'] == '/pub/job/skynet/0.0.1/api/v1/webview', 'home page should redirect to a webview'


def _fix_app_middleware(api_app: FastAPI):
    # A fix for https://github.com/encode/starlette/issues/472
    api_app.user_middleware = []
    api_app.middleware_stack = api_app.build_middleware_stack()
    mounts: List[Mount] = [r for r in api_app.router.routes if isinstance(r, Mount)]
    for mount in mounts:
        mount.app.user_middleware = []
        mount.app.middleware_stack = mount.app.build_middleware_stack()
