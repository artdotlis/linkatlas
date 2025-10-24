import sqlite3
from seqlink.model.database.sql.taxonomy import REMOVE_TAXA, ADD_TAXA
from utilslink.parse.string import clean_alpha_num_only
from utilslink.schema.taxa import PIDType


def remove_taxa(dbms: sqlite3.Cursor, sid: int, /) -> None:
    dbms.execute(REMOVE_TAXA, (sid,))


def add_taxa(
    dbms: sqlite3.Cursor,
    sid: int,
    name: str,
    linked_pid: str,
    linked_type: PIDType | None,
    /,
) -> None:
    typ = ""
    if linked_type is not None:
        typ = linked_type.value
    dbms.execute(ADD_TAXA, (sid, name, clean_alpha_num_only(name), linked_pid, typ))
