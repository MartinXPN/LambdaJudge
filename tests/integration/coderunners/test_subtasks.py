from textwrap import dedent

from bouncer.coderunners import CodeRunner
from models import Status, SubmissionRequest, TestCase, TestGroup
from tests.integration.config import lambda_client


class TestSubtasks:
    test_cases = [
        TestCase(input='1', target='2'), TestCase(input='2', target='3'),
        TestCase(input='3', target='4'), TestCase(input='4', target='6'), TestCase(input='5', target='6'),
        TestCase(input='6', target='7'), TestCase(input='4', target='6'), TestCase(input='5', target='6'),
    ]
    test_groups = [
        TestGroup(count=2, points=20, points_per_test=0),
        TestGroup(count=3, points=50, points_per_test=0),
        TestGroup(count=3, points=0, points_per_test=10),
    ]

    def test_partial(self):
        request = SubmissionRequest(test_cases=self.test_cases, test_groups=self.test_groups, language='C++17', code={
            'main.cpp': dedent('''
                #include <iostream>
                int main() {
                    int a;
                    std::cin >> a;
                    std::cout << a + 1;
                    return 0;
                }
            '''),
        })
        res = CodeRunner.from_language(language=request.language).invoke(lambda_client, request=request)
        print(res)
        assert res.overall.status == Status.WA
        assert res.overall.score == 20 + 20
        assert len(res.test_results) == len(self.test_cases)
        assert res.test_results[0].status == Status.OK
        assert res.test_results[1].status == Status.OK
        assert res.test_results[2].status == Status.OK
        assert res.test_results[3].status == Status.WA
        assert res.test_results[4].status == Status.SKIPPED
        assert res.test_results[5].status == Status.OK
        assert res.test_results[6].status == Status.WA
        assert res.test_results[7].status == Status.OK
