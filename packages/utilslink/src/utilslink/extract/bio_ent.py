from saim.designation.manager import AcronymManager

import re
from typing import Iterable, Final
from utilslink.container.bio_ent import AddDes, AddSeq, AddIdTaxa
from utilslink.extract.sequence import search_regex, GEN_RE, SI_ID_RE, SEQ_ACC_RE
from utilslink.extract.taxa import get_spe_name
from utilslink.iter.clean import rm_dup

_CAP_WORD_RE: Final[re.Pattern[str]] = re.compile(r"^[A-Z][a-z]+$")


def _get_designation(
    acr_man: AcronymManager, req_id: int, sub_str: str, match: str, /
) -> Iterable[AddDes]:
    res_ccno = acr_man.extract_all_valid_ccno_from_text(sub_str)
    if (siid := SI_ID_RE.match(match)) is not None:
        yield AddDes(did=req_id, des=siid.group(1))
    yield from (
        AddDes(did=req_id, des=ccno.designation) for ccno in res_ccno if ccno.acr != ""
    )


def _get_alpha_num(
    acr_man: AcronymManager, req_id: int, sub_str: str, match: str, /
) -> Iterable[AddDes | AddSeq]:
    yield from _get_designation(acr_man, req_id, sub_str, match)
    if (seq_acc := SEQ_ACC_RE.match(match)) is not None:
        yield AddSeq(did=req_id, seq=seq_acc.group(1))


def extract_bio_entity(
    acr_man: AcronymManager,
    tax_man: dict[str, set[str] | None],
    req_id: int,
    req_txt: str,
    /,
) -> Iterable[AddDes | AddIdTaxa | AddSeq]:
    cache: set[str] = set()
    if req_id >= 1 and req_txt != "":
        for pos_start, match in search_regex(req_txt, GEN_RE):
            if match in cache:
                continue
            cache.add(match)
            if _CAP_WORD_RE.match(match) is None:
                sub_start = pos_start - 50 if pos_start - 50 > 0 else pos_start
                sub_end = pos_start + 50 + len(match)
                yield from _get_alpha_num(
                    acr_man, req_id, req_txt[sub_start:sub_end], match
                )
            elif (gid := match.lower()) in tax_man:
                yield AddIdTaxa(
                    did=req_id,
                    taxa=get_spe_name(tax_man[gid], match, pos_start, req_txt),
                )


def extract_designation(
    acr_man: AcronymManager, req_id: int, req_txt: str, /
) -> Iterable[str]:
    if req_id > 0 and req_txt != "":
        yield from rm_dup(
            ccno.designation
            for ccno in acr_man.extract_all_valid_ccno_from_text(req_txt)
            if ccno.acr != ""
        )
        yield from rm_dup(mat for _, mat in search_regex(req_txt, SI_ID_RE))


def extract_taxa_des(
    acr_man: AcronymManager,
    tax_man: dict[str, set[str] | None],
    req_id: int,
    req_txt: str,
    /,
) -> Iterable[AddDes | AddIdTaxa]:
    cache: set[str] = set()
    if req_id >= 1 and req_txt != "":
        for pos_start, match in search_regex(req_txt, GEN_RE):
            if match in cache:
                continue
            cache.add(match)
            if _CAP_WORD_RE.match(match) is None:
                sub_start = pos_start - 50 if pos_start - 50 > 0 else pos_start
                sub_end = pos_start + 50 + len(match)
                yield from _get_designation(
                    acr_man, req_id, req_txt[sub_start:sub_end], match
                )
            elif (gid := match.lower()) in tax_man:
                yield AddIdTaxa(
                    did=req_id,
                    taxa=get_spe_name(tax_man[gid], match, pos_start, req_txt),
                )
