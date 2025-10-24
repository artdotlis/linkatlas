from typing import Final

INIT_DES: Final[
    str
] = """
create table designation
(
    id integer primary key autoincrement not null,
    seq_id integer not null,
    acr text not null,
    core text not null,
    suf text not null,
    designation text not null,
    constraint des_ch check(
        designation != ''
        and acr != ''
        and core != ''
    ),
    foreign key(seq_id)
        references sequence_accession(id),
    unique(seq_id, acr, core, suf)
);
"""

INDEX_ACR: Final[
    str
] = """
CREATE INDEX idx_acr
ON designation (acr);
"""

INDEX_DES_F: Final[
    str
] = """
CREATE INDEX idx_des_full
ON designation (acr, core, suf);
"""

INDEX_DES_SEQ: Final[
    str
] = """
CREATE INDEX idx_des_seq
ON designation (seq_id);
"""

REMOVE_DES: Final[
    str
] = """
delete from designation
where seq_id=?;
"""

ADD_DES: Final[
    str
] = """
insert or ignore into designation
(seq_id, designation, acr, core, suf)
values(?,?,?,?,?);
"""
