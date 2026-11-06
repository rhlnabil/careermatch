import { useState } from "react";

const API = "http://localhost:8000";

export default function CoverLetterTab({ cvFile, jobText, hasAnalysis, onGoToAnalyze }) {
  const [letter, setLetter] = useState(null);
  const [meta, setMeta] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [copied, setCopied] = useState(false);

  async function handleGenerate() {
    setError("");
    setLetter(null);
    setMeta(null);
    setLoading(true);
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 30000);
    try {
      const form = new FormData();
      form.append("cv", cvFile);
      form.append("job", jobText);
      const res = await fetch(`${API}/api/cover-letter`, {
        method: "POST", body: form, signal: controller.signal,
      });
      const data = await res.json();
      if (data.error) throw new Error(data.error);
      setLetter(data.letter);
      setMeta(data.meta);
    } catch (e) {
      if (e.name === "AbortError") setError("Timeout 30s.");
      else setError(e.message || "Erreur inconnue");
    } finally {
      clearTimeout(timeoutId);
      setLoading(false);
    }
  }

  async function handleCopy() {
    if (!letter) return;
    try {
      await navigator.clipboard.writeText(letter);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch { setError("Impossible de copier"); }
  }

  const canGenerate = cvFile && jobText && jobText.trim().length > 20 && !loading;

  return (
    <div className="space-y-6">
      <div className="bg-white/85 backdrop-blur-md rounded-xl border border-white/60 shadow-sm p-4 sm:p-6">
        <h2 className="text-lg font-semibold mb-2">Lettre de motivation</h2>
        <p className="text-sm text-slate-600 mb-4">
          Génère une lettre personnalisée à partir de ton CV et de l&apos;offre.
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
          className="px-6 py-2.5 rounded-lg bg-violet-600 text-white font-semibold shadow disabled:opacity-40 disabled:cursor-not-allowed hover:bg-violet-700"
        >
          {loading ? "Génération..." : "Générer la lettre"}
        </button>
        {error && <div className="mt-4 bg-red-50 border border-red-200 text-red-700 p-4 rounded-lg text-sm">{error}</div>}
      </div>

      {letter && (
        <div className="space-y-4">
          {meta && (
            <div className="flex flex-wrap gap-2 text-xs">
              {meta.job_title && <span className="px-3 py-1 rounded-full bg-violet-50 text-violet-700 border border-violet-200">Poste : {meta.job_title}</span>}
              {meta.company && <span className="px-3 py-1 rounded-full bg-violet-50 text-violet-700 border border-violet-200">Entreprise : {meta.company}</span>}
            </div>
          )}
          <div className="bg-white/90 backdrop-blur-md rounded-xl border border-white/60 shadow-sm p-6">
            <pre className="whitespace-pre-wrap font-sans text-sm leading-relaxed text-slate-800">{letter}</pre>
          </div>
          <div className="flex flex-wrap gap-3 justify-center">
            <button onClick={handleCopy} className="px-5 py-2.5 rounded-lg bg-slate-800 text-white font-semibold shadow hover:bg-slate-900">
              {copied ? "✓ Copié !" : "Copier le texte"}
            </button>
            <button onClick={handleGenerate} disabled={loading} className="px-5 py-2.5 rounded-lg bg-white/80 backdrop-blur border border-slate-300 text-slate-700 font-medium hover:bg-white">
              Régénérer
            </button>
          </div>
        </div>
      )}
    </div>
  );
}