import json
import os

import boto3
from botocore.config import Config

from models import SyncRequest, TestCase
from sync.summary import SummaryTable

aws_lambda = boto3.client('lambda', config=Config(retries={'max_attempts': 0}, read_timeout=300, connect_timeout=300))
dynamodb = boto3.resource('dynamodb')


def handler(event, context):
    print('Event:', type(event), event)
    print('Context:', context)

    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']  # bucket/some-folder/problem.zip
    problem = key.split('.')[0]
    print('bucket:', bucket, 'key:', key, 'problem:', problem)

    encryption_key = os.getenv('EFS_PROBLEMS_ENCRYPTION_KEY')
    print('encryption key len:', len(encryption_key))

    SummaryTable(dynamodb).log_start(problem)
    request = SyncRequest(bucket=bucket, key=key, encryption_key=encryption_key)
    print('request:', request)
    res = aws_lambda.invoke(FunctionName='SyncS3WithEFS', Payload=request.to_json())['Payload']
    res = res.read().decode('utf-8')
    res = json.loads(res)
    print('invocation result:', res)

    if 'tests_truncated' not in res:
        error = res.get('errorMessage', 'Could not process tests...')
        print('There was an error and we could not get the tests', error)
        return SummaryTable(dynamodb).log_error(problem, error)

    tests = TestCase.schema().load(res['tests_truncated'], many=True)
    print('tests:', tests)
    SummaryTable(dynamodb).write(problem, tests)
    print('Wrote to a summary table')
