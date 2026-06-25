import os
import datetime

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

# For html front-end
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi import Form

import json
import logging

logging.basicConfig(level=logging.DEBUG, 
filename='app.log', 
filemode='w', 
format='%(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI()
# Add session middleware for state management
app.add_middleware(SessionMiddleware, secret_key="your-secret-key-change-in-production", https_only=False)  # Set https_only=True in production

# Disable HTTPS check (for local dev only)
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# HTML templates directory
templates = Jinja2Templates(directory="templates")

# Configuration
CLIENT_SECRETS_FILE = "gcp-web-client-credentials.json"
SCOPES = ["https://www.googleapis.com/auth/calendar"]
REDIRECT_URI = "http://localhost:8000/oauth2callback"

# Store credentials in session (for demo purposes only; use a real DB for production)
CREDENTIALS_STORAGE = {}

## Helper function to create a Flow object
def get_flow():
    return Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
    )

# #
# @app.get("/")
# def read_root():
#     return {"message": "Welcome! Please log in first by visiting /login"}

# Route to render the initial empty form HTML
@app.get("/", response_class=HTMLResponse)
async def get_form(request: Request):
    session_id = "default_user"  # In production, use actual session/user ID
    credentials_json = CREDENTIALS_STORAGE.get(session_id)
    
    if not credentials_json:
        return RedirectResponse("/login") # User not authenticated, redirect to login
    return templates.TemplateResponse(request, "index.html", {"request": request})       

## Authentication endpoint to initiate the OAuth2 flow
@app.get("/login")
def login(request: Request):
    flow = get_flow()
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        prompt = 'consent', # force Google to return a refresh token each time the user authorizes the app. This is important for long-lived access.
        include_granted_scopes='false' #'true' - use only the scope being requested now. Was appending previous scopes to the new request, which caused issues with the Google API rejecting the request due to scope mismatch.
    )
    
    # Store the flow's state, code_verifier, and scopes in the session for the callback
    request.session['oauth_state'] = state
    request.session['code_verifier'] = flow.code_verifier
    request.session['scopes'] = SCOPES

    return RedirectResponse(authorization_url)

## OAuth2 Callback endpoint
@app.get("/oauth2callback")
def oauth2callback(request: Request):
    """
    Handles the Google OAuth2 callback. Exchanges the authorization code for 
    tokens and saves the credentials to CREDENTIALS_STORAGE.
    """
    # Verify the code was provided in the query parameters
    code = request.query_params.get("code")
    state = request.query_params.get("state")
    
    if not code:
        raise HTTPException(status_code=400, detail="Authorization code not found")
    
    # Verify state parameter to prevent CSRF attacks
    if state != request.session.get('oauth_state'):
        raise HTTPException(status_code=400, detail="Invalid state parameter")
    
    # Retrieve the stored code_verifier and scopes from the session
    code_verifier = request.session.get('code_verifier')
    stored_scopes = request.session.get('scopes')
    
    if not code_verifier:
        raise HTTPException(status_code=400, detail="Code verifier not found in session")
    
    logger.info(f"stored_scopes: {stored_scopes}")
    logger.info(f"SCOPES: {SCOPES}")
    logger.info(f"code_verifier: {code_verifier}")

    # Create a new Flow using the previous scopes 
    flow = get_flow()  
    
    # Restore the code_verifier that was used in the authorization request
    flow.code_verifier = code_verifier
    
    try:
        # Exchange the authorization code for access and refresh tokens
        flow.fetch_token(code=code)
    except Exception as e:
        logger.error(f"Token fetch error: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Failed to fetch token: {str(e)}")

    credentials = flow.credentials

    # Save credentials to CREDENTIALS_STORAGE dictionary
    # Use a session/user identifier as the key (for demo purposes)
    session_id = "default_user"  # In production, use actual session/user ID
    CREDENTIALS_STORAGE[session_id] = credentials.to_json()
    
    logger.info(f"Credentials stored for session: {session_id}")
        
    return {"message": "Successfully authenticated! You can now use the /create_event endpoint."}

## Display the form for creating a new calendar event
@app.get("/create_event", response_class=HTMLResponse)
async def display_event_form(request: Request):
    """
    Renders the HTML form for creating a new calendar event.
    """
    session_id = "default_user"  # In production, use actual session/user ID
    credentials_json = CREDENTIALS_STORAGE.get(session_id)
    
    if not credentials_json:
        return RedirectResponse("/login") # User not authenticated, redirect to login
    return templates.TemplateResponse(request, "index.html", {"request": request})

@app.post("/create_event")
async def create_event(request: Request): #event_details: dict):
    """
    Creates a new event in the user's Google Calendar.
    Expects event_details to contain 'summary', 'start_time', and 'end_time'.
    """
    session_id = "default_user"  # In production, use actual session/user ID
    credentials_json = CREDENTIALS_STORAGE.get(session_id)
    
    if not credentials_json:
        #raise HTTPException(status_code=401, detail="User not authenticated. Please log in first.")
        return RedirectResponse("/login") #User not authenticated, redirect to login
    else:
        credentials_dict = json.loads(credentials_json)
    
    logger.info(f"Credentials retrieved for session: {credentials_dict}")
    credentials = Credentials.from_authorized_user_info(info=credentials_dict)
    
    # Get event details from the request body
    event_details = await request.form() # Needs python-multipart dependency installed for form parsing
    logger.info(f"Submitted event details: {event_details}")

    try:
        service = build('calendar', 'v3', credentials=credentials)
        
        start_date_str = event_details.get('start_date')
        start_time_str = event_details.get('start_time')
        end_date_str = event_details.get('end_date')
        end_time_str = event_details.get('end_time')

        start_datetime = f"{start_date_str}T{start_time_str}:00" #Convert to ISO 8601 format
        end_datetime = f"{end_date_str}T{end_time_str}:00" #Convert to ISO 8601 format 

        event = {
            'summary': event_details.get('summary'),
            'start': {
                'dateTime': start_datetime,
                'timeZone': 'America/Chicago',  # Adjust to your desired timezone
            },
            'end': {
                'dateTime': end_datetime,
                'timeZone': 'America/Chicago',  # Adjust to your desired timezone
            },
        }

        # ## Hardcoded event for testing purposes
        # event = {
        #     "summary": "Project Sync",
        #     "start": {
        #         "dateTime": "2026-06-25T09:00:00",
        #         "timeZone": "America/New_York"
        #     },
        #     "end": {
        #         "dateTime": "2026-06-25T10:00:00",
        #         "timeZone": "America/New_York"
        #     }
        # }
        
        logger.info(f"Creating event with details: {event}")

        created_event = service.events().insert(calendarId='primary', body=event).execute()
        logger.info(f"Event created: {created_event.get('htmlLink')}")
        
        return {"message": "Event created successfully!", "event_link": created_event.get('htmlLink')}
    
    except Exception as e:
        logger.error(f"Error creating event: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create event: {str(e)}")