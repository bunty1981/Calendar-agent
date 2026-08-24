"""Desktop OAuth flow for the CLI: local-server InstalledAppFlow + on-disk
token caching (cli/token.json).
"""
import logging
import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

from core.calendar_client import get_service
from core.config import SCOPES

logger = logging.getLogger(__name__)

# Paths are resolved relative to this file, so `get_calendar_service()` works
# regardless of the caller's current working directory.
_CLI_DIR = os.path.dirname(os.path.abspath(__file__))
TOKEN_PATH = os.path.join(_CLI_DIR, "token.json")
CREDENTIALS_PATH = os.path.join(_CLI_DIR, "gcp-desktop-client-credentials.json")


def get_calendar_service():
    """Shows basic usage of the Google Calendar API.

    Returns an authenticated Calendar API service, or None on failure. The
    file token.json stores the user's access and refresh tokens, and is
    created automatically when the authorization flow completes for the
    first time.
    """
    creds = None
    if os.path.exists(TOKEN_PATH):
        try:
            creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
        except Exception as e:
            logger.warning(f"Could not load credentials from {TOKEN_PATH}: {e}")

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                logger.error(f"Error refreshing token: {e}")
                creds = None  # Force re-authentication via the interactive flow below

        # Refresh may have been skipped (no prior creds) or may have just
        # failed above (invalid/expired refresh token) — either way, fall
        # through to an interactive login rather than proceeding with
        # creds=None.
        if not creds or not creds.valid:
            if not os.path.exists(CREDENTIALS_PATH):
                logger.error(f"Missing credentials file: {CREDENTIALS_PATH}")
                logger.error("Please download it from the Google Cloud Console and save it in this directory.")
                return None
            try:
                flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
                creds = flow.run_local_server(port=0)
            except Exception as e:
                logger.error(f"Error during authentication flow: {e}")
                return None

        # Save the credentials for the next run
        try:
            with open(TOKEN_PATH, "w") as token:
                token.write(creds.to_json())
            logger.info(f"Credentials saved to {TOKEN_PATH}")
        except Exception as e:
            logger.error(f"Error saving token to {TOKEN_PATH}: {e}")

    try:
        return get_service(creds)
    except Exception as e:
        logger.error(f"Error building Google Calendar service: {e}")
        return None
