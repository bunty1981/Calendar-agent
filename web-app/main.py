import os
import datetime
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import RedirectResponse
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

app = FastAPI()

# Configuration
CLIENT_SECRETS_FILE = "gcp-web-client-credentials.json"
SCOPES = ["https://www.googleapis.com/auth/calendar"]
REDIRECT_URI = "http://localhost:8000/oauth2callback"

# Store credentials in session (for demo purposes only; use a real DB for production)
CREDENTIALS_STORAGE = {}

def get_flow():
    return Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
    )

@app.get("/")
def read_root():
    return {"message": "Welcome! Please log in first by visiting /login"}

@app.get("/login")
def login():
    flow = get_flow()
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true'
    )

    return RedirectResponse(authorization_url)

@app.get("/oauth2callback")
def oauth2callback(request: Request):
    flow = get_flow()
    print(f"Request URL: {request.url}")

    # Retrieve query parameters from Google
    code = request.query_params.get("code")
    state = request.query_params.get("state")
    error = request.query_params.get("error")

    if error:
        raise HTTPException(status_code=400, detail=f"OAuth error: {error}")
   
    #flow.fetch_authorization_response(str(request.url))
    flow.fetch_token(code=code)
    
    credentials = flow.credentials
    # Save credentials (using a simple dictionary here)
    CREDENTIALS_STORAGE['user'] = credentials
    
    return {"message": "Successfully authenticated! You can now use the /create_event endpoint."}

@app.post("/create_event")
def create_event(request_data: dict):
    if 'user' not in CREDENTIALS_STORAGE:
        raise HTTPException(status_code=401, detail="Not authenticated. Please visit /login first.")
    
    creds = Credentials(
        token=CREDENTIALS_STORAGE['user'].token,
        refresh_token=CREDENTIALS_STORAGE['user'].refresh_token,
        token_uri=CREDENTIALS_STORAGE['user'].token_uri,
        client_id=CREDENTIALS_STORAGE['user'].client_id,
        client_secret=CREDENTIALS_STORAGE['user'].client_secret,
        scopes=SCOPES
    )
    
    service = build('calendar', 'v3', credentials=creds)
    user_string = request_data.get("text")

    # Note: For strict natural language processing, you might want to use 
    # a library like 'openai' or 'dateutil' to parse user_string first.
    # Below is a hardcoded example demonstrating how to insert using the Google Calendar API.

    event_body = {
        'summary': user_string,  # In a real app, parse this into a title
        'description': 'Event created via FastAPI NLP parser.',
        'start': {
            'dateTime': datetime.datetime.utcnow().isoformat(),
            'timeZone': 'America/Chicago',
        },
        'end': {
            'dateTime': (datetime.datetime.utcnow() + datetime.timedelta(hours=1)).isoformat(),
            'timeZone': 'America/Chicago',
        },
    }

    try:
        event = service.events().insert(calendarId='primary', body=event_body).execute()
        return {"status": "success", "event_link": event.get('htmlLink')}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating event: {str(e)}")
