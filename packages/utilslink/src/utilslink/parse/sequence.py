import re
from typing import Final

SEQ_ACC: Final[tuple[str, ...]] = (
    # Nucleotide
    r"[A-Z]\d{5}|[A-Z]{2}\d{6}|[A-Z]{2}\d{8}",
    # WGS
    r"[A-Z]{4}\d{8,}|[A-Z]{6}\d{9,}",
    # MGA
    r"[A-Z]{5}\d{7}",
    # RefSeq - dna/rna only - TODO how many numbers ?
    r"(?:AC_|NC_|NG_|NT_|NW_|NZ_|NM_|NR_|XM_|XR_)\d+",
    # GENBANK + REFSEQ assemblies
    r"(?:GCA_|GCF_)\d+",
)

_REG_SEQ = re.compile(r"^" + r"|".join(SEQ_ACC) + "$")


def is_correct_seq_acc(seq_acc: str, /) -> bool:
    return _REG_SEQ.match(seq_acc) is not None
