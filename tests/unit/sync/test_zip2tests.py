import shutil
from pathlib import Path
from tempfile import TemporaryDirectory

from sync.services import zip2tests


class TestTruncation:
    def test_valid_tests(self):
        with TemporaryDirectory() as tests_dir:
            for i in range(20):
                with open(f'{tests_dir}/{i:02d}.in.txt', 'w') as inf, open(f'{tests_dir}/{i:02d}.out.txt', 'w') as of:
                    inf.write(f'test input: {i}')
                    of.write(f'test output: {i}')

            shutil.make_archive(f'{tests_dir}/res', 'zip', tests_dir)
            tests = zip2tests(Path(tests_dir) / 'res.zip')
            for i, test in enumerate(tests):
                assert test['input'] == f'test input: {i}'
                assert test['target'] == f'test output: {i}'
