import logging
import re

from ts3client.ts3query.ts3query_response import TS3QueryResponse


class FakeLogger(logging.Logger):
    def __init__(self):
        super().__init__("fake")
        self.records = []

    def _record(self, level, message):
        self.records.append((level, message))

    def debug(self, message, *args, **kwargs):
        self._record("debug", message)

    def info(self, message, *args, **kwargs):
        self._record("info", message)

    def warning(self, message, *args, **kwargs):
        self._record("warning", message)

    def error(self, message, *args, **kwargs):
        self._record("error", message)

    def exception(self, message, *args, **kwargs):
        self._record("exception", message)


class FakeResponse(TS3QueryResponse):
    def __init__(self, data=None, error_id=0, msg="ok", events=None, messages=None, response=b""):
        match = re.search(b"", b"")
        assert match is not None
        self.index = 0
        self.match = match
        self.response = response
        self.error_id = error_id
        self.msg = msg
        self.extra_msg = None
        self.data = {0: {}} if data is None else data
        self.events = [] if events is None else events
        self.messages = [] if messages is None else messages


class FakeCommands:
    def __init__(self):
        self.calls = []
        self.responses = {}

    def __getattr__(self, name):
        def command(*args, **kwargs):
            self.calls.append((name, args, kwargs))
            response = self.responses.get(name)
            if callable(response):
                return response(*args, **kwargs)
            return response if response is not None else FakeResponse()

        return command

    def called(self, name):
        return [call for call in self.calls if call[0] == name]


class FakeQuery:
    def __init__(self, commands=None):
        self.commands = commands or FakeCommands()
        self.messages = []
        self.events = []
        self.unread_messages = []
        self.unread_events = []
        self.sent = []
        self.polling = False
        self.keep_alive_calls = 0
        self.exit_calls = 0
        self.login_calls = []

    def login(self, login, password):
        self.login_calls.append((login, password))

    def logout(self):
        self.logout_calls = getattr(self, "logout_calls", 0) + 1

    def start_polling(self, *args, **kwargs):
        self.polling = True

    def stop_polling(self):
        self.polling = False

    def keep_alive(self):
        self.keep_alive_calls += 1

    def exit(self):
        self.exit_calls += 1

    def send(self, command):
        self.sent.append(command)
        return FakeResponse()


class FakeSSHTransport:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self.written = []
        self.expect_result = (0, None, b"")
        self.expect_error = None
        self.expect_calls = []
        self.read_until_result = b""
        self.read_until_results = []
        self.read_until_calls = []
        self.connected_flag = True
        self.closed = False
        self.close_calls = 0

    def connected(self):
        return self.connected_flag and not self.closed

    def write(self, data):
        self.written.append(data)

    def expect(self, patterns, timeout=None):
        self.expect_calls.append((patterns, timeout))
        if self.expect_error is not None:
            raise self.expect_error
        return self.expect_result

    def read_until(self, delimiter, timeout=None):
        self.read_until_calls.append((delimiter, timeout))
        if self.read_until_results:
            return self.read_until_results.pop(0)
        return self.read_until_result

    def close(self):
        self.closed = True
        self.close_calls += 1


class FakeStopEvent:
    def __init__(self, stop_after_waits=1):
        self.stop_after_waits = stop_after_waits
        self.waits = 0
        self.stopped = False

    def is_set(self):
        return self.stopped

    def set(self):
        self.stopped = True

    def wait(self, timeout=None):
        self.waits += 1
        if self.waits >= self.stop_after_waits:
            self.stopped = True
        return self.stopped


class FakeMessage:
    def __init__(self, content, invokername="user", invokerid=1):
        self.content = content
        self.invokername = invokername
        self.invokerid = invokerid
        self.used = False

    def mark_as_used(self):
        self.used = True


class FakeClient:
    def __init__(self):
        self.message_batches = []
        self.events = []
        self.sent = []
        self.enabled = []
        self.query = FakeQuery()

    def get_unread_messages(self):
        return self.message_batches.pop(0) if self.message_batches else []

    def get_user_entered_events(self):
        return self.events

    def send_private_message(self, clid, message):
        self.sent.append((clid, message))

    def enable_message_events(self):
        self.enabled.append("message")

    def enable_events_and_messages(self):
        self.enabled.append("all")
