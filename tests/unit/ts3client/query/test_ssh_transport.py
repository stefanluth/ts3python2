import re
import socket

import paramiko
import pytest

from ts3client.ts3query import transport as transport_module
from ts3client.ts3query.transport import SSHTransport
from ts3client.utils import patterns


class FakeChannel:
    def __init__(self, chunks=None, timeout_when_empty=False):
        self.chunks = list(chunks or [])
        self.timeout_when_empty = timeout_when_empty
        self.sent = []
        self.send_calls = []
        self.timeout = None
        self.closed = False
        self.recv_calls = 0

    def recv(self, size):
        self.recv_calls += 1
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

    def send(self, data):
        self.send_calls.append(data)
        return len(data)

    def settimeout(self, timeout):
        self.timeout = timeout

    def gettimeout(self):
        return self.timeout

    def close(self):
        self.closed = True


class FakeSSHTransport:
    def __init__(self):
        self.keepalive = None
        self.active = True

    def set_keepalive(self, seconds):
        self.keepalive = seconds

    def is_active(self):
        return self.active


class FakeSSHClient:
    next_chunks = None
    timeout_when_empty = False
    connect_error: BaseException | None = None
    instances = []

    def __init__(self):
        FakeSSHClient.instances.append(self)
        self.policy = None
        self.system_keys_loaded = False
        self.loaded_host_keys = []
        self.saved_host_keys = []
        self.connect_kwargs = None
        self.shell_term = None
        self.channel = FakeChannel(self.next_chunks, self.timeout_when_empty)
        self.transport = FakeSSHTransport()
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


@pytest.fixture
def ssh_client(monkeypatch):
    monkeypatch.setattr(transport_module.paramiko, "SSHClient", FakeSSHClient)
    FakeSSHClient.next_chunks = None
    FakeSSHClient.timeout_when_empty = False
    FakeSSHClient.connect_error = None
    FakeSSHClient.instances = []
    return FakeSSHClient


def make_transport(ssh_client, chunks=None, **kwargs):
    ssh_client.next_chunks = chunks
    kwargs.setdefault("timeout", 1)
    transport = SSHTransport("host", 22, "user", "password", **kwargs)
    return transport, transport._client


def test_connect_uses_ssh_options_and_raw_shell(ssh_client):
    transport, client = make_transport(ssh_client, chunks=[], timeout=3)

    assert client.connect_kwargs["hostname"] == "host"
    assert client.connect_kwargs["port"] == 22
    assert client.connect_kwargs["username"] == "user"
    assert client.connect_kwargs["password"] == "password"
    assert client.connect_kwargs["look_for_keys"] is False
    assert client.connect_kwargs["allow_agent"] is False
    assert client.connect_kwargs["timeout"] == 3
    assert client.connect_kwargs["banner_timeout"] == 3
    assert client.connect_kwargs["auth_timeout"] == 3

    assert client.transport.keepalive == 30
    assert client.shell_term == "raw"
    assert client.channel.timeout == 3


def test_default_policy_rejects_unknown_keys(ssh_client):
    _, client = make_transport(ssh_client, chunks=[], use_system_host_keys=False)

    assert isinstance(client.policy, paramiko.RejectPolicy)
    assert client.system_keys_loaded is False
    assert client.loaded_host_keys == []


def test_accept_all_policy_loads_and_saves_known_hosts(ssh_client, tmp_path):
    known_hosts = tmp_path / "known_hosts"
    known_hosts.write_text("")

    _, client = make_transport(
        ssh_client,
        chunks=[],
        known_hosts=str(known_hosts),
        accept_all_keys=True,
        use_system_host_keys=True,
    )

    assert isinstance(client.policy, paramiko.AutoAddPolicy)
    assert client.system_keys_loaded is True
    assert client.loaded_host_keys == [str(known_hosts)]
    assert client.saved_host_keys == [str(known_hosts)]


def test_missing_known_hosts_is_not_loaded_or_saved(ssh_client, tmp_path):
    missing = tmp_path / "missing_known_hosts"

    _, client = make_transport(ssh_client, chunks=[], known_hosts=str(missing), use_system_host_keys=False)

    assert client.loaded_host_keys == []
    assert client.saved_host_keys == []


def test_saving_known_hosts_creates_the_parent_directory(ssh_client, tmp_path):
    known_hosts = tmp_path / "nested" / "dir" / "known_hosts"

    _, client = make_transport(
        ssh_client,
        chunks=[],
        known_hosts=str(known_hosts),
        accept_all_keys=True,
        use_system_host_keys=False,
    )

    assert client.saved_host_keys == [str(known_hosts)]
    assert known_hosts.parent.is_dir()


def test_connect_failure_closes_client(ssh_client):
    ssh_client.connect_error = paramiko.AuthenticationException("bad credentials")

    with pytest.raises(paramiko.AuthenticationException):
        SSHTransport("host", 22, "user", "password", timeout=1)

    assert ssh_client.instances[-1].closed is True


def test_expect_match_consumes_through_match_and_keeps_remainder(ssh_client):
    payload = b"clid=1\n\rerror id=0 msg=ok\n\rEXTRA"
    transport, _ = make_transport(ssh_client, chunks=[payload])

    index, match, text = transport.expect([patterns.RESPONSE_END_BYTES], timeout=1)

    assert index == 0
    assert match.group("id") == b"0"
    assert text == b"clid=1\n\rerror id=0 msg=ok\n\r"
    assert transport.read_until(b"EXTRA", timeout=1) == b"EXTRA"


def test_expect_returns_first_matching_pattern_index(ssh_client):
    transport, _ = make_transport(ssh_client, chunks=[b"ab"])

    index, match, text = transport.expect([re.compile(b"b"), re.compile(b"a")], timeout=1)

    assert index == 0
    assert match.group(0) == b"b"
    assert text == b"ab"


def test_expect_accepts_a_single_compiled_pattern(ssh_client):
    transport, _ = make_transport(ssh_client, chunks=[b"error id=0 msg=ok\n\r"])

    index, match, text = transport.expect(patterns.RESPONSE_END_BYTES, timeout=1)

    assert index == 0
    assert match.group("id") == b"0"
    assert text == b"error id=0 msg=ok\n\r"


def test_expect_timeout_returns_buffered_text_and_clears_buffer(ssh_client):
    ssh_client.timeout_when_empty = True
    transport, _ = make_transport(ssh_client, chunks=[b"partial"], timeout=0.05)

    index, match, text = transport.expect([patterns.RESPONSE_END_BYTES], timeout=0.05)

    assert (index, match, text) == (-1, None, b"partial")
    assert transport._buffer == b""


def test_expect_timeout_without_data_returns_empty(ssh_client):
    ssh_client.timeout_when_empty = True
    transport, _ = make_transport(ssh_client, chunks=[], timeout=0.05)

    assert transport.expect([patterns.RESPONSE_END_BYTES], timeout=0.05) == (-1, None, b"")


def test_expect_eof_without_data_raises(ssh_client):
    transport, _ = make_transport(ssh_client, chunks=[])

    with pytest.raises(EOFError):
        transport.expect([patterns.RESPONSE_END_BYTES], timeout=1)


def test_expect_eof_returns_buffered_text(ssh_client):
    transport, _ = make_transport(ssh_client, chunks=[b"partial"])

    assert transport.expect([patterns.RESPONSE_END_BYTES], timeout=1) == (-1, None, b"partial")


def test_read_until_timeout_returns_buffered_data(ssh_client):
    ssh_client.timeout_when_empty = True
    transport, _ = make_transport(ssh_client, chunks=[b"partial"], timeout=0.05)

    assert transport.read_until(b"\n\r", timeout=0.05) == b"partial"


def test_read_until_eof_without_data_raises(ssh_client):
    transport, _ = make_transport(ssh_client, chunks=[])

    with pytest.raises(EOFError):
        transport.read_until(b"\n\r", timeout=1)


def test_read_until_handles_delimiter_split_across_reads(ssh_client):
    transport, _ = make_transport(ssh_client, chunks=[b"TS3\n", b"\rWelcome\n\r"])

    assert transport.read_until(b"\n\r", timeout=1) == b"TS3\n\r"
    assert transport.read_until(b"\n\r", timeout=1) == b"Welcome\n\r"


def test_write_uses_sendall(ssh_client):
    transport, client = make_transport(ssh_client, chunks=[])

    transport.write(b"version\n")

    assert client.channel.sent == [b"version\n"]
    assert client.channel.send_calls == []


def test_write_after_close_raises(ssh_client):
    transport, _ = make_transport(ssh_client, chunks=[])
    transport.close()

    with pytest.raises(ConnectionError):
        transport.write(b"version\n")


def test_connected_and_close(ssh_client):
    transport, client = make_transport(ssh_client, chunks=[])

    assert transport.connected() is True

    client.transport.active = False
    assert transport.connected() is False
    client.transport.active = True

    transport.close()

    assert transport.connected() is False
    assert client.channel.closed is True
    assert client.closed is True

    transport.close()

    assert client.closed is True
