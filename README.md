# SORA Academic

SORA Academic is the clean thesis-oriented implementation of Sleep Optimization
and Rest Arrangement.

The repository is organized around academic terms so the code can be explained
directly in Chapter III:

- one individual is one daily chromosome;
- one chromosome has 48 genes;
- one gene represents a 30-minute time slot;
- allele values are 0 sleep, 1 work, 2 nap, 3 rest, and 4 class;
- Genetic Algorithm operators are separated into population, selection,
  crossover, mutation, repair, fitness, and optimizer modules;
- Hill Climbing is implemented as a separate local search module;
- experiment runners are separated into weekly optimization and baseline
  comparison.

## Repository Map

```text
sora_academic/
|-- pyproject.toml
|-- docs/
|   `-- architecture.md
|-- frontend/
|   |-- src/                 # React/Vite frontend
|   `-- app.py              # Streamlit legacy frontend
|-- src/sora/
|   |-- config.py
|   |-- data/
|   |   `-- parser.py
|   |-- genetic_algorithm/
|   |   |-- representation.py
|   |   |-- constraints.py
|   |   |-- population.py
|   |   |-- selection.py
|   |   |-- crossover.py
|   |   |-- mutation.py
|   |   |-- repair.py
|   |   |-- fitness.py
|   |   `-- optimizer.py
|   |-- hill_climbing/
|   |   `-- local_search.py
|   |-- experiments/
|   |   |-- baseline.py
|   |   `-- weekly.py
|   `-- utils/
|       `-- metrics.py
`-- tests/
|-- api.py                  # FastAPI REST API
```

## Streamlit App

Run from the project root:

```powershell
.\.venv\Scripts\streamlit.exe run frontend\app.py
```

Main pages:

- Dataset Preview
- Weekly Optimization
- Baseline Comparison
- Calibration
- Multi-Subject

The frontend includes operator panel, convergence chart, chromosome viewer,
timeline visualization, daily quality panel, penalty breakdown, and CSV export.

## React SPA Frontend

The Apple-inspired SPA lives in `frontend/` and uses React, Vite, TypeScript,
and CSS design tokens. It reads datasets and optimization results from the REST
API.

```powershell
cd frontend
npm install
npm run dev
```

The existing Streamlit app remains available as `frontend/app.py` for the
legacy research workflow. See [docs/architecture.md](docs/architecture.md)
for the complete data flow and folder responsibilities.

## REST API

Install the API dependencies from the `sora_academic` directory and run:

```powershell
.\.venv\Scripts\pip.exe install -r requirements.txt
$env:PYTHONPATH="src"
.\.venv\Scripts\python.exe -m uvicorn api:app --reload
```

The API exposes `/api/health`, dataset management, weekly sleep optimization,
baseline comparison, and calibration endpoints. The React SPA consumes these
endpoints directly.

Weekly optimization uses each respondent's observed `Tidur_<Hari>` slots as
the sleep-duration and alignment baseline. The genetic algorithm may shift
those sleep slots and add a 30–90 minute power nap in the allowed window when
the change improves recovery fitness. Questionnaire files in CSV, XLSX, or
XLS format are normalized automatically on upload; the expected questionnaire
name column is `Nama Lengkap / Inisial`. The React app can use
`http://127.0.0.1:8000` as its API base URL.

## Thesis Pipeline

Run from the `sora_academic` directory:

```powershell
.\.venv\Scripts\python.exe scripts\demo_thesis.py --quick --subjects 2
```

Results are written to `thesis_output_academic/`.

Generate report tables after the pipeline:

```powershell
.\.venv\Scripts\python.exe scripts\generate_report.py --format all
```

## Verification

```powershell
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\python.exe -m compileall src api.py
.\.venv\Scripts\pytest.exe -q
```
