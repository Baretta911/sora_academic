import sys
from pathlib import Path

import pandas as pd
import pytest

from sora.config import DEFAULT_CROSSOVER_RATE, DEFAULT_MUTATION_RATE, DEFAULT_POPULATION_SIZE
from sora.experiments.baseline import run_baseline_comparison, run_baseline_comparison_with_details
from sora.experiments.calibration import run_parameter_grid_search
from sora.experiments.multi_subject import (
    run_multi_subject_comparison,
    run_multi_subject_comparison_with_audit,
    summarize_multi_subject_results,
)
from sora.experiments.weekly import run_weekly_optimization, run_weekly_optimization_with_history
from sora.genetic_algorithm.constraints import ScheduleContext
from sora.genetic_algorithm.mutation import mutate_chromosome
from sora.genetic_algorithm.optimizer import GeneticAlgorithmOptimizer
from sora.genetic_algorithm.representation import Allele
from sora.utils.metrics import calculate_debt_installment

SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from generate_report import load_summary

PARAMETERS = {
    "population_size": DEFAULT_POPULATION_SIZE,
    "mutation_rate": DEFAULT_MUTATION_RATE,
    "crossover_rate": DEFAULT_CROSSOVER_RATE,
}


def test_one_individual_is_one_daily_chromosome():
    optimizer = GeneticAlgorithmOptimizer([], [], population_size=10, random_seed=1)
    chromosome = optimizer.run_genetic_algorithm(generations=2)

    assert len(chromosome) == 48
    assert set(chromosome).issubset({0, 1, 2, 3, 4})


@pytest.mark.parametrize("work_slots", [[48], [-1], [1, 1], [True]])
def test_optimizer_rejects_invalid_public_slot_inputs(work_slots):
    with pytest.raises(ValueError):
        GeneticAlgorithmOptimizer(work_slots, [], population_size=10, random_seed=1)


def test_optimizer_rejects_public_work_class_overlap():
    with pytest.raises(ValueError, match="overlap"):
        GeneticAlgorithmOptimizer([10], [10], population_size=10, random_seed=1)


def test_mutation_does_not_change_mandatory_slots():
    context = ScheduleContext(
        work_slots=[10],
        class_slots=[20],
        population_size=10,
        mutation_rate=1.0,
        crossover_rate=0.8,
    )
    chromosome = [int(Allele.REST)] * 48
    chromosome[10] = int(Allele.WORK)
    chromosome[20] = int(Allele.CLASS)

    mutated = mutate_chromosome(chromosome, context, optimizer_rng(seed=2))

    assert mutated[10] == Allele.WORK
    assert mutated[20] == Allele.CLASS


def optimizer_rng(seed):
    return GeneticAlgorithmOptimizer([], [], population_size=10, random_seed=seed).rng


def test_baseline_comparison_returns_three_methods():
    row = pd.Series({"Nama": "A", "Kerja_Rabu": "[16,17,18,19]", "Kuliah_Rabu": "[28,29]"})

    result = run_baseline_comparison(row, PARAMETERS, random_seed=3)

    assert set(result) == {"sora", "greedy", "fixed"}
    assert "fitness" in result["sora"]


def test_baseline_rejects_infeasible_representative_day():
    dense_slots = list(range(0, 48, 2))
    row = pd.Series({"Nama": "A", "Kerja_Rabu": str(dense_slots), "Kuliah_Rabu": "[]"})

    with pytest.raises(ValueError, match="infeasible"):
        run_baseline_comparison(row, PARAMETERS, random_seed=3)


def test_baseline_details_include_schedules_and_convergence():
    row = pd.Series({"Nama": "A", "Kerja_Rabu": "[16,17,18,19]", "Kuliah_Rabu": "[28,29]"})

    details = run_baseline_comparison_with_details(row, PARAMETERS, random_seed=3)

    assert set(details) == {"metrics", "schedules", "convergence"}
    assert set(details["schedules"]) == {"sora", "greedy", "fixed"}
    assert len(details["schedules"]["sora"]) == 48
    assert details["convergence"]


def test_weekly_optimization_runs_from_csv(tmp_path):
    csv_path = Path(tmp_path) / "dataset.csv"
    days = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
    row = {"Nama": "A"}
    for day in days:
        row[f"Kerja_{day}"] = "[]"
        row[f"Kuliah_{day}"] = "[]"
    pd.DataFrame([row]).to_csv(csv_path, index=False)

    schedule, metrics = run_weekly_optimization(csv_path, PARAMETERS, "A", random_seed=4)

    assert len(schedule) == 7
    assert len(metrics) == 7


def test_weekly_optimization_with_history_runs_from_csv(tmp_path):
    csv_path = Path(tmp_path) / "dataset.csv"
    days = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
    row = {"Nama": "A"}
    for day in days:
        row[f"Kerja_{day}"] = "[]"
        row[f"Kuliah_{day}"] = "[]"
    pd.DataFrame([row]).to_csv(csv_path, index=False)

    schedule, metrics, history = run_weekly_optimization_with_history(csv_path, PARAMETERS, "A", random_seed=4)

    assert len(schedule) == 7
    assert len(metrics) == 7
    assert history
    assert {"day", "generation", "best_fitness", "mean_top10_fitness"}.issubset(history[0])


def test_weekly_optimization_accepts_hill_climb_iteration_budget(tmp_path):
    csv_path = Path(tmp_path) / "dataset.csv"
    days = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
    row = {"Nama": "A"}
    for day in days:
        row[f"Kerja_{day}"] = "[]"
        row[f"Kuliah_{day}"] = "[]"
    pd.DataFrame([row]).to_csv(csv_path, index=False)

    params = {**PARAMETERS, "hill_climbing_iterations": 2}
    schedule, metrics, history = run_weekly_optimization_with_history(csv_path, params, "A", random_seed=4)

    assert len(schedule) == 7
    assert len(metrics) == 7
    assert history


def test_weekly_missing_subject_returns_consistent_empty_results(tmp_path):
    csv_path = Path(tmp_path) / "dataset.csv"
    days = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
    row = {"Nama": "A"}
    for day in days:
        row[f"Kerja_{day}"] = "[]"
        row[f"Kuliah_{day}"] = "[]"
    pd.DataFrame([row]).to_csv(csv_path, index=False)

    assert run_weekly_optimization(csv_path, PARAMETERS, "B", random_seed=4) == (None, [])
    assert run_weekly_optimization_with_history(csv_path, PARAMETERS, "B", random_seed=4) == (None, [], [])


def test_debt_installment_uses_recent_sleep_history(tmp_path):
    history_path = Path(tmp_path) / "sleep_history.csv"
    pd.DataFrame({"sleep_hours": [6.0, 5.5, 7.5, 6.0]}).to_csv(history_path, index=False)

    assert calculate_debt_installment(history_path) == 2


def test_parameter_grid_search_writes_academic_parameter_file(tmp_path):
    csv_path = Path(tmp_path) / "calibration.csv"
    output_path = Path(tmp_path) / "best_params.json"
    row = {"Nama": "A"}
    for day in ["Senin", "Rabu", "Sabtu"]:
        row[f"Kerja_{day}"] = "[]"
        row[f"Kuliah_{day}"] = "[]"
    pd.DataFrame([row]).to_csv(csv_path, index=False)

    best_params, result_df = run_parameter_grid_search(
        csv_path,
        output_path,
        random_seed=5,
        parameter_grid={
            "population_size": [10],
            "mutation_rate": [0.05],
            "crossover_rate": [0.8],
        },
        generations=2,
    )

    assert best_params == {"population_size": 10, "mutation_rate": 0.05, "crossover_rate": 0.8}
    assert output_path.exists()
    assert result_df["average_fitness"].notna().all()


def test_multi_subject_comparison_returns_aggregate_table():
    df = pd.DataFrame(
        [
            {"Nama": "A", "Kerja_Rabu": "[]", "Kuliah_Rabu": "[]"},
            {"Nama": "B", "Kerja_Rabu": "[16,17]", "Kuliah_Rabu": "[]"},
        ]
    )

    result_df = run_multi_subject_comparison(df, PARAMETERS, random_seed=6)
    summary_df = summarize_multi_subject_results(result_df)

    assert len(result_df) == 2
    assert {"sora_fit", "greedy_fit", "fixed_fit"}.issubset(result_df.columns)
    assert {"metric", "mean", "std"}.issubset(summary_df.columns)


def test_multi_subject_audit_reports_skipped_subjects():
    df = pd.DataFrame(
        [
            {"Nama": "A", "Kerja_Rabu": "[]", "Kuliah_Rabu": "[]"},
            {"Nama": "B", "Kerja_Rabu": "[10]", "Kuliah_Rabu": "[10]"},
        ]
    )

    result_df, skipped_df = run_multi_subject_comparison_with_audit(df, PARAMETERS, random_seed=6)

    assert len(result_df) == 1
    assert skipped_df["Nama"].tolist() == ["B"]
    assert "overlap" in skipped_df["reason"].iloc[0]


def test_report_loader_rejects_empty_summary(tmp_path):
    summary_path = Path(tmp_path) / "summary_report.csv"
    summary_path.write_text("subject,avg_fitness,days,optimized_days\n", encoding="utf-8")

    with pytest.raises(ValueError, match="no rows"):
        load_summary(Path(tmp_path))
