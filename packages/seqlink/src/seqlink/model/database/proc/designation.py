from saim.designation.extract_ccno import get_syn_eq_struct

import sqlite3
from seqlink.model.database.sql.designation import REMOVE_DES, ADD_DES


def remove_designation(dbms: sqlite3.Cursor, sid: int, /) -> None:
    dbms.execute(REMOVE_DES, (sid,))


def add_designation(dbms: sqlite3.Cursor, sid: int, des: str, /) -> None:
    acr, core, suf = get_syn_eq_struct(des)
    if acr != "" and core != "":
        dbms.execute(ADD_DES, (sid, des, acr, core, suf))
