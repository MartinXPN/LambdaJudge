import base64
from dataclasses import dataclass
from enum import Enum

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
    input_files: dict[str, str] | None = None               # mapping filename -> textual content
    target_files: dict[str, str] | None = None              # mapping filename -> textual content
    input_assets: dict[str, str | bytes] | None = None      # mapping filename -> base64 encoded string or bytes
    target_assets: dict[str, str | bytes] | None = None     # mapping filename -> base64 encoded string or bytes

    def __post_init__(self):
        """
        Make sure that if input_assets or target_assets are provided (as base64 encoded strings), convert them to bytes
        """
        if self.input_assets is not None and all(isinstance(content, str) for content in self.input_assets.values()):
            self.input_assets = {
                filename: base64.b64decode(content.encode('utf-8'))
                for filename, content in self.input_assets.items()
            }
        if self.target_assets is not None and all(isinstance(content, str) for content in self.target_assets.values()):
            self.target_assets = {
                filename: base64.b64decode(content.encode('utf-8'))
                for filename, content in self.target_assets.items()
            }


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
    time_limit: float = 5       # seconds
    output_limit: float = 1     # MB

    # In case of both problem and test_cases being provided, tests = test_cases + problem.tests
    problem: str | None = None                   # used to find the test cases in the EFS
    test_cases: list[TestCase] | None = None     # list of test cases
    test_groups: list[TestGroup] | None = None

    return_outputs: bool = False
    stop_on_first_fail: bool = True
    lint: bool = False

    # Checker parameters
    comparison_mode: str = 'whole'    # whole | token | custom
    float_precision: float = 1e-5     # Floating point precision
    delimiter: str | None = None
    checker_code: dict[str, str] | None = None
    checker_language: str | None = None

    callback_url: str | None = None  # Where to send the results when they're ready
    encryption_key: str | None = None

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
    message: str | None = None
    outputs: str | None = None
    errors: str | None = None
    output_files: dict[str, str] | None = None
    output_assets: dict[str, str] | None = None


@dataclass
class SubmissionResult(DataClassJsonCamelMixIn):
    overall: RunResult
    compile_result: RunResult
    linting_result: RunResult | None = None
    test_results: list[RunResult] | None = None


@dataclass
class SyncRequest(DataClassJsonCamelMixIn):
    bucket: str
    key: str
    encryption_key: str
