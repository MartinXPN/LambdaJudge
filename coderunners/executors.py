from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from coderunners.process import Process

from models import RunResult, TestCase


class Executor(ABC):
    """
    Executes a test case and returns the result.
    """

    @abstractmethod
    def run(self, test: TestCase, **kwargs) -> RunResult:
        ...

    def cleanup(self, test: TestCase) -> None:
        ...


@dataclass
class ProcessExecutor(Executor):
    command: str | Iterable[str]
    ROOT: Path = Path('/tmp/')

    def run(self, test: TestCase, time_limit: float, memory_limit_mb: int, output_limit_mb: float) -> RunResult:

        # Crete input files and input assets
        for filename, content in (test.input_files or {}).items():
            print('Creating file at:', self.ROOT / filename)
            (self.ROOT / filename).write_text(content)
        for filename, content in (test.input_assets or {}).items():
            print('Creating asset at:', self.ROOT / filename)
            (self.ROOT / filename).write_bytes(content)

        r = Process(
            self.command,
            timeout=time_limit, memory_limit_mb=memory_limit_mb, output_limit_mb=output_limit_mb,
        ).run(test.input)

        # Read output files and output assets into the result
        r.output_files = {
            filename: (self.ROOT / filename).read_text() if (self.ROOT / filename).exists() else ''
            for filename in (test.target_files or {}).keys()
        }
        r.output_assets = {
            filename: (self.ROOT / filename).read_bytes() if (self.ROOT / filename).exists() else b''
            for filename in (test.target_assets or {}).keys()
        }
        return r

    def cleanup(self, test: TestCase) -> None:
        cleanup_files = (test.input_files or {}).keys() | (test.target_files or {}).keys() | \
                        (test.input_assets or {}).keys() | (test.target_assets or {}).keys()
        for filename in cleanup_files:
            if (self.ROOT / filename).exists():
                print('Removing file at:', self.ROOT / filename)
                (self.ROOT / filename).unlink()
