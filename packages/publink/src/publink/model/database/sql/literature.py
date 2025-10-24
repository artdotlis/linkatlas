from typing import Final

ADD_LITERATURE: Final[
    str
] = """
insert into literature
(doi, publish_date, version, last_update, type)
values(?,?,?,?,?)
ON CONFLICT(doi) DO UPDATE SET
    doi=?,
    publish_date=?,
    version=?,
    last_update=?,
    type=?
RETURNING id;
"""


GET_LITERATURE_STATUS: Final[
    str
] = """
select DISTINCT literature.version, literature.last_update, literature.type
from literature
where literature.doi=?;
"""


GET_LITERATURE_REPORT: Final[
    str
] = """
select DISTINCT literature.doi, literature.publish_date
from literature
inner join designation des
    on literature.id=des.lit_id
inner join taxon_name taxa
    on literature.id=taxa.lit_id;
"""

GET_LITERATURE_REPORT_ACR: Final[
    str
] = """
select DISTINCT literature.doi, literature.publish_date
from literature
inner join designation des
    on literature.id=des.lit_id
inner join taxon_name taxa
    on literature.id=taxa.lit_id
where des.acr=?;
"""

GET_PUB_STATUS: Final[
    str
] = """
select count(id), max(last_update)
from literature;
"""
