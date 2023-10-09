from bouncer.coderunners import CodeRunner
from models import Status, SubmissionRequest, TestCase
from tests.integration.config import lambda_client


class TestEscapeCharacters:

    def test_plain_text(self):
        request = SubmissionRequest(test_cases=[TestCase(input='', target='hello')], language='txt', code={
            'main.txt': 'hello',
        })

        res = CodeRunner.from_language(language=request.language).invoke(lambda_client, request=request)
        print(res)
        assert res.overall.status == Status.OK
        assert len(res.test_results) == 1 and res.test_results[0].status == Status.OK

    def test_escape_text(self):
        request = SubmissionRequest(test_cases=[TestCase(input='', target='h\'ell"o')], language='txt', code={
            'main.txt': 'h\'ell"o',
        })

        res = CodeRunner.from_language(language=request.language).invoke(lambda_client, request=request)
        print(res)
        assert res.overall.status == Status.OK
        assert len(res.test_results) == 1 and res.test_results[0].status == Status.OK

    def test_program(self):
        request = SubmissionRequest(test_cases=[
            TestCase(input='', target="""'import os; os.system("rm -rf /")"""),
        ], language='txt', code={
            'main.txt': """'import os; os.system("rm -rf /")""",
        })

        res = CodeRunner.from_language(language=request.language).invoke(lambda_client, request=request)
        print(res)
        assert res.overall.status == Status.OK
        assert len(res.test_results) == 1 and res.test_results[0].status == Status.OK

    def test_multiline_text(self):
        request = SubmissionRequest(test_cases=[
            TestCase(input='', target='line1\nline2\nline3\n')
        ], language='txt', code={'main.txt': 'line1\nline2\nline3\n'})

        res = CodeRunner.from_language(language=request.language).invoke(lambda_client, request=request)
        print(res)
        assert res.overall.status == Status.OK
        assert len(res.test_results) == 1 and res.test_results[0].status == Status.OK

    def test_empty_target(self):
        request = SubmissionRequest(test_cases=[TestCase(input='', target='')], language='txt', code={'main.txt': ''})

        res = CodeRunner.from_language(language=request.language).invoke(lambda_client, request=request)
        print(res)
        assert res.overall.status == Status.OK
        assert len(res.test_results) == 1 and res.test_results[0].status == Status.OK

    def test_whitespace(self):
        request = SubmissionRequest(test_cases=[
            TestCase(input='', target=' \t\n \t\t\n')
        ], language='txt', code={'main.txt': ' \t\n \t\t\n'})

        res = CodeRunner.from_language(language=request.language).invoke(lambda_client, request=request)
        print(res)
        assert res.overall.status == Status.OK
        assert len(res.test_results) == 1 and res.test_results[0].status == Status.OK

    def test_special_chars(self):
        request = SubmissionRequest(test_cases=[TestCase(input='', target='\\ \n ❤️🚀')], language='txt', code={
            'main.txt': '\\ \n ❤️🚀',
        })

        res = CodeRunner.from_language(language=request.language).invoke(lambda_client, request=request)
        print(res)
        assert res.overall.status == Status.OK
        assert len(res.test_results) == 1 and res.test_results[0].status == Status.OK

    def test_mismatch(self):
        request = SubmissionRequest(test_cases=[TestCase(input='', target='helloo')], language='txt', code={
            'main.txt': 'hello',
        })

        res = CodeRunner.from_language(language=request.language).invoke(lambda_client, request=request)
        print(res)
        assert res.overall.status == Status.WA
        assert len(res.test_results) == 1 and res.test_results[0].status == Status.WA
