import zipfile
from os.path import splitext, basename
from pathlib import Path
from urllib.parse import urlparse, unquote

import requests


def is_float(value: str):
    try:
        float(value)
        return True
    except ValueError:
        return False


def extract_s3_zip(bucket, bucket_path: str, save_path: Path, cached: bool = True) -> Path:
    print(f'Saving `{bucket_path}` \tto\t `{save_path}`', end='...', flush=True)
    bucket.download_file(f'{bucket_path}', str(save_path))
    print('Done!')

    extract_path = save_path.with_suffix('')
    print(f'Extracting `{save_path}` to `{extract_path}`', end='...', flush=True)
    with zipfile.ZipFile(save_path, 'r') as zip_ref:
        zip_ref.extractall(extract_path)
    print('Done!')

    return extract_path


def download_file(url: str, save_dir: Path) -> Path:
    print('Downloading file from:', url)
    r = requests.get(url, allow_redirects=True)
    filename, file_ext = splitext(basename(urlparse(unquote(url)).path))
    save_path = save_dir / (filename + file_ext)
    print('save path:', save_path)

    with open(save_path, 'wb') as f:
        f.write(r.content)
    return save_path
