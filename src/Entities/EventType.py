import time


class EventType:
    def __init__(self, event_id=None, start_time=None, active=None):
        self.event_id = id(self) if event_id is None else event_id
        self.start_time = start_time if start_time is not None else time.time()
        self.active = active if active is not None else True

        # self.Involved_Players 1 & 2

    def end(self):
        self.end_time = time.time()
        self.active = False
