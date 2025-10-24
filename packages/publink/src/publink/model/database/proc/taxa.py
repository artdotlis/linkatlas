import sqlite3
from typing import Iterable

from publink.model.database.sql.taxa import ADD_TAXA, GET_TAXA_REPORT, REMOVE_TAXA
from utilslink.parse.string import pa_str, clean_alpha_num_only
from utilslink.verify.types import check_value_or, ch_f_str


def remove_taxa(dbms: sqlite3.Cursor, lid: int, /) -> None:
    dbms.execute(REMOVE_TAXA, (lid,))


def add_taxa(dbms: sqlite3.Cursor, lid: int, name: str, /) -> None:
    dbms.execute(ADD_TAXA, (lid, name, clean_alpha_num_only(name)))


def get_taxa_with_doi(dbms: sqlite3.Cursor, doi: str, /) -> Iterable[str]:
    dbms.execute(GET_TAXA_REPORT, (doi.upper(),))
    for res in dbms.fetchall():
        if isinstance(res, tuple):
            yield check_value_or(res[0], [ch_f_str], pa_str)
