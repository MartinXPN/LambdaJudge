import glob
import gzip
import json
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile

import boto3
from cryptography.fernet import Fernet
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

    with TemporaryDirectory() as extraction_dir, ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extraction_dir)
        targets = (glob.glob(f'{extraction_dir}/**/*.ans.txt', recursive=True) +
                   glob.glob(f'{extraction_dir}/**/*.out.txt', recursive=True) +
                   glob.glob(f'{extraction_dir}/**/*.a', recursive=True) +
                   glob.glob(f'{extraction_dir}/**/*.ans', recursive=True) +
                   glob.glob(f'{extraction_dir}/**/*.out', recursive=True))
        targets = sorted(targets)
        print('targets:', targets)
        inputs = [t.replace('.a', '') if t.endswith('.a') else t.replace('.ans', '.in').replace('.out', '.in')
                  for t in targets]
        print('inputs:', inputs)

        tests = []
        for ins, outs in zip(inputs, targets):
            with open(ins) as inf, open(outs) as of:
                print(ins, outs)
                tests.append({
                    'input': inf.read(),
                    'target': of.read(),
                })

    tests_truncated = truncate(tests, max_len=100)

    print('encryption key len:', len(encryption_key))
    fernet = Fernet(encryption_key)

    # Compress:   (1) json.dumps   (2) .encode('utf-8')   (3) gzip.compress()   (4) encrypt
    # Decompress: (1) decrypt      (2) gzip.decompress()  (3) .decode('utf-8')  (4) json.loads()
    tests = json.dumps(tests)                                               # (1)
    print('initial sys.size of tests:', sys.getsizeof(tests))
    big = sys.getsizeof(tests) > 50 * 1024 * 1024
    tests = tests.encode('utf-8')                                           # (2)
    tests = gzip.compress(tests, compresslevel=9 if not big else 7)         # (3)
    tests = fernet.encrypt(tests)                                           # (4)
    print('final sys.size of tests:', sys.getsizeof(tests))

    with open(problem_file, 'wb') as f:
        f.write(tests)
    print(f'{problem_file} size on EFS:', Path(problem_file).stat().st_size)
    zip_path.unlink(missing_ok=True)

    return {
        'status_code': 200,
        'test_count': len(tests_truncated),
        'tests_truncated': tests_truncated,
    }
