"""REST API for the SORA Academic optimization engine."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Annotated

import pandas as pd
from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from sora.config import (
    DATASET_TEST,
    DEFAULT_CROSSOVER_RATE,
    DEFAULT_MUTATION_RATE,
    DEFAULT_POPULATION_SIZE,
)
from sora.data.parser import normalize_questionnaire_dataframe, parse_time_ranges
from sora.experiments.baseline import run_baseline_comparison_with_details
from sora.experiments.calibration import run_parameter_grid_search
from sora.experiments.weekly import run_weekly_optimization_with_history

ROOT = Path(__file__).resolve().parent
DATASET_DIR = ROOT / "dataset"

app = FastAPI(title="SORA Academic API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class OptimizationParameters(BaseModel):
    population_size: int = Field(DEFAULT_POPULATION_SIZE, ge=10, le=500)
    mutation_rate: float = Field(DEFAULT_MUTATION_RATE, ge=0, le=1)
    crossover_rate: float = Field(DEFAULT_CROSSOVER_RATE, ge=0, le=1)
    hill_climbing_iterations: int = Field(20, ge=0, le=200)


class WeeklyRequest(OptimizationParameters):
    target_name: str = Field(min_length=1, max_length=200)
    dataset_name: str = DATASET_TEST
    random_seed: int = Field(42, ge=0)


class BaselineRequest(OptimizationParameters):
    subject_name: str = Field(min_length=1, max_length=200)
    dataset_name: str = DATASET_TEST
    random_seed: int = Field(42, ge=0)


class CalibrationRequest(BaseModel):
    dataset_name: str = "dataset/dataset_kalibrasi_sora.csv"
    random_seed: int = Field(42, ge=0)
    generations: int = Field(20, ge=1, le=150)


def resolve_dataset(name: str) -> Path:
    candidate = (ROOT / name).resolve()
    if DATASET_DIR.resolve() not in candidate.parents or candidate.suffix.lower() != ".csv":
        raise HTTPException(status_code=400, detail="Dataset harus berupa CSV di folder dataset.")
    if not candidate.is_file():
        raise HTTPException(status_code=404, detail="Dataset tidak ditemukan.")
    return candidate


QUESTIONNAIRE_DAYS = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]


def normalize_questionnaire(dataset: pd.DataFrame) -> pd.DataFrame:
    """Normalize the Indonesian questionnaire layout to SORA slot columns."""
    if "Nama" in dataset.columns:
        return dataset
    name_column = "Nama Lengkap / Inisial"
    if name_column not in dataset.columns:
        raise HTTPException(status_code=422, detail="Dataset harus memiliki kolom Nama atau Nama Lengkap / Inisial.")
    normalized = pd.DataFrame({"Nama": dataset[name_column].fillna("").astype(str).str.strip()})
    for day in QUESTIONNAIRE_DAYS:
        for source_activity, target_activity in [
            ("Kerja", "Kerja"),
            ("Kuliah", "Kuliah"),
            ("Tidur / Istirahat Utama", "Tidur"),
        ]:
            source = f"Jadwal Jam {source_activity} ({day})"
            if source not in dataset.columns:
                raise HTTPException(status_code=422, detail=f"Kolom kuesioner tidak lengkap: {source}.")
            normalized[f"{target_activity}_{day}"] = dataset[source].map(
                lambda value: str(parse_time_ranges(value))
            )
    return normalized


def parameters_from(request: OptimizationParameters) -> dict:
    return request.model_dump()


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "sora-academic"}


@app.get("/")
def root() -> dict[str, object]:
    return {
        "service": "sora-academic",
        "status": "ok",
        "docs": "/docs",
        "health": "/api/health",
    }


@app.get("/api/datasets")
def list_datasets() -> list[dict]:
    return [
        {
            "name": path.name,
            "size": path.stat().st_size,
            "modified_at": path.stat().st_mtime,
            "status": "active",
        }
        for path in sorted(DATASET_DIR.glob("*.csv"))
    ]


@app.post("/api/datasets/upload")
async def upload_dataset(file: Annotated[UploadFile, File(...)]) -> dict:
    if not file.filename or Path(file.filename).suffix.lower() not in {".csv", ".xlsx", ".xls"}:
        raise HTTPException(status_code=400, detail="Format yang didukung: CSV, XLSX, atau XLS.")
    safe_name = Path(file.filename).name
    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="File dataset kosong.")
    suffix = Path(safe_name).suffix.lower()
    try:
        if suffix == ".csv":
            source = pd.read_csv(BytesIO(contents))
        else:
            source = pd.read_excel(BytesIO(contents))
        normalized = normalize_questionnaire(source)
    except HTTPException:
        raise
    except (ValueError, OSError, ImportError) as exc:
        raise HTTPException(status_code=422, detail=f"Dataset tidak dapat dibaca: {exc}") from exc
    output_name = f"{Path(safe_name).stem}.csv" if suffix != ".csv" else safe_name
    destination = DATASET_DIR / output_name
    normalized.to_csv(destination, index=False)
    return {"name": output_name, "size": destination.stat().st_size, "status": "uploaded", "rows": len(normalized)}


@app.get("/api/datasets/{dataset_name}/subjects")
def list_subjects(dataset_name: str) -> dict[str, list[str]]:
    dataset = normalize_questionnaire_dataframe(pd.read_csv(resolve_dataset(dataset_name)))
    if "Nama" not in dataset.columns:
        raise HTTPException(status_code=422, detail="Dataset tidak memiliki kolom Nama.")
    subjects = dataset["Nama"].dropna().astype(str).str.strip()
    return {"subjects": list(dict.fromkeys(subject for subject in subjects if subject))}


@app.get("/api/subjects")
def list_subjects_query(dataset_name: str = Query(DATASET_TEST)) -> dict[str, list[str]]:
    return list_subjects(dataset_name)


@app.post("/api/weekly/optimize")
def optimize_weekly(request: WeeklyRequest) -> dict:
    schedule, metrics, history = run_weekly_optimization_with_history(
        resolve_dataset(request.dataset_name),
        parameters_from(request),
        request.target_name,
        random_seed=request.random_seed,
    )
    if schedule is None:
        raise HTTPException(status_code=404, detail="Subjek tidak ditemukan dalam dataset.")
    return {
        "target_name": request.target_name,
        "schedule": schedule,
        "observed_schedule": [metric.get("observed_schedule", [3] * 48) for metric in metrics],
        "metrics": metrics,
        "history": history,
    }


@app.post("/api/baseline/compare")
def compare_baseline(request: BaselineRequest) -> dict:
    dataset = normalize_questionnaire_dataframe(pd.read_csv(resolve_dataset(request.dataset_name)))
    rows = dataset[dataset["Nama"].astype(str).str.casefold() == request.subject_name.strip().casefold()]
    if rows.empty:
        raise HTTPException(status_code=404, detail="Subjek baseline tidak ditemukan.")
    return run_baseline_comparison_with_details(
        rows.iloc[0],
        parameters_from(request),
        random_seed=request.random_seed,
    )


@app.post("/api/calibration/run")
def calibrate(request: CalibrationRequest) -> dict:
    best, results = run_parameter_grid_search(
        dataset_path=resolve_dataset(request.dataset_name),
        random_seed=request.random_seed,
        generations=request.generations,
    )
    return {"best_parameters": best, "results": results.to_dict(orient="records")}
