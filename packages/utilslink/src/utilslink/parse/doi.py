import re

_REG_DOI = re.compile(r"^10\.\d{4,9}/[-+><[\]._;()/:A-Za-z0-9]+$")


def is_correct_doi(doi: str, /) -> bool:
    return _REG_DOI.match(doi) is not None
