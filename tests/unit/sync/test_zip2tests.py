import shutil
from pathlib import Path
from tempfile import TemporaryDirectory

from models import TestCase
from sync.services import zip2tests


class TestTruncation:
    def test_dataclass(self):
        t = TestCase(input='asdf', target='sdfew', input_files={'yoyo.txt': 'abc'})
        d = t.to_dict()
        print(d)
        assert 'inputFiles' in d, 'to_dict() should turn keys to camel-case'
        assert d['inputFiles']['yoyo.txt'] == 'abc'
        assert d['targetFiles'] is None
        assert d['input'] == 'asdf'
        assert d['target'] == 'sdfew'

    def test_valid_tests(self):
        with TemporaryDirectory() as tests_dir:
            for i in range(20):
                with open(f'{tests_dir}/{i:02d}.in.txt', 'w') as inf, open(f'{tests_dir}/{i:02d}.out.txt', 'w') as of:
                    inf.write(f'test input: {i}')
                    of.write(f'test output: {i}')

            shutil.make_archive(f'{tests_dir}/res', 'zip', tests_dir)
            tests = zip2tests(Path(tests_dir) / 'res.zip')
            assert len(tests) == 20
            for i, test in enumerate(tests):
                assert test.input == f'test input: {i}'
                assert test.target == f'test output: {i}'
                assert test.input_files is None
                assert test.target_files is None

    def test_files(self):
        with TemporaryDirectory() as tests_dir:
            with open(f'{tests_dir}/00.in.txt', 'w') as f:
                f.write('First input')
            with open(f'{tests_dir}/00.out.txt', 'w') as f:
                f.write('First target')

            with open(f'{tests_dir}/00.in.yoyo.txt', 'w') as f:   # We should have a `yoyo.txt` when the program starts
                f.write('First file input')
            with open(f'{tests_dir}/00.out.yoyo.txt', 'w') as f:  # We should have another `yoyo.txt` in the end
                f.write('First file target')

            shutil.make_archive(f'{tests_dir}/res', 'zip', tests_dir)
            tests = zip2tests(Path(tests_dir) / 'res.zip')
            test = tests[0]
            print(test)
            assert test.input == 'First input'
            assert test.target == 'First target'
            assert test.input_files['yoyo.txt'] == 'First file input'
            assert test.target_files['yoyo.txt'] == 'First file target'
