from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar

from coderunners.process import Process
from models import RunResult


class Compiler(ABC):
    @abstractmethod
    def compile(self, submission_paths: list[Path]) -> tuple[Path, RunResult]:
        ...

    @classmethod
    def get_only_file(cls, submission_paths: list[Path], lang: str) -> Path:
        # TODO remove this method when multi-file support is implemented for every langauge
        if len(submission_paths) != 1:
            raise ValueError(f'There should be single file for {lang}')
        return submission_paths[0]

    @classmethod
    def find_main_file_path(cls, submission_paths: list[Path], main_file_name: str) -> Path:
        for path in submission_paths:
            if path.name == main_file_name:
                return path
        return submission_paths[0]

    @staticmethod
    def from_language(language: str) -> 'Compiler':
        language = language.lower()
        if language in CppCompiler.supported_standards:
            return CppCompiler(language_standard=language)
        if language in PythonCompiler.supported_standards:
            return PythonCompiler(language_standard=language)
        if language in CSharpCompiler.supported_standards:
            return CSharpCompiler(language_standard=language)
        if language in JsCompiler.supported_standards:
            return JsCompiler(language_standard=language)
        if language in JavaCompiler.supported_standards:
            return JavaCompiler()
        raise ValueError(f'{language} does not have a compiler yet')


@dataclass
class CppCompiler(Compiler):
    language_standard: str
    supported_standards = {'c++11', 'c++14', 'c++17', 'c++20'}

    def compile(self, submission_paths: list[Path]):
        submission_path = self.get_only_file(submission_paths, self.language_standard)
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
    MAIN_FILE_NAME: ClassVar[str] = 'main.py'

    language_standard: str
    supported_standards = {'python', 'python3'}

    def compile(self, submission_paths: list[Path]):
        binary_paths = [path.with_suffix('.pyc') for path in submission_paths]
        submission_paths_str = ' '.join([str(path) for path in submission_paths])
        print('Creating python binary at:', binary_paths)
        compile_res = Process(f'{self.language_standard} -m py_compile {submission_paths_str}',
                              timeout=10, memory_limit_mb=512).run()

        print('Compile res', compile_res)
        for path in binary_paths:
            path.unlink(missing_ok=True)

        main_file_path = self.find_main_file_path(submission_paths, self.MAIN_FILE_NAME)
        executable_path = f'{self.language_standard} {main_file_path}'
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

    def compile(self, submission_paths: list[Path]):
        submission_path = self.get_only_file(submission_paths, self.language_standard)

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


@dataclass
class JsCompiler(Compiler):
    language_standard: str
    supported_standards = {'js'}

    def compile(self, submission_paths: list[Path]):
        submission_path = self.get_only_file(submission_paths, self.language_standard)
        compile_res = Process(f'node --check {submission_path}', timeout=10, memory_limit_mb=512).run()
        print('Compile res', compile_res)
        executable_path = f'node {submission_path}'

        return executable_path, compile_res


@dataclass
class JavaCompiler(Compiler):
    supported_standards = {'java'}
    language_standard: str = 'java'

    def compile(self, submission_paths: list[Path]):
        submission_path = self.get_only_file(submission_paths, self.language_standard)
        compile_res = Process(f'javac -d /tmp/build {submission_path}', timeout=10, memory_limit_mb=512).run()
        classname = "Main"
        print('Compile res:', compile_res, 'Class name:', classname)
        executable_path = f'java -classpath /tmp/build/ {classname}'

        return executable_path, compile_res
