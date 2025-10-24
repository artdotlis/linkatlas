from dataclasses import dataclass


@dataclass(slots=True, frozen=True, kw_only=True)
class DesDB:
    des: str
    ori_acr: str
    ori_core: str
    ori_suf: str

    @property
    def core(self) -> str:
        return self.ori_core.upper()

    @property
    def suf(self) -> str:
        return self.ori_suf.upper()

    @property
    def acr(self) -> str:
        return self.ori_acr.upper()
