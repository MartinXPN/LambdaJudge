from textwrap import dedent

from bouncer.coderunners import CodeRunner
from models import Status, SubmissionRequest, TestCase
from tests.integration.config import lambda_client


class TestAssetsLimits:
    test_cases = [
        TestCase(
            input='', target='',
            target_files={'log.txt': ''}, target_assets={'image.png': b'Result image!'},
        ),
    ]

    def test_assets_under_1mb_preserved_and_text_truncated(self):
        submission_code = dedent(r'''
            # Large stdout (should be truncated to 32k when returned)
            print('A' * 100_000)

            # Large text file (should be truncated to 32k when returned)
            with open('log.txt', 'w', encoding='utf-8') as f:
                f.write('B' * 100_000)

            # Small binary "asset" (~10KB); remains under the 1MB threshold
            data = bytes([0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A]) + bytes(range(256)) * 40
            with open('image.png', 'wb') as f:
                f.write(data)
        ''').strip()

        request = SubmissionRequest(
            test_cases=self.test_cases,
            language='python',
            code={'main.py': submission_code},
            comparison_mode='ok',
            return_outputs=True,
        )

        res = CodeRunner.from_language(language=request.language).invoke(lambda_client, request=request)
        print(res)

        assert res.compile_result.status == Status.OK
        assert res.overall.status == Status.OK
        assert len(res.test_results) == 1

        r = res.test_results[0]
        assert r.status == Status.OK

        # Text fields are truncated to 32_000 chars when under 1MB
        assert r.outputs is not None and len(r.outputs) == 32_000
        assert r.output_files is not None and 'log.txt' in r.output_files
        assert len(r.output_files['log.txt']) == 32_000

        # Assets are passed through (not truncated) when under 1MB
        assert r.output_assets is not None and 'image.png' in r.output_assets
        content = r.output_assets['image.png']
        assert len(content) >= 8_000

    def test_assets_push_payload_over_1mb_then_omit_everything(self):
        submission_code = dedent(r'''
            import os

            # Create ~900KB of random bytes (incompressible), which after gzip+base64
            # will exceed 1MB in the JSON payload.
            with open('image.png', 'wb') as f:
                f.write(os.urandom(900_000))

            print('ok')  # tiny stdout
        ''').strip()

        request = SubmissionRequest(
            test_cases=self.test_cases,
            language='python',
            code={'main.py': submission_code},
            comparison_mode='ok',
            return_outputs=True,
        )

        res = CodeRunner.from_language(language=request.language).invoke(lambda_client, request=request)
        print(res)

        assert res.compile_result.status == Status.OK
        assert res.overall.status == Status.OK
        assert len(res.test_results) == 1

        r = res.test_results[0]
        print(r)
        assert r.status == Status.OK

        # When serialized size >= 1MB, everything is omitted
        assert r.message == 'Omitted outputs as the size of results exceeds 1MB'
        assert r.outputs is None
        assert r.errors is None
        assert r.output_files is None
        assert r.output_assets is None

    def test_multi_case_omission_boundary(self):
        # First three tests produce small assets; last three produce large random assets.
        cases = [
            TestCase(input='small', target='', target_files={'log.txt': ''}, target_assets={'image.png': b''}),
            TestCase(input='small', target='', target_files={'log.txt': ''}, target_assets={'image.png': b''}),
            TestCase(input='small', target='', target_files={'log.txt': ''}, target_assets={'image.png': b''}),
            TestCase(input='big', target='', target_files={'log.txt': ''}, target_assets={'image.png': b''}),
            TestCase(input='big', target='', target_files={'log.txt': ''}, target_assets={'image.png': b''}),
            TestCase(input='big', target='', target_files={'log.txt': ''}, target_assets={'image.png': b''}),
        ]

        submission_code = dedent(r'''
            import sys, os

            mode = sys.stdin.read().strip()

            # Always produce sizeable stdout and a text file to exercise 32k truncation
            print('A' * 100_000)
            with open('log.txt', 'w', encoding='utf-8') as f:
                f.write('B' * 100_000)

            if mode == 'big':
                # ~900KB random (incompressible) -> exceeds 1MB when encoded
                with open('image.png', 'wb') as f:
                    f.write(os.urandom(900_000))
            else:
                # ~10KB small asset (stays under 1MB cumulatively)
                data = bytes([0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A]) + bytes(range(256)) * 40
                with open('image.png', 'wb') as f:
                    f.write(data)
        ''').strip()

        request = SubmissionRequest(
            test_cases=cases,
            language='python',
            code={'main.py': submission_code},
            comparison_mode='ok',
            return_outputs=True,
            stop_on_first_fail=False,
        )

        res = CodeRunner.from_language(language=request.language).invoke(lambda_client, request=request)
        # print(res)

        assert res.compile_result.status == Status.OK
        assert res.overall.status == Status.OK
        assert len(res.test_results) == 6

        # First three results: under 1MB cumulative => outputs/files truncated, assets present
        for i in range(3):
            r = res.test_results[i]
            assert r.status == Status.OK
            assert r.outputs is not None and len(r.outputs) == 32_000
            assert r.output_files is not None and 'log.txt' in r.output_files
            assert len(r.output_files['log.txt']) == 32_000
            assert r.output_assets is not None and 'image.png' in r.output_assets
            assert len(res.test_results[i].output_assets['image.png']) >= 8_000

        # Last three results: first "big" should trigger the 1MB dropoff; all remaining should be omitted
        for i in range(3, 6):
            r = res.test_results[i]
            assert r.status == Status.OK
            assert r.message == 'Omitted outputs as the size of results exceeds 1MB'
            assert r.outputs is None
            assert r.errors is None
            assert r.output_files is None
            assert r.output_assets is None
