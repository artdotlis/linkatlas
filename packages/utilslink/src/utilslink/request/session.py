from urllib3 import Retry

from typing import Collection


def create_default_retry_args() -> dict[str, int | float | Collection[int]]:
    return {
        "status": 3,
        "backoff_factor": 0.2,
        "backoff_max": 10,
        "respect_retry_after_header": False,
        "status_forcelist": [500, 502, 503, 504],
    }


def create_default_retry() -> Retry:
    return Retry(**create_default_retry_args())  # type: ignore
