"""Thin wrapper around the Google Calendar API's events().insert() call.

Auth-agnostic: callers (cli/auth.py's desktop OAuth flow, webapp/auth.py's
web OAuth flow) obtain `credentials` however is appropriate for their own
flow and pass them in here.
"""
import logging

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)


def get_service(credentials):
    """Build a Google Calendar API v3 service client from OAuth credentials."""
    return build("calendar", "v3", credentials=credentials)


def insert_event(service, event_body: dict) -> dict:
    """Insert `event_body` onto the user's primary calendar.

    Returns the created event resource from the API on success. Raises
    HttpError (or any other exception from the underlying client) on
    failure; callers decide how to surface that to their own users.
    """
    event = service.events().insert(calendarId="primary", body=event_body).execute()
    logger.info(f"Event created: {event.get('summary')}")
    return event
