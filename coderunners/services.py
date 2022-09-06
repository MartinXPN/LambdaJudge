import gzip
from pathlib import Path
from typing import Optional

from cryptography.fernet import Fernet

from coderunners.checkers import Checker
from coderunners.compilers import Compiler
from coderunners.process import Process
from coderunners.scoring import Scorer
from coderunners.util import save_code
from models import RunResult, Status, SubmissionRequest, SubmissionResult, TestCase


class EqualityChecker(SubmissionRequest):
    ROOT: Path = Path('/tmp/')

    def compile(self, code: dict[str, str], language: str) -> tuple[Optional[Path], RunResult]:
        """ Compiles and returns (executable path | None, compilation result) """
        submission_paths = save_code(save_dir=self.ROOT, code=code)

        compiler = Compiler.from_language(language=language)
        executable_path, compilation = compiler.compile(submission_paths=submission_paths)
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

    def check(self) -> SubmissionResult:
        Process('rm -rf /tmp/*', timeout=5, memory_limit_mb=512).run()  # Avoid having no space left on device issues

        executable_path, compilation_result = self.compile(self.code, self.language)
        if executable_path is None:
            return SubmissionResult(overall=compilation_result, compile_result=compilation_result)

        if self.problem:
            # Compress:   (1) json.dumps   (2) .encode('utf-8')   (3) gzip.compress()   (4) encrypt
            # Decompress: (1) decrypt      (2) gzip.decompress()  (3) .decode('utf-8')  (4) json.loads()
            problem_file = f'/mnt/efs/{self.problem}.gz.fer'
            print('getting test cases from the storage: ', problem_file)
            fernet = Fernet(self.encryption_key.encode())
            with open(problem_file, 'rb') as f:
                data = fernet.decrypt(f.read())
                data = gzip.decompress(data)
                data = data.decode('utf-8')
                self.test_cases = TestCase.schema().loads(data, many=True)
        print(f'There are: {len(self.test_cases)} test cases')

        # Prepare the checker
        checker_executable_path = None
        if self.comparison_mode == 'custom':
            checker_executable_path, checker_compilation_result = self.compile(self.checker_code, self.checker_language)
            if checker_executable_path is None:
                checker_compilation_result.message = 'Checker compilation failed'
                return SubmissionResult(overall=checker_compilation_result, compile_result=checker_compilation_result)

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

            # Crete input files
            for filename, content in (test.input_files or {}).items():
                print('Creating file at:', self.ROOT / filename)
                (self.ROOT / filename).write_text(content)
            r = Process(
                f'{executable_path}',
                timeout=self.time_limit, memory_limit_mb=self.memory_limit, output_limit_mb=self.output_limit,
            ).run(test.input)

            output_files = {filename: (self.ROOT / filename).read_text() if (self.ROOT / filename).exists() else ''
                            for filename in (test.target_files or {}).keys()}

            (r.status, r.score, r.message) = checker.check(
                inputs=test.input, output=r.outputs, target=test.target,
                code=self.code,
                input_files=test.input_files, output_files=output_files, target_files=test.target_files,
            ) if r.status == Status.OK else (r.status, 0, r.message)
            print(f'Test {i} res: {r.status} => {r.score}')

            r.output_files = output_files
            test_results.append(r)
            if not self.return_outputs:
                test_results[-1].outputs = None
                test_results[-1].errors = None
                test_results[-1].output_files = None
            else:
                # TODO: limit outputs to 64kb: https://github.com/MartinXPN/LambdaJudge/issues/70
                pass

            if self.stop_on_first_fail and r.status != Status.OK:
                test_results += [
                    RunResult(status=Status.SKIPPED, memory=0, time=0, return_code=0)
                ] * (len(self.test_cases) - i - 1)
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

        res = SubmissionResult(overall=overall, compile_result=compilation_result, test_results=test_results)
        print('submission result:', res)
        return res
