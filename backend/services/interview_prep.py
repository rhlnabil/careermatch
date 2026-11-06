def build_interview_questions(cv_skills, job_skills, career, job_text):
    """Genere des questions d'entretien deterministes."""
    cv_skills = set(cv_skills or [])
    job_skills = set(job_skills or [])
    common = sorted(cv_skills & job_skills)
    missing = sorted(job_skills - cv_skills)

    questions = []

    for skill in common[:5]:
        questions.append({
            "category": "Technique",
            "question": f"Décrivez une situation où vous avez utilisé {skill}. Quel était le contexte et le résultat ?",
            "advice": (
                f"Structure ta réponse : contexte → action → résultat. Cite un projet "
                f"concret (ex : {_pick_project(career)}). Mentionne les difficultés "
                f"rencontrées et comment tu les as résolues."
            ),
        })

    for skill in missing[:2]:
        questions.append({
            "category": "Apprentissage",
            "question": f"Vous ne mentionnez pas {skill} dans votre CV. Comment comptez-vous combler cette lacune ?",
            "advice": (
                f"Sois honnête : 'Je ne l'ai pas encore pratiqué en production, mais j'ai "
                f"commencé à me former via X'. Cite une ressource concrète et propose un "
                f"plan d'apprentissage (ex : 2 semaines). L'honnêteté plaît."
            ),
        })

    if career and career.get("experiences"):
        for exp in career["experiences"][:2]:
            title = exp.get("title", "ce poste")
            company = exp.get("company", "")
            questions.append({
                "category": "Expérience",
                "question": f"Parlez-moi de votre expérience chez {company or 'cette entreprise'} en tant que {title}.",
                "advice": (
                    "Structure STAR : Situation, Tâche, Action, Résultat. "
                    "Mets en avant une réalisation mesurable. Reste concis (2 min max), "
                    "termine par ce que tu as appris."
                ),
            })

    questions.append({
        "category": "Motivation",
        "question": "Pourquoi voulez-vous rejoindre notre entreprise et ce poste en particulier ?",
        "advice": (
            "Cite 2 éléments précis de l'offre (technologies, mission, équipe). "
            "Fais le lien avec ton parcours. Évite les généralités."
        ),
    })

    questions.append({
        "category": "Comportemental",
        "question": "Décrivez un désaccord technique que vous avez eu avec un collègue. Comment l'avez-vous géré ?",
        "advice": (
            "Montre que tu écoutes, que tu argumentes avec des faits, et que tu sais "
            "faire des compromis. Termine par le résultat concret."
        ),
    })

    return {
        "questions": questions[:10],
        "meta": {
            "common_skills": common[:8],
            "missing_skills": missing[:5],
            "count": len(questions[:10]),
        },
    }


def _pick_project(career):
    if not career:
        return "ton parcours"
    edu = career.get("education") or []
    if edu:
        return edu[0].get("title", "ton parcours")[:60]
    return "ton parcours"