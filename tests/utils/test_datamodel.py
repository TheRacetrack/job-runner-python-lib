from dataclasses import dataclass, field
from typing import Optional

from racetrack_job_wrapper.utils.datamodel import parse_dict_datamodel, to_serializable


def test_parse_nested_dataclasses():
    class _Quantity:
        def __init__(self, quantity_str: str):
            self.quantity_str: str = quantity_str

        def __to_json__(self) -> str:
            return self.quantity_str

    @dataclass
    class _ResourcesManifest:
        memory: Optional[_Quantity] = None

    @dataclass
    class _GitManifest:
        remote: str
        branch: Optional[str] = None

    @dataclass
    class _Manifest:
        name: str
        git: _GitManifest
        resources: Optional[_ResourcesManifest] = None
        labels: list[str] = field(default_factory=list)
        origin_yaml_: Optional[str] = field(default=None, metadata={'exclude': True})

    datamodel = _Manifest(
        name='adder',
        git=_GitManifest(
            remote='url',
            branch='master',
        ),
        resources=_ResourcesManifest(
            memory=_Quantity('1GB'),
        ),
        labels=['a', 'b'],
    )
    expected_dict = {
        'name': 'adder',
        'git': {
            'remote': 'url',
            'branch': 'master',
        },
        'resources': {
            'memory': '1GB',
        },
        'labels': ['a', 'b'],
    }
    assert to_serializable(datamodel) == expected_dict
    assert to_serializable(parse_dict_datamodel(expected_dict, _Manifest)) == expected_dict

    datamodel = _Manifest(
        name='adder',
        git=_GitManifest(
            remote='url',
        ),
    )
    assert parse_dict_datamodel(to_serializable(datamodel), _Manifest) == datamodel
