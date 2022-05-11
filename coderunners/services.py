import gzip
from pathlib import Path
from typing import Optional

from cryptography.fernet import Fernet

from coderunners.checkers import Checker
from coderunners.compilers import Compiler
from coderunners.process import Process
from coderunners.scoring import Scorer
from coderunners.util import save_code
from models import RunResult, Status, SubmissionResult, TestCase, TestGroup

ROOT = Path('/tmp/')


def compile_code(code: dict[str, str], language: str) -> tuple[Optional[Path], RunResult]:
    # Currently, we only support single-file submissions
    submission_paths = save_code(save_dir=ROOT, code=code)

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


def check_code(code: dict[str, str], language: str, memory_limit: int, time_limit: int, output_limit: float,
               problem: Optional[str], test_cases: Optional[list[TestCase]], test_groups: list[TestGroup],
               return_outputs: bool, stop_on_first_fail: bool,
               comparison_mode: str, float_precision: float, delimiter: Optional[str],
               checker_code: Optional[dict[str, str]], checker_language: Optional[str],
               callback_url: Optional[str], encryption_key: Optional[str]) -> SubmissionResult:
    Process('rm -rf /tmp/*', timeout=5, memory_limit_mb=512).run()  # Avoid having no space left on device issues

    executable_path, compilation_result = compile_code(code, language)
    if executable_path is None:
        return SubmissionResult(overall=compilation_result, compile_result=compilation_result)

    if problem:
        # Compress:   (1) json.dumps   (2) .encode('utf-8')   (3) gzip.compress()   (4) encrypt
        # Decompress: (1) decrypt      (2) gzip.decompress()  (3) .decode('utf-8')  (4) json.loads()
        problem_file = f'/mnt/efs/{problem}.gz.fer'
        print('getting test cases from the storage: ', problem_file)
        fernet = Fernet(encryption_key.encode())
        with open(problem_file, 'rb') as f:
            data = fernet.decrypt(f.read())
            data = gzip.decompress(data)
            data = data.decode('utf-8')
            test_cases = TestCase.schema().loads(data, many=True)
    print(f'There are: {len(test_cases)} test cases')

    # Prepare the checker
    checker_executable_path = None
    if comparison_mode == 'custom':
        checker_executable_path, checker_compilation_result = compile_code(checker_code, checker_language)
        if checker_executable_path is None:
            checker_compilation_result.message = 'Checker compilation failed'
            return SubmissionResult(overall=checker_compilation_result, compile_result=checker_compilation_result)

    checker = Checker.from_mode(
        mode=comparison_mode,
        float_precision=float_precision, delimiter=delimiter, executable_path=checker_executable_path
    )

    # Run the first test as a warmup to avoid having big time consumption on the first run
    print('Running test warmup', end='...')
    Process(
        f'{executable_path}', timeout=time_limit, memory_limit_mb=memory_limit, output_limit_mb=output_limit,
    ).run(test_cases[0].input)
    print('Done')

    # Process all tests
    test_results: list[RunResult] = []
    for i, test in enumerate(test_cases):
        print(f'Running test {i}', end='...')
        r = Process(
            f'{executable_path}', timeout=time_limit, memory_limit_mb=memory_limit, output_limit_mb=output_limit,
        ).run(test.input)

        (r.status, r.score, r.message) = checker.check(
            inputs=test.input, output=r.outputs, target=test.target, code=code
        ) if r.status == Status.OK else (r.status, 0, r.message)
        print(f'Test {i} res: {r.status} => {r.score}')

        test_results.append(r)
        if not return_outputs:
            test_results[-1].outputs = None
            test_results[-1].errors = None

        if stop_on_first_fail and r.status != Status.OK:
            test_results += [RunResult(status=Status.WA, memory=0, time=0, return_code=0)] * (len(test_cases) - i - 1)
            break
    print('test_results:', test_results)
    assert len(test_results) == len(test_cases)

    # Scoring
    scorer = Scorer.from_request(test_groups)
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
