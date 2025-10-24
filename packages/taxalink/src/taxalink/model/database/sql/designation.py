from taxalink.schema.designation import get_all_des_sources
from typing import Final

INIT_TYP: Final[
    str
] = f"""
create table type_strain
(
    id integer primary key autoincrement not null,
    tax_id integer not null,
    acr text not null,
    core text not null,
    suf text not null,
    designation text not null,
    source text check(source in ({",".join(get_all_des_sources("'"))})) not null,
    last_update integer not null,
    constraint designation_ch check(
        designation != ''
        and core != ''
    ),
    foreign key(tax_id)
        references taxonomy(id),
    unique(tax_id, acr, core, suf)
);
"""

INDEX_TYPE_TAXA_SRC: Final[
    str
] = """
CREATE INDEX idx_type_taxa_source
ON type_strain (tax_id, source);
"""

INDEX_TYPE_TAXA: Final[
    str
] = """
CREATE INDEX idx_type_taxa
ON type_strain (tax_id);
"""

INDEX_TYPE_DES: Final[
    str
] = """
CREATE INDEX idx_type_des
ON type_strain (acr, core, suf);
"""


REMOVE_TYPE_STR: Final[
    str
] = """
delete from type_strain
where tax_id=? and source=?;
"""

ADD_TYPE_STR: Final[
    str
] = """
insert or ignore into type_strain
(tax_id, source, last_update, designation, acr, core, suf)
values(?,?,?,?,?,?,?);
"""

GET_TAXA_TYPES: Final[
    str
] = """
SELECT designation, source, last_update
FROM type_strain
WHERE tax_id=?;
"""
