import re
import unicodedata

from services.skills import extract_skills, extract_skills_with_weights
from services.experiences import extract_education
from services.llm_service import generate_cover_letter as llm_generate


def _strip_accents(s):
    return "".join(
        c for c in unicodedata.normalize("NFD", s)
        if unicodedata.category(c) != "Mn"
    )


def _extract_cv_header(cv_text):
    lines = [l.strip() for l in cv_text.split("\n") if l.strip()]
    name = ""
    status = ""
    city = ""

    if lines:
        first = lines[0]
        words = first.split()
        if 1 < len(words) <= 5 and all(w[0].isupper() for w in words if w):
            name = first

    for line in lines[:6]:
        if re.search(
            r"\b(etudiant|étudiant|diplome|diplômé|ingenieur|ingénieur|"
            r"developpeur|développeur|consultant|master|licence)\b",
            _strip_accents(line.lower()),
        ):
            status = line[:150]
            break

    for line in lines[:6]:
        m = re.search(
            r"([A-ZÀ-Ÿ][a-zà-ÿ\-]+(?:\s+[A-ZÀ-Ÿ][a-zà-ÿ\-]+)?)"
            r"(?:\s*[|,]\s*)(?:Maroc|France|Belgique|Suisse|Canada|"
            r"[A-ZÀ-Ÿ][a-zà-ÿ\-]+)",
            line,
        )
        if m:
            city = m.group(1)
            break

    return {"name": name, "status": status, "city": city}


def _extract_job_title(job_text):
    patterns = [
        r"(?:poste|position)\s+(?:de|d[''])\s*([A-Za-zÀ-ÿ][\w\s/-]{3,60})",
        r"(?:recherch(?:e|ons|é)|recrute|recrutons)\s+(?:un|une)?\s*"
        r"([A-Za-zÀ-ÿ][\w\s/-]{3,60})",
        r"développeur(?:se)?\s+([\w\s/-]{2,40})",
        r"ingénieur\s+([\w\s/-]{2,40})",
    ]
    for pat in patterns:
        m = re.search(pat, job_text, re.IGNORECASE)
        if m:
            title = m.group(0).strip()
            title = re.split(r"[.\n,]", title)[0].strip()
            if len(title) > 3:
                return title[:80]

    for line in job_text.split("\n"):
        line = line.strip()
        if line and len(line) < 80:
            return line[:80]
    return "le poste proposé"


def _extract_company(job_text):
    m = re.search(r"\bchez\s+([A-ZÀ-Ÿ][\w\s&'-]{2,40})", job_text)
    if m:
        return m.group(1).strip()[:60]
    for line in job_text.split("\n"):
        line = line.strip()
        if line and len(line) < 40 and line.isupper():
            return line[:60]
    return ""


def _format_skills_list(skills):
    skills = [s for s in skills if s]
    if not skills:
        return ""
    if len(skills) == 1:
        return skills[0]
    if len(skills) == 2:
        return f"{skills[0]} et {skills[1]}"
    return ", ".join(skills[:-1]) + f" et {skills[-1]}"


def _build_template_letter(cv_text, job_text):
    """
    Template deterministe utilise en fallback si Groq echoue
    (cle absente, quota, reseau).
    """
    header = _extract_cv_header(cv_text)
    job_title = _extract_job_title(job_text)
    company = _extract_company(job_text)

    cv_skills = extract_skills(cv_text)
    job_skills_w = extract_skills_with_weights(job_text)
    job_skills = set(job_skills_w.keys())

    # Filtrage : on ne garde que les competences techniques
    from services.skills import filter_technical_skills

    cv_tech = filter_technical_skills(cv_skills)
    job_tech = filter_technical_skills(job_skills)
    matched = sorted(cv_tech & job_tech)
    other = sorted(cv_tech - job_tech)[:3]

    education = extract_education(cv_text)
    top_edu = education[0]["title"] if education else ""
    edu_year = education[0].get("year") if education else ""

    profile = header["status"] or "À la recherche d'une nouvelle opportunité"
    profile = profile.rstrip(".").strip()

    p1 = (
        f"{profile}, je vous adresse ma candidature pour {job_title}"
        + (f" au sein de {company}" if company else "")
        + "."
    )

    if matched:
        p2 = (
            f"Votre offre met en avant {_format_skills_list(matched)}, "
            "compétences que j'ai développées à travers mes projets et expériences."
        )
    else:
        p2 = (
            "Votre offre a retenu mon attention et je pense pouvoir y contribuer "
            "efficacement grâce à mon profil technique."
        )

    p3_parts = []
    if top_edu:
        year_txt = f" ({edu_year})" if edu_year else ""
        p3_parts.append(
            f"Actuellement en {top_edu}{year_txt}, j'ai consolidé des bases "
            "solides en développement logiciel."
        )
    if other:
        p3_parts.append(f"Je maîtrise également {_format_skills_list(other)}.")
    p3 = " ".join(p3_parts)

    p4 = "Motivé par les missions décrites, je serais ravi d'échanger avec vous."

    parts = []
    if header["name"]:
        parts.append(header["name"])
    if header["city"]:
        parts.append(header["city"])
    if parts:
        parts.append("")
    parts.append("Madame, Monsieur,")
    parts.append("")
    parts.append(p1)
    parts.append("")
    parts.append(p2)
    if p3:
        parts.append("")
        parts.append(p3)
    parts.append("")
    parts.append(p4)
    parts.append("")
    parts.append(
        "Dans l'attente de votre retour, je vous prie d'agréer, Madame, "
        "Monsieur, l'expression de mes salutations distinguées."
    )
    if header["name"]:
        parts.append("")
        parts.append(header["name"])

    return "\n".join(parts), {
        "job_title": job_title,
        "company": company,
        "profile": profile,
        "top_skills": matched[:5],
        "other_skills": other,
        "education": top_edu,
        "education_year": edu_year,
    }


async def build_cover_letter(cv_text, job_text):
    """
    Genere une lettre via Groq. Si Groq echoue, fallback template.
    """
    header = _extract_cv_header(cv_text)
    job_title = _extract_job_title(job_text)
    company = _extract_company(job_text)

    cv_skills = extract_skills(cv_text)
    job_skills_w = extract_skills_with_weights(job_text)
    job_skills = set(job_skills_w.keys())

    try:
        letter_text = await llm_generate(
            cv_text,
            job_text,
            cv_skills=cv_skills,
            job_skills=job_skills,
        )

        if header["name"]:
            prefix = header["name"] + "\n"
            if header["city"]:
                prefix += header["city"] + "\n"
            prefix += "\n"
            letter_text = prefix + letter_text

        return {
            "letter": letter_text,
            "meta": {
                "job_title": job_title,
                "company": company,
                "profile": header["status"],
                "provider": "groq",
            },
        }
    except Exception as e:
        print(f"[cover_letter] Groq echoue, fallback template : {e}")
        letter_text, meta = _build_template_letter(cv_text, job_text)
        meta["provider"] = "fallback"
        meta["error"] = str(e)
        return {"letter": letter_text, "meta": meta}