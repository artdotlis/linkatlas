from typing import Final


REMOVE_DES: Final[
    str
] = """
delete from designation
where lit_id=?;
"""

ADD_DES: Final[
    str
] = """
insert or ignore into designation
(lit_id, designation, acr, core, suf)
values(?,?,?,?,?);
"""

GET_DES_REPORT: Final[
    str
] = """
select DISTINCT des.designation
from literature
inner join designation des
    on literature.id=des.lit_id
where literature.doi=?;
"""

GET_DES_REPORT_ACR: Final[
    str
] = """
select DISTINCT des.designation
from literature
inner join designation des
    on literature.id=des.lit_id
where literature.doi=? and des.acr=?;
"""
