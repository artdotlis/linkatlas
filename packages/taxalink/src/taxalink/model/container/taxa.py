from dataclasses import dataclass

from pydantic import BaseModel, ConfigDict, Field
from saim.shared.parse.date import date_to_str

from datetime import datetime
from taxalink.schema.designation import DesSource
from typing import final, Annotated
from utilslink.container.bio_ent import PIDType
from utilslink.parse.number import pa_float
from utilslink.schema.taxa import GBIFRanksE


@final
class TaxonomyAdd(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    pid: Annotated[str, Field(min_length=1)]
    pid_type: PIDType
    name: Annotated[str, Field(min_length=1)]
    correct: bool
    rank: Annotated[str, Field(min_length=1)]
    type_strain: tuple[Annotated[str, Field(min_length=1)], ...] = Field(
        default_factory=tuple
    )
    correct_pid: str = ""
    parent_pid: str = ""
    parent_name: str = ""


@final
class TaxonomyLink(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    pid: Annotated[str, Field(min_length=1)]
    pid_type: PIDType
    name: Annotated[str, Field(min_length=1)]
    type_strain: tuple[Annotated[str, Field(min_length=1)], ...]


@final
class TaxonomyDel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    pid: Annotated[str, Field(min_length=1)]
    pid_type: PIDType


@final
class TaxonomyCom(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    pid: Annotated[str, Field(min_length=1)]
    pid_type: PIDType
    merge_pid: Annotated[str, Field(min_length=1)]


@final
class _TaxRankEl(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    name: Annotated[str, Field(min_length=1)]
    rank: GBIFRanksE


@final
class _TaxTypeEl(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    des: Annotated[str, Field(min_length=1)]
    last_update: float
    source: DesSource


def _to_dat(dat: float) -> str:
    return date_to_str(datetime.fromtimestamp(pa_float(dat)), True)


@final
class TaxonomyResults(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    tid: Annotated[int, Field(ge=1)]
    pid: Annotated[str, Field(min_length=1)]
    pid_type: PIDType
    last_update: float
    name: Annotated[str, Field(min_length=1)]
    names: tuple[Annotated[str, Field(min_length=1)], ...]
    correct: bool
    rank: GBIFRanksE
    ranks: tuple[_TaxRankEl, ...]
    type_strain: tuple[_TaxTypeEl, ...]

    def to_string(self) -> str:
        ranks = ";".join(f"{rank.name}|{rank.rank.value}" for rank in self.ranks)
        names = ";".join(self.names)
        lup = _to_dat(self.last_update)
        types = ";".join(
            f"{des.des}|{des.source}|{_to_dat(des.last_update)}"
            for des in self.type_strain
        )
        return (
            f"{self.name},{self.pid},{self.pid_type},{self.correct!s},"
            + f"{lup},{names},"
            + f"{self.rank},{ranks},"
            + f"{types}"
        )


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class TaxUpdatePackage:
    data: TaxonomyCom | TaxonomyDel | TaxonomyAdd | TaxonomyLink
    version: str
    des_src: DesSource
