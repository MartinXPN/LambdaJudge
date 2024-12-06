from textwrap import dedent

from bouncer.coderunners import CodeRunner
from models import Status, SubmissionRequest, SubmissionResult, TestCase
from tests.integration.config import lambda_client


class TestMultiFile:
    test_cases = [TestCase(input='', target='2')]

    @staticmethod
    def run_test(request: SubmissionRequest) -> SubmissionResult:
        res = CodeRunner.from_language(language=request.language).invoke(lambda_client, request=request)
        print(res)
        assert res.overall.status == Status.OK
        assert len(res.test_results) == 1 and res.test_results[0].status == Status.OK
        return res

    def test_python(self):
        self.run_test(SubmissionRequest(test_cases=self.test_cases, language='python', code={
            'main.py': dedent('''
                from dir.code import one
                \n
                print(one() + one())
            ''').strip(),
            'ones.py': dedent('''
                def ret_one():
                    return 1
            ''').strip(),
            'dir': {
                'code.py': dedent('''
                    from ones import ret_one
                    \n
                    def one():
                        return ret_one()
                ''').strip(),
            }
        }))

    def test_cpp(self):
        self.run_test(SubmissionRequest(test_cases=self.test_cases, language='C++17', code={
            'main.cpp': dedent('''
                #include <iostream>
                #include "one.h"
                int main() {
                    std::cout << one_f() + one_f();
                    return 0;
                }
            ''').strip(),
            'one.h': dedent('''
                #ifndef ONE_H
                #define ONE_H
                int one_f() {
                    return 1;
                }
                #endif //ONE_H
            ''').strip(),
        }))

    def test_js(self):
        self.run_test(SubmissionRequest(test_cases=self.test_cases, language='js', code={
            'index.js': dedent('''
                console.log(2)
            ''').strip(),
            'package.json': dedent('''
                {
                    "name": "hello-world",
                    "version": "1.0.0"
                }
            ''').strip(),
        }))

    def test_csharp(self):
        self.run_test(SubmissionRequest(test_cases=self.test_cases, language='C#', time_limit=10, code={
            'main.cs': dedent('''
                namespace HelloWorld {
                    class Hello {
                        static void Main(string[] args) {
                            System.Console.WriteLine('2');
                        }
                    }
                }
            ''').strip(),
            'LoggingMethods.cs': dedent('''
                using System;
                namespace DelegatesAndEvents {
                    public static class LoggingMethods {
                        public static void LogToConsole(string message) {
                            Console.Error.WriteLine(message);
                        }
                    }
                }
            ''').strip(),
        }))

    def test_java(self):
        self.run_test(SubmissionRequest(test_cases=self.test_cases, language='Java', time_limit=5, code={
            'main.java': dedent('''
                class Main {
                    public static void main(String[] args) {
                        System.out.println("2");
                    }
                }
            ''').strip(),
        }))
