import time

from database.models import User, Account, Subscription

from database.db_transactions import db_transaction

from Calendarium.SyncUserData import SyncUserData
from datetime import datetime


db_trans = db_transaction()


class SyncMod:
    """
    Class incharge of synchronization
    """
    _last_subscription_check: datetime
    _last_sync: datetime
    _sync_user_objects: dict[str, SyncUserData]

    def __init__(self):
        print("Initializing SyncMod class...")
        self._sync_user_objects = {}
        self.check_subscription()
        print(self._sync_user_objects)
        self.sync_calendars()

    def check_subscription(self):
        """Programmer: Ali Rahbar
        Date: January 1, 2024

        Checks through the subscriptions and deletes the invalid ones
        """
        # Loop through all the subscriptions
        for subscription in Subscription.query.all():  # ToDo: Error
            print(subscription.user_id)
            # Collect the date
            till_date_valid = subscription.date_valid

            # if date has passed and is expired
            if till_date_valid < datetime.now():

                # Remove Subscription from table
                db_trans.delete_row_in_table(subscription)

                # remove from user object list
                if subscription.user_id in self._sync_user_objects:
                    del self._sync_user_objects[subscription.user_id]

            else:
                # Check if user doesn't exists
                if subscription.user_id not in self._sync_user_objects:
                    # Add user
                    self._sync_user_objects[subscription.user_id] = SyncUserData(subscription.user_id)

        # Push the last datetime updated as well as the new user
        self._last_subscription_check = datetime.now()

    def sync_calendars(self):
        """Programmer: Ali Rahbar
        Date: January 1, 2024

        Syncs All the subscribed calenders
        """
        for sync_user in self._sync_user_objects.values():
            sync_user.sync_user_data()

        self._last_sync = datetime.now()




