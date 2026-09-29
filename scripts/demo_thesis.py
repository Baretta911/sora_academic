#!/usr/bin/env python
"""Generate thesis-ready artifacts using the SORA Academic backend."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from sora.config import DATASET_CALIBRATION, DATASET_TEST, DEFAULT_RANDOM_SEED, THESIS_OUTPUT_DIR
from sora.data.parser import normalize_questionnaire_dataframe
from sora.experiments.calibration import run_parameter_grid_search
from sora.experiments.multi_subject import run_multi_subject_comparison, summarize_multi_subject_results
from sora.experiments.weekly import DAYS, run_weekly_optimization_with_history

DEFAULT_PARAMETERS = {"population_size": 50, "mutation_rate": 0.10, "crossover_rate": 0.80}
SUMMARY_COLUMNS = [
    "subject",
    "days",
    "optimized_days",
    "avg_fitness",
    "avg_sleep_hours",
    "schedule_file",
    "metrics_file",
]


def setup_output_dir() -> Path:
    """Create academic thesis output directories."""
    output_dir = ROOT / THESIS_OUTPUT_DIR
    (output_dir / "results" / "weekly_schedules").mkdir(parents=True, exist_ok=True)
    (output_dir / "results" / "daily_metrics").mkdir(parents=True, exist_ok=True)
    return output_dir


def load_subjects(dataset_path: Path) -> list[str]:
    """Return subject names from the test dataset."""
    dataset = normalize_questionnaire_dataframe(pd.read_csv(dataset_path))
    return dataset["Nama"].astype(str).drop_duplicates().tolist()


def run_calibration(output_dir: Path, random_seed: int, quick: bool) -> tuple[dict, str]:
    """Run calibration or return defaults if calibration cannot complete."""
    parameter_file = output_dir / "results" / "best_params_academic.json"
    parameter_grid = (
        {"population_size": [10], "mutation_rate": [0.05], "crossover_rate": [0.80]}
        if quick
        else None
    )
    generations = 3 if quick else 150
    try:
        best_parameters, result_df = run_parameter_grid_search(
            dataset_path=ROOT / DATASET_CALIBRATION,
            output_file=parameter_file,
            random_seed=random_seed,
            parameter_grid=parameter_grid,
            generations=generations,
        )
    except (OSError, ValueError) as exc:
        print(f"[WARN] Calibration failed: {exc}")
        return DEFAULT_PARAMETERS.copy(), "default_fallback"

    result_df.to_csv(output_dir / "results" / "calibration_results.csv", index=False)
    if best_parameters is None:
        return DEFAULT_PARAMETERS.copy(), "default_fallback"
    return best_parameters, "grid_search_calibration"


def run_weekly_batch(output_dir: Path, subjects: list[str], parameters: dict, random_seed: int) -> list[dict]:
    """Run weekly optimization for selected subjects and save tables."""
    summaries = []
    for subject_idx, subject in enumerate(subjects):
        print(f"[{subject_idx + 1}/{len(subjects)}] Optimizing {subject}")
        schedule, metrics, history = run_weekly_optimization_with_history(
            dataset_path=ROOT / DATASET_TEST,
            parameters=parameters,
            target_name=subject,
            random_seed=random_seed + subject_idx,
        )
        if schedule is None:
            continue

        schedule_df = pd.DataFrame(schedule, index=DAYS)
        metrics_df = pd.DataFrame(metrics)
        history_df = pd.DataFrame(history)

        schedule_df.to_csv(output_dir / "results" / "weekly_schedules" / f"{subject}.csv")
        metrics_df.to_csv(output_dir / "results" / "daily_metrics" / f"{subject}.csv", index=False)
        if not history_df.empty:
            history_df.to_csv(output_dir / "results" / "daily_metrics" / f"{subject}_convergence.csv", index=False)

        optimized_metrics = metrics_df[metrics_df["status"] == "optimized"]
        summaries.append(
            {
                "subject": subject,
                "days": len(schedule_df),
                "optimized_days": len(optimized_metrics),
                "avg_fitness": float(optimized_metrics["fitness"].mean()) if not optimized_metrics.empty else None,
                "avg_sleep_hours": float(metrics_df["sleep_hours"].mean()) if "sleep_hours" in metrics_df else 0.0,
                "schedule_file": f"results/weekly_schedules/{subject}.csv",
                "metrics_file": f"results/daily_metrics/{subject}.csv",
            }
        )
    return summaries


def write_documentation(output_dir: Path, summaries: list[dict], parameters: dict, parameter_source: str, seed: int) -> None:
    """Write metadata and reproducibility notes."""
    timestamp = datetime.now().astimezone().isoformat(timespec="seconds")
    metadata = {
        "timestamp": timestamp,
        "implementation": "sora_academic",
        "subjects_tested": len(summaries),
        "parameters": parameters,
        "parameter_source": parameter_source,
        "random_seed": seed,
        "dataset": {"calibration": DATASET_CALIBRATION, "test": DATASET_TEST},
    }
    (output_dir / "METADATA.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    (output_dir / "README.md").write_text(
        "\n".join(
            [
                "# SORA Academic Thesis Output",
                "",
                f"Generated: {timestamp}",
                f"Subjects tested: {len(summaries)}",
                f"Parameter source: {parameter_source}",
                f"Random seed: {seed}",
                "",
                "## Files",
                "",
                "- `summary_report.csv`: aggregated weekly optimization summary",
                "- `results/best_params_academic.json`: calibrated parameters when calibration succeeds",
                "- `results/weekly_schedules/`: 7-day chromosome schedules per subject",
                "- `results/daily_metrics/`: daily metrics and convergence histories",
            ]
        ),
        encoding="utf-8",
    )
    (output_dir / "INSTRUCTIONS.md").write_text(
        r"""\
# Reproduction Instructions

Run from the `sora_academic` directory:

```powershell
.\.venv\Scripts\python.exe scripts\demo_thesis.py --quick --subjects 2
```

For a full run, remove `--quick` and use `--full`.
""",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="SORA Academic thesis artifact pipeline")
    parser.add_argument("--full", action="store_true", help="Run all subjects")
    parser.add_argument("--subjects", type=int, default=2, help="Number of subjects for quick batch")
    parser.add_argument("--skip-calibration", action="store_true", help="Use default academic parameters")
    parser.add_argument("--quick", action="store_true", help="Use a tiny calibration grid for smoke runs")
    parser.add_argument("--seed", type=int, default=DEFAULT_RANDOM_SEED, help="Random seed")
    args = parser.parse_args()

    output_dir = setup_output_dir()
    subjects = load_subjects(ROOT / DATASET_TEST)
    selected_subjects = subjects if args.full else subjects[: args.subjects]

    parameter_file = output_dir / "results" / "best_params_academic.json"
    if args.skip_calibration or (parameter_file.exists() and not args.quick):
        if parameter_file.exists() and not args.skip_calibration:
            parameters = json.loads(parameter_file.read_text(encoding="utf-8"))
            parameter_source = "grid_search_calibration"
        else:
            parameters = DEFAULT_PARAMETERS.copy()
            parameter_source = "default_fallback"
    else:
        parameters, parameter_source = run_calibration(output_dir, args.seed, args.quick)

    summaries = run_weekly_batch(output_dir, selected_subjects, parameters, args.seed)
    summary_df = pd.DataFrame(summaries, columns=SUMMARY_COLUMNS)
    summary_df.to_csv(output_dir / "summary_report.csv", index=False)

    result_df = run_multi_subject_comparison(
        normalize_questionnaire_dataframe(pd.read_csv(ROOT / DATASET_TEST)).drop_duplicates(subset=["Nama"]),
        parameters,
        random_seed=args.seed,
    )
    if not result_df.empty:
        result_df.to_csv(output_dir / "results" / "multi_subject_comparison.csv", index=False)
        summarize_multi_subject_results(result_df).to_csv(
            output_dir / "results" / "multi_subject_summary.csv", index=False
        )
    write_documentation(output_dir, summaries, parameters, parameter_source, args.seed)

    print(f"[OK] Academic thesis output written to {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
