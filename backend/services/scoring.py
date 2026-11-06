def compute_report(cv_text, job_text, cv_skills, job_skills_with_weights):
    """
    Score = couverture ponderee.
    - Chaque competence de l'offre pese son nombre d'occurrences (min 1).
    - Score = somme des poids des competences trouvees dans le CV
              / somme des poids de toutes les competences de l'offre.
    """
    if not job_skills_with_weights:
        return {
            "score": 0.0,
            "skills_found": [],
            "skills_to_highlight": [],
            "bonus_skills": sorted(cv_skills - set()),
            "details": {
                "skill_coverage": 0.0,
                "skills_matched": 0,
                "skills_total": 0,
                "weight_matched": 0,
                "weight_total": 0,
            },
        }

    job_skills = set(job_skills_with_weights.keys())
    total_weight = sum(job_skills_with_weights.values())
    matched_weight = sum(
        w for s, w in job_skills_with_weights.items() if s in cv_skills
    )
    matched_skills = sorted(cv_skills & job_skills)
    missing_skills = sorted(job_skills - cv_skills)

    coverage_pct = round(100 * matched_weight / total_weight, 1) if total_weight else 0.0

    return {
        "score": coverage_pct,
        "skills_found": matched_skills,
        "skills_to_highlight": missing_skills,
        "bonus_skills": sorted(cv_skills - job_skills),
        "details": {
            "skill_coverage": coverage_pct,
            "skills_matched": len(matched_skills),
            "skills_total": len(job_skills),
            "weight_matched": matched_weight,
            "weight_total": total_weight,
        },
    }