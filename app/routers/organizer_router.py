from fastapi import APIRouter, Request, Form, Query, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import os
from typing import Optional
from datetime import datetime

from models.repositories import (
    JoggerRepository,
    EventRepository,
    RegistrationRepository,
    EventRepository,
)

router = APIRouter()

templates_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "templates"
)
templates = Jinja2Templates(directory=templates_path)


@router.get("/dashboard", response_class=HTMLResponse)
async def organizer_dashboard(
    request: Request,
    email: str = Query(..., description="Organizer email address"),
    success: Optional[str] = None,
    error: Optional[str] = None,
):
    """Organizer dashboard showing events organized by this organizer."""
    if not JoggerRepository.check_if_organizer(email):
        return RedirectResponse(url="/", status_code=303)

    events = EventRepository.get_events_by_organizer(email)

    for event in events:
        event["CurrentParticipants"] = RegistrationRepository.count_registrations(
            event["EventID"]
        )

    current_date = datetime.now()

    return templates.TemplateResponse(
        "organizer/dashboard.html",
        {
            "request": request,
            "email": email,
            "events": events,
            "title": "Event Organizer Dashboard",
            "success": success,
            "error": error,
            "current_date": current_date,
        },
    )


@router.get("/events/add", response_class=HTMLResponse)
async def add_event_form(
    request: Request, email: str = Query(..., description="Organizer email address")
):
    """Form to add a new event."""

    if not JoggerRepository.check_if_organizer(email):
        return RedirectResponse(url="/", status_code=303)

    return templates.TemplateResponse(
        "organizer/event_form.html",
        {"request": request, "email": email, "title": "Add Event", "action": "add"},
    )


@router.post("/events/add", response_class=HTMLResponse)
async def add_event(
    request: Request,
    email: str = Form(...),
    event_name: str = Form(...),
    event_date: datetime = Form(...),
    max_participants: int = Form(...),
):
    """Handle add event form submission."""

    if not JoggerRepository.check_if_organizer(email):
        return RedirectResponse(url="/", status_code=303)

    event_id = EventRepository.create_event(event_name, event_date, max_participants)

    if event_id:
        BaseRepository = EventRepository.__mro__[1]  # Get parent class
        query = "INSERT INTO event_em (OrganizerEmail, EventID) VALUES (%s, %s)"
        BaseRepository.execute_query(query, (email, event_id), commit=True)

        return RedirectResponse(
            url=f"/organizer/dashboard?email={email}&success=Event+added+successfully",
            status_code=303,
        )
    else:
        return RedirectResponse(
            url=f"/organizer/dashboard?email={email}&error=Failed+to+add+event",
            status_code=303,
        )


@router.get("/events/{event_id}/edit", response_class=HTMLResponse)
async def edit_event_form(
    request: Request,
    event_id: int,
    email: str = Query(..., description="Organizer email address"),
):
    """Form to edit an existing event."""

    if not JoggerRepository.check_if_organizer(email):
        return RedirectResponse(url="/", status_code=303)

    events = EventRepository.get_events_by_organizer(email)
    event = next((e for e in events if e["EventID"] == event_id), None)

    if not event:
        return RedirectResponse(
            url=f"/organizer/dashboard?email={email}&error=Event+not+found+or+not+authorized",
            status_code=303,
        )

    return templates.TemplateResponse(
        "organizer/event_form.html",
        {
            "request": request,
            "email": email,
            "title": "Edit Event",
            "action": "edit",
            "event": event,
        },
    )


@router.post("/events/{event_id}/edit", response_class=HTMLResponse)
async def edit_event(
    request: Request,
    event_id: int,
    email: str = Form(...),
    event_name: str = Form(...),
    event_date: datetime = Form(...),
    max_participants: int = Form(...),
):
    """Handle edit event form submission."""

    if not JoggerRepository.check_if_organizer(email):
        return RedirectResponse(url="/", status_code=303)

    events = EventRepository.get_events_by_organizer(email)
    event = next((e for e in events if e["EventID"] == event_id), None)

    if not event:
        return RedirectResponse(
            url=f"/organizer/dashboard?email={email}&error=Event+not+found+or+not+authorized",
            status_code=303,
        )

    EventRepository.update_event(event_id, event_name, event_date, max_participants)

    return RedirectResponse(
        url=f"/organizer/dashboard?email={email}&success=Event+updated+successfully",
        status_code=303,
    )


@router.get("/events/{event_id}/delete", response_class=HTMLResponse)
async def delete_event(
    request: Request,
    event_id: int,
    email: str = Query(..., description="Organizer email address"),
):
    """Delete an event."""

    if not JoggerRepository.check_if_organizer(email):
        return RedirectResponse(url="/", status_code=303)

    events = EventRepository.get_events_by_organizer(email)
    event = next((e for e in events if e["EventID"] == event_id), None)

    if not event:
        return RedirectResponse(
            url=f"/organizer/dashboard?email={email}&error=Event+not+found+or+not+authorized",
            status_code=303,
        )

    EventRepository.delete_event(event_id)

    return RedirectResponse(
        url=f"/organizer/dashboard?email={email}&success=Event+deleted+successfully",
        status_code=303,
    )


@router.get("/events/{event_id}/registrations", response_class=HTMLResponse)
async def view_registrations(
    request: Request,
    event_id: int,
    email: str = Query(..., description="Organizer email address"),
    success: Optional[str] = None,
    error: Optional[str] = None,
):
    """View and manage registrations for an event."""

    if not JoggerRepository.check_if_organizer(email):
        return RedirectResponse(url="/", status_code=303)

    events = EventRepository.get_events_by_organizer(email)
    event = next((e for e in events if e["EventID"] == event_id), None)

    if not event:
        return RedirectResponse(
            url=f"/organizer/dashboard?email={email}&error=Event+not+found+or+not+authorized",
            status_code=303,
        )

    registrations = RegistrationRepository.get_event_registrations(event_id)

    return templates.TemplateResponse(
        "organizer/registrations.html",
        {
            "request": request,
            "email": email,
            "event": event,
            "registrations": registrations,
            "title": f"Registrations for {event['EventName']}",
            "success": success,
            "error": error,
        },
    )


@router.get("/events/{event_id}/registrations/add", response_class=HTMLResponse)
async def add_registration_form(
    request: Request,
    event_id: int,
    email: str = Query(..., description="Organizer email address"),
):
    """Form to add a registration to an event."""

    if not JoggerRepository.check_if_organizer(email):
        return RedirectResponse(url="/", status_code=303)

    events = EventRepository.get_events_by_organizer(email)
    event = next((e for e in events if e["EventID"] == event_id), None)

    if not event:
        return RedirectResponse(
            url=f"/organizer/dashboard?email={email}&error=Event+not+found+or+not+authorized",
            status_code=303,
        )

    return templates.TemplateResponse(
        "organizer/registration_form.html",
        {
            "request": request,
            "email": email,
            "event": event,
            "title": f"Add Registration for {event['EventName']}",
        },
    )


@router.post("/events/{event_id}/registrations/add", response_class=HTMLResponse)
async def add_registration(
    request: Request,
    event_id: int,
    email: str = Form(...),
    jogger_email: str = Form(...),
):
    """Handle add registration form submission."""

    if not JoggerRepository.check_if_organizer(email):
        return RedirectResponse(url="/", status_code=303)

    events = EventRepository.get_events_by_organizer(email)
    event = next((e for e in events if e["EventID"] == event_id), None)

    if not event:
        return RedirectResponse(
            url=f"/organizer/dashboard?email={email}&error=Event+not+found+or+not+authorized",
            status_code=303,
        )

    jogger = JoggerRepository.get_jogger_by_email(jogger_email)
    if not jogger:
        return RedirectResponse(
            url=f"/organizer/events/{event_id}/registrations/add?email={email}&error=Jogger+not+found",
            status_code=303,
        )

    if RegistrationRepository.check_registration(event_id, jogger_email):
        return RedirectResponse(
            url=f"/organizer/events/{event_id}/registrations?email={email}&error=Jogger+already+registered",
            status_code=303,
        )

    current_participants = RegistrationRepository.count_registrations(event_id)
    if current_participants >= event["MaxParticipants"]:
        return RedirectResponse(
            url=f"/organizer/events/{event_id}/registrations?email={email}&error=Event+is+full",
            status_code=303,
        )

    RegistrationRepository.register_for_event(event_id, jogger_email)

    return RedirectResponse(
        url=f"/organizer/events/{event_id}/registrations?email={email}&success=Registration+added+successfully",
        status_code=303,
    )


@router.get(
    "/events/{event_id}/registrations/{jogger_email}/delete",
    response_class=HTMLResponse,
)
async def delete_registration(
    request: Request,
    event_id: int,
    jogger_email: str,
    email: str = Query(..., description="Organizer email address"),
):
    """Delete a registration from an event."""

    if not JoggerRepository.check_if_organizer(email):
        return RedirectResponse(url="/", status_code=303)

    events = EventRepository.get_events_by_organizer(email)
    event = next((e for e in events if e["EventID"] == event_id), None)

    if not event:
        return RedirectResponse(
            url=f"/organizer/dashboard?email={email}&error=Event+not+found+or+not+authorized",
            status_code=303,
        )

    if not RegistrationRepository.check_registration(event_id, jogger_email):
        return RedirectResponse(
            url=f"/organizer/events/{event_id}/registrations?email={email}&error=Registration+not+found",
            status_code=303,
        )

    RegistrationRepository.unregister_from_event(event_id, jogger_email)

    return RedirectResponse(
        url=f"/organizer/events/{event_id}/registrations?email={email}&success=Registration+removed+successfully",
        status_code=303,
    )
