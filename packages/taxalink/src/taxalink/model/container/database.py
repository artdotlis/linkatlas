from dataclasses import dataclass
from enum import Enum

from taxalink.model.container.taxa import PIDType, TaxUpdatePackage, TaxonomyResults
from taxalink.schema.designation import DesSource

from utilslink.container.bio_ent import AddDes
from utilslink.schema.taxa import GBIFRanksE


class DefCmd(str, Enum):
    sta = "STATUS"


@dataclass(slots=True, frozen=True)
class TaxUpdRes:
    tid: int
    version: str
    last_update: float


@dataclass(slots=True, frozen=True)
class TaxStatus:
    cnt: int
    last_update: float


@dataclass(slots=True, frozen=True)
class AddType(AddDes):
    des_source: DesSource


@dataclass(slots=True, frozen=True)
class ReportTax:
    pid: str = ""
    source: PIDType | None = None
    name: str = ""
    last_update: float = 0.0
    rank: GBIFRanksE = GBIFRanksE.unr
    correct_only: bool = False


type TW_REQ_UP_E = AddType | TaxUpdatePackage
type TW_REQ_UP_T = tuple[TW_REQ_UP_E, ...]
type TW_RES_UP_E = tuple[int, DesSource, tuple[str, ...]]

type TW_RES_REP_E = TaxStatus | TaxonomyResults
type TW_REQ_REP_E = ReportTax | DefCmd
