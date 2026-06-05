from textwrap import dedent

from bouncer.coderunners import CodeRunner
from models import Status, SubmissionRequest, TestCase
from tests.integration.config import lambda_client


class TestRust:
    def test_hello_world(self):
        test_cases = [TestCase(input='', target='Hello World!')]
        request = SubmissionRequest(test_cases=test_cases, language='rust', code={
            'main.rs': dedent('''
                fn main() {
                    print!("Hello World!");
                }
            ''').strip(),
        })
        res = CodeRunner.from_language(language=request.language).invoke(lambda_client, request=request)
        print(res)
        assert res.overall.status == Status.OK
        assert res.test_results is not None and len(res.test_results) == 1 and res.test_results[0].status == Status.OK

    def test_mixed_type_output(self):
        test_cases = [TestCase(input='', target='1 2 4 8 16 32 are powers of two')]
        request = SubmissionRequest(test_cases=test_cases, language='rust', code={
            'main.rs': dedent('''
                fn main() {
                    print!("{} {} {} {} {} {} {}", 1, 2, 4, 8, 16, 32, "are powers of two");
                }
            ''').strip(),
        }, return_outputs=True)
        res = CodeRunner.from_language(language=request.language).invoke(lambda_client, request=request)
        print(res)
        assert res.overall.status == Status.OK
        assert res.test_results is not None and len(res.test_results) == 1 and res.test_results[0].status == Status.OK
        assert res.test_results[0].outputs.strip() == '1 2 4 8 16 32 are powers of two'

    def test_compile_error(self):
        request = SubmissionRequest(test_cases=[], language='rust', code={
            'main.rs': dedent('''
                fn main() {
                    let value: i32 = "Hello World!";
                    print!("{}", value);
                }
            ''').strip(),
        })
        res = CodeRunner.from_language(language=request.language).invoke(lambda_client, request=request)
        print(res)
        assert res.overall.status == Status.COMPILATION_ERROR
        assert res.compile_result.status == Status.COMPILATION_ERROR

    def test_input_output_echo(self):
        test_cases = [TestCase(input='Hello World!', target='Hello World!')]
        request = SubmissionRequest(test_cases=test_cases, language='rust', code={
            'main.rs': dedent('''
                use std::io::{self, Read};

                fn main() {
                    let mut input = String::new();
                    io::stdin().read_to_string(&mut input).unwrap();
                    print!("{}", input.trim_end());
                }
            ''').strip(),
        }, return_outputs=True)
        res = CodeRunner.from_language(language=request.language).invoke(lambda_client, request=request)
        print(res)
        assert res.overall.status == Status.OK
        assert res.test_results is not None and len(res.test_results) == 1 and res.test_results[0].status == Status.OK
        assert res.test_results[0].outputs.strip() == 'Hello World!'

    def test_multi_file(self):
        test_cases = [TestCase(input='', target='2')]
        request = SubmissionRequest(test_cases=test_cases, language='rust', code={
            'main.rs': dedent('''
                mod dir;
                mod ones;

                fn main() {
                    print!("{}", dir::code::one() + dir::code::one());
                }
            ''').strip(),
            'ones.rs': dedent('''
                pub fn ret_one() -> i32 {
                    1
                }
            ''').strip(),
            'dir': {
                'mod.rs': 'pub mod code;',
                'code.rs': dedent('''
                    use crate::ones;

                    pub fn one() -> i32 {
                        ones::ret_one()
                    }
                ''').strip(),
            },
        }, return_outputs=True)
        res = CodeRunner.from_language(language=request.language).invoke(lambda_client, request=request)
        assert res.overall.status == Status.OK
        assert res.test_results is not None and len(res.test_results) == 1 and res.test_results[0].status == Status.OK
        assert res.test_results[0].outputs.strip() == '2'
