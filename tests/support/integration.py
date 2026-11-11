import time
from contextlib import contextmanager
from datetime import date

import paramiko

from plugins.plugin_manager import PluginManager
from ts3client.constants import NotifyRegisterType
from ts3client.ts3query import TS3Query


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


def unique_name(prefix="test"):
    return f"{prefix}-{time.time_ns()}"


def today_ts3():
    return date.today().strftime("%d-%m-%Y")


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


def wait_for_private_message(query, text, timeout=15):
    return wait_until(
        lambda: next((message for message in query.unread_messages if message.content == text), None),
        timeout=timeout,
        message=f"did not receive private message {text!r}",
    )


def wait_for_private_message_containing(query, needle, timeout=15):
    return wait_until(
        lambda: next((message for message in query.unread_messages if needle in message.content), None),
        timeout=timeout,
        message=f"did not receive private message containing {needle!r}",
    )


def configure_server_flood(host, port, password, retries=5):
    last_error = None
    for attempt in range(retries):
        query = None
        try:
            query = TS3Query(host, port, "serveradmin", password, timeout=5, accept_all_keys=True)
            query.flood_protection_timeout = 1.2
            response = query.commands.instanceedit(
                serverinstance_serverquery_flood_commands=10000,
                serverinstance_serverquery_flood_time=1,
                serverinstance_serverquery_flood_ban_time=1,
            )
            if response.error_id == 0:
                return
            last_error = response
            if response.error_id != 524:
                raise AssertionError(response)
        except paramiko.AuthenticationException:
            raise
        except (EOFError, ConnectionError, OSError, paramiko.SSHException) as error:
            last_error = error
        finally:
            if query is not None:
                try:
                    query.exit()
                except Exception:
                    pass
        time.sleep(1.5 * (attempt + 1))
    raise AssertionError(f"could not configure TS3 flood limits: {last_error}")


def open_query(host, port, password, retries=3):
    last_error = None
    for attempt in range(retries):
        query = None
        try:
            query = TS3Query(host, port, "serveradmin", password, timeout=5, accept_all_keys=True)
            query.flood_protection_timeout = 1.2
            query.disable_flood_protection()
            return query
        except paramiko.AuthenticationException:
            raise
        except (EOFError, ConnectionError, OSError, paramiko.SSHException) as error:
            last_error = error
            if query is not None:
                try:
                    query.exit()
                except Exception:
                    pass
        time.sleep(1.5 * (attempt + 1))
    raise AssertionError(f"could not open a TS3 query connection: {last_error}")


def open_used_query(host, port, server_port, password, retries=3):
    last_error = None
    for attempt in range(retries):
        query = open_query(host, port, password)
        response = query.commands.use(port=server_port)
        if response.error_id == 0:
            return query
        last_error = response
        query.exit()
        time.sleep(1.5 * (attempt + 1))
    raise AssertionError(f"could not select a TS3 virtual server: {last_error}")


def register_text_receive(query, event=NotifyRegisterType.TEXT_PRIVATE, channel_id=None):
    kwargs = {"event": event}
    if channel_id is not None:
        kwargs["id"] = channel_id
    query.commands.servernotifyregister(**kwargs)


def enable_text_receive(query, event=NotifyRegisterType.TEXT_PRIVATE, channel_id=None):
    register_text_receive(query, event=event, channel_id=channel_id)
    query.start_polling(0.1)


def channel_create(query, name, **kwargs):
    kwargs.setdefault("channel_flag_permanent", True)
    response = query.commands.channelcreate(channel_name=name, **kwargs)
    assert response.error_id == 0, response
    return response.data[0]["cid"]


def channel_delete(query, cid):
    query.commands.channeldelete(cid=cid, force=True)
