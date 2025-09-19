import base64
import gzip
from dataclasses import dataclass, field
from enum import Enum

from dataclasses_json import DataClassJsonMixin, LetterCase, Undefined, config


class DataClassJsonCamelMixIn(DataClassJsonMixin):
    dataclass_json_config = config(letter_case=LetterCase.CAMEL, undefined=Undefined.EXCLUDE)['dataclasses_json']


def decode_assets(data: dict[str, str] | None) -> dict[str, bytes] | None:
    if data is not None:
        print('base64_to_bytes:', {filename: type(content) for filename, content in (data or {}).items()})
    if data is not None and all(isinstance(content, str) for content in data.values()):
        return {
            filename: gzip.decompress(base64.b64decode(content.encode('utf-8')))
            for filename, content in data.items()
        }
    return data


def encode_assets(data: dict[str, bytes] | None) -> dict[str, str] | None:
    if data is not None:
        print('bytes_to_base64:', {filename: type(content) for filename, content in (data or {}).items()})
    if data is not None and all(isinstance(content, bytes) for content in data.values()):
        return {
            filename: base64.b64encode(gzip.compress(content, compresslevel=7, mtime=0)).decode('utf-8')
            for filename, content in data.items()
        }
    return data


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
    input_assets: dict[str, bytes] | None = field(          # mapping filename -> binary content
        metadata=config(encoder=encode_assets, decoder=decode_assets),
        default=None,
    )
    target_assets: dict[str, bytes] | None = field(         # mapping filename -> binary content
        metadata=config(encoder=encode_assets, decoder=decode_assets),
        default=None,
    )


@dataclass
class TestGroup(DataClassJsonCamelMixIn):
    points: float
    points_per_test: float
    count: int

    def __post_init__(self):
        if self.points != 0 and self.points_per_test != 0:
            raise ValueError('Both points and points_per_test values are nonzero')


# Defining a recursive type doesn't seem to work with dataclasses-json
CodeTree = dict[str, str | dict[str, str | dict[str, str]]]


@dataclass
class SubmissionRequest(DataClassJsonCamelMixIn):
    code: CodeTree              # Mapping from filename.extension -> content (Http requests have 2MB limit)
    language: str
    id: str | None = None       # Used to identify the submission (completely optional)

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
    checker_code: CodeTree | None = None
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
    output_files: dict[str, str] | None = None              # mapping filename -> textual content
    output_assets: dict[str, bytes] | None = field(         # mapping filename -> binary content
        metadata=config(encoder=encode_assets, decoder=decode_assets),
        default=None,
    )


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
