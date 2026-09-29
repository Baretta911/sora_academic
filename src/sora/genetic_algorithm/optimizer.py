"""Genetic Algorithm optimizer orchestration."""

import numpy as np

from sora.config import DEFAULT_RANDOM_SEED
from sora.genetic_algorithm.constraints import ScheduleContext
from sora.genetic_algorithm.crossover import single_point_crossover
from sora.genetic_algorithm.fitness import FitnessResult, calculate_fitness
from sora.genetic_algorithm.mutation import mutate_chromosome
from sora.genetic_algorithm.population import initialize_population
from sora.genetic_algorithm.repair import repair_chromosome
from sora.genetic_algorithm.selection import elitism_count, rank_population, select_parent_indices


class GeneticAlgorithmOptimizer:
    """Daily chromosome optimizer using Genetic Algorithm operators."""

    def __init__(
        self,
        work_slots: list[int],
        class_slots: list[int],
        population_size: int,
        mutation_rate: float = 0.10,
        crossover_rate: float = 0.80,
        observed_sleep_slots: list[int] | None = None,
        sleep_weight: float = 0.65,
        initial_fatigue: float = 0.0,
        anchor_start: int | None = None,
        debt_installment: int = 0,
        tail_memory: list[int] | None = None,
        random_seed: int | None = DEFAULT_RANDOM_SEED,
        hill_climbing_iterations: int = 20,
    ) -> None:
        self.context = ScheduleContext(
            work_slots=work_slots,
            class_slots=class_slots,
            observed_sleep_slots=observed_sleep_slots or [],
            population_size=population_size,
            mutation_rate=mutation_rate,
            crossover_rate=crossover_rate,
            sleep_weight=sleep_weight,
            initial_fatigue=initial_fatigue,
            anchor_start=anchor_start,
            debt_installment=debt_installment,
            tail_memory=tail_memory,
        )
        self.rng = np.random.default_rng(random_seed)
        self.hill_climbing_iterations = max(0, int(hill_climbing_iterations))

    @property
    def mandatory_absolute(self) -> list[int]:
        """Expose mandatory slots for experiment runners and baselines."""
        return self.context.mandatory_absolute

    def repair_chromosome(self, chromosome: list[int]) -> list[int]:
        """Repair a chromosome using the configured schedule context."""
        return repair_chromosome(chromosome, self.context)

    def calculate_fitness(self, chromosome: list[int]) -> FitnessResult:
        """Evaluate chromosome fitness using the configured schedule context."""
        return calculate_fitness(chromosome, self.context)

    def _apply_hill_climbing(
        self,
        chromosome: list[int],
        hill_climbing_iterations: int | None = None,
    ) -> list[int]:
        """Apply local refinement only when the configured iteration budget is positive."""
        if hill_climbing_iterations is None:
            effective_iterations = self.hill_climbing_iterations
        else:
            effective_iterations = max(0, int(hill_climbing_iterations))
        if effective_iterations <= 0:
            return chromosome

        from sora.hill_climbing.local_search import run_hill_climbing

        return run_hill_climbing(self, chromosome, max_iterations=effective_iterations)

    def run_genetic_algorithm(
        self,
        generations: int = 200,
        progress_callback=None,
        hill_climbing_iterations: int | None = None,
    ) -> list[int]:
        """Run GA for the configured number of generations and return best chromosome."""
        best_chromosome, _history = self._run_genetic_algorithm(
            generations=generations,
            progress_callback=progress_callback,
            collect_history=False,
            hill_climbing_iterations=hill_climbing_iterations,
        )
        return best_chromosome

    def run_genetic_algorithm_with_history(
        self,
        generations: int = 200,
        progress_callback=None,
        hill_climbing_iterations: int | None = None,
    ) -> tuple[list[int], list[dict]]:
        """Run GA and return best chromosome plus generation-level fitness history."""
        return self._run_genetic_algorithm(
            generations=generations,
            progress_callback=progress_callback,
            collect_history=True,
            hill_climbing_iterations=hill_climbing_iterations,
        )

    def _run_genetic_algorithm(
        self,
        generations: int,
        progress_callback,
        collect_history: bool,
        hill_climbing_iterations: int | None = None,
    ) -> tuple[list[int], list[dict]]:
        """Shared GA loop used by standard and traced execution."""
        effective_hill_climbing_iterations = (
            self.hill_climbing_iterations
            if hill_climbing_iterations is None
            else max(0, int(hill_climbing_iterations))
        )
        population = initialize_population(self.context, self.rng)
        progress_step = max(1, generations // 40)
        history = []

        for generation_idx in range(generations):
            population = rank_population(population, self.calculate_fitness)
            if collect_history:
                top_results = [self.calculate_fitness(chromosome).fitness for chromosome in population[:10]]
                history.append(
                    {
                        "generation": float(generation_idx + 1),
                        "best_fitness": float(top_results[0]),
                        "mean_top10_fitness": float(np.mean(top_results)),
                        "schedule": population[0][:],
                    }
                )
            elite_count = elitism_count(self.context.population_size)
            next_generation = population[:elite_count]

            while len(next_generation) < self.context.population_size:
                parent_a_idx, parent_b_idx = select_parent_indices(population, self.rng)
                if self.rng.random() < self.context.crossover_rate:
                    child = single_point_crossover(population[parent_a_idx], population[parent_b_idx], self.rng)
                else:
                    child = population[parent_a_idx][:]
                child = mutate_chromosome(child, self.context, self.rng)
                child = repair_chromosome(child, self.context)
                next_generation.append(child)

            population = next_generation
            if progress_callback and (
                generation_idx + 1 == generations or (generation_idx + 1) % progress_step == 0
            ):
                progress_callback(generation_idx + 1, generations)

        population = rank_population(population, self.calculate_fitness)
        if population:
            population[0] = self._apply_hill_climbing(population[0], effective_hill_climbing_iterations)
        population = rank_population(population, self.calculate_fitness)
        if collect_history and (not history or history[-1]["generation"] != float(generations)):
            top_results = [self.calculate_fitness(chromosome).fitness for chromosome in population[:10]]
            history.append(
                {
                    "generation": float(generations),
                    "best_fitness": float(top_results[0]),
                    "mean_top10_fitness": float(np.mean(top_results)),
                    "schedule": population[0][:],
                }
            )
        return population[0], history
