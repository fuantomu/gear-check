def enumerate_step(xs: list, start: int = 0, step: int = 1):
    for x in xs:
        yield (start, x)
        start += step


def get_formatted_time(time):
    seconds, _ = divmod(int(time), 1000)
    return f"{divmod(seconds,60)[0]:02d}:{divmod(seconds,60)[1]:02d}"
