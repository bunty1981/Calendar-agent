"""FastAPI web app: an HTML-form front-end for creating Google Calendar events.

Run with (from the repo root):
    python -m uvicorn webapp.app:app --reload
"""
import json
import os.path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from google.oauth2.credentials import Credentials
from starlette.middleware.sessions import SessionMiddleware

from core.calendar_client import get_service, insert_event
from core.event_builder import build_event_body
from core.logging_config import setup_logging
from webapp.auth import CREDENTIALS_STORAGE, get_flow

_WEBAPP_DIR = os.path.dirname(os.path.abspath(__file__))
logger = setup_logging(__name__, log_file=os.path.join(_WEBAPP_DIR, "app.log"))

app = FastAPI()
# Add session middleware for state management
app.add_middleware(SessionMiddleware, secret_key="your-secret-key-change-in-production", https_only=False)  # Set https_only=True in production

# HTML templates directory (resolved relative to this file)
templates = Jinja2Templates(directory=os.path.join(_WEBAPP_DIR, "templates"))

# In production, use an actual session/user ID instead of one shared constant.
SESSION_ID = "default_user"


# Route to render the initial empty form HTML
@app.get("/", response_class=HTMLResponse)
async def get_form(request: Request):
    if not CREDENTIALS_STORAGE.get(SESSION_ID):
        return RedirectResponse("/login")  # User not authenticated, redirect to login
    return templates.TemplateResponse(request, "index.html", {"request": request})


## Authentication endpoint to initiate the OAuth2 flow
@app.get("/login")
def login(request: Request):
    flow = get_flow()
    authorization_url, state = flow.authorization_url(
        access_type="offline",
        prompt="consent",  # force Google to return a refresh token each time the user authorizes the app. This is important for long-lived access.
        include_granted_scopes="false",  # 'true' - use only the scope being requested now. Was appending previous scopes to the new request, which caused issues with the Google API rejecting the request due to scope mismatch.
    )

    # Store the flow's state and code_verifier in the session for the callback
    request.session["oauth_state"] = state
    request.session["code_verifier"] = flow.code_verifier

    return RedirectResponse(authorization_url)


## OAuth2 Callback endpoint
@app.get("/oauth2callback")
def oauth2callback(request: Request):
    """Handles the Google OAuth2 callback. Exchanges the authorization code
    for tokens and saves the credentials to CREDENTIALS_STORAGE.
    """
    code = request.query_params.get("code")
    state = request.query_params.get("state")

    if not code:
        raise HTTPException(status_code=400, detail="Authorization code not found")

    # Verify state parameter to prevent CSRF attacks
    if state != request.session.get("oauth_state"):
        raise HTTPException(status_code=400, detail="Invalid state parameter")

    code_verifier = request.session.get("code_verifier")
    if not code_verifier:
        raise HTTPException(status_code=400, detail="Code verifier not found in session")

    # Create a new Flow and restore the code_verifier used in the authorization request
    flow = get_flow()
    flow.code_verifier = code_verifier

    try:
        flow.fetch_token(code=code)
    except Exception as e:
        logger.error(f"Token fetch error: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Failed to fetch token: {str(e)}")

    CREDENTIALS_STORAGE[SESSION_ID] = flow.credentials.to_json()
    logger.info(f"Credentials stored for session: {SESSION_ID}")

    return {"message": "Successfully authenticated! You can now use the /create_event endpoint."}


## Display the form for creating a new calendar event
@app.get("/create_event", response_class=HTMLResponse)
async def display_event_form(request: Request):
    if not CREDENTIALS_STORAGE.get(SESSION_ID):
        return RedirectResponse("/login")  # User not authenticated, redirect to login
    return templates.TemplateResponse(request, "index.html", {"request": request})


@app.post("/create_event")
async def create_event(request: Request):
    """Creates a new event in the user's Google Calendar from submitted form fields."""
    credentials_json = CREDENTIALS_STORAGE.get(SESSION_ID)
    if not credentials_json:
        return RedirectResponse("/login")  # User not authenticated, redirect to login

    credentials = Credentials.from_authorized_user_info(info=json.loads(credentials_json))

    form = await request.form()  # Needs python-multipart dependency installed for form parsing
    logger.info(f"Submitted event details: {form}")

    event_body = build_event_body(
        summary=form.get("summary"),
        start_date=f"{form.get('start_date')}T{form.get('start_time')}:00",  # Convert to ISO 8601 format
        end_date=f"{form.get('end_date')}T{form.get('end_time')}:00",  # Convert to ISO 8601 format
        description=form.get("description"),  # Form collects this but it was previously dropped here
        timezone="America/Chicago",  # Adjust to your desired timezone
        event_type="Timed",
    )
    logger.info(f"Creating event with details: {event_body}")

    try:
        service = get_service(credentials)
        created_event = insert_event(service, event_body)
        logger.info(f"Event created: {created_event.get('htmlLink')}")
        return {"message": "Event created successfully!", "event_link": created_event.get("htmlLink")}
    except Exception as e:
        logger.error(f"Error creating event: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create event: {str(e)}")
