import { useMemo, useState } from "react";
import { loadHistory, deleteAnalysis, clearHistory } from "./storage";

export default function HistoryTab({ onReopen }) {
  const [tick, setTick] = useState(0);
  const history = useMemo(() => loadHistory(), [tick]);

  return (
    <div className="space-y-6">
      <div className="bg-white/85 backdrop-blur-md rounded-xl border border-white/60 shadow-sm p-4 sm:p-6">
        <div className="flex items-center justify-between flex-wrap gap-2">
          <h2 className="text-lg font-semibold">Historique</h2>
          <p className="text-sm text-slate-500">
            {history.length} analyse{history.length > 1 ? "s" : ""} sauvegardée{history.length > 1 ? "s" : ""}
          </p>
        </div>
      </div>

      {history.length === 0 ? (
        <div className="text-center py-16 text-slate-500 bg-white/70 backdrop-blur rounded-xl border border-white/60">
          <p className="text-lg font-medium">Aucune analyse pour l&apos;instant</p>
          <p className="text-sm mt-1">Lance ta première analyse depuis l&apos;onglet « Analyser ».</p>
        </div>
      ) : (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold">Toutes les analyses</h2>
            <button
              onClick={() => {
                if (confirm("Supprimer tout l'historique ?")) {
                  clearHistory();
                  setTick((t) => t + 1);
                }
              }}
              className="text-sm text-red-600 hover:text-red-700"
            >
              Vider l&apos;historique
            </button>
          </div>

          <ul className="space-y-3">
            {history.map((entry) => (
              <li key={entry.id} className="bg-white/85 backdrop-blur-md border border-white/60 shadow-sm rounded-xl p-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                <div className="min-w-0 flex-1">
                  <p className="font-medium truncate">{entry.jobTitle}</p>
                  <p className="text-xs text-slate-500 mt-1">
                    {new Date(entry.date).toLocaleString("fr-FR")} · {entry.cvFileName}
                  </p>
                </div>
                <div className="flex items-center gap-3 shrink-0">
                  <span className="font-bold text-indigo-600 text-lg">{entry.report.score}%</span>
                  <button onClick={() => onReopen(entry)} className="px-3 py-1.5 text-sm rounded-lg bg-indigo-600 text-white hover:bg-indigo-700 shadow">
                    Ouvrir
                  </button>
                  <button
                    onClick={() => { deleteAnalysis(entry.id); setTick((t) => t + 1); }}
                    className="px-2 py-1.5 text-sm rounded-lg text-slate-500 hover:bg-white/60"
                    title="Supprimer"
                  >
                    ✕
                  </button>
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}