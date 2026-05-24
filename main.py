from datetime import datetime, timedelta
import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# from langchain_openai import ChatOpenAI
# from langchain_anthropic import ChatAnthropic
# from langchain_core.prompts import ChatPromptTemplate
# from langchain_core.output_parsers import PydanticOutputParser

from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langchain.agents import create_agent 
from langchain_core.tools import tool


import logging # log file generation
import json

import openai

# If modifying these scopes, delete the file token.json.
# SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"] # Read only scope
SCOPES = ["https://www.googleapis.com/auth/calendar"] # Read-write scope
TOKEN_PATH  = "token.json"
CREDENTIALS_PATH = "gcp-desktop-client-credentials.json"


# Set up logging
# logging.basicConfig(level=logging.INFO,
# logging.basicConfig(level=logging.ERROR,
logging.basicConfig(level=logging.DEBUG, 
filename='app.log', 
filemode='w', 
format='%(name)s - %(levelname)s - %(message)s')

logger = logging.getLogger(__name__)

  # 1a_Access the google calendar
  # 1b_Create tool to generate google calendar compatible events & insert them in the google calendar
  # 2_Create AI agent to read text and use tools to -
  #   2a_create google calendar compatible event(s)
  #   2b_Insert event in the google calendar
  # 4_Read back next 10 active events


  # 1a_Access the google calendar
# --------------------------------------------------
def get_calendar_service():
  """Shows basic usage of the Google Calendar API.
  Prints the start and name of the next 10 events on the user's calendar.
  """
  creds = None
  # The file token.json stores the user's access and refresh tokens, and is
  # created automatically when the authorization flow completes for the first
  # time.
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
        creds = None # Force re-authentication

    else:
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
    service = build("calendar", "v3", credentials=creds)
    return service
  except Exception as e:
      logger.error(f"Error building Google Calendar service: {e}")
      return None



# 1b_Create and insert all-day google calendar event
# --------------------------------------------------
def create_google_calendar_event_func(
    summary: str,
    start_date: str,
    end_date: str,
    description: str = None,
    location: str = None,
    timezone: str = 'America/Los_Angeles', # 'UTC',
    event_type: str = 'Timed' # 'All-day' or 'Timed'
) -> str:
  """
  Creates an event on the user's primary Google Calendar.

  Args:
      summary: The title or summary of the event.
      start_time: The start time in ISO format (e.g., '2025-11-03T10:00:00').
      end_time: The end time in ISO format (e.g., '2025-11-03T11:00:00').
      description: Optional description for the event.
      location: Optional location for the event.
      timezone: Defaults to 'America/Los_Angeles'. The timezone for the event.
      event_type: Defaults to 'Timed'. 'Timed'for events with specific start and end times, 'All-day' for events that last the entire day (no specific time).
  Returns:
      A JSON string with the event link or an error message.
  """

  # Access the google calendar
  service = get_calendar_service()
  if not service:
      return json.dumps({"error": "Failed to get Google Calendar service. Check authentication."})

  
  # create the event
  if event_type == 'Timed':
    event = {
      'summary' : summary,
      'description': description,
      'location': location,
      'start' : {'dateTime': start_date, 'timeZone': timezone},
      'end' : {'dateTime': end_date, 'timeZone': timezone}
    }
  elif event_type == 'All-day':
    start_date = datetime.fromisoformat(start_date).date() # Convert to date object
    #start_date = start_date.date() # Convert to date object
    if end_date:
      end_date = datetime.fromisoformat(end_date).date() # Convert to date object
      #end_date = end_date.date() 
    else:
      end_date = start_date + timedelta(days=1) # Note: For all-day events, the 'end' date is exclusive (the day AFTER the event ends)

    event = {
      'summary' : summary,
      'description': description,
      'location': location,
      'start' : {'date': start_date.strftime('%Y-%m-%d')},
      'end' : {'date': end_date.strftime('%Y-%m-%d')}
    }
    
  

  print(f"Creating event with summary: {summary}, start: {start_date}, end: {end_date}, timezone: {timezone}")

  # insert the event
  try:
    google_event = service.events().insert(calendarId='primary', body=event).execute()
    logger.info(f"Event created: {google_event.get('summary')}")
    return json.dumps({
        "status": "success",
        "summary": google_event.get("summary"),
        "htmlLink": google_event.get('htmlLink')
    })
  except HttpError as error:
      logger.error(f'An error occurred: {error}')
      return json.dumps({"error": str(error)})
  except Exception as e:
      logger.error(f'An unexpected error occurred: {e}')
      return json.dumps({"error": f"An unexpected error occurred: {e}"})



# Create agent to read text and use tools to create google calendar compatible event(s) and insert them in the google calendar
# --------------------------------------------------
@tool
def create_google_calendar_event(
    summary: str,
    start_date: str,
    end_date: str,
    description: str = None,
    location: str = None,
    timezone: str = 'America/Los_Angeles', # 'UTC',
    event_type: str = 'Timed' # 'All-day' or 'Timed'
) -> str:
  """
  Creates an event on the user's primary Google Calendar.

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
  return create_google_calendar_event_func(summary, start_date, end_date, description, location, timezone, event_type) 

# # Running on github / codespaces
# #------------------------------------------------
# import os;
# openai_api_key = os.environ.get("OPENAI_API_KEY") # Assumes OPENAI_API_KEY setup in github secrets
# anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY") # Assumes OPENAI_API_KEY setup in github secrets
# #------------------------------------------------

# Running on local machines
#--------------------------------------------------
import os;
from dotenv import load_dotenv # Load in environment variable, including secrete keys for .env
# *** If using this method ensure .env is listed in .gitignore do it STAYS local
load_dotenv() # Load environment variables from .env file
openai_api_key = os.getenv("HOME_MAC_OPENAI_API_KEY")
anthropic_api_key = os.getenv("HOME_MAC_ANTHROPIC_API_KEY")
#--------------------------------------------------


#llm = ChatOpenAI(model="gpt-4", temperature=0, api_key=openai_api_key) 
llm = ChatAnthropic(model="claude-haiku-4-5-20251001", temperature=0, api_key=anthropic_api_key)

TOOLS = [create_google_calendar_event]
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

agent = create_agent(llm, TOOLS, system_prompt=SYSTEM_MESSAGE)

def run_agent(user_input: str, history: list[BaseMessage]) -> AIMessage:
  """Single-run agent runner with automatic tool execution via Langchain"""
  try:
    result = agent.invoke(
    {"messages": history + [HumanMessage(content=user_input)]},
    config={"recursion_limit": 50}
    )
    # Return the last AI message
    return result["messages"][-1]
  except Exception as e:
    return AIMessage(content = f"Error:{str(e)}\n\nPlease try rephrasing your request or provide more specific details.")

if __name__ == "__main__":
  # # Test start calendar service & insert timed event
  # summary = 'Python 1 Hr Event Name'
  # now = datetime.now()
  # next_hour = (now + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
  # start_date = next_hour.isoformat()
  # end_date = (next_hour + timedelta(hours=1)).isoformat()
  # try:
  #   create_google_calendar_event(summary = summary, start_date = start_date, end_date = end_date)
  # except Exception as e:
  #   logger.error(f'An unexpected error occurred. Could not create google calendar event: {e}')

  # Run agent loop
  print("Initializing Google Calendar service...")
  print("If this is your first time, a browser window will open for authentication.")
  if get_calendar_service():
    print("Authentication successful! Calendar service is ready.")
  else:
    print("FATAL ERROR: Could not authenticate with Google Calendar.")
    print("Please check your credentials.json file and network connection.")
    exit(1)

  print("Create Google Calendar events.")
  print()
  print("Some prompt examples that you can use below:")
  print("  - Create an event titled 'Gym' for 2026-05-25 at 6 PM")
  print("  - Create an event with description 'Discuss project updates' on 2026-05-25 from 3 PM to 4 PM")
  print("  - Create an event at location 'Office' on 2026-05-25 from 10 AM to 11 AM")
  print()
  print("Commands: 'quit' or 'exit' to end")
  print("=" * 60)

  history: list[BaseMessage] = []

  while True:
    user_input = input("You: ").strip()

    # Check for exit commands
    if user_input.lower() in ['quit', 'exit', 'q', ""]:
      print("Goodbye!")
      break


    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] User input: {user_input}") # Log user input with timestamp

    user_input = timestamp + " - " + user_input # Prepend timestamp to user input for agent context  
    print("Agent: ", end="", flush=True)
    response = run_agent(user_input, history)
    print(response.content)
    print()

    # Update conversation history
    history += [HumanMessage(content=user_input), response]