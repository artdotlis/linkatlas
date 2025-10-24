import time
from pathlib import Path

from mpyflow.shared.container.data import InputData

from concurrent.futures.thread import ThreadPoolExecutor

from requests_cache import SQLiteCache, CachedSession

from seqlink.model.container.sequence import SeqUpdatePackage
from typing import final, Iterator, Iterable, Any, Callable
from utilslink.context.process import get_worker_ctx
from utilslink.iter.pack import package_data
from utilslink.request.cache import create_sqlite_backend, create_simple_get_cache
from utilslink.request.cooldown import CoolDown
from utilslink.schema.sequence import SeqType, AsmLvl
from utilslink.schema.taxa import PIDType


def _request_ena_search(
    _session: CachedSession, _last_req: Callable[[float], float], /
) -> Iterable[tuple[str, str, str, int | None, SeqType, int, AsmLvl | None, str]]:
    # TODO finish
    yield from tuple()


@final
class ENAReader:
    __slots__ = (
        "__backend",
        "__data",
        "__in",
        "__iter",
        "__last_req",
        "__out",
        "__package_size",
        "__version",
        "__work_dir",
    )

    def __init__(self, work_dir: Path, version: str, package_size: int = 1000, /) -> None:
        super().__init__()
        self.__in = True
        self.__out = False
        self.__iter: Iterator[tuple[SeqUpdatePackage, ...]] | None = None
        self.__data: None | tuple[SeqUpdatePackage, ...] = None
        self.__version = version
        self.__work_dir = work_dir
        self.__package_size = package_size
        mpc = get_worker_ctx()
        cur_time = time.time()
        self.__last_req: CoolDown = CoolDown(
            lock=mpc.Lock(),
            last_request=mpc.Value("f", cur_time),
            day_request=mpc.Value("f", cur_time),
            counter=mpc.Value("i", 0),
        )
        self.__backend: SQLiteCache | None = None

    @property
    def backend(self) -> SQLiteCache:
        if self.__backend is None:
            self.__backend = create_sqlite_backend("sequence_ena", self.__work_dir)(
                7, 200
            )
        return self.__backend

    @property
    def iter_data(self) -> Iterator[tuple[SeqUpdatePackage, ...]]:
        if self.__iter is None:
            self.__iter = iter(self.synchronize())
        return self.__iter

    def has_input(self) -> bool:
        return self.__in

    def has_output(self) -> bool:
        return self.__out

    def wr_on_close(self) -> None:
        self.backend.close()  # type: ignore

    def on_error(self) -> None:
        self.backend.close()  # type: ignore

    def synchronize(self) -> Iterable[tuple[SeqUpdatePackage, ...]]:
        with create_simple_get_cache(7, self.backend) as session:
            data_gen = (
                SeqUpdatePackage(
                    version=self.__version,
                    seq_typ=typ,
                    len=length,
                    lvl=lvl,
                    desc=desc,
                    seq_acc=acc,
                    pub_date=date,
                    misc=misc,
                    tax_id=f"{nid}" if nid is not None else "",
                    tax_id_type=PIDType.ncbi,
                )
                for acc, date, desc, nid, typ, length, lvl, misc in _request_ena_search(
                    session,
                    lambda call: self.__last_req.get_wait_time(call),
                )
                if acc != "" and (nid is not None or desc != "") and date != ""
            )
            for package in package_data(
                data_gen, self.__package_size, self.__package_size, lambda _val: 1
            ):
                yield package

    async def read(
        self, _th_exc: ThreadPoolExecutor, /
    ) -> InputData[tuple[SeqUpdatePackage, ...]] | None:
        buf = next(self.iter_data, None)
        res = buf
        if self.__data is not None:
            res = self.__data
        self.__data = buf
        if res is None:
            return None
        return InputData(tuple(dat for dat in res))

    async def write(self, _data: Any, _th_exc: ThreadPoolExecutor, /) -> bool:
        raise NotImplementedError("Not implemented")

    async def running(self, _th_exc: ThreadPoolExecutor, _provider_cnt: int, /) -> bool:
        if self.__data is not None:
            return True
        self.__data = next(self.iter_data, None)
        return self.__data is not None
