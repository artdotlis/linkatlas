from enum import Enum


class DesSource(str, Enum):
    sy_db = "DB"
    ex_icpa = "TYP_ICPA"


def get_all_des_sources(enc: str | None = None, /) -> tuple[str, ...]:
    return tuple(
        typ.value if enc is None else f"{enc}{typ.value}{enc}" for typ in DesSource
    )
