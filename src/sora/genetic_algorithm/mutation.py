"""Mutation operator for the Genetic Algorithm."""

import numpy as np

from sora.config import GENES_PER_DAY
from sora.genetic_algorithm.constraints import ScheduleContext, is_nap_allowed_slot
from sora.genetic_algorithm.representation import Allele


def mutate_chromosome(chromosome: list[int], context: ScheduleContext, rng: np.random.Generator) -> list[int]:
    """Mutate non-mandatory genes using activity-specific probabilities."""
    for slot in range(GENES_PER_DAY):
        if slot in context.mandatory_absolute:
            continue
        if rng.random() >= context.mutation_rate:
            continue
        if is_nap_allowed_slot(slot):
            chromosome[slot] = int(rng.choice([Allele.SLEEP, Allele.NAP, Allele.REST], p=[0.05, 0.10, 0.85]))
        else:
            chromosome[slot] = int(rng.choice([Allele.SLEEP, Allele.REST], p=[0.06, 0.94]))
    return chromosome
