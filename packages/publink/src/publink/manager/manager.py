from pathlib import Path

from cafi.constants.versions import CURRENT_VER
from mpyflow.library.sync_io.queue import SyncQueue
from mpyflow.library.work.pass_through import PassThrough
from mpyflow.library.workable.element import Workable
from mpyflow.library.worker import Worker
from mpyflow.run_wrapper import start_worker

from publink.model.container.database import (
    TW_REQ_REP_E,
    TW_RES_REP_E,
    ReportLit,
    DefCmd,
    PubStatus,
    TW_REQ_UP_E,
    TW_REQ_UP_T,
    AddDes,
    AddSeq,
    AddTaxa,
)
from publink.model.container.literature import LiteratureResults, LitUpdatePackage
from publink.model.database.proc.main_sqlite import init_pub_sqlite_database
from publink.model.database_worker import TYP_DB_NAME, pub_worker_rep, pub_worker_upd
from publink.model.europe_pmc import EuPmcReader
from publink.model.extract_work import ExtractWork
from publink.model.literature_files import LiteratureReader
from publink.model.open_alex import OpenAlexReader
from utilslink.container.conf import AgentConf
from utilslink.context.process import get_worker_ctx
from utilslink.database.sqlite_manager import DatabaseWork
from typing import Any, Self, final
import pickle
from utilslink.report.wish_list import create_ccno_wish_list
from utilslink.error.exceptions import DatabaseEx

type _CON_ANA_E = tuple[int, str | Path]
type _CON_ANA = tuple[_CON_ANA_E, ...]
type _LIT_UP_T = tuple[LitUpdatePackage, ...]
type _CON_UP_T = tuple[AddDes | AddSeq | AddTaxa, ...]


@final
class PubUpdateManager:
    __slots__ = (
        "__acf",
        "__work_dir",
        "__worker",
    )
    __instance: Self | None = None

    def __init__(
        self,
        agent: AgentConf,
        work_dir: Path,
        worker: int,
        /,
    ) -> None:
        self.__work_dir = work_dir
        self.__worker = worker if worker > 1 else 1
        self.__acf = agent
        super().__init__()

    def __new__(cls, *_args: Any) -> Self:
        if cls.__instance is not None:
            return cls.__instance
        cls.__instance = super().__new__(cls)
        return cls.__instance

    def update_database(self) -> None:
        ctx = get_worker_ctx()
        pub_con_ana = SyncQueue[_CON_ANA](ctx, 4, pickle.dumps, pickle.loads)
        lit_up = SyncQueue[TW_REQ_UP_T](ctx, 10, pickle.dumps, pickle.loads)
        cont_up = SyncQueue[TW_REQ_UP_T](
            ctx, self.__worker * 4, pickle.dumps, pickle.loads
        )
        database = DatabaseWork[TW_REQ_UP_E, _CON_ANA_E](
            self.__work_dir.joinpath(TYP_DB_NAME),
            init_pub_sqlite_database,
            pub_worker_upd,
            ctx.RLock(),
        )
        open_alex = OpenAlexReader(self.__work_dir, CURRENT_VER, self.__acf)
        eu_pmc = EuPmcReader(self.__work_dir, CURRENT_VER, self.__acf)
        lit_files = LiteratureReader(self.__work_dir, CURRENT_VER)
        extractor = ExtractWork(self.__work_dir, CURRENT_VER)

        oa_up_w = Workable[_LIT_UP_T, _LIT_UP_T](ctx, PassThrough(), open_alex)
        eup_up_w = Workable[_LIT_UP_T, _LIT_UP_T](ctx, PassThrough(), eu_pmc)
        lfi_up_w = Workable[_LIT_UP_T, _LIT_UP_T](ctx, PassThrough(), lit_files)
        extract_w = Workable[_CON_ANA, _CON_UP_T](ctx, extractor, pub_con_ana)
        db_lit_w = Workable[TW_REQ_UP_T, _CON_ANA](ctx, database, lit_up)
        db_con_w = Workable[TW_REQ_UP_T, _CON_ANA](ctx, database, cont_up)

        oa_worker = Worker[_LIT_UP_T, TW_REQ_UP_T](
            "open_alex", (oa_up_w,), (db_lit_w,), False, 100
        )
        eup_worker = Worker[_LIT_UP_T, TW_REQ_UP_T](
            "europe_pmc", (eup_up_w,), (db_lit_w,), False, 100
        )
        lit_worker = Worker[_LIT_UP_T, TW_REQ_UP_T](
            "literature_files", (lfi_up_w,), (db_lit_w,), False, 100
        )
        extract_info = Worker[_CON_ANA, TW_REQ_UP_T](
            "extract", (extract_w,), (db_con_w,), False, 100
        )
        db_worker_lit = Worker[TW_REQ_UP_T, _CON_ANA](
            "database_lit", (db_lit_w,), (extract_w,), False, 100
        )
        db_worker_con = Worker[TW_REQ_UP_T, _CON_ANA](
            "database_con", (db_con_w,), tuple(), False, 100
        )

        start_worker(
            self.__work_dir,
            "update literature",
            ctx,
            (
                (1, oa_worker),
                (1, eup_worker),
                (1, lit_worker),
                (self.__worker, extract_info),
                (2, db_worker_lit),
                (2, db_worker_con),
            ),
            (oa_up_w, eup_up_w, lfi_up_w, extract_w, db_lit_w, db_con_w),
        )


@final
class PubReportManager:
    __slots__ = ("__database", "__work_dir")
    __instance: Self | None = None

    def __init__(self, work_dir: Path, /) -> None:
        self.__work_dir = work_dir
        ctx = get_worker_ctx()
        self.__database = DatabaseWork[TW_REQ_REP_E, TW_RES_REP_E](
            self.__work_dir.joinpath(TYP_DB_NAME),
            init_pub_sqlite_database,
            pub_worker_rep,
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

    def report(self, acr: str, date: str, include_list: Path | None, /) -> None:
        output = self.__work_dir.joinpath("publink_report.csv")
        print(f"[REPORTING] acr: {acr} date: {date} -> writing to file {output!s}")
        req = (
            ReportLit(
                acr=acr, pub_date=date, include_des=create_ccno_wish_list(include_list)
            ),
        )
        with output.open("w") as out:
            for rep_con in self.__database.simple_get(req):
                for rep in rep_con:
                    if isinstance(rep, LiteratureResults):
                        out.write(
                            f"{rep.doi},{rep.pub_date},{';'.join(rep.des)}"
                            + f",{';'.join(rep.taxa)}\n"
                        )

    def status(self) -> tuple[int, float]:
        for res_con in self.__database.simple_get((DefCmd.sta,)):
            for res in res_con:
                if isinstance(res, PubStatus):
                    return res.cnt, res.last_update
        return 0, 0.0

    def close(self) -> None:
        self.__database.on_close()
