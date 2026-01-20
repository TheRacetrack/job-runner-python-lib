from dataclasses import dataclass, field
from http import HTTPMethod
from typing import Any, Callable, Dict


@dataclass
class EndpointConfig:
    """Definition of a single HTTP endpoint.

    Attributes:
        path: HTTP path at which the endpoint is registered.
        method: HTTP verb used to bind the handler - only GET and POST are supported at moment.
        handler: Callable invoked when the endpoint is hit.
        other_options: Additional FastAPI route options.
    """

    path: str
    method: HTTPMethod
    handler: Callable
    other_options: Dict[str, Any] = field(default_factory=dict)
