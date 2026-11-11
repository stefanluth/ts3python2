import time
from contextlib import contextmanager

import paramiko

from plugins.plugin_manager import PluginManager
from ts3client.constants import NotifyRegisterType
from ts3client.ts3query import TS3Query

TRANSIENT_ERRORS = (EOFError, ConnectionError, OSError, paramiko.SSHException)


@contextmanager
def running_plugins(client, config, timeout=5):
    manager = PluginManager(client, config)
    manager.run()
    try:
        yield manager
    finally:
        manager.stop(timeout=timeout)
        assert all(not thread.is_alive() for thread, _ in manager.threads.values())


def wait_until(predicate, timeout=10, interval=0.1, message="condition not met"):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        value = predicate()
        if value:
            return value
        time.sleep(interval)
    raise AssertionError(message)


def wait_for_message(query, text, timeout=15, contains=False):
    def matches(message):
        return text in message.content if contains else message.content == text

    kind = "containing " if contains else ""
    return wait_until(
        lambda: next((message for message in query.unread_messages if matches(message)), None),
        timeout=timeout,
        message=f"did not receive message {kind}{text!r}",
    )


def unique_name(prefix="test"):
    return f"{prefix}-{time.time_ns()}"


def ts3_date(day):
    return day.strftime("%d-%m-%Y")


def whoami(query):
    return query.commands.whoami().data[0]


def drain_messages(query):
    for message in query.unread_messages:
        message.mark_as_used()


def drain_events(client):
    for event in client.get_unread_events():
        event.used = True


def server_banner(query):
    server_info = query.commands.serverinfo().data[0]
    return {
        "url": server_info.get("virtualserver_hostbanner_gfx_url") or "",
        "mode": server_info.get("virtualserver_hostbanner_mode"),
    }


def restore_server_banner(query, banner):
    query.commands.serveredit(
        virtualserver_hostbanner_gfx_url=banner["url"],
        virtualserver_hostbanner_mode=banner["mode"],
    )


def enable_text_receive(query, event=NotifyRegisterType.TEXT_PRIVATE, channel_id=None):
    kwargs = {"event": event}
    if channel_id is not None:
        kwargs["id"] = channel_id
    query.commands.servernotifyregister(**kwargs)
    query.start_polling(0.1)


def channel_create(query, name, **kwargs):
    kwargs.setdefault("channel_flag_permanent", True)
    response = query.commands.channelcreate(channel_name=name, **kwargs)
    assert response.error_id == 0, response
    return response.data[0]["cid"]


def channel_delete(query, cid):
    query.commands.channeldelete(cid=cid, force=True)


def retry(attempt, retries=3, description="an operation", error_types=TRANSIENT_ERRORS):
    """Run attempt() until it succeeds, retrying transient transport errors."""
    last_error = None
    for index in range(retries):
        try:
            return attempt()
        except paramiko.AuthenticationException:
            raise
        except error_types as error:
            last_error = error
            if index + 1 < retries:
                time.sleep(1.5 * (index + 1))
    raise AssertionError(f"could not {description}: {last_error}")


def configure_server_flood(host, port, password, retries=5):
    def attempt():
        query = TS3Query(host, port, "serveradmin", password, timeout=5, accept_all_keys=True)
        try:
            query.flood_protection_timeout = 1.2
            response = query.commands.instanceedit(
                serverinstance_serverquery_flood_commands=10000,
                serverinstance_serverquery_flood_time=1,
                serverinstance_serverquery_flood_ban_time=1,
            )
            if response.error_id == 0:
                return
            if response.error_id != 524:
                raise AssertionError(response)
            raise ConnectionError(f"flood limits not applied yet: {response}")
        finally:
            try:
                query.exit()
            except Exception:
                pass

    retry(attempt, retries=retries, description="configure TS3 flood limits")


def _connect_query(host, port, password):
    query = TS3Query(host, port, "serveradmin", password, timeout=5, accept_all_keys=True)
    try:
        query.flood_protection_timeout = 1.2
        query.disable_flood_protection()
        return query
    except Exception:
        query.exit()
        raise


def open_used_connection(connect, close, server_port, retries=3, description="select a TS3 virtual server"):
    def attempt():
        connection = connect()
        try:
            query = getattr(connection, "query", connection)
            response = query.commands.use(port=server_port)
            if response.error_id == 0:
                return connection
            raise ConnectionError(f"could not select a TS3 virtual server: {response}")
        except Exception:
            try:
                close(connection)
            except Exception:
                pass
            raise

    return retry(attempt, retries=retries, description=description)


def open_used_query(host, port, server_port, password, retries=3):
    return open_used_connection(
        lambda: _connect_query(host, port, password),
        close=lambda query: query.exit(),
        server_port=server_port,
        retries=retries,
    )
