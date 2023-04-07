from dataclasses import dataclass
from enum import Enum
from typing import Optional

from dataclasses_json import DataClassJsonMixin, LetterCase, Undefined, config


class DataClassJsonCamelMixIn(DataClassJsonMixin):
    dataclass_json_config = config(letter_case=LetterCase.CAMEL, undefined=Undefined.EXCLUDE)['dataclasses_json']


class Status(Enum):
    OK = 'Solved'
    WA = 'Wrong answer'
    TLE = 'Time limit exceeded'
    MLE = 'Memory limit exceeded'
    OLE = 'Output limit exceeded'
    RUNTIME_ERROR = 'Runtime error'
    COMPILATION_ERROR = 'Compilation error'
    LINTING_ERROR = 'Linting error'
    SKIPPED = 'Skipped'


@dataclass
class TestCase(DataClassJsonCamelMixIn):
    input: str
    target: str
    input_files: Optional[dict[str, str]] = None        # list of (filename, content)
    target_files: Optional[dict[str, str]] = None       # list of (filename, content)


@dataclass
class TestGroup(DataClassJsonCamelMixIn):
    points: float
    points_per_test: float
    count: int

    def __post_init__(self):
        if self.points != 0 and self.points_per_test != 0:
            raise ValueError('Both points and points_per_test values are nonzero')


@dataclass
class SubmissionRequest(DataClassJsonCamelMixIn):
    # Code is a mapping from filename.extension -> content (Http requests have 2MB limit)
    code: dict[str, str]
    language: str
    memory_limit: int = 512     # MB
    time_limit: int = 5         # seconds
    output_limit: float = 1     # MB

    # In case of both problem and test_cases being provided, tests = test_cases + problem.tests
    problem: Optional[str] = None                   # used to find the test cases in the EFS
    test_cases: Optional[list[TestCase]] = None     # list of test cases
    test_groups: Optional[list[TestGroup]] = None

    return_outputs: bool = False
    stop_on_first_fail: bool = True
    lint: bool = False

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
        if self.checker_language:
            self.checker_language = self.checker_language.lower()

        if self.test_cases is None:
            self.test_cases = []

        if self.comparison_mode == 'custom':
            assert self.checker_code is not None and self.checker_language is not None


@dataclass
class RunResult(DataClassJsonCamelMixIn):
    status: Status
    memory: float
    time: float
    return_code: int
    score: float = 0
    message: Optional[str] = None
    outputs: Optional[str] = None
    errors: Optional[str] = None
    output_files: Optional[dict[str, str]] = None


@dataclass
class SubmissionResult(DataClassJsonCamelMixIn):
    overall: RunResult
    compile_result: RunResult
    linting_result: Optional[RunResult] = None
    test_results: Optional[list[RunResult]] = None


@dataclass
class SyncRequest(DataClassJsonCamelMixIn):
    bucket: str
    key: str
    encryption_key: str
