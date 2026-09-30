from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt

# Lokasi data
BASE_DIR = Path("thesis_output_academic/hasil/daily_metrics")
OUTPUT_DIR = Path("thesis_output_academic/visualisasi")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Baca seluruh file konvergensi
files = list(BASE_DIR.glob("*_convergence.csv"))

if not files:
    raise FileNotFoundError(
        f"Tidak ditemukan file *_convergence.csv di {BASE_DIR}"
    )

data = pd.concat(
    [pd.read_csv(file) for file in files],
    ignore_index=True
)

# Pastikan kolom numerik terbaca sebagai angka
data["generation"] = pd.to_numeric(data["generation"], errors="coerce")
data["best_fitness"] = pd.to_numeric(data["best_fitness"], errors="coerce")
data["mean_top10_fitness"] = pd.to_numeric(
    data["mean_top10_fitness"], errors="coerce"
)

data = data.dropna(
    subset=["day", "generation", "best_fitness", "mean_top10_fitness"]
)

# Rata-rata antar peserta pada setiap hari dan generasi
aggregate = (
    data.groupby(["day", "generation"], as_index=False)
    .agg(
        best_fitness=("best_fitness", "mean"),
        mean_top10_fitness=("mean_top10_fitness", "mean"),
        jumlah_data=("best_fitness", "count")
    )
)

# Urutan hari
day_order = [
    "Senin", "Selasa", "Rabu", "Kamis",
    "Jumat", "Sabtu", "Minggu"
]

# Grafik 1: rata-rata best fitness per hari
plt.figure(figsize=(12, 6))

for day in day_order:
    subset = aggregate[aggregate["day"] == day]
    if not subset.empty:
        plt.plot(
            subset["generation"],
            subset["best_fitness"],
            label=day
        )

plt.title("Rata-rata Best Fitness pada Setiap Hari")
plt.xlabel("Generasi")
plt.ylabel("Rata-rata Best Fitness")
plt.legend(title="Hari")
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(
    OUTPUT_DIR / "konvergensi_best_fitness_per_hari.png",
    dpi=300
)
plt.close()

# Grafik 2: rata-rata mean top-10 fitness per hari
plt.figure(figsize=(12, 6))

for day in day_order:
    subset = aggregate[aggregate["day"] == day]
    if not subset.empty:
        plt.plot(
            subset["generation"],
            subset["mean_top10_fitness"],
            label=day
        )

plt.title("Rata-rata Mean Top-10 Fitness pada Setiap Hari")
plt.xlabel("Generasi")
plt.ylabel("Rata-rata Mean Top-10 Fitness")
plt.legend(title="Hari")
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(
    OUTPUT_DIR / "konvergensi_mean_top10_per_hari.png",
    dpi=300
)
plt.close()

# Simpan tabel agregat agar bisa diperiksa atau digunakan kembali
aggregate.to_csv(
    OUTPUT_DIR / "konvergensi_agregat.csv",
    index=False
)

print(f"File konvergensi dibaca: {len(files)}")
print(f"Jumlah baris sumber: {len(data)}")
print(f"Jumlah baris agregat: {len(aggregate)}")
print(f"Hasil tersimpan di: {OUTPUT_DIR.resolve()}")