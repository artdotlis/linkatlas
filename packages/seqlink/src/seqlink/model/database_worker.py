from saim.shared.parse.date import is_reasonable_date

import datetime
import random

import sqlite3
from seqlink.model.container.database import (
    TW_REQ_REP_E,
    TW_RES_REP_E,
    DefCmd,
    TW_REQ_UP_E,
    ReportSeq,
    TW_RES_UP_E,
    SeqStatus,
)
from seqlink.model.container.sequence import SeqUpdatePackage, SequenceResults
from seqlink.model.database.proc.designation import remove_designation, add_designation
from seqlink.model.database.proc.sequence import (
    get_seq_db_status,
    add_sequence,
    update_sequence_status,
)
from seqlink.model.database.proc.taxonomy import remove_taxa, add_taxa

from typing import Iterable, Final
from utilslink.container.bio_ent import AddDes, AddIdTaxa
from utilslink.parse.sequence import is_correct_seq_acc
from utilslink.verify.version import is_version_newer

SEQ_DB_NAME: Final[str] = "seqlink_atlas_database.sqlite"
EXP_DAYS: Final[int] = 7


def _get_db_status(dbc: sqlite3.Cursor, /) -> SeqStatus:
    cnt, last_update = get_seq_db_status(dbc)
    return SeqStatus(cnt=cnt, last_update=last_update)


def _report_sequence(
    _req: ReportSeq,
    _dbc: sqlite3.Cursor,
    /,
) -> Iterable[SequenceResults]:
    # TODO finish
    yield from tuple()


def _skip_analysis(last_update: float, new_version: str, old_version: str, /) -> bool:
    lud = datetime.datetime.fromtimestamp(last_update)
    if is_version_newer(new_version, old_version):
        return False
    if lud <= datetime.datetime.now() - datetime.timedelta(
        days=(EXP_DAYS + random.randint(0, EXP_DAYS))  # noqa: S311
    ):
        return False
    return True


def _update_sequence_wrapper(
    seq_con: SeqUpdatePackage, dbc: sqlite3.Cursor, /
) -> TW_RES_UP_E | None:
    if (
        seq_con.version == ""
        or not is_reasonable_date(seq_con.pub_date)
        or not is_correct_seq_acc(seq_con.seq_acc)
    ):
        return None
    seq_id, version, last_update, new_seq = add_sequence(dbc, seq_con)
    if not new_seq and not _skip_analysis(last_update, version, seq_con.version):
        update_sequence_status(dbc, seq_id, version)
        remove_taxa(dbc, seq_id)
        remove_designation(dbc, seq_id)
        return (
            seq_id,
            f"{seq_con.desc} {seq_con.misc}".strip(),
            seq_con.tax_id_type,
            seq_con.tax_id,
        )
    return None


def seq_worker_upd(req: TW_REQ_UP_E, dbc: sqlite3.Cursor, /) -> Iterable[TW_RES_UP_E]:
    if isinstance(req, SeqUpdatePackage):
        if (res := _update_sequence_wrapper(req, dbc)) is not None:
            yield res
    elif isinstance(req, AddDes):
        add_designation(dbc, req.did, req.des)
    elif isinstance(req, AddIdTaxa):
        add_taxa(dbc, req.did, req.taxa, req.pid, req.pid_type)


def seq_worker_rep(req: TW_REQ_REP_E, dbc: sqlite3.Cursor, /) -> Iterable[TW_RES_REP_E]:
    if isinstance(req, ReportSeq):
        yield from _report_sequence(req, dbc)
    elif isinstance(req, DefCmd) and DefCmd.sta == req:
        yield _get_db_status(dbc)
