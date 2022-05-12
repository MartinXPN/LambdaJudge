from bouncer.coderunners import CodeRunner
from models import SubmissionRequest, TestCase, Status
from tests.integration.config import lambda_client


class TestEcho:
    test_cases = [TestCase(input='hello', target='hello')]

    def test_python_error(self):
        request = SubmissionRequest(test_cases=self.test_cases, language='python', code={
            'main.py': 'a = input(); print("yes")',
        })

        res = CodeRunner.from_language(language=request.language).invoke(lambda_client, request=request)
        print(res)
        assert res.overall.status == Status.WA
        assert len(res.test_results) == 1 and res.test_results[0].status == Status.WA

    def test_python_ok(self):
        request = SubmissionRequest(test_cases=self.test_cases, language='python', code={
            'main.py': 'a = input(); print(a)',
        })

        res = CodeRunner.from_language(language=request.language).invoke(lambda_client, request=request)
        print(res)
        assert res.overall.status == Status.OK
        assert len(res.test_results) == 1 and res.test_results[0].status == Status.OK
