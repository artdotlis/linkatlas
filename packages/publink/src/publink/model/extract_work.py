from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from mpyflow.shared.interfaces.logger import SyncStdoutInterface
from publink.model.literature_files import read_lit_file_txt
from taxalink.manager.manager import TaxaReportManager
from typing import final, Iterable, AsyncIterator
from saim.designation.manager import AcronymManager
from utilslink.container.bio_ent import AddDes, AddTaxa, AddSeq
from utilslink.extract.bio_ent import extract_bio_entity
from utilslink.extract.taxa import get_gen_spe_set
from utilslink.iter.pack import package_data


type _CON_ANA = tuple[tuple[int, str | Path], ...]
type _RES = AddDes | AddTaxa | AddSeq


@final
class ExtractWork:

    __slots__: tuple[str, ...] = (
        "__acronym_manager",
        "__package_size",
        "__taxa",
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
        super().__init__()

    def __work(self, req_id: int, req: str | Path, /) -> Iterable[_RES]:
        req_txt = req
        if isinstance(req_txt, Path):
            req_txt = read_lit_file_txt(req_txt)
        yield from extract_bio_entity(
            self.__acronym_manager, self.__taxa, req_id, req_txt
        )

    async def work(
        self,
        _sync_out: SyncStdoutInterface,
        data_con: _CON_ANA,
        _th_exc: ThreadPoolExecutor,
        /,
    ) -> AsyncIterator[tuple[_RES, ...]]:
        for package in package_data(
            (res for tid, mat in data_con for res in self.__work(tid, mat)),
            self.__package_size,
            self.__package_size,
            lambda _val: 1,
        ):
            yield package

    def on_close(self, _sync_out: SyncStdoutInterface, /) -> None:
        del self.__acronym_manager
