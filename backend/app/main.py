import os
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from backend.app.config import APP_NAME, APP_DESCRIPTION, APP_VERSION, BASE_DIR
from backend.app.database import engine, Base, get_db
from backend.app.services.seed_data import seed_database
from backend.app.routers import jobs, interviewers, candidates, booking, interviews, analytics

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI App
app = FastAPI(
    title=APP_NAME,
    description=APP_DESCRIPTION,
    version=APP_VERSION
)

# Static and Template directories
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(TEMPLATES_DIR, exist_ok=True)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# Include API Routers
app.include_router(jobs.router)
app.include_router(interviewers.router)
app.include_router(candidates.router)
app.include_router(booking.router)
app.include_router(interviews.router)
app.include_router(analytics.router)

# Automatic startup seeding
@app.on_event("startup")
def on_startup():
    from backend.app.database import SessionLocal
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()

# Page Routes (Frontend SSR + Alpine.js / Tailwind CSS)

@app.get("/", response_class=HTMLResponse)
def index_dashboard(request: Request):
    return templates.TemplateResponse(request=request, name="dashboard.html", context={"page_title": "Dashboard"})

@app.get("/jobs", response_class=HTMLResponse)
def jobs_page(request: Request):
    return templates.TemplateResponse(request=request, name="jobs.html", context={"page_title": "Job Openings"})

@app.get("/candidates", response_class=HTMLResponse)
def candidates_page(request: Request):
    return templates.TemplateResponse(request=request, name="candidates.html", context={"page_title": "Candidates"})

@app.get("/interviewers", response_class=HTMLResponse)
def interviewers_page(request: Request):
    return templates.TemplateResponse(request=request, name="interviewers.html", context={"page_title": "Interviewers & Availability"})

@app.get("/book/{token}", response_class=HTMLResponse)
def booking_page(request: Request, token: str):
    return templates.TemplateResponse(request=request, name="booking.html", context={"token": token, "page_title": "Schedule Your Interview"})

@app.get("/feedback/{interview_id}", response_class=HTMLResponse)
def feedback_page(request: Request, interview_id: int):
    return templates.TemplateResponse(request=request, name="feedback.html", context={"interview_id": interview_id, "page_title": "Interview Evaluation"})
