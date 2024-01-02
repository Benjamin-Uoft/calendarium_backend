import requests
from msal import TokenCache

from Calendarium.Calendars.Base.CalendarAccount import CalenderService
from Calendarium.Events.Event import Event
import webbrowser
from datetime import datetime, timedelta
import json
import os
import msal
from database.models import Account


class OutlookCalendarService(CalenderService):
    """
    Microsoft Outlook Calendar Service
    """

    _SCOPES = ['Calendars.ReadWrite', 'Calendars.ReadBasic']
    _GRAPH_API_ENDPOINT = 'https://graph.microsoft.com/v1.0'
    _APP_ID = '60109714-43af-4fde-ac6c-db47725dfefd'
    _headers: dict
    _account: Account

    def __init__(self, account: Account):
        self._account = account
        self._access_token = None

        # Save Session Token as a token file
        access_token_cache = msal.SerializableTokenCache()

        # read the token file
        if os.path.exists('ms_graph_api_token.json'):
            access_token_cache.deserialize(open('ms_graph_api_token.json', "r").read())
            token_detail = json.load(open('ms_graph_api_token.json', ))
            token_detail_key = list(token_detail['AccessToken'].keys())[0]
            token_expiration = datetime.fromtimestamp(int(token_detail['AccessToken'][token_detail_key]['expires_on']))
            if datetime.now() > token_expiration:
                # Token is expired, refresh it
                self._refresh_token(access_token_cache)

        # assign a SerializableTokenCache object to the client instance
        client = msal.PublicClientApplication(client_id=self._APP_ID, token_cache=access_token_cache)

        accounts = client.get_accounts()
        if accounts:
            # load the session
            token_response = client.acquire_token_silent(self._SCOPES, accounts[0])
        else:
            # authenticate your account as usual
            flow = client.initiate_device_flow(scopes=self._SCOPES)
            print('user_code: ' + flow['user_code'])
            webbrowser.open(flow['verification_uri'])
            token_response = client.acquire_token_by_device_flow(flow)

            # Writing to the file
            with open('ms_graph_api_token.json', 'w') as _f:
                _f.write(access_token_cache.serialize())

            # Print statements for debugging
            print("Token successfully written to file.")
            print(f"Token file path: {'ms_graph_api_token.json'}")

        # Add this to the __init__ method of OutlookCalendarService
        self._access_token = token_response
        self._headers = {
            'Authorization': 'Bearer ' + self._access_token['access_token']
        }

    def _refresh_token(self, access_token_cache):
        # Ensure you have the refresh token saved securely
        refresh_token = access_token_cache.find(TokenCache.CredentialType.REFRESH_TOKEN)[0]

        # Microsoft Identity Platform endpoint for token endpoint
        token_endpoint = "https://login.microsoftonline.com/common/oauth2/v2.0/token"

        # Create a confidential client application
        confidential_client = msal.ConfidentialClientApplication(
            self._APP_ID,
            authority="https://login.microsoftonline.com/common",
            client_credential=refresh_token.secret,
        )

        # Acquire a new access token using the refresh token
        token_response = confidential_client.acquire_token_by_refresh_token(
            refresh_token=refresh_token.secret,
            scopes=self._SCOPES,
        )

        # Update the token cache with the new access token
        access_token_cache.add(
            msal.TokenCache.CredentialType.ACCESS_TOKEN,
            msal.Credential(
                client_id=self._APP_ID,
                secret=None,
                token_response=token_response,
            ),
        )

        # Save the updated token cache to the file
        with open('ms_graph_api_token.json', 'w') as _f:
            _f.write(access_token_cache.serialize())

        # Update the instance variable with the new access token
        self._access_token = token_response

        # Update the headers with the new access token
        self._headers = {
            'Authorization': 'Bearer ' + self._access_token['access_token']
        }

        print("Token successfully refreshed.")

    def read_events_from_calendar(self):
        response = requests.get(
            self._GRAPH_API_ENDPOINT + '/me/calendar/events',
            headers=self._headers
        )

        results = []

        for event in response.json().get('value', []):
            results.append(Event(subject=event['subject'],
                                 location=event['location'],
                                 start_time=datetime.fromisoformat(event['start']['dateTime']),
                                 end_time=datetime.fromisoformat(event['end']['dateTime']),
                                 calendar_ids={self._account.account_id, event['id']}
                                 ))

        return results

    def add_event_to_calendar(self, event):
        request_body = {
            "subject": event.subject,
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

        response = requests.post(
            self._GRAPH_API_ENDPOINT + f'/me/events',
            headers=self._headers,
            json=request_body
        )

        print(response.json())
        return response

    def delete_event_from_calendar(self, event_id):
        if not event_id:
            print("Event ID is required to delete an event.")
            return

        response = requests.delete(
            self._GRAPH_API_ENDPOINT + f'/me/events/{event_id}',
            headers=self._headers
        )

        if response.status_code == 204:
            print(f"Event with ID {event_id} deleted successfully.")
        else:
            print(f"Error deleting event: {response.status_code}, {response.text}")


if __name__ == '__main__':
    calendar = OutlookCalendarService(Account())

    calendar.read_events_from_calendar()
