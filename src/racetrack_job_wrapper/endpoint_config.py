from dataclasses import dataclass
from http import HTTPMethod
from typing import Any, Callable, Dict


@dataclass
class EndpointConfig:
    path: str
    method: HTTPMethod
    handler: Callable
    other_options: Dict[str, Any] = {}