from dataclasses import dataclass
from typing import Optional, List, Union

from dataclasses_json import dataclass_json, LetterCase


class Status:
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
    submission_download_url: str
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
    status: str
    memory: float
    time: float
    score: float
    outputs: Union[str, List[str], None] = None
    compile_outputs: Optional[str] = None


@dataclass
class Stats:
    max_rss: float
    max_vms: float
    total_time: float
    return_code: int
    outputs: str
    errors: str
