from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from backend.app.database import get_db
from backend.app.models import Job
from backend.app.schemas import JobCreate, JobResponse

router = APIRouter(prefix="/api/jobs", tags=["Jobs"])

@router.get("/", response_model=List[JobResponse])
def get_all_jobs(db: Session = Depends(get_db)):
    return db.query(Job).order_by(Job.created_at.desc()).all()

@router.post("/", response_model=JobResponse)
def create_job(job_data: JobCreate, db: Session = Depends(get_db)):
    job = Job(**job_data.dict())
    db.add(job)
    db.commit()
    db.refresh(job)
    return job

@router.get("/{job_id}", response_model=JobResponse)
def get_job_by_id(job_id: int, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job opening not found")
    return job

@router.delete("/{job_id}")
def delete_job(job_id: int, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job opening not found")
    db.delete(job)
    db.commit()
    return {"message": "Job deleted successfully"}
