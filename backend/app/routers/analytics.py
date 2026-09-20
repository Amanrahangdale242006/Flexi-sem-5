from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.app.database import get_db
from backend.app.models import User, Job, Candidate, Interview, Feedback
from backend.app.services.seed_data import seed_database

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])

@router.get("/dashboard")
def get_dashboard_metrics(db: Session = Depends(get_db)):
    total_interviews = db.query(func.count(Interview.id)).scalar() or 0
    scheduled_interviews = db.query(func.count(Interview.id)).filter(Interview.status == "SCHEDULED").scalar() or 0
    completed_interviews = db.query(func.count(Interview.id)).filter(Interview.status == "COMPLETED").scalar() or 0
    cancelled_interviews = db.query(func.count(Interview.id)).filter(Interview.status == "CANCELLED").scalar() or 0

    total_candidates = db.query(func.count(Candidate.id)).scalar() or 0
    total_interviewers = db.query(func.count(User.id)).filter(User.role == "INTERVIEWER").scalar() or 0
    total_jobs = db.query(func.count(Job.id)).filter(Job.status == "OPEN").scalar() or 0

    # Interviewer workload breakdown
    interviewers = db.query(User).filter(User.role == "INTERVIEWER").all()
    workload = []
    for i in interviewers:
        count = db.query(func.count(Interview.id)).filter(Interview.interviewer_id == i.id).scalar() or 0
        workload.append({
            "interviewer_id": i.id,
            "name": i.name,
            "department": i.department,
            "interview_count": count,
            "max_per_day": i.max_interviews_per_day
        })

    # Candidate pipeline breakdown
    pipeline_counts = {
        "INVITED": db.query(func.count(Candidate.id)).filter(Candidate.status == "INVITED").scalar() or 0,
        "SCHEDULED": db.query(func.count(Candidate.id)).filter(Candidate.status == "SCHEDULED").scalar() or 0,
        "COMPLETED": db.query(func.count(Candidate.id)).filter(Candidate.status == "COMPLETED").scalar() or 0,
        "HIRED": db.query(func.count(Candidate.id)).filter(Candidate.status == "HIRED").scalar() or 0,
        "REJECTED": db.query(func.count(Candidate.id)).filter(Candidate.status == "REJECTED").scalar() or 0,
    }

    return {
        "metrics": {
            "total_interviews": total_interviews,
            "scheduled_interviews": scheduled_interviews,
            "completed_interviews": completed_interviews,
            "cancelled_interviews": cancelled_interviews,
            "total_candidates": total_candidates,
            "total_interviewers": total_interviewers,
            "total_jobs": total_jobs
        },
        "workload": workload,
        "pipeline": pipeline_counts
    }

@router.post("/reset-demo-data")
def reset_demo_data(db: Session = Depends(get_db)):
    seed_database(db, force_reset=True)
    return {"message": "Demo data successfully reset to clean presentation state!"}
