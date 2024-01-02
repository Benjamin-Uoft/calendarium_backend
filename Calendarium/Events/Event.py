from dataclasses import dataclass
from datetime import datetime


@dataclass
class Event(object):
    """
    Event Object to keep track of the calendar events
    """
    subject: str
    location: str
    start_time: datetime
    end_time: datetime
    calendar_ids: dict[int, str]

