from pathlib import Path

from dataclasses import dataclass
from typing import final
from publink.schema.literature import LitType


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class LitUpdatePackage:
    data: tuple[str, str, str | Path]
    version: str
    txt_typ: LitType


@final
@dataclass(slots=True, frozen=True)
class LiteratureResults:
    doi: str
    pub_date: str
    des: tuple[str, ...]
    taxa: tuple[str, ...]
    seq: tuple[str, ...]
