from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt

# Lokasi file
INPUT_FILE = Path(
    "thesis_output_academic/results/calibration_results.csv"
)
OUTPUT_DIR = Path("thesis_output_academic/visualisasi_kalibrasi")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Baca data kalibrasi
df = pd.read_csv(INPUT_FILE)

required = [
    "population_size",
    "mutation_rate",
    "crossover_rate",
    "average_fitness",
    "subjects_evaluated",
]

missing = [col for col in required if col not in df.columns]
if missing:
    raise ValueError(f"Kolom tidak ditemukan: {missing}")

for col in required:
    df[col] = pd.to_numeric(df[col], errors="coerce")

df = df.dropna(subset=required).copy()

if df.empty:
    raise ValueError("Data kalibrasi kosong atau tidak valid.")

# Identitas kombinasi parameter
df["kombinasi"] = df.apply(
    lambda row: (
        f"Pop={int(row['population_size'])}, "
        f"Mut={row['mutation_rate']:.2f}, "
        f"Cross={row['crossover_rate']:.2f}"
    ),
    axis=1,
)

# Urutkan dari fitness tertinggi
df = df.sort_values("average_fitness", ascending=False).reset_index(drop=True)

# Simpan tabel terurut
df.to_csv(OUTPUT_DIR / "kalibrasi_terurut.csv", index=False)

# Catat parameter terbaik berdasarkan average_fitness
best = df.iloc[0]
with open(OUTPUT_DIR / "parameter_terbaik.txt", "w", encoding="utf-8") as f:
    f.write("Kombinasi dengan average_fitness tertinggi\n")
    f.write(f"Population size : {int(best['population_size'])}\n")
    f.write(f"Mutation rate   : {best['mutation_rate']}\n")
    f.write(f"Crossover rate  : {best['crossover_rate']}\n")
    f.write(f"Average fitness : {best['average_fitness']}\n")
    f.write(f"Subjects tested : {int(best['subjects_evaluated'])}\n")

# Grafik 1: seluruh kombinasi parameter
plt.figure(figsize=(14, 8))
plt.barh(df["kombinasi"], df["average_fitness"])
plt.axvline(0, linewidth=0.8)
plt.gca().invert_yaxis()
plt.title("Hasil Kalibrasi Genetic Algorithm")
plt.xlabel("Average Fitness")
plt.ylabel("Kombinasi Parameter")
plt.grid(axis="x", alpha=0.3)
plt.tight_layout()
plt.savefig(
    OUTPUT_DIR / "kalibrasi_seluruh_kombinasi.png",
    dpi=300,
    bbox_inches="tight",
)
plt.close()

# Grafik 2: pengaruh crossover untuk setiap pasangan popsize-mutation
groups = list(
    df.groupby(["population_size", "mutation_rate"], sort=True)
)

fig, axes = plt.subplots(
    len(groups), 1,
    figsize=(10, max(4, 3.2 * len(groups))),
    squeeze=False,
)

for ax, ((pop, mut), group) in zip(axes[:, 0], groups):
    group = group.sort_values("crossover_rate")
    ax.plot(
        group["crossover_rate"],
        group["average_fitness"],
        marker="o",
    )
    ax.axhline(0, linewidth=0.8)
    ax.set_title(f"Population={int(pop)}, Mutation={mut:.2f}")
    ax.set_xlabel("Crossover Rate")
    ax.set_ylabel("Average Fitness")
    ax.grid(True, alpha=0.3)

fig.suptitle(
    "Perbandingan Crossover Rate pada Setiap Kombinasi Lain",
    y=1.01,
)
fig.tight_layout()
fig.savefig(
    OUTPUT_DIR / "kalibrasi_pengaruh_crossover.png",
    dpi=300,
    bbox_inches="tight",
)
plt.close(fig)

# Grafik 3: rata-rata fitness menurut mutation rate
mutation_summary = (
    df.groupby("mutation_rate", as_index=False)
    .agg(
        mean_fitness=("average_fitness", "mean"),
        combinations=("average_fitness", "count"),
    )
    .sort_values("mutation_rate")
)

plt.figure(figsize=(8, 5))
plt.plot(
    mutation_summary["mutation_rate"],
    mutation_summary["mean_fitness"],
    marker="o",
)
plt.axhline(0, linewidth=0.8)
plt.title("Rata-rata Fitness Menurut Mutation Rate")
plt.xlabel("Mutation Rate")
plt.ylabel("Rata-rata Fitness dari Kombinasi")
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(
    OUTPUT_DIR / "kalibrasi_mutation_rate.png",
    dpi=300,
    bbox_inches="tight",
)
plt.close()

print("Kalibrasi berhasil divisualisasikan.")
print(f"Jumlah kombinasi: {len(df)}")
print("\nKombinasi dengan average_fitness tertinggi:")
print(best[required].to_string())
print(f"\nOutput: {OUTPUT_DIR.resolve()}")
