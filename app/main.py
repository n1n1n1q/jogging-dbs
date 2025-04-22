from fastapi import FastAPI, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import uvicorn
import os

# Fix the imports to use relative imports
from models.repositories import JoggerRepository
from routers import admin_router, user_router, organizer_router

# Create FastAPI app instance
app = FastAPI(title="Jogging App")

# Set up templates directory
templates_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
templates = Jinja2Templates(directory=templates_path)

# Include routers
app.include_router(admin_router.router, prefix="/admin", tags=["admin"])
app.include_router(user_router.router, prefix="/user", tags=["user"])
app.include_router(organizer_router.router, prefix="/organizer", tags=["organizer"])

# Mount static files
# app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    """Home page with login options for different user roles."""
    print("A")
    return templates.TemplateResponse(
        "index.html", {"request": request, "title": "Jogging App - Login"}
    )


@app.post("/login", response_class=HTMLResponse)
async def login(request: Request, email: str = Form(...), role: str = Form(...)):
    """Handle login and redirect to appropriate view."""
    # Check if the email exists
    user = JoggerRepository.get_jogger_by_email(email)

    # Special case for admin - if they exist in appadmin table but not in jogger table
    if not user and role == "admin" and JoggerRepository.check_if_admin(email):
        # Auto-create the admin in the jogger table
        JoggerRepository.create_jogger(email, "Admin User")
        user = JoggerRepository.get_jogger_by_email(email)

    # Special case for organizer - if they exist in eventorganizer table but not in jogger table
    if not user and role == "organizer" and JoggerRepository.check_if_organizer(email):
        # Auto-create the organizer in the jogger table
        organizer_name = JoggerRepository.get_organizer_name(email)
        name = organizer_name if organizer_name else "Event Organizer"
        JoggerRepository.create_jogger(email, name)
        user = JoggerRepository.get_jogger_by_email(email)

    # Validate roles
    if role == "admin" and not JoggerRepository.check_if_admin(email):
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "title": "Jogging App - Login",
                "error": "You are not authorized as an admin.",
            },
        )

    if role == "organizer" and not JoggerRepository.check_if_organizer(email):
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "title": "Jogging App - Login",
                "error": "You are not authorized as an event organizer.",
            },
        )

    # If email doesn't exist and role is user, create new user
    if not user and role == "user":
        # For simplicity, we'll automatically create a new user with a default name
        # In a real app, you would have a registration form
        JoggerRepository.create_jogger(email, "New User")
    elif not user:
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "title": "Jogging App - Login",
                "error": f"User with email {email} does not exist",
            },
        )

    # Redirect to the appropriate view
    if role == "admin":
        return RedirectResponse(url=f"/admin/dashboard?email={email}", status_code=303)
    elif role == "organizer":
        return RedirectResponse(
            url=f"/organizer/dashboard?email={email}", status_code=303
        )
    else:  # User role
        return RedirectResponse(url=f"/user/dashboard?email={email}", status_code=303)


# Changed this to run the app directly without the app module prefix
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
