import { StrictMode, useEffect, useRef, useState, type ReactNode } from "react";
import { createRoot } from "react-dom/client";
import {
  ArrowUpRight,
  BarChart3,
  CalendarDays,
  Check,
  ChevronDown,
  CircleHelp,
  Database,
  FileText,
  Gauge,
  LayoutDashboard,
  Menu,
  RotateCcw,
  Save,
  Search,
  Settings2,
  SlidersHorizontal,
  Sparkles,
  Upload,
  X,
} from "lucide-react";
import "./styles.css";

type Page = "home" | "dataset" | "weekly" | "baseline" | "calibration";
const API_BASE_URL = import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000";

async function apiRequest<T>(path: string, options?: RequestInit): Promise<T> {
  const isMultipart = options?.body instanceof FormData;
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: isMultipart ? options?.headers : { "Content-Type": "application/json", ...(options?.headers ?? {}) },
    ...options,
  });
  if (!response.ok) {
    const detail = await response.json().catch(() => null);
    throw new Error(detail?.detail ?? `Permintaan gagal (${response.status})`);
  }
  return response.json() as Promise<T>;
}

const navItems: { id: Page; label: string; icon: typeof LayoutDashboard }[] = [
  { id: "home", label: "Beranda", icon: LayoutDashboard },
  { id: "dataset", label: "Dataset", icon: Database },
  { id: "weekly", label: "Mingguan", icon: CalendarDays },
  { id: "baseline", label: "Baseline", icon: BarChart3 },
  { id: "calibration", label: "Kalibrasi", icon: SlidersHorizontal },
];

const datasets = [
  { name: "academic_schedule.csv", size: "2.4 MB", date: "02 Sep 2026", status: "Aktif", rows: "1.248 baris" },
  { name: "student_sleep_patterns.csv", size: "841 KB", date: "31 Agu 2026", status: "Aktif", rows: "486 baris" },
  { name: "class_constraints.csv", size: "128 KB", date: "28 Agu 2026", status: "Arsip", rows: "96 baris" },
];

function App() {
  const [page, setPage] = useState<Page>("home");
  const [mobileOpen, setMobileOpen] = useState(false);
  const [selectedDataset, setSelectedDataset] = useState("dataset/dataset_pengujian_sora.csv");

  const navigate = (nextPage: Page) => {
    setPage(nextPage);
    setMobileOpen(false);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  return (
    <div className="app-shell">
      <header className="navbar">
        <button className="brand" onClick={() => navigate("home")} aria-label="Ke beranda">
          <span className="brand-mark">S</span>
          <span>SORA <em>Academic</em></span>
        </button>
        <button className="mobile-toggle" onClick={() => setMobileOpen((open) => !open)} aria-label="Buka menu">
          {mobileOpen ? <X size={20} /> : <Menu size={20} />}
        </button>
        <nav className={mobileOpen ? "nav-links open" : "nav-links"}>
          {navItems.map(({ id, label, icon: Icon }) => (
            <button className={page === id ? "nav-link active" : "nav-link"} key={id} onClick={() => navigate(id)}>
              <Icon size={15} />
              {label}
            </button>
          ))}
        </nav>
        <div className="nav-status"><span className="status-dot" /> Sistem siap</div>
      </header>

      <main className="content">
        {page === "home" && <HomePage navigate={navigate} selectedDataset={selectedDataset} />}
        {page === "dataset" && <DatasetPage selectedDataset={selectedDataset} onSelectDataset={setSelectedDataset} />}
        {page === "weekly" && <WeeklyPage datasetName={selectedDataset} />}
        {page === "baseline" && <BaselinePage datasetName={selectedDataset} />}
        {page === "calibration" && <CalibrationPage datasetName={selectedDataset} />}
      </main>

      <footer className="footer">
        <span>© 2026 SORA Academic</span>
        <span>Sleep Optimization &amp; Rest Arrangement</span>
      </footer>
    </div>
  );
}

function PageHeader({ eyebrow, title, description, action }: { eyebrow: string; title: string; description: string; action?: ReactNode }) {
  return (
    <div className="page-header">
      <div><p className="eyebrow">{eyebrow}</p><h1>{title}</h1><p className="page-description">{description}</p></div>
      {action}
    </div>
  );
}

function MetricCard({ label, value, detail, icon: Icon, tone = "blue" }: { label: string; value: string; detail: string; icon: typeof Gauge; tone?: string }) {
  return <div className="metric-card">
    <div className={`metric-icon ${tone}`}><Icon size={17} /></div>
    <p className="metric-label">{label}</p><strong>{value}</strong><span>{detail}</span>
  </div>;
}

function HomePage({ navigate, selectedDataset }: { navigate: (page: Page) => void; selectedDataset: string }) {
  return <div className="page-stack">
    <section className="hero">
      <div className="hero-copy">
        <p className="eyebrow"><Sparkles size={13} /> Sleep Optimization &amp; Rest Arrangement</p>
        <TypewriterHeadline />
        <p className="hero-description">SORA membantu menemukan ritme terbaik antara tidur, kelas, kerja, dan istirahat melalui optimasi yang terukur.</p>
        <div className="button-row"><button className="button primary" onClick={() => navigate("weekly")}>Mulai optimasi <ArrowUpRight size={16} /></button><button className="button ghost" onClick={() => navigate("dataset")}>Lihat dataset</button></div>
      </div>
      <div className="hero-visual"><div className="orb orb-blue" /><div className="orb orb-violet" /><div className="preview-card"><div className="preview-top"><span className="eyebrow">Dataset terpilih</span><Database size={15} /></div><strong className="preview-dataset">{selectedDataset.split("/").pop()}</strong><span className="positive"><Check size={13} /> Siap digunakan</span></div></div>
    </section>
    <section className="metrics-grid">
      <MetricCard label="Fitness score" value="—" detail="Jalankan optimasi untuk melihat hasil" icon={Gauge} />
      <MetricCard label="Jam tidur" value="—" detail="Belum ada jadwal yang dioptimasi" icon={Sparkles} tone="violet" />
      <MetricCard label="Dataset aktif" value={selectedDataset.split("/").pop() ?? "—"} detail="Dataset aktif untuk eksperimen" icon={Database} tone="green" />
    </section>
    <section className="section-heading"><div><p className="eyebrow">Ringkasan sistem</p><h2>Semua yang penting, sekilas.</h2></div><button className="text-button" onClick={() => navigate("weekly")}>Lihat laporan <ArrowUpRight size={15} /></button></section>
    <section className="bento-grid">
      <button className="bento-card bento-feature" onClick={() => navigate("weekly")}><div className="card-top"><span className="tag blue">Weekly optimization</span><ArrowUpRight size={17} /></div><h3>Mulai optimasi<br /><span>jadwal mingguan.</span></h3><p>Pilih subjek dan jalankan algoritma pada dataset aktif.</p><span className="card-foot">Buka optimasi <ArrowUpRight size={14} /></span></button>
      <button className="bento-card" onClick={() => navigate("dataset")}><div className="card-top"><span className="tag green">Dataset aktif</span><Database size={17} /></div><h3>{selectedDataset.split("/").pop()}</h3><p>Dataset yang dipakai eksperimen berikutnya</p><span className="card-foot">Kelola dataset <ArrowUpRight size={14} /></span></button>
      <button className="bento-card violet-card" onClick={() => navigate("calibration")}><div className="card-top"><span className="tag violet">Calibration</span><Settings2 size={17} /></div><h3>3 parameter</h3><p>menunggu penyesuaian</p><span className="card-foot">Buka panel kalibrasi <ArrowUpRight size={14} /></span></button>
    </section>
    <section className="activity-card"><div className="section-heading compact"><div><p className="eyebrow">Aktivitas terbaru</p><h2>Jejak optimasi</h2></div><CircleHelp size={17} /></div><div className="empty-state">Belum ada aktivitas. Jalankan optimasi untuk membuat riwayat.</div></section>
  </div>;
}

function DatasetPage({ selectedDataset, onSelectDataset }: { selectedDataset: string; onSelectDataset: (name: string) => void }) {
  const [query, setQuery] = useState("");
  const [uploaded, setUploaded] = useState("");
  const [remoteDatasets, setRemoteDatasets] = useState<typeof datasets>([]);
  const [apiError, setApiError] = useState("");
  const [uploading, setUploading] = useState(false);
  const fileInput = useRef<HTMLInputElement>(null);
  useEffect(() => {
    apiRequest<{ name: string; size: number; modified_at: number; status: string }[]>("/api/datasets")
      .then((items) => {
        setRemoteDatasets(items.map((item) => ({
          name: item.name,
          size: `${(item.size / 1024).toFixed(0)} KB`,
          date: new Date(item.modified_at * 1000).toLocaleDateString("id-ID", { day: "2-digit", month: "short", year: "numeric" }),
          status: item.status === "active" ? "Aktif" : "Arsip",
          rows: "Tersedia di API",
        })));
      })
      .catch(() => setApiError("API belum aktif; tidak ada dataset yang dapat dipilih."));
  }, []);
  const upload = async (file: File) => {
    setUploading(true);
    try {
      const body = new FormData();
      body.append("file", file);
      const result = await apiRequest<{ name: string }>("/api/datasets/upload", { method: "POST", body, headers: {} });
      setUploaded(`${result.name} berhasil diunggah.`);
      setRemoteDatasets((current) => [{ name: result.name, size: "Baru", date: "Baru saja", status: "Aktif", rows: "Menunggu validasi" }, ...current]);
      onSelectDataset(`dataset/${result.name}`);
    } catch (error) {
      setApiError(error instanceof Error ? error.message : "Upload gagal.");
    } finally {
      setUploading(false);
    }
  };
  const filtered = remoteDatasets.filter((item) => item.name.toLowerCase().includes(query.toLowerCase()));
  return <div className="page-stack"><PageHeader eyebrow="Sumber data" title="Dataset" description="Kelola data aktivitas aktual yang menjadi dasar optimasi tidur SORA." action={<><input ref={fileInput} hidden type="file" accept=".csv,.xlsx,.xls,text/csv,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,application/vnd.ms-excel" onChange={(event) => event.target.files?.[0] && upload(event.target.files[0])} /><button className="button primary" disabled={uploading} onClick={() => fileInput.current?.click()}><Upload size={16} /> {uploading ? "Mengunggah..." : "Upload dataset"}</button></>} />
    {uploaded && <div className="notice success-notice"><Check size={17} /><span>{uploaded}</span><button onClick={() => setUploaded("")}><X size={15} /></button></div>}
    {apiError && <div className="notice info-notice"><CircleHelp size={17} /><span>{apiError}</span></div>}
    <div className="toolbar"><label className="search"><Search size={17} /><input placeholder="Cari dataset..." value={query} onChange={(event) => setQuery(event.target.value)} /></label><button className="filter-button"><SlidersHorizontal size={15} /> Semua status <ChevronDown size={15} /></button></div>
    <div className="table-card"><div className="table-head"><span>Nama file</span><span>Ukuran</span><span>Diperbarui</span><span>Status</span><span /></div>{filtered.map((item) => <div className={selectedDataset === `dataset/${item.name}` ? "table-row selected-row" : "table-row"} key={item.name}><div className="file-cell"><span className="file-icon"><FileText size={17} /></span><div><strong>{item.name}</strong><span>{item.rows}</span></div></div><span>{item.size}</span><span>{item.date}</span><span><b className={`status-pill ${item.status === "Aktif" ? "active" : "archived"}`} />{item.status}</span><button className="icon-button" aria-label={`Pilih ${item.name}`} onClick={() => onSelectDataset(`dataset/${item.name}`)}>{selectedDataset === `dataset/${item.name}` ? <Check size={16} /> : <ArrowUpRight size={16} />}</button></div>)}{filtered.length === 0 && <div className="empty-state">Dataset tidak ditemukan.</div>}</div>
    <div className="info-grid"><div className="info-card"><Database size={18} /><div><strong>Format didukung</strong><span>CSV, XLSX, atau XLS kuesioner jadwal mingguan.</span></div></div><div className="info-card"><Check size={18} /><div><strong>Optimasi tidur</strong><span>Tidur aktual dipertahankan sebagai acuan, lalu digeser dan dilengkapi power nap bila meningkatkan fitness.</span></div></div></div>
  </div>;
}

function WeeklyPage({ datasetName }: { datasetName: string }) {
  const [subject, setSubject] = useState("");
  const [subjects, setSubjects] = useState<string[]>([]);
  const [result, setResult] = useState<{ schedule: number[][]; observed_schedule: number[][]; metrics: { day: string; fitness?: number; observed_fitness?: number; fitness_delta?: number; sleep_hours?: number; observed_sleep_hours?: number; nap_sessions?: number; sleep_change_slots?: number }[]; history: Iteration[] } | null>(null);
  const [population, setPopulation] = useState(50);
  const [mutation, setMutation] = useState(10);
  const [crossover, setCrossover] = useState(80);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  useEffect(() => {
    apiRequest<{ subjects: string[] }>(`/api/subjects?dataset_name=${encodeURIComponent(datasetName)}`)
      .then((data) => { setSubjects(data.subjects); setSubject(data.subjects[0] ?? ""); })
      .catch((reason) => setError(reason instanceof Error ? reason.message : "Subjek tidak dapat dimuat."));
  }, [datasetName]);
  const optimize = async () => {
    if (!subject) return;
    setLoading(true);
    setError("");
    try {
      const data = await apiRequest<{ schedule: number[][]; observed_schedule: number[][]; metrics: { day: string; fitness?: number; observed_fitness?: number; fitness_delta?: number; sleep_hours?: number; observed_sleep_hours?: number; nap_sessions?: number; sleep_change_slots?: number }[]; history: Iteration[] }>("/api/weekly/optimize", {
        method: "POST",
        body: JSON.stringify({ target_name: subject, dataset_name: datasetName, population_size: population, mutation_rate: mutation / 100, crossover_rate: crossover / 100 }),
      });
      setResult(data);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Optimasi gagal.");
    } finally {
      setLoading(false);
    }
  };
  const metrics = result?.metrics ?? [];
  const chartValues = metrics.map((item) => Math.max(10, Math.min(100, (item.fitness ?? 0) + 50)));
  return <div className="page-stack"><PageHeader eyebrow="Optimasi tidur berbasis data" title="Mingguan" description="Tidur aktual responden menjadi acuan. SORA menggeser waktu tidur dan menambahkan power nap hanya jika fitness meningkat." action={<div className="button-row compact-actions"><select className="filter-button" value={subject} onChange={(event) => setSubject(event.target.value)}><option value="">Pilih subjek</option>{subjects.map((name) => <option key={name}>{name}</option>)}</select><button className="button primary" disabled={!subject || loading} onClick={optimize}>{loading ? "Mengoptimasi..." : "Optimalkan jadwal tidur"} <ArrowUpRight size={15} /></button></div>} />
    {error && <div className="notice info-notice"><CircleHelp size={17} /><span>{error}</span></div>}
    <div className="metrics-grid"><MetricCard label="Fitness rata-rata" value={metrics.length ? (metrics.reduce((sum, item) => sum + (item.fitness ?? 0), 0) / metrics.length).toFixed(1) : "—"} detail={metrics.length ? `Populasi ${population} · mutasi ${mutation}%` : "Jalankan optimasi untuk melihat hasil"} icon={Gauge} /><MetricCard label="Tidur hasil optimasi" value={metrics.length ? `${(metrics.reduce((sum, item) => sum + (item.sleep_hours ?? 0), 0) / metrics.length).toFixed(1)} jam` : "—"} detail="Durasi tidur pada jadwal baru" icon={Sparkles} tone="green" /><MetricCard label="Power nap" value={metrics.length ? `${metrics.reduce((sum, item) => sum + (item.nap_sessions ?? 0), 0)} sesi` : "—"} detail={metrics.length ? "Ditambahkan bila membantu recovery" : "Belum ada hasil"} icon={Check} tone="violet" /></div>
    <section className="parameter-strip"><span className="eyebrow">Parameter eksperimen</span><label>Populasi <input type="number" min="10" max="500" value={population} onChange={(event) => setPopulation(Number(event.target.value))} /></label><label>Mutasi <input type="number" min="0" max="100" value={mutation} onChange={(event) => setMutation(Number(event.target.value))} />%</label><label>Crossover <input type="number" min="0" max="100" value={crossover} onChange={(event) => setCrossover(Number(event.target.value))} />%</label></section>
    <section className="chart-card"><div className="section-heading compact"><div><p className="eyebrow">Performa harian</p><h2>{result ? `Hasil optimasi · ${subject}` : "Belum ada hasil optimasi"}</h2></div><span className="chart-legend"><i /> Fitness <i className="muted-dot" /> Target</span></div>{result ? <div className="large-chart">{chartValues.map((height, i) => <div className="chart-column" key={i}><i style={{ height: `${height}%` }} /><span>{["Sen", "Sel", "Rab", "Kam", "Jum", "Sab", "Min"][i]}</span></div>)}</div> : <div className="empty-state">Pilih dataset dan subjek, lalu jalankan optimasi.</div>}</section>
    <ScheduleTimeline schedule={result?.schedule} />
    <WeeklyScheduleComparison observedSchedule={result?.observed_schedule} optimizedSchedule={result?.schedule} />
    <ScheduleTransition observedSchedule={result?.observed_schedule} optimizedSchedule={result?.schedule} metrics={metrics} />
    <IterationHistory history={result?.history} />
    <section className="activity-card"><div className="section-heading compact"><div><p className="eyebrow">Timeline</p><h2>Catatan minggu ini</h2></div></div><div className="empty-state">{result ? "Catatan akan mengikuti hasil optimasi aktif." : "Belum ada catatan. Jalankan optimasi untuk mengisinya."}</div></section>
  </div>;
}

type Iteration = { day: string; generation: number; best_fitness: number; mean_top10_fitness: number; schedule?: number[] };

function WeeklyScheduleComparison({ observedSchedule, optimizedSchedule }: { observedSchedule?: number[][]; optimizedSchedule?: number[][] }) {
  const ready = observedSchedule?.length === 7 && optimizedSchedule?.length === 7;
  return <section className="full-comparison-card">
    <div className="section-heading compact"><div><p className="eyebrow">Komparasi penuh · 7 hari</p><h2>Seluruh jadwal sebelum dan sesudah optimasi</h2><p className="page-description">Setiap baris menunjukkan 24 jam aktivitas. Warna yang sama digunakan agar pergeseran tidur dan penambahan power nap mudah dilacak.</p></div><span className="schedule-caption">Senin–Minggu · 48 slot/hari</span></div>
    {!ready ? <div className="empty-state">Komparasi penuh akan muncul setelah optimasi berhasil.</div> : <div className="comparison-timelines">
      <ScheduleTimeline schedule={observedSchedule} title="Jadwal awal dari dataset" compact />
      <ScheduleTimeline schedule={optimizedSchedule} title="Jadwal baru hasil optimasi" compact />
    </div>}
  </section>;
}

function TypewriterHeadline() {
  const phrases = ["Rancang hari yang lebih seimbang.", "Optimalkan tidur lebih cerdas.", "Temukan ritme terbaikmu."];
  const [phraseIndex, setPhraseIndex] = useState(0);
  const [text, setText] = useState("");
  const [deleting, setDeleting] = useState(false);
  useEffect(() => {
    const phrase = phrases[phraseIndex];
    const done = text === phrase && !deleting;
    const empty = text.length === 0 && deleting;
    const delay = done ? 1800 : empty ? 450 : deleting ? 42 : 78;
    const timer = window.setTimeout(() => {
      if (done) setDeleting(true);
      else if (empty) { setDeleting(false); setPhraseIndex((index) => (index + 1) % phrases.length); }
      else setText(deleting ? phrase.slice(0, text.length - 1) : phrase.slice(0, text.length + 1));
    }, delay);
    return () => window.clearTimeout(timer);
  }, [deleting, phraseIndex, text]);
  const split = text.lastIndexOf(" ");
  return <div className="typewriter-headline" aria-label={phrases[phraseIndex]}><h1>{split > 0 ? <><span>{text.slice(0, split)}</span>{" "}<em>{text.slice(split + 1)}</em></> : <span>{text}</span>}<i aria-hidden="true" /></h1></div>;
}

function ScheduleTransition({ observedSchedule, optimizedSchedule, metrics }: { observedSchedule?: number[][]; optimizedSchedule?: number[][]; metrics: { day: string; fitness?: number; observed_fitness?: number; fitness_delta?: number; sleep_hours?: number; observed_sleep_hours?: number; nap_sessions?: number; sleep_change_slots?: number }[] }) {
  const [openDay, setOpenDay] = useState<string | null>(null);
  const days = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"];
  const ready = observedSchedule?.length === 7 && optimizedSchedule?.length === 7;
  return <section className="transition-card">
    <div className="section-heading compact"><div><p className="eyebrow">Dampak optimasi</p><h2>Jadwal lama → jadwal baru</h2></div><span className="schedule-caption">Perubahan tidur dan power nap</span></div>
    {!ready ? <div className="empty-state">Perbandingan akan muncul setelah optimasi berhasil.</div> : <div className="transition-list">{days.map((day, index) => {
      const before = observedSchedule[index];
      const after = optimizedSchedule[index];
      const metric = metrics[index] ?? { day };
      const changedSlots = after.map((value, slot) => value !== before[slot] ? slot : "").filter((slot): slot is number => slot !== "");
      const isOpen = openDay === day;
      const durationDelta = (metric.sleep_hours ?? 0) - (metric.observed_sleep_hours ?? 0);
      const fitnessDelta = metric.fitness_delta ?? ((metric.fitness ?? 0) - (metric.observed_fitness ?? 0));
      const napText = (metric.nap_sessions ?? 0) > 0 ? `menambahkan ${metric.nap_sessions} sesi power nap` : "tidak menambahkan power nap";
      return <div className={isOpen ? "transition-day open" : "transition-day"} key={day}>
        <button className="transition-trigger" onClick={() => setOpenDay(isOpen ? null : day)}><span><b>{day}</b><small>{changedSlots.length} slot berubah · {napText}</small></span><strong className={fitnessDelta >= 0 ? "positive" : "negative"}>{fitnessDelta >= 0 ? "+" : ""}{fitnessDelta.toFixed(2)} fitness</strong><ChevronDown size={16} /></button>
        {isOpen && <div className="transition-detail"><ScheduleDiff before={before} after={after} changedSlots={changedSlots} /><div className="impact-copy"><Sparkles size={15} /><span>{describeImpact(metric, durationDelta, fitnessDelta, changedSlots.length)}</span></div></div>}
      </div>;
    })}</div>}
  </section>;
}

function describeImpact(metric: { sleep_hours?: number; observed_sleep_hours?: number; nap_sessions?: number }, durationDelta: number, fitnessDelta: number, changedSlots: number) {
  const duration = durationDelta === 0 ? "Durasi tidur dipertahankan" : `${durationDelta > 0 ? "Tidur bertambah" : "Tidur berkurang"} ${Math.abs(durationDelta).toFixed(1)} jam`;
  const nap = metric.nap_sessions ? `Power nap membantu menurunkan fatigue dan meningkatkan recovery.` : "Tidak ada power nap karena tidak memberi peningkatan fitness pada konfigurasi ini.";
  return `${duration}; ${changedSlots} slot disesuaikan; fitness ${fitnessDelta >= 0 ? "meningkat" : "menurun"} ${Math.abs(fitnessDelta).toFixed(2)}. ${nap}`;
}

function IterationHistory({ history }: { history?: Iteration[] }) {
  const [openDay, setOpenDay] = useState<string | null>(null);
  const [openChange, setOpenChange] = useState<string | null>(null);
  const grouped = (history ?? []).reduce<Record<string, typeof history>>((groups, item) => {
    (groups[item.day] ??= []).push(item);
    return groups;
  }, {});
  const sections: Record<string, Iteration[]> = grouped as Record<string, Iteration[]>;
  return <section className="history-card">
    <div className="section-heading compact"><div><p className="eyebrow">Transparansi optimizer</p><h2>History per iterasi</h2></div><span className="schedule-caption">Buka untuk melihat perubahan</span></div>
    <div className="history-list">{Object.keys(sections).length ? Object.entries(sections).map(([day, entries]) => {
      const rows = (entries ?? []).filter((entry, index, list) => {
        if (index === 0) return true;
        const previous = list[index - 1].schedule;
        return Boolean(entry.schedule && previous && entry.schedule.some((value, slot) => value !== previous[slot]));
      });
      const first = rows[0]?.best_fitness ?? 0;
      const last = rows[rows.length - 1]?.best_fitness ?? 0;
      const change = last - first;
      return <div className={openDay === day ? "history-item open" : "history-item"} key={day}>
        <button className="history-trigger" onClick={() => setOpenDay(openDay === day ? null : day)}><span className="history-day"><i className="activity-dot blue" /><b>{day}</b><small>{rows.length} checkpoint tersimpan</small></span><span className={change >= 0 ? "history-change positive" : "history-change negative"}>{change >= 0 ? "+" : ""}{change.toFixed(1)} fitness</span><ChevronDown size={16} /></button>
        {openDay === day && <div className="history-detail"><div className="change-summary"><span><i className="activity-dot blue" /> {rows.length - 1} perubahan jadwal terdeteksi</span><small>Checkpoint tanpa perubahan disembunyikan</small></div>{rows.slice(1).map((entry, index) => {
          const previous = rows[index].schedule;
          const changedSlots = entry.schedule && previous ? entry.schedule.map((value, slot) => value !== previous[slot] ? slot : "").filter((slot): slot is number => slot !== "") : [];
          const changeSegments = describeChanges(previous, entry.schedule ?? previous ?? [], changedSlots);
          const changeId = `${day}-${entry.generation}`;
          return <div className="visual-change" key={changeId}><button className="change-trigger" onClick={() => setOpenChange(openChange === changeId ? null : changeId)}><span><b>Perubahan {index + 1}</b><small>Generasi {entry.generation} · {changedSlots.length} slot berubah</small></span><strong className="positive">+{(entry.best_fitness - rows[index].best_fitness).toFixed(2)}</strong><ChevronDown size={15} /></button>{openChange === changeId && <><div className="change-description"><Sparkles size={14} /><span>{changeSegments.length ? changeSegments.join(" · ") : "Jadwal tetap stabil pada checkpoint ini."}</span></div><ScheduleDiff before={previous ?? entry.schedule ?? []} after={entry.schedule ?? previous ?? []} changedSlots={changedSlots} /></>}</div>;
        })}</div>}
      </div>;
    }) : <div className="empty-state">History akan muncul setelah optimasi dijalankan.</div>}</div>
  </section>;
}

function describeChanges(before: number[] | undefined, after: number[], changedSlots: number[]) {
  if (!before || !changedSlots.length) return [];
  const segments: string[] = [];
  let start = changedSlots[0];
  let end = start;
  changedSlots.slice(1).forEach((slot) => {
    if (slot === end + 1 && after[slot] === after[start] && before[slot] === before[start]) end = slot;
    else {
      segments.push(`${formatTime(start)}–${formatTime(end + 1)}: ${activityNames[before[start]] ?? "Aktivitas"} → ${activityNames[after[start]] ?? "Aktivitas"}`);
      start = slot;
      end = slot;
    }
  });
  segments.push(`${formatTime(start)}–${formatTime(end + 1)}: ${activityNames[before[start]] ?? "Aktivitas"} → ${activityNames[after[start]] ?? "Aktivitas"}`);
  return segments.slice(0, 4);
}

function ScheduleDiff({ before, after, changedSlots }: { before?: number[]; after: number[]; changedSlots: number[] }) {
  const cells = after.map((activity, slot) => <span key={slot} className={changedSlots.includes(slot) ? "diff-cell changed" : "diff-cell"} title={`${formatTime(slot)} · ${activityNames[activity] ?? "Aktivitas"}${changedSlots.includes(slot) ? " · berubah" : ""}`} style={{ background: `var(--activity-${activityClasses[activity] ?? "rest"})` }} />);
  return <div className="schedule-diff"><div className="diff-label"><span><i /> Sebelum</span><span><i className="changed-dot" /> Sesudah</span><small>slot berubah disorot</small></div><div className="diff-track">{before?.map((activity, slot) => <span key={slot} className="diff-cell" style={{ background: `var(--activity-${activityClasses[activity] ?? "rest"})` }} title={`${formatTime(slot)} · ${activityNames[activity] ?? "Aktivitas"}`} />)}</div><div className="diff-track after">{cells}</div><div className="diff-time"><span>00:00</span><span>06:00</span><span>12:00</span><span>18:00</span><span>24:00</span></div></div>;
}

const activityNames = ["Tidur", "Kerja", "Nap", "Istirahat", "Kuliah"];
const activityClasses = ["sleep", "work", "nap", "rest", "class"];
const activityDescriptions = [
  "Waktu tidur utama untuk pemulihan tubuh dan konsolidasi energi.",
  "Blok fokus untuk pekerjaan atau tugas akademik.",
  "Tidur singkat untuk membantu mengurangi rasa lelah.",
  "Waktu senggang untuk makan, relaksasi, dan transisi aktivitas.",
  "Jadwal perkuliahan atau kegiatan belajar terstruktur.",
];
function ScheduleTimeline({ schedule, title, compact = false }: { schedule?: number[][]; title?: string; compact?: boolean }) {
  const days = ["Sen", "Sel", "Rab", "Kam", "Jum", "Sab", "Min"];
  const visibleSchedule = schedule?.length === 7 ? schedule : [];
  return <section className={compact ? "schedule-card compact-schedule" : "schedule-card"}>
    <div className="section-heading compact"><div><p className="eyebrow">{title ? "Versi jadwal" : "Jadwal kontinu"}</p><h2>{title ?? "Aktivitas selama seminggu"}</h2></div><span className="schedule-caption">48 slot · 30 menit</span></div>
    {!compact && <div className="schedule-legend">{activityNames.map((name, index) => <span key={name} title={activityDescriptions[index]}><i className={activityClasses[index]} /> <b>{name}</b><small>{activityDescriptions[index]}</small></span>)}</div>}
    {visibleSchedule.length ? <div className="schedule-scroll"><div className="schedule-board">
      <div className="schedule-time-axis"><span>00:00</span><span>06:00</span><span>12:00</span><span>18:00</span><span>24:00</span></div>
      {visibleSchedule.map((day, dayIndex) => <div className="schedule-day" key={days[dayIndex]}><strong>{days[dayIndex]}</strong><div className="schedule-track">{compressSchedule(day).map((block) => {
        const activity = activityNames[block.activity] ?? "Aktivitas";
        const start = formatTime(block.start);
        const end = formatTime(block.start + block.length);
        const duration = `${block.length * 0.5} jam`;
        return <div className={`schedule-block ${activityClasses[block.activity] ?? "rest"}`} key={`${dayIndex}-${block.start}`} style={{ top: `${(block.start / 48) * 100}%`, height: `${(block.length / 48) * 100}%`, animationDelay: `${(dayIndex * 0.06) + (block.start * 0.008)}s` }} title={`${activity} · ${start}–${end} · ${duration}`}><span>{block.length >= 4 ? <><b>{activity}</b><small>{start}–{end}</small></> : ""}</span></div>;
      })}</div></div>)}
    </div></div> : <div className="empty-state">Jadwal akan muncul setelah optimasi berhasil.</div>}
    {!compact && <div className="schedule-notes">{activityNames.map((name, index) => <div key={name}><i className={activityClasses[index]} /><span><strong>{name}</strong><small>{activityDescriptions[index]}</small></span></div>)}</div>}
  </section>;
}

function compressSchedule(day: number[]) {
  const blocks: { activity: number; start: number; length: number }[] = [];
  day.forEach((activity, index) => {
    const previous = blocks[blocks.length - 1];
    if (previous?.activity === activity) previous.length += 1;
    else blocks.push({ activity, start: index, length: 1 });
  });
  return blocks;
}

function formatTime(slot: number) {
  const normalized = slot % 48;
  return `${String(Math.floor(normalized / 2)).padStart(2, "0")}:${normalized % 2 ? "30" : "00"}`;
}

function BaselinePage({ datasetName }: { datasetName: string }) {
  const [sleep, setSleep] = useState("7.5");
  const [nap, setNap] = useState("0.5");
  const [subject, setSubject] = useState("");
  const [subjects, setSubjects] = useState<string[]>([]);
  const [comparison, setComparison] = useState<{ metrics: Record<string, { fitness?: number; sleep_hours?: number; nap_sessions?: number }> } | null>(null);
  const [error, setError] = useState("");
  useEffect(() => { apiRequest<{ subjects: string[] }>(`/api/subjects?dataset_name=${encodeURIComponent(datasetName)}`).then((data) => { setSubjects(data.subjects); setSubject(data.subjects[0] ?? ""); }).catch(() => setError("Dataset belum tersedia atau belum memiliki kolom Nama.")); }, [datasetName]);
  const compare = async () => {
    if (!subject) return;
    setError("");
    try {
      const data = await apiRequest<{ metrics: Record<string, { fitness?: number; sleep_hours?: number; nap_sessions?: number }> }>("/api/baseline/compare", { method: "POST", body: JSON.stringify({ subject_name: subject, dataset_name: datasetName, population_size: 50, mutation_rate: 0.1, crossover_rate: 0.8 }) });
      setComparison(data);
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Perbandingan gagal."); }
  };
  const soraFitness = comparison?.metrics.sora?.fitness;
  return <div className="page-stack"><PageHeader eyebrow="Benchmark acuan" title="Baseline" description="Atur nilai pembanding untuk mengukur dampak optimasi secara objektif." action={<div className="button-row compact-actions"><select className="filter-button" value={subject} onChange={(event) => setSubject(event.target.value)}><option value="">Pilih subjek</option>{subjects.map((name) => <option key={name}>{name}</option>)}</select><button className="button primary" disabled={!subject} onClick={compare}>Bandingkan <ArrowUpRight size={15} /></button></div>} />
    {error && <div className="notice info-notice"><CircleHelp size={17} /><span>{error}</span></div>}
    <div className="notice info-notice"><Sparkles size={18} /><div><strong>Baseline akademik aktif</strong><span>Nilai ini digunakan sebagai pembanding pada setiap eksperimen mingguan.</span></div><span className="tag blue">Default</span></div>
    <div className="two-column"><section className="form-card"><div className="section-heading compact"><div><p className="eyebrow">Parameter acuan</p><h2>Nilai baseline</h2></div><Settings2 size={17} /></div><label className="field"><span>Target tidur (jam)</span><input type="number" step="0.5" value={sleep} onChange={(e) => setSleep(e.target.value)} /></label><label className="field"><span>Target nap (jam)</span><input type="number" step="0.5" value={nap} onChange={(e) => setNap(e.target.value)} /></label><label className="field"><span>Minimal recovery score</span><input type="number" value="70" readOnly /></label><button className="button primary full" onClick={() => setError("Baseline tersimpan untuk sesi ini.")}><Save size={16} /> Simpan baseline</button></section><section className="comparison-card"><div className="section-heading compact"><div><p className="eyebrow">Comparison matrix</p><h2>Hasil nyata</h2></div></div>{comparison ? Object.entries(comparison.metrics).map(([method, values]) => <div className="comparison-row" key={method}><span>{method}</span><strong>{values.fitness?.toFixed(1) ?? "—"}</strong><span className="muted">{values.sleep_hours?.toFixed(1) ?? "—"} jam · {values.nap_sessions ?? 0} nap</span><b>{method === "sora" ? "Optimasi" : "Acuan"}</b></div>) : <div className="empty-state">Pilih subjek lalu klik Bandingkan.</div>}</section></div>
  </div>;
}

function CalibrationPage({ datasetName }: { datasetName: string }) {
  const [population, setPopulation] = useState(50);
  const [mutation, setMutation] = useState(10);
  const [crossover, setCrossover] = useState(80);
  const [saved, setSaved] = useState(false);
  const [running, setRunning] = useState(false);
  const [apiResult, setApiResult] = useState<number | null>(null);
  const [error, setError] = useState("");
  const reset = () => { setPopulation(50); setMutation(10); setCrossover(80); setSaved(false); };
  const runCalibration = async () => {
    setRunning(true); setError("");
    try {
      const data = await apiRequest<{ best_parameters: { average_fitness?: number } | null }>("/api/calibration/run", { method: "POST", body: JSON.stringify({ dataset_name: datasetName, generations: 20 }) });
      setApiResult(data.best_parameters?.average_fitness ?? null); setSaved(true);
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Kalibrasi gagal."); } finally { setRunning(false); }
  };
  return <div className="page-stack"><PageHeader eyebrow="Penyesuaian sistem" title="Kalibrasi" description="Sesuaikan parameter Genetic Algorithm dan lihat perkiraan dampaknya secara langsung." />
    {error && <div className="notice info-notice"><CircleHelp size={17} /><span>{error}</span></div>}
    <div className="two-column calibration-layout"><section className="form-card control-panel"><div className="section-heading compact"><div><p className="eyebrow">Control panel</p><h2>Parameter optimizer</h2></div><SlidersHorizontal size={17} /></div><Slider label="Ukuran populasi" value={population} min={20} max={100} suffix=" individu" onChange={setPopulation} /><Slider label="Mutation rate" value={mutation} min={0} max={30} suffix="%" onChange={setMutation} /><Slider label="Crossover rate" value={crossover} min={50} max={100} suffix="%" onChange={setCrossover} /><div className="action-bar"><button className="button ghost" onClick={reset}><RotateCcw size={15} /> Reset</button><button className="button primary" disabled={running} onClick={runCalibration}>{running ? "Menjalankan..." : "Jalankan kalibrasi"} <Save size={15} /></button></div></section><section className="live-card"><div className="live-glow" /><div className="section-heading compact"><div><p className="eyebrow">Live preview</p><h2>Perkiraan hasil</h2></div><span className="live-badge"><i /> Live</span></div><div className="score-ring"><strong>{apiResult?.toFixed(1) ?? (80 + mutation * 0.15 + crossover * 0.04).toFixed(1)}</strong><span>{apiResult ? "hasil calibration" : "estimated fitness"}</span></div><div className="preview-stat"><span>Konvergensi</span><strong>{population > 60 ? "Lebih stabil" : "Cepat"}</strong></div><div className="preview-stat"><span>Eksplorasi</span><strong>{mutation > 15 ? "Tinggi" : "Seimbang"}</strong></div>{saved && <div className="saved-state"><Check size={15} /> Perubahan tersimpan</div>}</section></div>
  </div>;
}

function Slider({ label, value, min, max, suffix, onChange }: { label: string; value: number; min: number; max: number; suffix: string; onChange: (value: number) => void }) {
  return <label className="slider-field"><div><span>{label}</span><strong>{value}{suffix}</strong></div><input type="range" min={min} max={max} value={value} onChange={(e) => onChange(Number(e.target.value))} /><div className="range-labels"><span>{min}{suffix.trim()}</span><span>{max}{suffix.trim()}</span></div></label>;
}

createRoot(document.getElementById("root")!).render(<StrictMode><App /></StrictMode>);
