from textwrap import dedent

from bouncer.coderunners import CodeRunner
from models import Status, SubmissionRequest, TestCase
from tests.integration.config import lambda_client


class TestTLE:
    test_cases = [TestCase(input='hello', target='hello')]

    def test_return_size(self):
        request = SubmissionRequest(test_cases=self.test_cases, language='python', code={
            'main.py': dedent('''
                print('hello')
                while True:
                    pass
            '''),
        }, time_limit=1, return_outputs=True)

        res = CodeRunner.from_language(language=request.language).invoke(lambda_client, request=request)
        print(res)
        assert res.overall.status == Status.TLE
        assert len(res.test_results) == 1 and res.test_results[0].status == Status.TLE
