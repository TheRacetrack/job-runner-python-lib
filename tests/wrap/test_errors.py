from racetrack_job_wrapper.api import create_api_app
from racetrack_job_wrapper.entrypoint import JobEntrypoint
from racetrack_job_wrapper.health import HealthState
from fastapi.testclient import TestClient


def test_bad_request():
    class TestEntrypoint(JobEntrypoint):
        def perform(self):
            raise ValueError('nope')

    entrypoint = TestEntrypoint()
    api_app = create_api_app(entrypoint, HealthState(live=True, ready=True))

    client = TestClient(api_app)

    response = client.post('/api/v1/perform', json={})
    assert response.status_code == 400
    output = response.json()
    assert output['error'] == 'nope'
