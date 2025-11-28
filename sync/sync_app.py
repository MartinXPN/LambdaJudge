from pathlib import Path

import boto3

from models import SyncRequest
from sync.summary import truncate
from sync.sync import encrypt_tests, zip2tests

s3 = boto3.client('s3')


def handler(event, context):
    print('Event:', type(event), event)
    print('Context:', context)
    request = SyncRequest.from_dict(event)
    print('All the params:', request)

    bucket, key, encryption_key = request.bucket, request.key, request.encryption_key
    problem = key.split('.')[0]
    problem_file = Path(f'/mnt/efs/{problem}.gz.fer')
    zip_path = Path('/tmp/') / f'{problem}.zip'
    print('problem_file', problem_file, 'zip:', zip_path)

    s3.download_file(bucket, key, str(zip_path))
    print('download size:', zip_path.stat().st_size)

    tests = zip2tests(zip_path)
    tests_truncated = truncate(tests, max_len=100)
    tests = encrypt_tests(tests, encryption_key=encryption_key)

    problem_file.write_bytes(tests)
    print(f'{problem_file} size on EFS:', problem_file.stat().st_size)
    zip_path.unlink(missing_ok=True)

    return {
        'status_code': 200,
        'test_count': len(tests_truncated),
        'tests_truncated': [t.to_dict() for t in tests_truncated],
    }
