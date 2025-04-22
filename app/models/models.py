from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime


class Jogger(BaseModel):
    email: EmailStr
    name: str


class AppAdmin(BaseModel):
    admin_email: EmailStr


class EventOrganizer(BaseModel):
    email: EmailStr
    name: str


class JoggingRoute(BaseModel):
    route_id: Optional[int] = None
    route_name: str
    distance: float
    avg_pace: Optional[float] = None


class RouteAdmin(BaseModel):
    admin_email: EmailStr
    route_id: int


class JoggingEvent(BaseModel):
    event_id: Optional[int] = None
    event_name: str
    event_date: datetime
    max_participants: int


class EventEM(BaseModel):
    organizer_email: EmailStr
    event_id: int


class Jogging(BaseModel):
    session_id: Optional[int] = None
    start_dt: datetime
    end_dt: datetime
    distance: Optional[float] = None
    jogger_email: EmailStr
    route_id: Optional[int] = None


class EventRegistration(BaseModel):
    event_id: int
    jogger_email: EmailStr
    timestamp: Optional[datetime] = None


class RouteReview(BaseModel):
    review_id: Optional[int] = None
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None
    route_id: int
    jogger_email: EmailStr


class EventReview(BaseModel):
    review_id: Optional[int] = None
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None
    event_id: int
    jogger_email: EmailStr


class EventSession(BaseModel):
    event_id: int
    session_id: int


class LeaderboardEntry(BaseModel):
    event_id: int
    jogger_name: str
    finish_time: int
    rank: int
