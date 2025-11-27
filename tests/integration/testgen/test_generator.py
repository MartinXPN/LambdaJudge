import json
from textwrap import dedent

from models import TestGenRequest, TestGenResponse
from tests.integration.config import lambda_client


class TestGenerator:
    function_name = 'TestGenerator'
    bucket_name = 'lambda-judge-tests-bucket'
    problem = 'test-test-test'

    def invoke(self, aws_lambda_client, request: TestGenRequest) -> TestGenResponse:
        res = aws_lambda_client.invoke(FunctionName=self.function_name, Payload=request.to_json())['Payload']
        res = res.read().decode('utf-8')
        res = json.loads(res)
        print('invocation result:', res)
        return TestGenResponse.from_json(res)

    def test_generate_tests(self):
        code = dedent(
            '''
            from pathlib import Path
            from base import BaseTestGen

            class MyGen(BaseTestGen):
                def generate_public_tests(self):
                    return [{
                        'input': '1 2',
                        'target': '3',
                    }]

                def generate_private_tests(self):
                    return []

            if __name__ == '__main__':
                # BaseTestGen.zip(root) will create root and root.zip
                MyGen().zip(Path('/tmp/tests'), include_public_tests=True)
            '''
        ).strip()

        response = self.invoke(lambda_client, TestGenRequest(
            problem=self.problem,
            language='python',
            code={'main.py': code},
        ))

        assert response.status == 'success', response.message

    def test_compilation_error(self):
        code = dedent(
            '''
            from pathlib import Path
            from base import BaseTestGen

            class MyGen(BaseTestGen) error_error
                def generate_public_tests(self):
                    return [{
                        'input': '1 2',
                        'target': '3',
                    }]

                def generate_private_tests(self):
                    return []

            if __name__ == '__main__':
                MyGen().zip(Path('/tmp/tests'), include_public_tests=True)
            '''
        ).strip()

        response = self.invoke(lambda_client, TestGenRequest(
            problem=self.problem,
            language='python',
            code={'main.py': code},
        ))

        assert response.status == 'error'
        assert 'SyntaxError' in response.message
