import shutil
from pathlib import Path
from tempfile import TemporaryDirectory

from models import TestCase
from sync.sync import zip2tests


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
            tests_dir = Path(tests_dir)
            (tests_dir / '00.in.txt').write_text('First input')
            (tests_dir / '00.out.txt').write_text('First target')
            (tests_dir / '00.in.yoyo.txt').write_text('First file input')
            (tests_dir / '00.out.yoyo.txt').write_text('First file target')
            (tests_dir / '00.out.bik.txt').write_text('Second file target')
            shutil.make_archive(f'{tests_dir}/res', 'zip', tests_dir)
            tests = zip2tests(Path(tests_dir) / 'res.zip')
            test = tests[0]
            print(test)
            assert test.input == 'First input'
            assert test.target == 'First target'
            assert test.input_files['yoyo.txt'] == 'First file input'
            assert test.target_files['yoyo.txt'] == 'First file target'
            assert test.target_files['bik.txt'] == 'Second file target'

    def test_subfolders(self):
        with TemporaryDirectory() as tests_dir:
            tests_dir = Path(tests_dir)

            # Test 1
            (tests_dir / '01.in.txt').write_text('First input')
            (tests_dir / '01.out.txt').write_text(
                'subfolder1/subfolder2/subfolder3/image1.jpg\n'
                'subfolder1/subfolder4/subfolder3/image2.jpg\n'
                'subfolder2/subfolder2/image5.jpeg\n'
                'image6.jpg'
            )

            Path(f'{tests_dir}/01.in.subfolder1/subfolder2/subfolder3').mkdir(parents=True, exist_ok=True)
            Path(f'{tests_dir}/01.in.subfolder1/subfolder4/subfolder3').mkdir(parents=True, exist_ok=True)
            Path(f'{tests_dir}/01.in.subfolder2/subfolder2').mkdir(parents=True, exist_ok=True)

            (tests_dir / '01.in.subfolder1/subfolder2/subfolder3/image1.jpg').write_text('some jpeg file')
            (tests_dir / '01.in.subfolder1/subfolder4/subfolder3/image2.jpg').write_text('some jpeg file')
            (tests_dir / '01.in.subfolder2/subfolder2/image5.jpeg').write_text('some jpeg file')
            (tests_dir / '01.in.image6.jpg').write_text('some jpeg file')

            # Test 2
            (tests_dir / '02.in.txt').write_text('Second input')
            (tests_dir / '02.out.txt').write_text('lMJUev/mFDLKv/UHhhMCMwE.jpeg')

            Path(f'{tests_dir}/02.in.lMJUev/mFDLKv').mkdir(parents=True, exist_ok=True)
            (tests_dir / '02.in.lMJUev/mFDLKv/UHhhMCMwE.jpeg').write_text('some jpeg file')

            shutil.make_archive(f'{tests_dir}/res', 'zip', tests_dir)
            tests = zip2tests(Path(tests_dir) / 'res.zip')

            # Check Test 1
            test = tests[0]
            print(test)
            assert test.input == 'First input'
            assert test.target == (
                'subfolder1/subfolder2/subfolder3/image1.jpg\n'
                'subfolder1/subfolder4/subfolder3/image2.jpg\n'
                'subfolder2/subfolder2/image5.jpeg\n'
                'image6.jpg'
            )
            assert test.input_files['subfolder1/subfolder2/subfolder3/image1.jpg'] == 'some jpeg file'
            assert test.input_files['subfolder1/subfolder4/subfolder3/image2.jpg'] == 'some jpeg file'
            assert test.input_files['subfolder2/subfolder2/image5.jpeg'] == 'some jpeg file'
            assert test.input_files['image6.jpg'] == 'some jpeg file'

            # Check Test 2
            test = tests[1]
            print(test)
            assert test.input == 'Second input'
            assert test.target == 'lMJUev/mFDLKv/UHhhMCMwE.jpeg'
            assert test.input_files['lMJUev/mFDLKv/UHhhMCMwE.jpeg'] == 'some jpeg file'

    def test_assets(self):
        with TemporaryDirectory() as tests_dir:
            # stdin / stdout
            with open(f'{tests_dir}/00.in.txt', 'w') as f:
                f.write('First input')
            with open(f'{tests_dir}/00.out.txt', 'w') as f:
                f.write('First target')

            # Files
            with open(f'{tests_dir}/00.in.yoyo.txt', 'w') as f:   # We should have a `yoyo.txt` when the program starts
                f.write('First file input')
            with open(f'{tests_dir}/00.out.yoyo.txt', 'w') as f:  # We should have another `yoyo.txt` in the end
                f.write('First file target')
            with open(f'{tests_dir}/00.out.bik.txt', 'w') as f:
                f.write('Second file target')

            # Assets
            with open(f'{tests_dir}/00.in.asset.start.bin', 'wb') as f:
                f.write(b'Hello')
            with open(f'{tests_dir}/00.out.asset.finish.bin', 'wb') as f:
                f.write(b'World')

            shutil.make_archive(f'{tests_dir}/res', 'zip', tests_dir)
            tests = zip2tests(Path(tests_dir) / 'res.zip')
            test = tests[0]
            print(test)
            assert test.input == 'First input'
            assert test.target == 'First target'
            assert test.input_files['yoyo.txt'] == 'First file input'
            assert test.target_files['yoyo.txt'] == 'First file target'
            assert test.target_files['bik.txt'] == 'Second file target'
            assert test.input_assets['start.bin'] == b'Hello'
            assert test.target_assets['finish.bin'] == b'World'
