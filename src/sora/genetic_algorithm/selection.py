"""Selection and elitism procedures."""

import numpy as np


def rank_population(population: list[list[int]], fitness_function) -> list[list[int]]:
    """Sort population from highest to lowest fitness."""
    return sorted(population, key=lambda chromosome: fitness_function(chromosome).fitness, reverse=True)


def elitism_count(population_size: int) -> int:
    """Return number of elite individuals preserved per generation."""
    return 20 if population_size > 20 else max(1, population_size // 5)


def select_parent_indices(population: list[list[int]], rng: np.random.Generator) -> tuple[int, int]:
    """Select two parent indices from the top ranked candidates."""
    parent_pool_size = min(50, len(population))
    p1, p2 = rng.choice(parent_pool_size, 2, replace=False)
    return int(p1), int(p2)
