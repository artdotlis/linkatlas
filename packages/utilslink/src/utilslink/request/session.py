from requests import Session
from urllib3 import Retry

from typing import Collection, Final

from utilslink.version import VERSION


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


BOT_NAME: Final[str] = "linkatlas"
USER_AGENT: Final[str] = f"{BOT_NAME}-bot/{VERSION}"


def set_bot_agent_header(session: Session, contact: str, /) -> None:
    agent = (
        f"{USER_AGENT} (Python library)"
        if contact == ""
        else f"{USER_AGENT} (Python library; {contact})"
    )
    session.headers.update({"User-Agent": agent})
