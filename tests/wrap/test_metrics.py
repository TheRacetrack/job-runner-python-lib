from fastapi.testclient import TestClient

from racetrack_job_wrapper.health import HealthState
from racetrack_job_wrapper.loader import instantiate_class_entrypoint
from racetrack_job_wrapper.metrics import metric_requests_started
from racetrack_job_wrapper.wrapper import create_api_app


def test_metrics_endpoint():
    model = instantiate_class_entrypoint('sample/metrics_job.py', None)
    api_app = create_api_app(model, HealthState(live=True, ready=True))

    client = TestClient(api_app)

    requests_total_before = metric_requests_started.collect()[0].samples[0].value

    response = client.post('/api/v1/perform', json={})
    assert response.status_code == 200

    response = client.get('/metrics')
    assert response.status_code == 200

    data: str = response.text
    metric_lines = data.splitlines()
    assert f'requests_started_total {requests_total_before+1}' in metric_lines

    assert '# HELP job_wasted_seconds Seconds you have wasted here' in metric_lines
    assert 'job_wasted_seconds 1.2' in metric_lines
    assert '# HELP job_positives Number of positive results' in metric_lines
    assert 'job_positives{color="blue"} 5.0' in metric_lines

    assert 'job_zero_value 0.0' in metric_lines, 'zero value metric should be present'

    assert 'job_null_value' not in metric_lines, 'null value metric is absent'
