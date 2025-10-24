import re
from typing import Final, Iterable
from utilslink.parse.sequence import SEQ_ACC

SEQ_ACC_RE: Final[re.Pattern[str]] = re.compile(r"(" + r"|".join(SEQ_ACC) + r")")
SI_ID_RE: Final[re.Pattern[str]] = re.compile(r"(SI-?ID\s*\d+(?:\.\d+)?)")
GEN_RE: Final[re.Pattern[str]] = re.compile(
    r"((?:SI-ID\s*|[A-Z]+[_\s]*)\d+|\b[A-Z][a-z]+\b|(\d+(?:\D\d+)*))"
)


def search_regex(text: str, regex: re.Pattern[str], /) -> Iterable[tuple[int, str]]:
    for seq_acc in re.finditer(regex, text):
        res = seq_acc.group(1)
        if isinstance(res, str) and res != "":
            yield seq_acc.start(), res
