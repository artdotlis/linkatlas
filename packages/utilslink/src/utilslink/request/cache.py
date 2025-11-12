from requests_cache import BaseCache, CachedSession, SQLiteCache, SerializerPipeline

from datetime import timedelta
from pathlib import Path

from urllib3 import Retry
from requests.adapters import HTTPAdapter

from utilslink.error.exceptions import SessionCreationEx
from utilslink.request.session import create_default_retry, set_bot_agent_header
from typing import Callable


def _clean_cache(
    size_gb: int, exp_days: int, db_path: Path, cache: SQLiteCache, /
) -> SQLiteCache:
    if not db_path.is_file():
        raise SessionCreationEx(f"{db_path!s} is not a file")
    if exp_days <= 0:
        raise SessionCreationEx(f"{exp_days!s} should be at least 1 day")
    if (db_path.stat().st_size / 1000**3) <= size_gb:
        return cache
    cache.delete(expired=True)
    if (db_path.stat().st_size / 1000**3) <= size_gb:
        return cache
    cache.clear()  # type: ignore
    return cache


def create_sqlite_backend(
    name: str,
    work_dir: Path,
    serializer: SerializerPipeline | None = None,
    /,
) -> Callable[[int, int], SQLiteCache]:
    try:
        db_path = work_dir.joinpath(f"{name}.sqlite").absolute()
        cache = SQLiteCache(
            db_path=db_path,
            use_cache_dir=False,
            use_temp=False,
            use_memory=False,
            busy_timeout=None,
            wal=False,
            serializer=serializer,
        )
    except Exception as cex:
        raise SessionCreationEx(f"{cex!s}") from cex
    return lambda exp_days, db_size_gb: _clean_cache(db_size_gb, exp_days, db_path, cache)


def create_simple_get_cache(
    exp_days: int, backend: BaseCache, contact: str, retry: Retry | None = None, /
) -> CachedSession:
    try:
        session = CachedSession(
            backend=backend,
            expire_after=timedelta(days=exp_days),
            cache_control=False,
            stale_if_error=False,
            always_revalidate=False,
            allowable_codes=[200, 404, 403],
            allowable_methods=("GET",),
        )
        adapter = HTTPAdapter(
            max_retries=create_default_retry() if retry is None else retry
        )
        session.mount("http://", adapter)
        session.mount("https://", adapter)
    except Exception as cex:
        raise SessionCreationEx(f"{cex!s}") from cex
    set_bot_agent_header(session, contact)
    return session
