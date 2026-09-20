from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

# User Schemas
class UserBase(BaseModel):
    name: str
    email: str
    role: str = "INTERVIEWER"
    department: str = "Engineering"
    skills: str = ""
    max_interviews_per_day: int = 3

class UserCreate(UserBase):
    pass

class UserResponse(UserBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# Job Schemas
class JobBase(BaseModel):
    title: str
    department: str = "Engineering"
    description: str = ""
    required_skills: str = ""
    experience_level: str = "Mid-Level"
    status: str = "OPEN"

class JobCreate(JobBase):
    pass

class JobResponse(JobBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# Candidate Schemas
class CandidateBase(BaseModel):
    name: str
    email: str
    phone: Optional[str] = ""
    resume_url: Optional[str] = ""
    job_id: int

class CandidateCreate(CandidateBase):
    pass

class CandidateResponse(CandidateBase):
    id: int
    status: str
    invite_token: str
    created_at: datetime
    job_title: Optional[str] = None

    class Config:
        from_attributes = True


# Slot Schemas
class SlotBase(BaseModel):
    start_time: datetime
    end_time: datetime

class SlotCreate(SlotBase):
    interviewer_id: int

class SlotResponse(SlotBase):
    id: int
    interviewer_id: int
    is_booked: bool
    created_at: datetime
    interviewer_name: Optional[str] = None

    class Config:
        from_attributes = True


# Booking Schemas
class BookSlotRequest(BaseModel):
    token: str
    slot_id: int
    notes: Optional[str] = ""

class AvailableSlotOption(BaseModel):
    slot_id: int
    interviewer_id: int
    interviewer_name: str
    start_time: datetime
    end_time: datetime
    match_score: float = 100.0


# Interview Schemas
class InterviewBase(BaseModel):
    candidate_id: int
    interviewer_id: int
    job_id: int
    start_time: datetime
    end_time: datetime
    meeting_link: Optional[str] = ""
    status: str = "SCHEDULED"
    notes: Optional[str] = ""

class InterviewCreate(InterviewBase):
    pass

class InterviewResponse(InterviewBase):
    id: int
    created_at: datetime
    candidate_name: Optional[str] = None
    candidate_email: Optional[str] = None
    interviewer_name: Optional[str] = None
    job_title: Optional[str] = None
    has_feedback: bool = False

    class Config:
        from_attributes = True


# Feedback Schemas
class FeedbackCreate(BaseModel):
    interview_id: int
    technical_score: int = Field(ge=1, le=5)
    communication_score: int = Field(ge=1, le=5)
    problem_solving_score: int = Field(ge=1, le=5)
    overall_recommendation: str = "HIRE"
    strengths: str = ""
    weaknesses: str = ""
    notes: str = ""

class FeedbackResponse(FeedbackCreate):
    id: int
    interviewer_id: int
    created_at: datetime

    class Config:
        from_attributes = True


# Analytics & Dashboard Stats
class DashboardStats(BaseModel):
    total_interviews: int
    scheduled_interviews: int
    completed_interviews: int
    cancelled_interviews: int
    total_candidates: int
    total_interviewers: int
    total_jobs: int
