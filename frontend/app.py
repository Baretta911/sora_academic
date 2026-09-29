"""SORA Academic Streamlit app with clean backend imports."""

from __future__ import annotations

import sys
import tempfile
from datetime import datetime
from html import escape
from io import BytesIO
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from sora.config import DEFAULT_CROSSOVER_RATE, DEFAULT_MUTATION_RATE, DEFAULT_POPULATION_SIZE
from sora.data.parser import parse_slot_list, required_weekly_columns
from sora.experiments.baseline import run_baseline_comparison_with_details
from sora.experiments.calibration import run_parameter_grid_search
from sora.experiments.multi_subject import (
    run_multi_subject_comparison_with_audit,
    summarize_multi_subject_results,
)
from sora.experiments.weekly import DAYS, run_weekly_optimization_with_history

PAGE_CONFIG = {
    "page_title": "SORA Academic",
    "page_icon": "S",
    "layout": "wide",
    "initial_sidebar_state": "expanded",
}


def apply_styles() -> None:
   st.markdown(
       """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&family=Space+Grotesk:wght@500;600;700&display=swap');
:root {
  --bg: #000000;
  --bg-soft: #101112;
  --surface: #161617;
  --surface-strong: #1d1d1f;
  --surface-alt: rgba(255,255,255,0.03);
  --border: rgba(255,255,255,0.10);
  --border-strong: rgba(255,255,255,0.25);
  --text: #f5f5f7;
  --muted: #86868b;
  --muted-soft: #a1a1a6;
  --accent: #2997ff;
  --accent-soft: rgba(41,151,255,0.12);
  --success: #7dd3fc;
  --glow: 0 24px 60px rgba(0,0,0,0.35);
}
html, body, [class*="css"] {
  font-family: 'Inter', sans-serif !important;
  background: var(--bg) !important;
  color: var(--text) !important;
}
[data-testid="stAppViewContainer"], .stApp, section[data-testid="stMain"] {
  background:
   radial-gradient(circle at top left, rgba(41,151,255,0.15), transparent 26%),
   radial-gradient(circle at bottom right, rgba(138,92,246,0.12), transparent 26%),
   var(--bg) !important;
}
.block-container {
  max-width: 1400px !important;
  padding-top: 0.8rem !important;
  padding-bottom: 2.2rem !important;
}
#MainMenu, footer, header { visibility: hidden; }
section[data-testid="stSidebar"] {
  background: rgba(10,10,12,0.96) !important;
  backdrop-filter: blur(20px) !important;
  border-right: 1px solid var(--border) !important;
  width: 260px !important;
  min-width: 260px !important;
  max-width: 260px !important;
  box-shadow: inset -1px 0 0 rgba(255,255,255,0.03);
  padding: 1rem 0.75rem 1rem;
}
section[data-testid="stSidebar"] * { color: var(--text) !important; }
section[data-testid="stSidebar"] [data-testid="stRadio"] { gap: .5rem; }
section[data-testid="stSidebar"] [data-testid="stRadio"] label {
  border-radius: 16px;
  padding: .8rem .88rem;
  border: 1px solid transparent;
  background: rgba(255,255,255,0.015);
  transition: all .34s cubic-bezier(0.16,1,0.3,1);
  margin: .14rem 0;
}
section[data-testid="stSidebar"] [data-testid="stRadio"] label:hover {
  background: rgba(255,255,255,0.04);
  border-color: rgba(255,255,255,0.08);
  transform: translateX(2px);
}
section[data-testid="stSidebar"] [data-testid="stRadio"] label[aria-checked="true"] {
  background: linear-gradient(135deg, rgba(41,151,255,0.16), rgba(255,255,255,0.04));
  border-color: rgba(41,151,255,0.28);
  box-shadow: inset 0 0 0 1px rgba(41,151,255,0.22);
}
section[data-testid="stSidebar"] [data-testid="stRadio"] label > div {
  display:flex; align-items:center; justify-content:space-between; width:100%;
}
section[data-testid="stSidebar"] [data-testid="stRadio"] input[type="radio"] {
  accent-color: var(--accent);
  transform: scale(1.08);
}
.app-shell {
  background: linear-gradient(180deg, rgba(17,17,18,0.96), rgba(8,9,10,0.98));
  border: 1px solid var(--border);
  border-radius: 32px;
  box-shadow: var(--glow);
  padding: 1.1rem 1.1rem 1.4rem;
}
.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: .35rem .35rem 1rem;
}
.greeting {
  font-size: clamp(1.8rem, 3vw, 2.5rem);
  font-weight: 700;
  letter-spacing: -0.06em;
  color: var(--text);
  font-family: 'Space Grotesk', sans-serif !important;
}
.topbar-actions {
  display: flex;
  align-items: center;
  gap: .7rem;
  flex-wrap: wrap;
}
.search-box {
  display: flex;
  align-items: center;
  gap: .7rem;
  min-width: 240px;
  padding: .72rem .9rem;
  border-radius: 16px;
  background: rgba(255,255,255,0.03);
  border: 1px solid var(--border);
  color: var(--muted);
  font-size: .9rem;
}
.chip {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: .7rem .95rem;
  border-radius: 999px;
  border: 1px solid rgba(255,255,255,0.08);
  background: rgba(255,255,255,0.03);
  color: var(--text);
  font-weight: 600;
  font-size: .8rem;
  transition: all .28s cubic-bezier(0.16,1,0.3,1);
}
.chip:hover {
  border-color: var(--border-strong);
  transform: translateY(-1px);
}
.chip.primary {
  background: linear-gradient(135deg, #2997ff, #7dd3fc);
  color: #06131c;
  border-color: transparent;
  box-shadow: 0 12px 28px rgba(41,151,255,0.22);
}
.hero-panel {
  position: relative;
  display: grid;
  grid-template-columns: 1.25fr .75fr;
  align-items: center;
  gap: 1.1rem;
  padding: 1.3rem 1.3rem 1.2rem;
  margin-top: .5rem;
  border-radius: 28px;
  background: linear-gradient(180deg, rgba(19,19,21,0.97), rgba(8,9,10,0.98));
  border: 1px solid rgba(255,255,255,0.08);
  overflow: hidden;
}
.hero-panel::before {
  content: "";
  position: absolute;
  inset: auto -60px -80px auto;
  width: 260px;
  height: 260px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(41,151,255,0.26), transparent 60%);
  filter: blur(12px);
}
.kicker {
  font-size: 10px;
  letter-spacing: .18em;
  text-transform: uppercase;
  color: var(--muted);
  font-weight: 700;
}
.hero-title {
  font-family: 'Space Grotesk', sans-serif !important;
  font-size: clamp(2.8rem, 5vw, 4.8rem);
  line-height: .94;
  letter-spacing: -.07em;
  margin: .8rem 0 .8rem;
  font-weight: 700;
}
.hero-sub {
  max-width: 580px;
  color: var(--muted-soft);
  line-height: 1.6;
  font-size: 1rem;
}
.hero-actions {
  display: flex;
  flex-wrap: wrap;
  gap: .7rem;
  margin-top: 1rem;
}
.hero-visual {
  position: relative;
  min-height: 250px;
  border-radius: 24px;
  background: linear-gradient(180deg, rgba(19,20,21,0.96), rgba(10,11,12,0.98));
  border: 1px solid rgba(255,255,255,0.08);
  overflow: hidden;
}
.hero-visual::before {
  content: "";
  position: absolute;
  width: 180px;
  height: 180px;
  border-radius: 50%;
  right: -18px; top: -18px;
  background: radial-gradient(circle at 35% 35%, rgba(255,255,255,0.9), rgba(125,211,252,0.7) 28%, rgba(41,151,255,0.4) 56%, rgba(41,151,255,0.08) 100%);
  filter: blur(12px);
}
.hero-visual::after {
  content: "";
  position: absolute;
  width: 170px;
  height: 170px;
  left: 16px; bottom: -20px;
  border-radius: 50%;
  background: radial-gradient(circle at 38% 30%, rgba(255,255,255,0.95), rgba(249,168,212,0.8) 26%, rgba(168,85,247,0.45) 58%, rgba(168,85,247,0.08) 100%);
  filter: blur(18px);
}
.inner-card {
  position: absolute;
  right: 1rem;
  bottom: 1rem;
  width: 72%;
  background: rgba(8,8,10,0.92);
  border: 1px solid rgba(255,255,255,0.08);
  padding: 1rem 1rem .9rem;
  border-radius: 22px;
  box-shadow: 0 22px 36px rgba(0,0,0,0.25);
}
.mini-header { display:flex; align-items:center; justify-content:space-between; margin-bottom: .8rem; }
.dot-row { display:flex; gap:6px; }
.dot-row span {
  display:block; width:10px; height:10px; border-radius:50%;
}
.mini-number {
  font-family: 'Space Grotesk', sans-serif !important;
  font-size: 2.2rem;
  font-weight: 700;
  letter-spacing: -0.06em;
}
.mini-bars {
  display:grid; grid-template-columns: repeat(8, 1fr); gap:6px; margin-top:.9rem;
}
.mini-bars span {
  display:block; height:10px; border-radius:999px; background: rgba(255,255,255,0.08);
}
.mini-bars span:nth-child(2n) { background: rgba(125,211,252,0.7); }
.mini-bars span:nth-child(3n) { background: rgba(255,255,255,0.2); }
.metric-row {
  display:grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap:1rem; margin-top: 1rem;
}
.metric-card {
  padding: 1.1rem 1rem;
  border-radius: 22px;
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.08);
}
.metric-label {
  font-size: 10px; letter-spacing: .16em; text-transform: uppercase; font-weight: 700; color: var(--muted);
}
.metric-value {
  font-family: 'Space Grotesk', sans-serif !important;
  font-size: 2rem; font-weight: 700; letter-spacing: -0.06em; margin-top: .5rem;
}
.metric-sub {
  margin-top: .25rem; color: var(--muted-soft); font-size: 12px;
}
.bento-grid {
  display:grid; grid-template-columns: 1.5fr 1fr 1fr; gap:1rem; margin-top:1.2rem;
}
.bento-card {
  position: relative;
  min-height: 180px;
  padding: 1rem 1rem 1.2rem;
  border-radius: 28px;
  border: 1px solid rgba(255,255,255,0.08);
  background: linear-gradient(180deg, rgba(18,18,20,0.96), rgba(12,12,13,0.98));
  overflow: hidden;
}
.bento-card.feature { background: linear-gradient(135deg, rgba(41,151,255,0.12), rgba(255,255,255,0.02)); }
.bento-card.titanium { background: linear-gradient(135deg, rgba(255,255,255,0.04), rgba(255,255,255,0.02)); }
.bento-card.screen { background: linear-gradient(135deg, rgba(99,102,241,0.08), rgba(255,255,255,0.02)); }
.bento-card.battery { background: linear-gradient(135deg, rgba(168,85,247,0.12), rgba(255,255,255,0.02)); }
.tag {
  display:inline-flex; align-items:center; padding:.45rem .72rem; border-radius:999px; background: rgba(255,255,255,0.04); border:1px solid rgba(255,255,255,0.08); font-size:10px; letter-spacing:.14em; text-transform:uppercase; font-weight:700; color:#dbeafe;
}
.bento-card h3 {
  font-family: 'Space Grotesk', sans-serif !important; font-size: clamp(1.25rem, 2vw, 1.8rem); letter-spacing: -.04em; margin-top: .8rem; margin-bottom: .1rem;
}
.bento-card p { color: var(--muted-soft); line-height:1.6; font-size: .94rem; }
.bento-card.feature .graph {
  position:absolute; left:1rem; right:1rem; bottom:1rem; height: 74px; border-radius:18px; background: linear-gradient(180deg, rgba(41,151,255,0.2), rgba(41,151,255,0.02)); border:1px solid rgba(255,255,255,0.06);
}
.bento-card.feature .graph::before {
  content: ""; position: absolute; inset: 18px 16px 16px 16px; border-radius: 12px; background: linear-gradient(90deg, rgba(255,255,255,0.18), rgba(41,151,255,0.5), rgba(255,255,255,0.18)); clip-path: polygon(0 70%, 14% 62%, 32% 68%, 42% 44%, 60% 52%, 74% 26%, 88% 34%, 100% 0, 100% 100%, 0 100%);
}
.schedule-board {
  margin-top: 1.3rem; padding: 1rem; border-radius: 30px; border:1px solid rgba(255,255,255,0.08); background: linear-gradient(180deg, rgba(18,18,20,0.96), rgba(12,12,13,0.98));
}
.schedule-head { display:flex; justify-content:space-between; align-items:flex-end; gap:1rem; margin-bottom:1rem; }
.schedule-title { font-size:10px; letter-spacing:.16em; text-transform:uppercase; color:var(--muted); font-weight:700; }
.schedule-name { font-family: 'Space Grotesk', sans-serif !important; font-size:1.8rem; letter-spacing:-.05em; margin-top:.35rem; }
.schedule-grid { display:grid; grid-template-columns:56px repeat(7, minmax(80px, 1fr)); gap:.7rem; min-height:310px; }
.time-col, .day-col { position:relative; border-radius:18px; background: rgba(255,255,255,0.02); border:1px solid rgba(255,255,255,0.06); }
.day-col { overflow:hidden; }
.time-col { display:flex; flex-direction:column; justify-content:space-between; padding:.75rem .45rem; color: var(--muted); font-size:10px; letter-spacing:.08em; }
.day-head { display:flex; align-items:center; justify-content:center; padding:.7rem .5rem; font-size:11px; letter-spacing:.12em; text-transform:uppercase; color:var(--muted); border-bottom:1px solid rgba(255,255,255,0.06); }
.day-col.active .day-head { background:#111214; color:var(--text); }
.day-canvas { position:relative; height:230px; margin:.7rem; border-radius:16px; background:linear-gradient(180deg, rgba(255,255,255,0.01), rgba(255,255,255,0.02)); }
.block { position:absolute; left:10px; right:10px; border-radius:14px; border:1px solid rgba(255,255,255,0.08); padding:.5rem .6rem; font-size:10px; line-height:1.3; box-shadow:0 12px 20px rgba(0,0,0,0.15); }
.block.sleep { background:#1f2c42; color:#d9ecff; }
.block.focus { background:#efe4ff; color:#3f2a63; }
.block.work { background:#fbe6a7; color:#5b3c06; }
.block.rest { background:#dff4db; color:#1c4d34; }
.block .label { font-weight: 700; }
@media (max-width: 980px) {
  .hero-panel { grid-template-columns: 1fr; }
  .bento-grid { grid-template-columns: 1fr; }
  .metric-row { grid-template-columns: 1fr; }
  .schedule-grid { grid-template-columns: 52px repeat(7, minmax(76px, 1fr)); }
}
@media (max-width: 760px) {
  .topbar { flex-direction: column; align-items: flex-start; }
  .topbar-actions { width: 100%; }
  .search-box { min-width: 0; flex: 1; }
  .hero-panel { padding: 1.05rem; }
  .hero-title { font-size: 2.8rem; }
  section[data-testid="stSidebar"] { width: 100% !important; min-width: 100% !important; max-width: 100% !important; }
}
</style>
       """,
       unsafe_allow_html=True,
   )


def page_header(eyebrow: str, title: str, subtitle: str) -> None:
    st.markdown(
        f"""
        <div class="sora-hero">
          <div class="eyebrow">{escape(eyebrow)}</div>
          <div class="title">{escape(title)}</div>
          <div class="subtitle">{escape(subtitle)}</div>
          <div class="pill-row">
            <span class="pill">Sleep Planning</span>
            <span class="pill">Recovery Focus</span>
            <span class="pill">Smart Scheduling</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_label(label: str) -> None:
    st.markdown(
        f'<div class="section-label"><hr><span>{escape(label)}</span><hr></div>',
        unsafe_allow_html=True,
    )


def metric_card(label: str, value: str, caption: str = "") -> None:
    caption_html = (
        f'<div style="font-size:11px;color:var(--success);margin-top:.35rem">{escape(caption)}</div>'
        if caption
        else ""
    )
    st.markdown(
        f"""
        <div class="metric-card">
          <div class="metric-value">{escape(value)}</div>
          <div class="metric-label">{escape(label)}</div>
          {caption_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def result_banner(title: str, body: str, success: bool = True) -> None:
    color = "#22C55E" if success else "#EF4444"
    st.markdown(
        f"""
        <div class="panel" style="border-left:4px solid {color}; margin-bottom:1rem">
          <div style="font-family:JetBrains Mono,monospace;font-size:12px;letter-spacing:.08em;color:{color}">{escape(title)}</div>
          <div style="color:var(--muted);font-size:.9rem;margin-top:.35rem">{escape(body)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def method_explanation_panel() -> None:
    steps = [
        (
            "01",
            "Representasi Kromosom",
            "Satu individu adalah satu kromosom jadwal harian berisi 48 gen. Setiap gen mewakili slot 30 menit.",
        ),
        (
            "02",
            "Alel Aktivitas",
            "Nilai gen memakai 5 alel: 0 tidur, 1 kerja, 2 nap, 3 santai, dan 4 kuliah.",
        ),
        (
            "03",
            "Populasi",
            "Populasi adalah kumpulan individu kandidat jadwal. Ukurannya dikendalikan oleh population_size.",
        ),
        (
            "04",
            "Crossover",
            "Single-point crossover menggabungkan bagian awal parent pertama dan bagian akhir parent kedua.",
        ),
        (
            "05",
            "Mutasi",
            "Mutasi mengganti gen non-wajib dengan tidur, nap, atau santai berdasarkan mutation_rate.",
        ),
        (
            "06",
            "Elitisme",
            "Individu terbaik dipertahankan agar solusi bagus tidak hilang saat pembentukan generasi baru.",
        ),
        (
            "07",
            "Repair Constraint",
            "Kandidat jadwal diperbaiki agar kerja, kuliah, transit, target tidur, dan batas nap tetap konsisten.",
        ),
        (
            "08",
            "Hill Climbing",
            "Solusi terbaik hasil GA diperbaiki lagi secara lokal dengan pencarian tetangga yang menaikkan fitness.",
        ),
    ]
    cards = "".join(
        (
            '<div class="method-card">'
            f'<div class="method-index">{escape(index)}</div>'
            f'<div class="method-title">{escape(title)}</div>'
            f'<div class="method-body">{escape(body)}</div>'
            "</div>"
        )
        for index, title, body in steps
    )
    st.markdown(f'<div class="method-grid">{cards}</div>', unsafe_allow_html=True)


def read_uploaded_csv(uploaded_file) -> pd.DataFrame:
    return pd.read_csv(BytesIO(uploaded_file.getvalue()))


def save_uploaded_csv(uploaded_file) -> str:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
        tmp.write(uploaded_file.getbuffer())
        return tmp.name


def validate_columns(df: pd.DataFrame, required_columns: list[str]) -> bool:
    missing = [column for column in required_columns if column not in df.columns]
    if missing:
        st.error(f"CSV wajib punya kolom: {', '.join(missing)}")
        return False
    return True


def validate_dataset_rows(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    records = []
    required_columns = required_weekly_columns(DAYS)
    missing_columns = [column for column in required_columns if column not in df.columns]
    if missing_columns:
        summary = {"valid_rows": 0, "invalid_rows": len(df), "issues": len(missing_columns)}
        return pd.DataFrame({"issue": [f"Kolom hilang: {', '.join(missing_columns)}"]}), summary

    for row_index, row in df.iterrows():
        subject = str(row.get("Nama", f"Baris {row_index + 1}"))
        for day in DAYS:
            try:
                work_slots = parse_slot_list(row[f"Kerja_{day}"])
                class_slots = parse_slot_list(row[f"Kuliah_{day}"])
            except ValueError as exc:
                records.append(
                    {
                        "subject": subject,
                        "day": day,
                        "status": "invalid_format",
                        "issue": str(exc),
                    }
                )
                continue

            overlap = sorted(set(work_slots) & set(class_slots))
            if overlap:
                records.append(
                    {
                        "subject": subject,
                        "day": day,
                        "status": "overlap",
                        "issue": f"Kerja dan kuliah bentrok pada slot {overlap}",
                    }
                )

    issue_df = pd.DataFrame(records)
    invalid_subjects = set(issue_df["subject"]) if not issue_df.empty else set()
    summary = {
        "valid_rows": len(df) - len(invalid_subjects),
        "invalid_rows": len(invalid_subjects),
        "issues": len(issue_df),
    }
    return issue_df, summary


def parameter_controls(prefix: str) -> dict:
    preset = st.selectbox(
        "Preset Optimasi",
        ["Fast", "Balanced", "Deep"],
        index=1,
        key=f"{prefix}_preset",
    )
    if preset == "Fast":
        population_size = 30
        mutation_rate = 0.08
        crossover_rate = 0.70
        hill_climbing_iterations = 10
    elif preset == "Deep":
        population_size = 120
        mutation_rate = 0.15
        crossover_rate = 0.90
        hill_climbing_iterations = 30
    else:
        population_size = DEFAULT_POPULATION_SIZE
        mutation_rate = DEFAULT_MUTATION_RATE
        crossover_rate = DEFAULT_CROSSOVER_RATE
        hill_climbing_iterations = 20

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        population_size = st.slider("Population Size", 10, 200, int(population_size), 10, key=f"{prefix}_pop")
    with c2:
        mutation_rate = st.slider("Mutation Rate", 0.01, 0.5, float(mutation_rate), 0.01, key=f"{prefix}_mut")
    with c3:
        crossover_rate = st.slider("Crossover Rate", 0.0, 1.0, float(crossover_rate), 0.05, key=f"{prefix}_cross")
    with c4:
        hill_climbing_iterations = st.slider("HC Iter", 0, 50, int(hill_climbing_iterations), 1, key=f"{prefix}_hc")
    return {
        "population_size": int(population_size),
        "mutation_rate": float(mutation_rate),
        "crossover_rate": float(crossover_rate),
        "hill_climbing_iterations": int(hill_climbing_iterations),
    }


def slot_to_clock(slot: int) -> str:
    total_minutes = slot * 30
    hour, minute = divmod(total_minutes, 60)
    return f"{hour:02d}:{minute:02d}"


def sleep_window_for_day(day_schedule: list[int]) -> tuple[int, int, float]:
    sleep_slots = [idx for idx, value in enumerate(day_schedule) if int(value) == 0]
    if not sleep_slots:
        return 0, 0, 0.0

    longest_start = sleep_slots[0]
    longest_end = sleep_slots[0]
    longest_len = 1
    current_start = sleep_slots[0]
    current_end = sleep_slots[0]

    for slot in sleep_slots[1:]:
        if slot == current_end + 1:
            current_end = slot
        else:
            current_len = current_end - current_start + 1
            if current_len > longest_len:
                longest_start = current_start
                longest_end = current_end
                longest_len = current_len
            current_start = slot
            current_end = slot

    current_len = current_end - current_start + 1
    if current_len > longest_len:
        longest_start = current_start
        longest_end = current_end
        longest_len = current_len

    return longest_start, longest_end, longest_len * 0.5


def sleep_focus_summary(weekly_schedule: list[list[int]]) -> None:
    day_names = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
    cols = st.columns(len(day_names))
    for col, day_name, schedule in zip(cols, day_names, weekly_schedule):
        start_slot, end_slot, hours = sleep_window_for_day(schedule)
        start_label = slot_to_clock(start_slot)
        end_label = slot_to_clock(end_slot + 1)
        with col:
            st.markdown(
                f"""
                <div class="panel" style="padding:.9rem; min-height:180px; background:linear-gradient(180deg, rgba(52,211,153,.10), rgba(255,255,255,.96)); border:1px solid rgba(16,185,129,.2); box-shadow: 0 12px 28px rgba(16,185,129,.08);">
                  <div style="font-family:'JetBrains Mono', monospace; font-size:10px; letter-spacing:.12em; color:#047857; text-transform:uppercase;">{escape(day_name)}</div>
                  <div style="font-family:'Space Grotesk', sans-serif; font-size:1.8rem; font-weight:800; color:#0f172a; margin-top:.5rem;">{hours:.1f}h</div>
                  <div style="color:#475569; margin-top:.2rem; font-size:.82rem;">Pola tidur</div>
                  <div style="margin-top:.8rem; font-size:.82rem; color:#0f172a; font-weight:600;">{start_label} - {end_label}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def weekly_timeline_grid(weekly_schedule: list[list[int]]) -> None:
    day_names = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
    activity = {
        0: ("sleep", "🌙", "Core Sleep", "Recovery"),
        1: ("work", "☕", "Barista Shift", "Sepakat"),
        2: ("nap", "⚡", "Power Nap", "Reset"),
        3: ("rest", "✨", "Recovery", "Open time"),
        4: ("class", "📝", "UPN Classes", "Academic"),
    }
    now = datetime.now().astimezone()
    active_day = now.weekday()
    now_minutes = now.hour * 60 + now.minute
    now_position = ((now_minutes - 360) / 1440) * 100
    now_position = max(0.0, min(100.0, now_position))

    day_headers = "".join(
        f'<div class="chronos-day-head {"active" if index == active_day else ""}">{day_name[:3]}</div>'
        for index, day_name in enumerate(day_names)
    )

    gutter = "".join(
        f'<span style="top:{(slot / 48) * 100:.2f}%">{slot_to_clock(slot)}</span>'
        for slot in [0, 6, 12, 18, 24, 30, 36, 42]
    )

    day_columns = ""
    for day_index, (day_name, schedule) in enumerate(zip(day_names, weekly_schedule)):
        event_blocks = ""
        start_idx = None
        current_value = None
        for idx, value in enumerate(schedule):
            value_int = int(value)
            if current_value is None:
                current_value = value_int
                start_idx = idx
                continue
            if value_int == current_value:
                continue
            end_idx = idx
            event_blocks += _build_event_block(day_name, current_value, start_idx, end_idx, activity)
            current_value = value_int
            start_idx = idx
        if current_value is not None:
            event_blocks += _build_event_block(day_name, current_value, start_idx, len(schedule), activity)
        day_columns += f'<div class="chronos-day-column">{event_blocks}</div>'

    st.markdown(
        f"""
        <div class="chronos-shell">
          <div class="chronos-topbar">
            <div>
              <div class="chronos-kicker">Chronos / Sleep & Activity Optimizer</div>
              <div class="chronos-heading">Weekly rhythm</div>
            </div>
            <div class="chronos-actions">
              <span class="chronos-action primary">+ Add Event</span>
              <span class="chronos-action">✦ AI Sync</span>
              <span>Today</span>
              <strong>Week</strong>
              <span>Month</span>
            </div>
          </div>
          <div class="chronos-range">
            <div>
              <div class="chronos-range-title">Sep 01 — Sep 07, 2026 ▾</div>
              <div class="chronos-range-meta">Sleep and activity blocks · 06:00 to 06:00 next day</div>
            </div>
            <div class="chronos-range-meta">● Live schedule</div>
          </div>
          <div class="chronos-scroll">
            <div class="chronos-board">
              <div class="chronos-day-heads"><div class="chronos-day-head">Time</div>{day_headers}</div>
              <div class="chronos-columns">
                <div class="chronos-gutter">{gutter}</div>
                {day_columns}
              </div>
            </div>
          </div>
          <div class="chronos-now" style="top:{now_position:.2f}%"></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _build_event_block(day_name: str, value: int, start_idx: int | None, end_idx: int | None, activity: dict[int, tuple[str, str, str, str]]) -> str:
    if start_idx is None or end_idx is None:
        return ""
    kind, icon, title, subtitle = activity.get(int(value), ("rest", "✨", "Open Time", "Scheduled"))
    start_minutes = max(0, int(start_idx) * 30)
    end_minutes = max(30, int(end_idx) * 30)
    cycle_start = 6 * 60
    start_offset = (start_minutes - cycle_start + 1440) % 1440
    end_offset = (end_minutes - cycle_start + 1440) % 1440
    top = max(0.0, (start_offset / 1440) * 100)
    height = max(6.0, ((end_offset - start_offset) / 1440) * 100)
    start_clock = slot_to_clock(start_idx)
    end_clock = slot_to_clock(end_idx)
    attachment = '<span class="chronos-event-attachment">Schedule_Draft.pdf</span>' if kind == "class" else ""
    return (
        f'<div class="chronos-event {kind}" title="{escape(day_name + " " + start_clock + " - " + end_clock)}" '
        f'style="top:{top:.2f}%; height:{height:.2f}%">'
        f'<div class="chronos-event-title">{icon} {title}</div>'
        f'<div class="chronos-event-meta">{subtitle}</div>'
        f'<div class="chronos-event-time">{start_clock} — {end_clock}</div>{attachment}</div>'
    )


def daily_quality_panel(daily_metrics: list[dict]) -> None:
    cards = ""
    for metric in daily_metrics:
        day = escape(str(metric.get("day", "-"))[:3].upper())
        status = metric.get("status")
        sleep = float(metric.get("sleep_hours") or 0)
        penalty = float(metric.get("penalty") or 0) + float(metric.get("regularity_penalty") or 0)
        label = (
            "GOOD"
            if status == "optimized" and sleep >= 7 and penalty == 0
            else ("CHECK" if status == "optimized" else "SKIP")
        )
        color = "#22C55E" if label == "GOOD" else ("#F59E0B" if label == "CHECK" else "#EF4444")
        fitness = metric.get("fitness")
        cards += (
            '<div class="quality-card">'
            f'<div class="quality-day"><span>{day}</span><span style="color:{color}">{label}</span></div>'
            f'<div class="quality-main">{sleep:.1f}h</div>'
            f'<div class="quality-row"><span>Fitness</span><strong>'
            f'{"-" if fitness is None else f"{float(fitness):.2f}"}</strong></div>'
            f'<div class="quality-row"><span>Fatigue</span><strong>'
            f'{float(metric.get("fatigue_end") or 0):.2f}</strong></div>'
            f'<div class="quality-row"><span>Penalti</span><strong style="color:{color}">{penalty:.2f}</strong></div>'
            '</div>'
        )
    st.markdown(f'<div class="quality-grid">{cards}</div>', unsafe_allow_html=True)


def penalty_breakdown(metrics: dict, title: str) -> None:
    dynamic_penalty = float(metrics.get("penalty") or 0)
    regularity_penalty = float(metrics.get("regularity_penalty") or 0)
    nap_sessions = float(metrics.get("nap_sessions") or 0)
    recovery = float(metrics.get("recovery") or 0)
    items = [
        ("Dynamic", dynamic_penalty),
        ("Regularitas", regularity_penalty),
        ("Total", dynamic_penalty + regularity_penalty),
        ("Nap", nap_sessions),
    ]
    cards = ""
    for label, value in items:
        color = "#22C55E" if value == 0 else ("#F59E0B" if value > -250 else "#EF4444")
        cards += (
            '<div class="panel">'
            f'<div class="penalty-label">{escape(label)}</div>'
            f'<div class="penalty-value" style="color:{color}">{value:.2f}</div>'
            '</div>'
        )
    st.markdown(
        f'<div class="panel" style="margin-bottom:.8rem"><div class="eyebrow">{escape(title)}</div>'
        f'<div style="color:var(--muted);margin-top:.35rem">Recovery reward: '
        f'<strong>{recovery:.3f}</strong></div></div><div class="penalty-grid">{cards}</div>',
        unsafe_allow_html=True,
    )


def operator_panel(parameters: dict, generations: int, hill_climbing_iterations: int = 20) -> None:
    items = [
        ("Population", str(parameters["population_size"])),
        ("Mutation", f"{parameters['mutation_rate']:.2f}"),
        ("Crossover", f"{parameters['crossover_rate']:.2f}"),
        ("Generations", str(generations)),
        ("Elitism", "20" if parameters["population_size"] > 20 else str(max(1, parameters["population_size"] // 5))),
        ("HC Iter", str(hill_climbing_iterations)),
    ]
    cards = "".join(
        (
            '<div class="operator-card">'
            f'<div class="operator-value">{escape(value)}</div>'
            f'<div class="operator-label">{escape(label)}</div>'
            "</div>"
        )
        for label, value in items
    )
    st.markdown(f'<div class="operator-grid">{cards}</div>', unsafe_allow_html=True)


def convergence_chart(history: list[dict], title: str = "Convergence Chart") -> None:
    if not history:
        return
    history_df = pd.DataFrame(history)
    section_label(title)
    if "day" in history_df.columns:
        selected_day = st.selectbox("Hari convergence", history_df["day"].drop_duplicates().tolist())
        history_df = history_df[history_df["day"] == selected_day]
    chart_df = history_df.set_index("generation")[["best_fitness", "mean_top10_fitness"]]
    st.line_chart(chart_df, use_container_width=True)
    with st.expander("Convergence Data"):
        st.dataframe(history_df, use_container_width=True, hide_index=True)


def chromosome_viewer(chromosome: list[int], title: str = "Chromosome Viewer") -> None:
    section_label(title)
    genes = "".join(f'<div class="gene slot-{int(value)}" title="slot {idx}">{int(value)}</div>' for idx, value in enumerate(chromosome))
    st.markdown(f'<div class="chromosome-strip">{genes}</div>', unsafe_allow_html=True)


def baseline_schedule_grid(schedules: dict[str, list[int]]) -> None:
    section_label("Baseline Schedule Visualization")
    method_labels = {"sora": "SORA", "greedy": "Greedy", "fixed": "Fixed"}
    rows = ""
    for key in ["sora", "greedy", "fixed"]:
        schedule = schedules[key]
        rows += f'<div class="method-row"><div class="method-name">{method_labels[key]}</div>'
        rows += "".join(
            f'<div class="slot slot-{int(value)}" title="{method_labels[key]} slot {idx}: {int(value)}"></div>'
            for idx, value in enumerate(schedule)
        )
        rows += "</div>"
    st.markdown(f'<div class="timeline-panel">{rows}</div>', unsafe_allow_html=True)


def slot_time_label(slot: int) -> str:
    start_minutes = slot * 30
    end_minutes = (slot + 1) * 30
    start_hour, start_minute = divmod(start_minutes, 60)
    end_hour, end_minute = divmod(end_minutes, 60)
    return f"{start_hour:02d}:{start_minute:02d}-{end_hour % 24:02d}:{end_minute:02d}"


def build_weekly_schedule_export(weekly_schedule: list[list[int]]) -> pd.DataFrame:
    activity_labels = {0: "Tidur", 1: "Kerja", 2: "Nap", 3: "Santai", 4: "Kuliah"}
    rows = []
    for day, schedule in zip(DAYS, weekly_schedule):
        for slot, value in enumerate(schedule):
            rows.append(
                {
                    "day": day,
                    "slot": slot,
                    "time": slot_time_label(slot),
                    "activity_code": int(value),
                    "activity_label": activity_labels.get(int(value), "Unknown"),
                }
            )
    return pd.DataFrame(rows)


def premium_results_dashboard(
    schedule: list[list[int]],
    metrics: list[dict],
    total_sleep: float,
    avg_sleep: float,
    optimized_days: int,
    nap_sessions: int,
    target_name: str,
) -> None:
    day_names = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
    sleep_status = "Sempurna" if 7 <= avg_sleep <= 8.5 else ("Kurang" if avg_sleep < 7 else "Berlebih")
    sleep_color = "#10b981" if 7 <= avg_sleep <= 8.5 else ("#ef4444" if avg_sleep < 7 else "#f59e0b")
    
    html_content = f"""
    <div style="background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%); border:2px solid #e2e8f0; border-radius:20px; padding:2rem; box-shadow: 0 20px 50px rgba(15,23,42,.08); margin-bottom:2rem;">
      <!-- Header -->
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1.5rem; border-bottom:1px solid #e2e8f0; padding-bottom:1rem;">
        <div>
          <div style="font-size:14px; letter-spacing:.1em; color:#64748b; text-transform:uppercase; font-weight:700;">Jadwal Mingguan Optimal</div>
          <div style="font-size:24px; font-weight:800; color:#0f172a; margin-top:.35rem;">{escape(target_name)}</div>
        </div>
        <div style="background:{sleep_color}; color:white; padding:.6rem 1.2rem; border-radius:999px; font-weight:700; font-size:13px;">
          Status: {sleep_status}
        </div>
      </div>
      
      <!-- Metrics Row -->
      <div style="display:grid; grid-template-columns:repeat(3, 1fr); gap:1rem; margin-bottom:1.5rem;">
        <div style="background:linear-gradient(135deg, #e0f2fe 0%, #e0f2fe 100%); padding:1.2rem; border-radius:16px; border:1px solid #bae6fd;">
          <div style="font-size:12px; color:#0369a1; font-weight:700; text-transform:uppercase; letter-spacing:.08em;">Rata-rata Tidur</div>
          <div style="font-size:2.2rem; font-weight:800; color:#0c4a6e; margin-top:.5rem;">{avg_sleep:.1f}h</div>
          <div style="font-size:12px; color:#0369a1; margin-top:.35rem;">Target: 7-8 jam</div>
        </div>
        
        <div style="background:linear-gradient(135deg, #dbeafe 0%, #dbeafe 100%); padding:1.2rem; border-radius:16px; border:1px solid #bfdbfe;">
          <div style="font-size:12px; color:#1e40af; font-weight:700; text-transform:uppercase; letter-spacing:.08em;">Hari Aman</div>
          <div style="font-size:2.2rem; font-weight:800; color:#1e3a8a; margin-top:.5rem;">{optimized_days}/7</div>
          <div style="font-size:12px; color:#1e40af; margin-top:.35rem;">Jadwal teroptimasi</div>
        </div>
        
        <div style="background:linear-gradient(135deg, #fae8ff 0%, #fae8ff 100%); padding:1.2rem; border-radius:16px; border:1px solid #e9d5ff;">
          <div style="font-size:12px; color:#7e22ce; font-weight:700; text-transform:uppercase; letter-spacing:.08em;">Nap/Istirahat</div>
          <div style="font-size:2.2rem; font-weight:800; color:#5b21b6; margin-top:.5rem;">{nap_sessions}x</div>
          <div style="font-size:12px; color:#7e22ce; margin-top:.35rem;">Per minggu</div>
        </div>
      </div>
      
      <!-- Sleep Window Summary -->
      <div style="background:#f1f5f9; padding:1.2rem; border-radius:16px; border:1px solid #cbd5e1;">
        <div style="font-size:12px; color:#475569; font-weight:700; text-transform:uppercase; letter-spacing:.08em; margin-bottom:.75rem;">Jam Tidur Harian</div>
        <div style="display:grid; grid-template-columns:repeat(7, 1fr); gap:.5rem;">
    """
    
    for day_name, day_schedule in zip(day_names, schedule):
        start_slot, end_slot, hours = sleep_window_for_day(day_schedule)
        start_label = slot_to_clock(start_slot)
        end_label = slot_to_clock(end_slot + 1)
        html_content += f"""
          <div style="text-align:center; padding:.6rem; background:white; border-radius:12px; border:1px solid #e2e8f0;">
            <div style="font-size:11px; color:#64748b; font-weight:700; margin-bottom:.35rem;">{day_name}</div>
            <div style="font-size:13px; color:#0f172a; font-weight:800;">{hours:.1f}h</div>
            <div style="font-size:10px; color:#64748b; margin-top:.25rem;">{start_label} - {end_label}</div>
          </div>
        """
    
    if avg_sleep < 7:
        insight_text = (
            "Rata-rata tidur Anda masih di bawah target. Pertahankan jam tidur yang konsisten dan usahakan 30–60 menit lebih lama pada malam berikutnya agar energi tetap stabil."
        )
    elif avg_sleep > 8.5:
        insight_text = (
            "Polanya sudah cukup panjang, tetapi tidur yang berlebih dapat menurunkan rasa segar pada hari kerja. Coba jadikan porsi tidur lebih konsisten dan sesuai kebutuhan."
        )
    else:
        insight_text = (
            "Pola tidur Anda sudah berada pada zona yang sehat. Lanjutkan konsistensi ini untuk menjaga fokus, stamina, dan rasa segar sepanjang minggu."
        )

    html_content += f"""
        </div>
      </div>
      
      <!-- Insight -->
      <div style="background:linear-gradient(135deg, #f0fdf4 0%, #f0fdf4 100%); padding:1.2rem; border-radius:16px; border:1px solid #bbf7d0; margin-top:1rem;">
        <div style="display:flex; gap:.75rem;">
          <div style="font-size:20px;">💡</div>
          <div>
            <div style="font-weight:700; color:#15803d; margin-bottom:.35rem;">Rekomendasi</div>
            <div style="font-size:13px; color:#166534; line-height:1.5;">
              {insight_text}
            </div>
          </div>
        </div>
      </div>
    </div>
    """
    
    # Streamlit treats deeply indented HTML lines as Markdown code blocks.
    normalized_html = "\n".join(line.strip() for line in html_content.splitlines())
    st.markdown(normalized_html, unsafe_allow_html=True)


def workflow_guide_panel() -> None:
    st.markdown(
        """
        <div class="panel" style="margin-bottom:1rem; background:linear-gradient(180deg, rgba(255,255,255,0.94), rgba(248,250,252,0.92));">
          <div class="eyebrow">Quick Start</div>
          <div style="color:#475569; margin-top:.5rem; line-height:1.6">
            1. Upload file jadwal Anda.<br>
            2. Pilih subjek yang ingin dipetakan.<br>
            3. Klik <strong>Buat Jadwal Optimal</strong> dan lihat rekomendasi jam tidur yang lebih sehat.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def wizard_steps(active_step: int) -> None:
    labels = ["Profiling", "Magic Processing", "Dashboard"]
    cols = st.columns(3)
    for index, (label, col) in enumerate(zip(labels, cols, strict=True)):
        with col:
            variant = "active" if index == active_step else ("done" if index < active_step else "idle")
            st.markdown(
                f"""
                <div style="padding:.7rem .8rem; border-radius:12px; border:1px solid rgba(148,163,184,.18); background:{'#eef2ff' if variant=='active' else ('#f8fafc' if variant=='idle' else '#ecfdf5')}; color:{'#312e81' if variant=='active' else ('#475569' if variant=='idle' else '#065f46')}; font-weight:700; text-align:center; font-size:.82rem; margin-bottom:.5rem;">
                  {index + 1}. {label}
                </div>
                """,
                unsafe_allow_html=True,
            )


def weekly_page() -> None:
    page_header(
        "01 / Weekly Optimization",
        "Optimasi Mingguan",
        "Buat jadwal yang lebih sehat, seimbang, dan mudah dijalani setiap hari.",
    )
    wizard_steps(0)
    workflow_guide_panel()

    top_row = st.columns([5, 1])
    with top_row[0]:
        upload = st.file_uploader("Upload file jadwal", type=["csv"], key="weekly_upload")
    with top_row[1]:
        dev_mode = st.session_state.get("developer_mode", False)

    target_name = st.text_input("Nama Subjek", value="Subjek_041")

    with st.expander("Pengaturan optimasi"):
        parameters = parameter_controls("weekly")

    if dev_mode:
        with st.expander("Dapur mesin"):
            method_explanation_panel()

    run = st.button("Buat Jadwal Optimal", type="primary", use_container_width=True)

    if not run:
        st.info("Upload CSV, pilih subjek, lalu jalankan optimasi.")
        return
    if upload is None:
        st.error("Upload CSV terlebih dahulu.")
        return

    preview = read_uploaded_csv(upload)
    if not validate_columns(preview, required_weekly_columns(DAYS)):
        return
    st.success(f"Dataset siap diproses: {preview.shape[0]} baris, {preview.shape[1]} kolom.")
    st.caption("Format yang dibutuhkan: Nama, Kerja_Senin, Kuliah_Senin, ..., Kerja_Minggu, Kuliah_Minggu.")
    with st.expander("Preview dataset", expanded=True):
        st.dataframe(preview.head(10), use_container_width=True)
    dataset_path = save_uploaded_csv(upload)

    wizard_steps(1)
    status_messages = [
        "Menghitung ritme sirkadian...",
        "Menyusun jam tidur optimal...",
        "Mencegah titik kelelahan...",
    ]
    status_index = 0
    processing = st.container()
    with processing:
        st.markdown(
            """
            <div class="panel" style="margin:1rem 0; background:linear-gradient(180deg, rgba(255,255,255,0.97), rgba(239,246,255,0.96)); border:1px solid rgba(99,102,241,.15);">
              <div style="display:flex; align-items:center; gap:.75rem;">
                <div class="spinner" style="width:18px; height:18px; border-radius:50%; border:2px solid rgba(99,102,241,.18); border-top:2px solid #4f46e5; animation:spin 1s linear infinite;"></div>
                <div style="color:#334155; font-weight:600;">Menghitung ritme sirkadian...</div>
              </div>
            </div>
            <style>
            @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
            </style>
            """,
            unsafe_allow_html=True,
        )
    with st.spinner(status_messages[status_index]):
        try:
            schedule, metrics, convergence_history = run_weekly_optimization_with_history(
                dataset_path,
                parameters,
                target_name,
            )
        except ValueError as exc:
            result_banner("Data tidak valid", str(exc), success=False)
            return

    if schedule is None:
        result_banner("Subjek tidak ditemukan", target_name, success=False)
        return

    metrics_df = pd.DataFrame(metrics)
    schedule_export_df = build_weekly_schedule_export(schedule)
    optimized_days = int((metrics_df["status"] == "optimized").sum()) if not metrics_df.empty else 0
    total_sleep = sum(row.count(0) for row in schedule) / 2
    avg_sleep = total_sleep / 7
    nap_sessions = sum(
        sum(1 for idx in range(48) if row[idx] == 2 and (idx == 0 or row[idx - 1] != 2))
        for row in schedule
    )

    wizard_steps(2)
    premium_results_dashboard(
        schedule,
        metrics,
        total_sleep,
        avg_sleep,
        optimized_days,
        nap_sessions,
        target_name,
    )

    if dev_mode:
        section_label("Dapur Mesin")
        operator_panel(
            parameters,
            generations=200,
            hill_climbing_iterations=parameters.get("hill_climbing_iterations", 20),
        )
        convergence_chart(convergence_history)
        chromosome_viewer(schedule[0], "Chromosome Viewer: Senin")
    section_label("Jam Tidur")
    sleep_focus_summary(schedule)
    section_label("Timeline")
    weekly_timeline_grid(schedule)
    section_label("Daily Quality Panel")
    daily_quality_panel(metrics)
    optimized = [item for item in metrics if item.get("status") == "optimized"]
    if optimized:
        focus = min(
            optimized,
            key=lambda item: (
                float(item.get("penalty") or 0) + float(item.get("regularity_penalty") or 0),
                float(item.get("fitness") or 0),
            ),
        )
        section_label(f"Penalty Breakdown: {focus['day']}")
        penalty_breakdown(focus, f"Hari paling perlu dicek: {focus['day']}")

    section_label("Export Result")
    export_col1, export_col2 = st.columns(2)
    with export_col1:
        st.download_button(
            "Download Weekly Schedule CSV",
            schedule_export_df.to_csv(index=False),
            f"sora_weekly_schedule_{target_name}.csv",
            "text/csv",
            use_container_width=True,
        )
    with export_col2:
        st.download_button(
            "Download Weekly Metrics CSV",
            metrics_df.to_csv(index=False),
            f"sora_weekly_metrics_{target_name}.csv",
            "text/csv",
            use_container_width=True,
        )

    with st.expander("Detail Angka"):
        st.dataframe(pd.DataFrame(schedule, index=DAYS), use_container_width=True)
        st.dataframe(schedule_export_df, use_container_width=True)
        st.dataframe(metrics_df, use_container_width=True)


def baseline_page() -> None:
    page_header(
        "02 / Baseline Comparison",
        "Perbandingan Baseline",
        "Membandingkan SORA Academic dengan Greedy dan Fixed Schedule pada hari Rabu.",
    )
    upload = st.file_uploader("Upload dataset CSV", type=["csv"], key="baseline_upload")
    if upload is None:
        st.info("Upload CSV untuk memilih subjek.")
        return

    preview = read_uploaded_csv(upload)
    if not validate_columns(preview, ["Nama", "Kerja_Rabu", "Kuliah_Rabu"]):
        return
    selected_name = st.selectbox("Subjek", preview["Nama"].astype(str).tolist())
    with st.expander("Parameter Genetic Algorithm"):
        parameters = parameter_controls("baseline")
    with st.expander("Penjelasan Metode"):
        method_explanation_panel()
    run = st.button("Jalankan Baseline Comparison", type="primary", use_container_width=True)
    if not run:
        return

    row = preview[preview["Nama"].astype(str) == str(selected_name)].iloc[0]
    with st.spinner("Menghitung baseline..."):
        try:
            details = run_baseline_comparison_with_details(row, parameters)
        except ValueError as exc:
            result_banner("Data tidak valid", str(exc), success=False)
            return

    result = details["metrics"]
    schedules = details["schedules"]
    convergence_history = details["convergence"]
    sora_fit = result["sora"]["fitness"]
    greedy_fit = result["greedy"]["fitness"]
    fixed_fit = result["fixed"]["fitness"]
    winner = "SORA" if sora_fit > max(greedy_fit, fixed_fit) else "Baseline"
    result_df = pd.DataFrame(result).T
    result_banner("Perbandingan selesai", f"Winner: {winner} - Subjek: {selected_name}")

    c1, c2, c3 = st.columns(3)
    with c1:
        metric_card("SORA Fitness", f"{sora_fit:.2f}", "lebih tinggi lebih baik")
    with c2:
        metric_card("Greedy Fitness", f"{greedy_fit:.2f}", "baseline")
    with c3:
        metric_card("Fixed Fitness", f"{fixed_fit:.2f}", "baseline")

    section_label("Operator Panel")
    operator_panel(
        parameters,
        generations=150,
        hill_climbing_iterations=parameters.get("hill_climbing_iterations", 20),
    )
    convergence_chart(convergence_history, "SORA Convergence")
    chromosome_viewer(schedules["sora"], "Chromosome Viewer: SORA")
    baseline_schedule_grid(schedules)
    section_label("Penalty Breakdown")
    cols = st.columns(3)
    for col, key, label in zip(cols, ["sora", "greedy", "fixed"], ["SORA", "Greedy", "Fixed"]):
        with col:
            penalty_breakdown(result[key], label)

    section_label("Export Result")
    st.download_button(
        "Download Baseline Comparison CSV",
        result_df.to_csv(index=True, index_label="method"),
        f"sora_baseline_comparison_{selected_name}.csv",
        "text/csv",
        use_container_width=True,
    )

    with st.expander("Tabel Metrik"):
        st.dataframe(result_df, use_container_width=True)


def calibration_page() -> None:
    page_header(
        "03 / Calibration",
        "Kalibrasi Parameter",
        "Mencari kombinasi population_size, mutation_rate, dan crossover_rate terbaik.",
    )
    upload = st.file_uploader("Upload dataset kalibrasi CSV", type=["csv"], key="calibration_upload")
    with st.expander("Grid Parameter"):
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            population_options = st.multiselect("Population Size", [10, 20, 50, 100], default=[50, 100])
        with col2:
            mutation_options = st.multiselect("Mutation Rate", [0.01, 0.05, 0.10, 0.20], default=[0.05, 0.10])
        with col3:
            crossover_options = st.multiselect("Crossover Rate", [0.70, 0.80, 0.90], default=[0.80])
        with col4:
            generations = st.slider("Generations", 2, 150, 30, 1, key="calibration_generations")

    run = st.button("Jalankan Kalibrasi", type="primary", use_container_width=True)
    if not run:
        st.info("Upload dataset kalibrasi, pilih grid, lalu jalankan kalibrasi.")
        return
    if upload is None:
        st.error("Upload CSV kalibrasi terlebih dahulu.")
        return
    if not population_options or not mutation_options or not crossover_options:
        st.error("Setiap grid parameter harus berisi minimal satu nilai.")
        return

    preview = read_uploaded_csv(upload)
    required_columns = ["Nama"] + [column for day in ["Senin", "Rabu", "Sabtu"] for column in (f"Kerja_{day}", f"Kuliah_{day}")]
    if not validate_columns(preview, required_columns):
        return

    dataset_path = save_uploaded_csv(upload)
    parameter_grid = {
        "population_size": [int(value) for value in population_options],
        "mutation_rate": [float(value) for value in mutation_options],
        "crossover_rate": [float(value) for value in crossover_options],
    }
    output_path = ROOT.parent / "results" / "best_params_academic.json"

    with st.spinner("Menjalankan grid search akademik..."):
        try:
            best_params, result_df = run_parameter_grid_search(
                dataset_path=dataset_path,
                output_file=output_path,
                parameter_grid=parameter_grid,
                generations=generations,
            )
        except ValueError as exc:
            result_banner("Kalibrasi gagal", str(exc), success=False)
            return

    if best_params is None:
        result_banner("Kalibrasi tidak menghasilkan parameter", "Semua kombinasi gagal dievaluasi.", success=False)
        return

    result_banner("Kalibrasi selesai", f"Best parameters disimpan ke {output_path}")
    c1, c2, c3 = st.columns(3)
    with c1:
        metric_card("Population", str(best_params["population_size"]))
    with c2:
        metric_card("Mutation", f"{best_params['mutation_rate']:.2f}")
    with c3:
        metric_card("Crossover", f"{best_params['crossover_rate']:.2f}")

    section_label("Calibration Results")
    st.dataframe(result_df.sort_values("average_fitness", ascending=False), use_container_width=True, hide_index=True)
    st.download_button(
        "Download Calibration Results CSV",
        result_df.to_csv(index=False),
        "sora_academic_calibration_results.csv",
        "text/csv",
        use_container_width=True,
    )


def multi_subject_page() -> None:
    page_header(
        "04 / Multi-Subject",
        "Eksperimen Multi-Subjek",
        "Menjalankan baseline comparison pada banyak subjek untuk ringkasan agregat.",
    )
    upload = st.file_uploader("Upload dataset CSV", type=["csv"], key="multi_subject_upload")
    if upload is None:
        st.info("Upload CSV untuk menjalankan eksperimen multi-subjek.")
        return

    preview = read_uploaded_csv(upload)
    if preview.empty:
        st.error("CSV tidak berisi data subjek.")
        return
    if not validate_columns(preview, ["Nama", "Kerja_Rabu", "Kuliah_Rabu"]):
        return

    max_subjects = len(preview)
    col1, col2 = st.columns([2, 1])
    with col1:
        sample_size = st.slider("Jumlah Subjek", 1, max_subjects, min(5, max_subjects), key="multi_subject_sample")
    with col2:
        metric_card("Sampel", f"{sample_size}/{max_subjects}", "subjek")

    with st.expander("Parameter Genetic Algorithm"):
        parameters = parameter_controls("multi_subject")

    run = st.button("Jalankan Multi-Subject", type="primary", use_container_width=True)
    if not run:
        return

    with st.spinner("Menjalankan eksperimen multi-subjek..."):
        result_df, skipped_df = run_multi_subject_comparison_with_audit(preview.head(sample_size), parameters)
        summary_df = summarize_multi_subject_results(result_df)

    if result_df.empty:
        result_banner("Eksperimen gagal", "Tidak ada subjek berhasil diuji.", success=False)
        return

    sora_fit_mean = result_df["sora_fit"].mean()
    greedy_fit_mean = result_df["greedy_fit"].mean()
    fixed_fatigue_mean = result_df["fixed_fatigue"].mean()
    sora_fatigue_mean = result_df["sora_fatigue"].mean()
    improvement = ((sora_fit_mean - greedy_fit_mean) / abs(greedy_fit_mean) * 100) if greedy_fit_mean else 0
    fatigue_reduction = ((fixed_fatigue_mean - sora_fatigue_mean) / fixed_fatigue_mean * 100) if fixed_fatigue_mean else 0

    result_banner("Eksperimen selesai", f"{len(result_df)} subjek berhasil diuji.")
    if not skipped_df.empty:
        st.warning(f"{len(skipped_df)} subjek dilewati. Lihat detail statistik untuk alasannya.")
    c1, c2, c3 = st.columns(3)
    with c1:
        metric_card("Vs Greedy", f"{improvement:+.1f}%", "fitness mean")
    with c2:
        metric_card("Vs Fixed", f"{fatigue_reduction:+.1f}%", "fatigue turun")
    with c3:
        metric_card("Avg Sleep", f"{result_df['sora_sleep'].mean():.2f}h", "SORA")

    section_label("Aggregate Chart")
    chart_df = pd.DataFrame(
        {
            "Fitness": {
                "SORA": result_df["sora_fit"].mean(),
                "Greedy": result_df["greedy_fit"].mean(),
                "Fixed": result_df["fixed_fit"].mean(),
            },
            "Fatigue": {
                "SORA": result_df["sora_fatigue"].mean(),
                "Greedy": result_df["greedy_fatigue"].mean(),
                "Fixed": result_df["fixed_fatigue"].mean(),
            },
            "Sleep": {
                "SORA": result_df["sora_sleep"].mean(),
                "Greedy": result_df["greedy_sleep"].mean(),
                "Fixed": result_df["fixed_sleep"].mean(),
            },
        }
    )
    st.bar_chart(chart_df, use_container_width=True)

    section_label("Export Result")
    col_export1, col_export2 = st.columns(2)
    with col_export1:
        st.download_button(
            "Download Multi-Subject CSV",
            result_df.to_csv(index=False),
            f"sora_multi_subject_{len(result_df)}.csv",
            "text/csv",
            use_container_width=True,
        )
    with col_export2:
        st.download_button(
            "Download Summary CSV",
            summary_df.to_csv(index=False),
            "sora_multi_subject_summary.csv",
            "text/csv",
            use_container_width=True,
        )

    with st.expander("Detail Statistik"):
        st.dataframe(summary_df, use_container_width=True, hide_index=True)
        st.dataframe(result_df, use_container_width=True, hide_index=True)
        if not skipped_df.empty:
            st.dataframe(skipped_df, use_container_width=True, hide_index=True)


def dataset_preview_page() -> None:
    page_header(
        "Dataset Preview",
        "Validasi Dataset",
        "Memeriksa struktur CSV sebelum dijalankan ke backend akademik SORA.",
    )
    upload = st.file_uploader("Upload dataset CSV", type=["csv"], key="dataset_preview_upload")
    if upload is None:
        st.info("Upload CSV untuk melihat status dataset.")
        return

    try:
        df = read_uploaded_csv(upload)
    except Exception as exc:  # noqa: BLE001 - user-facing boundary, show friendly message
        result_banner("CSV gagal dibaca", str(exc), success=False)
        return

    issue_df, summary = validate_dataset_rows(df)
    required_columns = required_weekly_columns(DAYS)
    missing_columns = [column for column in required_columns if column not in df.columns]
    status_ok = not missing_columns and summary["issues"] == 0

    result_banner(
        "Dataset valid" if status_ok else "Dataset perlu diperbaiki",
        "Semua kolom dan slot sudah sesuai." if status_ok else "Ada kolom hilang, format slot salah, atau bentrok jadwal.",
        success=status_ok,
    )

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        metric_card("Total Subjek", str(len(df)), "baris CSV")
    with c2:
        metric_card("Subjek Valid", str(summary["valid_rows"]), "siap diproses")
    with c3:
        metric_card("Subjek Bermasalah", str(summary["invalid_rows"]), "perlu cek")
    with c4:
        metric_card("Total Issue", str(summary["issues"] + len(missing_columns)), "temuan")

    section_label("Struktur Kolom")
    column_status = pd.DataFrame(
        {
            "column": required_columns,
            "status": ["OK" if column in df.columns else "MISSING" for column in required_columns],
        }
    )
    st.dataframe(column_status, use_container_width=True, hide_index=True)

    section_label("Preview Data")
    st.dataframe(df.head(20), use_container_width=True)

    section_label("Issue Detail")
    if issue_df.empty and not missing_columns:
        st.markdown(
            '<div class="panel"><span class="health-ok">Tidak ada masalah format slot atau overlap.</span></div>',
            unsafe_allow_html=True,
        )
    else:
        if missing_columns:
            st.error(f"Kolom hilang: {', '.join(missing_columns)}")
        if not issue_df.empty:
            st.dataframe(issue_df, use_container_width=True, hide_index=True)


def home_page() -> None:
    st.markdown(
        """
        <div class="app-shell">
          <div class="topbar">
            <div class="greeting">Optimize your rhythm, Baretta</div>
            <div class="topbar-actions">
              <div class="search-box">Search schedule, sleep, focus</div>
              <div class="chip">Alerts</div>
              <div class="chip">Settings</div>
              <div class="chip primary">+ Add Event</div>
            </div>
          </div>

          <div class="hero-panel">
            <div class="hero-copy">
              <div class="kicker">Chronos / Sleep & Activity Optimizer</div>
              <div class="hero-title">Build a calmer week.</div>
              <div class="hero-sub">
                Protect recovery, reduce overload, and keep your rhythm stable with a weekly system designed around sleep quality and energy flow.
              </div>
              <div class="hero-actions">
                <div class="chip primary">Open schedule</div>
                <div class="chip">AI Sync</div>
                <div class="chip">Week</div>
              </div>
            </div>
            <div class="hero-visual">
              <div class="inner-card">
                <div class="mini-header">
                  <div class="dot-row"><span style="background:#ff5f57"></span><span style="background:#ffbd2e"></span><span style="background:#28c840"></span></div>
                  <div style="font-size:10px; letter-spacing:.16em; text-transform:uppercase; color:#a1a1a6;">sleep</div>
                </div>
                <div class="mini-number">7.8h</div>
                <div class="mini-bars">
                  <span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span>
                </div>
              </div>
            </div>
          </div>

          <div class="metric-row">
            <div class="metric-card">
              <div class="metric-label">Avg sleep</div>
              <div class="metric-value">7.8h</div>
              <div class="metric-sub">Within target range</div>
            </div>
            <div class="metric-card">
              <div class="metric-label">Consistency</div>
              <div class="metric-value">92%</div>
              <div class="metric-sub">Stable routine</div>
            </div>
            <div class="metric-card">
              <div class="metric-label">Recovery</div>
              <div class="metric-value">84%</div>
              <div class="metric-sub">Energy preserved</div>
            </div>
          </div>

          <div class="bento-grid">
            <div class="bento-card feature">
              <div class="tag">Neural engine</div>
              <h3>Deep rhythm optimization</h3>
              <p>Balance sleep depth, work load, and recovery windows with a calmer weekly pattern.</p>
              <div class="graph"></div>
            </div>
            <div class="bento-card titanium">
              <div class="tag">Material</div>
              <h3>Calm structure</h3>
              <p>Neutral surfaces, soft contrast, and stable spacing for mental clarity.</p>
            </div>
            <div class="bento-card screen">
              <div class="tag">Display</div>
              <h3>Precision view</h3>
              <p>Readable timeline and focus-aware blocks across the full week.</p>
            </div>
            <div class="bento-card battery" style="grid-column: span 2;">
              <div class="tag">Recovery</div>
              <h3>Sustainable energy</h3>
              <p>Higher-quality rest and fewer overload spikes across the week.</p>
            </div>
          </div>

          <div class="schedule-board">
            <div class="schedule-head">
              <div>
                <div class="schedule-title">Weekly rhythm</div>
                <div class="schedule-name">This week</div>
              </div>
              <div class="chip">Live view</div>
            </div>
            <div class="schedule-grid">
              <div class="time-col">
                <span>06:00</span>
                <span>12:00</span>
                <span>18:00</span>
                <span>00:00</span>
                <span>06:00</span>
              </div>
              <div class="day-col active">
                <div class="day-head">Mon</div>
                <div class="day-canvas">
                  <div class="block sleep" style="top: 8%; height: 38%;"><div class="label">Sleep</div>23:00 ? 06:00</div>
                  <div class="block work" style="top: 52%; height: 18%;"><div class="label">Focus</div>08:00 ? 10:00</div>
                </div>
              </div>
              <div class="day-col">
                <div class="day-head">Tue</div>
                <div class="day-canvas">
                  <div class="block sleep" style="top: 10%; height: 30%;"><div class="label">Sleep</div>23:30 ? 06:00</div>
                  <div class="block focus" style="top: 48%; height: 20%;"><div class="label">Study</div>10:00 ? 12:00</div>
                </div>
              </div>
              <div class="day-col">
                <div class="day-head">Wed</div>
                <div class="day-canvas">
                  <div class="block rest" style="top: 32%; height: 20%;"><div class="label">Reset</div>14:00 ? 16:00</div>
                  <div class="block work" style="top: 60%; height: 18%;"><div class="label">Shift</div>17:00 ? 19:00</div>
                </div>
              </div>
              <div class="day-col">
                <div class="day-head">Thu</div>
                <div class="day-canvas">
                  <div class="block sleep" style="top: 16%; height: 34%;"><div class="label">Sleep</div>00:00 ? 06:00</div>
                  <div class="block focus" style="top: 54%; height: 16%;"><div class="label">Deep work</div>09:00 ? 11:00</div>
                </div>
              </div>
              <div class="day-col">
                <div class="day-head">Fri</div>
                <div class="day-canvas">
                  <div class="block work" style="top: 16%; height: 22%;"><div class="label">Work</div>08:00 ? 10:00</div>
                  <div class="block rest" style="top: 52%; height: 18%;"><div class="label">Break</div>15:00 ? 17:00</div>
                </div>
              </div>
              <div class="day-col">
                <div class="day-head">Sat</div>
                <div class="day-canvas">
                  <div class="block sleep" style="top: 8%; height: 30%;"><div class="label">Sleep</div>23:00 ? 05:00</div>
                  <div class="block rest" style="top: 48%; height: 26%;"><div class="label">Recovery</div>09:00 ? 12:00</div>
                </div>
              </div>
              <div class="day-col">
                <div class="day-head">Sun</div>
                <div class="day-canvas">
                  <div class="block focus" style="top: 20%; height: 24%;"><div class="label">Review</div>11:00 ? 13:00</div>
                  <div class="block sleep" style="top: 54%; height: 24%;"><div class="label">Sleep</div>23:30 ? 05:30</div>
                </div>
              </div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )



def main() -> None:
    st.set_page_config(**PAGE_CONFIG)
    apply_styles()
    with st.sidebar:
        st.markdown(
            """
            <div style="padding:1rem 0 1.2rem; border-bottom:1px solid rgba(255,255,255,0.08); margin-bottom:.7rem;">
              <div style="display:flex; align-items:center; gap:.7rem;">
                <div style="width:32px; height:32px; border-radius:12px; background:linear-gradient(135deg,#2997ff,#7dd3fc); display:flex; align-items:center; justify-content:center; font-family:'Space Grotesk',sans-serif; font-weight:800; font-size:1rem; color:#08131d;">C</div>
                <div>
                  <div style="font-family:'Space Grotesk',sans-serif;font-size:1.75rem;font-weight:800;letter-spacing:-.06em;color:#F5F5F7; line-height:1;">Chronos</div>
                  <div style="font-family:'JetBrains Mono',monospace;font-size:9px;letter-spacing:.18em;color:#2997ff;text-transform:uppercase;margin-top:.35rem">Sleep Planner</div>
                </div>
              </div>
              <div style="font-size:12px;color:#86868b;margin-top:.8rem;line-height:1.55">Circadian rhythm intelligence</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown('<div class="sidebar-nav-label">Navigation</div>', unsafe_allow_html=True)
        page = st.radio(
            "",
            [
                "Home",
                "Dataset",
                "Weekly",
                "Baseline",
                "Calibration",
            ],
            label_visibility="collapsed",
            horizontal=False,
            index=0,
        )
        st.markdown(
            """
            <div class="nav-meta">
              <div class="sidebar-badge">● System ready</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.toggle("Developer Mode", key="developer_mode", help="Show technical diagnostics and optimization debug tools.")

    if page == "Home" or page == "Beranda":
        home_page()
    elif page == "Dataset":
        dataset_preview_page()
    elif page == "Weekly":
        weekly_page()
    elif page == "Baseline":
        baseline_page()
    elif page == "Calibration":
        calibration_page()
    elif page == "Multi-Subject":
        multi_subject_page()
    else:
        home_page()



if __name__ == "__main__":
    main()
