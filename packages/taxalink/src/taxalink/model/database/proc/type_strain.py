import time

import sqlite3
from taxalink.schema.designation import DesSource
from utilslink.container.database import DesDB
from taxalink.model.database.sql.designation import REMOVE_TYPE_STR, ADD_TYPE_STR


def remove_type_strain(dbms: sqlite3.Cursor, tid: int, des_src: DesSource, /) -> None:
    dbms.execute(REMOVE_TYPE_STR, (tid, des_src.value))


def add_type_strain(
    dbms: sqlite3.Cursor, tid: int, des_src: DesSource, ccno: DesDB, /
) -> None:
    if ccno.acr != "" and ccno.core != "":
        dbms.execute(
            ADD_TYPE_STR,
            (tid, des_src, time.time(), ccno.des, ccno.acr, ccno.core, ccno.suf),
        )
