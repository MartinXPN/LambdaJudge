from textwrap import dedent

from bouncer.coderunners import CodeRunner
from models import Status, SubmissionRequest, TestCase
from tests.integration.config import lambda_client


class TestCustomChecker:
    test_cases = [TestCase(input='', target='hello')]

    def test_checker_compilation(self):
        error = SubmissionRequest(test_cases=self.test_cases, language='python', code={
            'main.py': 'print("hello")',
        }, comparison_mode='custom', checker_language='python', checker_code={
            'checker.py': ' print("Solved\\n100\\n")',
        })
        ok = SubmissionRequest(test_cases=self.test_cases, language='python', code={
            'main.py': 'print("hello")',
        }, comparison_mode='custom', checker_language='python', checker_code={
            'checker.py': 'print("Solved\\n100\\n")',
        })

        res = CodeRunner.from_language(language=error.language).invoke(lambda_client, request=error)
        print(res)
        assert res.overall.status == Status.COMPILATION_ERROR
        assert res.compile_result.status == Status.COMPILATION_ERROR
        assert res.overall.message == 'Checker compilation failed'
        assert res.compile_result.message == 'Checker compilation failed'

        res = CodeRunner.from_language(language=ok.language).invoke(lambda_client, request=ok)
        print(res)
        assert res.overall.status == Status.OK
        assert res.compile_result.status == Status.OK

    def test_error(self):
        requests = [
            SubmissionRequest(test_cases=self.test_cases, language='python', code={
                'main.py': 'print("hello")',
            }, comparison_mode='custom', checker_language='python', checker_code={
                'checker.py': 'a = 10',
            }),
            SubmissionRequest(test_cases=self.test_cases, language='C++17', code={
                'main.cpp': '#include <iostream>\nint main() { std::cout << "hello"; return 0; }',
            }, comparison_mode='custom', checker_language='python', checker_code={
                'checker.py': 'print("line1\\nline2\\nline3\\nline4\\nline5")',
            }),
            SubmissionRequest(test_cases=self.test_cases, language='python', code={
                'main.py': 'print("hello")',
            }, comparison_mode='custom', checker_language='python', checker_code={
                'checker.py': 'print("Weird status\\n100\\nSome message here")',
            }),
        ]

        for i, request in enumerate(requests):
            res = CodeRunner.from_language(language=request.language).invoke(lambda_client, request=request)
            print(res)
            assert res.overall.status == Status.RUNTIME_ERROR
            assert res.test_results[0].status == Status.RUNTIME_ERROR
            if i == 0:
                assert 'Checker failed to produce status and score' in res.test_results[0].message
            elif i == 1:
                assert res.test_results[0].message == 'Checker did not produce a valid score value'
            elif i == 2:
                assert res.test_results[0].message == 'Checker did not produce a valid status'

    def test_ok(self):
        checker_code = dedent("""
            import sys
            executable_path, input_file, output_file, target_file, submission_dir = sys.argv
            #
            with open(input_file, 'r') as fin, open(output_file, 'r') as fout, open(target_file, 'r') as tgt:
                input_data = fin.read()
                output_data = fout.read()
                target_data = tgt.read()
            #
            if output_data.strip() == target_data.strip():
                print('Solved\\n90\\nGood job!\\n')
            else:
                print('Wrong answer\\n0\\nTry again...\\n')
            print(input_data)
            print(output_data)
            print(target_data)
            print(sys.argv)
            """).strip()
        requests = [
            SubmissionRequest(test_cases=self.test_cases, language='python', code={
                'main.py': 'print("hello world")',
            }, comparison_mode='custom', checker_language='python', checker_code={'checker.py': checker_code}),
            SubmissionRequest(test_cases=self.test_cases, language='python', code={
                'main.py': 'print("hello")',
            }, comparison_mode='custom', checker_language='python', checker_code={'checker.py': checker_code}),
            SubmissionRequest(test_cases=self.test_cases, language='C++17', code={
                'main.cpp': '#include <iostream>\nint main() { std::cout << "hello"; return 0; }',
            }, comparison_mode='custom', checker_language='python', checker_code={'checker.py': checker_code}),
        ]

        for i, request in enumerate(requests):
            res = CodeRunner.from_language(language=request.language).invoke(lambda_client, request=request)
            print(res)
            if i == 0:
                assert res.overall.status == Status.WA
                assert res.compile_result.status == Status.OK
            else:
                assert res.overall.status == Status.OK
                assert res.overall.score == 90
                assert res.compile_result.status == Status.OK

    def test_with_status_string(self):
        checker_code = dedent("""
            import sys
            executable_path, input_file, output_file, target_file, submission_dir = sys.argv
            status = input()
            #
            with open(input_file, 'r') as fin, open(output_file, 'r') as fout, open(target_file, 'r') as tgt:
                input_data = fin.read()
                output_data = fout.read()
                target_data = tgt.read()
            #
            if output_data.strip() == target_data.strip():
                print(f'{status} Solved')
                print(f'{status} 90')
                print('Good job!')
            else:
                print(f'{status} Wrong answer')
                print(f'{status} 0')
                print('Try again...')
            print(input_data)
            print(output_data)
            print(target_data)
            print(sys.argv)
            """).strip()
        requests = [
            SubmissionRequest(test_cases=self.test_cases, language='python', code={
                'main.py': 'print("hello world")',
            }, comparison_mode='custom', checker_language='python', checker_code={'checker.py': checker_code}),
            SubmissionRequest(test_cases=self.test_cases, language='python', code={
                'main.py': 'print("hello")',
            }, comparison_mode='custom', checker_language='python', checker_code={'checker.py': checker_code}),
            SubmissionRequest(test_cases=self.test_cases, language='C++17', code={
                'main.cpp': '#include <iostream>\nint main() { std::cout << "hello"; return 0; }',
            }, comparison_mode='custom', checker_language='python', checker_code={'checker.py': checker_code}),
        ]

        for i, request in enumerate(requests):
            res = CodeRunner.from_language(language=request.language).invoke(lambda_client, request=request)
            print(res)
            if i == 0:
                assert res.overall.status == Status.WA
                assert res.compile_result.status == Status.OK
            else:
                assert res.overall.status == Status.OK
                assert res.overall.score == 90
                assert res.compile_result.status == Status.OK
