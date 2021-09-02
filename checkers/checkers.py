from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

from util import is_float


class EqualityChecker(ABC):
    @abstractmethod
    def is_same(self, output: str, target: str) -> bool:
        ...

    @staticmethod
    def from_mode(mode: str,
                  float_precision: Optional[float] = None, delimiter: Optional[str] = None) -> 'EqualityChecker':
        if mode == 'whole':
            return WholeEquality()
        if mode == 'token':
            assert float_precision is not None
            return TokenEquality(float_precision=float_precision, delimiter=delimiter)
        raise ValueError(f'{mode} comparison mode is not implemented yet')


class WholeEquality(EqualityChecker):
    def is_same(self, output: str, target: str) -> bool:
        return output.strip() == target.strip()


@dataclass
class TokenEquality(EqualityChecker):
    float_precision: float = 1e-5
    delimiter: Optional[str] = None

    def is_same(self, output: str, target: str) -> bool:
        for o, t in zip(output.split(self.delimiter), target.split(self.delimiter)):
            if is_float(o) and is_float(t):
                if abs(float(o) - float(t)) > self.float_precision:
                    return False
            elif o.strip() != t.strip():
                return False

        return True
