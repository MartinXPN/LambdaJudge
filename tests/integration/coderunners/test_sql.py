from textwrap import dedent

from bouncer.coderunners import CodeRunner
from models import Status, SubmissionRequest, TestCase
from tests.integration.config import lambda_client


class TestSQLSubmissions:
    test_cases = [
        TestCase(input=dedent('''
                -- Initialization script goes here
            '''), target='hello world')]

    def test_echo(self):
        request = SubmissionRequest(test_cases=self.test_cases, language='SQL', code={
            'main.sql': dedent('''
                SELECT 'hello world'
            '''.strip()),
        })
        res = CodeRunner.from_language(language=request.language).invoke(lambda_client, request=request)
        print(res)
        assert res.overall.status == Status.OK
        assert res.overall.score == 100
        assert len(res.test_results) == 1
        assert res.test_results[0].status == Status.OK
