import gzip
from pathlib import Path
from typing import Optional

from cryptography.fernet import Fernet

from checkers import Checker
from compilers import Compiler
from models import Status, SubmissionResult, TestCase
from process import Process
from util import save_code

ROOT = Path('/tmp/')


def check_code(code: dict[str, str], language: str, memory_limit: int, time_limit: int, output_limit: float,
               problem: Optional[str], test_cases: Optional[list[TestCase]],
               aggregate_results: bool, return_outputs: bool, return_compile_outputs: bool, stop_on_first_fail: bool,
               comparison_mode: str, float_precision: float, delimiter: Optional[str],
               callback_url: Optional[str], encryption_key: Optional[str]) -> SubmissionResult:
    Process('rm -rf /tmp/*', timeout=5, memory_limit_mb=512).run()  # Avoid having no space left on device issues
    submission_path = save_code(save_dir=ROOT, code=code)[0]        # Currently we only support single-file submissions

    # Compile and prepare the executable
    compiler = Compiler.from_language(language=language)
    executable_path, compilation = compiler.compile(submission_path=submission_path)
    # Compile error
    if compilation.status != Status.OK or compilation.errors:
        print('Compile error:', compilation)
        message = None
        if compilation.status == Status.TLE:    message = 'Compilation time limit exceeded'
        if compilation.status == Status.MLE:    message = 'Compilation memory limit exceeded'

        return SubmissionResult(status=Status.COMPILATION_ERROR,
                                memory=compilation.memory, time=compilation.time, score=0, message=message,
                                compile_outputs=(compilation.outputs or '') + '\n' + (compilation.errors or ''))
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

    checker = Checker.from_mode(comparison_mode, float_precision=float_precision, delimiter=delimiter)
    test_results, test_scores = [], []
    for test in test_cases:
        r = Process(
            f'{executable_path}',
            timeout=time_limit, memory_limit_mb=memory_limit, output_limit_mb=output_limit,
        ).run(test.input)

        if r.status == Status.OK:
            r.status, score, r.message = checker.check(inputs=test.input, output=r.outputs,
                                                       target=test.target, code=code)
            test_scores.append(score)
        else:
            test_scores.append(0)
        test_results.append(r)
        if stop_on_first_fail and r.status != Status.OK:
            break
    print('test_results:', test_results)

    # Aggregate all the results across test cases
    failed_test = next((i for i, x in enumerate(test_results) if x.status != Status.OK), None)
    status = Status.OK if failed_test is None else test_results[failed_test].status
    max_memory = max(t.memory for t in test_results)
    max_time = max(t.time for t in test_results)

    res = SubmissionResult(
        status=status if aggregate_results else [t.status for t in test_results],
        memory=max_memory if aggregate_results else [t.memory for t in test_results],
        time=max_time if aggregate_results else [t.time for t in test_results],
        score=sum(test_scores) / len(test_cases),
        message=[t.message or '' for t in test_results] if return_outputs else None,
        outputs=[t.outputs or '' for t in test_results] if return_outputs else None,
        errors=[t.errors or '' for t in test_results] if return_outputs else None,
        compile_outputs=compilation.outputs if return_compile_outputs else None
    )
    print('submission result:', res)
    return res
