"""LangChain agent that turns free-form text into Google Calendar events.

The agent is built via `build_calendar_agent(get_service)`, where `get_service`
is a zero-argument callable that returns an authenticated Calendar API service
(or None on failure). This keeps the agent decoupled from any one OAuth flow:
the CLI passes its desktop-flow `cli.auth.get_calendar_service`; the web app
could pass a session-backed equivalent if it adopts the agent later instead
of its fixed-field form.
"""
import json
import logging
from typing import Callable, Optional

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langchain_core.tools import tool
from langchain.agents import create_agent

from core.calendar_client import insert_event
from core.config import ANTHROPIC_API_KEY, DEFAULT_TIMEZONE
from core.event_builder import build_event_body

logger = logging.getLogger(__name__)

SYSTEM_MESSAGE = (
    """
  You are a helpful personal assistant who can create events on google calendar.
  You accept natural language inputs and convert them into calendar events.
  When you receive a request, you must use the create_google_calendar_event tool to create the event on google calendar.
  The create_google_calendar_event tool accepts the following parameters:
- summary: The title or summary of the event.
- start_time: The start time in ISO format (e.g., '2025-11-03T10:00:00').
- end_time: The end time in ISO format (e.g., '2025-11-03T11:00:00').
- description: Optional description for the event.
- location: Optional location for the event.
- timezone: Defaults to 'America/Los_Angeles'. The timezone for the event.
- event_type: Defaults to 'Timed'. 'Timed'for events with specific start and end times, 'All-day' for events that last the entire day (no specific time).
  You convert the natural language input into the parameters required for the create_google_calendar_event tool
  and then call the tool with those parameters to create the event on google calendar.
  You MUST call the tool for every request and cannot create events without using the tool.
  You try to extract the relevant information from the user's input to fill in the parameters for the create_google_calendar_event tool.
  Each user input will be prepended with a timestamp to provide you with context of when the request was made,
  which you can use to determine the year and current date if not specified by the user.
  If the user does not specify a timezone, you can assume 'America/Los_Angeles' but you should confirm this assumption with the user before creating the event.
  If the user does not specify an event type (Timed or All-day), you can assume 'Timed' but you should confirm this assumption with the user before creating the event.
  If the user does not specify an end time for a Timed event, you can assume a default duration of 1 hour but you should confirm this assumption with the user before creating the event.
  If the user describes an event without specific times but mentions a date (e.g. "Meeting on 25th May"), you can assume it's an All-day event but you should confirm this assumption with the user before creating the event.
  For example, if the user says "Create an event titled 'Gym' for 25th May at 6 PM", you would
  use the prepended timestamp to determine the year (assuming the next occurrence of 25th May),
  use the current systemtime to determine the timezone,
  extract the summary as "Gym",
  the start_time as "2026-05-25T18:00:00",
  and the end_time as "2026-05-25T19:00:00" (assuming a default duration of 1 hour if not specified).
  If and when you extract the information and you find that some information is missing (e.g. the user did not specify the end time),
  you can make reasonable assumptions (e.g. default duration of 1 hour),
  but you must confirm these assumptions with the user before creating the event on google calendar.
  As another example, if the user says "Create an event with description 'Discuss project updates' on 25th May from 3 PM to 4 PM", you would
  extract the summary as "Discuss project updates",
  the start_time as "2026-05-25T15:00:00",
  and the end_time as "2026-05-25T16:00:00".
  If the user says "Create an Birthday party at location Cougar Zoo on 25th May, you would
  extract the summary as "Birthday party",
  the location as "Cougar Zoo",
  the start_time as "2026-05-25T00:00:00",
  and the end_time as "2026-05-26T00:00:00" (assuming it's an All-day event since no specific times were mentioned).
  If you are not sure of the extracted information, you can ask the user for clarification before calling the create_google_calendar_event tool.
  DO NOT create the event on google calendar until you are sure of the extracted information
  AND have CONFIRMATION from the user that the extracted information is correct.
  Once the event is created, always respond with the output from the create_google_calendar_event tool, which includes the event link.
  """
)


def build_calendar_agent(get_service: Callable[[], Optional[object]]):
    """Construct a LangChain agent wired to `get_service` for calendar access."""

    def create_google_calendar_event_func(
        summary: str,
        start_date: str,
        end_date: str,
        description: str = None,
        location: str = None,
        timezone: str = DEFAULT_TIMEZONE,
        event_type: str = "Timed",  # 'All-day' or 'Timed'
    ) -> str:
        """Creates an event on the user's primary Google Calendar.

        Returns:
            A JSON string with the event link or an error message.
        """
        service = get_service()
        if not service:
            return json.dumps({"error": "Failed to get Google Calendar service. Check authentication."})

        event_body = build_event_body(
            summary, start_date, end_date, description, location, timezone, event_type
        )
        print(
            f"Creating event with summary: {summary}, start: {start_date}, "
            f"end: {end_date}, timezone: {timezone}"
        )

        try:
            google_event = insert_event(service, event_body)
            return json.dumps({
                "status": "success",
                "summary": google_event.get("summary"),
                "htmlLink": google_event.get("htmlLink"),
            })
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")
            return json.dumps({"error": f"An unexpected error occurred: {e}"})

    @tool
    def create_google_calendar_event(
        summary: str,
        start_date: str,
        end_date: str,
        description: str = None,
        location: str = None,
        timezone: str = DEFAULT_TIMEZONE,
        event_type: str = "Timed",  # 'All-day' or 'Timed'
    ) -> str:
        """Creates an event on the user's primary Google Calendar.

        Args:
            summary: The title or summary of the event.
            start_time: The start time in ISO format (e.g., '2025-11-03T10:00:00').
            end_time: The end time in ISO format (e.g., '2025-11-03T11:00:00').
            description: Optional description for the event.
            location: Optional location for the event.
            timezone: The timezone for the event, defaults to 'America/Los_Angeles'.

        Returns:
            A JSON string with the event link or an error message.
        """
        return create_google_calendar_event_func(
            summary, start_date, end_date, description, location, timezone, event_type
        )

    llm = ChatAnthropic(model="claude-haiku-4-5-20251001", temperature=0, api_key=ANTHROPIC_API_KEY)
    return create_agent(llm, [create_google_calendar_event], system_prompt=SYSTEM_MESSAGE)


def run_agent(agent, user_input: str, history: list[BaseMessage]) -> AIMessage:
    """Single-run agent runner with automatic tool execution via LangChain."""
    try:
        result = agent.invoke(
            {"messages": history + [HumanMessage(content=user_input)]},
            config={"recursion_limit": 50},
        )
        # Return the last AI message
        return result["messages"][-1]
    except Exception as e:
        return AIMessage(content=f"Error:{str(e)}\n\nPlease try rephrasing your request or provide more specific details.")
