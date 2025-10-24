import re
from typing import Any
from utilslink.verify.types import check_type


def pa_str(to_ch: Any, /) -> str:
    return check_type(to_ch, str, "")


def pa_opt_str(to_ch: Any, /) -> str | None:
    return check_type(to_ch, str, None)


def conv_to_str(to_ch: Any, /) -> str:
    if to_ch is None:
        return ""
    return str(to_ch)


_NWR = re.compile(r"[^A-Za-z0-9]")


def clean_alpha_num_only(name: str, /) -> str:
    return _NWR.sub("", name).upper()
