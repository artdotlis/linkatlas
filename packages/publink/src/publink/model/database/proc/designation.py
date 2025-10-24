import sqlite3
from utilslink.container.database import DesDB
from typing import Iterable

from publink.model.database.sql.designation import (
    ADD_DES,
    GET_DES_REPORT,
    GET_DES_REPORT_ACR,
    REMOVE_DES,
)
from utilslink.parse.string import pa_str
from utilslink.verify.types import check_value_or, ch_f_str


def remove_des(dbms: sqlite3.Cursor, lid: int, /) -> None:
    dbms.execute(REMOVE_DES, (lid,))


def add_designation(dbms: sqlite3.Cursor, lid: int, ccno: DesDB, /) -> None:
    if ccno.acr != "" and ccno.core != "":
        dbms.execute(ADD_DES, (lid, ccno.des, ccno.acr, ccno.core, ccno.suf))


def get_des_with_doi(dbms: sqlite3.Cursor, doi: str, acr: str, /) -> Iterable[str]:
    if acr != "":
        dbms.execute(GET_DES_REPORT_ACR, (doi.upper(), acr))
    else:
        dbms.execute(GET_DES_REPORT, (doi.upper(),))
    for res in dbms.fetchall():
        if isinstance(res, tuple):
            yield check_value_or(res[0], [ch_f_str], pa_str)
