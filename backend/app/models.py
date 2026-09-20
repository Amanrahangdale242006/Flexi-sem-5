import datetime
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float
)
from sqlalchemy.orm import relationship
from backend.app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(120), unique=True, index=True, nullable=False)
    role = Column(String(50), default="INTERVIEWER")  # "RECRUITER", "INTERVIEWER"
    department = Column(String(100), default="Engineering")
    skills = Column(String(255), default="")  # Comma-separated: "Python, FastAPI, System Design"
    max_interviews_per_day = Column(Integer, default=3)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    slots = relationship("InterviewerSlot", back_populates="interviewer", cascade="all, delete-orphan")
    interviews = relationship("Interview", back_populates="interviewer")
    feedbacks = relationship("Feedback", back_populates="interviewer")

    def get_skill_list(self):
        if not self.skills:
            return []
        return [s.strip().lower() for s in self.skills.split(",") if s.strip()]


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(150), nullable=False)
    department = Column(String(100), default="Engineering")
    description = Column(Text, default="")
    required_skills = Column(String(255), default="")  # Comma-separated: "Python, SQL"
    experience_level = Column(String(50), default="Mid-Level")
    status = Column(String(50), default="OPEN")  # "OPEN", "CLOSED"
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    candidates = relationship("Candidate", back_populates="job", cascade="all, delete-orphan")
    interviews = relationship("Interview", back_populates="job")

    def get_required_skills_list(self):
        if not self.required_skills:
            return []
        return [s.strip().lower() for s in self.required_skills.split(",") if s.strip()]


class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(120), index=True, nullable=False)
    phone = Column(String(30), default="")
    resume_url = Column(String(255), default="")
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    status = Column(String(50), default="INVITED")  # "INVITED", "SCHEDULED", "COMPLETED", "CANCELLED", "REJECTED", "HIRED"
    invite_token = Column(String(64), unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    job = relationship("Job", back_populates="candidates")
    interviews = relationship("Interview", back_populates="candidate", cascade="all, delete-orphan")


class InterviewerSlot(Base):
    __tablename__ = "interviewer_slots"

    id = Column(Integer, primary_key=True, index=True)
    interviewer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    start_time = Column(DateTime, nullable=False, index=True)
    end_time = Column(DateTime, nullable=False)
    is_booked = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    interviewer = relationship("User", back_populates="slots")


class Interview(Base):
    __tablename__ = "interviews"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False)
    interviewer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    start_time = Column(DateTime, nullable=False, index=True)
    end_time = Column(DateTime, nullable=False)
    meeting_link = Column(String(255), default="")
    status = Column(String(50), default="SCHEDULED")  # "SCHEDULED", "COMPLETED", "CANCELLED", "RESCHEDULED"
    notes = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    candidate = relationship("Candidate", back_populates="interviews")
    interviewer = relationship("User", back_populates="interviews")
    job = relationship("Job", back_populates="interviews")
    feedback = relationship("Feedback", uselist=False, back_populates="interview", cascade="all, delete-orphan")


class Feedback(Base):
    __tablename__ = "feedbacks"

    id = Column(Integer, primary_key=True, index=True)
    interview_id = Column(Integer, ForeignKey("interviews.id"), unique=True, nullable=False)
    interviewer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    technical_score = Column(Integer, default=3)      # 1 to 5
    communication_score = Column(Integer, default=3)  # 1 to 5
    problem_solving_score = Column(Integer, default=3)# 1 to 5
    overall_recommendation = Column(String(50), default="HIRE") # "STRONG_HIRE", "HIRE", "HOLD", "REJECT"
    strengths = Column(Text, default="")
    weaknesses = Column(Text, default="")
    notes = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    interview = relationship("Interview", back_populates="feedback")
    interviewer = relationship("User", back_populates="feedbacks")
