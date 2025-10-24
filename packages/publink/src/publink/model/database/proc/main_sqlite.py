from pathlib import Path
import sqlite3

from publink.model.database.sql.init import (
    INIT_DES,
    INIT_LIT,
    INIT_TAX,
    INDEX_ACR,
    INDEX_TAX_NAM,
    INDEX_DES_F,
    INDEX_DES_LIT,
    INDEX_TAX_LIT,
    INIT_SEQ,
    INDEX_SEQ_LIT,
    INDEX_SEQ_ACC,
)


def init_pub_sqlite_database(dbf: Path, /) -> None:
    if not (dbf.exists() and dbf.is_file()):
        dbf.touch()
        con = sqlite3.connect(dbf)
        con.execute(INIT_LIT)
        con.execute(INIT_DES)
        con.execute(INDEX_ACR)
        con.execute(INDEX_DES_F)
        con.execute(INDEX_DES_LIT)
        con.execute(INIT_TAX)
        con.execute(INDEX_TAX_NAM)
        con.execute(INDEX_TAX_LIT)
        con.execute(INIT_SEQ)
        con.execute(INDEX_SEQ_ACC)
        con.execute(INDEX_SEQ_LIT)
        con.commit()
        con.close()
