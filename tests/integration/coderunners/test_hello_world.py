from textwrap import dedent

from bouncer.coderunners import CodeRunner
from models import Status, SubmissionRequest, SubmissionResult, TestCase
from tests.integration.config import lambda_client


class TestHelloWorld:
    test_cases = [TestCase(input='', target='Hello World!')]

    @staticmethod
    def run_test(request: SubmissionRequest) -> SubmissionResult:
        res = CodeRunner.from_language(language=request.language).invoke(lambda_client, request=request)
        print(res)
        assert res.overall.status == Status.OK
        assert len(res.test_results) == 1 and res.test_results[0].status == Status.OK
        return res

    def test_txt(self):
        self.run_test(SubmissionRequest(test_cases=self.test_cases, language='txt', code={
            'main.txt': 'Hello World!',
        }))

    def test_python(self):
        self.run_test(SubmissionRequest(test_cases=self.test_cases, language='python', code={
            'main.py': 'print("Hello World!")',
        }))

    def test_python_ml(self):
        self.run_test(SubmissionRequest(test_cases=self.test_cases, language='pythonml', code={
            'main.py': 'import numpy as np\nprint("Hello World!")',
        }))

    def test_c(self):
        self.run_test(SubmissionRequest(test_cases=self.test_cases, language='c', code={
            'main.c': '#include <stdio.h>\nint main() { printf("Hello World!"); return 0; }',
        }))

    def test_cpp(self):
        self.run_test(SubmissionRequest(test_cases=self.test_cases, language='C++17', code={
            'main.cpp': '#include <iostream>\nint main() { std::cout << "Hello World!"; return 0; }',
        }))

    def test_js(self):
        self.run_test(SubmissionRequest(test_cases=self.test_cases, language='js', code={
            'main.js': 'console.log(\'Hello World!\')',
        }))

    def test_csharp(self):
        self.run_test(SubmissionRequest(test_cases=self.test_cases, language='C#', time_limit=10, code={
            'main.cs': 'System.Console.WriteLine("Hello World!");',
        }))

    def test_java(self):
        self.run_test(SubmissionRequest(test_cases=self.test_cases, language='Java', time_limit=2, code={
            'main.java': dedent('''
                class Main {
                    public static void main(String[] args) {
                        System.out.println("Hello World!");
                    }
                }
            ''')
        }))
