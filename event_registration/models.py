from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Event(Base):
    __tablename__ = "events"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False, index=True)
    total_seats = Column(Integer, nullable=False)
    available_seats = Column(Integer, nullable=False)
    event_date = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), default=_utcnow)

    registrations = relationship(
        "Registration", back_populates="event", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Event(id={self.id!r}, name={self.name!r})>"


class Registration(Base):
    __tablename__ = "registrations"

    id = Column(String, primary_key=True, index=True)
    event_id = Column(String, ForeignKey("events.id"), nullable=False, index=True)
    user_name = Column(String, nullable=False)
    registered_at = Column(DateTime(timezone=True), default=_utcnow)
    status = Column(String, nullable=False, default="active")

    event = relationship("Event", back_populates="registrations")

    __table_args__ = (
        UniqueConstraint("event_id", "user_name", "status", name="uq_active_reg"),
    )

    def __repr__(self) -> str:
        return (
            f"<Registration(id={self.id!r}, event_id={self.event_id!r}, "
            f"user={self.user_name!r}, status={self.status!r})>"
        )
