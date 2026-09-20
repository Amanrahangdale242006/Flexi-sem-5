from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import datetime
from pydantic import BaseModel

from backend.app.database import get_db
from backend.app.models import User, InterviewerSlot, Interview
from backend.app.schemas import UserCreate, UserResponse, SlotBase, SlotCreate, SlotResponse

router = APIRouter(prefix="/api/interviewers", tags=["Interviewers"])

class RecurringSlotRequest(BaseModel):
    days_ahead: int = 7  # e.g., next 7 days
    start_hour: int = 10 # 10 AM
    end_hour: int = 17   # 5 PM
    slot_duration_minutes: int = 45

@router.get("/", response_model=List[UserResponse])
def get_all_interviewers(db: Session = Depends(get_db)):
    return db.query(User).filter(User.role == "INTERVIEWER").all()

@router.post("/", response_model=UserResponse)
def create_interviewer(user_data: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == user_data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="User with this email already exists")
    user = User(**user_data.dict())
    user.role = "INTERVIEWER"
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@router.get("/{interviewer_id}/slots", response_model=List[SlotResponse])
def get_interviewer_slots(interviewer_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == interviewer_id, User.role == "INTERVIEWER").first()
    if not user:
        raise HTTPException(status_code=404, detail="Interviewer not found")
    
    slots = db.query(InterviewerSlot).filter(
        InterviewerSlot.interviewer_id == interviewer_id
    ).order_by(InterviewerSlot.start_time.asc()).all()

    # Enrich slot with interviewer name
    for s in slots:
        s.interviewer_name = user.name
    return slots

@router.post("/{interviewer_id}/slots", response_model=SlotResponse)
def add_slot(interviewer_id: int, slot_data: SlotBase, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == interviewer_id, User.role == "INTERVIEWER").first()
    if not user:
        raise HTTPException(status_code=404, detail="Interviewer not found")

    if slot_data.start_time >= slot_data.end_time:
        raise HTTPException(status_code=400, detail="End time must be strictly after start time")

    slot = InterviewerSlot(
        interviewer_id=interviewer_id,
        start_time=slot_data.start_time,
        end_time=slot_data.end_time,
        is_booked=False
    )
    db.add(slot)
    db.commit()
    db.refresh(slot)
    slot.interviewer_name = user.name
    return slot

@router.post("/{interviewer_id}/slots/recurring")
def generate_recurring_slots(
    interviewer_id: int,
    req: RecurringSlotRequest,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == interviewer_id, User.role == "INTERVIEWER").first()
    if not user:
        raise HTTPException(status_code=404, detail="Interviewer not found")

    now = datetime.datetime.utcnow()
    created_count = 0

    for day in range(1, req.days_ahead + 1):
        target_date = (now + datetime.timedelta(days=day)).date()
        # Skip weekends (Saturday=5, Sunday=6)
        if target_date.weekday() >= 5:
            continue

        current_time = datetime.datetime.combine(target_date, datetime.time(hour=req.start_hour, minute=0))
        end_day_time = datetime.datetime.combine(target_date, datetime.time(hour=req.end_hour, minute=0))

        while current_time + datetime.timedelta(minutes=req.slot_duration_minutes) <= end_day_time:
            slot_end = current_time + datetime.timedelta(minutes=req.slot_duration_minutes)

            # Check if overlapping slot already exists
            exists = db.query(InterviewerSlot).filter(
                InterviewerSlot.interviewer_id == interviewer_id,
                InterviewerSlot.start_time == current_time
            ).first()

            if not exists:
                slot = InterviewerSlot(
                    interviewer_id=interviewer_id,
                    start_time=current_time,
                    end_time=slot_end,
                    is_booked=False
                )
                db.add(slot)
                created_count += 1

            # Advance by duration + 15 min buffer
            current_time = slot_end + datetime.timedelta(minutes=15)

    db.commit()
    return {"message": f"Successfully created {created_count} availability slots for {user.name}"}

@router.delete("/slots/{slot_id}")
def delete_slot(slot_id: int, db: Session = Depends(get_db)):
    slot = db.query(InterviewerSlot).filter(InterviewerSlot.id == slot_id).first()
    if not slot:
        raise HTTPException(status_code=404, detail="Slot not found")
    if slot.is_booked:
        raise HTTPException(status_code=400, detail="Cannot delete an already booked slot")
    db.delete(slot)
    db.commit()
    return {"message": "Slot removed successfully"}
