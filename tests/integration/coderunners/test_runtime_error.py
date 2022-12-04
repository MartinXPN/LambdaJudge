from bouncer.coderunners import CodeRunner
from models import Status, SubmissionRequest, TestCase
from tests.integration.config import lambda_client


class TestRuntimeError:
    test_cases = [TestCase(input='', target='hello')]

    def test_error(self):
        requests = [
            SubmissionRequest(test_cases=self.test_cases, language='C++17', code={
                'main.cpp': 'int main() { int a[10]; a[15] = 100; return 0; }',
            }),
        ]

        for request in requests:
            res = CodeRunner.from_language(language=request.language).invoke(lambda_client, request=request)
            print(res)
            assert res.overall.status == Status.RUNTIME_ERROR
            assert res.compile_result.status == Status.OK

    def test_ok(self):
        requests = [
            SubmissionRequest(test_cases=self.test_cases, language='C++17', code={
                'main.cpp': 'int main() { int a[10]; a[0] = 100; return 0; }',
            }),
        ]

        for request in requests:
            res = CodeRunner.from_language(language=request.language).invoke(lambda_client, request=request)
            print(res)
            assert res.overall.status != Status.RUNTIME_ERROR
