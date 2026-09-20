from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import uuid

from backend.app.database import get_db
from backend.app.models import Candidate, Job
from backend.app.schemas import CandidateCreate, CandidateResponse

router = APIRouter(prefix="/api/public", tags=["Public Portal"])

@router.post("/apply")
def public_apply(cand_data: CandidateCreate, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == cand_data.job_id, Job.status == "OPEN").first()
    if not job:
        raise HTTPException(status_code=404, detail="Selected job position is not open or does not exist")

    token = str(uuid.uuid4())[:16]
    candidate = Candidate(
        name=cand_data.name,
        email=cand_data.email,
        phone=cand_data.phone or "",
        resume_url=cand_data.resume_url or "",
        job_id=cand_data.job_id,
        status="INVITED",
        invite_token=token
    )
    db.add(candidate)
    db.commit()
    db.refresh(candidate)

    return {
        "message": "Application received! You can now choose your interview slot.",
        "candidate_id": candidate.id,
        "invite_token": candidate.invite_token,
        "booking_url": f"/book/{candidate.invite_token}"
    }
