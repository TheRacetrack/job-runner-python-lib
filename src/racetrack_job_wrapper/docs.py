import inspect
from typing import Optional, Any, Dict

from racetrack_job_wrapper.entrypoint import JobEntrypoint


def get_input_example(entrypoint: JobEntrypoint, endpoint: str = '/perform') -> Dict[str, Any]:
    """Return exemplary input for a Job endpoint (/perform endpoint or auxiliary endpoint)"""
    if hasattr(entrypoint, 'docs_input_examples'):
        docs_input_examples = getattr(entrypoint, 'docs_input_examples')()
        if not isinstance(docs_input_examples, dict):
            raise RuntimeError('docs_input_examples outcome is not a dict')
        if endpoint in docs_input_examples:
            return docs_input_examples[endpoint]
    if endpoint == '/perform' and hasattr(entrypoint, 'docs_input_example'):
        return getattr(entrypoint, 'docs_input_example')()
    return {}


def get_perform_docs(entrypoint: JobEntrypoint) -> Optional[str]:
    """Return docstring attached to a perform function"""
    if hasattr(entrypoint, 'perform'):
        perform_func = getattr(entrypoint, 'perform')
        return inspect.getdoc(perform_func)
    return None
