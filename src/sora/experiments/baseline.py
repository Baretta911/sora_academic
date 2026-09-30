"""Baseline comparison experiment."""

from sora.config import BASE_SLEEP_TARGET_SLOTS, DEFAULT_RANDOM_SEED, GENES_PER_DAY
from sora.data.parser import normalize_questionnaire_dataframe, parse_slot_list
from sora.genetic_algorithm.constraints import check_feasibility
from sora.genetic_algorithm.optimizer import GeneticAlgorithmOptimizer
from sora.genetic_algorithm.representation import Allele
from sora.hill_climbing.local_search import run_hill_climbing
from sora.experiments.weekly import DAYS
from sora.utils.metrics import calculate_debt_installment, extract_metrics

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



def run_baseline_comparison_with_details(
    row,
    parameters: dict,
    random_seed: int = DEFAULT_RANDOM_SEED,
) -> dict:
    """Compare SORA, greedy, and fixed schedules over seven sequential days."""
    row = normalize_questionnaire_dataframe(row.to_frame().T).iloc[0]

    methods = ("sora", "greedy", "fixed")

    has_full_week = all(
        f"Kerja_{day}" in row.index and f"Kuliah_{day}" in row.index
        for day in DAYS
    )
    day_names = DAYS if has_full_week else ["Rabu"]
    states = {
        method: {
            "fatigue": 0.0,
            "anchor": None,
            "tail": None,
            "schedules": [],
            "daily_metrics": [],
        }
        for method in methods
    }

    convergence_history = []
    debt_installment = calculate_debt_installment()

    for day_idx, day_name in enumerate(day_names):
        work_slots = parse_slot_list(row[f"Kerja_{day_name}"])
        class_slots = parse_slot_list(row[f"Kuliah_{day_name}"])
        observed_sleep_slots = parse_slot_list(
            row.get(f"Tidur_{day_name}", "[]")
        )

        overlap = sorted(set(work_slots) & set(class_slots))
        if overlap:
            raise ValueError(
                f"Work and class slots overlap on {day_name}: {overlap}"
            )

        for method in methods:
            state = states[method]

            optimizer = GeneticAlgorithmOptimizer(
                work_slots=work_slots,
                class_slots=class_slots,
                observed_sleep_slots=observed_sleep_slots,
                population_size=parameters["population_size"],
                mutation_rate=parameters["mutation_rate"],
                crossover_rate=parameters.get("crossover_rate", 0.80),
                initial_fatigue=state["fatigue"],
                anchor_start=state["anchor"],
                debt_installment=debt_installment,
                tail_memory=state["tail"],
                random_seed=random_seed + day_idx,
                hill_climbing_iterations=parameters.get(
                    "hill_climbing_iterations", 20
                ),
            )

            if not check_feasibility(optimizer.mandatory_absolute):
                raise ValueError(
                    f"Mandatory schedule is infeasible on {day_name}"
                )

            if method == "sora":
                schedule, day_history = (
                    optimizer.run_genetic_algorithm_with_history(
                        generations=200,
                        hill_climbing_iterations=parameters.get(
                            "hill_climbing_iterations", 20
                        ),
                    )
                )
                for record in day_history:
                    convergence_history.append(
                        {"day": day_name, **record}
                    )

            elif method == "greedy":
                schedule = greedy_schedule(
                    work_slots,
                    class_slots,
                    optimizer.mandatory_absolute,
                )
                schedule = optimizer.repair_chromosome(schedule)

            else:
                schedule = fixed_schedule(
                    work_slots,
                    class_slots,
                    optimizer.mandatory_absolute,
                )
                schedule = optimizer.repair_chromosome(schedule)

            result = optimizer.calculate_fitness(schedule)

            state["schedules"].append(schedule)
            state["daily_metrics"].append(
                {
                    "day": day_name,
                    **extract_metrics(optimizer, schedule),
                    "status": "evaluated",
                }
            )

            # Carry each method's own state into the following day.
            state["fatigue"] = result.fatigue_end
            state["anchor"] = result.core_start
            state["tail"] = schedule[-16:]

    # Average daily metrics to produce one comparable weekly summary.
    metric_keys = (
        "fitness",
        "fatigue",
        "sleep_hours",
        "core_start",
        "recovery",
        "penalty",
        "regularity_penalty",
        "nap_sessions",
    )

    weekly_metrics = {}
    for method in methods:
        daily = states[method]["daily_metrics"]
        weekly_metrics[method] = {
            key: sum(item[key] for item in daily) / len(daily)
            for key in metric_keys
        }

    return {
        "metrics": weekly_metrics,
        "schedules": {
            method: (
                states[method]["schedules"]
                if has_full_week
                else states[method]["schedules"][0]
            )
            for method in methods
        },
        "convergence": convergence_history,
    }