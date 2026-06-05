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

    # flake8: noqa: C901
    @staticmethod
    def from_language(language: str) -> Compiler:
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
        if language in TsCompiler.supported_standards:
            return TsCompiler(language_standard=language)
        if language in DartCompiler.supported_standards:
            return DartCompiler()
        if language in SwiftCompiler.supported_standards:
            return SwiftCompiler()
        if language in PhpCompiler.supported_standards:
            return PhpCompiler()
        if language in RubyCompiler.supported_standards:
            return RubyCompiler()
        if language in RustCompiler.supported_standards:
            return RustCompiler()
        if language in ZigCompiler.supported_standards:
            return ZigCompiler()
        if language in KotlinCompiler.supported_standards:
            return KotlinCompiler()
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
                              timeout=15, memory_limit_mb=512).run()
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
                              timeout=15, memory_limit_mb=512).run()
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

    dotnet = Path('/var/dotnet/dotnet')
    dll_path = Path('/tmp/out/program.dll')
    project_dir = Path('/tmp/program')
    template_dir = Path('/var/task/coderunners/csharp_template')
    project_file_path = project_dir / 'program.csproj'
    submission_dir = project_dir / 'Submission'

    def compile(self, submission_paths: list[Path]):
        shutil.copytree(self.template_dir, self.project_dir, dirs_exist_ok=True)
        shutil.rmtree(self.submission_dir, ignore_errors=True)
        self.submission_dir.mkdir(parents=True, exist_ok=True)

        # Copy files to project directory
        common = Path(os.path.commonpath([str(path.parent) for path in submission_paths]))
        for path in submission_paths:
            destination = self.submission_dir / path.relative_to(common)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, destination)

        compile_cmd = f'{self.dotnet} build {self.project_file_path} -c Release --no-restore -o {self.dll_path.parent}'
        compile_res = Process(compile_cmd, timeout=30, memory_limit_mb=1024).run()
        print('Compile res', compile_res)
        command = f'{self.dotnet} {self.dll_path}'
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
class TsCompiler(Compiler):
    MAIN_FILE_NAME: ClassVar[str] = 'index.ts'
    language_standard: str
    supported_standards = {'ts', 'typescript'}
    build_dir = Path('/tmp/ts_build')
    tsc = Path('/var/task/typescript_runner/node_modules/.bin/tsc')
    node_type_roots = Path('/var/task/typescript_runner/node_modules/@types')

    def compile(self, submission_paths: list[Path]):
        source_files = [path for path in submission_paths if path.suffix == '.ts']
        root_dir = Path(os.path.commonpath([str(path.parent) for path in source_files]))
        main_file_path = self.find_main_file_path(source_files, self.MAIN_FILE_NAME)
        emitted_main_path = self.build_dir / main_file_path.relative_to(root_dir).with_suffix('.js')

        shutil.rmtree(self.build_dir, ignore_errors=True)
        self.build_dir.mkdir(parents=True, exist_ok=True)

        compiler_options = (
            f'--outDir {self.build_dir}',
            f'--rootDir {root_dir}',
            '--target ESNext',
            '--module NodeNext',
            '--moduleResolution NodeNext',
            '--lib ESNext',
            '--types node',
            f'--typeRoots {self.node_type_roots}',
            '--noEmitOnError',
        )
        compile_cmd = ' '.join([str(self.tsc), *(str(path) for path in source_files), *compiler_options])
        compile_res = Process(compile_cmd, timeout=15, memory_limit_mb=512).run()
        print('Compile res', compile_res)
        command = f'node {emitted_main_path}'
        return ProcessExecutor(command=command), compile_res


@dataclass
class DartCompiler(Compiler):
    MAIN_FILE_NAME: ClassVar[str] = 'main.dart'
    supported_standards = {'dart'}
    build_dir = Path('/tmp/dart_build')
    executable_path = build_dir / 'main'
    dart = Path('/var/dart/dart-sdk/bin/dart')

    def compile(self, submission_paths: list[Path]):
        source_files = [path for path in submission_paths if path.suffix == '.dart']
        main_file_path = self.find_main_file_path(source_files, self.MAIN_FILE_NAME)

        shutil.rmtree(self.build_dir, ignore_errors=True)
        self.build_dir.mkdir(parents=True, exist_ok=True)

        compile_cmd = f'{self.dart} compile exe {main_file_path} -o {self.executable_path}'
        compile_res = Process(compile_cmd, timeout=30, memory_limit_mb=1024).run()
        print('Compile res', compile_res)
        return ProcessExecutor(command=str(self.executable_path)), compile_res


@dataclass
class SwiftCompiler(Compiler):
    MAIN_FILE_NAME: ClassVar[str] = 'main.swift'
    supported_standards = {'swift'}
    build_dir = Path('/tmp/swift_build')
    executable_path = build_dir / 'main'

    def compile(self, submission_paths: list[Path]):
        source_files = [path for path in submission_paths if path.suffix == '.swift']
        self.find_main_file_path(source_files, self.MAIN_FILE_NAME)

        shutil.rmtree(self.build_dir, ignore_errors=True)
        self.build_dir.mkdir(parents=True, exist_ok=True)

        source_files_str = ' '.join(str(path) for path in source_files)
        compile_cmd = f'swiftc -O {source_files_str} -o {self.executable_path}'
        compile_res = Process(compile_cmd, timeout=15, memory_limit_mb=1024).run()
        print('Compile res', compile_res)
        return ProcessExecutor(command=str(self.executable_path)), compile_res


@dataclass
class PhpCompiler(Compiler):
    MAIN_FILE_NAME: ClassVar[str] = 'main.php'
    supported_standards = {'php'}

    def compile(self, submission_paths: list[Path]):
        source_files = [path for path in submission_paths if path.suffix == '.php']
        main_file_path = self.find_main_file_path(source_files, self.MAIN_FILE_NAME)

        compile_cmd = ' && '.join(f'php -l {path}' for path in source_files)
        compile_res = Process(compile_cmd, timeout=10, memory_limit_mb=512).run()
        print('Compile res', compile_res)
        command = f'php {main_file_path}'
        return ProcessExecutor(command=command), compile_res


@dataclass
class RubyCompiler(Compiler):
    MAIN_FILE_NAME: ClassVar[str] = 'main.rb'
    supported_standards = {'ruby'}
    ruby = Path('/usr/bin/ruby3.4')

    def compile(self, submission_paths: list[Path]):
        source_files = [path for path in submission_paths if path.suffix == '.rb']
        main_file_path = self.find_main_file_path(source_files, self.MAIN_FILE_NAME)

        compile_cmd = ' && '.join(f'{self.ruby} -c {path}' for path in source_files)
        compile_res = Process(compile_cmd, timeout=10, memory_limit_mb=512).run()
        print('Compile res', compile_res)
        command = f'{self.ruby} {main_file_path}'
        return ProcessExecutor(command=command), compile_res


@dataclass
class RustCompiler(Compiler):
    MAIN_FILE_NAME: ClassVar[str] = 'main.rs'
    supported_standards = {'rust'}
    build_dir = Path('/tmp/rust_build')
    executable_path = build_dir / 'main'

    def compile(self, submission_paths: list[Path]):
        source_files = [path for path in submission_paths if path.suffix == '.rs']
        main_file_path = self.find_main_file_path(source_files, self.MAIN_FILE_NAME)

        shutil.rmtree(self.build_dir, ignore_errors=True)
        self.build_dir.mkdir(parents=True, exist_ok=True)

        compile_cmd = f'rustc -O --edition=2024 {main_file_path} -o {self.executable_path}'
        compile_res = Process(compile_cmd, timeout=15, memory_limit_mb=512).run()
        print('Compile res', compile_res)
        return ProcessExecutor(command=str(self.executable_path)), compile_res


@dataclass
class ZigCompiler(Compiler):
    MAIN_FILE_NAME: ClassVar[str] = 'main.zig'
    supported_standards = {'zig'}
    build_dir = Path('/tmp/zig_build')
    cache_dir = Path('/tmp/zig_cache')
    global_cache_dir = Path('/tmp/zig_global_cache')
    executable_path = build_dir / 'main'
    zig = Path('/var/zig/zig')

    def compile(self, submission_paths: list[Path]):
        source_files = [path for path in submission_paths if path.suffix == '.zig']
        main_file_path = self.find_main_file_path(source_files, self.MAIN_FILE_NAME)

        shutil.rmtree(self.build_dir, ignore_errors=True)
        shutil.rmtree(self.cache_dir, ignore_errors=True)
        shutil.rmtree(self.global_cache_dir, ignore_errors=True)
        self.build_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.global_cache_dir.mkdir(parents=True, exist_ok=True)

        compiler_options = (
            'build-exe',
            str(main_file_path),
            '-O ReleaseSafe',
            f'-femit-bin={self.executable_path}',
            f'--cache-dir {self.cache_dir}',
            f'--global-cache-dir {self.global_cache_dir}',
        )
        compile_cmd = ' '.join([str(self.zig), *compiler_options])
        compile_res = Process(compile_cmd, timeout=30, memory_limit_mb=1024).run()
        print('Compile res', compile_res)
        return ProcessExecutor(command=str(self.executable_path)), compile_res


@dataclass
class KotlinCompiler(Compiler):
    MAIN_FILE_NAME: ClassVar[str] = 'main.kt'
    supported_standards = {'kotlin', 'kt'}
    build_dir = Path('/tmp/kotlin_build')
    jar_path = build_dir / 'main.jar'
    kotlinc = Path('/var/kotlin/kotlinc/bin/kotlinc')

    def compile(self, submission_paths: list[Path]):
        source_files = [path for path in submission_paths if path.suffix == '.kt']

        shutil.rmtree(self.build_dir, ignore_errors=True)
        self.build_dir.mkdir(parents=True, exist_ok=True)

        source_files_str = ' '.join(str(path) for path in source_files)
        compile_cmd = f'{self.kotlinc} {source_files_str} -include-runtime -d {self.jar_path}'
        compile_res = Process(compile_cmd, timeout=30, memory_limit_mb=1024).run()
        print('Compile res', compile_res)
        return ProcessExecutor(command=f'java -jar {self.jar_path}'), compile_res


@dataclass
class JavaCompiler(Compiler):
    supported_standards = {'java'}
    language_standard: str = 'java'
    build_dir = Path('/tmp/build')

    def compile(self, submission_paths: list[Path]):
        self.build_dir.mkdir(parents=True, exist_ok=True)
        source_files = ' '.join(str(p) for p in submission_paths if p.suffix == '.java')
        build_res = Process(f'javac -d {self.build_dir} {source_files}', timeout=15, memory_limit_mb=512).run()
        print('Build res:', build_res)

        command = f'java -cp {self.build_dir / "Main.jar"} Main'
        if build_res.status != Status.OK:
            return ProcessExecutor(command=command), build_res

        compile_res = Process(f'cd {self.build_dir} && jar cvf Main.jar *', timeout=15, memory_limit_mb=512).run()
        print('Compile res:', compile_res)
        return ProcessExecutor(command=command), compile_res


@dataclass
class SQLiteCompiler(Compiler):
    supported_standards = {'sql', 'sqlite'}
    db_name: str = 'main.db'

    def compile(self, submission_paths: list[Path]):
        if len(submission_paths) != 1:
            return ProcessExecutor(command='echo "Only one file is allowed"'), RunResult(
                status=Status.COMPILATION_ERROR, memory=0, time=0, return_code=0, outputs=None,
                errors='Only one file is allowed for SQL submissions',
            )

        script = submission_paths[0].read_text()
        executor = SQLiteExecutor(script=script, db_name=self.db_name)
        return executor, RunResult(status=Status.OK, memory=0, time=0, return_code=0, outputs=None, errors=None)
