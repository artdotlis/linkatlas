from typing import Annotated, Any, final
from pydantic import AfterValidator, BaseModel, ConfigDict, Field
from utilslink.parse.date import conv_to_date_str


@final
class _ResultEle(BaseModel):
    model_config = ConfigDict(frozen=True, extra="ignore")

    pub: Annotated[str, Field(min_length=1), AfterValidator(conv_to_date_str)] = Field(
        alias="firstPublicationDate"
    )
    title: str = ""
    doi: str = ""
    abstract: str = Field(alias="abstractText", default="")


@final
class _ResultsCon(BaseModel):
    model_config = ConfigDict(frozen=True, extra="ignore")

    result: list[_ResultEle]


def _check_version(val: Any, /) -> str:
    if isinstance(val, dict):
        ver = val.get("version", "")
        print(f"Dictionary version detected - {val}")
        if isinstance(ver, str) and ver == "6.9":
            return ver
    if not isinstance(val, str) or val != "6.9":
        print(f"Wrong version detected - {val}")
        return ""
    return val


@final
class EuPmcSeaCon(BaseModel):
    model_config = ConfigDict(frozen=True, extra="ignore", validate_default=False)

    result_con: _ResultsCon = Field(alias="resultList")
    version: Annotated[str | dict[str, str], AfterValidator(_check_version)] = ""
    next: str = Field(alias="nextPageUrl", default="")
    cnt: int = Field(alias="hitCount", default=0)
