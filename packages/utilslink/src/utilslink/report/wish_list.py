from pathlib import Path


def create_ccno_wish_list(include_list: Path | None, /) -> tuple[str, ...]:
    if include_list is None or not (include_list.exists() or include_list.is_file()):
        return tuple()
    with include_list.open() as ifh:
        return tuple(line for line in ifh if line != "")
