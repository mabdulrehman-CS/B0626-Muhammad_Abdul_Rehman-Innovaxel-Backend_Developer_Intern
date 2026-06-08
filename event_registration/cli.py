import sys

import requests
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
from rich.text import Text

console = Console()
BASE_URL = "http://127.0.0.1:8000"


def _error(msg: str):
    console.print(f"[bold red]✗ Error:[/bold red] {msg}")


def _success(msg: str):
    console.print(f"[bold green]✓[/bold green] {msg}")


def _handle_error_response(resp):
    try:
        body = resp.json()
        code = body.get("code", "UNKNOWN")
        message = body.get("message", resp.text)
        _error(f"[{code}] {message}")
    except Exception:
        _error(f"HTTP {resp.status_code}: {resp.text}")


def create_event():
    console.rule("[bold cyan]Create Event[/bold cyan]")
    name = Prompt.ask("[yellow]Event name[/yellow]")
    seats = Prompt.ask("[yellow]Total seats[/yellow]")
    date = Prompt.ask("[yellow]Event date (YYYY-MM-DD)[/yellow]")
    time = Prompt.ask("[yellow]Event time (HH:MM:SS)[/yellow]")

    try:
        seats = int(seats)
    except ValueError:
        _error("Total seats must be an integer")
        return

    resp = requests.post(f"{BASE_URL}/events", json={
        "event_name": name, "total_seats": seats, "event_date": f"{date}T{time}",
    })

    if resp.status_code == 201:
        ev = resp.json()
        _success(f"Event created! ID: {ev['event_id']}")
        table = Table(title="New Event")
        table.add_column("Field", style="cyan")
        table.add_column("Value", style="white")
        for k, v in ev.items():
            table.add_row(k, str(v))
        console.print(table)
    else:
        _handle_error_response(resp)


def register_user_cli():
    console.rule("[bold cyan]Register User[/bold cyan]")
    event_id = Prompt.ask("[yellow]Event ID[/yellow]")
    user_name = Prompt.ask("[yellow]User name[/yellow]")

    resp = requests.post(f"{BASE_URL}/events/{event_id}/register", json={"user_name": user_name})

    if resp.status_code == 201:
        reg = resp.json()
        _success(f"Registered! Registration ID: {reg['registration_id']}")
        table = Table(title="Registration")
        table.add_column("Field", style="cyan")
        table.add_column("Value", style="white")
        for k, v in reg.items():
            table.add_row(k, str(v))
        console.print(table)
    else:
        _handle_error_response(resp)


def view_events():
    console.rule("[bold cyan]View Events[/bold cyan]")
    upcoming = Prompt.ask("[yellow]Upcoming only? (y/n)[/yellow]")
    sort_date = Prompt.ask("[yellow]Sort by date? (y/n)[/yellow]")

    params = {}
    if upcoming.lower() == "y":
        params["upcoming_only"] = "true"
    if sort_date.lower() == "y":
        params["sort_by_date"] = "true"

    resp = requests.get(f"{BASE_URL}/events", params=params)

    if resp.status_code == 200:
        events = resp.json().get("events", [])
        if not events:
            console.print("[dim]No events found.[/dim]")
            return
        table = Table(title="Events", show_lines=True)
        table.add_column("Event ID", style="cyan")
        table.add_column("Name", style="white")
        table.add_column("Date", style="yellow")
        table.add_column("Time", style="yellow")
        table.add_column("Total", justify="right", style="green")
        table.add_column("Available", justify="right", style="magenta")
        table.add_column("Active Regs", justify="right", style="red")
        for ev in events:
            table.add_row(
                ev["event_id"], ev["event_name"],
                ev["event_date"], ev["event_time"],
                str(ev["total_seats"]), str(ev["available_seats"]),
                str(ev["total_active_registrations"]),
            )
        console.print(table)
    else:
        _handle_error_response(resp)


def view_registrations():
    console.rule("[bold cyan]View Event Registrations[/bold cyan]")
    event_id = Prompt.ask("[yellow]Event ID[/yellow]")

    resp = requests.get(f"{BASE_URL}/events/{event_id}/registrations")

    if resp.status_code == 200:
        regs = resp.json().get("registrations", [])
        if not regs:
            console.print("[dim]No active registrations.[/dim]")
            return
        table = Table(title="Active Registrations", show_lines=True)
        table.add_column("Reg ID", style="cyan")
        table.add_column("User Name", style="white")
        table.add_column("Date", style="yellow")
        table.add_column("Time", style="yellow")
        for r in regs:
            table.add_row(
                r["registration_id"], r["user_name"],
                r["registered_date"], r["registered_time"],
            )
        console.print(table)
    else:
        _handle_error_response(resp)


def cancel_registration_cli():
    console.rule("[bold cyan]Cancel Registration[/bold cyan]")
    reg_id = Prompt.ask("[yellow]Registration ID[/yellow]")

    resp = requests.delete(f"{BASE_URL}/registrations/{reg_id}")

    if resp.status_code == 200:
        reg = resp.json()
        _success(f"Registration {reg['registration_id']} cancelled.")
    else:
        _handle_error_response(resp)


MENU_OPTIONS = {
    "1": ("Create Event", create_event),
    "2": ("Register User", register_user_cli),
    "3": ("View Events", view_events),
    "4": ("View Event Registrations", view_registrations),
    "5": ("Cancel Registration", cancel_registration_cli),
    "6": ("Exit", None),
}


def main():
    console.print(Panel(
        Text("Event Registration System", style="bold white", justify="center"),
        subtitle="Interactive CLI", style="bold cyan",
    ))

    while True:
        console.print()
        for key, (label, _) in MENU_OPTIONS.items():
            console.print(f"  [bold cyan]{key}[/bold cyan]. {label}")
        console.print()

        choice = Prompt.ask("[bold yellow]Select an option[/bold yellow]", choices=list(MENU_OPTIONS.keys()), default="6")

        if choice == "6":
            console.print("[bold green]Goodbye![/bold green]")
            sys.exit(0)

        _, action = MENU_OPTIONS[choice]
        if action:
            try:
                action()
            except requests.ConnectionError:
                _error("Cannot connect to the API server. Is it running on http://127.0.0.1:8000?")
            except Exception as e:
                _error(str(e))


if __name__ == "__main__":
    main()
