"""Hill Climbing local search after Genetic Algorithm."""

from sora.config import GENES_PER_DAY
from sora.genetic_algorithm.constraints import is_nap_allowed_slot
from sora.genetic_algorithm.representation import Allele


def run_hill_climbing(optimizer, chromosome: list[int], max_iterations: int = 20) -> list[int]:
    """Improve the GA result using deterministic local neighborhood search."""
    best_chromosome = chromosome[:]
    best_score = optimizer.calculate_fitness(best_chromosome).fitness
    context = optimizer.context

    for _ in range(max_iterations):
        improved = False

        for slot in range(1, GENES_PER_DAY - 1):
            can_swap = (
                best_chromosome[slot] in [Allele.SLEEP, Allele.NAP, Allele.REST]
                and best_chromosome[slot + 1] in [Allele.SLEEP, Allele.NAP, Allele.REST]
                and slot not in context.transit_slots
                and (slot + 1) not in context.transit_slots
                and best_chromosome[slot] != best_chromosome[slot + 1]
            )
            if not can_swap:
                continue
            candidate = best_chromosome[:]
            candidate[slot], candidate[slot + 1] = candidate[slot + 1], candidate[slot]
            candidate = optimizer.repair_chromosome(candidate)
            candidate_score = optimizer.calculate_fitness(candidate).fitness
            if candidate_score > best_score:
                best_chromosome = candidate
                best_score = candidate_score
                improved = True

        for slot in range(GENES_PER_DAY):
            if slot in context.mandatory_absolute:
                continue
            original_value = best_chromosome[slot]
            alternatives = [Allele.SLEEP, Allele.NAP, Allele.REST] if is_nap_allowed_slot(slot) else [Allele.SLEEP, Allele.REST]
            for alternative in alternatives:
                if alternative == original_value:
                    continue
                candidate = best_chromosome[:]
                candidate[slot] = int(alternative)
                candidate = optimizer.repair_chromosome(candidate)
                candidate_score = optimizer.calculate_fitness(candidate).fitness
                if candidate_score > best_score:
                    best_chromosome = candidate
                    best_score = candidate_score
                    improved = True
                    break

        if not improved:
            break
    return best_chromosome
