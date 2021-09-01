import glob
from pathlib import Path
from typing import List, Optional

import boto3

from checkers import WholeEquality, TokenEquality
from compilers import CppCompiler, PythonCompiler
from models import Status, SubmissionResult
from process import Process
from util import download_file, extract_s3_zip


def check_equality(problem: str, submission_download_url: str, language: str, memory_limit: int, time_limit: int,
                   return_outputs: bool, return_compile_outputs: bool, stop_on_first_fail: bool,
                   comparison_mode: str, float_precision: float, delimiter: Optional[str]) -> SubmissionResult:
    print('checking...:', locals())
    ROOT = Path('/tmp/')
    s3 = boto3.resource('s3')
    bucket = s3.Bucket('lambda-judge-bucket')

    save_path = ROOT / f'{problem}.zip'
    Process('rm -rf /tmp/*', timeout=5, memory_limit_mb=512).run()  # Avoid having no space left on device issues
    submission_path = download_file(submission_download_url, save_dir=ROOT)
    extract_path = extract_s3_zip(bucket, bucket_path=f'problems/{problem}.zip', save_path=save_path, cached=True)

    # Compile and prepare the executable
    if 'c++' in language:
        compiler = CppCompiler(language_standard=language)
    elif 'python' in language:
        compiler = PythonCompiler()
    else:
        raise ValueError(f'{language} does not have a compiler')

    executable_path, compile_res = compiler.compile(submission_path=submission_path)
    # Compile error
    if compile_res.errors:
        return SubmissionResult(status=Status.COMPILATION_ERROR,
                                memory=compile_res.max_rss, time=0, score=0,
                                compile_outputs=compile_res.outputs + compile_res.errors)

    # Checker types
    if comparison_mode == 'whole':
        checker = WholeEquality()
    elif comparison_mode == 'token':
        checker = TokenEquality(float_precision=float_precision, delimiter=delimiter)
    else:
        raise ValueError(f'{comparison_mode} comparison mode is not implemented yet')

    test_results: List[SubmissionResult] = []
    for input_file in sorted(glob.glob(f'{extract_path}/*.i.txt')):
        output_file = input_file.replace('.i.txt', '.o.txt')
        print('Test files:', input_file, output_file)

        test_res = Process(f'cat {input_file} | {executable_path}',
                           timeout=time_limit,
                           memory_limit_mb=memory_limit).run()
        if test_res.return_code != 0 or (not test_res.outputs and test_res.errors):
            print('Errs:', test_res.errors)
            print('Return code:', test_res.return_code)
            test_results.append(SubmissionResult(
                status=Status.MLE if test_res.max_rss > memory_limit or test_res.errors == Status.MLE
                else Status.TLE if 1.1 * test_res.total_time > time_limit or test_res.errors == Status.TLE
                else Status.RUNTIME_ERROR,
                memory=test_res.max_rss,
                time=test_res.total_time,
                score=0,
                outputs=test_res.outputs if return_outputs else None,
                compile_outputs=None
            ))
            if stop_on_first_fail:
                break
            else:
                continue

        output = test_res.outputs.strip()
        with open(output_file, 'r') as f:
            target = f.read().strip()

        test_results.append(SubmissionResult(
            status=Status.OK if checker.is_same(output, target) else Status.WA,
            memory=test_res.max_rss,
            time=test_res.total_time,
            score=0 if target != output else 100,
            outputs=test_res.outputs if return_outputs else None,
            compile_outputs=None
        ))

    # Aggregate all the results across test cases
    nb_test_cases = len(list(glob.glob(f'{extract_path}/*.i.txt')))
    failed_test = next((i for i, x in enumerate(test_results) if x.status != Status.OK), None)
    nb_success = sum(x.status == Status.OK for x in test_results)
    max_memory = max(x.memory for x in test_results)
    max_time = max(x.time for x in test_results)
    return SubmissionResult(
        status=Status.OK if failed_test is None else test_results[failed_test].status,
        memory=max_memory,
        time=max_time,
        score=100 * nb_success / nb_test_cases,
        outputs='\n-------------\n'.join([x.outputs for x in test_results]) if return_outputs else None,
        compile_outputs=compile_res.outputs if compile_res and return_compile_outputs else None)
