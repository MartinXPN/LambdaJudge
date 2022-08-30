import glob
import gzip
import json
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile

from cryptography.fernet import Fernet


def zip2tests(zip_path: Path) -> list[dict[str, str]]:
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
            # TODO: support files
            with open(ins) as inf, open(outs) as of:
                print(ins, outs)
                tests.append({
                    'input': inf.read(),
                    'target': of.read(),
                })
    return tests


def encrypt_tests(tests: list, encryption_key: str) -> bytes:
    print('encryption key len:', len(encryption_key))
    fernet = Fernet(encryption_key)

    # Compress:   (1) json.dumps   (2) .encode('utf-8')   (3) gzip.compress()   (4) encrypt
    # Decompress: (1) decrypt      (2) gzip.decompress()  (3) .decode('utf-8')  (4) json.loads()
    tests = json.dumps(tests)                                               # (1)
    print('initial sys.size of tests:', sys.getsizeof(tests))
    big = sys.getsizeof(tests) > 50 * 1024 * 1024
    tests = tests.encode('utf-8')                                           # (2)
    tests = gzip.compress(tests, compresslevel=9 if not big else 7)         # (3)
    tests = fernet.encrypt(tests)                                           # (4)
    print('final sys.size of tests:', sys.getsizeof(tests))
    return tests
