from typing import Final
from utilslink.schema.sequence import get_all_seq_types, get_all_assembly_lvls

INIT_SEQ: Final[
    str
] = f"""
create table sequence_accession
(
    id integer primary key autoincrement not null,
    seq_acc text not null,type text not null,
    description text not null,
    type text check(
        type in ({",".join(get_all_seq_types("'"))})
    ) not null,
    lvl text check(
        lvl in ({",".join(get_all_assembly_lvls("'"))})
    ) null,
    length integer null,
    version text not null,
    publish_date text not null,
    last_update integer not null,
    constraint literature_ch check(
        seq_acc != ''
        and publish_date != ''
    ),
    unique(seq_acc)
);
"""

INDEX_SEQ_ACC: Final[
    str
] = """
CREATE UNIQUE INDEX idx_seq_acc
ON sequence_accession (seq_acc);
"""


GET_SEQ_STATUS: Final[
    str
] = """
select count(id), max(last_update)
from sequence_accession;
"""


ADD_SEQ: Final[
    str
] = """
insert into sequence_accession
(seq_acc, type, description, lvl, length, version, publish_date, last_update)
values(?,?,?,?,?,?,?,?)
ON CONFLICT(seq_acc) DO UPDATE SET
    type=?,
    description=?,
    lvl=?,
    length=?,
    publish_date=?
RETURNING id, version, last_update;
"""

UPDATE_SEQ: Final[
    str
] = """
UPDATE sequence_accession
SET version=?, last_update=?
WHERE id=?;
"""
