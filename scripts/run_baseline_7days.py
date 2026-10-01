from pathlib import Path
import sys
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.sora.experiments.baseline import (
    run_baseline_comparison_with_details,
)
DATASET_TEST = "dataset/dataset_pengujian_sora_fixed.csv"

# Sesuaikan import ini dengan fungsi normalisasi
# yang digunakan oleh demo_thesis.py.
from src.sora.data.parser import normalize_questionnaire_dataframe


def main():
    dataset_path = ROOT / DATASET_TEST
    df = pd.read_csv(dataset_path)
    df = normalize_questionnaire_dataframe(df)

    parameters = {
        "population_size": 50,
        "mutation_rate": 0.01,
        "crossover_rate": 0.90,
    }

    # Pastikan seluruh kolom tujuh hari tersedia.
    days = [
        "Senin", "Selasa", "Rabu", "Kamis",
        "Jumat", "Sabtu", "Minggu",
    ]
    required = [
        f"{prefix}_{day}"
        for day in days
        for prefix in ("Kerja", "Kuliah")
    ]
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(
            "Kolom jadwal 7 hari belum lengkap: "
            + ", ".join(missing)
        )

    # Gunakan seluruh responden pada dataset pengujian.
    if len(df) < 53:
        raise ValueError(
            f"Dataset hanya memiliki {len(df)} baris; "
            "dibutuhkan minimal 53 responden."
        )

    selected = df.head(53)
    daily_rows = []
    weekly_rows = []

    for i, (_, subject) in enumerate(selected.iterrows(), start=1):
        print(f"[{i}/53] Menjalankan baseline...")

        result = run_baseline_comparison_with_details(
            subject,
            parameters=parameters,
            random_seed=42 + i,
        )

        daily = result["daily_metrics"]

        for method, method_days in daily.items():
            for day_index, metrics in enumerate(method_days):
                daily_rows.append({
                    "responden": i,
                    "metode": method,
                    "hari_ke": day_index + 1,
                    "hari": days[day_index],
                    **metrics,
                })

        for method, metrics in result["metrics"].items():
            weekly_rows.append({
                "responden": i,
                "nama": subject.get("Nama", f"baris_{i}"),
                "metode": method,
            })

    output_dir = ROOT / "thesis_output_academic" / "results"
    output_dir.mkdir(parents=True, exist_ok=True)

    daily_df = pd.DataFrame(daily_rows)
    weekly_df = pd.DataFrame(weekly_rows)

    daily_path = output_dir / "baseline_7days_daily.v2.csv"
    weekly_path = output_dir / "baseline_7days_weekly.v2.csv"

    daily_df.to_csv(daily_path, index=False, encoding="utf-8-sig")
    weekly_df.to_csv(weekly_path, index=False, encoding="utf-8-sig")

    print("\nSelesai.")
    print(f"Data harian : {daily_path}")
    print(f"Data mingguan: {weekly_path}")
    print(f"Baris harian: {len(daily_df)}")
    print(f"Baris mingguan: {len(weekly_df)}")


if __name__ == "__main__":
    main()