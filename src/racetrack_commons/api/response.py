import dataclasses
import json
from datetime import date, datetime
from pathlib import PosixPath

from pydantic import BaseModel
from fastapi.encoders import ENCODERS_BY_TYPE

from racetrack_client.utils.datamodel import to_serializable
from racetrack_client.utils.quantity import Quantity


class ResponseJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if dataclasses.is_dataclass(o):
            return to_serializable(dataclasses.asdict(o))
        if isinstance(o, BaseModel):
            return to_serializable(o.model_dump())
        if isinstance(o, PosixPath):
            return str(o)
        if isinstance(o, (date, datetime)):
            return o.isoformat()
        if hasattr(o, '__to_json__'):
            return getattr(o, '__to_json__')()
        return super().default(o)


def register_response_json_encoder():

    ENCODERS_BY_TYPE[BaseModel] = lambda o: to_serializable(o.model_dump())
    ENCODERS_BY_TYPE[PosixPath] = lambda o: str(o)
    ENCODERS_BY_TYPE[date] = lambda o: o.isoformat()
    ENCODERS_BY_TYPE[datetime] = lambda o: o.isoformat()
    ENCODERS_BY_TYPE[Quantity] = lambda o: getattr(o, '__to_json__')()
