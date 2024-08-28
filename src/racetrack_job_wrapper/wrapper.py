import os
from pathlib import Path
from typing import Optional, Dict, Any

import yaml
from fastapi import FastAPI

from racetrack_job_wrapper.wrapper_api import create_api_app
from racetrack_job_wrapper.health import HealthState
from racetrack_job_wrapper.loader import instantiate_class_entrypoint
from racetrack_job_wrapper.validate import validate_entrypoint
from racetrack_job_wrapper.log.context_error import wrap_context
from racetrack_job_wrapper.log.logs import get_logger

logger = get_logger(__name__)


def create_entrypoint_app(
    model_path: str,
    class_name: Optional[str] = None,
    health_state: HealthState = None,
    manifest_dict: Optional[Dict[str, Any]] = None,
) -> FastAPI:
    """Load entrypoint from a Python module and embed it in a FastAPI app"""
    entrypoint = instantiate_class_entrypoint(model_path, class_name)
    validate_entrypoint(entrypoint)
    if health_state is None:
        health_state = HealthState(live=True, ready=True)
    if manifest_dict is None:
        manifest_dict = read_job_manifest_dict()
    return create_api_app(entrypoint, health_state, manifest_dict)


def read_job_manifest_dict() -> Dict[str, Any]:
    with wrap_context('reading job manifest'):
        job_manifest_yaml = os.environ.get('JOB_MANIFEST_YAML', '')
        if job_manifest_yaml:
            job_manifest_yaml = job_manifest_yaml.replace('\\n', '\n')
            return yaml.safe_load(job_manifest_yaml)
        manifest_path = Path('job.yaml')
        if manifest_path.is_file():
            with manifest_path.open() as file:
                return yaml.load(file, Loader=yaml.FullLoader) or {}
        logger.warning(f'manifest yaml not found in JOB_MANIFEST_YAML env var')
        return {}
