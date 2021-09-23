from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict

from dataclasses_json import dataclass_json, LetterCase


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class CodeRunRequest:
    # Code is a mapping from filename.extension -> content (Http requests have 2MB limit)
    code: Dict[str, str]
    language: str
    memory_limit: int = 512
    time_limit: int = 5
    test_inputs: List[str] = field(default_factory=list)

    def __post_init__(self):
        self.language = self.language.lower()


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class CodeRunResult:
    memory: List[float]
    time: List[float]
    outputs: Optional[List[str]] = None
    compile_outputs: str = None


class Status(Enum):
    OK = 'OK'
    MLE = 'Memory Limit Exceeded'
    TLE = 'Time Limit Exceeded'
    RE = 'Runtime Error'


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class TestResult:
    status: Status
    memory: float
    time: float
    outputs: Optional[str] = None


@dataclass
class Stats:
    max_rss: float
    max_vms: float
    total_time: float
    return_code: int
    outputs: str
    errors: str
    status: Status
