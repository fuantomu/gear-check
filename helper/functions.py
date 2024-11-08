def enumerate_step(xs: list, start: int = 0, step: int = 1):
    for x in xs:
        yield (start, x)
        start += step


def get_formatted_time(time):
    seconds, _ = divmod(int(time), 1000)
    minutes, seconds = divmod(seconds, 60)
    if minutes >= 60:
        hours, minutes = divmod(minutes, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    return f"{minutes:02d}:{seconds:02d}"
