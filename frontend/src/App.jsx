import { useState } from "react";
import HistoryTab from "./HistoryTab";
import CoverLetterTab from "./CoverLetterTab";
import CvAnalyzerTab from "./CvAnalyzerTab";
import InterviewPrepTab from "./InterviewPrepTab";
import Iridescence from "./components/Iridescence";
import GooeyNav from "./components/GooeyNav";
import StarBorder from "./components/StarBorder";
import { saveAnalysis, buildEntry } from "./storage";
import { exportReportPdf } from "./exportPdf";

const API = "http://localhost:8000";

const NAV_ITEMS = [
  { label: "Analyser", key: "analyze" },
  { label: "Mon CV", key: "cv" },
  { label: "Lettre", key: "letter" },
  { label: "Entretien", key: "interview" },
  { label: "Historique", key: "history" },
];

export default function App() {
  const [tab, setTab] = useState("analyze");
  const [file, setFile] = useState(null);
  const [job, setJob] = useState("");
  const [report, setReport] = useState(null);
  const [recos, setRecos] = useState([]);
  const [meta, setMeta] = useState(null);
  const [career, setCareer] = useState(null);
  const [sectionsBreakdown, setSectionsBreakdown] = useState([]);
  const [jobMeta, setJobMeta] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const currentIndex = Math.max(0, NAV_ITEMS.findIndex((n) => n.key === tab));

  async function handleAnalyze() {
    setError("");
    setReport(null);
    setRecos([]);
    setMeta(null);
    setCareer(null);
    setSectionsBreakdown([]);
    setJobMeta(null);
    setLoading(true);
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 30000);
    try {
      const form = new FormData();
      form.append("cv", file);
      form.append("job", job);
      const res = await fetch(`${API}/api/analyze`, {
        method: "POST",
        body: form,
        signal: controller.signal,
      });
      const data = await res.json();
      if (data.error) throw new Error(`${data.type}: ${data.error}`);
      setReport(data.report);
      setRecos(data.recommendations || []);
      setMeta(data.meta);
      setCareer(data.career || null);
      setSectionsBreakdown(data.sections_breakdown || []);
      setJobMeta(data.job_meta || null);
      saveAnalysis(
        buildEntry({
          file,
          job,
          report: data.report,
          recommendations: data.recommendations,
          meta: data.meta,
        })
      );
    } catch (e) {
      if (e.name === "AbortError")
        setError("Timeout 30s — uvicorn ne repond pas.");
      else setError(e.message || "Erreur inconnue");
    } finally {
      clearTimeout(timeoutId);
      setLoading(false);
    }
  }

  function handleReopen(entry) {
    setJob(entry.jobText);
    setReport(entry.report);
    setRecos(entry.recommendations || []);
    setMeta(entry.meta || null);
    setCareer(entry.career || null);
    setSectionsBreakdown(entry.sectionsBreakdown || []);
    setJobMeta(entry.jobMeta || null);
    setFile(null);
    setError("");
    setTab("analyze");
  }

  async function handleExport() {
    if (!report) return;
    const jobTitle = (job || "").trim().split("\n").find((l) => l.trim()) || "";
    try {
      await exportReportPdf({
        report,
        recommendations: recos,
        meta,
        career,
        jobTitle,
      });
    } catch (e) {
      setError("Erreur export PDF : " + (e.message || "inconnue"));
    }
  }

  const canAnalyze = file && job.trim().length > 20 && !loading;
  const hasAnalysis = !!report;

  return (
    <div className="relative min-h-screen text-slate-800">
      {/* Background Iridescence fixe */}
      <div className="fixed inset-0 -z-10">
        <Iridescence
          color="#4a506e"
          speed={0.4}
          scale={1}
          detail={6}
          brightness={1.4}
          contrast={1}
          saturation={1.1}
          mouseReact={true}
          amplitude={0.08}
          stir={0.3}
          sheen={0.4}
          clickSwirl={true}
          grain={0}
          fade={0}
        />
      </div>

      <div className="relative">
        {/* Header avec GooeyNav */}
        <header className="sticky top-0 z-20 py-3 bg-white/40 backdrop-blur-xl border-b border-white/30">
          <div className="max-w-5xl mx-auto px-4 sm:px-6 flex items-center justify-between gap-3 flex-wrap">
            <img
              src="/CareerMatch.png"
              alt="CareerMatch"
              className="h-20 w-auto object-contain"
            />
            <GooeyNav
              items={NAV_ITEMS}
              activeIndex={currentIndex}
              onChange={(index) => setTab(NAV_ITEMS[index].key)}
              theme="light"
              color="#2563eb"
              colors={["#2563eb", "#06b6d4", "#ec4899"]}
              size="md"
              frame
              particleCount={15}
              spread={56}
              animationTime={600}
              timeVariance={300}
              gooeyness={0.5}
              wobble={0.5}
              hoverEffect
            />
          </div>
        </header>

        <main className="max-w-4xl mx-auto px-4 sm:px-6 py-6 sm:py-8 space-y-6 sm:space-y-8">
          {tab === "cv" && <CvAnalyzerTab />}
          {tab === "history" && <HistoryTab onReopen={handleReopen} />}
          {tab === "letter" && (
            <CoverLetterTab
              cvFile={file}
              jobText={job}
              hasAnalysis={hasAnalysis}
              onGoToAnalyze={() => setTab("analyze")}
            />
          )}
          {tab === "interview" && (
            <InterviewPrepTab
              cvFile={file}
              jobText={job}
              hasAnalysis={hasAnalysis}
              onGoToAnalyze={() => setTab("analyze")}
            />
          )}

          {tab === "analyze" && (
            <>
              <section className="grid md:grid-cols-2 gap-4 sm:gap-6">
                <div className="bg-white/85 backdrop-blur-md rounded-xl border border-white/60 shadow-sm p-4 sm:p-5">
                  <label className="block text-sm font-semibold mb-2">
                    1. Ton CV (PDF)
                  </label>
                  <input
                    type="file"
                    accept="application/pdf"
                    onChange={(e) => setFile(e.target.files[0])}
                    className="block w-full text-sm file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:bg-blue-600 file:text-white hover:file:bg-blue-700"
                  />
                  {file && (
                    <p className="mt-2 text-xs text-slate-500 truncate">
                      {file.name}
                    </p>
                  )}
                </div>
                <div className="bg-white/85 backdrop-blur-md rounded-xl border border-white/60 shadow-sm p-4 sm:p-5">
                  <label className="block text-sm font-semibold mb-2">
                    2. Offre d emploi
                  </label>
                  <textarea
                    value={job}
                    onChange={(e) => setJob(e.target.value)}
                    placeholder="Colle ici le texte de l'offre..."
                    className="w-full h-40 p-3 border border-slate-300 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  <p className="mt-1.5 text-[11px] text-slate-400">
                    {job.trim().length} caractères
                  </p>
                </div>
              </section>

              <div className="flex justify-center">
                <StarBorder
                  onClick={handleAnalyze}
                  disabled={!canAnalyze}
                  color="#06b6d4"
                  trailColor="#ec4899"
                  duration={3.5}
                  direction="clockwise"
                  stars={2}
                  trailLength={0.55}
                  thickness={2}
                  radius={12}
                  glow={0.7}
                  hover="brighten"
                  sparkle
                  clickPulse
                  theme="light"
                  backgroundColor="#2563eb"
                  textColor="#ffffff"
                  borderColor="rgba(255,255,255,0.18)"
                  className="px-8 py-3 text-base"
                >
                  {loading ? "Analyse en cours..." : "Analyser"}
                </StarBorder>
              </div>

              {error && (
                <div className="bg-red-50 border border-red-200 text-red-700 p-4 rounded-lg text-sm">
                  {error}
                </div>
              )}

              {report && (
                <section className="space-y-6">
                  <ScoreCard report={report} meta={meta} />

                  {jobMeta && <JobMetaCard jobMeta={jobMeta} />}
                  {career && career.count_diplomas > 0 && (
                    <EducationCard career={career} />
                  )}
                  {sectionsBreakdown.length > 0 && (
                    <SectionsBreakdown items={sectionsBreakdown} />
                  )}

                  <div className="grid md:grid-cols-2 gap-4 sm:gap-6">
                    <SkillCard
                      title="Competences trouvees"
                      color="green"
                      items={report.skills_found}
                    />
                    <SkillCard
                      title="A valoriser (si tu les maitrises)"
                      color="amber"
                      items={report.skills_to_highlight}
                    />
                  </div>

                  {report.bonus_skills.length > 0 && (
                    <SkillCard
                      title="Bonus (hors offre)"
                      color="slate"
                      items={report.bonus_skills}
                    />
                  )}

                  {recos.length > 0 && (
                    <div className="bg-white/85 backdrop-blur-md rounded-xl border border-white/60 shadow-sm p-4 sm:p-6 space-y-3">
                      <h2 className="text-lg font-semibold">Recommandations</h2>
                      {recos.map((r, i) => (
                        <div
                          key={i}
                          className={`p-4 rounded-lg border ${
                            r.priority === "high"
                              ? "bg-red-50 border-red-200"
                              : r.priority === "medium"
                              ? "bg-amber-50 border-amber-200"
                              : "bg-blue-50 border-blue-200"
                          }`}
                        >
                          <p className="font-semibold text-sm">{r.title}</p>
                          <p className="text-sm mt-1">{r.message}</p>
                        </div>
                      ))}
                    </div>
                  )}

                  <div className="flex flex-wrap gap-3 justify-center items-center">
                    <button
                      onClick={handleExport}
                      className="px-6 py-2.5 rounded-lg bg-slate-800 text-white font-semibold shadow hover:bg-slate-900"
                    >
                      ⬇️ Telecharger le rapport (PDF)
                    </button>
                    <StarBorder
                      onClick={() => setTab("letter")}
                      color="#06b6d4"
                      trailColor="#ec4899"
                      duration={4}
                      direction="clockwise"
                      stars={2}
                      trailLength={0.5}
                      thickness={2}
                      radius={10}
                      glow={0.6}
                      hover="brighten"
                      sparkle
                      clickPulse
                      theme="light"
                      backgroundColor="#2563eb"
                      textColor="#ffffff"
                      borderColor="rgba(255,255,255,0.18)"
                      className="px-6 py-2.5 text-sm"
                    >
                      ✉️ Generer une lettre
                    </StarBorder>
                    <button
                      onClick={() => setTab("interview")}
                      className="px-6 py-2.5 rounded-lg bg-white/80 backdrop-blur border border-slate-300 text-slate-700 font-semibold hover:bg-white"
                    >
                      🎤 Preparer l entretien
                    </button>
                  </div>
                </section>
              )}
            </>
          )}
        </main>
      </div>
    </div>
  );
}

function JobMetaCard({ jobMeta }) {
  const { work_mode, contract_types, salary } = jobMeta;
  const hasAny =
    (work_mode && work_mode.mode !== "unknown") ||
    (contract_types && contract_types.length > 0) ||
    salary;
  if (!hasAny) return null;
  return (
    <div className="bg-white/85 backdrop-blur-md rounded-xl border border-white/60 shadow-sm p-4 sm:p-5">
      <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-3">
        Infos de l&apos;offre
      </h3>
      <div className="flex flex-wrap gap-2">
        {work_mode && work_mode.mode !== "unknown" && (
          <span
            className={`px-3 py-1.5 rounded-full text-xs font-medium border ${
              work_mode.mode === "remote"
                ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                : work_mode.mode === "hybrid"
                ? "bg-blue-50 text-blue-700 border-blue-200"
                : "bg-slate-100 text-slate-700 border-slate-200"
            }`}
            title={work_mode.evidence || ""}
          >
            {work_mode.icon} {work_mode.label}
          </span>
        )}
        {contract_types &&
          contract_types.map((c) => (
            <span
              key={c}
              className="px-3 py-1.5 rounded-full bg-cyan-50 text-cyan-700 border border-cyan-200 text-xs font-medium"
            >
              📋 {c}
            </span>
          ))}
        {salary && (
          <span
            className="px-3 py-1.5 rounded-full bg-pink-50 text-pink-800 border border-pink-200 text-xs font-medium"
            title={salary.raw}
          >
            💰 {salary.formatted} {salary.period_label}
          </span>
        )}
      </div>
    </div>
  );
}

function ScoreCard({ report, meta }) {
  const { score, details } = report;
  const verdict =
    score >= 70
      ? "Excellent alignement"
      : score >= 40
      ? "Alignement moyen"
      : "Alignement faible";
  const color =
    score >= 70
      ? "text-green-600"
      : score >= 40
      ? "text-amber-600"
      : "text-red-600";
  const stroke = score >= 70 ? "#22c55e" : score >= 40 ? "#f59e0b" : "#ef4444";
  return (
    <div className="bg-white/85 backdrop-blur-md rounded-xl border border-white/60 shadow-sm p-6">
      <div className="flex flex-col sm:flex-row items-center gap-6">
        <div className="relative w-32 h-32 shrink-0">
          <svg viewBox="0 0 36 36" className="w-full h-full -rotate-90">
            <circle
              cx="18"
              cy="18"
              r="15.9"
              fill="none"
              stroke="#e2e8f0"
              strokeWidth="3"
            />
            <circle
              cx="18"
              cy="18"
              r="15.9"
              fill="none"
              stroke={stroke}
              strokeWidth="3"
              strokeDasharray={`${score} 100`}
              strokeLinecap="round"
            />
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className={`text-2xl font-bold ${color}`}>{score}%</span>
            <span className="text-[10px] text-slate-500 uppercase tracking-wide">
              correspondance
            </span>
          </div>
        </div>
        <div className="flex-1 text-center sm:text-left space-y-2">
          <p className={`text-lg font-semibold ${color}`}>{verdict}</p>
          <p className="text-sm text-slate-700">
            <strong>{details.skills_matched}</strong> competences sur{" "}
            <strong>{details.skills_total}</strong> recherchees dans l&apos;offre
            sont presentes dans ton CV.
          </p>
          {meta && (
            <p className="text-xs text-slate-400">
              CV analyse : {meta.cv_length} caracteres ·{" "}
              {meta.cv_skills_count} Compétences détectées
            </p>
          )}
        </div>
      </div>
    </div>
  );
}

function SectionsBreakdown({ items }) {
  const max = Math.max(...items.map((i) => i.count), 1);
  return (
    <div className="bg-white/85 backdrop-blur-md rounded-xl border border-white/60 shadow-sm p-4 sm:p-6">
      <h2 className="text-lg font-semibold mb-3">Analyse par section</h2>
      <div className="space-y-3">
        {items.map((s) => (
          <div key={s.key}>
            <div className="flex justify-between text-sm mb-1">
              <span className="font-medium text-slate-700">{s.label}</span>
              <span className="text-slate-500">
                {s.count} skill{s.count > 1 ? "s" : ""} de l&apos;offre
              </span>
            </div>
            <div className="h-2 bg-slate-100 rounded-full overflow-hidden mb-1">
              <div
                className="h-full bg-blue-500"
                style={{ width: `${(s.count / max) * 100}%` }}
              />
            </div>
            {s.skills_found.length > 0 && (
              <ul className="flex flex-wrap gap-1 mt-1">
                {s.skills_found.map((sk) => (
                  <li
                    key={sk}
                    className="px-2 py-0.5 rounded-full bg-blue-50 text-blue-700 text-xs"
                  >
                    {sk}
                  </li>
                ))}
              </ul>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

function EducationCard({ career }) {
  return (
    <div className="bg-white/85 backdrop-blur-md rounded-xl border border-white/60 shadow-sm p-4 sm:p-6 space-y-4">
      <div className="flex items-center justify-between flex-wrap gap-2">
        <h2 className="text-lg font-semibold">Formation détectée</h2>
        <div className="text-sm text-slate-500">
          {career.count_diplomas} formation{career.count_diplomas > 1 ? "s" : ""}
        </div>
      </div>
      <ul className="space-y-2">
        {career.education.map((e, i) => (
          <li
            key={i}
            className="flex items-start gap-3 p-3 rounded-lg bg-white/70 border border-slate-100"
          >
            <div className="w-2 h-2 rounded-full bg-cyan-500 mt-2 shrink-0" />
            <div className="min-w-0 flex-1">
              <p className="font-medium text-sm">{e.title}</p>
              {e.year && <p className="text-xs text-slate-500">{e.year}</p>}
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}

function SkillCard({ title, items, color }) {
  const palette = {
    green: "bg-green-50/90 border-green-200 text-green-800",
    amber: "bg-amber-50/90 border-amber-200 text-amber-800",
    slate: "bg-slate-50/90 border-slate-200 text-slate-700",
  }[color];
  return (
    <div
      className={`rounded-xl border backdrop-blur-md shadow-sm p-4 sm:p-5 ${palette}`}
    >
      <h3 className="font-semibold mb-3 text-sm">{title}</h3>
      {items.length === 0 ? (
        <p className="text-xs opacity-70">Aucune</p>
      ) : (
        <ul className="flex flex-wrap gap-2">
          {items.map((s) => (
            <li
              key={s}
              className="px-3 py-1 rounded-full bg-white/80 text-xs font-medium border border-current/20"
            >
              {s}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}