import os
from openai import AsyncOpenAI
from dotenv import load_dotenv

from services.skills import filter_technical_skills

load_dotenv()

_client = None


def get_client():
    global _client
    if _client is None:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key or api_key == "gsk_ta_cle_ici":
            raise RuntimeError(
                "GROQ_API_KEY manquante ou non configuree dans backend/.env"
            )
        _client = AsyncOpenAI(
            api_key=api_key,
            base_url="https://api.groq.com/openai/v1",
        )
    return _client


async def generate_cover_letter(
    cv_text: str,
    job_text: str,
    cv_skills: set = None,
    job_skills: set = None,
) -> str:
    """
    Genere une lettre de motivation via Groq.
    On passe au LLM :
      - le texte du CV
      - le texte de l'offre
      - la LISTE explicite des competences techniques en commun
      - la LISTE des competences manquantes
      - la LISTE NOIRE (langues + outils) que le LLM ne doit PAS mentionner
    """
    model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    client = get_client()

    # Filtrage : on retire les langues et outils des listes
    if cv_skills and job_skills:
        cv_tech = filter_technical_skills(cv_skills)
        job_tech = filter_technical_skills(job_skills)
        common_tech = sorted(cv_tech & job_tech)
        missing_tech = sorted(job_tech - cv_tech)
        non_tech_found = sorted((cv_skills | job_skills) - (cv_tech | job_tech))
    else:
        common_tech = []
        missing_tech = []
        non_tech_found = []

    common_str = ", ".join(common_tech) if common_tech else "aucune"
    missing_str = ", ".join(missing_tech) if missing_tech else "aucune"
    non_tech_str = ", ".join(non_tech_found) if non_tech_found else "aucune"

    system_prompt = (
        "Tu es un assistant specialise dans la redaction de lettres de motivation "
        "professionnelles en francais.\n\n"
        "REGLES ABSOLUES :\n"
        "1. Tu te bases STRICTEMENT sur les informations du CV. Tu n'inventes RIEN.\n"
        "2. Tu ne listes JAMAIS les langues parlees (Anglais, Arabe, etc.) dans les "
        "competences maitrisees. Une langue n'est pas une competence technique.\n"
        "3. Tu ne listes JAMAIS les outils bureautiques (Excel, Word, PowerPoint) "
        "ni les outils de gestion (Asana, Trello, Notion) comme 'competences maitrisees'.\n"
        "4. Tu ne listes JAMAIS les outils de design (Figma, Photoshop) comme "
        "competences techniques.\n"
        "5. Tu te concentres sur les competences TECHNIQUES reelles : langages, "
        "frameworks, bases de donnees, outils de dev (Git, Docker, etc.), cloud.\n"
        "6. Si tu mentionnes une competence, cite-la dans un contexte concret : "
        "'a travers mon projet X' ou 'lors de mon stage chez Y', pas en liste.\n\n"
        "STRUCTURE ATTENDUE :\n"
        "- Formule d'appel : Madame, Monsieur,\n"
        "- Accroche (2-3 lignes)\n"
        "- Paragraphe sur 2-3 competences techniques cles avec contexte\n"
        "- Paragraphe sur la formation ou une realisation\n"
        "- Phrase de motivation\n"
        "- Formule de politesse\n\n"
        "Longueur : 200-300 mots. Pas d'en-tete (nom, adresse, date). "
        "Reponds uniquement avec le corps de la lettre."
    )

    user_prompt = (
        f"CV (texte brut) :\n---\n{cv_text[:3500]}\n---\n\n"
        f"OFFRE D'EMPLOI (texte brut) :\n---\n{job_text[:2500]}\n---\n\n"
        f"COMPETENCES TECHNIQUES EN COMMUN (CV et offre) :\n{common_str}\n\n"
        f"COMPETENCES TECHNIQUES MANQUANTES (offre mais pas CV — "
        f"NE PAS MENTIONNER comme maitrisees) :\n{missing_str}\n\n"
        f"ELEMENTS A NE JAMAIS PRESENTER COMME COMPETENCES TECHNIQUES "
        f"(langues et outils) :\n{non_tech_str}\n\n"
        "Redige maintenant la lettre en respectant les regles."
    )

    response = await client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.3,
        max_tokens=800,
    )
    return response.choices[0].message.content.strip()