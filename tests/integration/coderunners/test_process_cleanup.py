from textwrap import dedent

from bouncer.coderunners import CodeRunner
from models import SubmissionRequest, TestCase
from tests.integration.config import lambda_client


class TestProcessCleanup:
    test_cases = [TestCase(input='', target='')]

    def test_cleanup(self):
        request = SubmissionRequest(test_cases=self.test_cases, language='python', code={
            'main.py': dedent(r'''
                import os, subprocess, time

                # start the detached 'sleep 40'
                sleeper = subprocess.Popen(
                    ['sleep', '40'],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    preexec_fn=os.setsid,
                )
                print('Started PID:', sleeper.pid)

                # give the kernel a moment to register the new process
                time.sleep(0.5)

                # walk /proc and print something ps-like
                for pid in filter(str.isdigit, os.listdir('/proc')):
                    with open(f'/proc/{pid}/stat') as f:
                        stat_fields = f.read().split()
                    with open(f'/proc/{pid}/cmdline') as f:
                        cmd = f.read().replace('\x00', ' ').strip()
                    print(f'{stat_fields[0]:>5} {stat_fields[2]} {cmd}')
            '''),
        }, return_outputs=True)

        res1 = CodeRunner.from_language(language=request.language).invoke(lambda_client, request=request)
        res2 = CodeRunner.from_language(language=request.language).invoke(lambda_client, request=request)
        res3 = CodeRunner.from_language(language=request.language).invoke(lambda_client, request=request)
        print('Process cleanup check result1:', res1.test_results[0].outputs, end='\n\n\n')
        print('Process cleanup check result2:', res2.test_results[0].outputs, end='\n\n\n')
        print('Process cleanup check result3:', res3.test_results[0].outputs, end='\n\n\n')

        sleep1 = res1.test_results[0].outputs.count('sleep 40')
        sleep2 = res2.test_results[0].outputs.count('sleep 40')
        sleep3 = res3.test_results[0].outputs.count('sleep 40')
        print(f'Sleep counts: {sleep1} {sleep2} {sleep3}')
        assert sleep1 == sleep2 == sleep3, 'The number of sleep processes should not increase'
