from textwrap import dedent

from bouncer.coderunners import CodeRunner
from models import Status, SubmissionRequest, TestCase
from tests.integration.config import lambda_client


class TestLinting:
    test_cases = [TestCase(input='hello', target='hello')]

    def test_cpp_error(self):
        request = SubmissionRequest(test_cases=self.test_cases, language='c++17', code={
            'main.cpp': dedent('''
                #include <iostream>
                \n
                int string_to_int(const char *num) {
                    return std::atoi(num);
                }
                \n
                int main() {
                    std::cout << "hello";
                    std::cerr << string_to_int("21345");
                    return 0;
                }
            '''),
        }, lint=True)

        res = CodeRunner.from_language(language=request.language).invoke(lambda_client, request=request)
        print(res)
        assert res.overall.status == Status.LINTING_ERROR
        assert res.linting_result.status == Status.LINTING_ERROR

    def test_cpp_ok(self):
        request = SubmissionRequest(test_cases=self.test_cases, language='c++17', code={
            'main.cpp': dedent('''
                #include <iostream>
                \n
                int main() {
                    std::cout << "hello";
                    return 0;
                }
            '''),
        }, lint=True)

        res = CodeRunner.from_language(language=request.language).invoke(lambda_client, request=request)
        print(res)
        assert res.overall.status == Status.OK
        assert len(res.test_results) == 1 and res.test_results[0].status == Status.OK
