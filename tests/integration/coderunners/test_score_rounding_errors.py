from bouncer.coderunners import CodeRunner
from models import Status, SubmissionRequest, TestCase
from tests.integration.config import lambda_client


class TestScoreRoundingErrors:
    test_cases = [TestCase(input='', target='yes') for _ in range(7)]

    def test_exact_numbers(self):
        request = SubmissionRequest(test_cases=self.test_cases, return_outputs=True, language='python', code={
            'main.py': 'print("yes")',
        })

        res = CodeRunner.from_language(language=request.language).invoke(lambda_client, request=request)
        print(res)
        assert res.overall.status == Status.OK
        assert res.overall.score == 100
