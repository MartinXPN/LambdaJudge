import boto3
import botocore

lambda_client = boto3.client(
    'lambda',
    region_name='us-east-1',
    endpoint_url='http://127.0.0.1:3001',
    use_ssl=False,
    verify=False,
    config=botocore.client.Config(
        signature_version=botocore.UNSIGNED,
        retries={'max_attempts': 0},
        read_timeout=300,
        connect_timeout=300,
    )
)
