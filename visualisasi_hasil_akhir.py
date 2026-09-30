
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

# =====================================================
# KONFIGURASI
# =====================================================
ROOT = Path("thesis_output_academic")
METRICS_DIR = ROOT / "hasil" / "daily_metrics"
WEEKLY_DIR = ROOT / "hasil" / "weekly_schedules"
SUMMARY_FILE = ROOT / "hasil" / "summary_report.csv"
BASELINE_FILE = ROOT / "results" / "baseline_comparison_53.csv"

OUT = ROOT / "visualisasi_hasil_akhir"
OUT.mkdir(parents=True, exist_ok=True)

DAYS = ["Senin", "Selasa", "Rabu", "Kamis",
        "Jumat", "Sabtu", "Minggu"]

# =====================================================
# BACA DATA
# =====================================================
def read_csv(path):
    return pd.read_csv(path, encoding="utf-8-sig")

if not SUMMARY_FILE.exists():
    raise FileNotFoundError(f"File tidak ditemukan: {SUMMARY_FILE}")

summary = read_csv(SUMMARY_FILE)

# Gabungkan seluruh daily_metrics standar.
# File konvergensi diabaikan.
metric_files = [
    p for p in METRICS_DIR.glob("*.csv")
    if not p.stem.endswith("_convergence")
]

if not metric_files:
    raise FileNotFoundError(
        f"Tidak ditemukan CSV metrik di {METRICS_DIR}"
    )

frames = []
for path in metric_files:
    df = read_csv(path)
    if "day" not in df.columns:
        print(f"Lewati (kolom day tidak ada): {path.name}")
        continue
    df["source_file"] = path.name
    frames.append(df)

if not frames:
    raise ValueError("Tidak ada file metrik dengan kolom day.")

metrics = pd.concat(frames, ignore_index=True)

# Konversi numerik bila kolom tersedia.
for col in ["fitness", "sleep_hours", "fatigue_end"]:
    if col in metrics.columns:
        metrics[col] = pd.to_numeric(metrics[col], errors="coerce")

# =====================================================
# 1. PERBANDINGAN BASELINE
# =====================================================
if BASELINE_FILE.exists():
    baseline = read_csv(BASELINE_FILE)
    print("\nKolom baseline:", list(baseline.columns))

    # Tampilkan ringkasan statistik kolom numerik.
    numeric = baseline.select_dtypes(include="number")
    numeric.describe().to_csv(
        OUT / "ringkasan_numerik_baseline.csv"
    )

    # Jika data berbentuk satu baris per subjek dan memiliki
    # kolom fitness untuk tiap metode, atur nama kolom di sini.
    # Contoh: {"SORA": "sora_fitness", ...}
    METHOD_COLUMNS = {
        "SORA": "sora_fitness",
        "Greedy": "greedy_fitness",
        "Fixed Schedule": "fixed_fitness",
    }

    if all(c in baseline.columns for c in METHOD_COLUMNS.values()):
        plot_data = pd.DataFrame({
            name: pd.to_numeric(baseline[col], errors="coerce")
            for name, col in METHOD_COLUMNS.items()
        })

        plot_data.boxplot()
        plt.title("Distribusi Fitness antar Metode")
        plt.ylabel("Fitness")
        plt.xlabel("Metode")
        plt.tight_layout()
        plt.savefig(OUT / "01_perbandingan_baseline_boxplot.png",
                    dpi=300)
        plt.close()

        plot_data.mean().plot(kind="bar")
        plt.title("Rata-rata Fitness antar Metode")
        plt.ylabel("Rata-rata Fitness")
        plt.xlabel("Metode")
        plt.xticks(rotation=0)
        plt.tight_layout()
        plt.savefig(OUT / "01b_rata_rata_baseline.png", dpi=300)
        plt.close()
    else:
        print(
            "Kolom fitness baseline belum cocok dengan "
            "METHOD_COLUMNS. Sesuaikan nama kolom pada script."
        )
else:
    print(f"Baseline tidak ditemukan: {BASELINE_FILE}")

# =====================================================
# 2. DISTRIBUSI FITNESS SORA
# =====================================================
if "fitness" in metrics.columns:
    fitness = metrics["fitness"].dropna()

    plt.figure()
    plt.hist(fitness, bins=20, edgecolor="black")
    plt.axvline(fitness.median(), linestyle="--",
                label=f"Median: {fitness.median():.2f}")
    plt.title("Distribusi Fitness SORA")
    plt.xlabel("Fitness")
    plt.ylabel("Frekuensi")
    plt.legend()
    plt.tight_layout()
    plt.savefig(OUT / "02_distribusi_fitness.png", dpi=300)
    plt.close()

    fitness.describe().to_csv(OUT / "statistik_fitness.csv")

# =====================================================
# 3. DURASI TIDUR
# =====================================================
if "sleep_hours" in metrics.columns:
    sleep = metrics["sleep_hours"].dropna()

    plt.figure()
    plt.hist(sleep, bins=15, edgecolor="black")
    plt.axvline(sleep.mean(), linestyle="--",
                label=f"Rata-rata: {sleep.mean():.2f} jam")
    plt.title("Distribusi Durasi Tidur SORA")
    plt.xlabel("Durasi tidur (jam)")
    plt.ylabel("Frekuensi")
    plt.legend()
    plt.tight_layout()
    plt.savefig(OUT / "03_distribusi_durasi_tidur.png", dpi=300)
    plt.close()

    sleep.describe().to_csv(OUT / "statistik_durasi_tidur.csv")

# =====================================================
# 4. RATA-RATA FITNESS PER HARI
# =====================================================
if "fitness" in metrics.columns:
    daily = metrics.copy()
    daily["day"] = pd.Categorical(
        daily["day"], categories=DAYS, ordered=True
    )
    daily_mean = daily.groupby("day", observed=False)["fitness"].mean()
    daily_mean.to_csv(OUT / "rata_rata_fitness_per_hari.csv")

    plt.figure()
    daily_mean.plot(marker="o")
    plt.title("Rata-rata Fitness per Hari")
    plt.xlabel("Hari")
    plt.ylabel("Rata-rata Fitness")
    plt.xticks(range(len(DAYS)), DAYS, rotation=30)
    plt.grid(True, axis="y", alpha=0.3)
    plt.tight_layout()
    plt.savefig(OUT / "04_fitness_per_hari.png", dpi=300)
    plt.close()

# =====================================================
# 5. CONTOH JADWAL MINGGUAN
# =====================================================
# Struktur weekly_schedules belum diasumsikan karena format
# kolomnya perlu dipastikan terlebih dahulu.
weekly_files = list(WEEKLY_DIR.glob("*.csv"))

if weekly_files:
    sample = read_csv(weekly_files[0])
    print("\nContoh file jadwal:", weekly_files[0].name)
    print("Kolom jadwal:", list(sample.columns))
    print(sample.head(3).to_string(index=False))
else:
    print("Folder weekly_schedules kosong atau tidak ditemukan.")

print("\nSelesai. Output tersimpan di:", OUT.resolve())