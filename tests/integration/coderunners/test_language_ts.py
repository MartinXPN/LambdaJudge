from textwrap import dedent

from bouncer.coderunners import CodeRunner
from models import Status, SubmissionRequest, TestCase
from tests.integration.config import lambda_client


class TestTypescript:
    def test_hello_world(self):
        test_cases = [TestCase(input='', target='Hello World!')]
        request = SubmissionRequest(test_cases=test_cases, language='typescript', code={
            'index.ts': 'console.log("Hello World!");',
        })
        res = CodeRunner.from_language(language=request.language).invoke(lambda_client, request=request)
        print(res)
        assert res.overall.status == Status.OK
        assert res.test_results is not None and len(res.test_results) == 1 and res.test_results[0].status == Status.OK

    def test_mixed_type_output(self):
        test_cases = [TestCase(input='', target='1 2 4 8 16 32 are powers of two')]
        request = SubmissionRequest(test_cases=test_cases, language='ts', code={
            'index.ts': dedent('''
                console.log(1, 2, 4, 8, 16, 32, "are powers of two");
            ''').strip(),
        }, return_outputs=True)
        res = CodeRunner.from_language(language=request.language).invoke(lambda_client, request=request)
        print(res)
        assert res.overall.status == Status.OK
        assert res.test_results is not None and len(res.test_results) == 1 and res.test_results[0].status == Status.OK
        assert res.test_results[0].outputs.strip() == '1 2 4 8 16 32 are powers of two'

    def test_compile_error(self):
        request = SubmissionRequest(test_cases=[], language='ts', code={
            'index.ts': 'const value: number = "Hello World!";\nconsole.log(value);',
        })
        res = CodeRunner.from_language(language=request.language).invoke(lambda_client, request=request)
        print(res)
        assert res.overall.status == Status.COMPILATION_ERROR
        assert res.compile_result.status == Status.COMPILATION_ERROR

    def test_input_output_echo(self):
        test_cases = [TestCase(input='Hello World!', target='Hello World!')]
        request = SubmissionRequest(test_cases=test_cases, language='ts', code={
            'index.ts': dedent('''
                import * as fs from "fs";

                const input: string = fs.readFileSync(0, "utf8").trimEnd();
                console.log(input);
            ''').strip(),
        }, return_outputs=True)
        res = CodeRunner.from_language(language=request.language).invoke(lambda_client, request=request)
        print(res)
        assert res.overall.status == Status.OK
        assert res.test_results is not None and len(res.test_results) == 1 and res.test_results[0].status == Status.OK
        assert res.test_results[0].outputs.strip() == 'Hello World!'

    def test_multi_file(self):
        test_cases = [TestCase(input='', target='2')]
        request = SubmissionRequest(test_cases=test_cases, language='ts', code={
            'index.ts': dedent('''
                import { one } from "./dir/code";

                console.log(one() + one());
            ''').strip(),
            'ones.ts': dedent('''
                export function retOne(): number {
                    return 1;
                }
            ''').strip(),
            'dir': {
                'code.ts': dedent('''
                    import { retOne } from "../ones";

                    export function one(): number {
                        return retOne();
                    }
                ''').strip(),
            },
        }, return_outputs=True)
        res = CodeRunner.from_language(language=request.language).invoke(lambda_client, request=request)
        assert res.overall.status == Status.OK
        assert res.test_results is not None and len(res.test_results) == 1 and res.test_results[0].status == Status.OK
        assert res.test_results[0].outputs.strip() == '2'
