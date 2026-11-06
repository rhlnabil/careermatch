from services.experiences import split_sections
from services.skills import extract_skills


SECTION_LABELS = {
    "header": "Profil / En-tête",
    "experience": "Expériences",
    "education": "Formation",
    "projects": "Projets",
    "skills": "Compétences",
    "languages": "Langues",
}


def analyze_by_section(cv_text, job_skills):
    """Pour chaque section du CV, calcule les skills de l'offre presentes."""
    sections = split_sections(cv_text)
    job_skills = set(job_skills or [])
    if not job_skills:
        return []

    breakdown = []
    for section_key, content in sections.items():
        if not content or len(content.strip()) < 20:
            continue
        section_skills = extract_skills(content)
        found = sorted(section_skills & job_skills)
        breakdown.append({
            "key": section_key,
            "label": SECTION_LABELS.get(section_key, section_key.capitalize()),
            "skills_found": found,
            "count": len(found),
        })

    breakdown.sort(key=lambda x: -x["count"])
    return breakdown