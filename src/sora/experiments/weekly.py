"""Weekly optimization experiment."""

import pandas as pd

from sora.config import DEFAULT_RANDOM_SEED
from sora.data.parser import normalize_questionnaire_dataframe, parse_slot_list, required_weekly_columns
from sora.genetic_algorithm.constraints import check_feasibility
from sora.genetic_algorithm.optimizer import GeneticAlgorithmOptimizer
from sora.genetic_algorithm.representation import Allele
from sora.hill_climbing.local_search import run_hill_climbing
from sora.utils.metrics import calculate_debt_installment

DAYS = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]


def _select_subject_row(df: pd.DataFrame, target_name: str):
    names = df["Nama"].astype(str)
    target = str(target_name).strip()
    exact = df[names.str.casefold() == target.casefold()]
    if len(exact) >= 1:
        return exact.iloc[0]
    partial = df[names.str.contains(target, case=False, na=False, regex=False)]
    if len(partial) == 1:
        return partial.iloc[0]
    return None


def run_weekly_optimization(
    dataset_path,
    parameters: dict,
    target_name: str,
    random_seed: int = DEFAULT_RANDOM_SEED,
) -> tuple[list[list[int]] | None, list[dict]]:
    """Run seven sequential daily optimizations for one subject."""
    weekly_schedule, daily_metrics, _histories = run_weekly_optimization_with_history(
        dataset_path=dataset_path,
        parameters=parameters,
        target_name=target_name,
        random_seed=random_seed,
    )
    return weekly_schedule, daily_metrics


def run_weekly_optimization_with_history(
    dataset_path,
    parameters: dict,
    target_name: str,
    random_seed: int = DEFAULT_RANDOM_SEED,
) -> tuple[list[list[int]] | None, list[dict], list[dict]]:
    """Run seven sequential daily optimizations and keep GA convergence history."""
    dataset = normalize_questionnaire_dataframe(pd.read_csv(dataset_path))
    missing_columns = [column for column in required_weekly_columns(DAYS) if column not in dataset.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")

    row = _select_subject_row(dataset, target_name)
    if row is None:
        return None, [], []

    weekly_schedule = []
    daily_metrics = []
    convergence_history = []
    daily_fatigue = 0.0
    anchor_sleep_start = None
    tail_memory = None
    debt_installment = calculate_debt_installment()

    for day_idx, day_name in enumerate(DAYS):
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
            initial_fatigue=daily_fatigue,
            anchor_start=anchor_sleep_start,
            debt_installment=debt_installment,
            tail_memory=tail_memory,
            random_seed=random_seed + day_idx,
            hill_climbing_iterations=parameters.get("hill_climbing_iterations", 20),
        )
        observed_schedule = [int(Allele.REST)] * 48
        for slot in work_slots:
            observed_schedule[slot] = int(Allele.WORK)
        for slot in class_slots:
            observed_schedule[slot] = int(Allele.CLASS)
        for slot in observed_sleep_slots:
            if slot not in optimizer.mandatory_absolute:
                observed_schedule[slot] = int(Allele.SLEEP)
        observed_result = optimizer.calculate_fitness(observed_schedule)

        if not check_feasibility(optimizer.mandatory_absolute):
            fallback = optimizer.repair_chromosome([int(Allele.REST)] * 48)
            weekly_schedule.append(fallback)
            daily_metrics.append(
                {
                    "day": day_name,
                    "status": "skipped_infeasible",
                    "fitness": None,
                    "fatigue_end": daily_fatigue,
                    "sleep_hours": 0.0,
                    "observed_fitness": observed_result.fitness,
                    "observed_schedule": observed_schedule,
                }
            )
            anchor_sleep_start = None
            tail_memory = fallback[-16:]
            continue

        best_ga, day_history = optimizer.run_genetic_algorithm_with_history(
            generations=200,
            hill_climbing_iterations=parameters.get("hill_climbing_iterations", 20),
        )
        for record in day_history:
            convergence_history.append({"day": day_name, **record})
        best_schedule = run_hill_climbing(optimizer, best_ga)
        result = optimizer.calculate_fitness(best_schedule)

        weekly_schedule.append(best_schedule)
        daily_metrics.append(
            {
                "day": day_name,
                "status": "optimized",
                "fitness": result.fitness,
                "fatigue_end": result.fatigue_end,
                "sleep_hours": result.sleep_hours,
                "observed_sleep_hours": len(observed_sleep_slots) / 2,
                "sleep_change_slots": len({slot for slot, allele in enumerate(best_schedule) if allele == Allele.SLEEP} ^ set(observed_sleep_slots)),
                "observed_fitness": observed_result.fitness,
                "fitness_delta": result.fitness - observed_result.fitness,
                "observed_schedule": observed_schedule,
                "core_start": result.core_start,
                "recovery": result.recovery_reward,
                "penalty": result.dynamic_penalty,
                "regularity_penalty": result.regularity_penalty,
                "nap_sessions": result.nap_sessions,
            }
        )
        daily_fatigue = result.fatigue_end
        anchor_sleep_start = result.core_start
        tail_memory = best_schedule[-16:]

    return weekly_schedule, daily_metrics, convergence_history
