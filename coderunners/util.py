import errno
from pathlib import Path


def is_float(value: str) -> bool:
    try:
        float(value)
        return True
    except ValueError:
        return False


def return_code2status(code: int) -> str:
    if code in errno.errorcode:
        return errno.errorcode[code]

    if code == 137:     return 'SIGKILL'
    if code == 139:     return 'SIGSEGV'
    if code == 143:     return 'SIGTERM'
    return ''


def save_code(save_dir: Path, code: dict[str, str]) -> list[Path]:
    saved_paths: list[Path] = []
    for filename, content in code.items():
        path = save_dir / filename
        saved_paths.append(path)
        with open(path, 'w') as f:
            f.write(content)

    return saved_paths
