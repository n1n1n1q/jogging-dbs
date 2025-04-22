from fastapi import APIRouter, Request, Form, Query, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import os
from typing import Optional
from datetime import datetime

from models.repositories import RouteRepository, JoggerRepository

router = APIRouter()

templates_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "templates"
)
templates = Jinja2Templates(directory=templates_path)


@router.get("/dashboard", response_class=HTMLResponse)
async def admin_dashboard(
    request: Request, email: str = Query(..., description="Admin email address")
):
    """Admin dashboard showing route management options."""
    if not JoggerRepository.check_if_admin(email):
        return RedirectResponse(url="/", status_code=303)

    routes = RouteRepository.get_all_routes()

    return templates.TemplateResponse(
        "admin/dashboard.html",
        {
            "request": request,
            "email": email,
            "routes": routes,
            "title": "Admin Dashboard",
        },
    )


@router.get("/routes/add", response_class=HTMLResponse)
async def add_route_form(
    request: Request, email: str = Query(..., description="Admin email address")
):
    """Form to add a new route."""

    if not JoggerRepository.check_if_admin(email):
        return RedirectResponse(url="/", status_code=303)

    return templates.TemplateResponse(
        "admin/route_form.html",
        {"request": request, "email": email, "title": "Add Route", "action": "add"},
    )


@router.post("/routes/add", response_class=HTMLResponse)
async def add_route(
    request: Request,
    email: str = Form(...),
    route_name: str = Form(...),
    distance: float = Form(...),
    avg_pace: Optional[float] = Form(None),
):
    """Handle add route form submission."""

    if not JoggerRepository.check_if_admin(email):
        return RedirectResponse(url="/", status_code=303)

    route_id = RouteRepository.create_route(route_name, distance, avg_pace)

    return RedirectResponse(
        url=f"/admin/dashboard?email={email}&success=Route+added+successfully",
        status_code=303,
    )


@router.get("/routes/{route_id}/edit", response_class=HTMLResponse)
async def edit_route_form(
    request: Request,
    route_id: int,
    email: str = Query(..., description="Admin email address"),
):
    """Form to edit an existing route."""

    if not JoggerRepository.check_if_admin(email):
        return RedirectResponse(url="/", status_code=303)

    route = RouteRepository.get_route_by_id(route_id)
    if not route:
        return RedirectResponse(
            url=f"/admin/dashboard?email={email}&error=Route+not+found", status_code=303
        )

    return templates.TemplateResponse(
        "admin/route_form.html",
        {
            "request": request,
            "email": email,
            "title": "Edit Route",
            "action": "edit",
            "route": route,
        },
    )


@router.post("/routes/{route_id}/edit", response_class=HTMLResponse)
async def edit_route(
    request: Request,
    route_id: int,
    email: str = Form(...),
    route_name: str = Form(...),
    distance: float = Form(...),
    avg_pace: Optional[float] = Form(None),
):
    """Handle edit route form submission."""

    if not JoggerRepository.check_if_admin(email):
        return RedirectResponse(url="/", status_code=303)

    RouteRepository.update_route(route_id, route_name, distance, avg_pace)

    return RedirectResponse(
        url=f"/admin/dashboard?email={email}&success=Route+updated+successfully",
        status_code=303,
    )


@router.get("/routes/{route_id}/delete", response_class=HTMLResponse)
async def delete_route(
    request: Request,
    route_id: int,
    email: str = Query(..., description="Admin email address"),
):
    """Delete a route."""

    if not JoggerRepository.check_if_admin(email):
        return RedirectResponse(url="/", status_code=303)

    RouteRepository.delete_route(route_id)

    return RedirectResponse(
        url=f"/admin/dashboard?email={email}&success=Route+deleted+successfully",
        status_code=303,
    )


@router.get("/routes/search", response_class=HTMLResponse)
async def search_routes(
    request: Request,
    email: str = Query(..., description="Admin email address"),
    query: str = Query(None, description="Search query"),
):
    """Search for routes."""

    if not JoggerRepository.check_if_admin(email):
        return RedirectResponse(url="/", status_code=303)

    if not query:
        return RedirectResponse(url=f"/admin/dashboard?email={email}", status_code=303)

# TODO: Implement actual search logic
    # For now, we'll just show all routes as a placeholder
    routes = RouteRepository.get_all_routes()

    return templates.TemplateResponse(
        "admin/dashboard.html",
        {
            "request": request,
            "email": email,
            "routes": routes,
            "title": "Search Results",
            "query": query,
        },
    )
