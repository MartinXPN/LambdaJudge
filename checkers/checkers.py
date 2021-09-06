from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

from util import is_float


class Checker(ABC):
    @abstractmethod
    def is_correct(self, inputs: str, output: str, target: str) -> bool:
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
    def is_correct(self, inputs: str, output: str, target: str) -> bool:
        return output.strip() == target.strip()


@dataclass
class TokenEquality(Checker):
    float_precision: float = 1e-5
    delimiter: Optional[str] = None

    def is_correct(self, inputs: str, output: str, target: str) -> bool:
        output = output.strip().split(self.delimiter)
        target = target.strip().split(self.delimiter)
        if len(output) != len(target):
            return False

        for o, t in zip(output, target):
            if is_float(o) and is_float(t):
                if abs(float(o) - float(t)) > self.float_precision:
                    return False
            elif o.strip() != t.strip():
                return False

        return True
