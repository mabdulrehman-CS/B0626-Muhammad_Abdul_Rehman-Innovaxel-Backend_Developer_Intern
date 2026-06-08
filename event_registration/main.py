from fastapi import Depends, FastAPI, Query
from sqlalchemy.orm import Session

from crud import (
    cancel_registration,
    create_event,
    get_event_detail,
    list_events,
    list_registrations,
    register_user,
    _split_dt,
)
from database import get_db, init_db
from exceptions import register_exception_handlers
from schemas import (
    ErrorResponse,
    EventCreateRequest,
    EventDetailResponse,
    EventListItem,
    EventListResponse,
    EventResponse,
    RegisterUserRequest,
    RegistrationListItem,
    RegistrationListResponse,
    RegistrationResponse,
)

app = FastAPI(
    title="Event Registration System API",
    description="REST API for creating events, registering users, and managing registrations.",
    version="1.0.0",
)

register_exception_handlers(app)


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/", tags=["Health"])
def root():
    return {"status": "ok", "service": "Event Registration System API"}


@app.post("/events", response_model=EventResponse, status_code=201, tags=["Events"],
          responses={409: {"model": ErrorResponse}, 422: {"model": ErrorResponse}})
def create_event_endpoint(body: EventCreateRequest, db: Session = Depends(get_db)):
    event = create_event(db, name=body.event_name, total_seats=body.total_seats, event_date=body.event_date)
    ed = _split_dt(event.event_date)
    cd = _split_dt(event.created_at) if event.created_at else {"date": None, "time": None}
    return EventResponse(
        event_id=event.id, event_name=event.name,
        event_date=ed["date"], event_time=ed["time"],
        total_seats=event.total_seats, available_seats=event.available_seats,
        created_date=cd["date"], created_time=cd["time"],
    )


@app.get("/events", response_model=EventListResponse, tags=["Events"])
def list_events_endpoint(
    upcoming_only: bool = Query(False),
    sort_by_date: bool = Query(False),
    db: Session = Depends(get_db),
):
    items = list_events(db, upcoming_only=upcoming_only, sort_by_date=sort_by_date)
    return EventListResponse(events=[EventListItem(**item) for item in items])


@app.get("/events/{event_id}", response_model=EventDetailResponse, tags=["Events"],
         responses={404: {"model": ErrorResponse}})
def get_event_endpoint(event_id: str, db: Session = Depends(get_db)):
    detail = get_event_detail(db, event_id)
    return EventDetailResponse(**detail)


@app.post("/events/{event_id}/register", response_model=RegistrationResponse, status_code=201,
          tags=["Registrations"], responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}})
def register_user_endpoint(event_id: str, body: RegisterUserRequest, db: Session = Depends(get_db)):
    reg = register_user(db, event_id=event_id, user_name=body.user_name)
    rd = _split_dt(reg.registered_at)
    return RegistrationResponse(
        registration_id=reg.id, event_id=reg.event_id, user_name=reg.user_name,
        registered_date=rd["date"], registered_time=rd["time"], status=reg.status,
    )


@app.get("/events/{event_id}/registrations", response_model=RegistrationListResponse, tags=["Registrations"],
         responses={404: {"model": ErrorResponse}})
def list_registrations_endpoint(event_id: str, db: Session = Depends(get_db)):
    regs = list_registrations(db, event_id)
    return RegistrationListResponse(registrations=[
        RegistrationListItem(
            registration_id=r.id, user_name=r.user_name,
            registered_date=_split_dt(r.registered_at)["date"],
            registered_time=_split_dt(r.registered_at)["time"],
        ) for r in regs
    ])


@app.delete("/registrations/{registration_id}", response_model=RegistrationResponse, tags=["Registrations"],
            responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}})
def cancel_registration_endpoint(registration_id: str, db: Session = Depends(get_db)):
    reg = cancel_registration(db, registration_id)
    rd = _split_dt(reg.registered_at)
    return RegistrationResponse(
        registration_id=reg.id, event_id=reg.event_id, user_name=reg.user_name,
        registered_date=rd["date"], registered_time=rd["time"], status=reg.status,
    )
