from typing import Final, Iterable
from utilslink.container.bio_ent import get_all_pid_types


def _get_all_linked_types() -> Iterable[str]:
    yield from get_all_pid_types("'")
    yield ""


INIT_TAX: Final[
    str
] = f"""
create table taxon_name
(
    id integer primary key autoincrement not null,
    seq_id integer not null,
    linked_pid text not null,
    linked_type text check(
        linked_type in ({",".join(_get_all_linked_types())})
    ) not null,
    name_canonical text not null,
    name_clean text not null,
    constraint taxa_ch check(
        name_canonical != ''
        and name_clean != ''
        and (linked_pid == '' or linked_type != '')
    ),
    foreign key(seq_id)
        references sequence_accession(id),
    unique(seq_id, linked_pid, linked_type, name_clean)
);
"""

INDEX_TAX_NAM: Final[
    str
] = """
CREATE INDEX idx_taxa_name
ON taxon_name (name_clean);
"""

INDEX_TAX_SEQ: Final[
    str
] = """
CREATE INDEX idx_taxa_seq
ON taxon_name (seq_id);
"""

REMOVE_TAXA: Final[
    str
] = """
delete from taxon_name
where seq_id=?;
"""

ADD_TAXA: Final[
    str
] = """
insert or ignore into taxon_name
(seq_id, name_canonical, name_clean, linked_pid, linked_type)
values(?,?,?,?,?);
"""
