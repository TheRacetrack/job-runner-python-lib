from dataclasses import dataclass
from http import HTTPMethod
from typing import Callable


@dataclass
class EndpointConfig:
    path: str
    method: HTTPMethod 
    handler: Callable