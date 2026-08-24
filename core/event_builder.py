"""Builds Google Calendar API event bodies from simple event fields.

Extracted from the original CLI's `create_google_calendar_event_func` (which
duplicated this logic) and the web app's `/create_event` route (which had a
second, less capable copy with no All-day support). Both now share this.
"""
from datetime import datetime, timedelta


def build_event_body(
    summary: str,
    start_date: str,
    end_date: str = None,
    description: str = None,
    location: str = None,
    timezone: str = "America/Los_Angeles",
    event_type: str = "Timed",  # 'All-day' or 'Timed'
) -> dict:
    """Build a Google Calendar API event resource dict.

    Args:
        summary: The title of the event.
        start_date: ISO-format start (e.g. '2025-11-03T10:00:00' for a Timed
            event, or a date-only ISO string for an All-day event).
        end_date: ISO-format end. Optional for All-day events, where it
            defaults to the day after start_date (the Calendar API's 'end'
            date is exclusive for all-day events).
        description: Optional event description.
        location: Optional event location.
        timezone: IANA timezone name, used only for Timed events.
        event_type: 'Timed' for events with specific start and end times,
            'All-day' for events that last the entire day.

    Returns:
        A dict ready to pass as the `body` of `events().insert(...)`.
    """
    if event_type == "Timed":
        return {
            "summary": summary,
            "description": description,
            "location": location,
            "start": {"dateTime": start_date, "timeZone": timezone},
            "end": {"dateTime": end_date, "timeZone": timezone},
        }

    if event_type == "All-day":
        start = datetime.fromisoformat(start_date).date()
        if end_date:
            end = datetime.fromisoformat(end_date).date()
        else:
            end = start + timedelta(days=1)  # 'end' date is exclusive for all-day events

        return {
            "summary": summary,
            "description": description,
            "location": location,
            "start": {"date": start.strftime("%Y-%m-%d")},
            "end": {"date": end.strftime("%Y-%m-%d")},
        }

    raise ValueError(f"Unknown event_type: {event_type!r} (expected 'Timed' or 'All-day')")
