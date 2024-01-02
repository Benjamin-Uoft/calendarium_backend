from Calendarium.Calendars.Base.CalendarAccount import CalenderService
import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from database.models import Account
from googleapiclient.errors import HttpError

from datetime import datetime, timedelta

from Calendarium.Events.Event import Event


class GoogleCalendarService(CalenderService):
    _SCOPES = ['https://www.googleapis.com/auth/calendar.events']
    _account: Account

    def __init__(self, account):

        self._account = account

        # Set up OAuth 2.0 credentials
        creds = None
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists("token.json"):
            creds = Credentials.from_authorized_user_file("token.json", self._SCOPES)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    "credentials.json", self._SCOPES
                )
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open("token.json", "w") as token:
                token.write(creds.to_json())

        # Build the service
        self._service = build('calendar', 'v3', credentials=creds)

    def read_events_from_calendar(self):
        # Call the API to get events
        events_result = self._service.events().list(calendarId='primary', timeMin='2023-01-01T00:00:00Z',
                                                    timeMax='2024-01-30T23:59:59Z', maxResults=10, singleEvents=True,
                                                    orderBy='startTime').execute()

        results = []
        # loop though all the events
        for event in events_result.get('items', []):
            try:
                results.append(Event(subject=event['summary'],
                                     location=event['location'],
                                     start_time=datetime.fromisoformat(event['start']['dateTime']),
                                     end_time=datetime.fromisoformat(event['end']['dateTime']),
                                     calendar_ids={self._account.account_id, event['id']}
                                     ))
            except:
                results.append(Event(subject=event['summary'],
                                     location='',
                                     start_time=datetime.fromisoformat(event['start']['dateTime']),
                                     end_time=datetime.fromisoformat(event['end']['dateTime']),
                                     calendar_ids={self._account.account_id, event['id']}
                                     ))

        return results

    def add_event_to_calendar(self, event):
        # Define the event
        body = {
            'summary': event.subject,
            'location': event.location,
            'start': {
                'dateTime': event.start_time.isoformat(),
                'timeZone': 'UTC',
            },
            'end': {
                'dateTime': event.end_time.isoformat(),
                'timeZone': 'UTC',
            },
        }

        # Insert the event
        event = self._service.events().insert(calendarId='primary', body=body).execute()

        return event['id']

    def delete_event_from_calendar(self, event_id):
        # Call the API to delete the event
        response = self._service.events().delete(calendarId='primary', eventId=event_id).execute()
        return response


if __name__ == '__main__':
    calendar = GoogleCalendarService(Account())
    calendar.read_events_from_calendar()
