import json
import boto3
from pathlib import Path
import subprocess


ROOT = Path('/tmp/')


def lambda_handler(event, context):
    print('Event:', event)
    print('Context:', context)

    problem = event['problem']
    submission = event['submission']

    s3 = boto3.resource('s3')
    bucket = s3.Bucket('lambda-judge-bucket')

    test_cases = []
    for o in bucket.objects.filter(Prefix=f'problems/{problem}/', Delimiter='/'):
        save_path = ROOT / Path(o.key)
        print(f'Saving `{o.key}` \tto\t `{save_path}`', end='...', flush=True)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        bucket.download_file(o.key, str(save_path))
        test_cases.append(save_path)
        print('Done!')

    submission_path = ROOT / submission
    print(f'Saving `submissions/{submission}` \tto\t `{submission_path}`', end='...', flush=True)
    bucket.download_file(f'submissions/{submission}', str(submission_path))
    print('Done!')

    if '.cpp' == submission_path.suffix:
        executable_path = (ROOT / submission_path.stem).with_suffix('.o')
        print('Creating executable at:', executable_path)
        p = subprocess.Popen(f'g++ -std=c++11 {submission_path} -o {executable_path}',
                             shell=True,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT)
        outs, errs = p.communicate()
        print('Out:', outs.decode("utf-8"))
        print('Err:', errs)
    elif '.py' == submission_path.suffix:
        executable_path = f'python {submission_path}'
    else:
        raise ValueError(f'{submission_path.suffix} submissions are not supported yet')

    is_correct = True
    for test_case in test_cases:
        if '.out' in str(test_case):
            continue

        input_file = str(test_case)
        output_file = input_file.replace('.in', '.out')
        print('Input file:', input_file)
        print('Output file:', output_file)

        p = subprocess.Popen(f'cat {input_file} | {executable_path}',
                             shell=True,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT)
        outs, errs = p.communicate(timeout=5)
        output = outs.decode('utf-8').strip()

        with open(output_file, 'r') as f:
            target = f.read().strip()

        print('Output:', output)
        print('Target:', target)
        if target != output:
            is_correct = False
            break

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "hello world",
            "solutionStatus": "OK" if is_correct else "FAIL",
        }),
    }
