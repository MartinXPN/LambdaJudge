from textwrap import dedent

from bouncer.coderunners import CodeRunner
from models import Status, SubmissionRequest, TestCase
from tests.integration.config import lambda_client


class TestHugeOutput:
    test_cases = [TestCase(input='hello', target='hello')]

    def test_return_size(self):
        request = SubmissionRequest(test_cases=self.test_cases, language='C++17', code={
            'main.cpp': dedent('''
                #include <iostream>
                using namespace std;
                int main() {
                    int n = 1000000;
                    for (int i = 10; i <= n; i++)
                        cout << i << " ";
                    return 0;
                }
            '''),
        }, output_limit=10, time_limit=10)  # Printing 1M numbers in 10 seconds should not be an issue

        res = CodeRunner.from_language(language=request.language).invoke(lambda_client, request=request)
        print(res)
        assert res.overall.status in {Status.OLE, Status.WA}
        assert len(res.test_results) == 1 and res.test_results[0].status in {Status.OLE, Status.WA}
