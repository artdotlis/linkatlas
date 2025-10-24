from pydantic import BaseModel, ConfigDict, Field

from typing import final, Annotated


@final
class LpsnOrgC(BaseModel):
    model_config = ConfigDict(frozen=True, extra="ignore", validate_default=False)

    id: int
    full_name: Annotated[str, Field(min_length=1)]
    category: Annotated[str, Field(min_length=1)]
    lpsn_correct_name_id: int | None = None
    lpsn_parent_id: int | None = None
    type_strain_names: list[Annotated[str, Field(min_length=1)]] = Field(
        default_factory=list
    )


@final
class LPSNCat(BaseModel):
    model_config = ConfigDict(frozen=True, extra="ignore", validate_default=False)

    next: Annotated[str, Field(min_length=1)] | None
    results: list[int]


@final
class LPSNId(BaseModel):
    model_config = ConfigDict(frozen=True, extra="ignore", validate_default=False)

    next: Annotated[str, Field(min_length=1)] | None
    results: list[LpsnOrgC]
