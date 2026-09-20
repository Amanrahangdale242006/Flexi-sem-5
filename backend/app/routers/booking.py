from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from backend.app.database import get_db
from backend.app.models import Candidate, Interview
from backend.app.schemas import BookSlotRequest, AvailableSlotOption, InterviewResponse
from backend.app.services.matching_engine import MatchingEngine
from backend.app.services.calendar_service import CalendarService

router = APIRouter(prefix="/api/booking", tags=["Candidate Booking"])

@router.get("/details")
def get_booking_details(token: str, db: Session = Depends(get_db)):
    candidate = db.query(Candidate).filter(Candidate.invite_token == token).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Invalid or expired booking link")

    existing_interview = db.query(Interview).filter(
        Interview.candidate_id == candidate.id,
        Interview.status == "SCHEDULED"
    ).first()

    interview_data = None
    if existing_interview:
        interview_data = {
            "id": existing_interview.id,
            "start_time": existing_interview.start_time,
            "end_time": existing_interview.end_time,
            "interviewer_name": existing_interview.interviewer.name if existing_interview.interviewer else "Interviewer",
            "meeting_link": existing_interview.meeting_link,
            "status": existing_interview.status
        }

    return {
        "candidate": {
            "id": candidate.id,
            "name": candidate.name,
            "email": candidate.email,
            "status": candidate.status,
            "job_title": candidate.job.title if candidate.job else "N/A",
            "department": candidate.job.department if candidate.job else "",
            "required_skills": candidate.job.required_skills if candidate.job else ""
        },
        "existing_interview": interview_data
    }

@router.get("/available-slots", response_model=List[AvailableSlotOption])
def get_available_slots(token: str, db: Session = Depends(get_db)):
    candidate = db.query(Candidate).filter(Candidate.invite_token == token).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Invalid booking link")

    slots = MatchingEngine.get_available_slots_for_candidate(db, candidate)
    return slots

@router.post("/confirm")
def confirm_booking(payload: BookSlotRequest, db: Session = Depends(get_db)):
    candidate = db.query(Candidate).filter(Candidate.invite_token == payload.token).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Invalid booking link")

    # Check if already has scheduled interview
    existing = db.query(Interview).filter(
        Interview.candidate_id == candidate.id,
        Interview.status == "SCHEDULED"
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="You already have an active scheduled interview.")

    try:
        interview = MatchingEngine.book_slot(db, candidate, payload.slot_id, payload.notes)
        return {
            "message": "Interview successfully confirmed!",
            "interview_id": interview.id,
            "start_time": interview.start_time,
            "end_time": interview.end_time,
            "meeting_link": interview.meeting_link,
            "interviewer_name": interview.interviewer.name
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/ics/{interview_id}")
def download_calendar_invite(interview_id: int, db: Session = Depends(get_db)):
    interview = db.query(Interview).filter(Interview.id == interview_id).first()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")

    ics_bytes = CalendarService.generate_ics(interview)
    filename = f"interview-{interview.id}.ics"

    return Response(
        content=ics_bytes,
        media_type="text/calendar",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )
