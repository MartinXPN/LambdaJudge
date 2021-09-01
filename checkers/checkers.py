from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

from util import is_float


class EqualityChecker(ABC):
    @abstractmethod
    def is_same(self, output: str, target: str) -> bool:
        ...


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
