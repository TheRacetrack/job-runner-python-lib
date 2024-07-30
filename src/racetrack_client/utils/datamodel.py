import dataclasses
from datetime import date, datetime
import json
from pathlib import Path, PosixPath
from typing import Dict, List, Type, TypeVar, Union, Any, get_origin, get_args
import types

import yaml

T = TypeVar("T")


def parse_dict_datamodel(obj_dict: Dict, clazz: Type[T]) -> T:
    """
    Cast dict object to expected dataclass model
    :param obj: dict object to be transformed to pydantic.BaseModel
    :param clazz: pydantic.BaseModel type
    """
    return parse_object(obj_dict, clazz)


def parse_object(obj: Any, clazz: Type[T]) -> T:
    """
    Cast object value to its expected type
    :param obj: object value to be transformed into its expected type
    :param clazz: object's expected type
    """
    if obj is None:
        return None
    if dataclasses.is_dataclass(clazz):
        assert isinstance(obj, dict), f'expected dict type to parse into a dataclass, got {type(obj)}'
        field_types = {field.name: field.type for field in dataclasses.fields(clazz)}
        dataclass_kwargs = dict()
        for key, value in obj.items():
            if key not in field_types:
                raise KeyError(f'unexpected field "{key}" provided to type {clazz}')
            dataclass_kwargs[key] = parse_object(value, field_types[key])
        return clazz(**dataclass_kwargs)
    elif get_origin(clazz) in {Union, types.UnionType}:  # Union or Optional type
        union_types = get_args(clazz)
        left_types = []
        for union_type in union_types:
            if dataclasses.is_dataclass(union_type):
                if obj is not None:
                    return parse_object(obj, union_type)
            elif clazz is type(None):
                if obj is None:
                    return None
            else:
                left_types.append(union_type)
        if not left_types:
            raise ValueError(f'none of the union types "{clazz}" match to a given value: {obj}')
        return parse_object(obj, left_types[0])
    else:
        return clazz(obj)


def parse_dict_datamodels(
    obj_list: List[Dict],
    clazz: Type[T],
) -> List[T]:
    """Cast list of dict objects to expected data model types (pydantic.BaseModel)"""
    return [parse_dict_datamodel(obj_dict, clazz) for obj_dict in obj_list]


def parse_yaml_datamodel(
    yaml_obj: str,
    clazz: Type[T],
) -> T:
    """
    Parse YAML and convert it to expected data model
    :param yaml_obj: YAML string
    :param clazz: dataclass type
    """
    data = yaml.load(yaml_obj, Loader=yaml.FullLoader)
    if data is None:
        data = {}
    return parse_dict_datamodel(data, clazz)


def parse_yaml_file_datamodel(
    path: Path,
    clazz: Type[T],
) -> T:
    """
    Parse YAML file and convert it to expected data model
    :param path: Path to a YAML file
    :param clazz: pydantic.BaseModel type
    """
    assert path.is_file(), f"File doesn't exist: {path}"
    data = path.read_text()
    return parse_yaml_datamodel(data, clazz)


def datamodel_to_yaml_str(dataclazz) -> str:
    data_dict = datamodel_to_dict(dataclazz)
    return yaml.dump(data_dict)


def convert_to_json(obj) -> str:
    obj = to_serializable(obj)
    obj = remove_none(obj)
    return json.dumps(obj)


def convert_to_yaml(obj) -> str:
    obj = to_serializable(obj)
    obj = remove_none(obj)
    return yaml.dump(obj, sort_keys=False)


def datamodel_to_dict(dataclazz) -> Dict:
    data_dict = dataclasses.asdict(dataclazz)
    data_dict = remove_none(data_dict)
    data_dict = to_serializable(data_dict)
    return data_dict


def remove_none(obj):
    """Remove unwanted null values"""
    if isinstance(obj, list):
        return [remove_none(x) for x in obj if x is not None]
    elif isinstance(obj, dict):
        return {k: remove_none(v) for k, v in obj.items() if k is not None and v is not None}
    else:
        return obj


def to_serializable(obj):
    if dataclasses.is_dataclass(obj):
        return to_serializable(dataclasses.asdict(obj))
    elif isinstance(obj, PosixPath):
        return str(obj)
    elif isinstance(obj, (date, datetime)):
        return obj.isoformat()
    elif isinstance(obj, list):
        return [to_serializable(x) for x in obj]
    elif isinstance(obj, dict):
        return {k: to_serializable(v) for k, v in obj.items()}
    elif hasattr(obj, '__to_json__'):
        return getattr(obj, '__to_json__')()
    else:
        return obj
