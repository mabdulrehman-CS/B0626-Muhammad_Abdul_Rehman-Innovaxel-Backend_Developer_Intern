from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class AppException(Exception):
    def __init__(self, status_code: int, message: str, code: str):
        self.status_code = status_code
        self.message = message
        self.code = code
        super().__init__(message)

class EventNotFoundException(AppException):
    def __init__(self, event_id: str = ""):
        super().__init__(
            status_code=404,
            message=f"Event not found{f': {event_id}' if event_id else ''}",
            code="EVENT_NOT_FOUND",
        )


class DuplicateEventNameException(AppException):
    def __init__(self, name: str = ""):
        super().__init__(
            status_code=409,
            message=f"An event with this name already exists{f': {name}' if name else ''}",
            code="DUPLICATE_EVENT_NAME",
        )


class EventFullException(AppException):
    def __init__(self):
        super().__init__(
            status_code=400,
            message="Event is full — no available seats",
            code="EVENT_FULL",
        )


class InvalidDateException(AppException):
    def __init__(self, detail: str = "event_date must be strictly in the future"):
        super().__init__(status_code=422, message=detail, code="INVALID_DATE")


class InvalidSeatsException(AppException):
    def __init__(self, detail: str = "total_seats must be a positive integer (> 0)"):
        super().__init__(status_code=422, message=detail, code="INVALID_SEATS")


class AlreadyRegisteredException(AppException):
    def __init__(self):
        super().__init__(
            status_code=409,
            message="User is already actively registered for this event",
            code="ALREADY_REGISTERED",
        )


class RegistrationNotFoundException(AppException):
    def __init__(self, registration_id: str = ""):
        super().__init__(
            status_code=404,
            message=f"Registration not found{f': {registration_id}' if registration_id else ''}",
            code="REGISTRATION_NOT_FOUND",
        )


class AlreadyCancelledException(AppException):
    def __init__(self):
        super().__init__(
            status_code=400,
            message="Registration is already cancelled",
            code="ALREADY_CANCELLED",
        )


def register_exception_handlers(app: FastAPI) -> None:

    @app.exception_handler(AppException)
    async def app_exception_handler(_request: Request, exc: AppException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": True, "message": exc.message, "code": exc.code},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        _request: Request, exc: RequestValidationError
    ):
        errors = exc.errors()
        for err in errors:
            loc = err.get("loc", [])
            field = loc[-1] if loc else ""
            msg = err.get("msg", "").lower()

            if field == "event_date" or "future" in msg:
                return JSONResponse(
                    status_code=422,
                    content={
                        "error": True,
                        "message": "event_date must be strictly in the future",
                        "code": "INVALID_DATE",
                    },
                )
            if field == "total_seats":
                return JSONResponse(
                    status_code=422,
                    content={
                        "error": True,
                        "message": "total_seats must be a positive integer (> 0)",
                        "code": "INVALID_SEATS",
                    },
                )

        messages = "; ".join(
            f"{'.'.join(str(p) for p in e.get('loc', []))}: {e.get('msg', '')}"
            for e in errors
        )
        return JSONResponse(
            status_code=422,
            content={
                "error": True,
                "message": f"Validation error — {messages}",
                "code": "VALIDATION_ERROR",
            },
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(_request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content={
                "error": True,
                "message": "An unexpected internal error occurred",
                "code": "INTERNAL_ERROR",
            },
        )
