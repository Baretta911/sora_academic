"""Initial population generation."""

import numpy as np

from sora.config import GENES_PER_DAY
from sora.genetic_algorithm.constraints import ScheduleContext
from sora.genetic_algorithm.repair import repair_chromosome
from sora.genetic_algorithm.representation import Allele


def create_initial_individual(context: ScheduleContext, rng: np.random.Generator) -> list[int]:
    """Create one initial chromosome and repair it."""
    chromosome = []
    for slot in range(GENES_PER_DAY):
        if slot in context.work_slots:
            chromosome.append(Allele.WORK)
        elif slot in context.class_slots:
            chromosome.append(Allele.CLASS)
        elif slot in context.transit_slots:
            chromosome.append(Allele.REST)
        elif slot in (context.observed_sleep_slots or []):
            chromosome.append(rng.choice([Allele.SLEEP, Allele.REST], p=[0.75, 0.25]))
        else:
            chromosome.append(rng.choice([Allele.SLEEP, Allele.REST], p=[0.10, 0.90]))
    return repair_chromosome([int(value) for value in chromosome], context)


def initialize_population(context: ScheduleContext, rng: np.random.Generator) -> list[list[int]]:
    """Create the first GA population."""
    return [create_initial_individual(context, rng) for _ in range(context.population_size)]
