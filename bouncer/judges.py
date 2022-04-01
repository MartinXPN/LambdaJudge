import copy
import json

import boto3
import botocore
import requests as requests

from coderunners import CodeRunner
from models import SubmissionRequest, SubmissionResult

cfg = botocore.config.Config(retries={'max_attempts': 0}, read_timeout=300, connect_timeout=300)
aws_lambda = boto3.client('lambda', config=cfg)
secret_manager = boto3.client('secretsmanager')
encryption_secret_key_id = 'arn:aws:secretsmanager:us-east-1:370358067229:secret:efs/problem/encryptionKey-xTnJWC'


def check_equality(request: SubmissionRequest) -> SubmissionResult:
    callback_url = copy.copy(request.callback_url)
    request.callback_url = None

    if request.problem:
        # If it's not a test run => we'll need an encryption key to decrypt the problem on EFS
        get_secret_value_response = secret_manager.get_secret_value(SecretId=encryption_secret_key_id)
        secrets = json.loads(get_secret_value_response['SecretString'])
        request.encryption_key = secrets['EFS_PROBLEMS_ENCRYPTION_KEY']

    coderunner = CodeRunner.from_language(language=request.language)
    print('coderunner:', coderunner)
    res = coderunner.invoke(aws_lambda, request=request)

    if callback_url is not None:
        print('Sending results to the callback url:\n', res.to_dict(encode_json=True))
        r = requests.post(callback_url, json=res.to_dict(encode_json=True))
        print('callback:', r.status_code, r.reason)
    return res
