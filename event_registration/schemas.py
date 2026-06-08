from datetime import datetime, timezone
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class EventCreateRequest(BaseModel):
    event_name: str = Field(..., min_length=1, description="Unique name of the event")
    total_seats: int = Field(..., gt=0, description="Total number of seats (> 0)")
    event_date: datetime = Field(..., description="Event date/time (must be in the future)")

    @field_validator("event_name")
    @classmethod
    def event_name_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("event_name must not be empty or whitespace")
        return v.strip()

    @field_validator("event_date")
    @classmethod
    def event_date_must_be_future(cls, v: datetime) -> datetime:
        now = datetime.now(timezone.utc)
        check = v if v.tzinfo else v.replace(tzinfo=timezone.utc)
        if check <= now:
            raise ValueError("event_date must be strictly in the future")
        return v


class RegisterUserRequest(BaseModel):
    user_name: str = Field(..., min_length=1, description="Name of the user registering")

    @field_validator("user_name")
    @classmethod
    def user_name_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("user_name must not be empty or whitespace")
        return v.strip()


class EventResponse(BaseModel):
    event_id: str
    event_name: str
    event_date: str
    event_time: str
    total_seats: int
    available_seats: int
    created_date: Optional[str] = None
    created_time: Optional[str] = None


class EventListItem(BaseModel):
    event_id: str
    event_name: str
    event_date: str
    event_time: str
    total_seats: int
    available_seats: int
    total_active_registrations: int


class EventDetailResponse(BaseModel):
    event_id: str
    event_name: str
    event_date: str
    event_time: str
    total_seats: int
    available_seats: int
    total_active_registrations: int
    seats_consistent: bool
    created_date: Optional[str] = None
    created_time: Optional[str] = None


class RegistrationResponse(BaseModel):
    registration_id: str
    event_id: str
    user_name: str
    registered_date: str
    registered_time: str
    status: str


class RegistrationListItem(BaseModel):
    registration_id: str
    user_name: str
    registered_date: str
    registered_time: str


class ErrorResponse(BaseModel):
    error: bool = True
    message: str
    code: str


class EventListResponse(BaseModel):
    events: List[EventListItem]


class RegistrationListResponse(BaseModel):
    registrations: List[RegistrationListItem]
