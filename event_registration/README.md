# Event Registration System API

A REST API built with **FastAPI**, **SQLAlchemy**, and **SQLite** for managing events and user registrations.

## Features

- **CRUD Operations** — Create events, register users, view data, cancel registrations
- **Concurrency Safety** — Prevents overbooking
- **Interactive CLI** — Rich-based menu for easy interaction

## Project Structure

```
event_registration/
├── main.py              # FastAPI app, all routes
├── models.py            # SQLAlchemy ORM models
├── schemas.py           # Pydantic request/response schemas
├── database.py          # DB engine, session, WAL mode setup
├── crud.py              # All DB operations with locking logic
├── exceptions.py        # Custom exception classes + handlers
├── cli.py               # Rich-based interactive CLI
├── requirements.txt     # All dependencies pinned
└── README.md            # This file
```

## Setup Instructions

1. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   # Windows:
   .\venv\Scripts\activate
   # macOS/Linux:
   source venv/bin/activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the API server:**
   ```bash
   uvicorn main:app --reload
   ```
   API available at `http://127.0.0.1:8000`. Interactive docs at `http://127.0.0.1:8000/docs`.

4. **Run the CLI (optional):**
   ```bash
   python cli.py
   ```

## API Endpoints

| Method   | Endpoint                           | Description                      |
|----------|------------------------------------|----------------------------------|
| `GET`    | `/`                                | Health check                     |
| `POST`   | `/events`                          | Create a new event               |
| `GET`    | `/events`                          | List all events                  |
| `GET`    | `/events/{event_id}`               | Get event detail                 |
| `POST`   | `/events/{event_id}/register`      | Register a user for an event     |
| `GET`    | `/events/{event_id}/registrations` | List active registrations        |
| `DELETE` | `/registrations/{registration_id}` | Cancel a registration            |
