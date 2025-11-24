import os

import boto3
from botocore.config import Config

from models import TestGenRequest, TestGenResponse
from testgen.generator import generate_tests

TESTS_BUCKET = os.getenv('TESTS_BUCKET')


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
    results, zip_path = generate_tests(request)
    print(f'Done generating tests: {results}')
    if results.status == 'error':
        return results.to_json()

    print(f'Zip path: {zip_path} => exists:{zip_path.exists()}, is_file:{zip_path.is_file()}')
    if not zip_path.exists() or not zip_path.is_file():
        return TestGenResponse(
            status='error',
            message='No zip file generated. It should be named `tests.zip`',
        ).to_json()

    # Upload the results to S3
    s3 = boto3.client(
        's3',
        aws_access_key_id=request.credentials['AccessKeyId'],
        aws_secret_access_key=request.credentials['SecretAccessKey'],
        aws_session_token=request.credentials['SessionToken'],
        config=Config(retries={'max_attempts': 2}),
    )
    print(f'Initialized the S3 client: {s3}')

    # Upload the zip file to S3
    s3.put_object(
        Bucket=TESTS_BUCKET,
        Key=f'{request.problem}.zip',
        Body=zip_path.read_bytes(),
        ServerSideEncryption='AES256',
    )
    print(f'Successfully uploaded tests archive to s3://{TESTS_BUCKET}/{request.problem}.zip')

    return results.to_json()
