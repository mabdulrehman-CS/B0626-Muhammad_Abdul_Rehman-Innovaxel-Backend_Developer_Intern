import requests
import json
import sys

BASE = "http://127.0.0.1:8000"
PASS = 0
FAIL = 0


def test(name, resp, expected_status, check_fn=None):
    global PASS, FAIL
    ok = resp.status_code == expected_status
    body = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
    if ok and check_fn:
        ok = check_fn(body)
    status = "PASS" if ok else "FAIL"
    if ok:
        PASS += 1
    else:
        FAIL += 1
    print(f"  [{status}] {name} — HTTP {resp.status_code} (expected {expected_status})")
    if not ok:
        print(f"         Body: {json.dumps(body, indent=2, default=str)}")
    return body


print("=" * 60)
print("EVENT REGISTRATION SYSTEM — API TESTS")
print("=" * 60)

print("\n--- Create Event ---")
r = requests.post(f"{BASE}/events", json={
    "event_name": "Tech Conference 2026",
    "total_seats": 3,
    "event_date": "2026-12-25T10:00:00"
})
ev = test("Create event (success)", r, 201)
EVENT_ID = ev.get("event_id", "")

r = requests.post(f"{BASE}/events", json={
    "event_name": "Tech Conference 2026",
    "total_seats": 50,
    "event_date": "2026-12-26T10:00:00"
})
test("Duplicate event name", r, 409, lambda b: b.get("code") == "DUPLICATE_EVENT_NAME")

r = requests.post(f"{BASE}/events", json={
    "event_name": "Old Event",
    "total_seats": 10,
    "event_date": "2020-01-01T10:00:00"
})
test("Past event_date", r, 422, lambda b: b.get("code") == "INVALID_DATE")

r = requests.post(f"{BASE}/events", json={
    "event_name": "Zero Seats",
    "total_seats": 0,
    "event_date": "2026-12-25T10:00:00"
})
test("Zero total_seats", r, 422, lambda b: b.get("code") == "INVALID_SEATS")

r = requests.post(f"{BASE}/events", json={
    "event_name": "Neg Seats",
    "total_seats": -5,
    "event_date": "2026-12-25T10:00:00"
})
test("Negative total_seats", r, 422, lambda b: b.get("code") == "INVALID_SEATS")

r = requests.post(f"{BASE}/events", json={
    "event_name": "",
    "total_seats": 10,
    "event_date": "2026-12-25T10:00:00"
})
test("Empty event_name", r, 422)

r = requests.post(f"{BASE}/events", json={
    "event_name": "   ",
    "total_seats": 10,
    "event_date": "2026-12-25T10:00:00"
})
test("Whitespace-only event_name", r, 422)

print("\n--- Get Event ---")
r = requests.get(f"{BASE}/events/{EVENT_ID}")
test("Get event detail", r, 200, lambda b: b.get("seats_consistent") is True)

r = requests.get(f"{BASE}/events/nonexistent-id")
test("Event not found", r, 404, lambda b: b.get("code") == "EVENT_NOT_FOUND")

print("\n--- List Events ---")
r = requests.get(f"{BASE}/events")
test("List events", r, 200, lambda b: len(b.get("events", [])) >= 1)

r = requests.get(f"{BASE}/events", params={"upcoming_only": "true", "sort_by_date": "true"})
test("List events (upcoming + sorted)", r, 200)

print("\n--- Register User ---")
r = requests.post(f"{BASE}/events/{EVENT_ID}/register", json={"user_name": "Abdul"})
reg1 = test("Register user (success)", r, 201)
REG_ID_1 = reg1.get("registration_id", "")

r = requests.post(f"{BASE}/events/{EVENT_ID}/register", json={"user_name": "Abdul"})
test("Duplicate registration", r, 409, lambda b: b.get("code") == "ALREADY_REGISTERED")

r = requests.post(f"{BASE}/events/{EVENT_ID}/register", json={"user_name": "Alice"})
reg2 = test("Register second user", r, 201)
REG_ID_2 = reg2.get("registration_id", "")

r = requests.post(f"{BASE}/events/{EVENT_ID}/register", json={"user_name": "Bob"})
reg3 = test("Register third user (last seat)", r, 201)
REG_ID_3 = reg3.get("registration_id", "")

r = requests.post(f"{BASE}/events/{EVENT_ID}/register", json={"user_name": "Charlie"})
test("Event full", r, 400, lambda b: b.get("code") == "EVENT_FULL")

r = requests.post(f"{BASE}/events/fake-id/register", json={"user_name": "User1"})
test("Register — event not found", r, 404, lambda b: b.get("code") == "EVENT_NOT_FOUND")

r = requests.post(f"{BASE}/events/{EVENT_ID}/register", json={"user_name": ""})
test("Register — empty user_name", r, 422)

print("\n--- View Registrations ---")
r = requests.get(f"{BASE}/events/{EVENT_ID}/registrations")
test("View active registrations", r, 200, lambda b: len(b.get("registrations", [])) == 3)

print("\n--- Seat Consistency ---")
r = requests.get(f"{BASE}/events/{EVENT_ID}")
detail = test("Seats consistent (0 available)", r, 200, lambda b: b["available_seats"] == 0 and b["seats_consistent"])

print("\n--- Cancel Registration ---")
r = requests.delete(f"{BASE}/registrations/{REG_ID_3}")
test("Cancel registration (success)", r, 200, lambda b: b.get("status") == "cancelled")

r = requests.get(f"{BASE}/events/{EVENT_ID}")
test("Seat restored after cancel", r, 200, lambda b: b["available_seats"] == 1 and b["seats_consistent"])

r = requests.delete(f"{BASE}/registrations/{REG_ID_3}")
test("Already cancelled", r, 400, lambda b: b.get("code") == "ALREADY_CANCELLED")

r = requests.delete(f"{BASE}/registrations/nonexistent-id")
test("Registration not found", r, 404, lambda b: b.get("code") == "REGISTRATION_NOT_FOUND")

r = requests.get(f"{BASE}/events/{EVENT_ID}/registrations")
test("Cancelled reg excluded", r, 200, lambda b: len(b.get("registrations", [])) == 2)

r = requests.post(f"{BASE}/events/{EVENT_ID}/register", json={"user_name": "Bob"})
test("Re-register after cancel", r, 201)

print("\n" + "=" * 60)
print(f"RESULTS: {PASS} passed, {FAIL} failed out of {PASS + FAIL}")
print("=" * 60)
sys.exit(1 if FAIL else 0)
