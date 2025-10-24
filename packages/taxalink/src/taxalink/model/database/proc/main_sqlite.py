from pathlib import Path
import sqlite3
from taxalink.model.database.sql.designation import (
    INIT_TYP,
    INDEX_TYPE_TAXA_SRC,
    INDEX_TYPE_TAXA,
    INDEX_TYPE_DES,
)
from taxalink.model.database.sql.taxa import (
    INIT_TAX,
    INDEX_TAXA_PID,
    INDEX_TAXA_PID_COR,
    INDEX_TAXA_UPDATE,
    INDEX_TAXA_COR_ID,
    INDEX_TAXA_PAR_ID,
    INDEX_TAXA_RANK,
    INDEX_TAXA_NAME,
)


def init_typ_sqlite_database(dbf: Path, /) -> None:
    if not (dbf.exists() and dbf.is_file()):
        dbf.touch()
        con = sqlite3.connect(dbf)
        con.execute(INIT_TAX)
        con.execute(INDEX_TAXA_UPDATE)
        con.execute(INDEX_TAXA_PID)
        con.execute(INDEX_TAXA_PID_COR)
        con.execute(INDEX_TAXA_COR_ID)
        con.execute(INDEX_TAXA_PAR_ID)
        con.execute(INDEX_TAXA_RANK)
        con.execute(INDEX_TAXA_NAME)
        con.execute(INIT_TYP)
        con.execute(INDEX_TYPE_TAXA_SRC)
        con.execute(INDEX_TYPE_TAXA)
        con.execute(INDEX_TYPE_DES)
        con.commit()
        con.close()
