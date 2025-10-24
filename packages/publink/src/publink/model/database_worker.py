import datetime
import random
from publink.schema.literature import LIT_TYPES
from typing import Iterable, Final
import sqlite3
from publink.model.container.database import (
    PubStatus,
    LitUpdRes,
    DefCmd,
    ReportLit,
    TW_REQ_UP_E,
    TW_RES_UP_E,
    TW_REQ_REP_E,
    TW_RES_REP_E,
)
from publink.model.container.literature import (
    LitUpdatePackage,
    LitType,
    LiteratureResults,
)
from utilslink.container.bio_ent import AddDes, AddTaxa, AddSeq
from utilslink.container.database import DesDB
from publink.model.database.proc.literature import (
    add_literature,
    get_literature_report,
    get_literature_version,
    get_pub_db_status,
)
from publink.model.database.proc.designation import (
    add_designation,
    get_des_with_doi,
    remove_des,
)
from publink.model.database.proc.taxa import add_taxa, get_taxa_with_doi, remove_taxa
from saim.designation.extract_ccno import get_syn_eq_struct
from saim.shared.parse.date import get_date, is_reasonable_date
from publink.model.database.proc.sequence import remove_seq, add_seq, get_seq_with_doi
from utilslink.parse.doi import is_correct_doi
from utilslink.verify.version import is_version_newer


def _prep_ccno_like(des: str, /) -> tuple[str, str, str] | None:
    if (res := get_syn_eq_struct(des))[0] != "" and res[1] != "":
        return res
    return None


def _get_db_status(dbc: sqlite3.Cursor, /) -> PubStatus:
    cnt, last_update = get_pub_db_status(dbc)
    return PubStatus(cnt=cnt, last_update=last_update)


def _filter_des(
    des_con: Iterable[str], include: set[tuple[str, str, str]], /
) -> Iterable[str]:
    for des in des_con:
        des_eq = _prep_ccno_like(des)
        if des_eq is None or (len(include) > 0 and des_eq not in include):
            continue
        yield des


def _update_literature(
    doi: str, date: str, version: str, txt_typ: LitType, dbc: sqlite3.Cursor, /
) -> int:
    lid = add_literature(dbc, doi, date, version, txt_typ.value)
    return lid


def _check_literature(doi: str, dbc: sqlite3.Cursor, /) -> LitUpdRes:
    version, update, lit_type = get_literature_version(dbc, doi)
    return LitUpdRes(doi=doi, version=version, last_update=update, type=lit_type)


def _report_literature(
    acr: str,
    pub_after: str,
    include: tuple[str, ...],
    dbc: sqlite3.Cursor,
    /,
) -> Iterable[LiteratureResults]:
    include_set = set(res for ccn in include if (res := _prep_ccno_like(ccn)) is not None)
    pub_after_date = get_date(pub_after)
    for doi, date in get_literature_report(dbc, acr):
        if (
            doi == ""
            or (pub_date := get_date(date)) is None
            or (pub_after_date is not None and pub_after_date.date > pub_date.date)
        ):
            continue
        des_res = tuple(_filter_des(get_des_with_doi(dbc, doi, acr), include_set))
        if len(des_res) == 0:
            continue
        taxa_res = tuple(get_taxa_with_doi(dbc, doi))
        seq_res = tuple(get_seq_with_doi(dbc, doi))
        if len(taxa_res) == 0:
            continue
        yield LiteratureResults(
            doi=doi, pub_date=date, des=des_res, taxa=taxa_res, seq=seq_res
        )


def _add_des(lid: int, des: str, dbc: sqlite3.Cursor, /) -> None:
    if lid > 0:
        acr, core, suf = get_syn_eq_struct(des)
        add_designation(dbc, lid, DesDB(des=des, ori_acr=acr, ori_core=core, ori_suf=suf))


def _add_seq(lid: int, seq: str, dbc: sqlite3.Cursor, /) -> None:
    if lid > 0:
        add_seq(dbc, lid, seq)


def _add_taxa(lid: int, taxa: str, dbc: sqlite3.Cursor, /) -> None:
    if lid > 0:
        add_taxa(dbc, lid, taxa)


def _remove_des(lid: int, dbc: sqlite3.Cursor, /) -> None:
    if lid > 0:
        remove_des(dbc, lid)


def _remove_taxa(lid: int, dbc: sqlite3.Cursor, /) -> None:
    if lid > 0:
        remove_taxa(dbc, lid)


def _remove_seq(lid: int, dbc: sqlite3.Cursor, /) -> None:
    if lid > 0:
        remove_seq(dbc, lid)


TYP_DB_NAME: Final[str] = "publink_atlas_database.sqlite"
EXP_DAYS: Final[int] = 31


def _skip_analysis(lit: LitUpdRes, version: str, lit_type: LitType, /) -> bool:
    lud = datetime.datetime.fromtimestamp(lit.last_update)
    if is_version_newer(lit.version, version):
        return False
    if lud <= datetime.datetime.now() - datetime.timedelta(
        days=(EXP_DAYS + random.randint(0, EXP_DAYS))  # noqa: S311
    ):
        return False
    if not (
        lit.type in LIT_TYPES
        and lit_type == LitType.abstract
        and lit_type.value == lit.type
    ):
        return False
    return True


def _update_literature_wrapper(
    req: LitUpdatePackage, dbc: sqlite3.Cursor, /
) -> TW_RES_UP_E | None:
    doi, date, text = req.data
    if req.version == "" or not is_reasonable_date(date) or not is_correct_doi(doi):
        return None
    check_res = _check_literature(doi, dbc)
    if not _skip_analysis(check_res, req.version, req.txt_typ):
        lid = _update_literature(doi, date, req.version, req.txt_typ, dbc)
        _remove_des(lid, dbc)
        _remove_taxa(lid, dbc)
        _remove_seq(lid, dbc)
        return lid, text
    return None


def pub_worker_upd(req: TW_REQ_UP_E, dbc: sqlite3.Cursor, /) -> Iterable[TW_RES_UP_E]:
    if isinstance(req, LitUpdatePackage):
        if (res := _update_literature_wrapper(req, dbc)) is not None:
            yield res
    elif isinstance(req, AddDes):
        _add_des(req.did, req.des, dbc)
    elif isinstance(req, AddTaxa):
        _add_taxa(req.did, req.taxa, dbc)
    elif isinstance(req, AddSeq):
        _add_seq(req.did, req.seq, dbc)


def pub_worker_rep(req: TW_REQ_REP_E, dbc: sqlite3.Cursor, /) -> Iterable[TW_RES_REP_E]:
    if isinstance(req, ReportLit):
        yield from _report_literature(req.acr, req.pub_date, req.include_des, dbc)
    elif isinstance(req, DefCmd) and DefCmd.sta == req:
        yield _get_db_status(dbc)
