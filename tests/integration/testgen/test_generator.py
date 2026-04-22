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
        assert response.message and 'SyntaxError' in response.message

    def test_generate_both_tests(self):
        """
        Given a string `s`,
        you would like to calculate the number of substrings that have an odd number of vowels (a, e, i, o, u, and y).


        ### Input
        The input contains a single string `s` (1 ≤ |s| ≤ 100).

        ### Output
        The program should print the number of substrings that have an odd number of vowels.

        ### Examples
        | Input | Output |
        | --- | --- |
        | abc | 3 |
        | hello | 7 |
        | xyz | 0 |


        ### Explanation
        1. abc → a, ab, abc
        2. hello → he, el, lo, hel, ell, llo, hell
        """
        code = dedent(
            '''
            import string
            from pathlib import Path
            from base import BaseTestGen


            class CountVowels(BaseTestGen):
                @staticmethod
                def solve(s: str) -> dict[str, str]:
                    count = 0
                    for i in range(len(s)):
                        for j in range(i + 1, len(s) + 1):
                            vowels = s[i:j].count('a') + s[i:j].count('e') + s[i:j].count('i') + \
                                s[i:j].count('o') + s[i:j].count('u') + s[i:j].count('y')
                            if vowels % 2 == 1:
                                count += 1

                    return {
                        'input': s,
                        'target': str(count)
                    }

                def generate_public_tests(self) -> list[dict[str, str]]:
                    return [self.solve('abc'), self.solve('hello'), self.solve('xyz')]

                def generate_private_tests(self) -> list[dict[str, str]]:
                    results = []
                    for ns, tests in [(10, 10), (20, 5), (50, 5), (100, 10)]:
                        for _ in range(tests):
                            s = ''.join(self.rand.choices(string.ascii_lowercase, k=ns))
                            results.append(self.solve(s))
                    return results


            if __name__ == '__main__':
                gen = CountVowels()
                gen.print_tests()
                gen.zip(Path('/tmp/tests'), include_public_tests=True)
            '''
        ).strip()

        response = self.invoke(lambda_client, TestGenRequest(
            problem=self.problem,
            language='python',
            code={'main.py': code},
        ))

        assert response.status == 'success', response.message
