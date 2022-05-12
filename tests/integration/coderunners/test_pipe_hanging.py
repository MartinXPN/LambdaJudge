import random
import string
from textwrap import dedent

from bouncer.coderunners import CodeRunner
from models import SubmissionRequest, TestCase, Status
from tests.integration.config import lambda_client


class TestPipeHanging:
    """
    Linux has a hard limit on the pipe size of 1MB.
    In case the program does not read the stdin, the pipe gets full and the program hangs.
    The current solution is to write to the subprocess stdin from a separate thread to avoid hanging.
    """
    random.seed(42)
    long_texts = [''.join(random.choices(string.printable, k=1000)) for _ in range(3000)]
    long_text = '\n'.join(long_texts) + '\n\n$$bik$$\n\n'
    test_cases = [TestCase(input=long_text, target='Done!')]

    def test_string_length(self):
        text_size_mb = len(self.long_text.encode('utf-8')) / 1024 / 1024
        print('Input size in MB:', text_size_mb)
        assert text_size_mb > 2

    def test_pass(self):
        request = SubmissionRequest(test_cases=self.test_cases, time_limit=1, language='C++17', code={
            'main.cpp': dedent('''
                #include <iostream>
                #include <string>
                int main() {
                    std::string s;
                    int n = 0;
                    while( std::getline(std::cin, s) ) {
                        n += s.size();
                        if( s == "$$bik$$" )
                            break;
                    }
                    std::cout << "Done!" << std::endl;
                    return 0;
                }
            '''),
        })
        res = CodeRunner.from_language(language=request.language).invoke(lambda_client, request=request)
        assert res.overall.status == Status.OK
        assert len(res.test_results) == 1 and res.test_results[0].status == Status.OK

    def test_hang(self):
        request = SubmissionRequest(test_cases=self.test_cases, time_limit=1, language='C++17', code={
            'main.cpp': dedent('''
                #include <iostream>
                #include <string>
                int main() {
                    std::string s;
                    std::cin >> s;
                    while( true ) {
                        // Do not read the input, let it fill up the PIPE
                    }
                    std::cout << "Done!" << std::endl;
                    return 0;
                }
            '''),
        })
        res = CodeRunner.from_language(language=request.language).invoke(lambda_client, request=request)
        assert res.overall.status == Status.TLE
        assert len(res.test_results) == 1 and res.test_results[0].status == Status.TLE
