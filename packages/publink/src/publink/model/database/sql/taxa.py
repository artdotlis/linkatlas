from typing import Final


REMOVE_TAXA: Final[
    str
] = """
delete from taxon_name
where lit_id=?;
"""

ADD_TAXA: Final[
    str
] = """
insert or ignore into taxon_name
(lit_id, name_canonical, name_clean)
values(?,?,?);
"""

GET_TAXA_REPORT: Final[
    str
] = """
select DISTINCT taxa.name_canonical
from literature
inner join taxon_name taxa
    on literature.id=taxa.lit_id
where literature.doi=?;
"""
