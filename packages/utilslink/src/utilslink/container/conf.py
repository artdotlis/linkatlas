from dataclasses import dataclass
from typing import final


@final
@dataclass(frozen=True, kw_only=True, slots=True)
class LPSNConf:
    user: str
    pw: str
    url: str
