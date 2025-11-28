import gzip
import json
import sys
from glob import glob
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile

from cryptography.fernet import Fernet

from models import TestCase


def read_files(paths: list[Path], mode: str = 'r', remove_prefix: str = '') -> dict[str, str | bytes]:
    contents = {}
    for path in paths:
        with open(path, mode) as f:
            filename = str(path).replace(remove_prefix, '').lstrip('.')
            contents[filename] = f.read()
    return contents


def zip2tests(zip_path: Path) -> list[TestCase]:
    with TemporaryDirectory() as extraction_dir, ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extraction_dir)
        targets = (glob(f'{extraction_dir}/**/*.ans.txt', recursive=True) +
                   glob(f'{extraction_dir}/**/*.out.txt', recursive=True) +
                   glob(f'{extraction_dir}/**/*.a', recursive=True) +
                   glob(f'{extraction_dir}/**/*.ans', recursive=True) +
                   glob(f'{extraction_dir}/**/*.out', recursive=True))
        targets = sorted([target for target in targets if '.asset.' not in target])     # Filter out asset files
        inputs = [t.replace('.a', '') if t.endswith('.a') else t.replace('.ans', '.in').replace('.out', '.in')
                  for t in targets]
        print('----')
        print('targets:', targets)
        print('inputs:', inputs)

        tests = []
        for ins, outs in zip(inputs, targets):
            print('Processing:', ins, outs)
            in_prefix, out_prefix = ins.replace('.txt', ''), outs.replace('.txt', '')
            input_files = set(glob(f'{in_prefix}*') + glob(f'{in_prefix}*/**', recursive=True)) - {ins, outs}
            target_files = set(glob(f'{out_prefix}*') + glob(f'{out_prefix}*/**', recursive=True)) - {ins, outs}
            input_files = [f for f in input_files if Path(f).is_file()]
            target_files = [f for f in target_files if Path(f).is_file()]
            input_assets = [f for f in input_files if '.asset.' in f]
            target_assets = [f for f in target_files if '.asset.' in f]
            input_files = [f for f in input_files if '.asset.' not in f]
            target_files = [f for f in target_files if '.asset.' not in f]
            print('Input files:', input_files)
            print('Target files:', target_files)
            print('Input assets:', input_assets)
            print('Target assets:', target_assets)

            input_files = read_files([Path(f) for f in input_files], remove_prefix=in_prefix)
            target_files = read_files([Path(f) for f in target_files], remove_prefix=out_prefix)
            input_assets = read_files([Path(f) for f in input_assets], 'rb', remove_prefix=f'{in_prefix}.asset.')
            target_assets = read_files([Path(f) for f in target_assets], 'rb', remove_prefix=f'{out_prefix}.asset.')

            tests.append(TestCase(
                input=Path(ins).read_text(),
                target=Path(outs).read_text(),
                input_files=input_files if len(input_files) != 0 else None,
                target_files=target_files if len(target_files) != 0 else None,
                input_assets=input_assets if len(input_assets) != 0 else None,
                target_assets=target_assets if len(target_assets) != 0 else None,
            ))
    return tests


def encrypt_tests(tests: list[TestCase], encryption_key: str) -> bytes:
    print('encryption key len:', len(encryption_key))
    fernet = Fernet(encryption_key)

    # Compress:   (1) json.dumps   (2) .encode('utf-8')   (3) gzip.compress()   (4) encrypt
    # Decompress: (1) decrypt      (2) gzip.decompress()  (3) .decode('utf-8')  (4) json.loads()
    # TestCase.schema().dumps(tests, many=True) does not invoke the decoder function properly
    # https://github.com/lidatong/dataclasses-json/issues/551 => We'll use json.dumps([t.to_dict()...]) instead
    tests = json.dumps([test.to_dict() for test in tests])                  # (1)
    print('initial sys.getsizeof of tests:', sys.getsizeof(tests))
    big = sys.getsizeof(tests) > 50 * 1024 * 1024
    tests = tests.encode('utf-8')                                           # (2)
    tests = gzip.compress(tests, compresslevel=9 if not big else 7)         # (3)
    tests = fernet.encrypt(tests)                                           # (4)
    print('final sys.getsizeof of tests:', sys.getsizeof(tests))
    return tests
