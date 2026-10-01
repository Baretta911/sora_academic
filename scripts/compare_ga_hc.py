
from pathlib import Path
import time
import pandas as pd

from sora.experiments.weekly import run_weekly_optimization
from sora.data.parser import normalize_questionnaire_dataframe

ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "dataset" / "dataset_pengujian_sora_fixed.csv"
OUTPUT = ROOT / "thesis_output_academic" / "results"

PARAMETERS = {
    "population_size": 50,
    "mutation_rate": 0.01,
    "crossover_rate": 0.90,
}

GENERATIONS = 200
HC_ITERATIONS = 20
SEED = 42
N_SUBJECTS = 53

METHODS = {
    "GA_Repair": 0,
    "GA_HC_Repair": HC_ITERATIONS,
}

def main():
    if not DATASET.exists():
        raise FileNotFoundError(f"Dataset tidak ditemukan: {DATASET}")

    df = normalize_questionnaire_dataframe(pd.read_csv(DATASET))

    if "Nama" not in df.columns:
        raise ValueError("Kolom 'Nama' tidak ditemukan.")

    if len(df) < N_SUBJECTS:
        raise ValueError(
            f"Dataset hanya memiliki {len(df)} baris; "
            f"dibutuhkan minimal {N_SUBJECTS}."
        )

    subjects = df["Nama"].astype(str).head(N_SUBJECTS).tolist()

    daily_rows = []
    summary_rows = []

    for index, subject_name in enumerate(subjects, start=1):
        subject_seed = SEED + index - 1
        print(f"[{index}/{N_SUBJECTS}] {subject_name}")

        for method_name, hc_iterations in METHODS.items():
            params = {
                **PARAMETERS,
                "hill_climbing_iterations": hc_iterations,
            }

            start = time.perf_counter()

            schedule, daily_metrics = run_weekly_optimization(
                dataset_path=DATASET,
                parameters=params,
                target_name=subject_name,
                random_seed=subject_seed,
            )

            elapsed = time.perf_counter() - start

            if schedule is None or not daily_metrics:
                print(f"  PERINGATAN: {subject_name} tidak menghasilkan jadwal.")
                continue

            valid_days = [
                item for item in daily_metrics
                if item.get("status") == "optimized"
            ]

            for day_index, item in enumerate(daily_metrics, start=1):
                daily_rows.append({
                    "responden": index,
                    "nama": subject_name,
                    "metode": method_name,
                    "seed": subject_seed,
                    "hari_ke": day_index,
                    "hari": item.get("day"),
                    "status": item.get("status"),
                    "fitness": item.get("fitness"),
                    "fatigue_end": item.get("fatigue_end"),
                    "sleep_hours": item.get("sleep_hours"),
                    "observed_sleep_hours": item.get("observed_sleep_hours"),
                    "fitness_delta": item.get("fitness_delta"),
                    "recovery": item.get("recovery"),
                    "penalty": item.get("penalty"),
                    "regularity_penalty": item.get("regularity_penalty"),
                    "nap_sessions": item.get("nap_sessions"),
                    "runtime_seconds_subject": elapsed,
                })

            def mean_metric(key):
                values = [
                    item.get(key) for item in valid_days
                    if item.get(key) is not None
                ]
                return sum(values) / len(values) if values else None

            summary_rows.append({
                "responden": index,
                "nama": subject_name,
                "metode": method_name,
                "seed": subject_seed,
                "hari_berhasil": len(valid_days),
                "fitness_mean_harian": mean_metric("fitness"),
                "fatigue_mean_harian": mean_metric("fatigue_end"),
                "sleep_hours_mean_harian": mean_metric("sleep_hours"),
                "runtime_seconds": elapsed,
            })

            print(
                f"  {method_name}: "
                f"hari={len(valid_days)}/7, "
                f"fitness={mean_metric('fitness')}, "
                f"waktu={elapsed:.2f}s"
            )

    OUTPUT.mkdir(parents=True, exist_ok=True)

    daily_path = OUTPUT / "ga_hc_comparison_daily.csv"
    summary_path = OUTPUT / "ga_hc_comparison_subjects.csv"
    group_path = OUTPUT / "ga_hc_comparison_summary.csv"

    daily_df = pd.DataFrame(daily_rows)
    summary_df = pd.DataFrame(summary_rows)

    daily_df.to_csv(daily_path, index=False)
    summary_df.to_csv(summary_path, index=False)

    if not summary_df.empty:
        group_df = (
            summary_df.groupby("metode")
            .agg(
                jumlah_subjek=("nama", "nunique"),
                fitness_mean=("fitness_mean_harian", "mean"),
                fitness_median=("fitness_mean_harian", "median"),
                fitness_sd=("fitness_mean_harian", "std"),
                fatigue_mean=("fatigue_mean_harian", "mean"),
                sleep_hours_mean=("sleep_hours_mean_harian", "mean"),
                runtime_mean_seconds=("runtime_seconds", "mean"),
                hari_berhasil_mean=("hari_berhasil", "mean"),
            )
            .reset_index()
        )
        group_df.to_csv(group_path, index=False)
        print("\nRINGKASAN KELOMPOK")
        print(group_df.to_string(index=False))

    print("\nFile tersimpan:")
    print(daily_path)
    print(summary_path)
    print(group_path)

if __name__ == "__main__":
    main()