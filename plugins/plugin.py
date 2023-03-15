import threading


class Plugin:
    def __init__(self, event: threading.Event):
        self.event = event
