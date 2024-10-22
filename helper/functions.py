def enumerate_step(xs: list, start: int = 0, step: int = 1):
    for x in xs:
        yield (start, x)
        start += step
