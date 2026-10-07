from pathlib import Path
import pandas as pd
import ast
import re


ROOT = Path(__file__).resolve().parents[1]
DATASET_DIR = ROOT / "dataset"

INPUT_FILE = (
    DATASET_DIR
    / "Jawaban Data Jadwal Kegiatan & Istirahat"
)

CALIBRATION_FILE = DATASET_DIR / "dataset_kalibrasi_sora.csv"
TESTING_FILE = DATASET_DIR / "dataset_pengujian_sora.csv"

CALIBRATION_SIZE = 10

DAYS = [
    "Senin",
    "Selasa",
    "Rabu",
    "Kamis",
    "Jumat",
    "Sabtu",
    "Minggu",
]


def parse_time_ranges(value):
    """Mengubah rentang waktu menjadi slot 30 menit (0-47)."""

    text = str(value).strip()

    if text.lower() in {"nan", "", "-", "null", "none"}:
        return []

    slots = []

    for item in text.split(","):
        match = re.fullmatch(
            r"\s*(\d{1,2}):(\d{2})\s*-\s*"
            r"(\d{1,2}):(\d{2})\s*",
            item,
        )

        if not match:
            raise ValueError(
                f"Format waktu tidak valid: {item!r}"
            )

        start_hour, start_minute, end_hour, end_minute = map(
            int, match.groups()
        )

        start = start_hour * 2 + start_minute // 30
        end = end_hour * 2 + end_minute // 30

        if end <= start:
            end += 48

        slots.extend(
            slot % 48
            for slot in range(start, end)
        )

    return sorted(set(slots))


def normalize_dataset(df):
    """Mengubah format Google Forms menjadi format SORA."""

    name_column = "Nama Lengkap / Inisial"

    normalized = pd.DataFrame()

    normalized["Nama"] = [
        f"Subjek_{i:03d}"
        for i in range(1, len(df) + 1)
    ]

    for day in DAYS:

        normalized[f"Kerja_{day}"] = df[
            f"Jadwal Jam Kerja ({day})"
        ].map(parse_time_ranges).map(str)

        normalized[f"Kuliah_{day}"] = df[
            f"Jadwal Jam Kuliah ({day})"
        ].map(parse_time_ranges).map(str)

        normalized[f"Tidur_{day}"] = df[
            f"Jadwal Jam Tidur / Istirahat Utama ({day})"
        ].map(parse_time_ranges).map(str)

    return normalized


def main():

    print("Membaca dataset:", INPUT_FILE)

    df = pd.read_csv(INPUT_FILE)

    print(f"Jumlah respons: {len(df)}")

    if len(df) != 63:
        raise ValueError(
            f"Jumlah respons tidak sesuai. "
            f"Ditemukan {len(df)}, seharusnya 63."
        )

    # Normalisasi
    normalized = normalize_dataset(df)

    # Split berdasarkan URUTAN respons
    calibration = normalized.iloc[:CALIBRATION_SIZE].copy()
    testing = normalized.iloc[CALIBRATION_SIZE:].copy()

    # Validasi jumlah
    assert len(calibration) == 10
    assert len(testing) == 53

    # Simpan
    calibration.to_csv(
        CALIBRATION_FILE,
        index=False
    )

    testing.to_csv(
        TESTING_FILE,
        index=False
    )

    print()
    print("Dataset berhasil dibuat.")
    print(
        f"Kalibrasi : {len(calibration)} "
        f"→ {CALIBRATION_FILE}"
    )
    print(
        f"Pengujian : {len(testing)} "
        f"→ {TESTING_FILE}"
    )


if __name__ == "__main__":
    main()