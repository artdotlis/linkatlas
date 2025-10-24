import time

from requests import RequestException
from mpyflow.shared.container.data import InputData

from concurrent.futures.thread import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from taxalink.schema.designation import DesSource
from utilslink.container.conf import LPSNConf
from utilslink.context.process import get_worker_ctx
from utilslink.iter.pack import package_data
from utilslink.parse.string import conv_to_str
from utilslink.request.cache import create_sqlite_backend, create_simple_get_cache
from utilslink.request.cooldown import CoolDown
from utilslink.request.jwt import JWTCred
from taxalink.model.container.taxa import TaxonomyAdd, PIDType, TaxUpdatePackage
from taxalink.schema.lpsn import LPSNCat, LPSNId, LpsnOrgC
from typing import final, Iterable, Final, Callable, Any, Iterator
from requests_cache import CachedSession, SQLiteCache

from utilslink.schema.taxa import GBIFRanksE, is_rank, parse_rank, get_lpsn_ranks_list

LPSN_API: Final[str] = "https://api.lpsn.dsmz.de/"
LPSN_ADV: Final[str] = f"{LPSN_API}advanced_search?"
LPSN_ORG: Final[str] = f"{LPSN_API}fetch/"


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class _SesCon:
    lpsn_cred: JWTCred
    session: CachedSession
    last_req: Callable[[float], float]


def _create_header(lpsn_cred: JWTCred, /) -> dict[str, str]:
    return {
        "Accept": "application/json",
        "Authorization": f"Bearer {lpsn_cred.token.access}",
    }


def _request_next[
    RT: (LPSNCat, LPSNId)
](
    req_res: RT,
    ses_con: _SesCon,
    cont: type[RT],
    cnt: int = 1,
    /,
) -> (
    tuple[RT, bool] | None
):
    if req_res.next is None or req_res.next == "" or cnt > 3:
        return None
    err_401 = False
    headers = _create_header(ses_con.lpsn_cred)
    try:
        res = ses_con.session.get(req_res.next, headers=headers, timeout=60)
        if res.status_code == 200:
            return cont(**res.json()), res.from_cache
        elif res.status_code == 401:
            err_401 = True
    except RequestException as exc:
        if exc.response is not None and exc.response.status_code == 401:
            err_401 = True
    if err_401:
        time.sleep(1)
        ses_con.lpsn_cred.refresh()
        return _request_next(req_res, ses_con, cont, cnt + 1)
    return None


def _request_lpsn_cat(
    category: str,
    ses_con: _SesCon,
    /,
) -> Iterable[int]:
    if category != "":
        req_url = f"{LPSN_ADV}category={category}"
        res_con = LPSNCat(next=req_url, results=[])
        while (new_res := _request_next(res_con, ses_con, LPSNCat)) is not None:
            res_con, from_cache = new_res
            for lid in res_con.results:
                yield lid
            if not from_cache:
                time.sleep(ses_con.last_req(time.time()))


def _request_lpsn_org(
    lpsn_id: list[int],
    ses_con: _SesCon,
    /,
) -> Iterable[LpsnOrgC]:
    if len(lpsn_id) > 0:
        req_url = f"{LPSN_ORG}{';'.join(map(str, lpsn_id))}"
        res_con = LPSNId(next=req_url, results=[])
        while (new_res := _request_next(res_con, ses_con, LPSNId)) is not None:
            res_con, from_cache = new_res
            for con in res_con.results:
                yield con
            if not from_cache:
                time.sleep(ses_con.last_req(time.time()))


def _get_missing_lpsn(
    taxa: dict[int, LpsnOrgC],
    ses_con: _SesCon,
    /,
) -> dict[int, LpsnOrgC]:
    mis_res: dict[int, LpsnOrgC] = {}
    for tax in taxa.values():
        for pid in (tax.lpsn_parent_id, tax.lpsn_correct_name_id):
            if pid is None or pid in mis_res or pid in taxa:
                continue
            for res in _request_lpsn_org([pid], ses_con):
                mis_res[res.id] = res
    return mis_res


def _get_lpsn_rank(lpsn: LpsnOrgC, /) -> GBIFRanksE:
    rank = lpsn.category.upper()
    if is_rank(rank):
        return parse_rank(rank)
    return GBIFRanksE.oth


def _create_walk(
    pos_id: int,
    path: dict[int, int | None],
    cor: dict[int, int | None],
    taxa: dict[int, LpsnOrgC],
    visited: set[int],
    /,
) -> Iterable[LpsnOrgC]:
    if pos_id not in visited:
        visited.add(pos_id)
        corid = cor.get(pos_id, None)
        if corid is not None and corid != pos_id:
            yield from _create_walk(corid, path, cor, taxa, visited)
        parid = path.get(pos_id, None)
        if parid is not None:
            yield from _create_walk(parid, path, cor, taxa, visited)
        if pos_id in taxa:
            yield taxa[pos_id]


def _prepare_walk(
    all_ids: set[int], ses_con: _SesCon, /
) -> tuple[dict[int, int | None], dict[int, int | None], dict[int, LpsnOrgC]]:
    path_up: dict[int, int | None] = dict()
    correct: dict[int, int | None] = dict()
    taxa: dict[int, LpsnOrgC] = dict()
    all_sorted = sorted(all_ids)
    for part in range(int(len(all_sorted) / 100) + 1):
        for lpsn_org in _request_lpsn_org(
            all_sorted[part * 100 : part * 100 + 100], ses_con
        ):
            if lpsn_org.id != lpsn_org.lpsn_parent_id:
                path_up[lpsn_org.id] = lpsn_org.lpsn_parent_id
            correct[lpsn_org.id] = lpsn_org.lpsn_correct_name_id
            taxa[lpsn_org.id] = lpsn_org
    taxa.update(_get_missing_lpsn(taxa, ses_con))
    return path_up, correct, taxa


def _get_taxa_info(
    path_up: dict[int, int | None],
    correct: dict[int, int | None],
    taxa: dict[int, LpsnOrgC],
    /,
) -> Iterable[TaxonomyAdd]:
    visited: set[int] = set()
    for tax_id in taxa:
        for wal in _create_walk(tax_id, path_up, correct, taxa, visited):
            cid = wal.lpsn_correct_name_id
            pname = ""
            if (
                wal.lpsn_parent_id is not None
                and (par := taxa.get(wal.lpsn_parent_id, None)) is not None
            ):
                pname = par.full_name
            if cid is None:
                cid = wal.id
            yield TaxonomyAdd(
                pid=str(wal.id),
                pid_type=PIDType.lpsn,
                name=wal.full_name,
                correct_pid=conv_to_str(cid),
                correct=wal.lpsn_correct_name_id is not None
                and wal.lpsn_correct_name_id == wal.id,
                parent_pid=conv_to_str(wal.lpsn_parent_id),
                parent_name=conv_to_str(pname),
                rank=_get_lpsn_rank(wal),
                type_strain=tuple(wal.type_strain_names),
            )


@final
class LpsnTaxReader:
    __slots__ = (
        "__backend",
        "__con",
        "__data",
        "__in",
        "__iter",
        "__kcl",
        "__last_req",
        "__out",
        "__package_size",
        "__version",
        "__work_dir",
    )

    def __init__(
        self, work_dir: Path, conf: LPSNConf, version: str, package_size: int = 1000, /
    ) -> None:
        super().__init__()
        self.__in = True
        self.__out = False
        self.__iter: Iterator[tuple[TaxUpdatePackage, ...]] | None = None
        self.__data: None | tuple[TaxUpdatePackage, ...] = None
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
        self.__kcl = JWTCred(conf.user, conf.pw, "api.lpsn.public", conf.url)
        self.__backend: SQLiteCache | None = None

    @property
    def backend(self) -> SQLiteCache:
        if self.__backend is None:
            self.__backend = create_sqlite_backend("taxon_name_lpsn", self.__work_dir)(
                7, 200
            )
        return self.__backend

    @property
    def iter_data(self) -> Iterator[tuple[TaxUpdatePackage, ...]]:
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

    def synchronize(self) -> Iterable[tuple[TaxUpdatePackage, ...]]:
        with create_simple_get_cache(7, self.backend) as session:
            ses_con = _SesCon(
                session=session,
                lpsn_cred=self.__kcl,
                last_req=lambda call: self.__last_req.get_wait_time(call),
            )
            all_ids = set(
                lid
                for cat in get_lpsn_ranks_list()
                for lid in _request_lpsn_cat(cat.lower(), ses_con)
            )
            path_up, correct, taxa = _prepare_walk(all_ids, ses_con)
            for package in package_data(
                (
                    TaxUpdatePackage(
                        version=self.__version, des_src=DesSource.sy_db, data=node
                    )
                    for node in _get_taxa_info(path_up, correct, taxa)
                ),
                self.__package_size,
                self.__package_size,
                lambda _val: 1,
            ):
                yield package

    async def read(
        self, _th_exc: ThreadPoolExecutor, /
    ) -> InputData[tuple[TaxUpdatePackage, ...]] | None:
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
