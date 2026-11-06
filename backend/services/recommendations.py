def build_recommendations(cv_text, job_text, cv_skills, job_skills, report):
    recos = []
    score = report["score"]
    missing = sorted(job_skills - cv_skills)
    found = sorted(cv_skills & job_skills)

    if missing:
        recos.append({
            "type": "skills_to_mention",
            "priority": "high",
            "title": f"{len(missing)} competence(s) attendue(s) absente(s) du CV",
            "message": "Si tu les maitrises, mentionne-les explicitement : "
                       + ", ".join(missing)
                       + ". Ne les invente pas : l'idee est de rendre visible ce que tu sais deja faire.",
        })

    if found and len(found) < len(job_skills):
        recos.append({
            "type": "skills_to_highlight",
            "priority": "medium",
            "title": "Mets en avant tes competences deja alignees",
            "message": "Ces competences sont attendues et deja presentes dans ton CV : "
                       + ", ".join(found)
                       + ". Place-les dans un titre, une section 'Competences' ou le resume en haut.",
        })

    if job_skills and len(found) == len(job_skills):
        recos.append({
            "type": "full_match",
            "priority": "low",
            "title": "Toutes les competences de l'offre sont presentes",
            "message": "Ton CV couvre l'ensemble des competences techniques demandees. Postule !",
        })

    if score < 40:
        recos.append({
            "type": "overall",
            "priority": "high",
            "title": "Alignement faible — cible mieux",
            "message": "Cette offre semble eloignee de ton profil. Cherche des offres plus proches, ou adapte ton CV en reprenant les mots-cles de l'offre.",
        })
    elif score >= 70:
        recos.append({
            "type": "overall",
            "priority": "low",
            "title": "Bon alignement — candidate !",
            "message": "Ton CV correspond bien a cette offre. Postule en soulignant les competences communes dans ta lettre de motivation.",
        })
    else:
        recos.append({
            "type": "overall",
            "priority": "medium",
            "title": "Alignement moyen",
            "message": "Quelques ajustements cibles peuvent ameliorer ton score : integre les competences manquantes que tu maitrises et reformule ton resume pour reprendre le vocabulaire de l'offre.",
        })

    return recos