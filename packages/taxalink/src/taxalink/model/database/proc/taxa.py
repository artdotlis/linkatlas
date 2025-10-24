import time
import re
import sqlite3
from taxalink.model.container.database import ReportTax
from taxalink.model.container.taxa import (
    PIDType,
    TaxonomyAdd,
    TaxonomyLink,
    TaxonomyResults,
)
from taxalink.model.database.sql.designation import GET_TAXA_TYPES
from taxalink.model.database.sql.taxa import (
    UPDATE_TAX,
    DELETE_TAX,
    MERGE_TAX,
    GET_TAXA_PID,
    ADD_TAXA,
    ADD_TAX_PARENT,
    ADD_TAX_CORRECT,
    GET_COR_TAXA_PID,
    TAX_WHERE_PID,
    TAX_WHERE_NAM,
    TAX_WHERE_DAT,
    TAX_WHERE_RANK,
    TAX_WHERE_COR,
    GET_TAXA_REPORT,
    GET_TAXA_NAMES,
    GET_TAXA_NAM_RANK,
    GET_TAXA_PAR_ID,
    GET_TAXA_STATUS,
)
from typing import Iterable, Any
from utilslink.parse.number import pa_pos_int_float, pa_int, pa_opt_int
from utilslink.parse.string import pa_str, clean_alpha_num_only
from utilslink.schema.taxa import is_informative_rank
from utilslink.verify.types import (
    check_value_or,
    ch_int,
    ch_float,
    ch_f_str,
    ch_opt_int,
    ch_opt_float,
)


def update_taxa_status(dbms: sqlite3.Cursor, tid: int, version: str, /) -> None:
    dbms.execute(UPDATE_TAX, (version, time.time(), tid))


def delete_taxa(dbms: sqlite3.Cursor, pid: str, pid_typ: PIDType, /) -> None:
    dbms.execute(DELETE_TAX, (pid, pid_typ.value))


def merge_taxa_id(
    dbms: sqlite3.Cursor, pid: str, new_pid: str, pid_typ: PIDType, /
) -> None:
    dbms.execute(MERGE_TAX, (new_pid, pid_typ.value, pid, pid_typ.value))


def _get_taxa_id(
    dbms: sqlite3.Cursor, pid: str, pid_typ: PIDType, clean_name: str, /
) -> tuple[int | None, float, str, int | None, int | None]:
    if pid == "":
        return None, 0, "", None, None
    dbms.execute(GET_TAXA_PID, (pid, pid_typ.value, clean_name))
    res = dbms.fetchone()
    if isinstance(res, tuple):
        last_update = check_value_or(res[1], [ch_int, ch_float], pa_pos_int_float)
        if last_update < 0:
            last_update = 0
            print(f"last update is negative - {pid} - {pid_typ.value}")
        return (
            check_value_or(res[0], [ch_int], pa_int),
            last_update,
            check_value_or(res[2], [ch_f_str], pa_str),
            check_value_or(res[3], [ch_opt_int], pa_opt_int),
            check_value_or(res[4], [ch_opt_int], pa_opt_int),
        )
    return None, 0, "", None, None


def _get_correct_id(dbms: sqlite3.Cursor, pid: str, pid_typ: PIDType, /) -> int | None:
    if pid == "":
        return None
    dbms.execute(GET_COR_TAXA_PID, (pid, pid_typ.value))
    res = dbms.fetchone()
    if isinstance(res, tuple):
        return check_value_or(res[0], [ch_int], pa_int)
    return None


def _link_taxa(dbms: sqlite3.Cursor, taxa: TaxonomyAdd, tid: int, /) -> None:
    clean_parent_name = clean_alpha_num_only(taxa.parent_name)
    parent_tid, *_ = _get_taxa_id(dbms, taxa.parent_pid, taxa.pid_type, clean_parent_name)
    if parent_tid is not None:
        dbms.execute(ADD_TAX_PARENT, (parent_tid, tid))
    if taxa.correct:
        dbms.execute(ADD_TAX_CORRECT, (tid, tid))
    else:
        dbms.execute(
            ADD_TAX_CORRECT, (_get_correct_id(dbms, taxa.correct_pid, taxa.pid_type), tid)
        )


def get_taxa_id(
    dbms: sqlite3.Cursor, taxa: TaxonomyAdd | TaxonomyLink, /
) -> tuple[int | None, float, str, str]:
    clean_name = clean_alpha_num_only(taxa.name)
    tid, lup, ver, *_ = _get_taxa_id(dbms, taxa.pid, taxa.pid_type, clean_name)
    if tid is not None and isinstance(taxa, TaxonomyAdd):
        _link_taxa(dbms, taxa, tid)
    return tid, lup, ver, clean_name


def add_taxa(dbms: sqlite3.Cursor, taxa: TaxonomyAdd, /) -> tuple[int | None, float, str]:
    tid, lup, ver, clean_name = get_taxa_id(dbms, taxa)
    if tid is None:
        dbms.execute(
            ADD_TAXA, (taxa.name, clean_name, taxa.pid, taxa.pid_type, taxa.rank, lup, "")
        )
        tid_p = dbms.fetchone()
        if isinstance(tid_p, tuple):
            tid = check_value_or(tid_p[0], [ch_int], pa_int)
            _link_taxa(dbms, taxa, tid)
            return tid, lup, ver
        else:
            print(f"Could not detect tid {taxa.name} - {taxa.pid} - {taxa.pid_type}")
            return None, 0, ""
    return tid, lup, ver


def _get_all_other_names(
    dbms: sqlite3.Cursor, tid: int, correct_id: Any, /
) -> Iterable[Any]:
    if isinstance(correct_id, int):
        dbms.execute(GET_TAXA_NAMES, (tid, correct_id))
        for res in dbms.fetchall():
            if isinstance(res, tuple) and len(res) == 1:
                yield res[0]


def _get_all_types(dbms: sqlite3.Cursor, tid: int, /) -> Iterable[Any]:
    dbms.execute(GET_TAXA_TYPES, (tid,))
    for res in dbms.fetchall():
        if isinstance(res, tuple) and len(res) == 3:
            yield {"des": res[0], "source": res[1], "last_update": res[2]}


def _get_all_upper(dbms: sqlite3.Cursor, cor_id: Any, par_id: Any, /) -> Iterable[Any]:
    if isinstance(par_id, int):
        dbms.execute(GET_TAXA_NAM_RANK, (par_id,))
        res = dbms.fetchone()
        if isinstance(res, tuple) and len(res) == 4:
            yield {"name": res[0], "rank": res[1]}
            yield from _get_all_upper(dbms, res[2], res[3])
    elif isinstance(cor_id, int):
        dbms.execute(GET_TAXA_PAR_ID, (cor_id,))
        res = dbms.fetchone()
        if isinstance(res, tuple) and len(res) == 1:
            yield from _get_all_upper(dbms, None, res[0])


_LAST_AND = re.compile(r"\s+and\s*$")


def _build_search_where(req: ReportTax, /) -> tuple[str, tuple[str, ...]]:
    where = f" WHERE {TAX_WHERE_DAT} and "
    req_arg: tuple[str, ...] = (str(req.last_update),)
    if req.pid != "" and req.source is not None:
        where += TAX_WHERE_PID + " and "
        req_arg = (*req_arg, req.pid, req.source.value)
    if req.name != "":
        where += TAX_WHERE_NAM + " and "
        req_arg = (*req_arg, clean_alpha_num_only(req.name))
    if is_informative_rank(req.rank):
        where += TAX_WHERE_RANK + " and "
        req_arg = (*req_arg, req.rank.value)
    if req.correct_only:
        where += TAX_WHERE_COR
    return _LAST_AND.sub("", where) + ";", req_arg


def search_taxa(dbms: sqlite3.Cursor, req: ReportTax, /) -> Iterable[TaxonomyResults]:
    where, args = _build_search_where(req)
    dbms.execute(GET_TAXA_REPORT + where, args)
    for res in dbms.fetchall():
        if isinstance(res, tuple) and len(res) == 8:
            (
                tid,
                linked_pid,
                linked_type,
                name,
                last_update,
                rank,
                correct_id,
                parent_id,
            ) = res
            if not isinstance(tid, int):
                continue
            yield TaxonomyResults(
                **{
                    "tid": tid,
                    "pid": linked_pid,
                    "pid_type": linked_type,
                    "last_update": last_update,
                    "name": name,
                    "correct": type(tid) is type(correct_id) and tid == correct_id,
                    "rank": rank,
                    "names": tuple(_get_all_other_names(dbms, tid, correct_id)),
                    "ranks": tuple(_get_all_upper(dbms, correct_id, parent_id)),
                    "type_strain": tuple(_get_all_types(dbms, tid)),
                }
            )


def get_taxa_db_status(dbms: sqlite3.Cursor, /) -> tuple[int, float]:
    dbms.execute(GET_TAXA_STATUS, tuple())
    res = dbms.fetchone()
    if isinstance(res, tuple) and len(res) == 2:
        return check_value_or(res[0], [ch_int], pa_int), check_value_or(
            res[1], [ch_int, ch_opt_float], pa_pos_int_float
        )
    return 0, 0.0
