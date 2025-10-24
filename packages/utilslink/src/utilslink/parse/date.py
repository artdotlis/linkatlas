import datetime
from typing import Any
from saim.shared.parse.date import get_date, date_to_str

from utilslink.verify.types import check_type


def conv_to_date_str(date: Any, /) -> str:
    if not isinstance(date, str):
        raise TypeError(f"date is not a string {date}")
    parsed = get_date(date)
    if parsed is None:
        return ""
    return date_to_str(parsed, True)


def conv_to_date_float(date: Any, /) -> float:
    if not isinstance(date, str):
        raise TypeError(f"date is not a string {date}")
    parsed = get_date(date)
    if parsed is None:
        return 0.0
    return parsed.date.timestamp()


def pa_date(to_ch: Any, /) -> datetime.date:
    return check_type(to_ch, datetime.date, datetime.date.today())


def pa_opt_date(to_ch: Any, /) -> datetime.date | None:
    return check_type(to_ch, datetime.date, None)
