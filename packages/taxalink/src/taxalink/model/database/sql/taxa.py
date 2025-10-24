from typing import Final
from utilslink.container.bio_ent import get_all_pid_types

INIT_TAX: Final[
    str
] = f"""
create table taxonomy
(
    id integer primary key autoincrement not null,
    name_canonical text not null,
    name_clean text not null,
    linked_pid text not null,
    linked_type text check(
        linked_type in ({",".join(get_all_pid_types("'"))})
    ) not null,
    correct_id integer null,
    parent_id integer null,
    rank text not null,
    last_update integer not null,
    version text not null,
    constraint taxa_ch check(
        name_clean != ''
        and name_canonical != ''
        and linked_pid != ''
    ),
    foreign key(correct_id)
        references taxonomy(id),
    foreign key(parent_id)
        references taxonomy(id),
    unique(name_clean, linked_pid, linked_type)
);
"""

INDEX_TAXA_PID: Final[
    str
] = """
CREATE INDEX idx_linked_pid
ON taxonomy (linked_pid, linked_type);
"""

INDEX_TAXA_COR_ID: Final[
    str
] = """
CREATE INDEX idx_correct_id
ON taxonomy (correct_id);
"""

INDEX_TAXA_PAR_ID: Final[
    str
] = """
CREATE INDEX idx_parent_id
ON taxonomy (parent_id);
"""

INDEX_TAXA_RANK: Final[
    str
] = """
CREATE INDEX idx_rank
ON taxonomy (rank);
"""

INDEX_TAXA_NAME: Final[
    str
] = """
CREATE INDEX idx_name_clean
ON taxonomy (name_clean);
"""

INDEX_TAXA_UPDATE: Final[
    str
] = """
CREATE INDEX idx_last_update
ON taxonomy (last_update);
"""

INDEX_TAXA_PID_COR: Final[
    str
] = """
CREATE INDEX idx_linked_pid_cor
ON taxonomy (linked_pid, linked_type, correct_id);
"""

UPDATE_TAX: Final[
    str
] = """
UPDATE taxonomy
SET version=?, last_update=?
WHERE id=?;
"""

DELETE_TAX: Final[
    str
] = """
UPDATE taxonomy
SET correct_id=NULL
WHERE linked_pid=? and linked_type=?;
"""


MERGE_TAX: Final[
    str
] = """
UPDATE taxonomy
SET correct_id=(
    SELECT tx.id
    FROM taxonomy tx
    WHERE tx.id=tx.correct_id and tx.linked_pid=? and tx.linked_type=?
    LIMIT 1
)
WHERE linked_pid=? and linked_type=?;
"""

ADD_TAX_PARENT: Final[
    str
] = """
UPDATE taxonomy
SET parent_id=?
WHERE id=?;
"""

ADD_TAX_CORRECT: Final[
    str
] = """
UPDATE taxonomy
SET correct_id=?
WHERE id=?;
"""

GET_TAXA_PID: Final[
    str
] = """
SELECT tx.id, tx.last_update, tx.version, tx.parent_id, tx.correct_id
FROM taxonomy tx
WHERE tx.linked_pid=? and tx.linked_type=? and tx.name_clean=?
LIMIT 1
"""

GET_COR_TAXA_PID: Final[
    str
] = """
SELECT tx.id
FROM taxonomy tx
WHERE tx.linked_pid=? and tx.linked_type=? and tx.correct_id=tx.id
LIMIT 1
"""

ADD_TAXA: Final[
    str
] = """
insert into taxonomy
(
    name_canonical, name_clean, linked_pid,
    linked_type, rank, last_update, version
)
values(?,?,?,?,?,?,?)
RETURNING id;
"""

GET_TAXA_STATUS: Final[
    str
] = """
SELECT COUNT(id), MAX(last_update)
FROM taxonomy;
"""

TAX_WHERE_DAT: Final[str] = "last_update>?"
TAX_WHERE_PID: Final[str] = "linked_pid=? and linked_type=?"
TAX_WHERE_NAM: Final[str] = "name_clean=?"
TAX_WHERE_RANK: Final[str] = "rank=?"
TAX_WHERE_COR: Final[str] = "id=correct_id"

GET_TAXA_REPORT: Final[
    str
] = """
SELECT id, linked_pid, linked_type, name_canonical, last_update,
    rank, correct_id, parent_id
FROM taxonomy
"""

GET_TAXA_NAMES: Final[
    str
] = """
SELECT name_canonical
FROM taxonomy
WHERE id!=? and correct_id=?;
"""

GET_TAXA_NAM_RANK: Final[
    str
] = """
SELECT name_canonical, rank, correct_id, parent_id
FROM taxonomy
WHERE id=?
LIMIT 1;
"""

GET_TAXA_PAR_ID: Final[
    str
] = """
SELECT parent_id
FROM taxonomy
WHERE id=?
LIMIT 1;
"""
