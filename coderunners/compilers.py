from abc import abstractmethod, ABC
from dataclasses import dataclass
from pathlib import Path
from typing import Tuple

from models import RunResult
from process import Process


class Compiler(ABC):
    @abstractmethod
    def compile(self, submission_path: Path) -> Tuple[Path, RunResult]:
        ...

    @staticmethod
    def from_language(language: str) -> 'Compiler':
        language = language.lower()
        if language in CppCompiler.supported_standards:
            return CppCompiler(language_standard=language)
        if language in PythonCompiler.supported_standards:
            return PythonCompiler(language_standard=language)
        if language in CSharpCompiler.supported_standards:
            return CSharpCompiler(language_standard=language)
        raise ValueError(f'{language} does not have a compiler yet')


@dataclass
class CppCompiler(Compiler):
    language_standard: str
    supported_standards = {'c++11', 'c++14', 'c++17', 'c++20'}

    def compile(self, submission_path: Path):
        executable_path = submission_path.with_suffix('.o')
        print('Creating executable at:', executable_path)
        compile_res = Process(f'g++ -O3 -Wno-write-strings '
                              f'-std={self.language_standard} {submission_path} '
                              f'-o {executable_path}',
                              timeout=10, memory_limit_mb=512).run()

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
                              timeout=10, memory_limit_mb=512).run()

        print('Compile res', compile_res)
        binary_path.unlink(missing_ok=True)
        executable_path = f'{self.language_standard} {submission_path}'
        return executable_path, compile_res


@dataclass
class CSharpCompiler(Compiler):
    language_standard: str
    supported_standards = {'c#'}

    dotnet_path = Path('/var/dotnet/dotnet')
    project_dir = Path('/tmp/program')
    project_file_path = Path(project_dir, 'program.csproj')
    code_path = Path(project_dir, 'Program.cs')
    dll_path = Path('/tmp/out/program.dll')

    def compile(self, submission_path: Path):
        create_project_cmd = f'{self.dotnet_path} new console -o {self.project_dir}'
        copy_source_code_cmd = f'cat {submission_path} > {self.code_path}'
        project_create_res = Process(' && '.join([create_project_cmd, copy_source_code_cmd]),
                                     timeout=10, memory_limit_mb=512).run()
        print('Project Create res', project_create_res)

        compile_cmd = f'{self.dotnet_path} build {self.project_file_path} -c Release -o {self.dll_path.parent}'
        compile_res = Process(compile_cmd, timeout=10, memory_limit_mb=512).run()

        print('Compile res', compile_res)
        executable_path = f'{self.dotnet_path} run {self.dll_path} --project {self.project_dir}'

        return executable_path, compile_res
