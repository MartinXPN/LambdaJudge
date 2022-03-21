import math
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory
from typing import Optional

from models import Status
from process import Process
from util import is_float, save_code


class Checker(ABC):
    @abstractmethod
    def check(self, inputs: str, output: str, target: str, code: dict[str, str]) -> tuple[Status, float, Optional[str]]:
        """
        Check if the program behaved correctly and return the verdict
        :param inputs: all the input of the program
        :param output: the output of the submitted program
        :param target: what the output should be according to the precalculated test
        :param code: mapping {filename: content} of the submitted code
        :return: [verdict: Status, score: float 0 to 100, message: str]
        """
        ...

    @staticmethod
    def from_mode(mode: str,
                  float_precision: Optional[float] = None, delimiter: Optional[str] = None,
                  executable_path: Optional[Path] = None) -> 'Checker':
        if mode == 'whole':
            return WholeEquality()
        if mode == 'token':
            assert float_precision is not None
            return TokenEquality(float_precision=float_precision, delimiter=delimiter)
        if mode == 'custom':
            assert executable_path is not None
            return CustomChecker(executable_path=executable_path)
        raise ValueError(f'{mode} comparison mode is not implemented yet')


class WholeEquality(Checker):
    def check(self, inputs: str, output: str, target: str, code: dict[str, str]) -> tuple[Status, float, Optional[str]]:
        return (Status.OK, 100, None) if output.strip() == target.strip() else (Status.WA, 0, None)


@dataclass
class TokenEquality(Checker):
    float_precision: float = 1e-5
    delimiter: Optional[str] = None

    def is_correct(self, output: str, target: str) -> bool:
        output = output.strip().split(self.delimiter)
        target = target.strip().split(self.delimiter)
        if len(output) != len(target):
            return False

        for o, t in zip(output, target):
            if is_float(o) and is_float(t):
                diff = abs(float(o) - float(t))
                if math.isnan(diff) or diff > self.float_precision:
                    return False
            elif o.strip() != t.strip():
                return False

        return True

    def check(self, inputs: str, output: str, target: str, code: dict[str, str]) -> tuple[Status, float, Optional[str]]:
        return (Status.OK, 100, None) if self.is_correct(output, target) else (Status.WA, 0, None)


@dataclass
class CustomChecker(Checker):
    executable_path: Path

    def check(self, inputs: str, output: str, target: str, code: dict[str, str]) -> tuple[Status, float, Optional[str]]:
        with NamedTemporaryFile('rw') as inf, \
                NamedTemporaryFile('rw') as ouf, \
                NamedTemporaryFile('rw') as tg, \
                TemporaryDirectory() as code_dir:
            save_code(save_dir=code_dir, code=code)
            inf.write(inputs)
            ouf.write(output)
            tg.write(target)

            res = Process(
                f'{self.executable_path} {inf.name} {ouf.name} {tg.name} {code_dir}',
                timeout=1, memory_limit_mb=512, output_limit_mb=1,
            ).run()

        if res.status != Status.OK:
            return res.status, 0, f'Checker failed with: {res.message}, having errors: {res.errors}'

        outputs = res.outputs.split('\n', maxsplit=2)
        if len(outputs) < 2:
            return (Status.RUNTIME_ERROR, 0,
                    'Checker failed to produce status and score (each should be on separate lines)')
        if len(outputs) == 2:
            status, score = outputs
            message = None
        else:
            status, score, message = outputs

        if not is_float(score):
            return Status.RUNTIME_ERROR, 0, 'Checker did not produce a valid score value'
        score = float(score)

        try:
            status = Status(status)
        except ValueError:
            return Status.RUNTIME_ERROR, 0, 'Checker did not produce a valid status'

        return status, score, message
