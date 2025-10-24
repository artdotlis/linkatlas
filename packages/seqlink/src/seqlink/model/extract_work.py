from pathlib import Path
from taxalink.manager.manager import TaxaReportManager

from typing import final, AsyncIterator, Iterable
from saim.designation.manager import AcronymManager
from concurrent.futures.thread import ThreadPoolExecutor
from mpyflow.shared.interfaces.logger import SyncStdoutInterface

from utilslink.container.bio_ent import AddDes, AddIdTaxa
from utilslink.extract.bio_ent import extract_taxa_des
from utilslink.extract.taxa import get_gen_spe_set
from utilslink.iter.pack import package_data
from utilslink.schema.taxa import PIDType

type _CON_ANA = tuple[tuple[int, str, PIDType | None, str], ...]


@final
class ExtractWork:

    __slots__: tuple[str, ...] = (
        "__acronym_manager",
        "__package_size",
        "__taxa",
        "__taxa_rep",
        "__work_dir",
    )

    def __init__(
        self,
        work_dir: Path,
        version: str,
        package_size: int = 1000,
        /,
    ) -> None:
        self.__acronym_manager = AcronymManager(version, 100)
        self.__package_size = package_size
        self.__taxa = get_gen_spe_set(TaxaReportManager(work_dir))
        self.__taxa_rep: None | TaxaReportManager = None
        self.__work_dir = work_dir
        super().__init__()

    @property
    def _reporter(self) -> TaxaReportManager:
        if self.__taxa_rep is None:
            self.__taxa_rep = TaxaReportManager(self.__work_dir)
        return self.__taxa_rep

    def __work(self, data_con: _CON_ANA, /) -> Iterable[AddDes | AddIdTaxa]:
        yield from (
            res
            for tid, mat, *_ in data_con
            for res in extract_taxa_des(self.__acronym_manager, self.__taxa, tid, mat)
        )
        yield from (
            AddIdTaxa(did=tid, taxa=res_t, pid=str(pid), pid_type=pid_t)
            for tid, *_, pid_t, pid in data_con
            if pid_t is not None
            and (res_t := self._reporter.get_name_by_id(str(pid), pid_t)) is not None
        )

    async def work(
        self,
        _sync_out: SyncStdoutInterface,
        data_con: _CON_ANA,
        _th_exc: ThreadPoolExecutor,
        /,
    ) -> AsyncIterator[tuple[AddDes | AddIdTaxa, ...]]:
        for package in package_data(
            self.__work(data_con),
            self.__package_size,
            self.__package_size,
            lambda _val: 1,
        ):
            yield package

    def on_close(self, _sync_out: SyncStdoutInterface, /) -> None:
        del self.__acronym_manager
