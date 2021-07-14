import glob
import subprocess
import zipfile
import json
from pathlib import Path
from threading import Timer

import boto3
import resource

ROOT = Path('/tmp/')


def run_shell(command: str, timeout: float, memory_limit_mb: int = 512):
    memory_bits = memory_limit_mb * 1024 * 1024
    proc = subprocess.Popen(
        command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        preexec_fn=lambda: resource.setrlimit(resource.RLIMIT_AS, (memory_bits, memory_bits))
    )
    timer = Timer(timeout, proc.kill)
    try:
        timer.start()
        outs, errs = proc.communicate(timeout=timeout)
        if outs: outs = outs.decode('utf-8')
        if errs: errs = errs.decode('utf-8')
    except subprocess.TimeoutExpired:
        outs, errs = None, 'Time limit exceeded'
    finally:
        proc.kill()
        timer.cancel()

    if outs is None and errs is None:
        errs = 'Time limit exceeded'
    return outs, errs


def lambda_handler(event, context):
    print('Event:', event)
    print('Context:', context)

    problem = event['problem']
    submission = event['submission']

    s3 = boto3.resource('s3')
    bucket = s3.Bucket('lambda-judge-bucket')

    save_path = ROOT / f'{problem}.zip'
    extract_path = ROOT

    if save_path.exists():
        print(f'Saving `{problem}.zip` \tto\t `{save_path}`', end='...', flush=True)
        bucket.download_file(f'{problem}.zip', str(save_path))
        print('Done!')

        print(f'Extracting `{save_path}` to `{extract_path}`', end='...', flush=True)
        with zipfile.ZipFile(save_path, 'r') as zip_ref:
            zip_ref.extractall(extract_path)
        print('Done!')
    else:
        print('File already exists!')

    submission_path = ROOT / submission
    print(f'Saving `submissions/{submission}` \tto\t `{submission_path}`', end='...', flush=True)
    bucket.download_file(f'submissions/{submission}', str(submission_path))
    print('Done!')

    if '.cpp' == submission_path.suffix:
        executable_path = (ROOT / submission_path.stem).with_suffix('.o')
        print('Creating executable at:', executable_path)
        outs, errs = run_shell(f'g++ -std=c++11 {submission_path} -o {executable_path}', timeout=30)
        print('Compile out:', outs)
        print('Compile err:', errs)

        # Compile error
        if errs:
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'status': 'OK',
                    'solutionStatus': 'FAIL',
                }),
            }

    elif '.py' == submission_path.suffix:
        executable_path = f'python {submission_path}'
        print(f'Evaluating python submission with: `{executable_path}`')
    else:
        raise ValueError(f'{submission_path.suffix} submissions are not supported yet')

    is_correct = True
    for test_case in glob.glob(f'{extract_path}/{problem}/*'):
        print('Test case path:', test_case)
        if '.a' in str(test_case):
            continue

        input_file = str(test_case)
        output_file = input_file + '.a'
        print('Input file:', input_file)
        print('Output file:', output_file)

        outs, errs = run_shell(f'cat {input_file} | {executable_path}', timeout=2, memory_limit_mb=128)
        if errs:
            is_correct = False
            break

        output = outs.strip()
        with open(output_file, 'r') as f:
            target = f.read().strip()

        print('Output:', output)
        print('Target:', target)
        if target != output:
            is_correct = False
            break

    return {
        'statusCode': 200,
        'body': json.dumps({
            'status': 'OK',
            'solutionStatus': 'OK' if is_correct else 'FAIL',
        }),
    }
