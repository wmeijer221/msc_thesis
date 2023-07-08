



from typing import Generator, Iterator





def bla() -> Generator[str, None, None]:
    for i in range(15):
        yield str(i)


def bla2() -> Iterator[str]:
    for i in range(6):
        yield str(i)

for q in bla():
    print(q)

for r in bla2():
    print(r)

    