from textwrap import dedent

from bouncer.coderunners import CodeRunner
from models import Status, SubmissionRequest, TestCase
from tests.integration.config import lambda_client


class TestJava:
    def test_hello_world(self):
        test_cases = [TestCase(input='', target='Hello World!')]
        request = SubmissionRequest(test_cases=test_cases, language='java', code={
            'main.java': dedent('''
                class Main {
                    public static void main(String[] args) {
                        System.out.print("Hello World!");
                    }
                }
            ''').strip(),
        })
        res = CodeRunner.from_language(language=request.language).invoke(lambda_client, request=request)
        print(res)
        assert res.overall.status == Status.OK
        assert res.test_results is not None and len(res.test_results) == 1 and res.test_results[0].status == Status.OK

    def test_mixed_type_output(self):
        test_cases = [TestCase(input='', target='1 2 4 8 16 32 are powers of two')]
        request = SubmissionRequest(test_cases=test_cases, language='java', code={
            'main.java': dedent('''
                class Main {
                    public static void main(String[] args) {
                        System.out.print(1 + " " + 2 + " " + 4 + " " + 8 + " " + 16 + " " + 32
                                + " are powers of two");
                    }
                }
            ''').strip(),
        }, return_outputs=True)
        res = CodeRunner.from_language(language=request.language).invoke(lambda_client, request=request)
        print(res)
        assert res.overall.status == Status.OK
        assert res.test_results is not None and len(res.test_results) == 1 and res.test_results[0].status == Status.OK
        assert res.test_results[0].outputs.strip() == '1 2 4 8 16 32 are powers of two'

    def test_compile_error(self):
        request = SubmissionRequest(test_cases=[], language='java', code={
            'main.java': dedent('''
                class Main {
                    public static void main(String[] args) {
                        System.out.print("Hello World!")
                    }
                }
            ''').strip(),
        })
        res = CodeRunner.from_language(language=request.language).invoke(lambda_client, request=request)
        print(res)
        assert res.overall.status == Status.COMPILATION_ERROR
        assert res.compile_result.status == Status.COMPILATION_ERROR

    def test_input_output_echo(self):
        test_cases = [TestCase(input='Hello World!', target='Hello World!')]
        request = SubmissionRequest(test_cases=test_cases, language='java', code={
            'main.java': dedent('''
                import java.io.BufferedReader;
                import java.io.InputStreamReader;

                class Main {
                    public static void main(String[] args) throws Exception {
                        BufferedReader reader = new BufferedReader(new InputStreamReader(System.in));
                        String a = reader.readLine();
                        System.out.print(a);
                    }
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
        request = SubmissionRequest(test_cases=test_cases, language='java', code={
            'main.java': dedent('''
                import dir.Code;

                class Main {
                    public static void main(String[] args) {
                        System.out.print(Code.one() + Code.one());
                    }
                }
            ''').strip(),
            'ones': {
                'Ones.java': dedent('''
                    package ones;

                    public class Ones {
                        public static int retOne() {
                            return 1;
                        }
                    }
                ''').strip(),
            },
            'dir': {
                'Code.java': dedent('''
                    package dir;

                    import ones.Ones;

                    public class Code {
                        public static int one() {
                            return Ones.retOne();
                        }
                    }
                ''').strip(),
            },
        }, return_outputs=True)
        res = CodeRunner.from_language(language=request.language).invoke(lambda_client, request=request)
        assert res.overall.status == Status.OK
        assert res.test_results is not None and len(res.test_results) == 1 and res.test_results[0].status == Status.OK
        assert res.test_results[0].outputs.strip() == '2'
