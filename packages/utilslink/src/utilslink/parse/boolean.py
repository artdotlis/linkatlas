from typing import Any
from utilslink.verify.types import check_type


def pa_int_bool(to_ch: Any, /) -> bool:
    return check_type(to_ch, int, -1) == 1
