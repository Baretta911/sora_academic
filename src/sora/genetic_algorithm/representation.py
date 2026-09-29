"""Chromosome, gene, and allele representation."""

from enum import IntEnum

from sora.config import GENES_PER_DAY, SLOT_DURATION_HOURS


class Allele(IntEnum):
    """Activity allele used in each 30-minute gene."""

    SLEEP = 0
    WORK = 1
    NAP = 2
    REST = 3
    CLASS = 4


VALID_ALLELES = {int(allele) for allele in Allele}


def slot_to_time_label(slot: int) -> str:
    """Convert a slot index into a HH:MM label."""
    hour = slot // 2
    minute = "30" if slot % 2 else "00"
    return f"{hour:02d}:{minute}"


def sleep_hours(chromosome: list[int]) -> float:
    """Return main sleep duration from a chromosome."""
    return chromosome.count(Allele.SLEEP) * SLOT_DURATION_HOURS


def validate_chromosome(chromosome: list[int]) -> None:
    """Validate chromosome length and allele values."""
    if len(chromosome) != GENES_PER_DAY:
        raise ValueError(f"Chromosome length must be {GENES_PER_DAY}, got {len(chromosome)}")
    invalid = set(chromosome) - VALID_ALLELES
    if invalid:
        raise ValueError(f"Unknown allele values: {sorted(invalid)}")
