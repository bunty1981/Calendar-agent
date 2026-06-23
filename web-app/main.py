import os
import datetime
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

import logging

logging.basicConfig(level=logging.DEBUG, 
filename='app.log', 
filemode='w', 
format='%(name)s - %(levelname)s - %(message)s')

app = FastAPI()
logger = logging.getLogger(__name__)

# Add session middleware for state management
app.add_middleware(SessionMiddleware, secret_key="your-secret-key-change-in-production")

# Disable HTTPS check (for local dev only)
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

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
def login(request: Request):
    flow = get_flow()
    authorization_url, state = flow.authorization_url(
        access_type='offline',
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

    # Create a new Flow without specifying scopes (they're already in the auth code)
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,  # Don't override scopes; they're embedded in the authorization code
        redirect_uri=REDIRECT_URI
    )
    
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
