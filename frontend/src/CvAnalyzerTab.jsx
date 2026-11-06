import { useState } from "react";

const API = "http://localhost:8000";

export default function CvAnalyzerTab() {
  const [file, setFile] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleAnalyze() {
    setError("");
    setResult(null);
    setLoading(true);
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 30000);
    try {
      const form = new FormData();
      form.append("cv", file);
      const res = await fetch(`${API}/api/analyze-cv`, {
        method: "POST", body: form, signal: controller.signal,
      });
      const data = await res.json();
      if (data.error) throw new Error(data.error);
      setResult(data);
    } catch (e) {
      if (e.name === "AbortError") setError("Timeout 30s.");
      else setError(e.message || "Erreur inconnue");
    } finally {
      clearTimeout(timeoutId);
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="bg-white/85 backdrop-blur-md rounded-xl border border-white/60 shadow-sm p-4 sm:p-6">
        <h2 className="text-lg font-semibold mb-2">Analyse ton CV</h2>
        <p className="text-sm text-slate-600 mb-4">
          Découvre ton score, tes points forts et tes axes d&apos;amélioration.
        </p>
        <input
          type="file"
          accept="application/pdf"
          onChange={(e) => setFile(e.target.files[0])}
          className="block w-full text-sm file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:bg-emerald-600 file:text-white hover:file:bg-emerald-700 mb-4"
        />
        {file && <p className="text-xs text-slate-500 truncate mb-4">{file.name}</p>}
        <button
          onClick={handleAnalyze}
          disabled={!file || loading}
          className="px-6 py-2.5 rounded-lg bg-emerald-600 text-white font-semibold shadow disabled:opacity-40 disabled:cursor-not-allowed hover:bg-emerald-700"
        >
          {loading ? "Analyse..." : "Analyser mon CV"}
        </button>
        {error && <div className="mt-4 bg-red-50 border border-red-200 text-red-700 p-4 rounded-lg text-sm">{error}</div>}
      </div>

      {result && <CvReport result={result} />}
    </div>
  );
}

function CvReport({ result }) {
  const { score, contact, stats, sections, skills_by_category, languages, education, strengths, improvements, skills_count, quality, radar } = result;
  const stroke = score.total >= 70 ? "#22c55e" : score.total >= 40 ? "#f59e0b" : "#ef4444";
  const textColor = score.total >= 70 ? "text-green-600" : score.total >= 40 ? "text-amber-600" : "text-red-600";

  return (
    <div className="space-y-6">
      <div className="bg-white/85 backdrop-blur-md rounded-xl border border-white/60 shadow-sm p-6 flex flex-col sm:flex-row items-center gap-6">
        <div className="relative w-32 h-32 shrink-0">
          <svg viewBox="0 0 36 36" className="w-full h-full -rotate-90">
            <circle cx="18" cy="18" r="15.9" fill="none" stroke="#e2e8f0" strokeWidth="3" />
            <circle cx="18" cy="18" r="15.9" fill="none" stroke={stroke} strokeWidth="3" strokeDasharray={`${score.total} 100`} strokeLinecap="round" />
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className={`text-2xl font-bold ${textColor}`}>{score.total}</span>
            <span className="text-[10px] text-slate-500 uppercase tracking-wide">score CV</span>
          </div>
        </div>
        <div className="flex-1 grid grid-cols-2 gap-3 w-full">
          <SubScore label="Structure" value={score.structure} />
          <SubScore label="Coordonnées" value={score.contact} />
          <SubScore label="Densité technique" value={score.skills} />
          <SubScore label="Longueur" value={score.length} />
        </div>
      </div>

      <div className="bg-white/85 backdrop-blur-md rounded-xl border border-white/60 shadow-sm p-4 sm:p-6">
        <h3 className="font-semibold mb-3">Coordonnées détectées</h3>
        <div className="grid sm:grid-cols-2 gap-2 text-sm">
          <ContactRow label="Email" value={contact.email} />
          <ContactRow label="Téléphone" value={contact.phone} />
          <ContactRow label="LinkedIn" value={contact.linkedin ? `linkedin.com/in/${contact.linkedin}` : ""} />
          <ContactRow label="Ville" value={contact.city} />
        </div>
      </div>

      <div className="bg-white/85 backdrop-blur-md rounded-xl border border-white/60 shadow-sm p-4 sm:p-6">
        <h3 className="font-semibold mb-3">Statistiques</h3>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center">
          <StatBox value={stats.characters} label="caractères" />
          <StatBox value={stats.words} label="mots" />
          <StatBox value={stats.lines} label="lignes" />
          <StatBox value={`${stats.reading_time_min} min`} label="lecture" />
        </div>
      </div>

      <div className="bg-white/85 backdrop-blur-md rounded-xl border border-white/60 shadow-sm p-4 sm:p-6">
        <h3 className="font-semibold mb-3">Sections détectées</h3>
        <div className="flex flex-wrap gap-2">
          {sections.found.map((s) => (
            <span key={s} className="px-3 py-1 rounded-full bg-green-50 text-green-700 border border-green-200 text-xs font-medium">✓ {s}</span>
          ))}
          {sections.missing.map((s) => (
            <span key={s} className="px-3 py-1 rounded-full bg-red-50 text-red-700 border border-red-200 text-xs font-medium">✗ {s}</span>
          ))}
        </div>
      </div>

      {radar && (
        <div className="bg-white/85 backdrop-blur-md rounded-xl border border-white/60 shadow-sm p-4 sm:p-6">
          <h3 className="font-semibold mb-3">Répartition des compétences</h3>
          <RadarChart data={radar.percentages} />
        </div>
      )}

      {Object.keys(skills_by_category).length > 0 && (
        <div className="bg-white/85 backdrop-blur-md rounded-xl border border-white/60 shadow-sm p-4 sm:p-6">
          <h3 className="font-semibold mb-3">Compétences techniques <span className="text-slate-400 text-sm">({skills_count})</span></h3>
          <div className="space-y-3">
            {Object.entries(skills_by_category).map(([cat, items]) => (
              <div key={cat}>
                <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-1">{cat}</p>
                <ul className="flex flex-wrap gap-1.5">
                  {items.map((s) => (
                    <li key={s} className="px-2.5 py-0.5 rounded-full bg-indigo-50 text-indigo-700 border border-indigo-200 text-xs">{s}</li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>
      )}

      {languages.length > 0 && (
        <div className="bg-white/85 backdrop-blur-md rounded-xl border border-white/60 shadow-sm p-4 sm:p-6">
          <h3 className="font-semibold mb-3">Langues</h3>
          <ul className="flex flex-wrap gap-2">
            {languages.map((l) => (
              <li key={l} className="px-3 py-1 rounded-full bg-slate-100 text-slate-700 border border-slate-200 text-xs font-medium">{l}</li>
            ))}
          </ul>
        </div>
      )}

      {education.length > 0 && (
        <div className="bg-white/85 backdrop-blur-md rounded-xl border border-white/60 shadow-sm p-4 sm:p-6">
          <h3 className="font-semibold mb-3">Formation</h3>
          <ul className="space-y-2">
            {education.map((e, i) => (
              <li key={i} className="p-3 rounded-lg bg-emerald-50/90 border border-emerald-100">
                <p className="text-sm font-medium">{e.title}</p>
                {e.year && <p className="text-xs text-slate-500">{e.year}</p>}
              </li>
            ))}
          </ul>
        </div>
      )}

      {quality && quality.length > 0 && (
        <div className="bg-white/85 backdrop-blur-md rounded-xl border border-white/60 shadow-sm p-4 sm:p-6">
          <h3 className="font-semibold mb-3">Qualité de forme</h3>
          <ul className="space-y-1.5 text-sm text-slate-700">
            {quality.map((q, i) => (
              <li key={i} className="flex gap-2"><span className="text-amber-600">⚠</span><span>{q}</span></li>
            ))}
          </ul>
        </div>
      )}

      <div className="grid md:grid-cols-2 gap-4 sm:gap-6">
        <div className="bg-green-50/90 backdrop-blur-md rounded-xl border border-green-200 shadow-sm p-4 sm:p-5">
          <h3 className="font-semibold text-green-800 mb-3">✓ Points forts</h3>
          {strengths.length === 0 ? <p className="text-sm text-green-700">Aucun point fort détecté.</p> : (
            <ul className="space-y-1.5 text-sm text-green-900">{strengths.map((s, i) => <li key={i}>• {s}</li>)}</ul>
          )}
        </div>
        <div className="bg-amber-50/90 backdrop-blur-md rounded-xl border border-amber-200 shadow-sm p-4 sm:p-5">
          <h3 className="font-semibold text-amber-800 mb-3">→ À améliorer</h3>
          {improvements.length === 0 ? <p className="text-sm text-amber-700">Rien à signaler !</p> : (
            <ul className="space-y-1.5 text-sm text-amber-900">{improvements.map((s, i) => <li key={i}>• {s}</li>)}</ul>
          )}
        </div>
      </div>
    </div>
  );
}

function RadarChart({ data }) {
  const entries = Object.entries(data).filter(([, v]) => v > 0);
  if (entries.length < 3) return <p className="text-sm text-slate-500">Pas assez de catégories pour le radar.</p>;
  const size = 240, cx = size / 2, cy = size / 2, radius = 80, n = entries.length;
  const angles = entries.map((_, i) => (Math.PI * 2 * i) / n - Math.PI / 2);
  const points = entries.map(([, value], i) => {
    const r = (value / 100) * radius;
    return [cx + r * Math.cos(angles[i]), cy + r * Math.sin(angles[i])];
  });
  const polygon = points.map((p) => p.join(",")).join(" ");
  const gridLevels = [0.25, 0.5, 0.75, 1];
  return (
    <div className="flex flex-col items-center">
      <svg viewBox={`0 0 ${size} ${size}`} className="w-full max-w-xs">
        {gridLevels.map((level, idx) => (
          <polygon key={idx} points={entries.map((_, i) => {
            const r = level * radius;
            return `${cx + r * Math.cos(angles[i])},${cy + r * Math.sin(angles[i])}`;
          }).join(" ")} fill="none" stroke="#e2e8f0" strokeWidth="1" />
        ))}
        {angles.map((a, i) => (
          <line key={i} x1={cx} y1={cy} x2={cx + radius * Math.cos(a)} y2={cy + radius * Math.sin(a)} stroke="#e2e8f0" strokeWidth="1" />
        ))}
        <polygon points={polygon} fill="rgba(79,70,229,0.25)" stroke="#4f46e5" strokeWidth="2" />
        {points.map((p, i) => <circle key={i} cx={p[0]} cy={p[1]} r="3" fill="#4f46e5" />)}
        {entries.map(([label, value], i) => {
          const labelR = radius + 22;
          const x = cx + labelR * Math.cos(angles[i]);
          const y = cy + labelR * Math.sin(angles[i]);
          return (
            <g key={label}>
              <text x={x} y={y} fontSize="9" textAnchor="middle" dominantBaseline="middle" fill="#475569">{label}</text>
              <text x={x} y={y + 10} fontSize="8" textAnchor="middle" fill="#94a3b8">{value}%</text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}

function SubScore({ label, value }) {
  const color = value >= 70 ? "bg-green-500" : value >= 40 ? "bg-amber-500" : "bg-red-500";
  return (
    <div>
      <div className="flex justify-between text-xs mb-1">
        <span className="text-slate-600">{label}</span>
        <span className="font-semibold">{value}%</span>
      </div>
      <div className="h-2 bg-slate-200 rounded-full overflow-hidden">
        <div className={`h-full ${color}`} style={{ width: `${value}%` }} />
      </div>
    </div>
  );
}

function ContactRow({ label, value }) {
  return (
    <div className="flex justify-between gap-2 py-1">
      <span className="text-slate-500">{label}</span>
      <span className={`font-medium truncate ${value ? "text-slate-800" : "text-red-500"}`}>{value || "Non détecté"}</span>
    </div>
  );
}

function StatBox({ value, label }) {
  return (
    <div className="p-3 bg-white/70 rounded-lg border border-slate-100">
      <p className="text-lg font-bold text-slate-800">{value}</p>
      <p className="text-xs text-slate-500">{label}</p>
    </div>
  );
}