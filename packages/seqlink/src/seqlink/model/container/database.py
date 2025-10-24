from dataclasses import dataclass

from enum import Enum
from seqlink.model.container.sequence import SeqUpdatePackage, SequenceResults
from utilslink.container.bio_ent import AddDes, AddIdTaxa
from utilslink.schema.taxa import PIDType


class DefCmd(str, Enum):
    sta = "STATUS"


@dataclass(slots=True, frozen=True)
class ReportSeq:
    seq_acc: str = ""
    last_update: float = 0.0
    include_des: tuple[str, ...] = tuple()


@dataclass(slots=True, frozen=True)
class SeqStatus:
    cnt: int
    last_update: float


type TW_REQ_UP_E = AddDes | AddIdTaxa | SeqUpdatePackage
type TW_REQ_UP_T = tuple[TW_REQ_UP_E, ...]
type TW_RES_UP_E = tuple[int, str, PIDType | None, str]

type TW_RES_REP_E = SeqStatus | SequenceResults
type TW_REQ_REP_E = ReportSeq | DefCmd
