import copy

import boto3
import requests as requests

from coderunners import CodeRunner
from models import SubmissionResult, SubmissionRequest

aws_lambda = boto3.client('lambda')


def check_equality(request: SubmissionRequest) -> SubmissionResult:
    callback_url = copy.copy(request.callback_url)
    request.callback_url = None

    coderunner = CodeRunner.from_language(language=request.language)
    print('coderunner:', coderunner)
    res = coderunner.invoke(aws_lambda, request=request)

    if callback_url is not None:
        print('Sending results to the callback url:\n', res.to_dict())
        r = requests.post(callback_url, data=res.to_dict())
        print('callback:', r.status_code, r.reason)
    return res
