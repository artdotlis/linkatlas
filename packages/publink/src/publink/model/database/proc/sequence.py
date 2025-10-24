import sqlite3
from typing import Iterable

from publink.model.database.sql.sequence import REMOVE_SEQ, ADD_SEQ, GET_SEQ_REPORT
from utilslink.parse.string import pa_str
from utilslink.verify.types import check_value_or, ch_f_str


def remove_seq(dbms: sqlite3.Cursor, lid: int, /) -> None:
    dbms.execute(REMOVE_SEQ, (lid,))


def add_seq(dbms: sqlite3.Cursor, lid: int, seq_acc: str, /) -> None:
    dbms.execute(ADD_SEQ, (lid, seq_acc))


def get_seq_with_doi(dbms: sqlite3.Cursor, doi: str, /) -> Iterable[str]:
    dbms.execute(GET_SEQ_REPORT, (doi.upper(),))
    for res in dbms.fetchall():
        if isinstance(res, tuple):
            yield check_value_or(res[0], [ch_f_str], pa_str)
