import gzip
from pathlib import Path
from typing import Dict, List, Optional

from checkers import Checker
from coderunners import CodeRunner
from compilers import Compiler
from models import Status, SubmissionResult, TestCase
from process import Process

ROOT = Path('/tmp/')


def save_code(save_dir: Path, code: Dict[str, str]) -> List[Path]:
    saved_paths: List[Path] = []
    for filename, content in code.items():
        path = save_dir / filename
        saved_paths.append(path)
        with open(path, 'w') as f:
            f.write(content)

    return saved_paths


def check_code(code: Dict[str, str], language: str, memory_limit: int, time_limit: int, output_limit: float,
               problem: Optional[str], test_cases: Optional[List[TestCase]],
               aggregate_results: bool, return_outputs: bool, return_compile_outputs: bool,
               comparison_mode: str, float_precision: float, delimiter: Optional[str],
               callback_url: Optional[str]) -> SubmissionResult:
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

    code_runner = CodeRunner(executable_path=executable_path,
                             time_limit=time_limit, memory_limit_mb=memory_limit, output_limit_mb=output_limit)
    if problem:
        with open(f'/mnt/efs/{problem}.gz', 'rb') as f:
            json_tests = gzip.decompress(f.read()).decode('utf-8')
            test_cases = TestCase.schema().loads(json_tests, many=True)

    checker = Checker.from_mode(comparison_mode, float_precision=float_precision, delimiter=delimiter)

    test_results = []
    for test in test_cases:
        r = code_runner.run(test.input)
        if r.status == Status.OK and not checker.is_correct(inputs=test.input, output=r.outputs, target=test.target):
            r.status = Status.WA
        test_results.append(r)
    print('test_results:', test_results)

    # Aggregate all the results across test cases
    failed_test = next((i for i, x in enumerate(test_results) if x.status != Status.OK), None)
    status = Status.OK if failed_test is None else test_results[failed_test].status
    nb_success = sum(t.status == Status.OK for t in test_results)
    max_memory = max(t.memory for t in test_results)
    max_time = max(t.time for t in test_results)

    res = SubmissionResult(
        status=status if aggregate_results else [t.status for t in test_results],
        memory=max_memory if aggregate_results else [t.memory for t in test_results],
        time=max_time if aggregate_results else [t.time for t in test_results],
        score=100 * nb_success / len(test_cases),
        outputs=[t.outputs or '' for t in test_results] if return_outputs else None,
        errors=[t.errors or '' for t in test_results] if return_outputs else None,
        compile_outputs=compilation.outputs if return_compile_outputs else None
    )
    print('submission result:', res)
    return res
