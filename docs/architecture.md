# Arsitektur SORA Academic

## Peta folder

```text
sora_academic/
├── api.py                  # REST API FastAPI
├── requirements.txt        # Dependency backend
├── pyproject.toml          # Konfigurasi pytest dan ruff
├── dataset/                # Dataset CSV yang dipakai optimizer
├── src/sora/               # Engine inti SORA
│   ├── data/               # Parser dan validasi dataset
│   ├── genetic_algorithm/  # Chromosome, GA, repair, dan fitness
│   ├── hill_climbing/      # Optimasi lokal
│   ├── experiments/        # Weekly, baseline, calibration
│   └── utils/              # Metric dan helper
├── frontend/               # React/Vite SPA
│   ├── src/                # UI dan style
│   └── app.py              # Streamlit legacy app
├── scripts/                # Pipeline thesis dan report
└── tests/                  # Test engine backend
```

## Alur data

1. Dataset CSV/XLSX diunggah melalui `api.py`.
2. Dataset kuesioner dinormalisasi menjadi kolom `Kerja_<Hari>`,
   `Kuliah_<Hari>`, dan `Tidur_<Hari>`.
3. `experiments/weekly.py` memilih satu responden.
4. Genetic Algorithm mengoptimalkan tidur aktual dan power nap,
   dengan kerja/kuliah sebagai constraint.
5. API mengembalikan jadwal awal, jadwal hasil optimasi, metric, dan history.
6. React SPA memvisualisasikan perbandingan tujuh hari dan perubahan iterasi.

## Command utama

Backend:

```powershell
$env:PYTHONPATH="src"
.\.venv\Scripts\python.exe -m uvicorn api:app --reload
```

Frontend:

```powershell
cd frontend
& "C:\Program Files\nodejs\npm.cmd" run dev
```

Validasi:

```powershell
.\.venv\Scripts\python.exe -m compileall src api.py
.\.venv\Scripts\ruff.exe check api.py src
cd frontend
& "C:\Program Files\nodejs\npm.cmd" run build
```
