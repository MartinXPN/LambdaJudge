import gzip
from pathlib import Path

from cryptography.fernet import Fernet

from coderunners.checkers import Checker
from coderunners.compilers import Compiler, TxtCompiler
from coderunners.executors import Executor
from coderunners.linters import Linter
from coderunners.process import Process
from coderunners.scoring import Scorer
from coderunners.util import save_code
from models import RunResult, Status, SubmissionRequest, SubmissionResult, TestCase


class EqualityChecker(SubmissionRequest):
    ROOT: Path = Path('/tmp/')

    @staticmethod
    def compile(code_paths: list[Path], language: str) -> tuple[Executor | None, RunResult]:
        """ Compiles and returns (executable path | None, compilation result) """
        compiler = Compiler.from_language(language=language)
        executor, compilation = compiler.compile(submission_paths=code_paths)
        if compilation.status == Status.OK and not compilation.errors:
            return executor, compilation

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

        executor, compile_result = self.compile(code_paths, self.language)
        if executor is None:
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

        # Only 1 test case is allowed for text submissions
        if isinstance(executor, TxtCompiler):
            print(f'txt => Reducing the number of test cases from {len(self.test_cases)} to 1...')
            self.test_cases = self.test_cases[:1]

        # Prepare the checker
        checker_executor = None
        if self.comparison_mode == 'custom':
            checker_code_paths = save_code(save_dir=self.ROOT, code=self.checker_code)
            checker_executor, checker_compile_result = self.compile(checker_code_paths, self.checker_language)
            if checker_executor is None:
                checker_compile_result.message = 'Checker compilation failed'
                return SubmissionResult(overall=checker_compile_result, compile_result=checker_compile_result)

        checker = Checker.from_mode(
            mode=self.comparison_mode,
            float_precision=self.float_precision, delimiter=self.delimiter, executor=checker_executor,
        )

        # Run the first test as a warmup to avoid having big time consumption on the first run
        print('Running test warmup', end='...')
        executor.run(
            self.test_cases[0],
            time_limit=self.time_limit, memory_limit_mb=self.memory_limit, output_limit_mb=self.output_limit
        )
        executor.cleanup(self.test_cases[0])
        print('Done')

        # Process all tests
        test_results: list[RunResult] = []
        for i, test in enumerate(self.test_cases):
            print(f'Running test {i}', end='...')
            r = executor.run(
                test=test,
                time_limit=self.time_limit, memory_limit_mb=self.memory_limit, output_limit_mb=self.output_limit,
            )

            (r.status, r.score, r.message) = checker.check(
                inputs=test.input, output=r.outputs, target=test.target,
                code=self.code,
                input_files=test.input_files, output_files=r.output_files, target_files=test.target_files,
                input_assets=test.input_assets, output_assets=r.output_assets, target_assets=test.target_assets,
            ) if r.status == Status.OK else (r.status, 0, r.message)
            print(f'Test {i} res: {r.status} => score {r.score}')

            # Clean up
            executor.cleanup(test)

            # Report the result
            test_results.append(r)
            if not self.return_outputs:
                test_results[-1].outputs = None
                test_results[-1].errors = None
                test_results[-1].output_files = None
                test_results[-1].output_assets = None
            else:
                max_len = 32000     # limit each item to 64KB (2 bytes per character)
                test_results[-1].outputs = r.outputs[:max_len] if r.outputs else None
                test_results[-1].errors = r.errors[:max_len] if r.errors else None
                test_results[-1].output_files = {
                    filename: content[:max_len] for filename, content in r.output_files.items()
                } if r.output_files else None
                test_results[-1].output_assets = {
                    filename: content[:max_len] for filename, content in r.output_assets.items()
                } if r.output_assets else None

            # Stop on failure
            if self.stop_on_first_fail and test_results[-1].status != Status.OK:
                test_results += [
                    RunResult(status=Status.SKIPPED, memory=0, time=0, return_code=0)
                ] * (len(self.test_cases) - i - 1)
                print('Expected:', test.target)
                print('Actual:', r.outputs)
                print('Expected files:', test.target_files)
                print('Actual files:', r.output_files)
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
