import json
import os
import uuid

import boto3
from botocore.config import Config

from models import TestGenRequest, TestGenResponse
from sync.summary import SummaryTable

aws_lambda = boto3.client('lambda', config=Config(retries={'max_attempts': 0}, read_timeout=360, connect_timeout=360))
sts = boto3.client('sts')
dynamodb = boto3.resource('dynamodb')
s3 = boto3.client('s3')

UPLOAD_ROLE_ARN = os.getenv('UPLOAD_ROLE_ARN')
TESTS_BUCKET = os.getenv('TESTS_BUCKET')


def assume_upload_role(bucket: str, key: str) -> dict:
    """
    Mint short-lived STS creds restricted to s3:PutObject for one key.
    """

    resp = sts.assume_role(
        RoleArn=UPLOAD_ROLE_ARN,
        RoleSessionName=f'upload-tests-{uuid.uuid4()}',
        Policy=json.dumps({
            'Version': '2012-10-17',
            'Statement': [
                {
                    'Effect': 'Allow',
                    'Action': ['s3:PutObject', 's3:AbortMultipartUpload'],
                    'Resource': f'arn:aws:s3:::{bucket}/{key}',
                }
            ],
        }),
        DurationSeconds=900,
    )
    return resp["Credentials"]


def handler(event, context):
    """
    Bouncer that takes the request and triggers the generator lambda
    """
    print('Event:', type(event), event)
    print('Context:', context)
    request = TestGenRequest.from_json(event['body'])
    print('All the params:', request)

    # Start + Assume upload role
    table = SummaryTable(dynamodb)
    table.log_start(request.problem)
    creds = assume_upload_role(TESTS_BUCKET, f'{request.problem}.zip')
    request.credentials = creds

    # Trigger the generator lambda
    res = aws_lambda.invoke(FunctionName='TestGenerator', Payload=request.to_json())['Payload']
    res = res.read().decode('utf-8')
    res = json.loads(res)
    res = TestGenResponse.from_json(res)
    print('Invocation result:', res)

    # Log errors in DynamoDB
    if res.status == 'error':
        print('There was an error during test generation:', res.message)
        table.log_error(request.problem, res.message or 'Unknown error during test generation')
        return {
            'statusCode': 500,
            'body': json.dumps({'error': res.message or 'Unknown error during test generation'}),
        }

    return {
        'statusCode': 200,
        'body': res.to_json(),
    }
