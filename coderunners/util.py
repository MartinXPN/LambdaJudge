import errno
from pathlib import Path
from typing import Union


def is_float(value: str) -> bool:
    try:
        float(value)
        return True
    except ValueError:
        return False


def save_code(save_dir: Path, code: dict[str, Union[str, dict[str, str]]]) -> list[Path]:
    saved_paths: list[Path] = []
    save_dir.mkdir(parents=True, exist_ok=True)
    for filename, content in code.items():
        if isinstance(content, str):
            saved_paths.append(save_dir / filename)
            with open(save_dir / filename, 'w') as f:
                f.write(content)
        elif isinstance(content, dict):
            saved_paths += save_code(save_dir / filename, content)
        else:
            raise TypeError(f'Unsupported type for content {type(content)}')
    return saved_paths


return_code2status = errno.errorcode | {
    137: 'SIGKILL',
    139: 'SIGSEGV',
    143: 'SIGTERM',
}
