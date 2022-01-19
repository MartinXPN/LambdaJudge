import errno


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
