from typing import Any

from racetrack_client.utils.datamodel import convert_to_json_serializable


def to_json_serializable(obj: Any) -> Any:
    try:
        import numpy as np
        if isinstance(obj, np.ndarray):
            return convert_to_json_serializable(obj.tolist())
    except ModuleNotFoundError:
        pass

    return convert_to_json_serializable(obj)
