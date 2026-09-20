from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from backend.app.database import get_db
from backend.app.models import Interview, Feedback
from backend.app.schemas import InterviewResponse, FeedbackCreate, FeedbackResponse
from backend.app.services.matching_engine import MatchingEngine

router = APIRouter(prefix="/api/interviews", tags=["Interviews"])

@router.get("/", response_model=List[InterviewResponse])
def get_all_interviews(
    status: Optional[str] = None,
    interviewer_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Interview)
    if status:
        query = query.filter(Interview.status == status)
    if interviewer_id:
        query = query.filter(Interview.interviewer_id == interviewer_id)

    interviews = query.order_by(Interview.start_time.asc()).all()
    results = []
    for item in interviews:
        res = InterviewResponse.from_orm(item)
        res.candidate_name = item.candidate.name if item.candidate else "N/A"
        res.candidate_email = item.candidate.email if item.candidate else "N/A"
        res.interviewer_name = item.interviewer.name if item.interviewer else "N/A"
        res.job_title = item.job.title if item.job else "N/A"
        res.has_feedback = (item.feedback is not None)
        results.append(res)
    return results

@router.get("/{interview_id}", response_model=InterviewResponse)
def get_interview(interview_id: int, db: Session = Depends(get_db)):
    item = db.query(Interview).filter(Interview.id == interview_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Interview not found")
    res = InterviewResponse.from_orm(item)
    res.candidate_name = item.candidate.name if item.candidate else "N/A"
    res.candidate_email = item.candidate.email if item.candidate else "N/A"
    res.interviewer_name = item.interviewer.name if item.interviewer else "N/A"
    res.job_title = item.job.title if item.job else "N/A"
    res.has_feedback = (item.feedback is not None)
    return res

@router.post("/{interview_id}/cancel")
def cancel_interview(interview_id: int, db: Session = Depends(get_db)):
    success = MatchingEngine.cancel_interview(db, interview_id)
    if not success:
        raise HTTPException(status_code=404, detail="Interview not found")
    return {"message": "Interview has been cancelled and slot released."}

@router.post("/{interview_id}/feedback", response_model=FeedbackResponse)
def submit_feedback(interview_id: int, feedback_data: FeedbackCreate, db: Session = Depends(get_db)):
    interview = db.query(Interview).filter(Interview.id == interview_id).first()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")

    existing_feedback = db.query(Feedback).filter(Feedback.interview_id == interview_id).first()
    if existing_feedback:
        raise HTTPException(status_code=400, detail="Feedback has already been submitted for this interview")

    feedback = Feedback(
        interview_id=interview_id,
        interviewer_id=interview.interviewer_id,
        technical_score=feedback_data.technical_score,
        communication_score=feedback_data.communication_score,
        problem_solving_score=feedback_data.problem_solving_score,
        overall_recommendation=feedback_data.overall_recommendation,
        strengths=feedback_data.strengths,
        weaknesses=feedback_data.weaknesses,
        notes=feedback_data.notes
    )
    db.add(feedback)

    # Mark interview as COMPLETED
    interview.status = "COMPLETED"

    # Update candidate status based on recommendation
    if interview.candidate:
        if feedback_data.overall_recommendation in ["STRONG_HIRE", "HIRE"]:
            interview.candidate.status = "HIRED"
        elif feedback_data.overall_recommendation == "REJECT":
            interview.candidate.status = "REJECTED"
        else:
            interview.candidate.status = "COMPLETED"

    db.commit()
    db.refresh(feedback)
    return feedback

@router.get("/{interview_id}/feedback", response_model=FeedbackResponse)
def get_feedback(interview_id: int, db: Session = Depends(get_db)):
    feedback = db.query(Feedback).filter(Feedback.interview_id == interview_id).first()
    if not feedback:
        raise HTTPException(status_code=404, detail="No feedback found for this interview")
    return feedback
