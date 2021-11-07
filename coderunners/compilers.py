from abc import abstractmethod, ABC
from dataclasses import dataclass
from pathlib import Path
from typing import Tuple

from models import Stats, Status
from process import Process


class Compiler(ABC):
    @abstractmethod
    def compile(self, submission_path: Path) -> Tuple[Path, Stats]:
        ...

    @staticmethod
    def from_language(language: str) -> 'Compiler':
        language = language.lower()
        if language in CppCompiler.supported_standards:
            return CppCompiler(language_standard=language)
        if language in PythonCompiler.supported_standards:
            return PythonCompiler(language_standard=language)
        raise ValueError(f'{language} does not have a compiler yet')


@dataclass
class CppCompiler(Compiler):
    language_standard: str
    supported_standards = {'c++11', 'c++14', 'c++17', 'c++20'}

    def compile(self, submission_path: Path):
        executable_path = submission_path.with_suffix('.o')
        print('Creating executable at:', executable_path)
        compile_res = Process(f'g++ -std={self.language_standard} {submission_path} -o {executable_path}',
                              timeout=30,
                              memory_limit_mb=512).run()

        if compile_res.status == Status.TLE:    compile_res.status = Status.COMPILATION_TLE
        if compile_res.status == Status.MLE:    compile_res.status = Status.COMPILATION_MLE
        print('Compile res', compile_res)
        return executable_path, compile_res


@dataclass
class PythonCompiler(Compiler):
    language_standard: str
    supported_standards = {'python', 'python3'}

    def compile(self, submission_path: Path):
        binary_path = submission_path.with_suffix('.pyc')
        print('Creating python binary at:', binary_path)
        compile_res = Process(f'{self.language_standard} -m py_compile {submission_path}',
                              timeout=30,
                              memory_limit_mb=512).run()

        if compile_res.status == Status.TLE:    compile_res.status = Status.COMPILATION_TLE
        if compile_res.status == Status.MLE:    compile_res.status = Status.COMPILATION_MLE
        print('Compilation res', compile_res)
        binary_path.unlink(missing_ok=True)
        executable_path = f'{self.language_standard} {submission_path}'
        return executable_path, compile_res
