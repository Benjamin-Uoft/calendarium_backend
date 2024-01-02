from database.db_transactions import db_transaction
from database.models import User, Account

from Calendarium.Events.Event import Event
from Calendarium.Calendars.Base.CalendarAccount import CalenderService
from Calendarium.Calendars.Google import GoogleCalendarService
from Calendarium.Calendars.Microsoft import OutlookCalendarService

db_trans = db_transaction()


class SyncUserData:
    _user: User
    _accounts: list[CalenderService]
    _tracked_events: list[Event]

    def __init__(self, user_id):
        self._user = User.query.get(user_id=user_id).first()
        self._accounts = []

        # Collect the accounts the user has
        data_query = Account.query.filter(user_id=user_id)

        for account in db_trans.select_from_table_all_query(data_query):
            if account.type == 'Google':
                self._accounts.append(GoogleCalendarService(account))

            elif account.type == 'Microsoft':
                self._accounts.append(OutlookCalendarService(account))


        self._events = []

    def sync_user_data(self):

        # Loop through all the accounts
        for account_details in self._accounts:
            # Connect to account
            account = Account(account_details)

            events = account.read_events_from_calendar()

            for event in events:
                if self._does_event_exist(event) and self._event_time_same(event):  # ToDo: work on update
                    events.remove(event)

                else:
                    self._push_events_to_other_accounts(event, account_details)

            # ToDo Check if the event got deleted

    def _does_event_exist(self, event):
        return any([event.calendar_ids.values()[0] in old_event.calendar_ids.values() for old_event in self._events])

    def _event_time_same(self, event):
        old_event = [old_event for old_event in self._events if event.calendar_ids.values()[0] in old_event.calendar_ids.values()][0]

        return old_event.name == event.name and old_event.location == event.location and old_event.start_time == event.start_time and old_event.end_time == event.end_time

    def _push_events_to_other_accounts(self, new_event, account_details):
        remaining_accounts = [account for account in self._accounts if account != account_details]

        for account in remaining_accounts:
            new_event.calendar_ids[account.account_id] = account.add_event(new_event)

        self._events.append(new_event)

    def get_user_id(self):
        return self._user.user_id



