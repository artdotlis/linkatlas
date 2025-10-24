import os
from concurrent.futures.thread import ThreadPoolExecutor
from collections.abc import Iterable

import sqlite3
from multiprocessing.synchronize import RLock
from pathlib import Path
from typing import final, AsyncIterator, Callable
from mpyflow.shared.interfaces.logger import SyncStdoutInterface

from utilslink.iter.pack import package_data


def _optimize_performance(db_file: Path, /) -> None:
    con = sqlite3.connect(
        db_file,
        isolation_level=None,
    )
    for exe in (
        "pragma locking_mode=DEFERRED;",
        "pragma journal_mode=WAL;",
        "pragma synchronous=OFF;",
        "pragma cache_size=-4000000;",
        "pragma busy_timeout=5000;",
        "pragma foreign_keys=ON;",
        "pragma page_size=4096;",
        "pragma mmap_size=4295000000;",
        "pragma temp_store=MEMORY;",
        "pragma auto_vacuum=NONE;",
        "VACUUM;",
    ):
        con.execute(exe)
    con.commit()
    con.close()


@final
class DatabaseWork[REQ, RES]:
    __slots__ = (
        "__db_file",
        "__dbc",
        "__init",
        "__lock",
        "__package_size",
        "__ro",
        "__worker",
    )

    def __init__(
        self,
        db_file: Path,
        init: Callable[[Path], None],
        worker: Callable[[REQ, sqlite3.Cursor], Iterable[RES]],
        lock: RLock,
        readonly: bool = False,
        package_size: int = 1000,
        /,
    ) -> None:
        self.__lock = lock
        self.__ro = readonly
        self.__db_file = db_file
        self.__worker = worker
        self.__dbc: None | sqlite3.Connection = None
        self.__init = init
        self.__package_size = package_size
        super().__init__()

    @property
    def _dbc(self) -> sqlite3.Connection:
        if self.__dbc is None:
            self.__dbc = self.__connect()
        return self.__dbc

    def __connect(self) -> sqlite3.Connection:
        self.__init(self.__db_file)
        _optimize_performance(self.__db_file)
        dbc = sqlite3.connect(
            ":memory:" if self.__ro else self.__db_file,
            isolation_level="DEFERRED",
            cached_statements=100000,
            check_same_thread=False,
            autocommit=False,
        )
        if self.__ro:
            with sqlite3.connect(self.__db_file) as dbb:
                dbb.backup(dbc)
        return dbc

    def on_close(self, sync_out: SyncStdoutInterface | None = None, /) -> None:
        self._dbc.commit()
        self._dbc.execute("PRAGMA wal_checkpoint(FULL)")
        self._dbc.close()
        if sync_out is not None:
            sync_out.print_message("", "closed main database connection")
        with self.__db_file.open() as dbh:
            os.fsync(dbh)

    def __work(self, data_con: tuple[REQ, ...]) -> tuple[RES, ...]:
        cur = self._dbc.cursor()
        res: tuple[RES, ...] = tuple(
            res for data in data_con for res in self.__worker(data, cur)
        )
        self._dbc.commit()
        cur.close()
        return res

    def simple_get(self, data: tuple[REQ, ...], /) -> Iterable[tuple[RES, ...]]:
        with self.__lock:
            res = self.__work(data)
        for package in package_data(
            res, self.__package_size, self.__package_size, lambda _val: 1
        ):
            yield package

    async def work(
        self,
        _sync_out: SyncStdoutInterface,
        data: tuple[REQ, ...],
        _th_exc: ThreadPoolExecutor,
        /,
    ) -> AsyncIterator[tuple[RES, ...]]:
        for res in self.simple_get(data):
            yield res
