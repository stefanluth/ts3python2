import logging
import re
import socket

from ts3client.ts3query.ts3query_response import TS3QueryResponse

_EMPTY_MATCH = re.match(b"", b"")


class FakeLogger(logging.Logger):
    def __init__(self):
        super().__init__("fake")

    def debug(self, message, *args, **kwargs):
        pass

    def info(self, message, *args, **kwargs):
        pass

    def warning(self, message, *args, **kwargs):
        pass

    def error(self, message, *args, **kwargs):
        pass

    def exception(self, message, *args, **kwargs):
        pass


class FakeResponse(TS3QueryResponse):
    def __init__(self, data=None, error_id=0, msg="ok", events=None, messages=None, response=b""):
        self.index = 0
        self.match = _EMPTY_MATCH
        self.response = response
        self.error_id = error_id
        self.msg = msg
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
        self.exit_calls = 0
        self.started = []
        self.stopped = 0
        self.events = []
        self.messages = []

    def exit(self):
        self.exit_calls += 1

    def start_polling(self, interval=1):
        self.started.append(interval)

    def stop_polling(self):
        self.stopped += 1


class FakeClient:
    def __init__(self):
        self.id = 1
        self.message_batches = []
        self.sent = []
        self.enabled = []
        self.query = FakeQuery()
        self.users = []
        self.user_infos = {}
        self.moves = []
        self.events = []
        self.channels = []
        self.channel_sent = []
        self.server_sent = []
        self.messages_sent = []

    def get_unread_messages(self):
        return self.message_batches.pop(0) if self.message_batches else []

    def send_private_message(self, clid, message):
        self.sent.append((clid, message))

    def send_channel_message(self, message):
        self.channel_sent.append(message)

    def send_server_message(self, message):
        self.server_sent.append(message)

    def send_message(self, target, target_mode, message):
        self.messages_sent.append((target, target_mode, message))

    def enable_message_events(self):
        self.enabled.append("message")

    def enable_events_and_messages(self):
        self.enabled.append("events_and_messages")

    def get_users(self):
        return self.users

    def get_user_info(self, clid):
        return self.user_infos[clid]

    def move_user(self, clid, cid):
        self.moves.append((clid, cid))

    def get_user_entered_events(self):
        return [event for event in self.events if not event.used]


class FakeMessage:
    def __init__(self, content, invokername="user", invokerid=1, invokeruid="uid-1", targetmode=1, target=0):
        self.content = content
        self.invokername = invokername
        self.invokerid = invokerid
        self.invokeruid = invokeruid
        self.targetmode = targetmode
        self.target = target
        self.used = False

    def mark_as_used(self):
        self.used = True


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


class FakeSSHTransport:
    def __init__(self, *args, **kwargs):
        self.written = []
        self.expect_result = (0, None, b"")
        self.expect_error = None
        self.connected_flag = True
        self.closed = False
        self.close_calls = 0

    def connected(self):
        return self.connected_flag and not self.closed

    def write(self, data):
        self.written.append(data)

    def expect(self, patterns, timeout=None):
        if self.expect_error is not None:
            raise self.expect_error
        return self.expect_result

    def read_until(self, delimiter, timeout=None):
        return b""

    def close(self):
        self.closed = True
        self.close_calls += 1


class FakeParamikoChannel:
    def __init__(self, chunks=None, timeout_when_empty=False):
        self.chunks = list(chunks or [])
        self.timeout_when_empty = timeout_when_empty
        self.sent = []
        self.timeout = None
        self.closed = False

    def recv(self, size):
        if self.chunks:
            item = self.chunks.pop(0)
            if isinstance(item, BaseException):
                raise item
            return item
        if self.timeout_when_empty:
            raise socket.timeout()
        return b""

    def sendall(self, data):
        self.sent.append(data)

    def settimeout(self, timeout):
        self.timeout = timeout

    def gettimeout(self):
        return self.timeout

    def close(self):
        self.closed = True


class FakeParamikoTransport:
    def __init__(self):
        self.active = True

    def set_keepalive(self, seconds):
        pass

    def is_active(self):
        return self.active


class FakeParamikoClient:
    next_chunks = None
    timeout_when_empty = False
    connect_error: BaseException | None = None
    instances: list["FakeParamikoClient"] = []

    def __init__(self):
        type(self).instances.append(self)
        self.policy = None
        self.system_keys_loaded = False
        self.loaded_host_keys = []
        self.saved_host_keys = []
        self.connect_kwargs = None
        self.shell_term = None
        self.channel = FakeParamikoChannel(self.next_chunks, self.timeout_when_empty)
        self.transport = FakeParamikoTransport()
        self.closed = False

    def set_missing_host_key_policy(self, policy):
        self.policy = policy

    def load_system_host_keys(self):
        self.system_keys_loaded = True

    def load_host_keys(self, filename):
        self.loaded_host_keys.append(filename)

    def connect(self, **kwargs):
        error = type(self).connect_error
        if error is not None:
            raise error
        self.connect_kwargs = kwargs

    def get_transport(self):
        return self.transport

    def invoke_shell(self, term):
        self.shell_term = term
        return self.channel

    def save_host_keys(self, filename):
        self.saved_host_keys.append(filename)

    def close(self):
        self.closed = True
