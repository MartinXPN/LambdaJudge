import os
from pathlib import Path

import boto3
from botocore.config import Config

from models import TestGenRequest
from testgen.generator import generate_tests

TESTS_BUCKET = os.getenv('TESTS_BUCKET')
ZIP_PATH = Path('/tmp/') / 'tests.zip'


def handler(event, context):
    """
    Lambda to execute code that generates tests.
    This lambda has no internet access and no permissions to access resources.
    It is run on an isolated container after which the results are stored in S3.
    """
    print('Event:', type(event), event)
    print('Context:', context)
    request = TestGenRequest.from_dict(event)
    print('Bucket:', TESTS_BUCKET, 'Problem:', request.problem, 'Language:', request.language)

    if request.credentials is None:
        raise ValueError('No credentials provided to upload tests')

    # Generate the test cases and compress them into a zip file
    results = generate_tests(request)
    print(f'Done generating tests: {results}')
    if results.status == 'error':
        return results.to_json()

    # Upload the results to S3
    s3 = boto3.client(
        's3',
        aws_access_key_id=request.credentials['AccessKeyId'],
        aws_secret_access_key=request.credentials['SecretAccessKey'],
        aws_session_token=request.credentials['SessionToken'],
        config=Config(retries={'max_attempts': 2}),
    )
    print(f'Initialized the S3 client: {s3}')

    # TODO: Implement the error handling (missing zip, S3 upload failure, etc.)
    with open(ZIP_PATH, 'rb') as f:
        s3.put_object(
            Bucket=TESTS_BUCKET,
            Key=f'{request.problem}.zip',
            Body=f,
            ServerSideEncryption='AES256',
        )

    return results.to_json()
