"""Crossover operator for the Genetic Algorithm."""

import numpy as np


def single_point_crossover(parent_a: list[int], parent_b: list[int], rng: np.random.Generator) -> list[int]:
    """Create one child using single-point crossover."""
    cut_point = int(rng.integers(10, 38))
    return parent_a[:cut_point] + parent_b[cut_point:]
