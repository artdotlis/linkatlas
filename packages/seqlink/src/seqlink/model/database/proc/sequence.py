import time

import sqlite3
from seqlink.model.container.sequence import SeqUpdatePackage
from seqlink.model.database.sql.sequence import GET_SEQ_STATUS, ADD_SEQ, UPDATE_SEQ
from utilslink.error.exceptions import DatabaseEx
from utilslink.parse.number import pa_int, pa_pos_int_float
from utilslink.parse.string import pa_str
from utilslink.verify.types import check_value_or, ch_int, ch_float, ch_f_str


def get_seq_db_status(dbms: sqlite3.Cursor, /) -> tuple[int, float]:
    dbms.execute(GET_SEQ_STATUS, tuple())
    res = dbms.fetchone()
    if isinstance(res, tuple) and len(res) == 2:
        return check_value_or(res[0], [ch_int], pa_int), check_value_or(
            res[1], [ch_int, ch_float], pa_pos_int_float
        )
    return 0, 0.0


def update_sequence_status(dbms: sqlite3.Cursor, sid: int, version: str, /) -> None:
    dbms.execute(UPDATE_SEQ, (version, time.time(), sid))


def add_sequence(
    dbms: sqlite3.Cursor, seq: SeqUpdatePackage, /
) -> tuple[int, str, float, bool]:
    update_run = time.time()
    lvl = None if seq.lvl is None else seq.lvl.value
    dbms.execute(
        ADD_SEQ,
        (
            seq.seq_acc,
            seq.seq_typ.value,
            seq.desc,
            lvl,
            seq.len,
            seq.version,
            seq.pub_date,
            update_run,
            seq.seq_typ.value,
            seq.desc,
            lvl,
            seq.len,
            seq.pub_date,
        ),
    )
    sid_p = dbms.fetchone()
    if not isinstance(sid_p, tuple) or len(sid_p) != 3:
        raise DatabaseEx(f"{seq.seq_acc} could not be updated properly")
    sid = check_value_or(sid_p[0], [ch_int], pa_int)
    last_update = check_value_or(sid_p[1], [ch_int, ch_float], pa_pos_int_float)
    if last_update < 0:
        last_update = time.time()
    ver = check_value_or(sid_p[2], [ch_f_str], pa_str)
    return sid, ver, last_update, last_update >= update_run
