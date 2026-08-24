"""Tests for core.event_builder — the logic extracted out of the old
main.py / web-app/main.py duplication.
"""
import pytest

from core.event_builder import build_event_body


def test_timed_event_uses_datetime_and_timezone():
    body = build_event_body(
        summary="Gym",
        start_date="2026-05-25T18:00:00",
        end_date="2026-05-25T19:00:00",
        description="Leg day",
        location="Office Gym",
        timezone="America/Los_Angeles",
        event_type="Timed",
    )
    assert body == {
        "summary": "Gym",
        "description": "Leg day",
        "location": "Office Gym",
        "start": {"dateTime": "2026-05-25T18:00:00", "timeZone": "America/Los_Angeles"},
        "end": {"dateTime": "2026-05-25T19:00:00", "timeZone": "America/Los_Angeles"},
    }


def test_all_day_event_uses_date_only():
    body = build_event_body(
        summary="Birthday party",
        start_date="2026-05-25T00:00:00",
        end_date="2026-05-26T00:00:00",
        location="Cougar Zoo",
        event_type="All-day",
    )
    assert body["start"] == {"date": "2026-05-25"}
    assert body["end"] == {"date": "2026-05-26"}


def test_all_day_event_without_end_defaults_to_next_day():
    # The Calendar API's 'end' date is exclusive for all-day events, so a
    # single-day event with no end_date should span exactly one day.
    body = build_event_body(
        summary="Meeting on 25th May",
        start_date="2026-05-25T00:00:00",
        event_type="All-day",
    )
    assert body["start"] == {"date": "2026-05-25"}
    assert body["end"] == {"date": "2026-05-26"}


def test_unknown_event_type_raises():
    with pytest.raises(ValueError):
        build_event_body(summary="x", start_date="2026-05-25T00:00:00", event_type="Weekly")
