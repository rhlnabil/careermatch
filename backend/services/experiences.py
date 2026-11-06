import re
import unicodedata

_nlp = None


def _get_nlp():
    global _nlp
    if _nlp is None:
        try:
            import spacy

            _nlp = spacy.load("fr_core_news_sm")
            print("[experiences] spaCy charge (fr_core_news_sm)")
        except Exception as e:
            print(f"[experiences] spaCy indisponible, fallback regex : {e}")
            _nlp = False
    return _nlp


def _strip_accents(s):
    return "".join(
        c for c in unicodedata.normalize("NFD", s)
        if unicodedata.category(c) != "Mn"
    )


def _normalize(s):
    return re.sub(r"\s+", " ", _strip_accents(s.lower())).strip()


MONTHS = (
    r"(?:janvier|janv|fevrier|fevr|février|févr|mars|avril|avr|mai|juin|"
    r"juillet|juil|aout|août|septembre|sept|octobre|oct|novembre|nov|"
    r"decembre|décembre|déc|dec)"
)

ONGOING_WORDS = (
    r"(?:present|présent|presente|présente|aujourd'hui|aujourd|"
    r"actuel|actuelle|actuellement|en cours|current)"
)

DATE_RANGE = re.compile(
    r"(?:(?:" + MONTHS + r")\.?\s*)?"
    r"(\d{4}|\d{1,2}[/-]\d{4})"
    r"\s*[-–—]\s*"
    r"(?:(?:" + MONTHS + r")\.?\s*)?"
    r"(\d{4}|\d{1,2}[/-]\d{4}|" + ONGOING_WORDS + r")",
    re.IGNORECASE,
)

SINCE_DATE = re.compile(r"\bdepuis\s+(\d{4})", re.IGNORECASE)

SINGLE_DATE = re.compile(
    r"(?:(?:" + MONTHS + r")\.?\s*)?(\d{4}|\d{1,2}[/-]\d{4})",
    re.IGNORECASE,
)

DIPLOMA_START = re.compile(
    r"^(master|licence|bachelor|doctorat|phd|these|bts|dut|"
    r"baccalaureat|ingenieur|cycle|diplome|deug|cap\b|bep\b|"
    r"mba|msc|bsc|prepa|classe prepa|bac\b)",
    re.IGNORECASE,
)

JOB_KEYWORDS = re.compile(
    r"\b(stage|stagiaire|alternance|alternant|apprenti|apprentissage|"
    r"cdi|cdd|freelance|interim|"
    r"developpeur|developer|developpeuse|"
    r"ingenieur|engineer|"
    r"manager|chef|directeur|directrice|responsable|"
    r"assistant|assistante|consultant|consultante|"
    r"analyste|analyst|technicien|technicienne|technique|"
    r"comptable|avocat|juriste|medecin|infirmier|infirmiere|"
    r"professeur|enseignant|formateur|formatrice|"
    r"commercial|commerciale|vendeur|vendeuse|"
    r"secretaire|receptionniste|"
    r"architecte|designer|"
    r"intern|trainee|junior|senior|lead|"
    r"support|it|web|data|fullstack|full.stack|frontend|backend)\b",
    re.IGNORECASE,
)

SECTION_HEADERS = {
    "experience": [
        "experience", "experiences", "experiences professionnelles",
        "parcours professionnel", "parcours", "emplois",
        "work experience", "stages", "stages et experiences",
        "experiences professionnelles et stages",
    ],
    "education": [
        "formation", "formations", "education", "diplomes", "diplome",
        "cursus", "scolarite", "etudes", "parcours scolaire",
        "formations et diplomes",
    ],
    "projects": ["projets", "projects", "realisations"],
    "skills": [
        "competences", "competences techniques", "skills",
        "expertises", "technologies",
    ],
    "languages": ["langues", "languages"],
}


def split_sections(text):
    if not text:
        return {}
    lines = text.split("\n")
    sections = {"header": []}
    current = "header"

    for line in lines:
        stripped = line.strip()
        if not stripped:
            sections.setdefault(current, []).append("")
            continue

        norm = _normalize(stripped)
        norm_clean = re.sub(r"[^\w\s]", "", norm).strip()

        matched = None
        if len(stripped) < 60 and len(norm_clean.split()) <= 5:
            for sec, aliases in SECTION_HEADERS.items():
                for alias in aliases:
                    if norm_clean == alias or norm_clean.startswith(alias + " "):
                        matched = sec
                        break
                if matched:
                    break

        if matched:
            current = matched
            sections.setdefault(current, [])
        else:
            sections.setdefault(current, []).append(stripped)

    return {k: "\n".join(v).strip() for k, v in sections.items() if v}


def _extract_year(raw):
    if not raw:
        return None
    m = re.search(r"(\d{4})", raw)
    return int(m.group(1)) if m else None


def _is_ongoing(raw):
    if not raw:
        return False
    return bool(re.search(ONGOING_WORDS, _strip_accents(raw.lower())))


def _parse_date_from_text(text):
    m = DATE_RANGE.search(text)
    if m:
        return (
            _extract_year(m.group(1)),
            _extract_year(m.group(2)),
            _is_ongoing(m.group(2)),
        )
    m = SINCE_DATE.search(text)
    if m:
        return (_extract_year(m.group(1)), None, True)
    return None


def _extract_companies_with_spacy(text):
    nlp = _get_nlp()
    if not nlp:
        return []
    doc = nlp(text[:4000])
    return [
        ent.text
        for ent in doc.ents
        if ent.label_ == "ORG"
        or (ent.label_ == "PER" and len(ent.text.split()) >= 2)
    ]


def _merge_multiline_entries(lines):
    """
    Fusionne les lignes qui appartiennent au meme bloc 'titre'.
    Ex: 'Juin 2026 – Aout' + '2026' -> 'Juin 2026 – Aout 2026'
    """
    merged = []
    i = 0
    while i < len(lines):
        line = lines[i]
        need_merge = False
        # Cas : "Juin 2026 – Aout" sans l'annee finale
        if re.search(r"[-–—]\s*(?:" + MONTHS + r")\.?\s*$", line, re.IGNORECASE):
            need_merge = True
        # Cas : une date sans fin, et ligne suivante courte sans '|'
        elif (
            re.search(r"(?:" + MONTHS + r")\.?\s*\d{4}\s*[-–—]\s*\d{0,4}$", line, re.IGNORECASE)
            and not DATE_RANGE.search(line)
        ):
            if i + 1 < len(lines):
                nxt = lines[i + 1].strip()
                if len(nxt) < 40 and "|" not in nxt:
                    need_merge = True

        if need_merge and i + 1 < len(lines):
            merged.append(line + " " + lines[i + 1])
            i += 2
        else:
            merged.append(line)
            i += 1
    return merged


def _parse_title_company(line):
    """
    Format prioritaire :
      'Titre | Entreprise – Sous-entreprise | Ville • Date'
      → titre = part[0], entreprise = part[1] coupe au premier ' – '
    Fallback : split sur ' — ' / ' – ' si pas de '|'
    """
    clean = re.sub(r"\s+", " ", line).strip()
    clean_no_date = DATE_RANGE.sub("", clean).strip(" -–—|•·,")

    if "|" in clean_no_date:
        parts = [p.strip() for p in clean_no_date.split("|") if p.strip()]
        if len(parts) >= 2:
            title = parts[0][:150]
            company_raw = parts[1]
            company = re.split(r"\s+[-–—]\s+", company_raw, maxsplit=1)[0].strip()[:80]
            return title, company
        elif len(parts) == 1:
            return parts[0][:150], ""

    parts = re.split(r"\s*[—–]\s*|\s+-\s+", clean_no_date, maxsplit=1)
    title = parts[0].strip()[:150] if parts else ""
    company = ""
    if len(parts) > 1:
        company = re.split(r"\s*[|,]\s*", parts[1], maxsplit=1)[0].strip()[:80]
    return title, company


def extract_experiences(text):
    if not text:
        return []
    sections = split_sections(text)

    if "experience" in sections and sections["experience"]:
        section_text = sections["experience"]
    else:
        section_text = text

    raw_lines = [l.strip() for l in section_text.split("\n") if l.strip()]
    lines = _merge_multiline_entries(raw_lines)

    companies_spacy = _extract_companies_with_spacy(section_text)
    experiences = []
    CURRENT_YEAR = 2025

    for i, line in enumerate(lines):
        # Skip les descriptions
        if line.startswith(("•", "-", "*", "–")):
            continue
        if len(line) > 300:
            continue

        norm_line = _normalize(line)
        if DIPLOMA_START.match(norm_line):
            continue

        is_stage = bool(re.search(
            r"\b(stage|stagiaire|alternance|alternant|apprenti|apprentissage|intern|trainee|cdi|cdd)\b",
            norm_line,
        ))
        has_job_title = bool(JOB_KEYWORDS.search(norm_line))
        date_info = _parse_date_from_text(line)

        if not date_info:
            for j in range(max(0, i - 1), min(len(lines), i + 2)):
                if j == i:
                    continue
                date_info = _parse_date_from_text(lines[j])
                if date_info:
                    break

        if not date_info:
            continue

        if not (is_stage or has_job_title):
            continue

        start, end, ongoing = date_info
        if start and start > CURRENT_YEAR + 1:
            continue

        title, company = _parse_title_company(line)

        if not title or len(title) < 5:
            for j in range(i - 1, max(-1, i - 3), -1):
                if j < 0:
                    continue
                prev = lines[j]
                if not prev or _parse_date_from_text(prev):
                    continue
                if JOB_KEYWORDS.search(_normalize(prev)):
                    t, c = _parse_title_company(prev)
                    if t and len(t) >= 5:
                        title = t
                        if not company and c:
                            company = c
                    break

        if not title or len(title) < 3:
            title = line[:150]

        if not company:
            window = " ".join(lines[max(0, i - 1): min(len(lines), i + 2)])
            for c in companies_spacy:
                if c.lower() in window.lower() and c.lower() != title.lower():
                    company = c[:80]
                    break

        experiences.append({
            "title": title[:150],
            "company": company,
            "start_year": start,
            "end_year": end,
            "ongoing": ongoing,
            "duration_years": (
                round(CURRENT_YEAR - start, 1) if ongoing and start
                else round((end - start), 1) if end and start and end != start else 0
            ),
        })

    # ============ DEDUP INTELLIGENTE ============
    # On garde les entrees uniques par (entreprise + annees + titre tronque)
    # Cela evite de supprimer 2 stages differents qui ont le meme titre
    seen = set()
    unique = []
    for e in experiences:
        company_key = (e["company"] or "").lower().strip()
        title_key = e["title"][:40].lower().strip()

        if company_key:
            k = ("company", company_key, e["start_year"], e["end_year"])
        else:
            k = ("title", title_key, e["start_year"], e["end_year"])

        if k in seen:
            continue
        seen.add(k)
        unique.append(e)

    unique.sort(key=lambda x: (-(x["start_year"] or 0), -(x["end_year"] or 0)))
    return unique[:10]


def extract_education(text):
    if not text:
        return []
    sections = split_sections(text)

    if "education" not in sections or not sections["education"]:
        return []

    edu_text = sections["education"]
    lines = [l.strip() for l in edu_text.split("\n") if l.strip()]
    lines = _merge_multiline_entries(lines)

    entries_lines = []
    current = []
    for line in lines:
        norm = _normalize(line)
        norm_clean = re.sub(r"[^\w\s]", "", norm).strip()
        is_new = bool(DIPLOMA_START.match(norm_clean))

        if is_new and current:
            entries_lines.append(current)
            current = [line]
        elif not current:
            current = [line]
        else:
            current.append(line)
    if current:
        entries_lines.append(current)

    entries = []
    for block in entries_lines:
        joined = " ".join(block)

        period = None
        range_m = DATE_RANGE.search(joined)
        if range_m:
            start = _extract_year(range_m.group(1))
            end = _extract_year(range_m.group(2))
            ongoing = _is_ongoing(range_m.group(2))
            if ongoing and start:
                period = f"{start} - present"
            elif start and end and start != end:
                period = f"{start} - {end}"
            elif end:
                period = str(end)
            elif start:
                period = str(start)
        else:
            single = SINGLE_DATE.search(joined)
            if single:
                period = str(_extract_year(single.group(1)))

        title = DATE_RANGE.sub("", joined)
        title = re.sub(r"\(\s*\)", "", title)
        title = re.sub(r"\s+", " ", title).strip(" -–—,;:()")
        if len(title) < 10:
            title = joined[:220]

        entries.append({
            "title": title[:220],
            "year": period,
        })

    return entries[:8]


def estimate_years_experience(experiences):
    if not experiences:
        return 0.0
    total = sum(e.get("duration_years", 0) or 0 for e in experiences)
    return round(min(total, 50), 1)


def build_career_summary(text):
    experiences = extract_experiences(text)
    education = extract_education(text)
    years = estimate_years_experience(experiences)
    return {
        "experiences": experiences,
        "education": education,
        "years_experience": years,
        "count_jobs": len(experiences),
        "count_diplomas": len(education),
    }