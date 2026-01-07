from http import HTTPMethod
import random
from typing import Annotated, Dict, List

from fastapi import Body, Path, Query

from racetrack_job_wrapper.endpoint_config import EndpointConfig


class Job:
    def perform(self, x: float, y: float) -> float:
        """
        Add numbers.
        :param x: First element to add.
        :param y: Second element to add.
        :return: Sum of the numbers.
        """
        return x + y

    def auxiliary_endpoints_v2(self) -> List[EndpointConfig]:
        """
        Dict of custom endpoint paths (besides "/perform") handled by Entrypoint methods.
        EndpointConfig consists of a path to the endpoint, http method(POST or GET only),
        handler function for the endpoint and optional parameters dict that is passed to FastAPI.
        """
        return [
            EndpointConfig('/multiply/{path}', HTTPMethod.POST, self.multiply, other_options=dict(tags=["items"])),
            EndpointConfig('/random', HTTPMethod.GET, self.random, other_options=dict(tags=["items"])),
        ]

    def multiply(self, body: Annotated[float, Body(examples=[1.2])], query: Annotated[float, Query(example=2.4)], path: Annotated[float, Path(example=234.21)]) -> float:
        """
        Standard FastAPI methods of documenting and configuring parameters between body, query and path work for auxiliary endpoints.
        """
        return body*query*path

    def random(self, start: float, end: float) -> float:
        """Return random number within a range"""
        return random.uniform(start, end)
    
    def docs_input_examples(self) -> Dict[str, Dict]:
        """Return mapping of Job's endpoints to corresponding exemplary inputs."""
        return {
            '/perform': {
                'x': 40,
                'y': 2,
            }
        }
    

