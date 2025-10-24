from dataclasses import dataclass
from utilslink.schema.taxa import PIDType


def get_pid_type(source: str, /) -> PIDType | None:
    for typ in PIDType:
        if typ.value == source:
            return typ
    return None


def get_all_pid_types(enc: str | None = None, /) -> tuple[str, ...]:
    return tuple(
        typ.value if enc is None else f"{enc}{typ.value}{enc}" for typ in PIDType
    )


@dataclass(slots=True, frozen=True)
class AddDes:
    did: int
    des: str


@dataclass(slots=True, frozen=True)
class AddTaxa:
    did: int
    taxa: str


@dataclass(slots=True, frozen=True)
class AddSeq:
    did: int
    seq: str


@dataclass(frozen=True, slots=True)
class AddIdTaxa(AddTaxa):
    pid: str = ""
    pid_type: PIDType | None = None
