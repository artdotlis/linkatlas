import datetime
import random

import sqlite3
from taxalink.schema.designation import DesSource

from taxalink.model.database.proc.type_strain import add_type_strain
from saim.designation.extract_ccno import get_syn_eq_struct

from taxalink.model.container.database import (
    TaxUpdRes,
    ReportTax,
    TaxStatus,
    AddType,
    DefCmd,
    TW_RES_UP_E,
    TW_RES_REP_E,
    TW_REQ_UP_E,
    TW_REQ_REP_E,
)
from taxalink.model.container.taxa import (
    TaxonomyAdd,
    TaxonomyLink,
    PIDType,
    TaxonomyDel,
    TaxonomyCom,
    TaxUpdatePackage,
    TaxonomyResults,
)
from taxalink.model.database.proc.taxa import (
    update_taxa_status,
    get_taxa_id,
    add_taxa,
    delete_taxa,
    search_taxa,
    merge_taxa_id,
    get_taxa_db_status,
)
from taxalink.model.database.proc.type_strain import remove_type_strain
from typing import Iterable, Final
from utilslink.container.database import DesDB
from utilslink.verify.version import is_version_newer

TYP_DB_NAME: Final[str] = "taxalink_atlas_database.sqlite"
EXP_DAYS: Final[int] = 7


def _add_type_strain(
    tid: int, des_src: DesSource, des: str, dbc: sqlite3.Cursor, /
) -> None:
    acr, core, suf = get_syn_eq_struct(des)
    add_type_strain(
        dbc, tid, des_src, DesDB(des=des, ori_acr=acr, ori_core=core, ori_suf=suf)
    )


def _add_taxa(taxa: TaxonomyAdd | TaxonomyLink, dbc: sqlite3.Cursor, /) -> TaxUpdRes:
    if isinstance(taxa, TaxonomyLink):
        tax_id, last_update, version, _ = get_taxa_id(dbc, taxa)
    else:
        tax_id, last_update, version = add_taxa(dbc, taxa)
    if tax_id is None:
        tax_id = 0
    return TaxUpdRes(
        tid=tax_id,
        last_update=last_update,
        version=version,
    )


def _del_taxa(pid: str, pid_type: PIDType, dbc: sqlite3.Cursor, /) -> None:
    delete_taxa(dbc, pid, pid_type)


def _get_taxa(req: ReportTax, dbc: sqlite3.Cursor, /) -> Iterable[TaxonomyResults]:
    for res in search_taxa(dbc, req):
        yield res


def _com_taxa(pid: str, new_pid: str, pid_type: PIDType, dbc: sqlite3.Cursor, /) -> None:
    merge_taxa_id(dbc, pid, new_pid, pid_type)


def _get_db_status(dbc: sqlite3.Cursor, /) -> TaxStatus:
    cnt, last_update = get_taxa_db_status(dbc)
    return TaxStatus(cnt=cnt, last_update=last_update)


def _skip_analysis(tax: TaxUpdRes, version: str, des_src: DesSource, /) -> bool:
    lud = datetime.datetime.fromtimestamp(tax.last_update)
    if is_version_newer(tax.version, version):
        return False
    if lud <= datetime.datetime.now() - datetime.timedelta(
        days=(EXP_DAYS + random.randint(0, EXP_DAYS))  # noqa: S311
    ):
        return False
    return des_src == DesSource.sy_db


def _update_taxonomy_wrapper(
    tax_con: TaxUpdatePackage, dbc: sqlite3.Cursor, /
) -> Iterable[TW_RES_UP_E]:
    tax = tax_con.data
    if isinstance(tax, TaxonomyCom):
        _com_taxa(tax.pid, tax.merge_pid, tax.pid_type, dbc)
    elif isinstance(tax, TaxonomyDel):
        _del_taxa(tax.pid, tax.pid_type, dbc)
    elif isinstance(tax, (TaxonomyAdd, TaxonomyLink)):
        check_res = _add_taxa(tax, dbc)
        if check_res.tid > 0 and not _skip_analysis(
            check_res, tax_con.version, tax_con.des_src
        ):
            update_taxa_status(dbc, check_res.tid, tax_con.version)
            remove_type_strain(dbc, check_res.tid, tax_con.des_src)
            yield check_res.tid, tax_con.des_src, tax.type_strain


def typ_worker_upd(req: TW_REQ_UP_E, dbc: sqlite3.Cursor, /) -> Iterable[TW_RES_UP_E]:
    if isinstance(req, TaxUpdatePackage) and req.version != "":
        yield from _update_taxonomy_wrapper(req, dbc)
    elif isinstance(req, AddType):
        _add_type_strain(req.did, req.des_source, req.des, dbc)


def typ_worker_rep(req: TW_REQ_REP_E, dbc: sqlite3.Cursor, /) -> Iterable[TW_RES_REP_E]:
    if isinstance(req, ReportTax):
        yield from _get_taxa(req, dbc)
    elif isinstance(req, DefCmd) and DefCmd.sta == req:
        yield _get_db_status(dbc)
