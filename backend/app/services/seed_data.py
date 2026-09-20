import datetime
import uuid
from sqlalchemy.orm import Session
from backend.app.models import User, Job, Candidate, InterviewerSlot, Interview, Feedback

def seed_database(db: Session, force_reset: bool = False):
    """
    Populates database with realistic college presentation demo data.
    """
    if force_reset:
        db.query(Feedback).delete()
        db.query(Interview).delete()
        db.query(InterviewerSlot).delete()
        db.query(Candidate).delete()
        db.query(Job).delete()
        db.query(User).delete()
        db.commit()

    # Check if data already exists
    if db.query(User).count() > 0:
        return

    # 1. Create Users (Recruiter & Interviewers)
    recruiter = User(
        name="Sarah Jenkins",
        email="sarah.jenkins@techcorp.com",
        role="RECRUITER",
        department="Talent Acquisition",
        skills="",
        max_interviews_per_day=5
    )

    interviewers = [
        User(
            name="Dr. Alex Rivera",
            email="alex.rivera@techcorp.com",
            role="INTERVIEWER",
            department="Backend & Cloud",
            skills="Python, FastAPI, Docker, Kubernetes, PostgreSQL, System Design",
            max_interviews_per_day=3
        ),
        User(
            name="Elena Chen",
            email="elena.chen@techcorp.com",
            role="INTERVIEWER",
            department="Frontend & Mobile",
            skills="React, TypeScript, Tailwind CSS, Next.js, Redux, UI/UX",
            max_interviews_per_day=3
        ),
        User(
            name="Marcus Vance",
            email="marcus.vance@techcorp.com",
            role="INTERVIEWER",
            department="AI & Data Science",
            skills="Python, PyTorch, Machine Learning, NLP, Data Engineering, SQL",
            max_interviews_per_day=2
        ),
        User(
            name="Priya Sharma",
            email="priya.sharma@techcorp.com",
            role="INTERVIEWER",
            department="DevOps & Security",
            skills="AWS, Linux, CI/CD, Terraform, Cyber Security, Python",
            max_interviews_per_day=3
        )
    ]

    db.add(recruiter)
    for interviewer in interviewers:
        db.add(interviewer)
    db.commit()

    # 2. Create Jobs
    jobs = [
        Job(
            title="Senior Python / Backend Engineer",
            department="Engineering",
            description="Looking for an experienced backend developer to architect scalable microservices and APIs.",
            required_skills="Python, FastAPI, PostgreSQL, System Design",
            experience_level="Senior (3-5 yrs)",
            status="OPEN"
        ),
        Job(
            title="Frontend React Specialist",
            department="Product",
            description="Passionate frontend engineer to build responsive and intuitive customer-facing web applications.",
            required_skills="React, TypeScript, Tailwind CSS",
            experience_level="Mid-Level (2-4 yrs)",
            status="OPEN"
        ),
        Job(
            title="Machine Learning Engineer",
            department="Data & AI",
            description="Develop and deploy cutting-edge deep learning and LLM fine-tuning pipelines.",
            required_skills="Python, PyTorch, Machine Learning, SQL",
            experience_level="Mid-Level (2-3 yrs)",
            status="OPEN"
        )
    ]

    for job in jobs:
        db.add(job)
    db.commit()

    # 3. Create Interviewer Availability Slots for the next 5 days
    now = datetime.datetime.utcnow()
    # Align to tomorrow 9:00 AM
    tomorrow = (now + datetime.timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0)

    for interviewer in interviewers:
        for day_offset in range(1, 5):
            base_day = tomorrow + datetime.timedelta(days=day_offset)
            # Add 3 slots per day: 10:00 AM, 2:00 PM, 4:00 PM
            slot_hours = [10, 14, 16]
            for h in slot_hours:
                start_dt = base_day.replace(hour=h, minute=0)
                end_dt = start_dt + datetime.timedelta(minutes=45)
                slot = InterviewerSlot(
                    interviewer_id=interviewer.id,
                    start_time=start_dt,
                    end_time=end_dt,
                    is_booked=False
                )
                db.add(slot)
    db.commit()

    # 4. Create Candidates
    candidates = [
        Candidate(
            name="Rahul Verma",
            email="rahul.verma@example.com",
            phone="+91 98765 43210",
            resume_url="https://drive.google.com/sample_resume_rahul",
            job_id=jobs[0].id,
            status="INVITED",
            invite_token=str(uuid.uuid4())[:16]
        ),
        Candidate(
            name="Samantha Reed",
            email="samantha.reed@example.com",
            phone="+1 555-0192",
            resume_url="https://drive.google.com/sample_resume_samantha",
            job_id=jobs[1].id,
            status="INVITED",
            invite_token=str(uuid.uuid4())[:16]
        ),
        Candidate(
            name="David Miller",
            email="david.miller@example.com",
            phone="+1 555-0144",
            resume_url="https://drive.google.com/sample_resume_david",
            job_id=jobs[2].id,
            status="SCHEDULED",
            invite_token=str(uuid.uuid4())[:16]
        ),
        Candidate(
            name="Ananya Iyer",
            email="ananya.iyer@example.com",
            phone="+91 91234 56789",
            resume_url="https://drive.google.com/sample_resume_ananya",
            job_id=jobs[0].id,
            status="COMPLETED",
            invite_token=str(uuid.uuid4())[:16]
        )
    ]

    for cand in candidates:
        db.add(cand)
    db.commit()

    # 5. Create a Scheduled Interview for David Miller
    david = candidates[2]
    # Pick Alex Rivera's first slot
    alex = interviewers[0]
    david_slot = db.query(InterviewerSlot).filter(
        InterviewerSlot.interviewer_id == alex.id,
        InterviewerSlot.is_booked == False
    ).first()

    if david_slot:
        david_slot.is_booked = True
        david_interview = Interview(
            candidate_id=david.id,
            interviewer_id=alex.id,
            job_id=jobs[2].id,
            start_time=david_slot.start_time,
            end_time=david_slot.end_time,
            meeting_link=f"https://meet.jit.si/Interview-ML-{david.id}",
            status="SCHEDULED",
            notes="Discuss previous transformer architecture projects."
        )
        db.add(david_interview)
        db.commit()

    # 6. Create a Completed Interview + Feedback for Ananya Iyer (to show past evaluation & charts)
    ananya = candidates[3]
    past_start = now - datetime.timedelta(days=2, hours=3)
    past_end = past_start + datetime.timedelta(minutes=45)

    ananya_interview = Interview(
        candidate_id=ananya.id,
        interviewer_id=alex.id,
        job_id=jobs[0].id,
        start_time=past_start,
        end_time=past_end,
        meeting_link=f"https://meet.jit.si/Interview-Backend-{ananya.id}",
        status="COMPLETED",
        notes="Candidate has strong grasp of distributed database indexing."
    )
    db.add(ananya_interview)
    db.commit()

    ananya_feedback = Feedback(
        interview_id=ananya_interview.id,
        interviewer_id=alex.id,
        technical_score=5,
        communication_score=4,
        problem_solving_score=5,
        overall_recommendation="STRONG_HIRE",
        strengths="Exceptional understanding of concurrency, async Python, and database normalization.",
        weaknesses="Could improve on cloud deployment and CI/CD pipelines.",
        notes="High potential candidate. Recommended for next round with Engineering Director."
    )
    db.add(ananya_feedback)
    db.commit()
