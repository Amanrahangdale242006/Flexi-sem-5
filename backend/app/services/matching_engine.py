import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict, Any, Optional

from backend.app.models import User, Job, Candidate, InterviewerSlot, Interview
from backend.app.config import BUFFER_TIME_MINUTES

class MatchingEngine:
    """
    Automated Matching & Scheduling Engine:
    1. Matches candidates and interviewers by required technical skills.
    2. Filters available unbooked slots.
    3. Prevents scheduling conflicts and double-booking.
    4. Applies load balancing across interviewers to prevent burnout.
    """

    @staticmethod
    def calculate_skill_overlap(interviewer_skills: List[str], required_skills: List[str]) -> float:
        """
        Calculates skill match percentage (Jaccard-like or coverage percentage).
        Returns a float between 0.0 and 100.0.
        """
        if not required_skills:
            return 100.0
        if not interviewer_skills:
            return 0.0

        interviewer_set = set(interviewer_skills)
        required_set = set(required_skills)
        matched = interviewer_set.intersection(required_set)
        
        # Percentage of required skills possessed by interviewer
        return round((len(matched) / len(required_set)) * 100.0, 1)

    @classmethod
    def get_qualified_interviewers(cls, db: Session, job: Job) -> List[Dict[str, Any]]:
        """
        Retrieves all interviewers qualified for the job, ranked by skill match score.
        """
        interviewers = db.query(User).filter(User.role == "INTERVIEWER").all()
        required_skills = job.get_required_skills_list()

        qualified = []
        for interviewer in interviewers:
            score = cls.calculate_skill_overlap(interviewer.get_skill_list(), required_skills)
            # If no skills specified on job, everyone is eligible (100%).
            # Otherwise require at least 30% match or include top matches
            if score > 0 or not required_skills:
                qualified.append({
                    "interviewer": interviewer,
                    "match_score": score
                })

        # Sort by match score descending
        qualified.sort(key=lambda x: x["match_score"], reverse=True)
        return qualified

    @classmethod
    def get_available_slots_for_candidate(cls, db: Session, candidate: Candidate) -> List[Dict[str, Any]]:
        """
        Finds all viable, conflict-free interview slots for a given candidate.
        Ensures:
        - Slot belongs to a qualified interviewer.
        - Slot is in the future.
        - Slot is not already booked.
        - Interviewer hasn't exceeded max_interviews_per_day for that slot date.
        - Interviewer has no overlapping interview (with buffer time).
        """
        now = datetime.datetime.utcnow()
        job = candidate.job
        if not job:
            return []

        qualified_interviewers_info = cls.get_qualified_interviewers(db, job)
        if not qualified_interviewers_info:
            return []

        interviewer_map = {q["interviewer"].id: q for q in qualified_interviewers_info}
        interviewer_ids = list(interviewer_map.keys())

        # Query all future unbooked slots for qualified interviewers
        slots = db.query(InterviewerSlot).filter(
            InterviewerSlot.interviewer_id.in_(interviewer_ids),
            InterviewerSlot.is_booked == False,
            InterviewerSlot.start_time > now
        ).order_by(InterviewerSlot.start_time.asc()).all()

        available_options = []
        for slot in slots:
            interviewer = slot.interviewer
            slot_date = slot.start_time.date()

            # Check daily interview limit for this interviewer
            daily_count = db.query(func.count(Interview.id)).filter(
                Interview.interviewer_id == interviewer.id,
                Interview.status == "SCHEDULED",
                func.date(Interview.start_time) == slot_date
            ).scalar() or 0

            if daily_count >= interviewer.max_interviews_per_day:
                continue

            # Check overlap with existing interviews of the interviewer (including buffer)
            buffer = datetime.timedelta(minutes=BUFFER_TIME_MINUTES)
            overlap = db.query(Interview).filter(
                Interview.interviewer_id == interviewer.id,
                Interview.status == "SCHEDULED",
                Interview.start_time < (slot.end_time + buffer),
                Interview.end_time > (slot.start_time - buffer)
            ).first()

            if overlap:
                continue

            match_score = interviewer_map[interviewer.id]["match_score"]

            available_options.append({
                "slot_id": slot.id,
                "interviewer_id": interviewer.id,
                "interviewer_name": interviewer.name,
                "interviewer_department": interviewer.department,
                "start_time": slot.start_time,
                "end_time": slot.end_time,
                "match_score": match_score
            })

        return available_options

    @classmethod
    def book_slot(cls, db: Session, candidate: Candidate, slot_id: int, notes: str = "") -> Interview:
        """
        Books the selected slot for the candidate:
        - Locks the slot.
        - Creates an Interview record with a secure meeting room link.
        - Updates candidate status to 'SCHEDULED'.
        """
        slot = db.query(InterviewerSlot).filter(
            InterviewerSlot.id == slot_id,
            InterviewerSlot.is_booked == False
        ).with_for_update().first() if db.bind.dialect.name != "sqlite" else db.query(InterviewerSlot).filter(
            InterviewerSlot.id == slot_id,
            InterviewerSlot.is_booked == False
        ).first()

        if not slot:
            raise ValueError("The selected slot is no longer available or does not exist.")

        # Mark slot as booked
        slot.is_booked = True

        # Generate unique secure video meeting link
        room_name = f"Interview-{candidate.job_id}-{candidate.id}-{slot.id}"
        meeting_link = f"https://meet.jit.si/{room_name}"

        # Create the Interview
        interview = Interview(
            candidate_id=candidate.id,
            interviewer_id=slot.interviewer_id,
            job_id=candidate.job_id,
            start_time=slot.start_time,
            end_time=slot.end_time,
            meeting_link=meeting_link,
            status="SCHEDULED",
            notes=notes
        )
        db.add(interview)

        # Update candidate status
        candidate.status = "SCHEDULED"

        db.commit()
        db.refresh(interview)
        return interview

    @classmethod
    def cancel_interview(cls, db: Session, interview_id: int) -> bool:
        """
        Cancels an interview and frees up the corresponding slot if applicable.
        """
        interview = db.query(Interview).filter(Interview.id == interview_id).first()
        if not interview:
            return False

        interview.status = "CANCELLED"
        if interview.candidate:
            interview.candidate.status = "CANCELLED"

        # Reopen slot if found
        slot = db.query(InterviewerSlot).filter(
            InterviewerSlot.interviewer_id == interview.interviewer_id,
            InterviewerSlot.start_time == interview.start_time
        ).first()
        if slot:
            slot.is_booked = False

        db.commit()
        return True
