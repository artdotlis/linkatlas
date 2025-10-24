from typing import Annotated, final
from pydantic import BaseModel, ConfigDict, Field


@final
class _ResultsCon(BaseModel):
    model_config = ConfigDict(frozen=True, extra="ignore", validate_default=False)
    publication_date: str | None
    title: str | None
    doi: str | None
    abstract_inverted_index: dict[str, tuple[Annotated[int, Field(ge=0)], ...]] | None = (
        Field(default_factory=dict)
    )


@final
class _MetaCon(BaseModel):
    model_config = ConfigDict(frozen=True, extra="ignore", validate_default=False)
    next_cursor: str | None


@final
class OpAlexWorksCon(BaseModel):
    model_config = ConfigDict(frozen=True, extra="ignore", validate_default=False)

    results: tuple[_ResultsCon, ...]
    meta: _MetaCon
