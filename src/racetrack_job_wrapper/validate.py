import json

from racetrack_job_wrapper.utils.datamodel import to_serializable
from racetrack_job_wrapper.docs import get_input_example
from racetrack_job_wrapper.entrypoint import JobEntrypoint, list_auxiliary_endpoints
from racetrack_job_wrapper.log.context_error import wrap_context


MAX_INPUT_EXAMPLE_JSON_SIZE = 1024 * 1024  # 1MB


def validate_entrypoint(entrypoint: JobEntrypoint):
    """Validate if Job entrypoint methods are correct. Raise exception in case of error"""
    with wrap_context('invalid docs input example'):
        _validate_docs_input_examples(entrypoint)


def _validate_docs_input_examples(entrypoint: JobEntrypoint):
    auxiliary_endpoints = sorted(list_auxiliary_endpoints(entrypoint).keys())
    endpoints = ['/perform'] + auxiliary_endpoints
    for endpoint in endpoints:
        _validate_docs_input_example(entrypoint, endpoint)


def _validate_docs_input_example(entrypoint: JobEntrypoint, endpoint: str):
    docs_input_example = get_input_example(entrypoint, endpoint)
    if not isinstance(docs_input_example, dict):
        raise RuntimeError(f'input example (for {endpoint} endpoint) is not a dict')
    with wrap_context(f'failed to encode input example (for {endpoint} endpoint) to JSON'):
        raw_json = json.JSONEncoder().encode(to_serializable(docs_input_example))
    if len(raw_json) > MAX_INPUT_EXAMPLE_JSON_SIZE:
        raise RuntimeError(f'input example (for {endpoint} endpoint) encoded to JSON ({len(raw_json)} bytes) '
                           f'exceeds maximum size ({MAX_INPUT_EXAMPLE_JSON_SIZE} bytes)')
