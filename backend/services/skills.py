import json
import re
from pathlib import Path

_DATA = Path(__file__).resolve().parent.parent / "data" / "skills.json"
_RAW = json.loads(_DATA.read_text(encoding="utf-8-sig"))


def _flatten(data: dict) -> dict:
    """Accepte un dict {categorie: {skill: aliases}} ou {skill: aliases}."""
    if not data:
        return {}
    flat = {}
    for k, v in data.items():
        if isinstance(v, dict):
            flat.update(v)
        elif isinstance(v, list):
            flat[k] = v
    return flat


SKILLS = _flatten(_RAW)
print(f"[skills] {len(SKILLS)} competences chargees")


# Competences qu'on NE doit PAS presenter comme "maitrisees" dans une lettre
# de motivation (langues, outils bureautiques, outils de gestion).
NON_TECHNICAL_SKILLS = {
    # Langues
    "Francais", "Anglais", "Espagnol", "Allemand", "Italien", "Portugais",
    "Arabe", "Chinois", "Japonais", "Russe", "Neerlandais", "Turc", "Coreen",
    # Bureautique
    "Microsoft Word", "Microsoft Excel", "Microsoft PowerPoint",
    "Microsoft Outlook", "Microsoft Access", "Microsoft Teams",
    "Google Workspace", "Google Docs", "Google Sheets",
    "LibreOffice", "Markdown",
    # Design (outils)
    "Figma", "Sketch", "Adobe XD", "Photoshop", "Illustrator", "InDesign",
    "After Effects", "Premiere Pro", "Blender", "Canva",
    # Gestion de projet (outils)
    "Jira", "Trello", "Asana", "Monday.com", "Notion", "Confluence",
    "MS Project",
}


def normalize(text) -> str:
    if not text:
        return ""
    return re.sub(r"\s+", " ", str(text).lower())


def extract_skills(text) -> set:
    """Retourne l'ensemble des competences presentes dans le texte."""
    text = normalize(text)
    if not text:
        return set()
    found = set()
    for skill, aliases in SKILLS.items():
        for alias in aliases:
            pattern = r"(?<![A-Za-z0-9])" + re.escape(alias) + r"(?![A-Za-z0-9])"
            if re.search(pattern, text):
                found.add(skill)
                break
    return found


def extract_skills_with_weights(text) -> dict:
    """Retourne {competence: nombre d'occurrences dans le texte}."""
    text = normalize(text)
    if not text:
        return {}
    weights = {}
    for skill, aliases in SKILLS.items():
        count = 0
        for alias in aliases:
            pattern = r"(?<![A-Za-z0-9])" + re.escape(alias) + r"(?![A-Za-z0-9])"
            count += len(re.findall(pattern, text))
        if count > 0:
            weights[skill] = count
    return weights


def filter_technical_skills(skills) -> set:
    """Retourne uniquement les competences techniques (exclut langues/outils)."""
    if not skills:
        return set()
    return {s for s in skills if s not in NON_TECHNICAL_SKILLS}


def get_skill_categories() -> dict:
    """Retourne {competence: categorie} a partir de skills.json."""
    mapping = {}
    for cat, skills in _RAW.items():
        if isinstance(skills, dict):
            for skill_name in skills.keys():
                mapping[skill_name] = cat
    return mapping