import re
from typing import Final

_VER_RE: Final[re.Pattern[str]] = re.compile(r"^v?(\d+)\.(\d+)\.\d+")


def is_version_newer(old: str, incoming: str, /) -> bool:
    o_mat = _VER_RE.match(old)
    if o_mat is None:
        return True
    ov1, ov2 = int(o_mat.group(1)), int(o_mat.group(2))
    i_mat = _VER_RE.match(incoming)
    if i_mat is None:
        return False
    iv1, iv2 = int(i_mat.group(1)), int(i_mat.group(2))
    if ov1 < iv1:
        return True
    return ov1 == iv1 and ov2 <= iv2
