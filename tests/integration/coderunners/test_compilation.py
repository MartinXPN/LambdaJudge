from textwrap import dedent

from bouncer.coderunners import CodeRunner
from models import Status, SubmissionRequest, TestCase
from tests.integration.config import lambda_client


class TestCompileError:
    test_cases = [TestCase(input='', target='hello')]

    def test_error(self):
        requests = [
            SubmissionRequest(test_cases=self.test_cases, language='python', code={
                'main.py': ' print("hello")',
            }),
            SubmissionRequest(test_cases=self.test_cases, language='C++20', code={
                'main.cpp': 'int main() { cout << "hello"; return 0; }',
            }),
            SubmissionRequest(test_cases=self.test_cases, language='Java', time_limit=2, code={
                'main.java': dedent('''
                    class Main {
                        public static void main(String[] args) {
                            System.out.println("hello")
                        }
                    }
                ''')
            }),
        ]

        for request in requests:
            res = CodeRunner.from_language(language=request.language).invoke(lambda_client, request=request)
            print(res)
            assert res.overall.status == Status.COMPILATION_ERROR
            assert res.compile_result.status == Status.COMPILATION_ERROR
            assert res.overall.errors is not None

    def test_ok(self):
        requests = [
            SubmissionRequest(test_cases=self.test_cases, language='python', code={
                'main.py': 'print("hello")',
            }),
            SubmissionRequest(test_cases=self.test_cases, language='C++20', code={
                'main.cpp': '#include <iostream>\nint main() { std::cout << "hello"; return 0; }',
            }),
            SubmissionRequest(test_cases=self.test_cases, language='Java', time_limit=2, code={
                'main.java': dedent('''
                class Main {
                    public static void main(String[] args) {
                        System.out.println("hello");
                    }
                }
            ''')
            }),
        ]

        for request in requests:
            res = CodeRunner.from_language(language=request.language).invoke(lambda_client, request=request)
            print(res)
            assert res.overall.status != Status.COMPILATION_ERROR
            assert res.compile_result.status != Status.COMPILATION_ERROR
