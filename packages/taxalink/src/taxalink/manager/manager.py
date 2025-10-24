from cafi.constants.versions import CURRENT_VER

import pickle
from pathlib import Path
from taxalink.model.container.database import (
    AddType,
    TW_REQ_UP_T,
    DefCmd,
    TaxStatus,
    ReportTax,
    TW_REQ_UP_E,
    TW_RES_REP_E,
    TW_REQ_REP_E,
)
from taxalink.model.container.taxa import TaxonomyResults, TaxUpdatePackage
from taxalink.model.database_worker import typ_worker_upd, TYP_DB_NAME, typ_worker_rep
from taxalink.model.extract_work import ExtractWork
from taxalink.model.lpsn import LpsnTaxReader
from taxalink.model.ncbi import NcbiTaxReader
from taxalink.schema.designation import DesSource
from utilslink.container.bio_ent import get_pid_type
from utilslink.container.conf import LPSNConf
from utilslink.context.process import get_worker_ctx
from utilslink.database.sqlite_manager import DatabaseWork
from taxalink.model.database.proc.main_sqlite import init_typ_sqlite_database
from typing import final, Self, Any, Iterable
from utilslink.error.exceptions import DatabaseEx
from mpyflow.library.sync_io.queue import SyncQueue
from mpyflow.library.worker import Worker
from mpyflow.library.work.pass_through import PassThrough
from mpyflow.library.workable.element import Workable
from utilslink.parse.date import conv_to_date_float
from mpyflow.run_wrapper import start_worker

from utilslink.schema.taxa import parse_rank, GBIFRanksE, PIDType

type _CON_ANA_E = tuple[int, DesSource, tuple[str, ...]]
type _CON_ANA = tuple[_CON_ANA_E, ...]
type _TAX_UP_T = tuple[TaxUpdatePackage, ...]
type _TYP_UP_T = tuple[AddType, ...]


@final
class TaxaUpdateManager:
    __slots__ = (
        "__lcf",
        "__work_dir",
        "__worker",
    )
    __instance: Self | None = None

    def __init__(
        self,
        work_dir: Path,
        worker: int,
        lpsn: LPSNConf,
        /,
    ) -> None:
        self.__work_dir = work_dir
        self.__worker = worker if worker > 1 else 1
        self.__lcf = lpsn
        super().__init__()

    def __new__(cls, *_args: Any) -> Self:
        if cls.__instance is not None:
            return cls.__instance
        cls.__instance = super().__new__(cls)
        return cls.__instance

    def update_database(self) -> None:
        ctx = get_worker_ctx()
        tax_con_ana = SyncQueue[_CON_ANA](ctx, 4, pickle.dumps, pickle.loads)
        tax_up = SyncQueue[TW_REQ_UP_T](ctx, 8, pickle.dumps, pickle.loads)
        typ_up = SyncQueue[TW_REQ_UP_T](
            ctx, self.__worker * 4, pickle.dumps, pickle.loads
        )
        database = DatabaseWork[TW_REQ_UP_E, _CON_ANA_E](
            self.__work_dir.joinpath(TYP_DB_NAME),
            init_typ_sqlite_database,
            typ_worker_upd,
            ctx.RLock(),
        )
        ncbi_in = NcbiTaxReader(self.__work_dir, CURRENT_VER)
        lpns_in = LpsnTaxReader(self.__work_dir, self.__lcf, CURRENT_VER)
        extractor = ExtractWork(CURRENT_VER)

        ncbi_up_w = Workable[_TAX_UP_T, _TAX_UP_T](ctx, PassThrough(), ncbi_in)
        lpsn_up_w = Workable[_TAX_UP_T, _TAX_UP_T](ctx, PassThrough(), lpns_in)
        db_tax_w = Workable[TW_REQ_UP_T, _CON_ANA](ctx, database, tax_up)
        db_typ_w = Workable[TW_REQ_UP_T, _CON_ANA](ctx, database, typ_up)
        extract_w = Workable[_CON_ANA, _TYP_UP_T](ctx, extractor, tax_con_ana)

        ncbi_worker = Worker[_TAX_UP_T, TW_REQ_UP_T](
            "ncbi", (ncbi_up_w,), (db_tax_w,), False, 100
        )
        lpsn_worker = Worker[_TAX_UP_T, TW_REQ_UP_T](
            "lpsn", (lpsn_up_w,), (db_tax_w,), False, 100
        )
        extract_info = Worker[_CON_ANA, TW_REQ_UP_T](
            "extract", (extract_w,), (db_typ_w,), False, 100
        )
        db_worker_tax = Worker[TW_REQ_UP_T, _CON_ANA](
            "database_tax", (db_tax_w,), (extract_w,), False, 100
        )
        db_worker_typ = Worker[TW_REQ_UP_T, _CON_ANA](
            "database_type", (db_typ_w,), tuple(), False, 100
        )

        start_worker(
            self.__work_dir,
            "update taxonomy",
            ctx,
            (
                (1, lpsn_worker),
                (1, ncbi_worker),
                (self.__worker, extract_info),
                (2, db_worker_tax),
                (2, db_worker_typ),
            ),
            (lpsn_up_w, ncbi_up_w, db_tax_w, db_typ_w, extract_w),
        )


@final
class TaxaReportManager:
    __slots__ = ("__database", "__work_dir")
    __instance: Self | None = None

    def __init__(self, work_dir: Path, /) -> None:
        self.__work_dir = work_dir
        ctx = get_worker_ctx()
        self.__database = DatabaseWork[TW_REQ_REP_E, TW_RES_REP_E](
            self.__work_dir.joinpath(TYP_DB_NAME),
            init_typ_sqlite_database,
            typ_worker_rep,
            ctx.RLock(),
            True,
        )
        if self.status()[0] == 0:
            raise DatabaseEx("type database is empty")
        super().__init__()

    def __new__(cls, *_args: Any) -> Self:
        if cls.__instance is not None:
            return cls.__instance
        cls.__instance = super().__new__(cls)
        return cls.__instance

    def report(self, source: str, date: str, rank: str, correct_only: bool, /) -> None:
        output = self.__work_dir.joinpath("taxalink_report.csv")
        print(f"[REPORTING] taxa data source: {source} date: {date}")
        print(f"[REPORTING] rank: {rank} only correct names: {correct_only}")
        print(f"|_> writing to file {output!s}")
        req = ReportTax(
            source=get_pid_type(source),
            last_update=conv_to_date_float(date),
            rank=parse_rank(rank),
            correct_only=correct_only,
        )
        with output.open("w") as out:
            for rep_con in self.__database.simple_get((req,)):
                for rep in rep_con:
                    if isinstance(rep, TaxonomyResults):
                        out.write(f"{rep.to_string()}\n")

    def get_all_rank(self, rank: GBIFRanksE, /) -> Iterable[TaxonomyResults]:
        req = (
            ReportTax(
                rank=rank,
            ),
        )
        for rep_con in self.__database.simple_get(req):
            for rep in rep_con:
                if not isinstance(rep, TaxonomyResults):
                    continue
                yield rep

    def get_name_by_id(self, to_sea_id: str, id_type: PIDType, /) -> None | str:
        req = (
            ReportTax(
                pid=to_sea_id,
                name=id_type,
            ),
        )
        for rep_con in self.__database.simple_get(req):
            for rep in rep_con:
                if not isinstance(rep, TaxonomyResults):
                    continue
                return rep.name
        return None

    def status(self) -> tuple[int, float]:
        for res_con in self.__database.simple_get((DefCmd.sta,)):
            for res in res_con:
                if isinstance(res, TaxStatus):
                    return res.cnt, res.last_update
        return 0, 0.0

    def close(self) -> None:
        self.__database.on_close()
