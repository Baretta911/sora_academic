import csv
from pathlib import Path

source = Path("dataset/dataset_pengujian_sora.csv")
target = Path("dataset/dataset_pengujian_sora_fixed.csv")

with source.open("r", encoding="utf-8-sig", newline="") as f:
    lines = f.readlines()

header = next(csv.reader([lines[0].strip()]))
rows = []

for line_number, line in enumerate(lines[1:], start=2):
    line = line.strip()

    # Hapus pembungkus kutip luar yang keliru
    if line.startswith('"') and line.endswith('"'):
        line = line[1:-1]

    # Pulihkan kutip ganda yang digunakan untuk mengapit nilai
    line = line.replace('""', '"')

    values = next(csv.reader([line]))

    if len(values) != len(header):
        raise ValueError(
            f"Baris {line_number}: ditemukan {len(values)} kolom, "
            f"seharusnya {len(header)}. Data tidak disimpan."
        )

    rows.append(values)

with target.open("w", encoding="utf-8-sig", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(header)
    writer.writerows(rows)

print("File hasil:", target)
print("Jumlah baris:", len(rows))
print("Jumlah kolom:", len(header))