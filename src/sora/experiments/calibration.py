"""Hyperparameter calibration for the academic SORA implementation."""

from __future__ import annotations

import itertools
import json
from pathlib import Path

import pandas as pd

from sora.config import (
    DATASET_CALIBRATION,
    DEFAULT_RANDOM_SEED,
    PARAMETER_FILE,
)
from sora.data.parser import parse_slot_list
from sora.genetic_algorithm.constraints import check_feasibility
from sora.genetic_algorithm.optimizer import GeneticAlgorithmOptimizer
from sora.hill_climbing.local_search import run_hill_climbing

REPRESENTATIVE_DAYS = ["Senin", "Rabu", "Sabtu"]
DEFAULT_PARAMETER_GRID = {
    "population_size": [50, 100],
    "mutation_rate": [0.01, 0.05, 0.10],
    "crossover_rate": [0.70, 0.80, 0.90],
}


def required_calibration_columns(days: list[str] | None = None) -> list[str]:
    """Return required dataset columns for calibration."""
    selected_days = days or REPRESENTATIVE_DAYS
    return ["Nama"] + [column for day in selected_days for column in (f"Kerja_{day}", f"Kuliah_{day}")]


def _parameter_combinations(parameter_grid: dict[str, list[float | int]]) -> list[dict]:
    """Expand a calibration grid into parameter dictionaries."""
    keys = ["population_size", "mutation_rate", "crossover_rate"]
    return [dict(zip(keys, values, strict=True)) for values in itertools.product(*(parameter_grid[key] for key in keys))]


def run_parameter_grid_search(
    dataset_path=DATASET_CALIBRATION,
    output_file=PARAMETER_FILE,
    random_seed: int = DEFAULT_RANDOM_SEED,
    parameter_grid: dict[str, list[float | int]] | None = None,
    generations: int = 150,
) -> tuple[dict | None, pd.DataFrame]:
    """Search GA hyperparameters using representative calibration days."""
    dataset = pd.read_csv(dataset_path)
    missing_columns = [column for column in required_calibration_columns() if column not in dataset.columns]
    if missing_columns:
        raise ValueError(f"Missing required calibration columns: {missing_columns}")
    if dataset.empty:
        raise ValueError("Calibration dataset has no subject rows")

    grid = parameter_grid or DEFAULT_PARAMETER_GRID
    results = []

    for parameter_idx, parameters in enumerate(_parameter_combinations(grid)):
        total_fitness = 0.0
        total_evaluations = 0
        for subject_idx, (_, row) in enumerate(dataset.iterrows()):
            subject_fitness = 0.0
            evaluated_days = 0
            for day_idx, day_name in enumerate(REPRESENTATIVE_DAYS):
                work_slots = parse_slot_list(row[f"Kerja_{day_name}"])
                class_slots = parse_slot_list(row[f"Kuliah_{day_name}"])
                overlap = sorted(set(work_slots) & set(class_slots))
                if overlap:
                    raise ValueError(f"Work and class slots overlap for {row['Nama']} on {day_name}: {overlap}")

                optimizer = GeneticAlgorithmOptimizer(
                    work_slots=work_slots,
                    class_slots=class_slots,
                    population_size=int(parameters["population_size"]),
                    mutation_rate=float(parameters["mutation_rate"]),
                    crossover_rate=float(parameters["crossover_rate"]),
                    random_seed=random_seed + (parameter_idx * 10000) + (subject_idx * 100) + day_idx,
                )
                if not check_feasibility(optimizer.mandatory_absolute):
                    continue

                best_ga = optimizer.run_genetic_algorithm(generations=generations)
                best_schedule = run_hill_climbing(optimizer, best_ga)
                subject_fitness += optimizer.calculate_fitness(best_schedule).fitness
                evaluated_days += 1

            if evaluated_days:
                total_fitness += subject_fitness / evaluated_days
                total_evaluations += 1

        average_fitness = total_fitness / total_evaluations if total_evaluations else float("-inf")
        results.append(
            {
                "population_size": int(parameters["population_size"]),
                "mutation_rate": float(parameters["mutation_rate"]),
                "crossover_rate": float(parameters["crossover_rate"]),
                "average_fitness": float(average_fitness),
                "subjects_evaluated": int(total_evaluations),
            }
        )

    result_df = pd.DataFrame(results)
    if result_df.empty or result_df["average_fitness"].eq(float("-inf")).all():
        return None, result_df

    best_row = result_df.loc[result_df["average_fitness"].idxmax()]
    best_parameters = {
        "population_size": int(best_row["population_size"]),
        "mutation_rate": float(best_row["mutation_rate"]),
        "crossover_rate": float(best_row["crossover_rate"]),
    }

    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(best_parameters, indent=2), encoding="utf-8")
    return best_parameters, result_df
