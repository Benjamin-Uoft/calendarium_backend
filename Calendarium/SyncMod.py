import time

from database.db_transactions import db_transaction

from Calendarium.SyncUserData import SyncUserData
from flask import current_app


def start_sync():
    sync_user_data = SyncUserData()

    while True:
        time.sleep(30)
        sync_user_data.sync_user_data()


if __name__ == "__main__":
    start_sync()


