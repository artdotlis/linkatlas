from taxalink.model.container.database import AddType
from taxalink.schema.designation import DesSource
from typing import final, AsyncIterator, Iterable
from saim.designation.manager import AcronymManager
from concurrent.futures.thread import ThreadPoolExecutor
from mpyflow.shared.interfaces.logger import SyncStdoutInterface

from utilslink.extract.bio_ent import extract_designation
from utilslink.iter.pack import package_data

type _CON_ANA = tuple[tuple[int, DesSource, tuple[str, ...]], ...]


@final
class ExtractWork:

    __slots__: tuple[str, ...] = ("__acronym_manager", "__package_size")

    def __init__(self, version: str, package_size: int = 1000, /) -> None:
        self.__acronym_manager = AcronymManager(version, 100)
        self.__package_size = package_size
        super().__init__()

    def __work(
        self, req_id: int, req_typ: DesSource, req_txt: str, /
    ) -> Iterable[AddType]:
        yield from (
            AddType(did=req_id, des_source=req_typ, des=des)
            for des in extract_designation(self.__acronym_manager, req_id, req_txt)
        )

    async def work(
        self,
        _sync_out: SyncStdoutInterface,
        data_con: _CON_ANA,
        _th_exc: ThreadPoolExecutor,
        /,
    ) -> AsyncIterator[tuple[AddType, ...]]:
        for package in package_data(
            (
                res
                for tid, src, mat in data_con
                for to_ana in mat
                for res in self.__work(tid, src, to_ana)
            ),
            self.__package_size,
            self.__package_size,
            lambda _val: 1,
        ):
            yield package

    def on_close(self, _sync_out: SyncStdoutInterface, /) -> None:
        del self.__acronym_manager
