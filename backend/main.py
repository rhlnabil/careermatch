from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from services.pdf_extract import extract_text
from services.skills import extract_skills, extract_skills_with_weights
from services.scoring import compute_report
from services.recommendations import build_recommendations
from services.experiences import build_career_summary, split_sections
from services.cover_letter import build_cover_letter
from services.cv_analyzer import analyze_cv
from services.section_analyzer import analyze_by_section
from services.interview_prep import build_interview_questions
from services.work_mode import extract_job_meta

app = FastAPI(title="CareerMatch API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"status": "ok", "service": "CareerMatch"}


@app.post("/api/analyze")
async def analyze(cv: UploadFile = File(...), job: str = Form(...)):
    try:
        cv_bytes = await cv.read()
        cv_text = extract_text(cv_bytes) or ""
        job_text = job or ""

        cv_skills = extract_skills(cv_text)
        job_skills_w = extract_skills_with_weights(job_text)
        report = compute_report(cv_text, job_text, cv_skills, job_skills_w)
        recommendations = build_recommendations(
            cv_text, job_text, cv_skills, set(job_skills_w.keys()), report
        )
        career = build_career_summary(cv_text)
        sections_breakdown = analyze_by_section(cv_text, set(job_skills_w.keys()))
        job_meta = extract_job_meta(job_text)

        return {
            "report": report,
            "recommendations": recommendations,
            "career": career,
            "sections_breakdown": sections_breakdown,
            "job_meta": job_meta,
            "cv_preview": cv_text[:500],
            "meta": {
                "cv_length": len(cv_text),
                "job_length": len(job_text),
                "cv_skills_count": len(cv_skills),
                "job_skills_count": len(job_skills_w),
            },
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e), "type": type(e).__name__},
        )


@app.post("/api/analyze-cv")
async def analyze_cv_endpoint(cv: UploadFile = File(...)):
    try:
        cv_bytes = await cv.read()
        cv_text = extract_text(cv_bytes) or ""
        if not cv_text.strip():
            return JSONResponse(
                status_code=400,
                content={
                    "error": "Le PDF ne contient pas de texte extractible (scan ?)",
                    "type": "EmptyPDF",
                },
            )
        result = analyze_cv(cv_text)
        return result
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e), "type": type(e).__name__},
        )


@app.post("/api/cover-letter")
async def cover_letter(cv: UploadFile = File(...), job: str = Form(...)):
    try:
        cv_bytes = await cv.read()
        cv_text = extract_text(cv_bytes) or ""
        job_text = job or ""
        result = await build_cover_letter(cv_text, job_text)
        return result
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e), "type": type(e).__name__},
        )


@app.post("/api/interview-prep")
async def interview_prep(cv: UploadFile = File(...), job: str = Form(...)):
    try:
        cv_bytes = await cv.read()
        cv_text = extract_text(cv_bytes) or ""
        job_text = job or ""

        cv_skills = extract_skills(cv_text)
        job_skills = extract_skills(job_text)
        career = build_career_summary(cv_text)

        result = build_interview_questions(cv_skills, job_skills, career, job_text)
        return result
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e), "type": type(e).__name__},
        )


@app.post("/api/debug/cv")
async def debug_cv(cv: UploadFile = File(...)):
    try:
        cv_bytes = await cv.read()
        cv_text = extract_text(cv_bytes) or ""
        sections = split_sections(cv_text)
        return {
            "cv_length": len(cv_text),
            "sections": {
                name: {"length": len(content), "preview": content[:1500]}
                for name, content in sections.items()
            },
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e), "type": type(e).__name__},
        )