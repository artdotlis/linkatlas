import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from mpyflow.shared.container.data import InputData
from pydantic_core._pydantic_core import ValidationError
import re
from requests_cache import SQLiteCache, CachedSession, CachedResponse, OriginalResponse
from publink.model.container.literature import LitUpdatePackage, LitType
from publink.schema.open_alex import OpAlexWorksCon
from typing import final, Callable, Final, Iterator, Iterable, Any
from utilslink.context.process import get_worker_ctx
from utilslink.iter.pack import package_data
from utilslink.parse.date import conv_to_date_str
from utilslink.parse.string import pa_str
from utilslink.request.cache import create_sqlite_backend, create_simple_get_cache
from utilslink.request.cooldown import CoolDown


_OA_REQ = (
    "https://api.openalex.org/works?"
    + "per-page=200&"
    + "select=doi,publication_date,title,abstract_inverted_index"
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


def _create_abstract(r_ind: dict[str, tuple[int, ...]] | None, /) -> str:
    if r_ind is None:
        return ""
    last_ind = 0
    for ind_v in r_ind.values():
        new_m = max(ind_v)
        last_ind = new_m if new_m > last_ind else last_ind
    reversed_abs = ["" for _ in range(0, last_ind + 1)]
    for key, ind_v in r_ind.items():
        for pos in ind_v:
            reversed_abs[pos] = key
    return " ".join(reversed_abs)


def _request_open_alex_works(
    session: CachedSession,
    mail: str,
    last_req: Callable[[float], float],
    filter_values: tuple[str, ...],
    /,
) -> Iterable[tuple[str, str, str, str]]:
    fil = f"filter=abstract.search:{'|'.join(filter_values)}"
    main_req = (
        f"{_OA_REQ}&{fil},has_doi:true,has_abstract:true,"
        + "from_publication_date:1000-01-01"
    )
    if mail != "":
        main_req += f"&mailto={mail}"
    req = f"{main_req}&cursor=*"
    fail_cnt = 0
    while req != "":
        res = _fallback_retry(fail_cnt, req, session)
        if res is None:
            fail_cnt += 1
            req = req if fail_cnt < 3 else ""
            continue
        if res.status_code == 200:
            try:
                res_con = OpAlexWorksCon(**res.json())
                for res_data in res_con.results:
                    yield (
                        pa_str(res_data.doi),
                        conv_to_date_str(pa_str(res_data.publication_date)),
                        pa_str(res_data.title),
                        _create_abstract(res_data.abstract_inverted_index),
                    )
                req = ""
                if res_con.meta.next_cursor is not None:
                    req = main_req + f"&cursor={res_con.meta.next_cursor}"
            except ValidationError as val_exc:
                print(f"Malformed EU API response - {val_exc!s} - {req}")
                req = ""
            if res.from_cache:
                time.sleep(last_req(time.time()))
        else:
            req = ""


_CLEAN_DOI = re.compile(r"^https://doi\.org/")
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
class OpenAlexReader:
    __slots__ = (
        "__backend",
        "__data",
        "__in",
        "__iter",
        "__last_req",
        "__mail",
        "__out",
        "__package_size",
        "__version",
        "__work_dir",
    )

    def __init__(
        self, work_dir: Path, version: str, mail: str = "", package_size: int = 1000, /
    ) -> None:
        super().__init__()
        self.__in = True
        self.__out = False
        self.__iter: Iterator[tuple[LitUpdatePackage, ...]] | None = None
        self.__data: None | tuple[LitUpdatePackage, ...] = None
        self.__version = version
        self.__work_dir = work_dir
        self.__package_size = package_size
        self.__mail = mail
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
                "literature_open_alex", self.__work_dir
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
                for doi, date, title, abstract in _request_open_alex_works(
                    session,
                    self.__mail,
                    lambda call: self.__last_req.get_wait_time(call),
                    _FIL,
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
