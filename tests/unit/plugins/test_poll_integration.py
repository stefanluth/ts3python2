import json
from datetime import datetime, timedelta, timezone

import pytest

import plugins.commands.poll as poll_module
from plugins.plugins.command_handler import CommandHandler
from tests.support.fakes import FakeClient, FakeLogger, FakeMessage, FakeStopEvent, make_user

NOW = datetime(2026, 11, 12, 12, 0, tzinfo=timezone.utc)


@pytest.fixture(autouse=True)
def deterministic_poll_ids(monkeypatch):
    monkeypatch.setattr("plugins.poll_store.random.choice", lambda alphabet: "a")


def make_handler(client, stop):
    handler = CommandHandler(client, stop)
    handler.logger = FakeLogger()
    return handler


def make_config(polls_dir):
    return {
        "Poll": {
            "trigger": "poll",
            "polls_dir": str(polls_dir),
            "notify_users": False,
            "description": "Polls",
        }
    }


def test_command_handler_runs_poll_lifecycle_and_stops(tmp_path, monkeypatch):
    client = FakeClient()
    client.users = [
        make_user(2, "Creator", "creator-uid"),
        make_user(3, "Alice", "uid-3"),
    ]
    handler = make_handler(client, FakeStopEvent(stop_after_waits=4))
    client.message_batches = [
        [
            FakeMessage(
                "!poll create Lunch? | Pizza | Sushi", invokername="Creator", invokerid=2, invokeruid="creator-uid"
            )
        ],
        [FakeMessage("!poll vote aaa b", invokername="Alice", invokerid=3, invokeruid="uid-3")],
        [FakeMessage("!poll results aaa", invokername="Alice", invokerid=3, invokeruid="uid-3")],
    ]

    handler.run(prefix="!", commands=make_config(tmp_path), check_interval=0)

    assert "aaa" in client.server_sent[0]
    assert "Lunch?" in client.server_sent[0]
    assert (3, "Vote recorded for aaa: b.") in client.sent
    creator_messages = [text for target, text in client.sent if target == 2]
    assert any("Alice voted on poll aaa: b. Total voters: 1." in text for text in creator_messages)
    results = [text for target, text in client.sent if target == 3 and "Poll aaa: Lunch?" in text]
    assert results
    assert "Total voters: 1" in results[-1]

    path = tmp_path / "aaa.json"
    assert path.exists()
    data = json.loads(path.read_text())
    assert "results" in data
    assert data["votes"] == {"uid-3": [1]}
    assert data["results"]["total_voters"] == 1


def test_command_handler_tick_closes_timed_poll_and_stops_poll(tmp_path, monkeypatch):
    timed_dir = tmp_path / "timed"
    monkeypatch.setattr(poll_module, "utcnow", lambda: NOW)

    client = FakeClient()
    client.users = [
        make_user(2, "Creator", "creator-uid"),
        make_user(3, "Alice", "uid-3"),
    ]
    handler = make_handler(client, FakeStopEvent(stop_after_waits=1))
    client.message_batches = [
        [
            FakeMessage(
                "!poll create Timed? | A | B --duration 1s",
                invokername="Creator",
                invokerid=2,
                invokeruid="creator-uid",
            )
        ]
    ]

    handler.run(prefix="!", commands=make_config(timed_dir), check_interval=0)

    path = timed_dir / "aaa.json"
    assert path.exists()
    assert json.loads(path.read_text())["closed"] is False

    monkeypatch.setattr(poll_module, "utcnow", lambda: NOW + timedelta(seconds=2))
    handler.event = FakeStopEvent(stop_after_waits=1)
    handler.run(prefix="!", commands=make_config(timed_dir), check_interval=0)

    assert "Status: ended" in client.server_sent[-1]
    assert "Results: !poll results aaa" in client.server_sent[-1]
    data = json.loads(path.read_text())
    assert data["closed"] is True

    stopped = []
    original_stop = handler.commands[0].stop

    def recording_stop():
        stopped.append(True)
        original_stop()

    handler.commands[0].stop = recording_stop
    handler.stop()

    assert stopped == [True]
