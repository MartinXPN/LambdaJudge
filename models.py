from dataclasses import dataclass
from enum import Enum
from typing import Optional

from dataclasses_json import LetterCase, dataclass_json


class Status(Enum):
    OK = 'Solved'
    WA = 'Wrong answer'
    TLE = 'Time limit exceeded'
    MLE = 'Memory limit exceeded'
    OLE = 'Output limit exceeded'
    RUNTIME_ERROR = 'Runtime error'
    COMPILATION_ERROR = 'Compilation error'
    SKIPPED = 'Skipped'


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class TestCase:
    input: str
    target: str
    input_files: Optional[dict[str, str]] = None        # list of (filename, content)
    target_files: Optional[dict[str, str]] = None       # list of (filename, content)


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class TestGroup:
    points: float
    points_per_test: float
    count: int

    def __post_init__(self):
        if self.points != 0 and self.points_per_test != 0:
            raise ValueError('Both points and points_per_test values are nonzero')


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class SubmissionRequest:
    # Code is a mapping from filename.extension -> content (Http requests have 2MB limit)
    code: dict[str, str]
    language: str
    memory_limit: int = 512     # MB
    time_limit: int = 5         # seconds
    output_limit: float = 1     # MB

    # Provide either problem (which is used to find the test cases in the EFS)
    # Or provide the test cases as a list of TestCases directly
    problem: Optional[str] = None
    test_cases: Optional[list[TestCase]] = None
    test_groups: Optional[list[TestGroup]] = None

    return_outputs: bool = False
    stop_on_first_fail: bool = True

    # Checker parameters
    comparison_mode: str = 'whole'    # whole | token | custom
    float_precision: float = 1e-5     # Floating point precision
    delimiter: Optional[str] = None
    checker_code: Optional[dict[str, str]] = None
    checker_language: Optional[str] = None

    callback_url: Optional[str] = None  # Where to send the results when they're ready
    encryption_key: Optional[str] = None

    def __post_init__(self):
        self.language = self.language.lower()
        assert self.problem is not None and self.test_cases is None or \
            self.problem is None and self.test_cases is not None
        if self.comparison_mode == 'custom':
            assert self.checker_code is not None and self.checker_language is not None


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class RunResult:
    status: Status
    memory: float
    time: float
    return_code: int
    score: float = 0
    message: Optional[str] = None
    outputs: Optional[str] = None
    errors: Optional[str] = None


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class SubmissionResult:
    overall: RunResult
    compile_result: RunResult
    test_results: Optional[list[RunResult]] = None
