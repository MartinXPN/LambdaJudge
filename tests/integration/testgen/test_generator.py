import json
from textwrap import dedent

import boto3

from models import TestGenRequest, TestGenResponse
from testgen.bouncer_app import assume_upload_role
from tests.integration.config import lambda_client


class TestGenerator:
    function_name = 'TestGenerator'
    bucket_name = 'lambda-judge-tests-bucket'

    def invoke(self, aws_lambda_client, request: TestGenRequest) -> TestGenResponse:
        request.credentials = assume_upload_role(bucket=self.bucket_name, key=f'{request.problem}.zip')
        res = aws_lambda_client.invoke(FunctionName=self.function_name, Payload=request.to_json())['Payload']
        res = res.read().decode('utf-8')
        res = json.loads(res)
        print('invocation result:', res)
        return TestGenResponse.from_json(res)

    def test_generate_tests(self):
        problem = 'test-test-test'
        code = dedent(
            '''
            from pathlib import Path
            from base import BaseTestGen, TestCase

            class MyGen(BaseTestGen):
                def generate_public_tests(self):
                    return [TestCase(
                        input='1 2',
                        target='3',
                    )]

                def generate_private_tests(self):
                    return []

            if __name__ == '__main__':
                # BaseTestGen.zip(root) will create root and root.zip
                MyGen().zip(Path('/tmp/tests'), include_public_tests=True)
            '''
        ).strip()

        response = self.invoke(lambda_client, TestGenRequest(
            problem=problem,
            language='python',
            code={'main.py': code},
        ))

        assert response.status == 'success', response.message

        # Assert the ZIP landed in S3
        s3_client = boto3.client('s3', region_name='us-east-1')
        s3_obj = s3_client.get_object(Bucket=self.bucket_name, Key=f'{problem}.zip')
        body = s3_obj['Body'].read()
        print('S3 Body:', body)
        assert len(body) > 0
