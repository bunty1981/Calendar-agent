"""Web OAuth flow for the web app: browser-redirect Flow + credential storage.

CREDENTIALS_STORAGE is an in-memory dict keyed by session id, for demo
purposes only — use a real session/database-backed store in production.
"""
import os

from google_auth_oauthlib.flow import Flow

from core.config import SCOPES

# Disable HTTPS check (for local dev only)
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

# Resolved relative to this file so it works regardless of the caller's cwd.
CLIENT_SECRETS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gcp-web-client-credentials.json")
REDIRECT_URI = "http://localhost:8000/oauth2callback"

CREDENTIALS_STORAGE = {}


def get_flow() -> Flow:
    """Create a Flow object for the web OAuth2 authorization-code flow."""
    return Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI,
    )
