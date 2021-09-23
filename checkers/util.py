import zipfile
from pathlib import Path


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
