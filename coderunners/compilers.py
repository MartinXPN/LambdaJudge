import os
import shutil
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar

from coderunners.executors import Executor, ProcessExecutor, SQLiteExecutor
from coderunners.process import Process
from models import RunResult, Status


class Compiler(ABC):
    @abstractmethod
    def compile(self, submission_paths: list[Path]) -> tuple[Executor, RunResult]:
        ...

    @classmethod
    def find_main_file_path(cls, submission_paths: list[Path], main_file_name: str) -> Path:
        for path in submission_paths:
            if path.name == main_file_name:
                return path
        return submission_paths[0]

    @staticmethod
    def from_language(language: str) -> 'Compiler':
        language = language.lower().strip()
        if language in TxtCompiler.supported_standards:
            return TxtCompiler()
        if language in CCompiler.supported_standards:
            return CCompiler(language_standard=language)
        if language in CppCompiler.supported_standards:
            return CppCompiler(language_standard=language)
        if language in PythonCompiler.supported_standards:
            return PythonCompiler(language_standard=language)
        if language in PythonMLCompiler.supported_standards:
            return PythonMLCompiler()
        if language in CSharpCompiler.supported_standards:
            return CSharpCompiler(language_standard=language)
        if language in JsCompiler.supported_standards:
            return JsCompiler(language_standard=language)
        if language in JavaCompiler.supported_standards:
            return JavaCompiler()
        if language in SQLiteCompiler.supported_standards:
            return SQLiteCompiler()
        raise ValueError(f'{language} does not have a compiler yet')


@dataclass
class TxtCompiler(Compiler):
    MAIN_FILE_NAME: ClassVar[str] = 'main.txt'
    supported_standards = {'txt', 'text'}

    def compile(self, submission_paths: list[Path]):
        if len(submission_paths) != 1:
            raise ValueError('Only one file is allowed for txt submissions')

        command = f'cat {submission_paths[0]}'
        compile_res = RunResult(status=Status.OK, memory=0, time=0, return_code=0, outputs=None, errors=None)
        return ProcessExecutor(command=command), compile_res


@dataclass
class CCompiler(Compiler):
    MAIN_FILE_NAME: ClassVar[str] = 'main.c'
    language_standard: str
    supported_standards = {'c', 'c11', 'c17', 'c23'}

    def __post_init__(self):
        if self.language_standard == 'c':
            self.language_standard = 'c23'
        if self.language_standard == 'c23':     # TODO: Remove this when upgrading to gcc 14 and above
            self.language_standard = 'c2x'

    def compile(self, submission_paths: list[Path]):
        submission_paths_str = ' '.join([str(path) for path in submission_paths])
        main_file_path = self.find_main_file_path(submission_paths, self.MAIN_FILE_NAME)
        executable_path = main_file_path.with_suffix('.o')

        print('Creating executable at:', executable_path)
        compile_res = Process(f'gcc -O3 '
                              f'-std={self.language_standard} {submission_paths_str} '
                              f'-o {executable_path}',
                              timeout=10, memory_limit_mb=512).run()
        print('Compile res', compile_res)
        return ProcessExecutor(command=str(executable_path)), compile_res


@dataclass
class CppCompiler(Compiler):
    MAIN_FILE_NAME: ClassVar[str] = 'main.cpp'
    language_standard: str
    supported_standards = {'c++', 'c++11', 'c++14', 'c++17', 'c++20', 'c++23'}

    def __post_init__(self):
        if self.language_standard == 'c++':
            self.language_standard = 'c++20'
        if self.language_standard == 'c++23':   # TODO: Remove this when upgrading to gcc 14 and above
            self.language_standard = 'c++2b'

    def compile(self, submission_paths: list[Path]):
        submission_paths_str = ' '.join([str(path) for path in submission_paths])
        main_file_path = self.find_main_file_path(submission_paths, self.MAIN_FILE_NAME)
        executable_path = main_file_path.with_suffix('.o')

        print('Creating executable at:', executable_path)
        compile_res = Process(f'g++ -O3 -Wno-write-strings -fsanitize=address '
                              f'-std={self.language_standard} {submission_paths_str} '
                              f'-o {executable_path}',
                              timeout=10, memory_limit_mb=512).run()
        print('Compile res', compile_res)
        command = f'ASAN_OPTIONS=detect_leaks=1 LSAN_OPTIONS=detect_leaks=0 {executable_path}'
        return ProcessExecutor(command=command), compile_res


@dataclass
class PythonCompiler(Compiler):
    MAIN_FILE_NAME: ClassVar[str] = 'main.py'
    language_standard: str
    supported_standards = {'python', 'python3'}

    def compile(self, submission_paths: list[Path]):
        binary_paths = [path.with_suffix('.pyc') for path in submission_paths]
        submission_paths_str = ' '.join([str(path) for path in submission_paths])
        main_file_path = self.find_main_file_path(submission_paths, self.MAIN_FILE_NAME)
        command = f'{self.language_standard} {main_file_path}'

        print('Creating python binary at:', binary_paths)
        compile_res = Process(f'{self.language_standard} -m py_compile {submission_paths_str}',
                              timeout=10, memory_limit_mb=512).run()
        print('Compile res', compile_res)

        for path in binary_paths:
            path.unlink(missing_ok=True)
        return ProcessExecutor(command=command), compile_res


@dataclass
class PythonMLCompiler(Compiler):
    MAIN_FILE_NAME: ClassVar[str] = 'main.py'
    supported_standards = {'pythonml'}

    def compile(self, submission_paths: list[Path]):
        binary_paths = [path.with_suffix('.pyc') for path in submission_paths]
        submission_paths_str = ' '.join([str(path) for path in submission_paths])
        main_file_path = self.find_main_file_path(submission_paths, self.MAIN_FILE_NAME)

        print('Creating python binary at:', binary_paths)
        compile_res = Process(f'python -m py_compile {submission_paths_str}', timeout=10, memory_limit_mb=512).run()
        print('Compile res', compile_res)

        for path in binary_paths:
            path.unlink(missing_ok=True)
        command = f'MPLCONFIGDIR=/tmp/matplotlib python {main_file_path}'
        return ProcessExecutor(command=command), compile_res


@dataclass
class CSharpCompiler(Compiler):
    language_standard: str
    supported_standards = {'c#'}

    dotnet_path = Path('/var/dotnet/dotnet')
    dll_path = Path('/tmp/out/program.dll')
    project_dir = Path('/tmp/program')
    project_file_path = project_dir / 'program.csproj'

    def compile(self, submission_paths: list[Path]):
        project_create_res = Process(f'{self.dotnet_path} new console -o {self.project_dir}',
                                     timeout=30, memory_limit_mb=512).run()
        (self.project_dir / 'Program.cs').unlink(missing_ok=True)   # Remove the default file created by .Net
        print('All files in project dir:', list(self.project_dir.iterdir()))
        print('Project Create res', project_create_res)

        command = f'{self.dotnet_path} run {self.dll_path} --project {self.project_dir}'
        if project_create_res.status != Status.OK:
            return ProcessExecutor(command=command), project_create_res

        # Copy files to project directory
        common = os.path.commonprefix([p.parent for p in submission_paths])
        for path in submission_paths:
            destination = self.project_dir / path.relative_to(common)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, destination)

        compile_cmd = f'{self.dotnet_path} build {self.project_file_path} -c Release -o {self.dll_path.parent}'
        compile_res = Process(compile_cmd, timeout=30, memory_limit_mb=512).run()
        print('Compile res', compile_res)
        return ProcessExecutor(command=command), compile_res


@dataclass
class JsCompiler(Compiler):
    MAIN_FILE_NAME: ClassVar[str] = 'index.js'
    language_standard: str
    supported_standards = {'js'}

    def compile(self, submission_paths: list[Path]):
        main_file_path = self.find_main_file_path(submission_paths, self.MAIN_FILE_NAME)
        project = main_file_path if len(submission_paths) == 1 else main_file_path.parent

        compile_res = Process(f'node --check {project}', timeout=10, memory_limit_mb=512).run()
        print('Compile res', compile_res)
        command = f'node {project}'
        return ProcessExecutor(command=command), compile_res


@dataclass
class JavaCompiler(Compiler):
    supported_standards = {'java'}
    language_standard: str = 'java'
    build_dir = Path('/tmp/build')

    def compile(self, submission_paths: list[Path]):
        self.build_dir.mkdir(parents=True, exist_ok=True)
        source_files = ' '.join(str(p) for p in submission_paths if p.suffix == '.java')
        build_res = Process(f'javac -d {self.build_dir} {source_files}', timeout=10, memory_limit_mb=512).run()
        print('Build res:', build_res)

        command = f'java -cp {self.build_dir / "Main.jar"} Main'
        if build_res.status != Status.OK:
            return ProcessExecutor(command=command), build_res

        compile_res = Process(f'cd {self.build_dir} && jar cvf Main.jar *', timeout=10, memory_limit_mb=512).run()
        print('Compile res:', compile_res)
        return ProcessExecutor(command=command), compile_res


@dataclass
class SQLiteCompiler(Compiler):
    supported_standards = {'sql', 'sqlite'}
    db_name: str = 'main.db'

    def compile(self, submission_paths: list[Path]):
        if len(submission_paths) != 1:
            return ProcessExecutor(command='echo "Only one file is allowed"'), RunResult(
                status=Status.CE, memory=0, time=0, return_code=0, outputs=None,
                errors='Only one file is allowed for SQL submissions',
            )

        script = submission_paths[0].read_text()
        executor = SQLiteExecutor(script=script, db_name=self.db_name)
        return executor, RunResult(status=Status.OK, memory=0, time=0, return_code=0, outputs=None, errors=None)
