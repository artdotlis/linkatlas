from collections import defaultdict
from concurrent.futures.thread import ThreadPoolExecutor
from enum import Enum
from io import BytesIO

import tarfile
from re import Pattern
import re
from taxalink.schema.designation import DesSource
from utilslink.container.conf import AgentConf
from utilslink.error.exceptions import RequestURIEx, ValidationEx
from utilslink.iter.pack import package_data
from utilslink.parse.string import conv_to_str
from utilslink.request.cache import create_simple_get_cache, create_sqlite_backend
from taxalink.model.container.taxa import (
    TaxonomyDel,
    PIDType,
    TaxonomyCom,
    TaxonomyAdd,
    TaxUpdatePackage,
    TaxonomyLink,
)

from typing import final, Final, Iterable, IO, Any, Iterator
from pathlib import Path
from mpyflow.shared.container.data import InputData
from requests_cache import SQLiteCache

from utilslink.schema.taxa import (
    GBIFRanksE,
    DomainE,
    parse_domain,
    is_rank,
    is_ncbi_rank,
    parse_ncbi_rank,
)


class _NameClass(str, Enum):
    nam = "scientific name"
    syn = "synonym"
    tst = "type material"
    eq_nam = "equivalent name"


_NCBI_FTP: Final[str] = "https://ftp.ncbi.nih.gov/pub/taxonomy/taxdump.tar.gz"
_CLEAN: Final[tuple[Pattern[str], ...]] = (re.compile(r"^culture-collection:\s+"),)

_NODE_REG: Final[Pattern[str]] = re.compile(
    r"^" + r"\s*\|\s*".join(["1", "1", "no rank"]) + r"\s*\|.*$"
)

_NAMES_REG: Final[Pattern[str]] = re.compile(
    r"^" + r"\s*\|\s*".join(["1", "all", r"\s", "synonym"]) + r"(\s*\|.*)?$"
)
_MERGED_REG: Final[Pattern[str]] = re.compile(r"^\s*\d+\s*\|\s*\d+\s*(\|.*)?$")
_DEL_REG: Final[Pattern[str]] = re.compile(r"^\s*\d+\s*(\|.*)?$")

_FIELD_TAX_TERM: Final[str] = "\t|\t"
_ROW_TAX_TERM: Final[str] = "\t|\n"

_SPE_NAME_FILTER = re.compile(r"\sspp?\.$|^[a-z]")


def read_ncbi_tax_deleted(tax_csv: IO[bytes], /) -> Iterable[TaxonomyDel]:
    for line in tax_csv:
        line_dec = line.decode("utf-8")
        if _DEL_REG.match(line_dec) is None:
            raise ValidationEx("Deleted tax file is malformed!")
        del_id, *_ = line_dec.strip(_ROW_TAX_TERM).split(_FIELD_TAX_TERM)
        yield TaxonomyDel(pid=str(del_id), pid_type=PIDType.ncbi)


def read_ncbi_tax_merged(tax_csv: IO[bytes], /) -> Iterable[TaxonomyCom]:
    for line in tax_csv:
        line_dec = line.decode("utf-8")
        if _MERGED_REG.match(line_dec) is None:
            raise ValidationEx("Merged tax file is malformed!")
        old_id, new_id, *_ = line_dec.strip(_ROW_TAX_TERM).split(_FIELD_TAX_TERM)
        yield TaxonomyCom(pid=str(old_id), merge_pid=str(new_id), pid_type=PIDType.ncbi)


def read_ncbi_tax_names(
    tax_csv: IO[bytes], ranks: dict[int, GBIFRanksE], /
) -> tuple[dict[int, str], dict[int, set[str]], dict[int, set[str]]]:
    cor_nam: dict[int, str] = {}
    syn_nam: dict[int, set[str]] = defaultdict(set)
    typ_str: dict[int, set[str]] = defaultdict(set)
    for ind, line in enumerate(tax_csv):
        line_dec = line.decode("utf-8")
        if ind == 0 and _NAMES_REG.match(line_dec) is None:
            raise ValidationEx("Names tax file is malformed!")
        nid, name, _, cla = line_dec.strip(_ROW_TAX_TERM).split(_FIELD_TAX_TERM)
        nid_int = int(nid)
        if nid_int in ranks:
            match cla:
                case str(_NameClass.nam.value):
                    cor_nam[nid_int] = name
                case str(_NameClass.syn.value) | str(_NameClass.eq_nam.value):
                    syn_nam[nid_int].add(name)
                case str(_NameClass.tst.value):
                    typ_str[nid_int].add(name)
    return cor_nam, syn_nam, typ_str


def _walk_to_parent(
    pos_id: int, path: dict[int, int], visited: set[int], /
) -> Iterable[int]:
    if pos_id not in visited:
        visited.add(pos_id)
        parid = path.get(pos_id, None)
        if parid is not None:
            yield from _walk_to_parent(parid, path, visited)
        yield pos_id


def _is_reasonable_next_step(
    cur_rank: GBIFRanksE, next_rank: GBIFRanksE, cur_name: str, /
) -> bool:
    if _SPE_NAME_FILTER.search(cur_name) is not None:
        return False
    if next_rank == GBIFRanksE.sub_spe:
        return False
    if next_rank == GBIFRanksE.spe and cur_rank != GBIFRanksE.sub_spe:
        return False
    if cur_rank == GBIFRanksE.str:
        return False
    return True


def _is_correct_fin(
    path: dict[int, int], ranks: dict[int, GBIFRanksE], cor: dict[int, str], /
) -> bool:
    for cur_id, par_id in path.items():
        if (
            ranks.get(par_id, GBIFRanksE.oth) == GBIFRanksE.dom
            and parse_domain(cor.get(par_id, "")) != DomainE.ukn
        ):
            return True
        spe_gen = (GBIFRanksE.spe, GBIFRanksE.gen)
        if ranks.get(par_id, GBIFRanksE.oth) in spe_gen:
            return True
        if ranks.get(cur_id, GBIFRanksE.oth) in spe_gen:
            return True
    return False


def _walk_to_domain(
    pos_id: int,
    walked: dict[int, int],
    path: dict[int, int],
    ranks: dict[int, GBIFRanksE],
    cor: dict[int, str],
    /,
) -> bool:
    par_id = path.get(pos_id, None)
    if par_id is None or ranks[pos_id] == GBIFRanksE.dom:
        return _SPE_NAME_FILTER.search(cor[pos_id]) is None
    walked[pos_id] = par_id
    if _is_reasonable_next_step(ranks[pos_id], ranks[par_id], cor[pos_id]):
        return _walk_to_domain(par_id, walked, path, ranks, cor)
    return False


def _prune_path(
    path: dict[int, int], ranks: dict[int, GBIFRanksE], cor: dict[int, str], /
) -> dict[int, int]:
    pruned_path: dict[int, int] = {}
    visited: set[int] = set()
    for cur_id in path.keys():
        if cur_id in visited:
            continue
        walked: dict[int, int] = {}
        if _walk_to_domain(cur_id, walked, path, ranks, cor) and _is_correct_fin(
            walked, ranks, cor
        ):
            pruned_path.update(walked)
        visited.update(walked.keys())
    return pruned_path


def _prune_taxa(taxa: dict[int, str], /) -> Iterable[tuple[int, str]]:
    for tax_id, tax_nam in taxa.items():
        if _SPE_NAME_FILTER.search(tax_nam) is None:
            yield tax_id, tax_nam


def read_ncbi_tax_nodes(
    tax_csv: IO[bytes], /
) -> tuple[dict[int, GBIFRanksE], dict[int, int]]:
    ranks: dict[int, GBIFRanksE] = {}
    path: dict[int, int] = dict()
    for ind, line in enumerate(tax_csv):
        line_dec = line.decode("utf-8")
        if ind == 0 and _NODE_REG.match(line_dec) is None:
            raise ValidationEx("Node tax file is malformed!")
        rank: str
        tax_id, parent, rank, *_ = line_dec.strip(_ROW_TAX_TERM).split(_FIELD_TAX_TERM)
        rank = rank.upper()
        if not (is_rank(rank) or is_ncbi_rank(rank)):
            print(f"{rank} - unknown!")
            continue
        tax_id_int = int(tax_id)
        par_id_int = int(parent)
        if tax_id_int != par_id_int:
            path[tax_id_int] = par_id_int
        ranks[tax_id_int] = parse_ncbi_rank(rank)
    return ranks, path


def _create_to_add_taxa(
    path: dict[int, int],
    ranks: dict[int, GBIFRanksE],
    cor: dict[int, str],
    syn: dict[int, set[str]],
    typ: dict[int, set[str]],
    /,
) -> Iterable[TaxonomyAdd]:
    visited: set[int] = set()
    for cor_id in cor.keys():
        for cur_id in _walk_to_parent(cor_id, path, visited):
            par_id = path.get(cur_id, None)
            yield TaxonomyAdd(
                pid=str(cur_id),
                pid_type=PIDType.ncbi,
                name=cor[cur_id],
                correct_pid=str(cur_id),
                correct=True,
                parent_pid=conv_to_str(par_id),
                parent_name=cor[par_id] if par_id is not None else "",
                rank=ranks[cur_id],
                type_strain=tuple(typ[cur_id]),
            )
            for syn_name in syn.get(cur_id, tuple()):
                yield TaxonomyAdd(
                    pid=str(cur_id),
                    pid_type=PIDType.ncbi,
                    name=syn_name,
                    correct_pid=str(cur_id),
                    correct=False,
                    rank=ranks[cur_id],
                )


def _extract_from_file(
    res_down: bytes, /
) -> Iterable[TaxonomyCom | TaxonomyDel | TaxonomyAdd | TaxonomyLink]:
    with tarfile.open(fileobj=BytesIO(res_down), mode="r:gz") as tar:
        if (ext_res := tar.extractfile("delnodes.dmp")) is not None:
            yield from read_ncbi_tax_deleted(ext_res)
        if (ext_res := tar.extractfile("merged.dmp")) is not None:
            yield from read_ncbi_tax_merged(ext_res)
        if (ext_res := tar.extractfile("nodes.dmp")) is not None:
            ranks, tmp_path = read_ncbi_tax_nodes(ext_res)
            if (ext_res := tar.extractfile("names.dmp")) is not None:
                tmp_cor, syn, typ = read_ncbi_tax_names(ext_res, ranks)
                path = _prune_path(tmp_path, ranks, tmp_cor)
                cor = {cid: cna for cid, cna in _prune_taxa(tmp_cor)}
                yield from _create_to_add_taxa(path, ranks, cor, syn, typ)


@final
class NcbiTaxReader:
    __slots__ = (
        "__acf",
        "__backend",
        "__con",
        "__data",
        "__file",
        "__in",
        "__iter",
        "__out",
        "__package_size",
        "__version",
        "__work_dir",
    )

    def __init__(
        self, work_dir: Path, version: str, agent: AgentConf, package_size: int = 1000, /
    ) -> None:
        super().__init__()
        file = "taxon_name_ncbi"
        self.__backend: SQLiteCache | None = None
        self.__in = True
        self.__out = False
        self.__iter: Iterator[tuple[TaxUpdatePackage, ...]] | None = None
        self.__data: None | tuple[TaxUpdatePackage, ...] = None
        self.__version = version
        self.__work_dir = work_dir
        self.__file = file
        self.__acf = agent
        self.__package_size = package_size

    @property
    def backend(self) -> SQLiteCache:
        if self.__backend is None:
            self.__backend = create_sqlite_backend(self.__file, self.__work_dir)(7, 200)
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
        with create_simple_get_cache(7, self.backend, self.__acf.contact) as session:
            res = session.get(_NCBI_FTP, stream=True, timeout=60)
            if res.status_code == 200:
                res_down = res.content
            else:
                raise RequestURIEx(f"Could not get {_NCBI_FTP}")

            for package in package_data(
                (
                    TaxUpdatePackage(
                        version=self.__version, des_src=DesSource.sy_db, data=node
                    )
                    for node in _extract_from_file(res_down)
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
