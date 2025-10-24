import sqlite3
import time
from typing import Iterable


from publink.model.database.sql.literature import (
    ADD_LITERATURE,
    GET_LITERATURE_REPORT,
    GET_LITERATURE_REPORT_ACR,
    GET_LITERATURE_STATUS,
    GET_PUB_STATUS,
)
from utilslink.error.exceptions import DatabaseEx
from utilslink.parse.number import pa_pos_int_float, pa_int
from utilslink.parse.string import pa_str
from utilslink.verify.types import check_value_or, ch_int, ch_float, ch_f_str


def get_literature_version(dbms: sqlite3.Cursor, doi: str, /) -> tuple[str, float, str]:
    dbms.execute(GET_LITERATURE_STATUS, (doi.upper(),))
    res = dbms.fetchone()
    if isinstance(res, tuple):
        last_update = check_value_or(res[1], [ch_int, ch_float], pa_pos_int_float)
        if last_update < 0:
            last_update = time.time()
        return (
            check_value_or(res[0], [ch_f_str], pa_str),
            last_update,
            check_value_or(res[2], [ch_f_str], pa_str),
        )
    return "", time.time(), ""


def get_literature_report(dbms: sqlite3.Cursor, acr: str, /) -> Iterable[tuple[str, str]]:
    if acr != "":
        dbms.execute(GET_LITERATURE_REPORT_ACR, (acr,))
    else:
        dbms.execute(GET_LITERATURE_REPORT)
    for res in dbms.fetchall():
        if isinstance(res, tuple):
            doi = check_value_or(res[0], [ch_f_str], pa_str)
            date = check_value_or(res[1], [ch_f_str], pa_str)
            yield doi, date


def get_pub_db_status(dbms: sqlite3.Cursor, /) -> tuple[int, float]:
    dbms.execute(GET_PUB_STATUS, tuple())
    res = dbms.fetchone()
    if isinstance(res, tuple) and len(res) == 2:
        return check_value_or(res[0], [ch_int], pa_int), check_value_or(
            res[1], [ch_int, ch_float], pa_pos_int_float
        )
    return 0, 0.0


def add_literature(
    dbms: sqlite3.Cursor, doi: str, date: str, version: str, lit_type: str, /
) -> int:
    dbms.execute(ADD_LITERATURE, (doi.upper(), date, version, time.time(), lit_type) * 2)
    res = dbms.fetchone()
    if isinstance(res, tuple):
        return check_value_or(res[0], [ch_int], pa_int)
    raise DatabaseEx("Literature id was not returned!")
