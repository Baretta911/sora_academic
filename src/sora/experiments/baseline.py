"""Baseline comparison experiment."""

from sora.config import BASE_SLEEP_TARGET_SLOTS, DEFAULT_RANDOM_SEED, GENES_PER_DAY
from sora.data.parser import normalize_questionnaire_dataframe, parse_slot_list
from sora.genetic_algorithm.constraints import check_feasibility
from sora.genetic_algorithm.optimizer import GeneticAlgorithmOptimizer
from sora.genetic_algorithm.representation import Allele
from sora.hill_climbing.local_search import run_hill_climbing
from sora.utils.metrics import extract_metrics


def greedy_schedule(work_slots: list[int], class_slots: list[int], mandatory_slots: list[int]) -> list[int]:
    """Create a greedy baseline by filling the longest free blocks with sleep."""
    schedule = [Allele.REST] * GENES_PER_DAY
    for slot in work_slots:
        schedule[slot] = Allele.WORK
    for slot in class_slots:
        schedule[slot] = Allele.CLASS

    free_indices = [slot for slot in range(GENES_PER_DAY) if slot not in mandatory_slots]
    blocks = []
    if free_indices:
        current_block = [free_indices[0]]
        for index in range(1, len(free_indices)):
            if free_indices[index] == free_indices[index - 1] + 1:
                current_block.append(free_indices[index])
            else:
                blocks.append(current_block)
                current_block = [free_indices[index]]
        blocks.append(current_block)

    blocks.sort(key=len, reverse=True)
    sleep_assigned = 0
    for block in blocks:
        for slot in block:
            if sleep_assigned >= BASE_SLEEP_TARGET_SLOTS:
                break
            schedule[slot] = Allele.SLEEP
            sleep_assigned += 1
        if sleep_assigned >= BASE_SLEEP_TARGET_SLOTS:
            break
    return [int(value) for value in schedule]


def fixed_schedule(
    work_slots: list[int],
    class_slots: list[int],
    mandatory_slots: list[int],
    sleep_start_hour: int = 22,
    sleep_duration_hours: int = 7,
) -> list[int]:
    """Create a fixed 22:00 sleep baseline."""
    schedule = [Allele.REST] * GENES_PER_DAY
    for slot in work_slots:
        schedule[slot] = Allele.WORK
    for slot in class_slots:
        schedule[slot] = Allele.CLASS

    start_slot = sleep_start_hour * 2
    duration_slots = sleep_duration_hours * 2
    for offset in range(duration_slots):
        slot = (start_slot + offset) % GENES_PER_DAY
        if slot not in mandatory_slots:
            schedule[slot] = Allele.SLEEP
    return [int(value) for value in schedule]


def run_baseline_comparison(row, parameters: dict, random_seed: int = DEFAULT_RANDOM_SEED) -> dict[str, dict]:
    """Compare SORA, greedy, and fixed schedules on Wednesday."""
    details = run_baseline_comparison_with_details(row, parameters, random_seed=random_seed)
    return details["metrics"]


def run_baseline_comparison_with_details(row, parameters: dict, random_seed: int = DEFAULT_RANDOM_SEED) -> dict:
    """Compare methods and return metrics, schedules, and SORA convergence history."""
    row = normalize_questionnaire_dataframe(row.to_frame().T).iloc[0]
    day_name = "Rabu"
    work_slots = parse_slot_list(row[f"Kerja_{day_name}"])
    class_slots = parse_slot_list(row[f"Kuliah_{day_name}"])
    observed_sleep_slots = parse_slot_list(row.get(f"Tidur_{day_name}", "[]"))
    overlap = sorted(set(work_slots) & set(class_slots))
    if overlap:
        raise ValueError(f"Work and class slots overlap on {day_name}: {overlap}")

    optimizer = GeneticAlgorithmOptimizer(
        work_slots=work_slots,
        class_slots=class_slots,
        observed_sleep_slots=observed_sleep_slots,
        population_size=parameters["population_size"],
        mutation_rate=parameters["mutation_rate"],
        crossover_rate=parameters.get("crossover_rate", 0.80),
        random_seed=random_seed,
        hill_climbing_iterations=parameters.get("hill_climbing_iterations", 20),
    )
    if not check_feasibility(optimizer.mandatory_absolute):
        raise ValueError(f"Mandatory schedule is infeasible on {day_name}")

    best_ga, convergence_history = optimizer.run_genetic_algorithm_with_history(
        generations=150,
        hill_climbing_iterations=parameters.get("hill_climbing_iterations", 20),
    )
    best_sora = best_ga

    greedy = optimizer.repair_chromosome(greedy_schedule(work_slots, class_slots, optimizer.mandatory_absolute))
    fixed = optimizer.repair_chromosome(fixed_schedule(work_slots, class_slots, optimizer.mandatory_absolute))

    return {
        "metrics": {
            "sora": extract_metrics(optimizer, best_sora),
            "greedy": extract_metrics(optimizer, greedy),
            "fixed": extract_metrics(optimizer, fixed),
        },
        "schedules": {
            "sora": best_sora,
            "greedy": greedy,
            "fixed": fixed,
        },
        "convergence": convergence_history,
    }
