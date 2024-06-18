from dataclasses import dataclass

from fastapi.testclient import TestClient

from racetrack_job_wrapper.api import create_api_app
from racetrack_job_wrapper.health import HealthState
from racetrack_job_wrapper.wrapper import create_entrypoint_app
from racetrack_client.utils.quantity import Quantity


def test_serialize_numpy_array():
    api_app = create_entrypoint_app('sample/numpy_response_model.py', manifest_dict={})

    client = TestClient(api_app)

    response = client.post('/api/v1/perform', json={})
    assert response.status_code == 200
    output = response.json()
    assert output == [1, 2, 3]


@dataclass
class DataClassy:
    name: str
    age: int
    is_classy: bool


def test_serialize_dataclass():
    class TestEntrypoint:
        def perform(self):
            return DataClassy(name='Data', age=30, is_classy=True)

    entrypoint = TestEntrypoint()
    api_app = create_api_app(entrypoint, HealthState(live=True, ready=True))

    client = TestClient(api_app)

    response = client.post('/api/v1/perform', json={})
    assert response.status_code == 200
    assert response.json() == {'name': 'Data', 'age': 30, 'is_classy': True}


def test_serialize_quantity():
    class TestEntrypoint:
        def perform(self):
            return [
                Quantity('100Mi'),
                {
                    'quantity': Quantity('1000m'),
                },
            ]

    entrypoint = TestEntrypoint()

    api_app = create_api_app(entrypoint, HealthState(live=True, ready=True))

    client = TestClient(api_app)

    response = client.post('/api/v1/perform', json={})
    assert response.status_code == 200
    assert response.json() == [
        '100Mi',
        {'quantity': '1000m'},
    ]
