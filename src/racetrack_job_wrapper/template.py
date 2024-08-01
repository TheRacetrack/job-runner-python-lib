from pathlib import Path
from typing import Dict

from jinja2 import Template

from racetrack_job_wrapper.manifest.merge import load_merged_manifest
from racetrack_job_wrapper.log.logs import get_logger
from racetrack_job_wrapper.client.env import merge_env_vars, read_secret_vars_from_file

logger = get_logger(__name__)
JOB_MANIFEST_FILENAME = 'job.yaml'


def render_template(
    template_file: str,
    out_file: str,
):
    assert Path(template_file).is_file(), f'template file was not found: {template_file}'
    template_content = Path(template_file).read_text()
    template = Template(template_content)

    manifest_path = Path(JOB_MANIFEST_FILENAME)
    assert manifest_path.is_file(), f'manifest file was not found: {manifest_path}'
    manifest = load_merged_manifest(manifest_path, {})

    secret_build_env = read_secret_vars_from_file('.', manifest.secret_build_env_file, 'secret build vars')
    build_env_vars: Dict[str, str] = merge_env_vars(manifest.build_env, secret_build_env)

    render_vars = {
        'manifest': manifest,
        'manifest_jobtype_extra': manifest.get_jobtype_extra() or {},
        'env_vars': build_env_vars,
    }
    templated = template.render(**render_vars)
    Path(out_file).write_text(templated)
    logger.info(f'template file rendered into {out_file}')
