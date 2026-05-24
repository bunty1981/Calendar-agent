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
    timezone: str = 'UTC' #'America/Los_Angeles',
) -> str:
  """
  Creates an event on the user's primary Google Calendar.

  Args:
      summary: The title or summary of the event.
      start_time: The start time in ISO format (e.g., '2025-11-03T10:00:00').
      end_time: The end time in ISO format (e.g., '2025-11-03T11:00:00').
      description: Optional description for the event.
      location: Optional location for the event.
      timezone: The timezone for the event, defaults to 'Asia/Singapore'.

  Returns:
      A JSON string with the event link or an error message.
  """

  # Access the google calendar
  service = get_calendar_service()
  if not service:
      return json.dumps({"error": "Failed to get Google Calendar service. Check authentication."})

  
  # create the event
  event = {
    'summary' : summary,
    'start' : {'dateTime': start_date, 'timeZone': timezone},
    'end' : {'dateTime': end_date, 'timeZone': timezone}
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
    timezone: str = 'UTC' #'America/Los_Angeles',
) -> str:
  """
  Creates an event on the user's primary Google Calendar.

  Args:
      summary: The title or summary of the event.
      start_time: The start time in ISO format (e.g., '2025-11-03T10:00:00').
      end_time: The end time in ISO format (e.g., '2025-11-03T11:00:00').
      description: Optional description for the event.
      location: Optional location for the event.
      timezone: The timezone for the event, defaults to 'Asia/Singapore'.

  Returns:
      A JSON string with the event link or an error message.
  """
  return create_google_calendar_event_func(summary, start_date, end_date, description, location, timezone) 

  # # Running on github / codespaces
  # import os;
  # openai_api_key = os.environ.get("OPENAI_API_KEY") # Assumes OPENAI_API_KEY setup in github secrets
  # anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY") # Assumes OPENAI_API_KEY setup in github secrets

  # llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, api_key=openai_api_key) 
  # #llm_claude = ChatAnthropic(model="claude-3-5-sonnet-20241022", temperature=0, api_key=anthropic_api_key) 

# Running on local machines
import os;
from dotenv import load_dotenv # Load in environment variable, including secrete keys for .env
# *** If using this method ensure .env is listed in .gitignore do it STAYS local

OPENAI_API_KEY = os.getenv("HOME_MAC_OPENAI_API_KEY")
print(f"Loaded OPENAI_API_KEY: {'Yes' if OPENAI_API_KEY else 'No'}") # Debug print to confirm key loading
print(f"OPENAI_API_KEY: {OPENAI_API_KEY[:5]}...") # Print first 5 characters for verification without exposing full key

ANTHROPIC_API_KEY = os.getenv("HOME_MAC_ANTHROPIC_API_KEY")
print(f"Loaded ANTHROPIC_API_KEY: {'Yes' if ANTHROPIC_API_KEY else 'No'}") # Debug print to confirm key loading
print(f"ANTHROPIC_API_KEY: {ANTHROPIC_API_KEY[-5:]}...") # Print first 5 characters for verification without exposing full key


#llm = ChatOpenAI(model="gpt-4", temperature=0, api_key="OPENAI_API_KEY") 
llm = ChatAnthropic(model="claude-2", temperature=0, base_url="https://api.anthropic.com", api_key="ANTHROPIC_API_KEY")

TOOLS = [create_google_calendar_event]
SYSTEM_MESSAGE = ("You are a helpful personal assistant who can create events on google calendar.")

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

    print("Agent: ", end="", flush=True)
    response = run_agent(user_input, history)
    print(response.content)
    print()

    # Update conversation history
    history += [HumanMessage(content=user_input), response]