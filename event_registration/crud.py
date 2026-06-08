import random
import string
from datetime import datetime, timezone
from typing import List

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from exceptions import (
    AlreadyCancelledException,
    AlreadyRegisteredException,
    DuplicateEventNameException,
    EventFullException,
    EventNotFoundException,
    RegistrationNotFoundException,
)
from models import Event, Registration


def _new_id() -> str:
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=5))


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _split_dt(dt: datetime) -> dict:
    return {"date": dt.strftime("%Y-%m-%d"), "time": dt.strftime("%H:%M:%S")}


def create_event(
    db: Session,
    name: str,
    total_seats: int,
    event_date: datetime,
) -> Event:
    existing = db.query(Event).filter(Event.name == name).first()
    if existing:
        raise DuplicateEventNameException(name)

    event = Event(
        id=_new_id(),
        name=name,
        total_seats=total_seats,
        available_seats=total_seats,
        event_date=event_date,
        created_at=_utcnow(),
    )
    db.add(event)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise DuplicateEventNameException(name)
    db.refresh(event)
    return event


def get_event(db: Session, event_id: str) -> Event:
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise EventNotFoundException(event_id)
    return event


def list_events(
    db: Session,
    upcoming_only: bool = False,
    sort_by_date: bool = False,
) -> List[dict]:
    query = db.query(Event)

    if upcoming_only:
        query = query.filter(Event.event_date > _utcnow())

    if sort_by_date:
        query = query.order_by(Event.event_date.asc())

    events = query.all()
    result = []
    for ev in events:
        active_count = (
            db.query(func.count(Registration.id))
            .filter(Registration.event_id == ev.id, Registration.status == "active")
            .scalar()
        )
        ed = _split_dt(ev.event_date)
        result.append(
            {
                "event_id": ev.id,
                "event_name": ev.name,
                "event_date": ed["date"],
                "event_time": ed["time"],
                "total_seats": ev.total_seats,
                "available_seats": ev.available_seats,
                "total_active_registrations": active_count or 0,
            }
        )
    return result


def get_event_detail(db: Session, event_id: str) -> dict:
    event = get_event(db, event_id)
    active_count = (
        db.query(func.count(Registration.id))
        .filter(Registration.event_id == event.id, Registration.status == "active")
        .scalar()
    ) or 0

    ed = _split_dt(event.event_date)
    cd = _split_dt(event.created_at) if event.created_at else {"date": None, "time": None}

    return {
        "event_id": event.id,
        "event_name": event.name,
        "event_date": ed["date"],
        "event_time": ed["time"],
        "total_seats": event.total_seats,
        "available_seats": event.available_seats,
        "total_active_registrations": active_count,
        "seats_consistent": event.available_seats == (event.total_seats - active_count),
        "created_date": cd["date"],
        "created_time": cd["time"],
    }


def register_user(db: Session, event_id: str, user_name: str) -> Registration:
    event = (
        db.query(Event)
        .filter(Event.id == event_id)
        .with_for_update()
        .first()
    )
    if not event:
        raise EventNotFoundException(event_id)

    if event.available_seats <= 0:
        raise EventFullException()

    existing = (
        db.query(Registration)
        .filter(
            Registration.event_id == event_id,
            Registration.user_name == user_name,
            Registration.status == "active",
        )
        .first()
    )
    if existing:
        raise AlreadyRegisteredException()

    event.available_seats -= 1

    registration = Registration(
        id=_new_id(),
        event_id=event_id,
        user_name=user_name,
        registered_at=_utcnow(),
        status="active",
    )
    db.add(registration)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise AlreadyRegisteredException()

    db.refresh(registration)
    return registration


def list_registrations(db: Session, event_id: str) -> List[Registration]:
    get_event(db, event_id)
    return (
        db.query(Registration)
        .filter(Registration.event_id == event_id, Registration.status == "active")
        .order_by(Registration.registered_at.asc())
        .all()
    )


def cancel_registration(db: Session, registration_id: str) -> Registration:
    registration = (
        db.query(Registration).filter(Registration.id == registration_id).first()
    )
    if not registration:
        raise RegistrationNotFoundException(registration_id)

    if registration.status == "cancelled":
        raise AlreadyCancelledException()

    event = (
        db.query(Event)
        .filter(Event.id == registration.event_id)
        .with_for_update()
        .first()
    )

    registration.status = "cancelled"
    event.available_seats += 1

    db.commit()
    db.refresh(registration)
    return registration
