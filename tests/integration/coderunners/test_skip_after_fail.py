from textwrap import dedent

from bouncer.coderunners import CodeRunner
from models import Status, SubmissionRequest, TestCase
from tests.integration.config import lambda_client


class TestMemoryLimit:
    test_cases = [
        TestCase(input='', target='Correct!'),
        TestCase(input='', target='Incorrect!'),
        TestCase(input='', target='Skipped!'),
    ]

    def test_skip(self):
        request = SubmissionRequest(test_cases=self.test_cases, language='python', memory_limit=256, code={
            'main.py': 'print("Correct!")',
        }, stop_on_first_fail=True)

        res = CodeRunner.from_language(language=request.language).invoke(lambda_client, request=request)
        print(res)
        assert res.overall.status == Status.WA
        assert res.test_results[0].status == Status.OK
        assert res.test_results[1].status == Status.WA
        assert res.test_results[2].status == Status.SKIPPED

    def test_no_skip(self):
        request = SubmissionRequest(test_cases=self.test_cases, language='python', memory_limit=256, code={
            'main.py': 'print("Correct!")',
        }, stop_on_first_fail=False)

        res = CodeRunner.from_language(language=request.language).invoke(lambda_client, request=request)
        print(res)
        assert res.overall.status == Status.WA
        assert res.test_results[0].status == Status.OK
        assert res.test_results[1].status == Status.WA
        assert res.test_results[2].status == Status.WA
