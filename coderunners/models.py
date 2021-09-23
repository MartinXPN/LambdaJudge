from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict

from dataclasses_json import dataclass_json, LetterCase


class Status(Enum):
    OK = 'Solved'
    WA = 'Wrong answer'
    TLE = 'Time limit exceeded'
    MLE = 'Memory limit exceeded'
    RUNTIME_ERROR = 'Runtime error'
    COMPILATION_ERROR = 'Compilation error'


@dataclass
class Stats:
    max_rss: float
    max_vms: float
    total_time: float
    return_code: int
    outputs: str
    errors: str
    status: Status


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
class TestResult:
    status: Status
    memory: float
    time: float
    outputs: Optional[str] = None
