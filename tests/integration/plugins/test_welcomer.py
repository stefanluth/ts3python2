import pytest

from tests.support.integration import (
    drain_events,
    enable_text_receive,
    open_used_query,
    running_plugins,
    unique_name,
    wait_for_message,
    wait_until,
    whoami,
)
from ts3client.constants import NotifyRegisterType
from ts3client.event import ClientEnterViewEvent

pytestmark = pytest.mark.integration


def test_welcomer_sends_a_message_to_a_joining_client(server, fresh_client):
    fresh_client.enable_events_and_messages()
    drain_events(fresh_client)

    joining = open_used_query(server.host, server.query_port, server.server_port, server.password)
    try:
        clid = whoami(joining)["client_id"]
        event = wait_until(
            lambda: next(
                (
                    event
                    for event in fresh_client.get_events()
                    if isinstance(event, ClientEnterViewEvent) and event.clid == clid and not event.used
                ),
                None,
            ),
            timeout=15,
            message="bot did not receive the client enter event",
        )

        # The test harness only creates ServerQuery clients, which Welcomer
        # intentionally ignores. Promote the real event to a voice client so the
        # welcome path runs against the live server.
        assert event.client_type == 1
        event.client_type = 0

        enable_text_receive(joining, event=NotifyRegisterType.TEXT_PRIVATE)

        message = unique_name("welcome")
        with running_plugins(fresh_client, {"Welcomer": {"messages": [message]}}):
            wait_for_message(joining, message)
            assert event.used is True
    finally:
        joining.stop_polling()
        joining.exit()
