from textwrap import dedent

from bouncer.coderunners import CodeRunner
from models import Status, SubmissionRequest, TestCase
from tests.integration.config import lambda_client


class TestC:
    def test_hello_world(self):
        test_cases = [TestCase(input='', target='Hello World!')]
        request = SubmissionRequest(test_cases=test_cases, language='c', code={
            'main.c': dedent('''
                #include <stdio.h>

                int main() {
                    printf("Hello World!");
                    return 0;
                }
            ''').strip(),
        })
        res = CodeRunner.from_language(language=request.language).invoke(lambda_client, request=request)
        print(res)
        assert res.overall.status == Status.OK
        assert res.test_results is not None and len(res.test_results) == 1 and res.test_results[0].status == Status.OK

    def test_mixed_type_output(self):
        test_cases = [TestCase(input='', target='1 2 4 8 16 32 are powers of two')]
        request = SubmissionRequest(test_cases=test_cases, language='c', code={
            'main.c': dedent('''
                #include <stdio.h>

                int main() {
                    printf("%d %d %d %d %d %d %s", 1, 2, 4, 8, 16, 32, "are powers of two");
                    return 0;
                }
            ''').strip(),
        }, return_outputs=True)
        res = CodeRunner.from_language(language=request.language).invoke(lambda_client, request=request)
        print(res)
        assert res.overall.status == Status.OK
        assert res.test_results is not None and len(res.test_results) == 1 and res.test_results[0].status == Status.OK
        assert res.test_results[0].outputs.strip() == '1 2 4 8 16 32 are powers of two'

    def test_compile_error(self):
        request = SubmissionRequest(test_cases=[], language='c', code={
            'main.c': dedent('''
                #include <stdio.h>

                int main() {
                    printf("Hello World!")
                }
            ''').strip(),
        })
        res = CodeRunner.from_language(language=request.language).invoke(lambda_client, request=request)
        print(res)
        assert res.overall.status == Status.COMPILATION_ERROR
        assert res.compile_result.status == Status.COMPILATION_ERROR

    def test_input_output_echo(self):
        test_cases = [TestCase(input='Hello World!', target='Hello World!')]
        request = SubmissionRequest(test_cases=test_cases, language='c', code={
            'main.c': dedent('''
                #include <stdio.h>
                #include <string.h>

                int main() {
                    char a[1024];
                    if (fgets(a, sizeof(a), stdin) == NULL) {
                        return 0;
                    }
                    a[strcspn(a, "\\n")] = '\\0';
                    printf("%s", a);
                    return 0;
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
        request = SubmissionRequest(test_cases=test_cases, language='c', code={
            'main.c': dedent('''
                #include <stdio.h>
                #include "dir/code.h"

                int main() {
                    printf("%d", one() + one());
                    return 0;
                }
            ''').strip(),
            'ones.h': dedent('''
                #ifndef ONES_H
                #define ONES_H

                static inline int ret_one() {
                    return 1;
                }

                #endif //ONES_H
            ''').strip(),
            'dir': {
                'code.h': dedent('''
                    #ifndef CODE_H
                    #define CODE_H

                    #include "../ones.h"

                    static inline int one() {
                        return ret_one();
                    }

                    #endif //CODE_H
                ''').strip(),
            },
        }, return_outputs=True)
        res = CodeRunner.from_language(language=request.language).invoke(lambda_client, request=request)
        assert res.overall.status == Status.OK
        assert res.test_results is not None and len(res.test_results) == 1 and res.test_results[0].status == Status.OK
        assert res.test_results[0].outputs.strip() == '2'
