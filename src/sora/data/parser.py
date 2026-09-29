"""Dataset parsing helpers."""

import ast
import re

import pandas as pd


def parse_slot_list(value) -> list[int]:
    """Parse a CSV cell into a validated list of 0-47 slot integers."""
    text = str(value).strip()
    if text.lower() in {"nan", "", "null", "none"}:
        return []
    try:
        parsed = ast.literal_eval(text)
    except (ValueError, SyntaxError, TypeError) as exc:
        raise ValueError(f"Invalid slot list format: {value!r}") from exc

    if not isinstance(parsed, list):
        raise TypeError(f"Slot value must be a list: {value!r}")
    if not all(type(slot) is int and 0 <= slot < 48 for slot in parsed):
        raise ValueError(f"Slots must be unique integers in range 0-47: {value!r}")
    if len(parsed) != len(set(parsed)):
        raise ValueError(f"Slot list contains duplicates: {value!r}")
    return parsed


def parse_time_ranges(value) -> list[int]:
    """Convert questionnaire time ranges into unique 30-minute slot indices."""
    text = str(value).strip()
    if text.lower() in {"nan", "", "-", "null", "none"}:
        return []
    slots: list[int] = []
    for item in text.split(","):
        match = re.fullmatch(r"\s*(\d{1,2}):(\d{2})\s*-\s*(\d{1,2}):(\d{2})\s*", item)
        if not match:
            raise ValueError(f"Invalid time range format: {item!r}")
        start_hour, start_minute, end_hour, end_minute = map(int, match.groups())
        start = start_hour * 2 + start_minute // 30
        end = end_hour * 2 + end_minute // 30
        if start < 0 or end > 48 or start_hour > 24 or end_hour > 24:
            raise ValueError(f"Time range is outside one day: {item!r}")
        if end <= start:
            end += 48
        slots.extend(slot % 48 for slot in range(start, end))
    return sorted(set(slots))


def normalize_questionnaire_dataframe(dataset: pd.DataFrame) -> pd.DataFrame:
    """Normalize the raw Google Forms questionnaire into SORA slot columns."""
    if "Nama" in dataset.columns:
        return dataset

    name_column = "Nama Lengkap / Inisial"
    if name_column not in dataset.columns:
        raise ValueError(f"Dataset harus memiliki kolom {name_column!r} atau 'Nama'.")

    days = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
    normalized = pd.DataFrame(
        {"Nama": dataset[name_column].fillna("").astype(str).str.strip()}
    )
    for day in days:
        for source_activity, target_activity in [
            ("Kerja", "Kerja"),
            ("Kuliah", "Kuliah"),
            ("Tidur / Istirahat Utama", "Tidur"),
        ]:
            source = f"Jadwal Jam {source_activity} ({day})"
            if source not in dataset.columns:
                raise ValueError(f"Kolom kuesioner tidak lengkap: {source}.")
            normalized[f"{target_activity}_{day}"] = dataset[source].map(
                lambda value: str(parse_time_ranges(value))
            )
    return normalized


def required_weekly_columns(days: list[str]) -> list[str]:
    """Return required dataset columns for weekly optimization."""
    return ["Nama"] + [column for day in days for column in (f"Kerja_{day}", f"Kuliah_{day}")]
