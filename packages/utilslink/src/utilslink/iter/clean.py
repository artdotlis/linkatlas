from typing import Iterable


def rm_dup(res: Iterable[str], /) -> Iterable[str]:
    cache: set[str] = set()
    for ele in res:
        if ele == "":
            continue
        if ele not in cache:
            yield ele
        cache.add(ele)
