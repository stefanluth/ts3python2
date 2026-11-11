import paramiko
import pytest

from tests.support.fakes import FakeParamikoClient
from ts3client.ts3query import transport as transport_module
from ts3client.ts3query.transport import SSHTransport
from ts3client.utils import patterns


def test_constructor_configures_ssh_client(ssh_client):
    _, client = make_transport(ssh_client, chunks=[], timeout=3)

    assert client.connect_kwargs["hostname"] == "host"
    assert client.connect_kwargs["port"] == 22
    assert client.connect_kwargs["look_for_keys"] is False
    assert client.connect_kwargs["allow_agent"] is False
    assert client.shell_term == "raw"


@pytest.mark.parametrize(
    ("accept_all_keys", "precreated", "use_system_host_keys", "expected_policy", "saves_host_keys"),
    [
        (True, True, True, paramiko.AutoAddPolicy, True),
        (True, False, False, paramiko.AutoAddPolicy, True),
        (False, False, False, paramiko.RejectPolicy, False),
    ],
    ids=["auto-add-loads-existing", "auto-add-creates-parent", "reject-does-not-save"],
)
def test_host_key_policy_loads_and_saves_known_hosts(
    ssh_client, tmp_path, accept_all_keys, precreated, use_system_host_keys, expected_policy, saves_host_keys
):
    known_hosts = tmp_path / "nested" / "known_hosts"
    if precreated:
        known_hosts.parent.mkdir(parents=True)
        known_hosts.write_text("")

    _, client = make_transport(
        ssh_client,
        chunks=[],
        known_hosts=str(known_hosts),
        accept_all_keys=accept_all_keys,
        use_system_host_keys=use_system_host_keys,
    )

    assert isinstance(client.policy, expected_policy)
    assert client.system_keys_loaded is use_system_host_keys
    assert client.loaded_host_keys == ([str(known_hosts)] if precreated else [])
    assert client.saved_host_keys == ([str(known_hosts)] if saves_host_keys else [])
    assert known_hosts.parent.is_dir() is (accept_all_keys or precreated)


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


@pytest.mark.parametrize(
    ("method", "chunks", "timeout_when_empty", "expected"),
    [
        ("expect", [b"partial"], True, (-1, None, b"partial")),
        ("read_until", [b"partial"], True, b"partial"),
        ("read_until", [], False, None),
    ],
    ids=["timeout-drains-buffer", "read-until-timeout-drains-buffer", "eof-raises"],
)
def test_partial_buffer_is_drained_or_eof_is_raised(ssh_client, method, chunks, timeout_when_empty, expected):
    ssh_client.timeout_when_empty = timeout_when_empty
    transport, _ = make_transport(ssh_client, chunks=chunks, timeout=0.05)

    def call():
        if method == "expect":
            return transport.expect([patterns.RESPONSE_END_BYTES], timeout=0.05)
        return transport.read_until(b"\n\r", timeout=0.05)

    if expected is None:
        with pytest.raises(EOFError):
            call()
    else:
        assert call() == expected

    assert transport._buffer == b""


def test_read_until_handles_delimiter_split_across_reads(ssh_client):
    transport, _ = make_transport(ssh_client, chunks=[b"TS3\n", b"\rWelcome\n\r"])

    assert transport.read_until(b"\n\r", timeout=1) == b"TS3\n\r"
    assert transport.read_until(b"\n\r", timeout=1) == b"Welcome\n\r"


def test_close_disconnects_and_rejects_writes(ssh_client):
    transport, client = make_transport(ssh_client, chunks=[])

    assert transport.connected() is True

    client.transport.active = False
    assert transport.connected() is False
    client.transport.active = True

    transport.close()
    transport.close()

    assert transport.connected() is False
    assert client.channel.closed is True
    assert client.closed is True

    with pytest.raises(ConnectionError):
        transport.write(b"version\n")


def test_recv_restores_the_channel_timeout_after_a_failure(ssh_client):
    transport, _ = make_transport(ssh_client, chunks=[EOFError("boom")], timeout=1)

    with pytest.raises(EOFError):
        transport._recv(0.2)

    assert transport._channel is not None
    assert transport._channel.gettimeout() == 1


def test_write_rejects_a_closed_stream(ssh_client):
    transport, _ = make_transport(ssh_client, chunks=[])
    transport._eof = True

    with pytest.raises(ConnectionError):
        transport.write(b"version\n")


@pytest.fixture
def ssh_client(monkeypatch):
    monkeypatch.setattr(transport_module.paramiko, "SSHClient", FakeParamikoClient)
    FakeParamikoClient.next_chunks = None
    FakeParamikoClient.timeout_when_empty = False
    FakeParamikoClient.connect_error = None
    FakeParamikoClient.instances = []
    return FakeParamikoClient


def make_transport(ssh_client, chunks=None, **kwargs):
    ssh_client.next_chunks = chunks
    kwargs.setdefault("timeout", 1)
    transport = SSHTransport("host", 22, "user", "password", **kwargs)
    return transport, transport._client
