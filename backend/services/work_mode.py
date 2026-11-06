import re


REMOTE_PATTERNS = [
    r"\b(?:full[\s-]?remote|100\s*%\s*remote|télétravail\s+total|teletravail\s+total)\b",
    r"\b(?:télétravail|teletravail)\s+(?:complet|intégral|integral|possible|autorisé|autorise)\b",
    r"\bremote\s+(?:only|first|friendly|possible)\b",
    r"\b(?:entièrement|entierement)\s+(?:en\s+)?(?:télétravail|teletravail|remote)\b",
]

HYBRID_PATTERNS = [
    r"\bhybride?\b",
    r"\b(?:télétravail|teletravail)\s+(?:partiel|partielle)\b",
    r"\b(?:1|2|3|4)\s+jours?\s+(?:de\s+)?(?:télétravail|teletravail|remote)\b",
    r"\b(?:remote|télétravail|teletravail)\s+(?:\d\s+)?jours?\s+par\s+semaine\b",
    r"\bflexible?\s+(?:sur\s+)?(?:le\s+)?(?:lieu|présentiel|presentiel)\b",
]

ONSITE_PATTERNS = [
    r"\b(?:100\s*%\s*)?(?:sur[\s-]?site|présentiel|presentiel)\b",
    r"\b(?:entièrement|entierement)\s+(?:en\s+)?(?:présentiel|presentiel)\b",
    r"\b(?:pas\s+de\s+télétravail|pas\s+de\s+teletravail|aucun\s+télétravail)\b",
    r"\b(?:bureau|locaux)\s+(?:uniquement|seulement|obligatoire)\b",
]


def detect_work_mode(text: str) -> dict:
    """
    Detecte le mode de travail dans une offre.
    Retourne {mode, label, icon, confidence, evidence}
    """
    if not text:
        return _none_result()

    text_lower = text.lower()

    # 1. Remote en priorite (le plus specifique)
    for pattern in REMOTE_PATTERNS:
        m = re.search(pattern, text_lower, re.IGNORECASE)
        if m:
            return {
                "mode": "remote",
                "label": "Télétravail total",
                "icon": "🌍",
                "confidence": "high",
                "evidence": m.group(0).strip(),
            }

    # 2. Hybride
    for pattern in HYBRID_PATTERNS:
        m = re.search(pattern, text_lower, re.IGNORECASE)
        if m:
            return {
                "mode": "hybrid",
                "label": "Hybride",
                "icon": "🔀",
                "confidence": "high",
                "evidence": m.group(0).strip(),
            }

    # 3. Presentiel
    for pattern in ONSITE_PATTERNS:
        m = re.search(pattern, text_lower, re.IGNORECASE)
        if m:
            return {
                "mode": "onsite",
                "label": "Présentiel",
                "icon": "🏢",
                "confidence": "high",
                "evidence": m.group(0).strip(),
            }

    return _none_result()


def _none_result():
    return {
        "mode": "unknown",
        "label": "Non précisé",
        "icon": "❓",
        "confidence": "low",
        "evidence": "",
    }


# ============================================================
# BONUS — Détection type de contrat + salaire (feature #9)
# ============================================================

CONTRACT_PATTERNS = {
    "CDI": [r"\bcdi\b", r"\bcontrat\s+(?:à|a)\s+durée\s+indéterminée\b"],
    "CDD": [r"\bcdd\b", r"\bcontrat\s+(?:à|a)\s+durée\s+déterminée\b"],
    "Stage": [r"\bstage\b", r"\bstagiaire\b", r"\binternship\b"],
    "Alternance": [r"\balternance\b", r"\bapprentissage\b", r"\bcontrat\s+pro\b"],
    "Freelance": [r"\bfreelance\b", r"\bmission\b.*\b(?:tjm|jours?)\b"],
    "Intérim": [r"\bintérim\b", r"\binterim\b", r"\bmission\s+temporaire\b"],
    "VIE": [r"\bvie\b", r"\bvolontariat\s+international\b"],
}


def detect_contract_type(text: str) -> list:
    """Retourne la liste des types de contrat detectes."""
    if not text:
        return []
    text_lower = text.lower()
    found = []
    for contract, patterns in CONTRACT_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                found.append(contract)
                break
    return found


# Fourchettes : 30k, 30 k, 30 000, 35-45k, 35 000 - 45 000 €
SALARY_PATTERNS = [
    # "35-45k€" / "35 000 - 45 000 €" / "35k à 45k"
    r"(\d{2,3})\s*[\-–à]\s*(\d{2,3})\s*k(?:€|e| euros?)?",
    r"(\d{2,3})\s*k\s*[\-–à]\s*(\d{2,3})\s*k",
    # "35 000 - 45 000 €"
    r"(\d{2,3}\s*\d{3})\s*[\-–à]\s*(\d{2,3}\s*\d{3})\s*(?:€|euros?)",
    # "45k€" / "45 000 €" / "45000€"
    r"(\d{2,3})\s*k(?:€|e| euros?)",
    r"(\d{2,3}\s*\d{3})\s*(?:€|euros?)",
]

SALARY_PERIODS = {
    "annuel": r"\b(?:an|annuel|annuelle|brut|par\s+an)\b",
    "mensuel": r"\b(?:mois|mensuel|mensuelle|par\s+mois)\b",
    "journalier": r"\b(?:jour|journalier|tjm|par\s+jour)\b",
}


def detect_salary(text: str) -> dict:
    """
    Detecte une fourchette de salaire.
    Retourne {min, max, unit, period, raw, formatted} ou None
    """
    if not text:
        return None

    text_lower = text.lower()

    # Periode
    period = None
    for p, pattern in SALARY_PERIODS.items():
        if re.search(pattern, text_lower):
            period = p
            break

    for pattern in SALARY_PATTERNS:
        m = re.search(pattern, text_lower, re.IGNORECASE)
        if not m:
            continue

        raw = m.group(0)
        groups = m.groups()

        try:
            if len(groups) == 2:
                lo = _parse_amount(groups[0])
                hi = _parse_amount(groups[1])
                if lo and hi:
                    return _format_salary(lo, hi, period, raw)
            elif len(groups) == 1:
                val = _parse_amount(groups[0])
                if val:
                    return _format_salary(val, val, period, raw)
        except (ValueError, IndexError):
            continue

    return None


def _parse_amount(s: str) -> int | None:
    if not s:
        return None
    clean = re.sub(r"[^\d]", "", s)
    if not clean:
        return None
    val = int(clean)
    # Si < 1000, c'est probablement en k€ (35 -> 35000)
    if val < 1000:
        val *= 1000
    return val


def _format_salary(lo: int, hi: int, period: str | None, raw: str) -> dict:
    period_label = {
        "annuel": "brut/an",
        "mensuel": "brut/mois",
        "journalier": "/jour",
        None: "brut/an",
    }.get(period, "brut/an")

    if lo == hi:
        formatted = f"{lo // 1000} k€"
    else:
        formatted = f"{lo // 1000}–{hi // 1000} k€"

    return {
        "min": lo,
        "max": hi,
        "period": period or "annuel",
        "period_label": period_label,
        "formatted": formatted,
        "raw": raw.strip(),
    }


def extract_job_meta(text: str) -> dict:
    """Point d'entree : renvoie work_mode + contract_types + salary."""
    return {
        "work_mode": detect_work_mode(text),
        "contract_types": detect_contract_type(text),
        "salary": detect_salary(text),
    }