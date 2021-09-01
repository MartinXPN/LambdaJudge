from abc import abstractmethod, ABC
from dataclasses import dataclass
from pathlib import Path
from typing import Tuple

from models import Stats
from process import Process


class Compiler(ABC):
    @abstractmethod
    def compile(self, submission_path: Path) -> Tuple[Path, Stats]:
        ...


@dataclass
class CppCompiler:
    language_standard: str

    def compile(self, submission_path: Path):
        executable_path = submission_path.with_suffix('.o')
        print('Creating executable at:', executable_path)
        compile_res = Process(f'g++ -std={self.language_standard} {submission_path} -o {executable_path}',
                              timeout=30,
                              memory_limit_mb=512).run()
        print('Compile res', compile_res)
        return executable_path, compile_res


@dataclass
class PythonCompiler:
    def compile(self, submission_path: Path):
        executable_path = f'python {submission_path}'
        print(f'Evaluating python submission with: `{executable_path}`')
        return executable_path, Stats(max_rss=0, max_vms=0, total_time=0, return_code=0, outputs='', errors='')
