from typing import Any
from utilslink.verify.types import check_type


def pa_int(to_ch: Any, /) -> int:
    return check_type(to_ch, int, -1)


def pa_float(to_ch: Any, /) -> float:
    return check_type(to_ch, float, -1.0)


def pa_opt_int(to_ch: Any, /) -> int | None:
    return check_type(to_ch, int, None)


def pa_opt_float(to_ch: Any, /) -> float | None:
    return check_type(to_ch, float, None)


def pa_pos_int_float(to_ch: Any, /) -> float:
    if (res := check_type(to_ch, float, -1.0)) > 0:
        return res
    if (res := check_type(to_ch, int, -1)) > 0:
        return res
    return 0.0
