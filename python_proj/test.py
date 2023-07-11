from typing import Iterator
import itertools


def a() -> Iterator:
    for i in range(15):
        yield i


def b() -> Iterator:
    return itertools.chain(a(), [16])


print(list(b()))