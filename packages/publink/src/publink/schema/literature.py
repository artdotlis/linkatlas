from enum import Enum
from typing import Final, final


@final
class LitType(str, Enum):
    full = "FULLTEXT"
    abstract = "ABSTRACT"


LIT_TYPES: Final[tuple[str, ...]] = tuple(lit.value for lit in LitType)


def get_all_lit_types(enc: str | None = None, /) -> tuple[str, ...]:
    return tuple(typ if enc is None else f"{enc}{typ}{enc}" for typ in LIT_TYPES)
