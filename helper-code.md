# Code to create google calendar compatible event
from datetime import datetime, timedelta

def create_event_body(summary, start, end=None, is_all_day=False):
    event = {'summary': summary}
    
    if is_all_day:
        # All-day: Use 'date' key (YYYY-MM-DD)
        event['start'] = {'date': start.strftime('%Y-%m-%d')}
        # End date is exclusive; if not provided, default to next day
        if not end: end = start + timedelta(days=1)
        event['end'] = {'date': end.strftime('%Y-%m-%d')}
    else:
        # Timed: Use 'dateTime' key (RFC3339)
        event['start'] = {'dateTime': start.isoformat(), 'timeZone': 'UTC'}
        if not end: end = start + timedelta(hours=1)
        event['end'] = {'dateTime': end.isoformat(), 'timeZone': 'UTC'}
        
    return event

# Usage:
timed = create_event_body("Meeting", datetime(2024, 5, 10, 14, 30))
all_day = create_event_body("Conference", datetime(2024, 6, 1), is_all_day=True)


# LLM model using multiple response formats
# https://forum.langchain.com/t/multiple-response-formats-when-creating-agents/3433/4
