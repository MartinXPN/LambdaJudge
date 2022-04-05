import errno
from pathlib import Path


def is_float(value: str) -> bool:
    try:
        float(value)
    except ValueError:
        return False
    return True


def save_code(save_dir: Path, code: dict[str, str]) -> list[Path]:
    saved_paths: list[Path] = []
    for filename, content in code.items():
        path = save_dir / filename
        saved_paths.append(path)
        with open(path, 'w') as f:
            f.write(content)

    return saved_paths


return_code2status = errno.errorcode | {
    137: 'SIGKILL',
    139: 'SIGSEGV',
    143: 'SIGTERM',
}
