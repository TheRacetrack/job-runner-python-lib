import importlib.util
import inspect
import os
import sys
from importlib.abc import Loader
from pathlib import Path
from typing import Type, Optional

from racetrack_job_wrapper.entrypoint import JobEntrypoint
from racetrack_job_wrapper.log.logs import get_logger

logger = get_logger(__name__)


def instantiate_class_entrypoint(entrypoint_path: str, class_name: Optional[str]) -> JobEntrypoint:
    """
    Create Job Entrypoint instance from a class found in a specified Python file.
    It is done by loading the module dynamically and searching for a first defined class
     or particular one if the name was given.
    """
    sys.path.append(os.getcwd())

    venv_path = os.environ.get('VENV_PACKAGES_PATH')
    if venv_path and Path(venv_path).is_dir():
        venv_sys_path = Path(venv_path).resolve().absolute().as_posix()
        # At position 0 there should be a working directory, so local modules takes precedence over site-packages
        sys.path.insert(1, venv_sys_path)
        logger.debug(f'Activated Job\'s venv: {venv_sys_path}')

    assert Path(entrypoint_path).is_file(), f'{entrypoint_path} file not found'
    spec = importlib.util.spec_from_file_location("racetrack_job", entrypoint_path)
    ext_module = importlib.util.module_from_spec(spec)
    loader: Optional[Loader] = spec.loader
    assert loader is not None, 'no module loader'
    sys.modules[spec.name] = ext_module
    loader.exec_module(ext_module)

    if class_name:
        assert hasattr(ext_module, class_name), f'class name {class_name} was not found'
        model_class = getattr(ext_module, class_name)
    else:
        model_class = find_entrypoint_class(ext_module)
    logger.info(f'loaded job class: {model_class.__name__}')
    return model_class()


def find_entrypoint_class(ext_module) -> Type[JobEntrypoint]:
    """
    Find a class defined in a Python module given as an entrypoint for a Job.
    This function doesn't check whether the class implements JobEntrypoint interface.
    The interface should be implemented implicitly, by implementing required methods.
    """
    class_members = [c[1] for c in inspect.getmembers(ext_module, inspect.isclass)]
    class_members = [c for c in class_members if c.__module__ == 'racetrack_job']  # omit classes loaded by imports
    assert len(class_members) > 0, 'no class has been found in module'
    assert len(class_members) == 1, 'multiple classes found in a module, the name should be set explicitly.'
    return class_members[0]
