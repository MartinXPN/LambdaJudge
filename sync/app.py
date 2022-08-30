import json
from pathlib import Path

import boto3
from services import encrypt_tests, zip2tests
from test_summary import SummaryTable, truncate

from models import SyncRequest

ROOT = Path('/tmp/')
aws_lambda = boto3.client('lambda')
s3 = boto3.client('s3')
secret_manager = boto3.client('secretsmanager')
dynamodb = boto3.resource('dynamodb')
encryption_secret_key_id = 'arn:aws:secretsmanager:us-east-1:370358067229:secret:efs/problem/encryptionKey-xTnJWC'


def sync_s3_handler(event, context):
    print('Event:', type(event), event)
    print('Context:', context)

    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']  # some-bucket/some-folder/img.jpg
    problem = key.split('.')[0]
    print('bucket:', bucket, 'key:', key, 'problem:', problem)

    get_secret_value_response = secret_manager.get_secret_value(SecretId=encryption_secret_key_id)
    secrets = json.loads(get_secret_value_response['SecretString'])
    encryption_key = secrets['EFS_PROBLEMS_ENCRYPTION_KEY']
    print('encryption key len:', len(encryption_key))

    request = SyncRequest(bucket=bucket, key=key, encryption_key=encryption_key)
    print('request:', request)
    res = aws_lambda.invoke(FunctionName='SyncS3WithEFS', Payload=request.to_json())['Payload']
    res = res.read().decode('utf-8')
    res = json.loads(res)
    print('invocation result:', res)

    SummaryTable(dynamodb).write(problem, res['tests_truncated'])
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
    tests = encrypt_tests(tests, encryption_key=encryption_key)

    with open(problem_file, 'wb') as f:
        f.write(tests)
    print(f'{problem_file} size on EFS:', Path(problem_file).stat().st_size)
    zip_path.unlink(missing_ok=True)

    return {
        'status_code': 200,
        'test_count': len(tests_truncated),
        'tests_truncated': tests_truncated,
    }
