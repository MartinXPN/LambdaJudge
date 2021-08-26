from dataclasses import dataclass
from typing import Optional

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
class SubmissionRequest:
    problem: str
    submission_download_url: str
    language: str
    memory_limit: int = 512
    time_limit: int = 5
    return_outputs: bool = False
    return_compile_outputs: bool = True
    stop_on_first_fail: bool = True

    def __post_init__(self):
        self.language = self.language.lower()


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class SubmissionResult:
    status: str
    memory: float
    time: float
    score: float
    outputs: Optional[str] = None
    compile_outputs: Optional[str] = None
