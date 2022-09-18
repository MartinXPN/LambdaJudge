from textwrap import dedent

from bouncer.coderunners import CodeRunner
from models import Status, SubmissionRequest, TestCase
from tests.integration.config import lambda_client


class TestHugeOutput:
    test_cases = [TestCase(input='hello', target=' ')]

    def test_ok(self):
        checker_code = dedent("""
            import sys
            executable_path, input_file, output_file, target_file, submission_dir = sys.argv
            #
            with open(input_file, 'r') as fin, open(output_file, 'r') as fout, open(target_file, 'r') as tgt:
                input_data = fin.read()
                output_data = fout.read()
            target_data = ' '.join(map(str, range(0, 1000000)))
            #
            if output_data.strip() == target_data.strip():
                print('Solved\\n100\\nGood job!\\n')
            else:
                print('Wrong answer\\n10\\nAnother one!\\n')
            print(output_data[-50:])
            print(len(output_data), len(target_data))
            print(len(output_data.split()), len(target_data.split()))
            """).strip()
        submission_code = dedent('''
            #include <iostream>
            using namespace std;
            int main() {
                int n = 1000000;
                for (int i = 0; i < n; i++)
                    cout << i << " ";
                return 0;
            }
            ''')
        request = SubmissionRequest(
            test_cases=self.test_cases, language='C++17', code={'main.cpp': submission_code},
            output_limit=10, time_limit=10,  # Printing 1M numbers in 10 seconds should not be an issue
            comparison_mode='custom', checker_language='python', checker_code={'checker.py': checker_code}
        )

        res = CodeRunner.from_language(language=request.language).invoke(lambda_client, request=request)
        print(res)
        assert res.overall.status == Status.OK
        assert len(res.test_results) == 1 and res.test_results[0].status == Status.OK
