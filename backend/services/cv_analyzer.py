import re
import unicodedata

from services.skills import (
    extract_skills,
    filter_technical_skills,
    get_skill_categories,
)
from services.experiences import split_sections, extract_education


def _strip_accents(s):
    return "".join(
        c for c in unicodedata.normalize("NFD", s)
        if unicodedata.category(c) != "Mn"
    )


CITIES = [
    "Casablanca", "Rabat", "Marrakech", "Fès", "Fes", "Tanger", "Agadir",
    "Meknès", "Meknes", "Oujda", "Kénitra", "Kenitra", "Salé", "Sale",
    "Tétouan", "Tetouan", "Paris", "Lyon", "Marseille", "Toulouse",
    "Bordeaux", "Lille", "Nantes", "Nice", "Strasbourg", "Montréal",
    "Montreal", "Québec", "Quebec", "Bruxelles", "Genève", "Geneve",
    "Tunis", "Alger", "Londres", "London", "Berlin", "Madrid", "Rome",
]


def _extract_contact(cv_text):
    email = ""
    phone = ""
    linkedin = ""
    city = ""

    m = re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", cv_text)
    if m:
        email = m.group(0)

    m = re.search(
        r"(?:\+?\d{1,3}[\s.-]?)?(?:\(?\d{1,3}\)?[\s.-]?){2,5}\d{2,4}",
        cv_text,
    )
    if m:
        candidate = m.group(0).strip()
        if len(re.sub(r"\D", "", candidate)) >= 8:
            phone = candidate

    m = re.search(
        r"linkedin(?:\.com/in/)?[\s:/]*([A-Za-z0-9_-]{3,})",
        cv_text,
        re.IGNORECASE,
    )
    if m:
        linkedin = m.group(1)

    lines = [l.strip() for l in cv_text.split("\n")[:8] if l.strip()]
    for line in lines:
        for c in CITIES:
            if re.search(r"\b" + re.escape(c) + r"\b", line, re.IGNORECASE):
                city = c
                break
        if city:
            break

    return {"email": email, "phone": phone, "linkedin": linkedin, "city": city}


LANGUAGE_PATTERNS = {
    "Français": r"\b(fran[cç]ais|french)\b",
    "Anglais": r"\b(anglais|english)\b",
    "Arabe": r"\b(arabe|arabic)\b",
    "Espagnol": r"\b(espagnol|spanish)\b",
    "Allemand": r"\b(allemand|german|deutsch)\b",
    "Italien": r"\b(italien|italian)\b",
    "Portugais": r"\b(portugais|portuguese)\b",
    "Chinois": r"\b(chinois|mandarin|chinese)\b",
    "Japonais": r"\b(japonais|japanese)\b",
    "Russe": r"\b(russe|russian)\b",
    "Néerlandais": r"\b(neerlandais|néerlandais|dutch)\b",
    "Turc": r"\b(turc|turkish)\b",
}


def _extract_languages(cv_text):
    languages = []
    for name, pattern in LANGUAGE_PATTERNS.items():
        if re.search(pattern, cv_text, re.IGNORECASE):
            languages.append(name)
    return languages


def _categorize_skills(cv_skills):
    skill_to_cat = get_skill_categories()
    grouped = {}
    for skill in cv_skills:
        cat = skill_to_cat.get(skill, "Autre")
        grouped.setdefault(cat, []).append(skill)
    for cat in grouped:
        grouped[cat] = sorted(grouped[cat])
    return dict(sorted(grouped.items(), key=lambda x: -len(x[1])))


def _compute_score(contact, sections, stats, technical_skills):
    expected = {"experience", "education", "skills"}
    found = set(sections.keys()) & expected
    structure_score = (len(found) / len(expected)) * 100

    contact_score = 0
    if contact["email"]:
        contact_score += 40
    if contact["phone"]:
        contact_score += 40
    if contact["linkedin"]:
        contact_score += 20

    skills_count = len(technical_skills)
    skills_score = min(skills_count / 20 * 100, 100)

    char_count = stats["characters"]
    if 3000 <= char_count <= 6000:
        length_score = 100
    elif char_count < 3000:
        length_score = (char_count / 3000) * 100
    else:
        length_score = max(0, 100 - (char_count - 6000) / 50)

    total = (
        0.30 * structure_score
        + 0.20 * contact_score
        + 0.30 * skills_score
        + 0.20 * length_score
    )

    return {
        "total": round(total, 1),
        "structure": round(structure_score, 1),
        "contact": round(contact_score, 1),
        "skills": round(skills_score, 1),
        "length": round(length_score, 1),
    }


def _build_feedback(contact, sections, stats, technical_skills, languages, education):
    strengths = []
    improvements = []

    if contact["email"] and contact["phone"]:
        strengths.append("Coordonnées complètes (email + téléphone)")
    else:
        if not contact["email"]:
            improvements.append("Ajoute ton adresse email en haut du CV")
        if not contact["phone"]:
            improvements.append("Ajoute ton numéro de téléphone")

    if contact["linkedin"]:
        strengths.append("Profil LinkedIn mentionné")
    else:
        improvements.append("Ajoute l'URL de ton profil LinkedIn")

    if contact["city"]:
        strengths.append(f"Ville identifiable : {contact['city']}")
    else:
        improvements.append("Précise ta ville en haut du CV")

    if "experience" in sections:
        strengths.append("Section 'Expériences' bien identifiée")
    else:
        improvements.append("Ajoute une section 'Expériences professionnelles' claire")

    if "education" in sections:
        strengths.append("Section 'Formation' bien identifiée")
    else:
        improvements.append("Ajoute une section 'Formation' claire")

    if "projects" in sections:
        strengths.append("Section 'Projets' présente")
    else:
        improvements.append("Ajoute une section 'Projets' avec tes réalisations")

    if "skills" in sections:
        strengths.append("Section 'Compétences' présente")
    else:
        improvements.append("Ajoute une section 'Compétences techniques' claire")

    if len(technical_skills) >= 20:
        strengths.append(f"Bonne densité technique ({len(technical_skills)} compétences)")
    elif len(technical_skills) >= 10:
        strengths.append(f"{len(technical_skills)} compétences techniques identifiées")
    else:
        improvements.append(
            f"Peu de compétences techniques détectées ({len(technical_skills)}) — objectif : 15+"
        )

    if len(languages) >= 2:
        strengths.append(f"Langues mentionnées : {', '.join(languages)}")
    elif len(languages) == 0:
        improvements.append("Ajoute une section 'Langues' (français, anglais...)")

    if len(education) >= 2:
        strengths.append(f"{len(education)} formations listées")
    elif len(education) == 0:
        improvements.append("Ajoute tes diplômes dans une section 'Formation'")

    if stats["characters"] > 7000:
        improvements.append(
            f"CV long ({stats['characters']} caractères) — essaie de condenser à 1 page"
        )
    elif stats["characters"] < 2000:
        improvements.append(
            f"CV court ({stats['characters']} caractères) — développe tes expériences"
        )

    return strengths, improvements


def _check_quality(cv_text):
    """Detecte les problemes de forme evidents dans le CV."""
    issues = []
    lines = cv_text.split("\n")

    double_spaces = sum(1 for l in lines if "  " in l and l.strip())
    if double_spaces > 5:
        issues.append(f"{double_spaces} lignes contiennent des doubles espaces")

    long_lines = [i + 1 for i, l in enumerate(lines) if len(l) > 150]
    if long_lines:
        sample = ", ".join(map(str, long_lines[:5]))
        issues.append(
            f"{len(long_lines)} lignes > 150 caractères (ex : lignes {sample})"
        )

    upper_anomalies = []
    for i, l in enumerate(lines):
        if not l.strip() or len(l.strip()) > 150:
            continue
        words = [w for w in l.split() if w]
        if len(words) >= 4:
            upper_count = sum(1 for w in words if w.isupper() and len(w) >= 4)
            if upper_count >= max(3, len(words) * 0.6):
                upper_anomalies.append(i + 1)
    if upper_anomalies:
        sample = ", ".join(map(str, upper_anomalies[:5]))
        issues.append(
            f"{len(upper_anomalies)} lignes en majuscules hors titres (ex : lignes {sample})"
        )

    if re.search(r"[ \t]+[,;:!?]", cv_text):
        issues.append(
            "Espaces avant la ponctuation (ex : 'bonjour ,' au lieu de 'bonjour,')"
        )

    bullets = re.findall(r"^\s*([•\-\*])", cv_text, re.MULTILINE)
    if bullets and len(set(bullets)) > 1:
        used = " ".join(sorted(set(bullets)))
        issues.append(f"Puces incohérentes : mélange de [{used}]")

    if not re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", cv_text):
        issues.append("Aucune adresse email détectée")

    return issues


RADAR_CATEGORIES = {
    "Frontend": [
        "Informatique - Frontend",
        "Design & UX",
    ],
    "Backend": [
        "Informatique - Backend",
        "Informatique - Mobile",
    ],
    "Bases de données": ["Bases de donnees"],
    "Cloud & DevOps": [
        "Cloud & DevOps",
        "Réseaux & Sécurité",
        "Reseaux & Securite",
    ],
    "Data & IA": ["Data & IA"],
    "Autres": [
        "Outils & Methodes IT",
        "Gestion de projet",
        "Finance & Comptabilité",
        "Finance & Comptabilite",
        "Marketing & Communication",
        "Ressources Humaines",
        "Juridique",
        "Logistique & Supply Chain",
        "BTP & Construction",
        "Industrie & Mécanique",
        "Industrie & Mecanique",
        "Electricité & Electronique",
        "Electricite & Electronique",
        "Energie & Environnement",
        "Agriculture & Agroalimentaire",
        "Hotellerie & Restauration",
        "Tourisme",
        "Aviation",
        "Aeronautique & Spatial",
        "Sante & Medical",
        "Vente & Commerce",
        "Education & Formation",
    ],
}


def _compute_radar(skills_by_category):
    """Regroupe les skills par grand domaine pour le radar."""
    radar = {k: 0 for k in RADAR_CATEGORIES.keys()}
    cat_to_domain = {}
    for domain, cats in RADAR_CATEGORIES.items():
        for cat in cats:
            cat_to_domain[cat] = domain

    for cat, items in skills_by_category.items():
        domain = cat_to_domain.get(cat, "Autres")
        radar[domain] += len(items)

    max_val = max(radar.values()) if radar.values() else 1
    if max_val == 0:
        max_val = 1
    radar_pct = {k: round(v / max_val * 100, 0) for k, v in radar.items()}
    return {"counts": radar, "percentages": radar_pct}


def analyze_cv(cv_text):
    """Analyse complete d'un CV, sans offre d'emploi."""
    if not cv_text or not cv_text.strip():
        return {"error": "CV vide"}

    sections = split_sections(cv_text)
    contact = _extract_contact(cv_text)

    words = len(cv_text.split())
    lines_count = len([l for l in cv_text.split("\n") if l.strip()])
    stats = {
        "characters": len(cv_text),
        "words": words,
        "lines": lines_count,
        "reading_time_min": round(words / 200, 1),
    }

    all_skills = extract_skills(cv_text)
    technical_skills = filter_technical_skills(all_skills)
    skills_by_category = _categorize_skills(technical_skills)

    languages = _extract_languages(cv_text)
    education = extract_education(cv_text)

    expected = {"experience", "education", "skills", "projects", "languages"}
    sections_found = sorted(set(sections.keys()) & expected)
    sections_missing = sorted(expected - set(sections.keys()))

    score = _compute_score(contact, sections, stats, technical_skills)
    strengths, improvements = _build_feedback(
        contact, sections, stats, technical_skills, languages, education
    )
    quality = _check_quality(cv_text)
    radar = _compute_radar(skills_by_category)

    return {
        "score": score,
        "contact": contact,
        "stats": stats,
        "sections": {"found": sections_found, "missing": sections_missing},
        "skills_by_category": skills_by_category,
        "skills_count": len(technical_skills),
        "languages": languages,
        "education": education,
        "strengths": strengths,
        "improvements": improvements,
        "quality": quality,
        "radar": radar,
    }