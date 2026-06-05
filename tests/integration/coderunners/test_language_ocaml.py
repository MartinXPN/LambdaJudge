from textwrap import dedent

from bouncer.coderunners import CodeRunner
from models import Status, SubmissionRequest, TestCase
from tests.integration.config import lambda_client


class TestOcaml:
    def test_hello_world(self):
        test_cases = [TestCase(input='', target='Hello World!')]
        request = SubmissionRequest(test_cases=test_cases, language='ocaml', code={
            'main.ml': 'print_string "Hello World!"',
        })
        res = CodeRunner.from_language(language=request.language).invoke(lambda_client, request=request)
        print(res)
        assert res.overall.status == Status.OK
        assert res.test_results is not None and len(res.test_results) == 1 and res.test_results[0].status == Status.OK

    def test_mixed_type_output(self):
        test_cases = [TestCase(input='', target='1 2 4 8 16 32 are powers of two')]
        request = SubmissionRequest(test_cases=test_cases, language='ml', code={
            'main.ml': dedent('''
                let values = [1; 2; 4; 8; 16; 32]
                let rendered = values |> List.map string_of_int |> String.concat " "
                let () = print_string (rendered ^ " are powers of two")
            ''').strip(),
        }, return_outputs=True)
        res = CodeRunner.from_language(language=request.language).invoke(lambda_client, request=request)
        print(res)
        assert res.overall.status == Status.OK
        assert res.test_results is not None and len(res.test_results) == 1 and res.test_results[0].status == Status.OK
        assert res.test_results[0].outputs.strip() == '1 2 4 8 16 32 are powers of two'

    def test_compile_error(self):
        request = SubmissionRequest(test_cases=[], language='ml', code={
            'main.ml': dedent('''
                let value : int = "Hello World!"
                let () = print_int value
            ''').strip(),
        })
        res = CodeRunner.from_language(language=request.language).invoke(lambda_client, request=request)
        print(res)
        assert res.overall.status == Status.COMPILATION_ERROR
        assert res.compile_result.status == Status.COMPILATION_ERROR

    def test_input_output_echo(self):
        test_cases = [TestCase(input='Hello World!', target='Hello World!')]
        request = SubmissionRequest(test_cases=test_cases, language='ml', code={
            'main.ml': dedent('''
                let () =
                  try
                    let input = input_line stdin in
                    print_string input
                  with End_of_file -> ()
            ''').strip(),
        }, return_outputs=True)
        res = CodeRunner.from_language(language=request.language).invoke(lambda_client, request=request)
        print(res)
        assert res.overall.status == Status.OK
        assert res.test_results is not None and len(res.test_results) == 1 and res.test_results[0].status == Status.OK
        assert res.test_results[0].outputs.strip() == 'Hello World!'

    def test_multi_file(self):
        test_cases = [TestCase(input='', target='2')]
        request = SubmissionRequest(test_cases=test_cases, language='ml', code={
            'main.ml': dedent('''
                let () = print_int (Code.one () + Code.one ())
            ''').strip(),
            'ones.mli': 'val ret_one : unit -> int',
            'ones.ml': dedent('''
                let ret_one () = 1
            ''').strip(),
            'dir': {
                'code.ml': dedent('''
                    let one () = Ones.ret_one ()
                ''').strip(),
            },
        }, return_outputs=True)
        res = CodeRunner.from_language(language=request.language).invoke(lambda_client, request=request)
        assert res.overall.status == Status.OK
        assert res.test_results is not None and len(res.test_results) == 1 and res.test_results[0].status == Status.OK
        assert res.test_results[0].outputs.strip() == '2'
