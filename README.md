@'
# CareerMatch — Analyseur de CV intelligent

Analyse un CV, le compare à une offre d'emploi et génère un rapport détaillé.

## Fonctionnalités

- Score de correspondance pondéré
- Compétences trouvées / manquantes
- Extraction expériences, diplômes, langues
- Détection mode de travail, contrat, salaire
- Lettre de motivation générée par Groq (Llama 3.3)
- Préparation entretien (10 questions + conseils)
- Export PDF
- Historique en localStorage

## Stack

React 19 + Vite + Tailwind CSS + OGL (WebGL)  
FastAPI + PyMuPDF + spaCy + scikit-learn + Groq API

## Lancer en local

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env
# remplis GROQ_API_KEY dans .env
python -m uvicorn main:app --reload