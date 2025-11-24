from pathlib import Path

from coderunners.process import Process
from coderunners.util import save_code
from models import Status, TestGenRequest, TestGenResponse

base_generator = '''
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
'''.lstrip()


def generate_tests(request: TestGenRequest) -> tuple[TestGenResponse, Path]:
    root = Path('/tmp/')
    zip_path = root / 'tests.zip'
    Process('rm -rf /tmp/*', timeout=5, memory_limit_mb=512).run()  # Clean up before starting
    (root / 'base.py').write_text(base_generator)

    # Save the user code and run it (currently only a single-file generator)
    code_paths = save_code(save_dir=root, code=request.code)
    main_path = code_paths[0]
    r = Process(f'python {main_path}', timeout=10, memory_limit_mb=512, output_limit_mb=20).run()

    if r.status != Status.OK:
        return TestGenResponse(
            status='error',
            message=f'Error while running the test generation code:\n{r.errors}\n\n{r.outputs}\n{r.message}',
        ), zip_path

    if not zip_path.exists() or not zip_path.is_file():
        return TestGenResponse(
            status='error',
            message='No zip file generated. It should be named `tests.zip`',
        ), zip_path

    return TestGenResponse(status='success', message=r.message), zip_path
