import base64
import gzip
from pathlib import Path
from typing import Optional

from cryptography.fernet import Fernet

from coderunners.checkers import Checker
from coderunners.compilers import Compiler
from coderunners.linters import Linter
from coderunners.process import Process
from coderunners.scoring import Scorer
from coderunners.util import save_code
from models import RunResult, Status, SubmissionRequest, SubmissionResult, TestCase


class EqualityChecker(SubmissionRequest):
    ROOT: Path = Path('/tmp/')

    def compile(self, code_paths: list[Path], language: str) -> tuple[Optional[Path], RunResult]:
        """ Compiles and returns (executable path | None, compilation result) """
        compiler = Compiler.from_language(language=language)
        executable_path, compilation = compiler.compile(submission_paths=code_paths)
        if compilation.status == Status.OK and not compilation.errors:
            return executable_path, compilation

        # Compile error
        print('Compile error:', compilation)
        if compilation.status == Status.TLE:
            compilation.message = 'Compilation time limit exceeded'
        if compilation.status == Status.MLE:
            compilation.message = 'Compilation memory limit exceeded'

        compilation.status = Status.COMPILATION_ERROR
        compilation.score = 0
        return None, compilation

    # flake8: noqa: C901
    def check(self) -> SubmissionResult:
        Process('rm -rf /tmp/*', timeout=5, memory_limit_mb=512).run()  # Avoid having no space left on device issues
        code_paths = save_code(save_dir=self.ROOT, code=self.code)

        executable_path, compile_result = self.compile(code_paths, self.language)
        if executable_path is None:
            return SubmissionResult(overall=compile_result, compile_result=compile_result)

        # Lint the code
        lint_result = None
        if self.lint:
            linter = Linter.from_language(language=self.language)
            lint_result = linter.lint(code_paths)
            if lint_result.status != Status.OK:
                return SubmissionResult(overall=lint_result, compile_result=compile_result, linting_result=lint_result)

        problem_file = Path(f'/mnt/efs/{self.problem}.gz.fer')
        if self.problem and problem_file.exists():
            # Compress:   (1) json.dumps   (2) .encode('utf-8')   (3) gzip.compress()   (4) encrypt
            # Decompress: (1) decrypt      (2) gzip.decompress()  (3) .decode('utf-8')  (4) json.loads()
            print('getting test cases from the storage: ', problem_file)
            fernet = Fernet(self.encryption_key.encode())
            with open(problem_file, 'rb') as f:
                data = fernet.decrypt(f.read())
                data = gzip.decompress(data)
                data = data.decode('utf-8')
                self.test_cases += TestCase.schema().loads(data, many=True)
        print(f'There are: {len(self.test_cases)} test cases')

        # If there are no test cases => run the program and return OK as the result (no comparisons)
        if not self.test_cases:
            self.test_cases = [TestCase(input='', target='')]
            self.comparison_mode = 'ok'

        # Prepare the checker
        checker_executable_path = None
        if self.comparison_mode == 'custom':
            checker_code_paths = save_code(save_dir=self.ROOT, code=self.checker_code)
            checker_executable_path, checker_compile_result = self.compile(checker_code_paths, self.checker_language)
            if checker_executable_path is None:
                checker_compile_result.message = 'Checker compilation failed'
                return SubmissionResult(overall=checker_compile_result, compile_result=checker_compile_result)

        checker = Checker.from_mode(
            mode=self.comparison_mode,
            float_precision=self.float_precision, delimiter=self.delimiter, executable_path=checker_executable_path
        )

        # Run the first test as a warmup to avoid having big time consumption on the first run
        print('Running test warmup', end='...')
        Process(
            f'{executable_path}',
            timeout=self.time_limit, memory_limit_mb=self.memory_limit, output_limit_mb=self.output_limit,
        ).run(self.test_cases[0].input)
        print('Done')

        # Process all tests
        test_results: list[RunResult] = []
        for i, test in enumerate(self.test_cases):
            print(f'Running test {i}', end='...')

            # Convert asset files to bytes from base64 strings
            input_assets: dict[str, bytes] = {filename: base64.b64decode(content.encode('utf-8'))
                                              for filename, content in (test.input_assets or {}).items()}
            target_assets: dict[str, bytes] = {filename: base64.b64decode(content.encode('utf-8'))
                                               for filename, content in (test.target_assets or {}).items()}

            # Crete input files and input assets
            for filename, content in (test.input_files or {}).items():
                print('Creating file at:', self.ROOT / filename)
                (self.ROOT / filename).write_text(content)
            for filename, content in input_assets.items():
                print('Creating asset at:', self.ROOT / filename)
                (self.ROOT / filename).write_bytes(content)

            r = Process(
                f'{executable_path}',
                timeout=self.time_limit, memory_limit_mb=self.memory_limit, output_limit_mb=self.output_limit,
            ).run(test.input)

            output_files = {filename: (self.ROOT / filename).read_text() if (self.ROOT / filename).exists() else ''
                            for filename in (test.target_files or {}).keys()}
            output_assets = {filename: (self.ROOT / filename).read_bytes() if (self.ROOT / filename).exists() else b''
                             for filename in target_assets.keys()}

            (r.status, r.score, r.message) = checker.check(
                inputs=test.input, output=r.outputs, target=test.target,
                code=self.code,
                input_files=test.input_files, output_files=output_files, target_files=test.target_files,
                input_assets=input_assets, output_assets=output_assets, target_assets=target_assets,
            ) if r.status == Status.OK else (r.status, 0, r.message)
            print(f'Test {i} res: {r.status} => {r.score}')

            # Clean up
            cleanup_files = (test.input_files or {}).keys() | (test.target_files or {}).keys() | \
                            (test.input_assets or {}).keys() | (test.target_assets or {}).keys()
            for filename in cleanup_files:
                if (self.ROOT / filename).exists():
                    print('Removing file at:', self.ROOT / filename)
                    (self.ROOT / filename).unlink()

            # Report the result
            test_results.append(r)
            if not self.return_outputs:
                test_results[-1].outputs = None
                test_results[-1].errors = None
                test_results[-1].output_files = None
            else:
                max_len = 32000     # limit each item to 64KB (2 bytes per character)
                test_results[-1].outputs = r.outputs[:max_len] if r.outputs else None
                test_results[-1].errors = r.errors[:max_len] if r.errors else None
                test_results[-1].output_files = {
                    filename: content[:max_len]
                    for filename, content in output_files.items()
                } if output_files else None
                test_results[-1].output_assets = {
                    filename: base64.b64encode(content[:max_len]).decode('utf-8')
                    for filename, content in output_assets.items()
                } if output_assets else None

            # Stop on failure
            if self.stop_on_first_fail and test_results[-1].status != Status.OK:
                test_results += [
                    RunResult(status=Status.SKIPPED, memory=0, time=0, return_code=0)
                ] * (len(self.test_cases) - i - 1)
                print('Expected:', test.target, test.target_files)
                print('Actual:', test_results[-1].outputs, test_results[-1].output_files)
                break
        print('test_results:', test_results)
        assert len(test_results) == len(self.test_cases)

        # Scoring
        scorer = Scorer.from_request(self.test_groups)
        total, per_test = scorer.score(test_results)
        print('Total score:', total, 'Score per test:', per_test)
        for r, score in zip(test_results, per_test):
            r.score = score

        # Aggregate all the results across test cases
        first_failed = next((i for i, x in enumerate(test_results) if x.status != Status.OK), None)
        overall = RunResult(
            status=Status.OK if first_failed is None else test_results[first_failed].status,
            memory=max(t.memory for t in test_results),
            time=max(t.time for t in test_results),
            return_code=0 if first_failed is None else test_results[first_failed].return_code,
            score=total,
        )

        res = SubmissionResult(
            overall=overall, compile_result=compile_result, linting_result=lint_result, test_results=test_results
        )
        print('submission result:', res)
        return res
