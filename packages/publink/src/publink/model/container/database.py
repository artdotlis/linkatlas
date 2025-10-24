from pathlib import Path

from dataclasses import dataclass
from enum import Enum

from publink.model.container.literature import (
    LitUpdatePackage,
    LiteratureResults,
)
from utilslink.container.bio_ent import AddDes, AddTaxa, AddSeq


class DefCmd(str, Enum):
    sta = "STATUS"


@dataclass(slots=True, frozen=True)
class ReportLit:
    acr: str
    pub_date: str
    include_des: tuple[str, ...]


@dataclass(slots=True, frozen=True)
class LitUpdRes:
    doi: str
    version: str
    last_update: float
    type: str


@dataclass(slots=True, frozen=True)
class PubStatus:
    cnt: int
    last_update: float


type TW_REQ_UP_E = AddDes | AddTaxa | AddSeq | LitUpdatePackage
type TW_REQ_UP_T = tuple[TW_REQ_UP_E, ...]
type TW_RES_UP_E = tuple[int, str | Path]

type TW_RES_REP_E = PubStatus | LiteratureResults
type TW_REQ_REP_E = ReportLit | DefCmd
