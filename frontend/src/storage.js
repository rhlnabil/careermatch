const KEY = "careermatch_history_v1";
const MAX_ENTRIES = 50;

export function loadHistory() {
  try {
    return JSON.parse(localStorage.getItem(KEY) || "[]");
  } catch {
    return [];
  }
}

export function saveAnalysis(entry) {
  const history = loadHistory();
  history.unshift(entry);
  const trimmed = history.slice(0, MAX_ENTRIES);
  localStorage.setItem(KEY, JSON.stringify(trimmed));
  return trimmed;
}

export function deleteAnalysis(id) {
  const history = loadHistory().filter((e) => e.id !== id);
  localStorage.setItem(KEY, JSON.stringify(history));
  return history;
}

export function clearHistory() {
  localStorage.removeItem(KEY);
  return [];
}

export function buildEntry({ file, job, report, recommendations, meta }) {
  const firstLine = (job || "").trim().split("\n").find((l) => l.trim()) || "";
  return {
    id: String(Date.now()),
    date: new Date().toISOString(),
    cvFileName: file?.name || "cv.pdf",
    jobTitle: firstLine.slice(0, 80) || "Offre sans titre",
    jobText: job,
    report,
    recommendations: recommendations || [],
    meta: meta || null,
  };
}