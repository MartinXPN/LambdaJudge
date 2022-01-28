import math
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

from models import Status
from util import is_float


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
                  float_precision: Optional[float] = None, delimiter: Optional[str] = None) -> 'Checker':
        if mode == 'whole':
            return WholeEquality()
        if mode == 'token':
            assert float_precision is not None
            return TokenEquality(float_precision=float_precision, delimiter=delimiter)
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
    def check(self, inputs: str, output: str, target: str, code: dict[str, str]) -> tuple[Status, float, Optional[str]]:
        pass
