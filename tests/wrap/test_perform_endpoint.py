from racetrack_job_wrapper.wrapper import create_entrypoint_app
from fastapi.testclient import TestClient


def test_wrapped_endpoints():
    api_app = create_entrypoint_app('sample/adder_model.py', class_name='AdderModel', manifest_dict={})

    client = TestClient(api_app)

    paths = [
        '/api/v1/perform',
        '/pub/job/adder/latest/api/v1/perform',
        '/pub/fatman/adder/latest/api/v1/perform',  # backward compatibility
    ]
    for path in paths:
        response = client.post(
            path,
            json={'numbers': [40, 2]},
        )
        assert response.status_code == 200
        assert response.json() == 42
