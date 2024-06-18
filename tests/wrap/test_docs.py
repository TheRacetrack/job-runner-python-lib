import os

import pytest
from fastapi.testclient import TestClient

from racetrack_job_wrapper.wrapper import create_entrypoint_app


@pytest.fixture(scope="function")
def revert_workdir():
    workdir = os.getcwd()
    yield
    os.chdir(workdir)


def test_swaggerui_home_page(revert_workdir):
    os.chdir('sample')
    os.environ['JOB_NAME'] = 'adder'
    os.environ['JOB_VERSION'] = '0.0.1'

    api_app = create_entrypoint_app('adder_model.py', class_name='AdderModel', manifest_dict={})

    client = TestClient(api_app)

    response = client.get('/pub/job/adder/0.0.1/', follow_redirects=False)
    assert response.status_code == 307, 'root endpoint should redirect to a home page'
    assert response.headers['location'] == '/pub/job/adder/0.0.1/docs', 'home page should redirect to docs page by default'

    response = client.get('/pub/job/adder/0.0.1/docs')
    assert response.status_code == 200, 'docs page should be available'
    html = response.text
    assert 'Swagger UI' in html, 'docs page should contain Swagger UI'
