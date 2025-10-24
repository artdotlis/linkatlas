import re
from typing import Final, Protocol, Iterable
from utilslink.error.exceptions import BootstrapEx
from utilslink.schema.taxa import GBIFRanksE

_BIN_RE: Final[re.Pattern[str]] = re.compile(r"^([A-Z][a-z]+)\s+([a-z]+)$")
_SPE_RE: Final[re.Pattern[str]] = re.compile(r"^\s([a-z]+)")


class _RankTaxa(Protocol):
    @property
    def name(self) -> str: ...


class TaxaReportManagerP(Protocol):
    def get_all_rank(self, rank: GBIFRanksE, /) -> Iterable[_RankTaxa]: ...
    def close(self) -> None: ...


def get_gen_spe_set(man: TaxaReportManagerP, /) -> dict[str, set[str] | None]:
    genera: dict[str, set[str] | None] = {
        gen.name.lower(): None for gen in man.get_all_rank(GBIFRanksE.gen)
    }
    for spe in man.get_all_rank(GBIFRanksE.spe):
        mat = _BIN_RE.match(spe.name)
        if mat is None or (gen_l := mat.group(1).lower()) not in genera:
            continue
        spe_s = genera[gen_l]
        if spe_s is None:
            genera[gen_l] = {mat.group(2)}
        else:
            spe_s.add(mat.group(2))
    man.close()
    if len(genera) == 0:
        raise BootstrapEx("Could not initialize taxa set")
    return genera


def get_spe_name(spe_s: set[str] | None, gen: str, pos: int, full: str, /) -> str:
    if spe_s is None:
        return gen
    spe_m = _SPE_RE.match(full[pos + len(gen) :])
    if spe_m is not None and spe_m.group(1) in spe_s:
        return f"{gen} {spe_m.group(1)}"
    return gen
