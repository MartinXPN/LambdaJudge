from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Union, Dict

from dataclasses_json import dataclass_json, LetterCase


class Status(Enum):
    OK = 'Solved'
    WA = 'Wrong answer'
    TLE = 'Time limit exceeded'
    MLE = 'Memory limit exceeded'
    RUNTIME_ERROR = 'Runtime error'
    COMPILATION_ERROR = 'Compilation error'


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class TestCase:
    input: str
    target: str


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class SubmissionRequest:
    # Code is a mapping from filename.extension -> content (Http requests have 2MB limit)
    code: Dict[str, str]
    language: str
    memory_limit: int = 512
    time_limit: int = 5

    # Provide either problem (which is used to find the test cases in the s3 bucket)
    # Or provide the test cases as a list of TestCases directly
    problem: Optional[str] = None
    test_cases: Optional[List[TestCase]] = None

    return_outputs: bool = False
    return_compile_outputs: bool = True
    stop_on_first_fail: bool = True
    comparison_mode: str = 'whole'    # whole / token
    float_precision: float = 1e-5     # Floating point precision
    delimiter: Optional[str] = None

    def __post_init__(self):
        self.language = self.language.lower()
        assert self.problem is not None and self.test_cases is None or \
               self.problem is None     and self.test_cases is not None


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class SubmissionResult:
    status: Status
    memory: float
    time: float
    score: float
    outputs: Union[str, List[str], None] = None
    compile_outputs: Optional[str] = None


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class CodeRunRequest:
    # Code is a mapping from filename.extension -> content (Http requests have 2MB limit)
    code: Dict[str, str]
    language: str
    memory_limit: int = 512
    time_limit: int = 5
    test_inputs: List[str] = field(default_factory=list)


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class TestResult:
    status: Status
    memory: float
    time: float
    outputs: Optional[str] = None
