import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from backend.app.database import get_db
from backend.app.models import Candidate, Job
from backend.app.schemas import CandidateCreate, CandidateResponse

router = APIRouter(prefix="/api/candidates", tags=["Candidates"])

@router.get("/", response_model=List[CandidateResponse])
def get_all_candidates(db: Session = Depends(get_db)):
    candidates = db.query(Candidate).order_by(Candidate.created_at.desc()).all()
    results = []
    for c in candidates:
        res = CandidateResponse.from_orm(c)
        res.job_title = c.job.title if c.job else "N/A"
        results.append(res)
    return results

@router.post("/", response_model=CandidateResponse)
def create_candidate(cand_data: CandidateCreate, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == cand_data.job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Selected job opening does not exist")

    token = str(uuid.uuid4())[:16]
    candidate = Candidate(
        name=cand_data.name,
        email=cand_data.email,
        phone=cand_data.phone,
        resume_url=cand_data.resume_url,
        job_id=cand_data.job_id,
        status="INVITED",
        invite_token=token
    )
    db.add(candidate)
    db.commit()
    db.refresh(candidate)

    res = CandidateResponse.from_orm(candidate)
    res.job_title = job.title
    return res

@router.get("/{candidate_id}", response_model=CandidateResponse)
def get_candidate(candidate_id: int, db: Session = Depends(get_db)):
    c = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Candidate not found")
    res = CandidateResponse.from_orm(c)
    res.job_title = c.job.title if c.job else "N/A"
    return res

@router.post("/{candidate_id}/regenerate-token")
def regenerate_invite_token(candidate_id: int, db: Session = Depends(get_db)):
    c = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Candidate not found")
    c.invite_token = str(uuid.uuid4())[:16]
    db.commit()
    return {"message": "Invite token regenerated", "token": c.invite_token}

@router.delete("/{candidate_id}")
def delete_candidate(candidate_id: int, db: Session = Depends(get_db)):
    c = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Candidate not found")
    db.delete(c)
    db.commit()
    return {"message": "Candidate removed successfully"}
