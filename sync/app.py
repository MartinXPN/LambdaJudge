import base64
import json
import os
from pathlib import Path

import boto3
import botocore

from models import SyncRequest, TestCase
from sync.services import encrypt_tests, zip2tests
from sync.summary import SummaryTable, truncate

ROOT = Path('/tmp/')
cfg = botocore.config.Config(retries={'max_attempts': 0}, read_timeout=300, connect_timeout=300)
aws_lambda = boto3.client('lambda', config=cfg)
s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')


def trigger_sync_s3_handler(event, context):
    print('Event:', type(event), event)
    print('Context:', context)

    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']  # some-bucket/some-folder/img.jpg
    problem = key.split('.')[0]
    print('bucket:', bucket, 'key:', key, 'problem:', problem)

    encryption_key = os.environ.get('EFS_PROBLEMS_ENCRYPTION_KEY', '')
    print('encryption key len:', len(encryption_key))

    request = SyncRequest(bucket=bucket, key=key, encryption_key=encryption_key)
    print('request:', request)
    res = aws_lambda.invoke(FunctionName='SyncS3WithEFS', Payload=request.to_json())['Payload']
    res = res.read().decode('utf-8')
    res = json.loads(res)
    print('invocation result:', res)

    SummaryTable(dynamodb).write(problem, TestCase.schema().load(res['tests_truncated'], many=True))
    print('Wrote to a summary table')


def sync_efs_handler(event, context):
    print('Event:', type(event), event)
    print('Context:', context)
    request = SyncRequest.from_dict(event)
    print('All the params:', request)

    bucket, key, encryption_key = request.bucket, request.key, request.encryption_key
    problem = key.split('.')[0]
    problem_file = f'/mnt/efs/{problem}.gz.fer'
    zip_path = ROOT / f'{problem}.zip'
    print('problem_file', problem_file, 'zip:', zip_path)

    s3.download_file(bucket, key, str(zip_path))
    print('download size:', zip_path.stat().st_size)

    tests = zip2tests(zip_path)
    tests_truncated = truncate(tests, max_len=100)
    # Convert asset files to base64 strings
    for test in tests_truncated:
        test.input_assets = {
            filename: base64.b64encode(content).decode('utf-8')
            for filename, content in test.input_assets.items()
        } if test.input_assets else None
        test.target_assets = {
            filename: base64.b64encode(content).decode('utf-8')
            for filename, content in test.target_assets.items()
        } if test.target_assets else None
    tests = encrypt_tests(tests, encryption_key=encryption_key)

    with open(problem_file, 'wb') as f:
        f.write(tests)
    print(f'{problem_file} size on EFS:', Path(problem_file).stat().st_size)
    zip_path.unlink(missing_ok=True)

    return {
        'status_code': 200,
        'test_count': len(tests_truncated),
        'tests_truncated': [t.to_dict() for t in tests_truncated],
    }
