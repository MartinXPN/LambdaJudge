import copy
import os
import random
import time

import boto3
import botocore
import requests as requests

from bouncer.coderunners import CodeRunner
from models import RunResult, Status, SubmissionRequest, SubmissionResult

cfg = botocore.config.Config(retries={'max_attempts': 0}, read_timeout=300, connect_timeout=300)
aws_lambda = boto3.client('lambda', config=cfg)


def check_equality(request: SubmissionRequest) -> SubmissionResult:
    callback_url = copy.copy(request.callback_url)
    print(f'callback_url: {callback_url}')
    request.callback_url = None

    if request.problem:
        # If problem is provided => we'll need an encryption key to decrypt the problem on EFS
        request.encryption_key = os.environ['EFS_PROBLEMS_ENCRYPTION_KEY']

    coderunner = CodeRunner.from_language(language=request.language)
    print('coderunner:', coderunner)
    try:
        res = coderunner.invoke(aws_lambda, request=request)
    except Exception as e:
        print('Failed to run the code:', e)
        res = SubmissionResult(
            overall=RunResult(
                status=Status.SKIPPED, time=0, memory=0, return_code=1, message='Failed to run the code',
            ),
            compile_result=RunResult(
                status=Status.SKIPPED, time=0, memory=0, return_code=1, message='Failed to run the code',
            ),
        )

    if callback_url is not None:
        print('Sending results to the callback url:\n', res.to_dict(encode_json=True))
        for attempt in range(8):
            try:
                r = requests.post(callback_url, json=res.to_dict(encode_json=True))
                print('Callback response:', r.status_code, r.reason)
                if r.status_code == 200:
                    break
            except requests.RequestException as e:
                print('Failed callback attempt:', attempt, e)

            # Calculate the delay using exponential backoff with jitter.
            base_delay = 2
            delay = min(base_delay * (2 ** attempt) + (random.randint(0, 1000) / 1000), 20)
            print(f'Waiting for {delay:.2f} seconds before retrying...')
            time.sleep(delay)

    return res
