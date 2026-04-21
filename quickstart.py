import datetime
import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
# SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"] # Read only scope
SCOPES = ["https://www.googleapis.com/auth/calendar"] # Read-write scope


def main():
  """Shows basic usage of the Google Calendar API.
  Prints the start and name of the next 10 events on the user's calendar.
  """
  creds = None
  # The file token.json stores the user's access and refresh tokens, and is
  # created automatically when the authorization flow completes for the first
  # time.
  if os.path.exists("token.json"):
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    full_path = os.path.abspath("token.json")
    print(f"File found at: {full_path}")
  # If there are no (valid) credentials available, let the user log in.
  if not creds or not creds.valid:
    #print("In here\n")
    if creds and creds.expired and creds.refresh_token:
      creds.refresh(Request())
      #print("In here 1\n")
    else:
      flow = InstalledAppFlow.from_client_secrets_file(
          #"credentials.json", SCOPES
          "gcp-desktop-client-credentials.json", SCOPES
      )
      #print("In here 2\n")
      creds = flow.run_local_server(port=0) #, prompt='select_account') --> un-comment to force a re-authentication each time
    # Save the credentials for the next run
    with open("token.json", "w") as token:
      token.write(creds.to_json())
  try:
    service = build("calendar", "v3", credentials=creds)

    # Create Calendar events

    # # Create event at current time + 1 hr
    # # Get current time and set start to end time to +1 to +2 hour from now
    # # Formatting as ISO 8601/RFC3339 is required by the API
    # now = datetime.datetime.now(datetime.timezone.utc)
    # start_time = (now + datetime.timedelta(hours=1)).isoformat()
    # end_time = (now + datetime.timedelta(hours=2)).isoformat()

    # # Define event details
    # event = {
    #   'summary': 'Python Meeting - 1 hr',
    #   'location': 'Online',
    #   'description': 'Automated meeting created via Python script.',
    #   'start': {
    #     'dateTime': start_time, #'2026-05-20T09:00:00-07:00', # YYYY-MM-DDTHH:MM:SS-Timezone
    #     'timeZone': 'UTC' #'America/Los_Angeles',
    #   },
    #   'end': {
    #     'dateTime': end_time, #'2026-05-20T10:00:00-07:00',
    #     'timeZone': 'UTC' #'America/Los_Angeles',
    #   },
    # }

    # # Insert the event
    # event = service.events().insert(calendarId='primary', body=event).execute()
    # print(f"Event created: {event.get('htmlLink')}")

    # Set-up an all day event
    # 2. Get current date in 'YYYY-MM-DD' format
    today = datetime.date.today()
    today_add_1= (today + datetime.timedelta(days=1)).isoformat()
    print(f"Today: {today}")

    # 3. Define the all-day event
    # Note: For all-day events, the 'end' date is exclusive (the day AFTER the event ends)
    today_add_2 = (today + datetime.timedelta(days=2)).isoformat()

    event = {
      'summary': 'Python All Day Event Name',
      'start': {
        'date': today_add_1,  # Start of the day
      },
      'end': {
        'date': today_add_2,  # Exclusive end (marks the whole of the 20th)
      },
    }



    # Insert the event
    event = service.events().insert(calendarId='primary', body=event).execute()
    print(f"Event created: {event.get('htmlLink')}")


    # Call the Calendar API
    now = datetime.datetime.now(tz=datetime.timezone.utc).isoformat()
    print("Getting the upcoming 10 events")
    events_result = (
        service.events()
        .list(
            calendarId="primary",
            timeMin=now,
            maxResults=10,
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )
    events = events_result.get("items", [])

    if not events:
      print("No upcoming events found.")
      return

    # Prints the start and name of the next 10 events
    for event in events:
      start = event["start"].get("dateTime", event["start"].get("date"))
      print(start, event["summary"])

  except HttpError as error:
    print(f"An error occurred: {error}")


if __name__ == "__main__":
  main()