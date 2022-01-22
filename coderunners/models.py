from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict

from dataclasses_json import dataclass_json, LetterCase


class Status(Enum):
    OK = 'Solved'
    WA = 'Wrong answer'
    TLE = 'Time limit exceeded'
    MLE = 'Memory limit exceeded'
    OLE = 'Output limit exceeded'
    RUNTIME_ERROR = 'Runtime error'
    COMPILATION_ERROR = 'Compilation error'


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class TestCase:
    input: str
    target: str


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class CodeRunRequest:
    # Code is a mapping from filename.extension -> content (Http requests have 2MB limit)
    code: Dict[str, str]
    language: str
    memory_limit: int = 512
    time_limit: int = 5
    output_limit: float = 1
    program_inputs: List[str] = field(default_factory=list)

    def __post_init__(self):
        self.language = self.language.lower()


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class RunResult:
    status: Status
    memory: float
    time: float
    return_code: int
    outputs: Optional[str] = None
    errors: Optional[str] = None
