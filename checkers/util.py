def is_float(value: str):
    try:
        float(value)
        return True
    except ValueError:
        return False
