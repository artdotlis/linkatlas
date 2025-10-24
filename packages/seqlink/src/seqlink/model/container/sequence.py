from pydantic import BaseModel, Field, ConfigDict
from saim.shared.parse.date import date_to_str

import datetime
from dataclasses import dataclass
from typing import final, Annotated
from utilslink.parse.number import pa_float
from utilslink.schema.sequence import SeqType, AsmLvl
from utilslink.schema.taxa import PIDType


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class SeqUpdatePackage:
    seq_acc: str
    desc: str
    seq_typ: SeqType
    len: int
    lvl: AsmLvl | None
    pub_date: str
    version: str
    tax_id: str
    tax_id_type: PIDType | None
    misc: str


@final
class _TaxEl(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    id: str
    id_type: PIDType | None


def _to_val(pid: PIDType | None, /) -> str:
    if pid is None:
        return ""
    return pid.value


def _to_dat(dat: float) -> str:
    return date_to_str(datetime.datetime.fromtimestamp(pa_float(dat)), True)


@final
class SequenceResults(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    seq_acc: Annotated[str, Field(ge=1)]
    desc: str
    pub_date: str
    seq_typ: SeqType
    len: int
    lvl: AsmLvl | None
    des: tuple[str, ...]
    taxa: tuple[_TaxEl, ...]
    last_update: float

    def to_string(self) -> str:
        names = ";".join(
            f"{nam.name}|{nam.id}|{_to_val(nam.id_type)}" for nam in self.taxa
        )
        lup = _to_dat(self.last_update)
        des = ";".join(self.des)
        lvl = ""
        if self.lvl is not None:
            lvl = self.lvl.value
        return (
            f"{self.seq_acc},{self.desc},{self.seq_typ.value},{self.pub_date}"
            + f"{self.len},{lvl},{des},{names},{lup}"
        )
