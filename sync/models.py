# TODO: Unite model files into one
from dataclasses import dataclass
from typing import Optional

from dataclasses_json import config, DataClassJsonMixin, LetterCase, Undefined


class DataClassJsonCamelMixIn(DataClassJsonMixin):
    dataclass_json_config = config(letter_case=LetterCase.CAMEL, undefined=Undefined.EXCLUDE)['dataclasses_json']


@dataclass
class SyncRequest(DataClassJsonCamelMixIn):
    bucket: str
    key: str
    encryption_key: str


@dataclass
class TestCase(DataClassJsonCamelMixIn):
    input: str
    target: str
    input_files: Optional[dict[str, str]] = None        # list of (filename, content)
    target_files: Optional[dict[str, str]] = None       # list of (filename, content)
