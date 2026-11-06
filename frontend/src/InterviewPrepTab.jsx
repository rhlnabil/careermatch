import { useState } from "react";

const API = "http://localhost:8000";

export default function InterviewPrepTab({ cvFile, jobText, hasAnalysis, onGoToAnalyze }) {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleGenerate() {
    setError("");
    setResult(null);
    setLoading(true);
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 30000);
    try {
      const form = new FormData();
      form.append("cv", cvFile);
      form.append("job", jobText);
      const res = await fetch(`${API}/api/interview-prep`, {
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

  const canGenerate = cvFile && jobText && jobText.trim().length > 20 && !loading;

  return (
    <div className="space-y-6">
      <div className="bg-white/85 backdrop-blur-md rounded-xl border border-white/60 shadow-sm p-4 sm:p-6">
        <h2 className="text-lg font-semibold mb-2">Préparation entretien</h2>
        <p className="text-sm text-slate-600 mb-4">
          10 questions probables + conseils de réponse pour cette offre.
        </p>
        {!canGenerate && (
          <div className="bg-amber-50 border border-amber-200 text-amber-800 p-4 rounded-lg text-sm mb-4">
            {!hasAnalysis ? (
              <>Lance d&apos;abord une analyse.{" "}
                <button onClick={onGoToAnalyze} className="underline font-medium">Aller à l&apos;analyse</button>
              </>
            ) : "CV ou offre manquant."}
          </div>
        )}
        <button
          onClick={handleGenerate}
          disabled={!canGenerate}
          className="px-6 py-2.5 rounded-lg bg-pink-600 text-white font-semibold shadow disabled:opacity-40 disabled:cursor-not-allowed hover:bg-pink-700"
        >
          {loading ? "Génération..." : "Générer les questions"}
        </button>
        {error && <div className="mt-4 bg-red-50 border border-red-200 text-red-700 p-4 rounded-lg text-sm">{error}</div>}
      </div>

      {result && (
        <div className="space-y-3">
          {result.questions.map((q, i) => (
            <QuestionCard key={i} index={i} item={q} />
          ))}
        </div>
      )}
    </div>
  );
}

function QuestionCard({ index, item }) {
  const [open, setOpen] = useState(false);
  const colors = {
    Technique: "bg-blue-50/90 border-blue-200 text-blue-800",
    Apprentissage: "bg-amber-50/90 border-amber-200 text-amber-800",
    Expérience: "bg-emerald-50/90 border-emerald-200 text-emerald-800",
    Motivation: "bg-indigo-50/90 border-indigo-200 text-indigo-800",
    Comportemental: "bg-purple-50/90 border-purple-200 text-purple-800",
  };
  const color = colors[item.category] || "bg-white/85 border-slate-200 text-slate-800";
  return (
    <div className={`rounded-xl border backdrop-blur-md shadow-sm p-4 ${color}`}>
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1">
          <span className="text-xs font-semibold uppercase opacity-70">Q{index + 1} · {item.category}</span>
          <p className="font-medium text-sm mt-1">{item.question}</p>
        </div>
        <button onClick={() => setOpen(!open)} className="text-xs underline shrink-0">
          {open ? "Masquer" : "Conseil"}
        </button>
      </div>
      {open && (
        <div className="mt-3 pt-3 border-t border-current/20 text-sm">
          <p className="font-semibold mb-1">💡 Conseil</p>
          <p>{item.advice}</p>
        </div>
      )}
    </div>
  );
}