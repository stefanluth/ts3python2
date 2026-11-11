import json
import re
import time

import pytest

from tests.support.integration import (
    channel_create,
    channel_delete,
    drain_messages,
    enable_text_receive,
    open_used_query,
    running_plugins,
    unique_name,
    wait_for_message,
    wait_until,
    whoami,
)
from ts3client.constants import NotifyRegisterType, TargetMode

pytestmark = pytest.mark.integration

CREATED_POLL_PATTERN = re.compile(r"Created (?:server|channel) poll ([a-z2-9]{3})", re.IGNORECASE)


def poll_config(polls_dir, check_interval=0.05):
    return {
        "prefix": "!",
        "check_interval": check_interval,
        "commands": {
            "Poll": {
                "trigger": "poll",
                "polls_dir": str(polls_dir),
                "notify_users": True,
                "notify_query_clients": True,
            }
        },
    }


def send(query, text, *, channel=False):
    query.commands.sendtextmessage(
        targetmode=TargetMode.CHANNEL if channel else TargetMode.SERVER,
        target=0,
        msg=text,
    )


def enable_events(query, *, channel=False):
    enable_text_receive(query, event=NotifyRegisterType.TEXT_SERVER)
    enable_text_receive(query, event=NotifyRegisterType.TEXT_PRIVATE)
    if channel:
        enable_text_receive(query, event=NotifyRegisterType.TEXT_CHANNEL, channel_id=0)
    drain_messages(query)


def drain(*queries):
    for query in queries:
        drain_messages(query)


def wait_for_poll_ready(query, timeout=15):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        send(query, "!poll help")
        try:
            return wait_for_message(query, "Poll commands:", contains=True, timeout=0.5)
        except AssertionError:
            continue
    raise AssertionError("bot did not become ready to receive poll commands")


def wait_for_created_poll(query, timeout=20):
    def find():
        return next(
            (message for message in query.unread_messages if CREATED_POLL_PATTERN.search(message.content)),
            None,
        )

    message = wait_until(find, timeout=timeout, message="did not receive the poll creation confirmation")
    match = CREATED_POLL_PATTERN.search(message.content)
    assert match is not None
    return match.group(1), message.content


def wait_for_private(query, text, timeout=20):
    def find():
        return next(
            (
                message
                for message in query.unread_messages
                if message.source == TargetMode.CLIENT and text in message.content
            ),
            None,
        )

    return wait_until(find, timeout=timeout, message="did not receive the poll private message")


def wait_for_source(query, text, source, timeout=20):
    def find():
        return next(
            (message for message in query.unread_messages if message.source == source and text in message.content),
            None,
        )

    return wait_until(find, timeout=timeout, message=f"did not receive the {source.name} poll message")


def test_server_poll_lifecycle(server, fresh_client, fresh_query, tmp_path):
    voter = open_used_query(server.host, server.query_port, server.server_port, server.password)
    try:
        enable_events(fresh_query)
        enable_events(voter)
        question = unique_name("question")
        alpha = unique_name("alpha")
        beta = unique_name("beta")

        with running_plugins(fresh_client, {"CommandHandler": poll_config(tmp_path)}):
            wait_for_poll_ready(fresh_query)
            drain(fresh_query, voter)
            send(fresh_query, f"!poll create {question}|{alpha}|{beta} --server")
            poll_id, confirmation = wait_for_created_poll(fresh_query)
            assert "server poll" in confirmation.lower()

            wait_for_source(voter, f"[server poll {poll_id}]", TargetMode.SERVER)
            wait_for_private(voter, question)

            send(voter, f"!poll vote {poll_id} a")
            wait_for_message(voter, f"Vote recorded for {poll_id}: a.", timeout=20)

            send(fresh_query, f"!poll results {poll_id}")
            wait_for_message(fresh_query, "Total voters: 1", contains=True, timeout=20)

            send(fresh_query, f"!poll end {poll_id}")
            wait_for_source(voter, "Status: ended", TargetMode.SERVER)
            wait_for_private(voter, "Status: ended")

        path = tmp_path / f"{poll_id}.json"
        assert path.exists()
        assert "results" in json.loads(path.read_text())
    finally:
        voter.stop_polling()
        voter.exit()


def test_channel_poll_filters_membership_and_notifies(server, fresh_client, fresh_query, used_query, tmp_path):
    voter = open_used_query(server.host, server.query_port, server.server_port, server.password)
    outsider = open_used_query(server.host, server.query_port, server.server_port, server.password)
    outside_cid = channel_create(used_query, unique_name("poll-outside"))
    try:
        outside_clid = whoami(outsider)["client_id"]
        assert used_query.commands.clientmove(clid=outside_clid, cid=outside_cid).error_id == 0
        wait_until(
            lambda: used_query.commands.clientinfo(clid=outside_clid).data[0]["cid"] == outside_cid,
            timeout=10,
            message="outsider was not moved to the other channel",
        )

        enable_events(fresh_query, channel=True)
        enable_events(voter, channel=True)
        enable_text_receive(outsider, event=NotifyRegisterType.TEXT_PRIVATE)
        drain_messages(outsider)

        question = unique_name("question")
        alpha = unique_name("alpha")
        beta = unique_name("beta")

        with running_plugins(fresh_client, {"CommandHandler": poll_config(tmp_path)}):
            wait_for_poll_ready(fresh_query)
            drain(fresh_query, voter, outsider)
            send(fresh_query, f"!poll create {question}|{alpha}|{beta}", channel=True)
            poll_id, confirmation = wait_for_created_poll(fresh_query)
            assert "channel poll" in confirmation.lower()

            wait_for_source(voter, f"[channel poll {poll_id}", TargetMode.CHANNEL)
            wait_for_private(voter, question)
            time.sleep(0.2)
            assert not any(
                message.source == TargetMode.CLIENT and question in message.content
                for message in outsider.unread_messages
            )

            send(outsider, f"!poll vote {poll_id} a")
            wait_for_message(outsider, "only", contains=True, timeout=10)

            send(voter, f"!poll vote {poll_id} a")
            wait_for_message(voter, f"Vote recorded for {poll_id}: a.", timeout=10)

            send(fresh_query, f"!poll results {poll_id}")
            wait_for_message(fresh_query, "Total voters: 1", contains=True, timeout=10)

            send(fresh_query, f"!poll end {poll_id}")
            wait_for_source(voter, "Status: ended", TargetMode.CHANNEL)

        path = tmp_path / f"{poll_id}.json"
        data = json.loads(path.read_text())
        assert data["scope"] == "channel"
        assert data["results"]["total_voters"] == 1
    finally:
        outsider.stop_polling()
        outsider.exit()
        channel_delete(used_query, outside_cid)
        voter.stop_polling()
        voter.exit()


def test_multi_choice_anonymous_and_timed_poll(server, fresh_client, fresh_query, tmp_path):
    voter = open_used_query(server.host, server.query_port, server.server_port, server.password)
    try:
        enable_events(fresh_query)
        enable_events(voter)
        question = unique_name("question")
        alpha = unique_name("alpha")
        beta = unique_name("beta")
        gamma = unique_name("gamma")

        with running_plugins(fresh_client, {"CommandHandler": poll_config(tmp_path)}):
            wait_for_poll_ready(fresh_query)
            drain(fresh_query, voter)
            send(
                fresh_query,
                f"!poll create {question}|{alpha}|{beta}|{gamma} --multi --anonymous --duration 2s",
            )
            poll_id, confirmation = wait_for_created_poll(fresh_query)
            assert "anonymous" in confirmation.lower()
            assert "multiple choices" in confirmation.lower()

            wait_for_private(voter, question)

            send(voter, f"!poll vote {poll_id} a")
            send(voter, f"!poll vote {poll_id} ac")
            wait_until(
                lambda: (
                    sum(1 for message in voter.unread_messages if f"Vote recorded for {poll_id}" in message.content)
                    >= 2
                ),
                timeout=10,
                message="did not receive both vote confirmations",
            )

            send(fresh_query, f"!poll results {poll_id}")
            results = wait_for_message(fresh_query, "Total selections: 2", contains=True, timeout=10)
            assert "Total voters: 1" in results.content
            assert f"a) {alpha}: 1" in results.content
            assert f"b) {beta}: 0" in results.content
            assert f"c) {gamma}: 1" in results.content
            voter_name = whoami(voter)["client_nickname"]
            assert voter_name not in results.content
            assert "serveradmin" not in results.content

            wait_for_source(fresh_query, "Status: ended", TargetMode.SERVER, timeout=10)
            wait_for_source(voter, "Status: ended", TargetMode.SERVER, timeout=10)

        path = tmp_path / f"{poll_id}.json"
        data = json.loads(path.read_text())
        assert data["closed"] is True
        assert data["anonymous"] is True
        assert data["multi_choice"] is True
        assert data["voter_names"] == {}
        assert data["results"]["total_voters"] == 1
        assert data["results"]["total_selections"] == 2
        assert all(len(key) == 64 for key in data["votes"])
    finally:
        voter.stop_polling()
        voter.exit()


def test_poll_survives_plugin_restart(server, fresh_client, fresh_query, tmp_path):
    voter = open_used_query(server.host, server.query_port, server.server_port, server.password)
    try:
        enable_events(fresh_query)
        enable_events(voter)
        question = unique_name("question")
        alpha = unique_name("alpha")
        beta = unique_name("beta")
        config = {"CommandHandler": poll_config(tmp_path)}

        with running_plugins(fresh_client, config):
            wait_for_poll_ready(fresh_query)
            drain(fresh_query, voter)
            send(fresh_query, f"!poll create {question}|{alpha}|{beta} --server")
            poll_id, _ = wait_for_created_poll(fresh_query)
            wait_for_private(voter, question)
            send(voter, f"!poll vote {poll_id} b")
            wait_for_message(voter, f"Vote recorded for {poll_id}: b.", timeout=10)

        with running_plugins(fresh_client, config):
            wait_for_poll_ready(fresh_query)
            drain(fresh_query, voter)
            send(fresh_query, f"!poll results {poll_id}")
            results = wait_for_message(fresh_query, "Total voters: 1", contains=True, timeout=10)
            assert f"b) {beta}: 1" in results.content

        path = tmp_path / f"{poll_id}.json"
        data = json.loads(path.read_text())
        assert data["votes"]
        assert data["results"]["total_voters"] == 1
    finally:
        voter.stop_polling()
        voter.exit()
