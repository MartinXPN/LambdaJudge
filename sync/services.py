import glob
import gzip
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile

from cryptography.fernet import Fernet

from models import TestCase


def read_files(paths: list[Path], remove_prefix: str) -> dict[str, str]:
    contents = {}
    for path in paths:
        with open(path) as f:
            filename = str(path).replace(remove_prefix, '').lstrip('.')
            contents[filename] = f.read()
    return contents


def zip2tests(zip_path: Path) -> list[TestCase]:
    with TemporaryDirectory() as extraction_dir, ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extraction_dir)
        targets = (glob.glob(f'{extraction_dir}/**/*.ans.txt', recursive=True) +
                   glob.glob(f'{extraction_dir}/**/*.out.txt', recursive=True) +
                   glob.glob(f'{extraction_dir}/**/*.a', recursive=True) +
                   glob.glob(f'{extraction_dir}/**/*.ans', recursive=True) +
                   glob.glob(f'{extraction_dir}/**/*.out', recursive=True))
        targets = sorted(targets)
        print('targets:', targets)
        inputs = [t.replace('.a', '') if t.endswith('.a') else t.replace('.ans', '.in').replace('.out', '.in')
                  for t in targets]
        print('inputs:', inputs)

        tests = []
        for ins, outs in zip(inputs, targets):
            in_prefix, out_prefix = ins.replace('.txt', ''), outs.replace('.txt', '')
            input_files, target_files = glob.glob(f'{in_prefix}*'), glob.glob(f'{out_prefix}*')
            input_files = read_files([Path(f) for f in input_files if f not in {ins, outs}], remove_prefix=in_prefix)
            target_files = read_files([Path(f) for f in target_files if f not in {ins, outs}], remove_prefix=out_prefix)

            with open(ins) as inf, open(outs) as of:
                print(ins, outs)
                tests.append(TestCase(
                    input=inf.read(),
                    target=of.read(),
                    input_files=input_files if len(input_files) != 0 else None,
                    target_files=target_files if len(target_files) != 0 else None,
                ))
    return tests


def encrypt_tests(tests: list[TestCase], encryption_key: str) -> bytes:
    print('encryption key len:', len(encryption_key))
    fernet = Fernet(encryption_key)

    # Compress:   (1) json.dumps   (2) .encode('utf-8')   (3) gzip.compress()   (4) encrypt
    # Decompress: (1) decrypt      (2) gzip.decompress()  (3) .decode('utf-8')  (4) json.loads()
    tests = TestCase.schema().dumps(tests, many=True)                       # (1)
    print('initial sys.size of tests:', sys.getsizeof(tests))
    big = sys.getsizeof(tests) > 50 * 1024 * 1024
    tests = tests.encode('utf-8')                                           # (2)
    tests = gzip.compress(tests, compresslevel=9 if not big else 7)         # (3)
    tests = fernet.encrypt(tests)                                           # (4)
    print('final sys.size of tests:', sys.getsizeof(tests))
    return tests
