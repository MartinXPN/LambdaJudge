from textwrap import dedent

from bouncer.coderunners import CodeRunner
from models import SubmissionRequest, TestCase, Status
from tests.integration.config import lambda_client


class TestMemoryLimit:
    test_cases = [TestCase(input='', target='Watch the limits!')]

    def test_exceeds(self):
        request = SubmissionRequest(test_cases=self.test_cases, language='python', memory_limit=256, code={
            'main.py': dedent("""
                a = []
                for i in range(1000000):
                    a.append(bytearray(37159444))
                print('Watch the limits!')
            """),
        })

        res = CodeRunner.from_language(language=request.language).invoke(lambda_client, request=request)
        print(res)
        assert res.overall.status == Status.MLE
        assert res.compile_result.status == Status.OK
        assert len(res.test_results) == 1 and res.test_results[0].status == Status.MLE

    def test_ok(self):
        request = SubmissionRequest(test_cases=self.test_cases, language='python', memory_limit=256, code={
            'main.py': dedent("""
            a = []
            for i in range(2):
                a.append(bytearray(37159444))
            print('Watch the limits!')
            """),
        })

        res = CodeRunner.from_language(language=request.language).invoke(lambda_client, request=request)
        print(res)
        assert res.overall.status == Status.OK
        assert res.compile_result.status == Status.OK
        assert len(res.test_results) == 1 and res.test_results[0].status == Status.OK
