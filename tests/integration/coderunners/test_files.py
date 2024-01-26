from textwrap import dedent

from bouncer.coderunners import CodeRunner
from models import Status, SubmissionRequest, TestCase
from tests.integration.config import lambda_client


class TestFiles:
    test_cases = [
        TestCase(input='1', target='2', input_files={'hello.txt': 'hello'}, target_files={'hello.txt': 'hello'}),
        TestCase(input='2', target='4', input_files={'hello.txt': 'hello'}, target_files={'hello.txt': 'hello'}),
        TestCase(input='3', target='4', input_files={'hello.txt': 'hello'}, target_files={'res.txt': 'heyhey'}),
        TestCase(input='4', target='5', input_files={'hello.txt': 'hello'}, target_files={'res.txt': 'heyhey'},
                 input_assets={'img.bmp': b'image!'}, target_assets={'res.bmp': b'Result!!!'}),
        TestCase(input='5', target='6',
                 input_files={'hello.txt': 'hello',
                              'subfolder/hey.txt': 'hello hello',
                              'subfolder/subsubfolder/greetings.txt': 'welcome'},
                 target_files={'res.txt': 'heyhey',
                               'subfolder/hey.txt': 'hello hello',
                               'subfolder/subsubfolder/greetings.txt': 'welcome',
                               'subfolder/subsubfolder/res.txt': 'Result!!!'}),
    ]

    def test_no_file(self):
        request = SubmissionRequest(test_cases=self.test_cases, stop_on_first_fail=False, language='python', code={
            'main.py': dedent('''
                n = int(input())
                print(n + 1)
            '''),
        })
        res = CodeRunner.from_language(language=request.language).invoke(lambda_client, request=request)
        print(res)
        assert res.overall.status == Status.WA
        assert len(res.test_results) == 5
        assert res.test_results[0].status == Status.OK
        assert res.test_results[1].status == Status.WA
        assert res.test_results[2].status == Status.WA
        assert res.test_results[3].status == Status.WA

    def test_with_file(self):
        request = SubmissionRequest(test_cases=self.test_cases, stop_on_first_fail=False, language='python', code={
            'main.py': dedent('''
                from pathlib import Path
                n = int(input())
                print(n + 1)
                Path('res.txt').write_text('heyhey')
                # Create a subfolder and subsubfolder and write to the corresponding files
                Path('subfolder/subsubfolder').mkdir(parents=True, exist_ok=True)
                Path('subfolder/hey.txt').write_text('hello hello')
                Path('subfolder/subsubfolder/res.txt').write_text('Result!!!')
                # print(os.getcwd())
            '''),
        }, return_outputs=True)
        res = CodeRunner.from_language(language=request.language).invoke(lambda_client, request=request)
        print(res)
        assert res.overall.status == Status.WA
        assert len(res.test_results) == 5
        assert res.test_results[0].status == Status.OK
        assert res.test_results[1].status == Status.WA
        assert res.test_results[2].status == Status.OK
        assert res.test_results[3].status == Status.WA
        assert res.test_results[4].status == Status.OK

    def test_with_assets(self):
        request = SubmissionRequest(test_cases=self.test_cases, stop_on_first_fail=False, language='python', code={
            'main.py': dedent('''
                n = int(input())
                print(n + 1)
                with open('res.txt', 'w') as f:
                    f.write('heyhey')
                with open('res.bmp', 'wb') as f:
                    f.write(b'Result!!!')
            '''),
        }, return_outputs=True)
        res = CodeRunner.from_language(language=request.language).invoke(lambda_client, request=request)
        print(res)
        assert res.overall.status == Status.WA
        assert len(res.test_results) == 5
        assert res.test_results[0].status == Status.OK
        assert res.test_results[1].status == Status.WA
        assert res.test_results[2].status == Status.OK
        assert res.test_results[3].status == Status.OK
        assert res.test_results[4].status == Status.WA
