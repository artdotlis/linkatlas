import multiprocessing
from multiprocessing.context import SpawnContext
from utilslink.error.exceptions import WrongContextEx
from typing import Final


_CTX: Final[multiprocessing.context.BaseContext] = multiprocessing.get_context("spawn")


def get_worker_ctx() -> SpawnContext:
    if not isinstance(_CTX, multiprocessing.context.SpawnContext):
        raise WrongContextEx(f"Expected SpawnContext got {type(_CTX).__name__}")
    return _CTX
