from dataclasses import dataclass

from dataclasses_json import LetterCase, dataclass_json


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class SyncRequest:
    bucket: str
    key: str
    encryption_key: str
