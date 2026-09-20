import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from backend.app.database import engine, Base, SessionLocal
from backend.app.services.seed_data import seed_database
from backend.app.models import User, Job, Candidate, InterviewerSlot, Interview
from backend.app.services.matching_engine import MatchingEngine
from backend.app.services.calendar_service import CalendarService

def run_tests():
    print("[1] Initializing Database Schema...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    print("[2] Seeding Demo Data...")
    seed_database(db, force_reset=True)

    users_count = db.query(User).count()
    jobs_count = db.query(Job).count()
    candidates_count = db.query(Candidate).count()
    slots_count = db.query(InterviewerSlot).count()
    interviews_count = db.query(Interview).count()

    print(f"    - Users (Recruiter/Interviewers): {users_count}")
    print(f"    - Job Openings: {jobs_count}")
    print(f"    - Candidates: {candidates_count}")
    print(f"    - Availability Slots: {slots_count}")
    print(f"    - Interviews: {interviews_count}")

    assert users_count >= 5, "Users not seeded properly"
    assert jobs_count >= 3, "Jobs not seeded properly"
    assert slots_count > 0, "Slots not seeded properly"

    print("[3] Testing Matching Engine for an Invited Candidate...")
    cand = db.query(Candidate).filter(Candidate.status == "INVITED").first()
    assert cand is not None, "No invited candidate found"
    print(f"    Candidate: {cand.name} for Job: {cand.job.title}")

    available_slots = MatchingEngine.get_available_slots_for_candidate(db, cand)
    print(f"    Found {len(available_slots)} available slots matching candidate's job skills.")
    assert len(available_slots) > 0, "No available slots returned by matching engine"

    first_slot = available_slots[0]
    print(f"    Selected Slot ID: {first_slot['slot_id']} with Interviewer: {first_slot['interviewer_name']} (Match: {first_slot['match_score']}%)")

    print("[4] Testing Slot Booking...")
    interview = MatchingEngine.book_slot(db, cand, first_slot['slot_id'], notes="Test college project booking")
    print(f"    Booked Interview ID: {interview.id}, Status: {interview.status}")
    assert interview.status == "SCHEDULED", "Interview not marked as SCHEDULED"
    assert cand.status == "SCHEDULED", "Candidate not marked as SCHEDULED"

    print("[5] Testing Calendar (.ics) Generation...")
    ics_bytes = CalendarService.generate_ics(interview)
    assert len(ics_bytes) > 0, "ICS file is empty"
    assert b"BEGIN:VCALENDAR" in ics_bytes, "Invalid ICS format"
    assert b"BEGIN:VEVENT" in ics_bytes, "Invalid VEVENT in ICS"
    print(f"    ICS Generated Successfully! Size: {len(ics_bytes)} bytes")

    print("\n[SUCCESS] All verification tests passed flawlessly!")
    db.close()

if __name__ == "__main__":
    run_tests()
