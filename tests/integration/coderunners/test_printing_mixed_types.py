from textwrap import dedent

from bouncer.coderunners import CodeRunner
from models import Status, SubmissionRequest, TestCase
from tests.integration.config import lambda_client


class TestMixedTypes:
    test_cases = [TestCase(input='', target='1 2 4 8 16 32 are powers of two')]

    def test_ok(self):
        request = SubmissionRequest(test_cases=self.test_cases, language='python', code={
            'main.py': dedent('''
                print(1, 2, 4, 8, 16, 32, 'are powers of two')
            '''),
        }, return_outputs=True)

        res = CodeRunner.from_language(language=request.language).invoke(lambda_client, request=request)
        print(res)
        assert res.overall.status == Status.OK
        assert len(res.test_results) == 1 and res.test_results[0].status == Status.OK
