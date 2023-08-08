from bouncer.coderunners import CodeRunner
from models import Status, SubmissionRequest
from tests.integration.config import lambda_client


class TestNoInputs:
    def test_resolve_successfully(self):
        request = SubmissionRequest(test_cases=[], return_outputs=True, language='python', code={
            'main.py': 'print("yes")',
        })

        res = CodeRunner.from_language(language=request.language).invoke(lambda_client, request=request)
        print(res)
        assert res.overall.status == Status.OK
        assert len(res.test_results) == 1 and res.test_results[0].status == Status.OK
        assert res.test_results[0].outputs.strip() == 'yes'

    def test_resolve_error(self):
        request = SubmissionRequest(test_cases=[], language='python', code={
            'main.py': ' print("yes")',
        })

        res = CodeRunner.from_language(language=request.language).invoke(lambda_client, request=request)
        print(res)
        assert res.overall.status == Status.COMPILATION_ERROR
