from textwrap import dedent

import pytest

from bouncer.coderunners import CodeRunner
from models import SubmissionRequest, TestCase, Status
from tests.integration.config import lambda_client


class TestInternetIsolation:
    test_cases = [TestCase(input='', target='What\'s your IP?')]

    @pytest.mark.skip('This will be only viable when deployed in a VPC in a private Subnet - not locally')
    def test_no_internet_access(self):
        request = SubmissionRequest(test_cases=self.test_cases, language='python', time_limit=5, code={
            'main.py': dedent("""
                import json
                import urllib.request
                base_url = 'http://httpbin.org/post'
                body = {'con1':40, 'con2':20, 'con3':99, 'con4':40, 'password':'1234'}
                params = json.dumps(body).encode('utf8')
                req = urllib.request.Request(base_url, data=params, headers={'content-type':'application/json'})
                response = urllib.request.urlopen(req)
                print(response.read().decode('utf8'))
            """)
        })

        res = CodeRunner.from_language(language=request.language).invoke(lambda_client, request=request)
        print(res)
        assert res.compile_result.status == Status.OK
        # The program should just hang as it does not have internet access
        assert res.overall.status == Status.TLE
        assert len(res.test_results) == 1 and res.test_results[0].status == Status.TLE
