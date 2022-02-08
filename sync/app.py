import json
from pathlib import Path

import boto3

ROOT = Path('/tmp/')
s3 = boto3.resource('s3')
secret_manager = boto3.client('secretsmanager')
encryption_secret_key_id = 'arn:aws:secretsmanager:us-east-1:370358067229:secret:efs/problem/encryptionKey-xTnJWC'


def sync_handler(event, context):
    print('Event:', type(event), event)
    print('Context:', context)

    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']  # some-bucket/some-folder/img.jpg
    problem = key.split('.')[0]
    problem_file = f'/mnt/efs/{problem}.gz.fer'
    zip_path = ROOT / f'{problem}.zip'
    print('problem_file', problem_file, 'zip:', zip_path)

    res = s3.Bucket(bucket).download_file(key, str(zip_path))
    print('result:', res)

    print('getting secrets...')
    get_secret_value_response = secret_manager.get_secret_value(SecretId=encryption_secret_key_id)
    print('got response:', get_secret_value_response)
    secrets = json.loads(get_secret_value_response['SecretString'])
    print('secrets:', secrets)
    encryption_key = secrets['EFS_PROBLEMS_ENCRYPTION_KEY']
    print('encryption_key', encryption_key)

    zip_path.unlink(missing_ok=True)
    return {
        'status_code': 200
    }
