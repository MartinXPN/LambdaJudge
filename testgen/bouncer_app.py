import json

import boto3
from botocore.config import Config

from models import TestGenRequest, TestGenResponse

aws_lambda = boto3.client('lambda', config=Config(retries={'max_attempts': 0}, read_timeout=360, connect_timeout=360))
dynamodb = boto3.resource('dynamodb')
s3 = boto3.client('s3')


def handler(event, context):
    """
    Bouncer that takes the request and triggers the generator lambda
    """
    print('Event:', type(event), event)
    print('Context:', context)
    request = TestGenRequest.from_json(event['body'])
    print('All the params:', request)

    # Trigger the generator lambda
    res = aws_lambda.invoke(FunctionName='TestGenerator', Payload=request.to_json())['Payload']
    res = res.read().decode('utf-8')
    res = json.loads(res)
    res = TestGenResponse.from_json(res)
    print('Invocation result:', res)

    # TODO: Write to DynamoDB to track the status of test generation

    return {
        'statusCode': 200,
        'body': res.to_json(),
    }
