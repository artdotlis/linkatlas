from pathlib import Path
import sqlite3
from seqlink.model.database.sql.designation import (
    INIT_DES,
    INDEX_ACR,
    INDEX_DES_F,
    INDEX_DES_SEQ,
)
from seqlink.model.database.sql.sequence import INIT_SEQ, INDEX_SEQ_ACC
from seqlink.model.database.sql.taxonomy import INDEX_TAX_SEQ, INIT_TAX, INDEX_TAX_NAM


def init_seq_sqlite_database(dbf: Path, /) -> None:
    if not (dbf.exists() and dbf.is_file()):
        dbf.touch()
        con = sqlite3.connect(dbf)
        con.execute(INIT_SEQ)
        con.execute(INDEX_SEQ_ACC)

        con.execute(INIT_TAX)
        con.execute(INDEX_TAX_NAM)
        con.execute(INDEX_TAX_SEQ)

        con.execute(INIT_DES)
        con.execute(INDEX_ACR)
        con.execute(INDEX_DES_F)
        con.execute(INDEX_DES_SEQ)
        con.commit()
        con.close()
