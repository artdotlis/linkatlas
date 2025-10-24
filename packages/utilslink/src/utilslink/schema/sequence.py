from typing import final, Final

from enum import Enum


@final
class SeqType(str, Enum):
    gene = "GENE"
    genome = "GENOME"
    r_rna = "RRNAOP"


@final
class AsmLvl(str, Enum):
    com = "COMPLETE"
    chr = "CHROMOSOME"
    con = "CONTIG"
    sca = "SCAFFOLD"


SEQ_TYPES: Final[tuple[str, ...]] = tuple(seq.value for seq in SeqType)


def get_all_seq_types(enc: str | None = None, /) -> tuple[str, ...]:
    return tuple(typ if enc is None else f"{enc}{typ}{enc}" for typ in SEQ_TYPES)


ASM_LVLS: Final[tuple[str, ...]] = tuple(lvl.value for lvl in AsmLvl)


def get_all_assembly_lvls(enc: str | None = None, /) -> tuple[str, ...]:
    return tuple(lvl if enc is None else f"{enc}{lvl}{enc}" for lvl in ASM_LVLS)
