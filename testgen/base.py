import shutil
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from pprint import pprint
from random import Random
from typing import TypedDict


class TestCase(TypedDict):
    input: str
    target: str
    input_files: dict[str, str] | None
    target_files: dict[str, str] | None


@dataclass
class BaseTestGen(ABC):
    seed: int = 42

    def __post_init__(self):
        self.rand = Random(self.seed)

    @abstractmethod
    def generate_public_tests(self) -> list[TestCase]:
        ...

    @abstractmethod
    def generate_private_tests(self) -> list[TestCase]:
        ...

    def print_tests(self, public: bool = True, private: bool = True) -> None:
        self.rand.seed(self.seed)
        if public:
            tests = list(self.generate_public_tests())
            print(f'---- Public ({len(tests)}) ----')
            pprint(tests)
        if private:
            tests = list(self.generate_private_tests())
            print(f'---- Private ({len(tests)}) ----')
            pprint(tests)

    def zip(self, root: Path, include_public_tests: bool = False) -> None:
        self.rand.seed(self.seed)
        tests = self.generate_public_tests() if include_public_tests else []
        tests += self.generate_private_tests()

        root.mkdir(parents=True, exist_ok=True)
        root.with_suffix('.zip').unlink(missing_ok=True)

        for i, test in enumerate(tests, start=1):
            (root / f'{i:03}.in.txt').write_text(test['input'])
            (root / f'{i:03}.out.txt').write_text(test['target'])
            for in_file, in_file_content in test.get('input_files', {}).items():
                file_path = root / f'{i:03}.in.{in_file}'
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(in_file_content)
            for out_file, out_file_content in test.get('target_files', {}).items():
                file_path = root / f'{i:03}.out.{out_file}'
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(out_file_content)

        shutil.make_archive(str(root), 'zip', root)
        shutil.rmtree(root)
