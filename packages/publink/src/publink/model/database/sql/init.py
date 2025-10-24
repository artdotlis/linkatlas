from publink.schema.literature import get_all_lit_types
from typing import Final


INIT_LIT: Final[
    str
] = f"""
create table literature
(
    id integer primary key autoincrement not null,
    doi text not null,
    type text check(
        type in ({",".join(get_all_lit_types("'"))})
    ) not null,
    version text not null,
    publish_date text not null,
    last_update integer not null,
    constraint literature_ch check(
        doi != ''
        and publish_date != ''
    )
    unique(doi)
);
"""


INIT_DES: Final[
    str
] = """
create table designation
(
    id integer primary key autoincrement not null,
    lit_id integer not null,
    acr text not null,
    core text not null,
    suf text not null,
    designation text not null,
    constraint des_ch check(
        designation != ''
        and acr != ''
        and core != ''
    ),
    foreign key(lit_id)
        references literature(id),
    unique(lit_id, acr, core, suf)
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

INDEX_DES_LIT: Final[
    str
] = """
CREATE INDEX idx_des_lit
ON designation (lit_id);
"""


INIT_TAX: Final[
    str
] = """
create table taxon_name
(
    id integer primary key autoincrement not null,
    lit_id integer not null,
    name_canonical text not null,
    name_clean text not null,
    constraint taxa_ch check(
        name_canonical != ''
        and name_clean !=''
    ),
    foreign key(lit_id)
        references literature(id),
    unique(lit_id, name_clean)
);
"""

INDEX_TAX_NAM: Final[
    str
] = """
CREATE INDEX idx_taxa_name
ON taxon_name (name_clean);
"""

INDEX_TAX_LIT: Final[
    str
] = """
CREATE INDEX idx_taxa_lit
ON taxon_name (lit_id);
"""

INIT_SEQ: Final[
    str
] = """
create table sequence_accession
(
    id integer primary key autoincrement not null,
    lit_id integer not null,
    seq_acc text not null,
    constraint taxa_ch check(seq_acc != ''),
    foreign key(lit_id)
        references literature(id),
    unique(lit_id, seq_acc)
);
"""

INDEX_SEQ_ACC: Final[
    str
] = """
CREATE INDEX idx_seq_acc
ON sequence_accession (seq_acc);
"""

INDEX_SEQ_LIT: Final[
    str
] = """
CREATE INDEX idx_seq_lit
ON sequence_accession (lit_id);
"""
