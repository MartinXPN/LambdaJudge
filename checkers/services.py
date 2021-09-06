import glob
from pathlib import Path
from typing import Optional, List

import boto3

from checkers import Checker
from compilers import Compiler
from models import Status, SubmissionResult, TestCase
from process import Process
from testrunners import TestRunner
from util import download_file, extract_s3_zip

ROOT = Path('/tmp/')
s3 = boto3.resource('s3')
bucket = s3.Bucket('lambda-judge-bucket')


def check_equality(submission_download_url: str, language: str, memory_limit: int, time_limit: int,
                   problem: Optional[str], test_cases: Optional[List[TestCase]],
                   return_outputs: bool, return_compile_outputs: bool, stop_on_first_fail: bool,
                   comparison_mode: str, float_precision: float, delimiter: Optional[str]) -> SubmissionResult:
    print('checking...:', locals())
    # Setup the environment
    Process('rm -rf /tmp/*', timeout=5, memory_limit_mb=512).run()  # Avoid having no space left on device issues
    submission_path = download_file(submission_download_url, save_dir=ROOT)

    # Compile and prepare the executable
    compiler = Compiler.from_language(language=language)
    executable_path, compile_res = compiler.compile(submission_path=submission_path)
    # Compile error
    if compile_res.errors:
        return SubmissionResult(status=Status.COMPILATION_ERROR,
                                memory=compile_res.max_rss, time=0, score=0,
                                compile_outputs=compile_res.outputs + compile_res.errors)

    checker = Checker.from_mode(comparison_mode,
                                float_precision=float_precision, delimiter=delimiter)
    test_runner = TestRunner(executable_path=executable_path,
                             time_limit=time_limit, memory_limit_mb=memory_limit,
                             checker=checker,
                             stop_on_first_fail=stop_on_first_fail)

    if problem:
        save_path = ROOT / f'{problem}.zip'
        extract_path = extract_s3_zip(bucket, bucket_path=f'problems/{problem}.zip', save_path=save_path, cached=True)
        test_results = test_runner.from_files(input_paths=sorted(glob.glob(f'{extract_path}/*.i.txt')),
                                              target_paths=sorted(glob.glob(f'{extract_path}/*.o.txt')))
        nb_test_cases = len(list(glob.glob(f'{extract_path}/*.i.txt')))
        print(f'There are {nb_test_cases} test cases')
        print(list(glob.glob(f'{extract_path}/*')))
    elif test_cases:
        test_results = test_runner.from_tests(inputs=[t.input for t in test_cases],
                                              targets=[t.target for t in test_cases])
        nb_test_cases = len(test_cases)
    else:
        raise ValueError('Either `problem` or `test_cases` need to be provided!')

    # Aggregate all the results across test cases
    failed_test = next((i for i, x in enumerate(test_results) if x.status != Status.OK), None)
    nb_success = sum(x.status == Status.OK for x in test_results)
    max_memory = max(x.memory for x in test_results)
    max_time = max(x.time for x in test_results)
    return SubmissionResult(
        status=Status.OK if failed_test is None else test_results[failed_test].status,
        memory=max_memory,
        time=max_time,
        score=100 * nb_success / nb_test_cases,
        outputs=[x.outputs for x in test_results] if return_outputs else None,
        compile_outputs=compile_res.outputs if compile_res and return_compile_outputs else None)
