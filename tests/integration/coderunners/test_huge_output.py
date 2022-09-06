from textwrap import dedent

from bouncer.coderunners import CodeRunner
from models import Status, SubmissionRequest, TestCase
from tests.integration.config import lambda_client


class TestHugeOutput:
    test_cases = [TestCase(input='hello', target='hello')]

    def test_return_size(self):
        request = SubmissionRequest(test_cases=self.test_cases, language='python', code={
            'main.py': dedent('''
                n = 0
                while True:
                    n += 1
                    print(n)
            '''),
        }, return_outputs=True)

        res = CodeRunner.from_language(language=request.language).invoke(lambda_client, request=request)
        print(res)
        assert res.overall.status in {Status.OLE, Status.TLE}
        assert len(res.test_results) == 1 and res.test_results[0].status in {Status.OLE, Status.TLE}
        assert len(res.test_results[0].outputs) <= 32000
