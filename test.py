from reader import Reader


def callback(code: str) -> bool:
    print(code)
    return False


reader = Reader(callback, rotate_image=True, allow_repeats=True)
