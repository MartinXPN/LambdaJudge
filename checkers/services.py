import glob
import zipfile
from pathlib import Path
from typing import List

import boto3

from models import Status, SubmissionRequest, SubmissionResult
from process import Process


def is_float(value: str):
    try:
        float(value)
        return True
    except ValueError:
        return False


def extract_s3_zip(bucket, bucket_path: str, save_path: Path, cached: bool = True) -> Path:
    print(f'Saving `{bucket_path}` \tto\t `{save_path}`', end='...', flush=True)
    bucket.download_file(f'{bucket_path}', str(save_path))
    print('Done!')

    extract_path = save_path.with_suffix('')
    print(f'Extracting `{save_path}` to `{extract_path}`', end='...', flush=True)
    with zipfile.ZipFile(save_path, 'r') as zip_ref:
        zip_ref.extractall(extract_path)
        folder_path = extract_path / zip_ref.namelist()[0]  # ['A/', 'A/018.a', 'A/012.a', ... ]
    print('Done!')

    return folder_path


def download_s3_file(bucket, bucket_path: str, save_path: Path) -> Path:
    print(f'Saving `submissions/{bucket_path}` \tto\t `{save_path}`', end='...', flush=True)
    bucket.download_file(f'{bucket_path}', str(save_path))
    print('Done!')
    return save_path


def check_equality(request: SubmissionRequest) -> SubmissionResult:
    ROOT = Path('/tmp/')
    s3 = boto3.resource('s3')
    bucket = s3.Bucket('lambda-judge-bucket')

    save_path = ROOT / f'{request.problem}'
    Process('rm -rf /tmp/*', timeout=5, memory_limit_mb=512).run()  # Avoid having no space left on device issues

    extract_path = extract_s3_zip(bucket,
                                  bucket_path=f'problems/{request.problem}',
                                  save_path=save_path,
                                  cached=True)

    submission_path = download_s3_file(bucket,
                                       bucket_path=f'submissions/{request.submission}',
                                       save_path=ROOT / request.submission)

    compile_res = None
    if 'c++' in request.language:
        executable_path = submission_path.with_suffix('.o')
        print('Creating executable at:', executable_path)
        compile_res = Process(f'g++ -std={request.language} {submission_path} -o {executable_path}',
                              timeout=30,
                              memory_limit_mb=512).run()
        print('Compile res', compile_res)

        # Compile error
        if compile_res.errors:
            return SubmissionResult(status=Status.COMPILATION_ERROR,
                                    memory=compile_res.max_rss, time=compile_res.total_time, score=0,
                                    compile_outputs=compile_res.outputs + compile_res.errors)

    elif 'python' in request.language:
        executable_path = f'python {submission_path}'
        print(f'Evaluating python submission with: `{executable_path}`')
    else:
        raise ValueError(f'{request.language} submissions are not supported yet')

    test_results: List[SubmissionResult] = []
    for test_case in glob.glob(f'{extract_path}/*'):
        if '.a' in str(test_case):
            continue

        input_file = str(test_case)
        output_file = input_file + '.a'
        print('Test files:', input_file, output_file)

        test_res = Process(f'cat {input_file} | {executable_path}',
                           timeout=request.time_limit,
                           memory_limit_mb=request.memory_limit).run()
        if test_res.return_code != 0 or (not test_res.outputs and test_res.errors):
            print('Errs:', test_res.errors)
            print('Return code:', test_res.return_code)
            test_results.append(SubmissionResult(
                status=Status.RUNTIME_ERROR if test_res.errors not in {Status.MLE, Status.TLE} else test_res.errors,
                memory=test_res.max_rss,
                time=test_res.total_time,
                score=0,
                outputs=test_res.outputs if request.return_outputs else None,
                compile_outputs=None
            ))
            if request.stop_on_first_fail:
                break
            else:
                continue

        output = test_res.outputs.strip()
        with open(output_file, 'r') as f:
            target = f.read().strip()

        if is_float(target) and is_float(output):
            target, output = f'{float(target):.3f}', f'{float(output):.3f}'

        test_results.append(SubmissionResult(
            status=Status.WA if target != output else Status.OK,
            memory=test_res.max_rss,
            time=test_res.total_time,
            score=0 if target != output else 100,
            outputs=test_res.outputs if request.return_outputs else None,
            compile_outputs=None
        ))

    # Aggregate all the results across test cases
    nb_test_cases = len(list(glob.glob(f'{extract_path}/*.a')))
    failed_test = next((i for i, x in enumerate(test_results) if x.status != Status.OK), None)
    nb_success = sum(x.status == Status.OK for x in test_results)
    max_memory = max(x.memory for x in test_results)
    max_time = max(x.time for x in test_results)
    return SubmissionResult(
        status=Status.OK if failed_test is None else test_results[failed_test].status,
        memory=max_memory,
        time=max_time,
        score=100 * nb_success / nb_test_cases,
        outputs='\n-------------\n'.join([x.outputs for x in test_results]) if request.return_outputs else None,
        compile_outputs=compile_res.outputs if compile_res and request.return_compile_outputs else None)
