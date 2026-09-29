"""Multi-subject baseline experiment for SORA Academic."""

from __future__ import annotations

import pandas as pd

from sora.config import DEFAULT_RANDOM_SEED
from sora.experiments.baseline import run_baseline_comparison


def run_multi_subject_comparison(
    dataset: pd.DataFrame,
    parameters: dict,
    random_seed: int = DEFAULT_RANDOM_SEED,
) -> pd.DataFrame:
    """Run representative-day baseline comparison for multiple subjects."""
    result_df, _skipped_df = run_multi_subject_comparison_with_audit(dataset, parameters, random_seed=random_seed)
    return result_df


def run_multi_subject_comparison_with_audit(
    dataset: pd.DataFrame,
    parameters: dict,
    random_seed: int = DEFAULT_RANDOM_SEED,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Run representative-day comparison and return successful plus skipped subjects."""
    rows = []
    skipped = []
    for subject_idx, (_, row) in enumerate(dataset.iterrows()):
        subject_name = row.get("Nama", f"row_{subject_idx}")
        try:
            metrics = run_baseline_comparison(row, parameters, random_seed=random_seed + subject_idx)
        except (KeyError, ValueError) as exc:
            skipped.append({"Nama": subject_name, "reason": str(exc)})
            continue

        rows.append(
            {
                "Nama": subject_name,
                "sora_fit": metrics["sora"]["fitness"],
                "greedy_fit": metrics["greedy"]["fitness"],
                "fixed_fit": metrics["fixed"]["fitness"],
                "sora_fatigue": metrics["sora"]["fatigue"],
                "greedy_fatigue": metrics["greedy"]["fatigue"],
                "fixed_fatigue": metrics["fixed"]["fatigue"],
                "sora_sleep": metrics["sora"]["sleep_hours"],
                "greedy_sleep": metrics["greedy"]["sleep_hours"],
                "fixed_sleep": metrics["fixed"]["sleep_hours"],
            }
        )
    return pd.DataFrame(rows), pd.DataFrame(skipped)


def summarize_multi_subject_results(result_df: pd.DataFrame) -> pd.DataFrame:
    """Return mean and standard deviation table for multi-subject metrics."""
    if result_df.empty:
        return pd.DataFrame()
    numeric_columns = [column for column in result_df.columns if column != "Nama"]
    return result_df[numeric_columns].agg(["mean", "std"]).transpose().reset_index(names="metric")
