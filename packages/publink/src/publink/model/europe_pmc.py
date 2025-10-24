import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from mpyflow.shared.container.data import InputData
from requests_cache import SQLiteCache, CachedSession, CachedResponse, OriginalResponse
from publink.model.container.literature import LitUpdatePackage, LitType
from utilslink.context.process import get_worker_ctx
from utilslink.iter.pack import package_data
from utilslink.request.cache import create_simple_get_cache, create_sqlite_backend
from typing import Callable, Final, final, Iterator, Iterable, Any
from pydantic import ValidationError
from publink.schema.europe_pmc import EuPmcSeaCon
from utilslink.request.cooldown import CoolDown

_MAIN_API: Final[str] = "https://www.ebi.ac.uk/europepmc/webservices/rest/"
_ALL_SEA_API: Final[str] = (
    f"{_MAIN_API}search?format=json&pageSize=1000&resultType=core&query="
)


def _fallback_retry(
    fail_cnt: int, req: str, session: CachedSession, /
) -> CachedResponse | OriginalResponse | None:
    try:
        return session.get(req, timeout=60)
    except Exception:
        if fail_cnt < 3:
            print(f"[RETRY-{fail_cnt}] after 10 min")
            time.sleep(600)
    return None


def _request_eu_pmc_search(
    session: CachedSession, last_req: Callable[[float], float], query: str, /
) -> Iterable[tuple[str, str, str, str]]:
    req = _ALL_SEA_API + query
    fail_cnt = 0
    while req != "":
        res = _fallback_retry(fail_cnt, req, session)
        if res is None:
            fail_cnt += 1
            req = req if fail_cnt < 3 else ""
            continue
        if res.status_code == 200:
            try:
                res_con = EuPmcSeaCon(**res.json())
                for res_data in res_con.result_con.result:
                    yield (
                        res_data.doi,
                        res_data.pub,
                        res_data.title,
                        res_data.abstract,
                    )
                req = res_con.next
            except ValidationError as val_exc:
                print(f"Malformed EU API response - {val_exc!s} - {req}")
                req = ""
            if res.from_cache:
                time.sleep(last_req(time.time()))
        else:
            req = ""


_FIL: Final[tuple[str, ...]] = (
    "strain",
    "subspecies",
    "species",
    "culture",
    "sample",
    "isolate",
    "isolation",
)


@final
class EuPmcReader:
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
        self.__iter: Iterator[tuple[LitUpdatePackage, ...]] | None = None
        self.__data: None | tuple[LitUpdatePackage, ...] = None
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
            self.__backend = create_sqlite_backend(
                "literature_europe_pmc", self.__work_dir
            )(7, 200)
        return self.__backend

    @property
    def iter_data(self) -> Iterator[tuple[LitUpdatePackage, ...]]:
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

    def synchronize(self) -> Iterable[tuple[LitUpdatePackage, ...]]:
        with create_simple_get_cache(7, self.backend) as session:
            data_gen = (
                LitUpdatePackage(
                    version=self.__version,
                    txt_typ=LitType.abstract,
                    data=(doi.upper(), date, f"{title} {abstract}".strip()),
                )
                for doi, date, title, abstract in _request_eu_pmc_search(
                    session,
                    lambda call: self.__last_req.get_wait_time(call),
                    " OR ".join(_FIL),
                )
                if not (doi == "" or (title == "" and abstract == "") or date == "")
            )
            for package in package_data(
                data_gen, self.__package_size, self.__package_size, lambda _val: 1
            ):
                yield package

    async def read(
        self, _th_exc: ThreadPoolExecutor, /
    ) -> InputData[tuple[LitUpdatePackage, ...]] | None:
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
