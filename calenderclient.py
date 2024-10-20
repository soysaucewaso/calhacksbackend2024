import datetime
import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/calendar"]


def get_calendar_info():
  """Shows basic usage of the Google Calendar API.
  Prints the start and name of the next 10 events on the user's calendar.
  """
  creds = None

  if os.path.exists("token.json"):
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)
  # If there are no (valid) credentials available, let the user log in.
  if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
      creds.refresh(Request())
    else:
      flow = InstalledAppFlow.from_client_secrets_file(
          "/Users/sawyer/Downloads/gmail_credentials.json", SCOPES
      )
      creds = flow.run_local_server(port=8080)
    # Save the credentials for the next run
    with open("token.json", "w") as token:
      token.write(creds.to_json())

  try:
    service = build("calendar", "v3", credentials=creds)

    # Call the Calendar API
    now_utc = datetime.datetime.utcnow()
    one_month_ago = (now_utc - datetime.timedelta(days=30)).strftime('%Y-%m-%dT%H:%M:%SZ')
    fifteen_days_from_now = (now_utc + datetime.timedelta(days=15)).strftime('%Y-%m-%dT%H:%M:%SZ')
    # calendar_list = service.calendarList().list().execute()
    events_result = (
        service.events()
        .list(
            calendarId="nnq1jg0hi0904ivqsu0o4953ks@group.calendar.google.com",
            timeMin=one_month_ago,
            maxResults=50,
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )
    events = events_result.get("items", [])

    if not events:
      return "No upcoming events found."
    all_summaries = ""

    # Prints the start and name of the next 10 events
    for event in events:
        # Extract relevant information
        summary = event.get('summary', 'No title')
        start = event['start'].get('dateTime', event['start'].get('date', 'No start time'))
        end = event['end'].get('dateTime', event['end'].get('date', 'No end time'))
        location = event.get('location', 'No location specified')
        description = event.get('description', 'No description')
        organizer = event.get('organizer', {}).get('email', 'No organizer specified')

        # Get attendees (excluding the organizer)
        attendees = [
            attendee['email']
            for attendee in event.get('attendees', [])
            if not attendee.get('organizer', False)
        ]

        # Check if it's a recurring event
        is_recurring = 'recurringEventId' in event

        # Check if there are reminders
        has_reminders = event.get('reminders', {}).get('useDefault', False) or event.get('reminders', {}).get(
            'overrides', [])

        # Create a summary string
        summary_text = f"""
        Event: {summary}
        Start: {start}
        End: {end}
        Location: {location}
        Organizer: {organizer}
        Attendees: {', '.join(attendees) if attendees else 'No attendees'}
        Recurring: {'Yes' if is_recurring else 'No'}
        Reminders: {'Yes' if has_reminders else 'No'}

        Description:
        {description[:100]}{'...' if len(description) > 100 else ''}
        """

        all_summaries += summary_text
        all_summaries += "-" * 50 + "\n"
    return all_summaries

  except HttpError as error:
    return f"An error occured with the Calender: {error}"

#  print(get_calendar_info())