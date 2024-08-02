from typing import Any

from racetrack_job_wrapper.utils.datamodel import to_serializable


def to_json_serializable(obj: Any) -> Any:
    try:
        import numpy as np
        if isinstance(obj, np.ndarray):
            return to_serializable(obj.tolist())
    except ModuleNotFoundError:
        pass

    return to_serializable(obj)
