from typing import Final


REMOVE_SEQ: Final[
    str
] = """
delete from sequence_accession
where lit_id=?;
"""

ADD_SEQ: Final[
    str
] = """
insert or ignore into sequence_accession
(lit_id, seq_acc)
values(?,?);
"""


GET_SEQ_REPORT: Final[
    str
] = """
select DISTINCT seq.seq_acc
from literature
inner join sequence_accession seq
    on literature.id=seq.lit_id
where literature.doi=?;
"""
