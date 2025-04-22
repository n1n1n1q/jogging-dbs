from fastapi import APIRouter, Request, Form, Query, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import os
from typing import Optional
from datetime import datetime

from models.repositories import (
    JoggerRepository,
    RouteRepository,
    EventRepository,
    RegistrationRepository,
    JoggingSessionRepository,
    ReviewRepository,
    LeaderboardRepository,
)

router = APIRouter()

templates_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "templates"
)
templates = Jinja2Templates(directory=templates_path)


@router.get("/dashboard", response_class=HTMLResponse)
async def user_dashboard(
    request: Request,
    email: str = Query(..., description="User email address"),
    success: Optional[str] = None,
    error: Optional[str] = None,
):
    """User dashboard with options for events, routes, and sessions."""
    user = JoggerRepository.get_jogger_by_email(email)
    if not user:
        return RedirectResponse(url="/", status_code=303)

    return templates.TemplateResponse(
        "user/dashboard.html",
        {
            "request": request,
            "email": email,
            "user": user,
            "title": "User Dashboard",
            "success": success,
            "error": error,
        },
    )


@router.get("/events", response_class=HTMLResponse)
async def list_events(
    request: Request,
    email: str = Query(..., description="User email address"),
    success: Optional[str] = None,
    error: Optional[str] = None,
):
    """List all available events with registration options."""
    user = JoggerRepository.get_jogger_by_email(email)
    if not user:
        return RedirectResponse(url="/", status_code=303)

    events = EventRepository.get_all_events()

    event_data = []
    for event in events:
        is_registered = RegistrationRepository.check_registration(
            event["EventID"], email
        )
        current_participants = RegistrationRepository.count_registrations(
            event["EventID"]
        )
        is_full = current_participants >= event["MaxParticipants"]
        is_past = event["EventDate"] < datetime.now()

        event_data.append(
            {
                **event,
                "is_registered": is_registered,
                "is_full": is_full,
                "is_past": is_past,
                "current_participants": current_participants,
            }
        )

    return templates.TemplateResponse(
        "user/events.html",
        {
            "request": request,
            "email": email,
            "user": user,
            "events": event_data,
            "title": "Events",
            "success": success,
            "error": error,
        },
    )


@router.get("/events/{event_id}/register", response_class=HTMLResponse)
async def register_for_event(
    request: Request,
    event_id: int,
    email: str = Query(..., description="User email address"),
):
    """Register for an event."""
    user = JoggerRepository.get_jogger_by_email(email)
    if not user:
        return RedirectResponse(url="/", status_code=303)

    event = EventRepository.get_event_by_id(event_id)
    if not event:
        return RedirectResponse(
            url=f"/user/events?email={email}&error=Event+not+found", status_code=303
        )

    if RegistrationRepository.check_registration(event_id, email):
        return RedirectResponse(
            url=f"/user/events?email={email}&error=Already+registered+for+this+event",
            status_code=303,
        )

    current_participants = RegistrationRepository.count_registrations(event_id)
    if current_participants >= event["MaxParticipants"]:
        return RedirectResponse(
            url=f"/user/events?email={email}&error=Event+is+full", status_code=303
        )

    if event["EventDate"] < datetime.now():
        return RedirectResponse(
            url=f"/user/events?email={email}&error=Cannot+register+for+past+events",
            status_code=303,
        )

    RegistrationRepository.register_for_event(event_id, email)

    return RedirectResponse(
        url=f"/user/events?email={email}&success=Successfully+registered+for+event",
        status_code=303,
    )


@router.get("/events/{event_id}/unregister", response_class=HTMLResponse)
async def unregister_from_event(
    request: Request,
    event_id: int,
    email: str = Query(..., description="User email address"),
):
    """Unregister from an event."""
    user = JoggerRepository.get_jogger_by_email(email)
    if not user:
        return RedirectResponse(url="/", status_code=303)

    if not RegistrationRepository.check_registration(event_id, email):
        return RedirectResponse(
            url=f"/user/events?email={email}&error=Not+registered+for+this+event",
            status_code=303,
        )

    RegistrationRepository.unregister_from_event(event_id, email)

    return RedirectResponse(
        url=f"/user/events?email={email}&success=Successfully+unregistered+from+event",
        status_code=303,
    )


@router.get("/events/{event_id}/details", response_class=HTMLResponse)
async def event_details(
    request: Request,
    event_id: int,
    email: str = Query(..., description="User email address"),
    success: Optional[str] = None,
    error: Optional[str] = None,
):
    """Show event details including participants, reviews, and leaderboard."""
    user = JoggerRepository.get_jogger_by_email(email)
    if not user:
        return RedirectResponse(url="/", status_code=303)

    event = EventRepository.get_event_by_id(event_id)
    if not event:
        return RedirectResponse(
            url=f"/user/events?email={email}&error=Event+not+found", status_code=303
        )

    registrations = RegistrationRepository.get_event_registrations(event_id)

    is_registered = RegistrationRepository.check_registration(event_id, email)

    reviews = ReviewRepository.get_event_reviews(event_id)

    user_review = ReviewRepository.get_event_review_by_jogger(event_id, email)

    leaderboard = LeaderboardRepository.get_leaderboard_for_event(event_id)

    avg_rating = ReviewRepository.get_event_average_rating(event_id)

    return templates.TemplateResponse(
        "user/event_details.html",
        {
            "request": request,
            "email": email,
            "user": user,
            "event": event,
            "registrations": registrations,
            "is_registered": is_registered,
            "reviews": reviews,
            "user_review": user_review,
            "leaderboard": leaderboard,
            "is_past": event["EventDate"] < datetime.now(),
            "avg_rating": avg_rating,
            "title": f"Event Details: {event['EventName']}",
            "success": success,
            "error": error,
        },
    )


@router.get("/events/{event_id}/review", response_class=HTMLResponse)
async def review_event_form(
    request: Request,
    event_id: int,
    email: str = Query(..., description="User email address"),
):
    """Form to add or edit an event review."""
    user = JoggerRepository.get_jogger_by_email(email)
    if not user:
        return RedirectResponse(url="/", status_code=303)

    event = EventRepository.get_event_by_id(event_id)
    if not event:
        return RedirectResponse(
            url=f"/user/events?email={email}&error=Event+not+found", status_code=303
        )

    if (
        not RegistrationRepository.check_registration(event_id, email)
        or event["EventDate"] >= datetime.now()
    ):
        return RedirectResponse(
            url=f"/user/events/{event_id}/details?email={email}&error=You+cannot+review+an+event+you+have+not+participated+in",
            status_code=303,
        )

    review = ReviewRepository.get_event_review_by_jogger(event_id, email)
    action = "edit" if review else "add"

    return templates.TemplateResponse(
        "user/review_form.html",
        {
            "request": request,
            "email": email,
            "user": user,
            "event": event,
            "review": review,
            "action": action,
            "type": "event",
            "title": f"Review Event: {event['EventName']}",
        },
    )


@router.post("/events/{event_id}/review", response_class=HTMLResponse)
async def submit_event_review(
    request: Request,
    event_id: int,
    email: str = Form(...),
    rating: int = Form(...),
    comment: Optional[str] = Form(None),
    review_id: Optional[int] = Form(None),
):
    """Submit an event review."""
    if rating < 1 or rating > 5:
        return RedirectResponse(
            url=f"/user/events/{event_id}/details?email={email}&error=Rating+must+be+between+1+and+5",
            status_code=303,
        )

    if review_id:
        ReviewRepository.update_event_review(review_id, rating, comment)
    else:
        ReviewRepository.create_event_review(event_id, email, rating, comment)

    return RedirectResponse(
        url=f"/user/events/{event_id}/details?email={email}&success=Review+submitted+successfully",
        status_code=303,
    )


@router.get(
    "/events/{event_id}/reviews/{review_id}/delete", response_class=HTMLResponse
)
async def delete_event_review(
    request: Request,
    event_id: int,
    review_id: int,
    email: str = Query(..., description="User email address"),
):
    """Delete an event review."""
    review = ReviewRepository.get_event_review_by_jogger(event_id, email)

    if not review or review["ReviewID"] != review_id:
        return RedirectResponse(
            url=f"/user/events/{event_id}/details?email={email}&error=Review+not+found+or+not+authorized",
            status_code=303,
        )

    ReviewRepository.delete_event_review(review_id)

    return RedirectResponse(
        url=f"/user/events/{event_id}/details?email={email}&success=Review+deleted+successfully",
        status_code=303,
    )


@router.get("/events/{event_id}/certificate", response_class=HTMLResponse)
async def get_event_certificate(
    request: Request,
    event_id: int,
    email: str = Query(..., description="User email address"),
):
    """Generate a certificate for a completed event."""
    user = JoggerRepository.get_jogger_by_email(email)
    if not user:
        return RedirectResponse(url="/", status_code=303)

    registration = EventRegistrationRepository.get_registration(event_id, email)
    if not registration:
        return RedirectResponse(
            url=f"/user/events/{event_id}?email={email}&error=Not+registered+for+this+event",
            status_code=303,
        )

    event = JoggingEventRepository.get_event_by_id(event_id)
    if not event:
        return RedirectResponse(
            url=f"/user/events?email={email}&error=Event+not+found", status_code=303
        )

    organizer = EventOrganizerRepository.get_organizer_by_id(event["OrganizerID"])
    organizer_name = organizer["Name"] if organizer else "Unknown Organizer"

    event_date = datetime.strptime(event["EventDate"], "%Y-%m-%d").strftime("%B %d, %Y")

    return templates.TemplateResponse(
        "user/event_certificate.html",
        {
            "request": request,
            "email": email,
            "user": user,
            "event": event,
            "event_date": event_date,
            "organizer_name": organizer_name,
            "certificate_date": datetime.now().strftime("%B %d, %Y"),
            "title": f"Event Certificate: {event['Name']}",
        },
    )


@router.get("/events/{event_id}/registration-certificate", response_class=HTMLResponse)
async def get_registration_certificate(
    request: Request,
    event_id: int,
    email: str = Query(..., description="User email address"),
):
    """Generate a registration certificate for an event."""
    user = JoggerRepository.get_jogger_by_email(email)
    if not user:
        return RedirectResponse(url="/", status_code=303)

    registration = RegistrationRepository.get_registration(event_id, email)
    if not registration:
        return RedirectResponse(
            url=f"/user/events/{event_id}/details?email={email}&error=Not+registered+for+this+event",
            status_code=303,
        )

    return templates.TemplateResponse(
        "user/registration_certificate.html",
        {
            "request": request,
            "email": email,
            "user": user,
            "event": registration,
            "registration_time": registration["TimeStamp"],
            "title": f"Registration Certificate: {registration['EventName']}",
        },
    )


@router.get("/routes", response_class=HTMLResponse)
async def list_routes(
    request: Request,
    email: str = Query(..., description="User email address"),
    success: Optional[str] = None,
    error: Optional[str] = None,
):
    """List all available jogging routes."""
    user = JoggerRepository.get_jogger_by_email(email)
    if not user:
        return RedirectResponse(url="/", status_code=303)

    routes = RouteRepository.get_all_routes()

    route_data = []
    for route in routes:
        review = ReviewRepository.get_route_review_by_jogger(route["RouteID"], email)
        route_data.append({**route, "has_review": bool(review)})

    return templates.TemplateResponse(
        "user/routes.html",
        {
            "request": request,
            "email": email,
            "user": user,
            "routes": route_data,
            "title": "Jogging Routes",
            "success": success,
            "error": error,
        },
    )


@router.get("/routes/{route_id}/details", response_class=HTMLResponse)
async def route_details(
    request: Request,
    route_id: int,
    email: str = Query(..., description="User email address"),
    success: Optional[str] = None,
    error: Optional[str] = None,
):
    """Show route details including reviews."""
    user = JoggerRepository.get_jogger_by_email(email)
    if not user:
        return RedirectResponse(url="/", status_code=303)

    route = RouteRepository.get_route_by_id(route_id)
    if not route:
        return RedirectResponse(
            url=f"/user/routes?email={email}&error=Route+not+found", status_code=303
        )

    reviews = ReviewRepository.get_route_reviews(route_id)

    user_review = ReviewRepository.get_route_review_by_jogger(route_id, email)

    avg_rating = ReviewRepository.get_route_average_rating(route_id)

    return templates.TemplateResponse(
        "user/route_details.html",
        {
            "request": request,
            "email": email,
            "user": user,
            "route": route,
            "reviews": reviews,
            "user_review": user_review,
            "avg_rating": avg_rating,
            "title": f"Route Details: {route['RouteName']}",
            "success": success,
            "error": error,
        },
    )


@router.get("/routes/{route_id}/review", response_class=HTMLResponse)
async def review_route_form(
    request: Request,
    route_id: int,
    email: str = Query(..., description="User email address"),
):
    """Form to add or edit a route review."""
    user = JoggerRepository.get_jogger_by_email(email)
    if not user:
        return RedirectResponse(url="/", status_code=303)

    route = RouteRepository.get_route_by_id(route_id)
    if not route:
        return RedirectResponse(
            url=f"/user/routes?email={email}&error=Route+not+found", status_code=303
        )

    review = ReviewRepository.get_route_review_by_jogger(route_id, email)
    action = "edit" if review else "add"

    return templates.TemplateResponse(
        "user/review_form.html",
        {
            "request": request,
            "email": email,
            "user": user,
            "route": route,
            "review": review,
            "action": action,
            "type": "route",
            "title": f"Review Route: {route['RouteName']}",
        },
    )


@router.post("/routes/{route_id}/review", response_class=HTMLResponse)
async def submit_route_review(
    request: Request,
    route_id: int,
    email: str = Form(...),
    rating: int = Form(...),
    comment: Optional[str] = Form(None),
    review_id: Optional[int] = Form(None),
):
    """Submit a route review."""
    if rating < 1 or rating > 5:
        return RedirectResponse(
            url=f"/user/routes/{route_id}/details?email={email}&error=Rating+must+be+between+1+and+5",
            status_code=303,
        )

    if review_id:
        ReviewRepository.update_route_review(review_id, rating, comment)
    else:
        ReviewRepository.create_route_review(route_id, email, rating, comment)

    return RedirectResponse(
        url=f"/user/routes/{route_id}/details?email={email}&success=Review+submitted+successfully",
        status_code=303,
    )


@router.get(
    "/routes/{route_id}/reviews/{review_id}/delete", response_class=HTMLResponse
)
async def delete_route_review(
    request: Request,
    route_id: int,
    review_id: int,
    email: str = Query(..., description="User email address"),
):
    """Delete a route review."""
    review = ReviewRepository.get_route_review_by_jogger(route_id, email)

    if not review or review["ReviewID"] != review_id:
        return RedirectResponse(
            url=f"/user/routes/{route_id}/details?email={email}&error=Review+not+found+or+not+authorized",
            status_code=303,
        )

    ReviewRepository.delete_route_review(review_id)

    return RedirectResponse(
        url=f"/user/routes/{route_id}/details?email={email}&success=Review+deleted+successfully",
        status_code=303,
    )


@router.get("/sessions", response_class=HTMLResponse)
async def list_sessions(
    request: Request,
    email: str = Query(..., description="User email address"),
    success: Optional[str] = None,
    error: Optional[str] = None,
):
    """List all jogging sessions for the user."""
    user = JoggerRepository.get_jogger_by_email(email)
    if not user:
        return RedirectResponse(url="/", status_code=303)

    sessions = JoggingSessionRepository.get_sessions_for_jogger(email)

    return templates.TemplateResponse(
        "user/sessions.html",
        {
            "request": request,
            "email": email,
            "user": user,
            "sessions": sessions,
            "title": "Jogging Sessions",
            "success": success,
            "error": error,
        },
    )


@router.get("/sessions/add", response_class=HTMLResponse)
async def add_session_form(
    request: Request,
    email: str = Query(..., description="User email address"),
    event_id: Optional[int] = None,
):
    """Form to add a new jogging session."""
    user = JoggerRepository.get_jogger_by_email(email)
    if not user:
        return RedirectResponse(url="/", status_code=303)

    routes = RouteRepository.get_all_routes()

    event = None
    if event_id:
        event = EventRepository.get_event_by_id(event_id)

    return templates.TemplateResponse(
        "user/session_form.html",
        {
            "request": request,
            "email": email,
            "user": user,
            "routes": routes,
            "event_id": event_id,
            "event": event,
            "title": "Add Jogging Session",
            "action": "add",
        },
    )


@router.post("/sessions/add", response_class=HTMLResponse)
async def add_session(
    request: Request,
    email: str = Form(...),
    start_dt: datetime = Form(...),
    end_dt: datetime = Form(...),
    distance: Optional[float] = Form(None),
    route_id: Optional[int] = Form(None),
    event_id: Optional[int] = Form(None),
):
    # """Handle add session form submission."""
    # if end_dt <= start_dt:
    #     return RedirectResponse(
    #         url=f"/user/sessions/add?email={email}&error=End+date+must+be+after+start+date",
    #         status_code=303,
    #     )

    session_id = JoggingSessionRepository.create_session(
        start_dt, end_dt, distance, email, route_id
    )

    if not session_id:
        return RedirectResponse(
            url=f"/user/sessions/add?email={email}&error=Failed+to+create+session",
            status_code=303,
        )

    if event_id:
        try:
            JoggingSessionRepository.add_session_to_event(event_id, session_id)
            return RedirectResponse(
                url=f"/user/events/{event_id}/details?email={email}&success=Session+added+successfully",
                status_code=303,
            )
        except Exception as e:
            JoggingSessionRepository.delete_session(session_id)
            return RedirectResponse(
                url=f"/user/sessions/add?email={email}&error=Error+associating+session+with+event:+{str(e)}",
                status_code=303,
            )

    return RedirectResponse(
        url=f"/user/sessions?email={email}&success=Session+added+successfully",
        status_code=303,
    )


@router.get("/sessions/{session_id}/edit", response_class=HTMLResponse)
async def edit_session_form(
    request: Request,
    session_id: int,
    email: str = Query(..., description="User email address"),
):
    """Form to edit an existing jogging session."""
    user = JoggerRepository.get_jogger_by_email(email)
    if not user:
        return RedirectResponse(url="/", status_code=303)

    session = JoggingSessionRepository.get_session_by_id(session_id)
    if not session or session["JoggerEmail"] != email:
        return RedirectResponse(
            url=f"/user/sessions?email={email}&error=Session+not+found+or+not+authorized",
            status_code=303,
        )

    routes = RouteRepository.get_all_routes()

    return templates.TemplateResponse(
        "user/session_form.html",
        {
            "request": request,
            "email": email,
            "user": user,
            "routes": routes,
            "session": session,
            "title": "Edit Jogging Session",
            "action": "edit",
        },
    )


@router.post("/sessions/{session_id}/edit", response_class=HTMLResponse)
async def edit_session(
    request: Request,
    session_id: int,
    email: str = Form(...),
    start_dt: datetime = Form(...),
    end_dt: datetime = Form(...),
    distance: Optional[float] = Form(None),
    route_id: Optional[int] = Form(None),
):
    """Handle edit session form submission."""
    session = JoggingSessionRepository.get_session_by_id(session_id)
    if not session or session["JoggerEmail"] != email:
        return RedirectResponse(
            url=f"/user/sessions?email={email}&error=Session+not+found+or+not+authorized",
            status_code=303,
        )

    if end_dt <= start_dt:
        return RedirectResponse(
            url=f"/user/sessions/{session_id}/edit?email={email}&error=End+date+must+be+after+start+date",
            status_code=303,
        )

    JoggingSessionRepository.update_session(
        session_id, start_dt, end_dt, distance, route_id
    )

    return RedirectResponse(
        url=f"/user/sessions?email={email}&success=Session+updated+successfully",
        status_code=303,
    )


@router.get("/sessions/{session_id}/delete", response_class=HTMLResponse)
async def delete_session(
    request: Request,
    session_id: int,
    email: str = Query(..., description="User email address"),
):
    """Delete a jogging session."""
    session = JoggingSessionRepository.get_session_by_id(session_id)
    if not session or session["JoggerEmail"] != email:
        return RedirectResponse(
            url=f"/user/sessions?email={email}&error=Session+not+found+or+not+authorized",
            status_code=303,
        )

    JoggingSessionRepository.delete_session(session_id)

    return RedirectResponse(
        url=f"/user/sessions?email={email}&success=Session+deleted+successfully",
        status_code=303,
    )


@router.get("/sessions/{session_id}/report", response_class=HTMLResponse)
async def get_session_report(
    request: Request,
    session_id: int,
    email: str = Query(..., description="User email address"),
):
    """Generate a detailed report for a jogging session."""
    user = JoggerRepository.get_jogger_by_email(email)
    if not user:
        return RedirectResponse(url="/", status_code=303)
    session = JoggingSessionRepository.get_session_by_id(session_id)
    if not session or session["JoggerEmail"] != email:
        return RedirectResponse(
            url=f"/user/sessions?email={email}&error=Session+not+found+or+not+authorized",
            status_code=303,
        )
    route = None
    route_name = "No specific route"
    route_avg_pace = 0
    pace_diff = 0
    pace_diff_abs = 0
    if session["RouteID"]:
        route = RouteRepository.get_route_by_id(session["RouteID"])
        if route:
            route_name = route["RouteName"]
            if route.get("AvgPace"):
                route_avg_pace = route["AvgPace"]
    duration_seconds = (session["EndDT"] - session["StartDT"]).total_seconds()
    hours = duration_seconds / 3600
    minutes = duration_seconds / 60
    duration_formatted = (
        f"{int(hours)}h {int(minutes % 60)}m {int(duration_seconds % 60)}s"
    )
    if hours < 1:
        duration_formatted = f"{int(minutes)}m {int(duration_seconds % 60)}s"
    distance_meters = session["Distance"] * 1000 if session["Distance"] > 0 else 0
    pace_s_per_m = duration_seconds / distance_meters if distance_meters > 0 else 0
    pace_formatted = f"{pace_s_per_m:.4f}"
    speed = session["Distance"] / hours if hours > 0 else 0
    route_avg_pace_s_per_m = 0
    if route_avg_pace > 0:
        route_avg_pace_s_per_m = route_avg_pace * 60 / 1000
        pace_diff = pace_s_per_m - route_avg_pace_s_per_m
        pace_diff_abs = abs(pace_diff)
    avg_calories_per_km = 70
    calories_burnt = int(session["Distance"] * avg_calories_per_km)
    performance_rating = 2
    if route_avg_pace_s_per_m > 0 and pace_s_per_m > route_avg_pace_s_per_m * 1.15:
        performance_rating = 1
    if pace_s_per_m > 0.008:
        performance_rating = 1
    session_data = {
        **session,
        "RouteName": route_name,
        "Duration": duration_formatted,
        "DurationSeconds": duration_seconds,
    }
    return templates.TemplateResponse(
        "user/session_report.html",
        {
            "request": request,
            "email": email,
            "user": user,
            "session": session_data,
            "duration_formatted": duration_formatted,
            "pace": pace_formatted,
            "speed": round(speed, 2),
            "route_avg_pace": (
                f"{route_avg_pace_s_per_m:.4f}" if route_avg_pace_s_per_m > 0 else "0"
            ),
            "pace_diff": pace_diff,
            "pace_diff_abs": round(pace_diff_abs, 4),
            "calories_burnt": calories_burnt,
            "performance_rating": performance_rating,
            "title": f"Session Report: {session['StartDT'].strftime('%B %d, %Y')}",
        },
    )


@router.get("/session/{session_id}/report", response_class=HTMLResponse)
async def session_report_singular(
    session_id: int, email: str = Query(..., description="User email address")
):
    """Redirect from singular session path to plural sessions path."""
    return RedirectResponse(
        url=f"/user/sessions/{session_id}/report?email={email}", status_code=303
    )
