from database.db_transactions import db_transaction
from database.models import User, Account, Event
from Calendarium.Calendars.Events.Event import TempEvent
from Calendarium.account import Account


db_trans = db_transaction()


class SyncUserData:
    _user: User
    _accounts: list[Account]
    _events: list[Event]

    def __init__(self, user_id):
        self._user = User.query.get(user_id=user_id).first()

        # Collect the accounts the user has
        data_query = Account.query.filter(user_id=user_id)
        self._accounts = db_trans.select_from_table_all_query(data_query)

        # Collect All the events from the database
        data_query = Event.query.filter(user_id=user_id)
        self._events = db_trans.select_from_table_all_query(data_query)

    def sync_user_data(self):

        # Loop through all the accounts
        for account_details in self._accounts:
            # Connect to account
            account = Account(account_details)

            events = account.read_events_from_calendar()

            # Split the events into old and new
            old_events, new_events = self.check_if_event_exists(events)

            # Push new events to other accounts
            self.push_events_to_other_accounts(new_events, account_details)


    def check_if_event_exists(self, events):

        old_events = []
        new_events = []

        # Loop through all the events
        for event in events:
            if any(event_id in recorded_events.event_ids for recorded_events in self._events for event_id in event.event_ids):
                old_events.append(event)

            else:
                new_events.append(event)

        return old_events, new_events

    def push_events_to_other_accounts(self, new_events, account_details):
        remaining_accounts = [account for account in self._accounts if account != account_details]

        for account_details in remaining_accounts:

            account = Account(account_details)

            for new_event in new_events:
                new_event.event_ids[account_details['type']] = account.add_event_to_calendar(new_event)

        self._events.extend(new_events)

    def get_user_id(self):
        return self._user.user_id



