"""Metric extraction and sleep-history helpers."""

from pathlib import Path

import numpy as np
import pandas as pd

from sora.config import HISTORY_FILE


def extract_metrics(optimizer, chromosome: list[int]) -> dict[str, float]:
    """Convert FitnessResult into a table-friendly dictionary."""
    result = optimizer.calculate_fitness(chromosome)
    return {
        "fitness": result.fitness,
        "fatigue": result.fatigue_end,
        "sleep_hours": result.sleep_hours,
        "core_start": result.core_start,
        "recovery": result.recovery_reward,
        "penalty": result.dynamic_penalty,
        "regularity_penalty": result.regularity_penalty,
        "nap_sessions": result.nap_sessions,
    }


def calculate_debt_installment(history_file=HISTORY_FILE, base_sleep_target: float = 7.0) -> int:
    """Calculate additional sleep slots from the last three sleep-history rows."""
    path = Path(history_file)
    if not path.exists():
        return 0

    try:
        history = pd.read_csv(path)
    except (OSError, pd.errors.EmptyDataError, pd.errors.ParserError, UnicodeDecodeError):
        return 0

    if history.empty or "sleep_hours" not in history.columns:
        return 0

    total_debt_hours = 0.0
    for sleep_actual in pd.to_numeric(history.tail(3)["sleep_hours"], errors="coerce").dropna():
        if sleep_actual < base_sleep_target:
            total_debt_hours += base_sleep_target - float(sleep_actual)

    if total_debt_hours <= 0:
        return 0
    daily_repayment_hours = min(1.5, total_debt_hours * 0.30)
    return int(np.ceil(daily_repayment_hours * 2))
