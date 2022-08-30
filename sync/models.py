# TODO: Unite model files into one
from dataclasses import dataclass
from typing import Optional

from dataclasses_json import LetterCase, dataclass_json


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class SyncRequest:
    bucket: str
    key: str
    encryption_key: str


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class TestCase:
    input: str
    target: str
    input_files: Optional[dict[str, str]] = None        # list of (filename, content)
    target_files: Optional[dict[str, str]] = None       # list of (filename, content)
