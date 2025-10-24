from collections.abc import Callable
from collections.abc import Iterable
from collections.abc import Iterator


def _pack_iter[T](
    data_iter: Iterator[T],
    pkg_count: int,
    current_size: int,
    pkg_size: int,
    get_pkg_size: Callable[[T], int],
    /,
) -> Iterable[T]:
    run_size = current_size
    for _ in range(pkg_count - 1):
        if run_size >= pkg_size:
            break
        data_el = next(data_iter, None)
        if data_el is None:
            break
        run_size += get_pkg_size(data_el)
        yield data_el


def package_data[T](
    data: Iterable[T], pkg_count: int, pkg_size: int, get_pkg_size: Callable[[T], int], /
) -> Iterable[tuple[T, ...]]:
    data_iter = iter(data)
    while (fir_d := next(data_iter, None)) is not None:
        start_size = get_pkg_size(fir_d)
        res = (
            fir_d,
            *_pack_iter(data_iter, pkg_count, start_size, pkg_size, get_pkg_size),
        )
        yield res
