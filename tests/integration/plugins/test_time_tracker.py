import json
import re
import time
from datetime import datetime

import pytest

from plugins.time_tracker_store import TimeTrackerStore, get_store, reset_stores
from tests.support.integration import (
    channel_create,
    channel_delete,
    drain_messages,
    enable_text_receive,
    running_plugins,
    send_text,
    unique_name,
    wait_for_private,
    wait_until,
    whoami,
)
from tests.support.paths import hashed_path
from ts3client.constants import NotifyRegisterType, TargetMode

pytestmark = pytest.mark.integration

TRACKER_MARKERS = (
    "Time tracking for",
    "Top tracked time",
    "No tracked",
    "Tracker commands:",
    "Unknown metric:",
    "Time tracking enabled.",
    "Time tracking disabled.",
)

LEADERBOARD_LINE = re.compile(r"^\s+(\d+)\.\s+(.*?)\s+-\s+")


@pytest.fixture(autouse=True)
def clean_tracker_stores():
    reset_stores()
    yield
    reset_stores()


def tracker_config(
    data_dir,
    *,
    trigger="tracker",
    include_query_clients=True,
    idle_threshold=0,
    afk_channel_ids=None,
    check_interval=0.05,
    leaderboard_size=10,
):
    return {
        "TimeTracker": {
            "data_dir": str(data_dir),
            "check_interval": check_interval,
            "idle_threshold": idle_threshold,
            "afk_channel_ids": list(afk_channel_ids or []),
            "include_query_clients": include_query_clients,
        },
        "CommandHandler": {
            "prefix": "!",
            "check_interval": 0.05,
            "commands": {
                "Tracker": {
                    "trigger": trigger,
                    "description": "Tracker",
                    "data_dir": str(data_dir),
                    "leaderboard_size": leaderboard_size,
                }
            },
        },
    }


def profile_file(data_dir, uid):
    return hashed_path(data_dir / "profiles", uid)


def profile_data(data_dir, uid):
    try:
        return json.loads(profile_file(data_dir, uid).read_text())
    except OSError, ValueError:
        return None


def wait_for_profile(data_dir, uid, predicate=None, timeout=20, message=None):
    def check():
        data = profile_data(data_dir, uid)
        if data is None:
            return None
        if predicate is not None and not predicate(data):
            return None
        return data

    return wait_until(
        check,
        timeout=timeout,
        message=message or f"profile {uid} did not reach the expected state",
    )


def assert_profile_schema(data, uid, name=None, *, require_last_seen=True):
    assert data["schema_version"] == 1
    assert data["uid"] == uid
    assert isinstance(data["name"], str) and data["name"]
    if name is not None:
        assert data["name"] == name
    for key in ("total_seconds", "idle_seconds", "afk_seconds"):
        value = data[key]
        assert isinstance(value, int | float) and not isinstance(value, bool)
        assert value >= 0
    assert data["idle_seconds"] <= data["total_seconds"]
    assert data["afk_seconds"] <= data["total_seconds"]
    assert isinstance(data["session_count"], int) and data["session_count"] >= 1
    assert isinstance(data["do_not_track"], bool)
    datetime.fromisoformat(data["created_at"])
    datetime.fromisoformat(data["updated_at"])
    if require_last_seen:
        assert data["last_seen_at"] is not None
        datetime.fromisoformat(data["last_seen_at"])


def seed_profile(data_dir, uid, name, *, total, idle=0, afk=0, do_not_track=False):
    store = TimeTrackerStore(data_dir)
    store.record_interval(uid, name, elapsed=total, idle_elapsed=idle, afk_elapsed=afk, new_session=True)
    if do_not_track:
        store.set_do_not_track(uid, True)


def enable_tracker_events(query):
    enable_text_receive(query, event=NotifyRegisterType.TEXT_SERVER)
    enable_text_receive(query, event=NotifyRegisterType.TEXT_PRIVATE)
    drain_messages(query)


def wait_for_server(query, text, timeout=20):
    def find():
        return next(
            (
                message
                for message in query.unread_messages
                if message.source == TargetMode.SERVER and text in message.content
            ),
            None,
        )

    message = wait_until(find, timeout=timeout, message=f"did not receive a server message containing {text!r}")
    message.mark_as_used()
    return message


def wait_for_server_any(query, texts, timeout=20):
    def find():
        return next(
            (
                message
                for message in query.unread_messages
                if message.source == TargetMode.SERVER and any(text in message.content for text in texts)
            ),
            None,
        )

    message = wait_until(
        find,
        timeout=timeout,
        message=f"did not receive a server message containing any of {texts!r}",
    )
    message.mark_as_used()
    return message


def wait_for_tracker_ready(query, trigger="tracker", timeout=20):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        send_text(query, f"!{trigger} help")
        try:
            return wait_for_private(query, "Tracker commands:", timeout=0.5)
        except AssertionError:
            continue
    raise AssertionError("bot did not become ready to receive tracker commands")


def assert_no_server_replies(query):
    replies = [
        message
        for message in query.unread_messages
        if message.source == TargetMode.SERVER and any(marker in message.content for marker in TRACKER_MARKERS)
    ]
    assert replies == [], [message.content for message in replies]


def assert_no_private_replies(query):
    replies = [
        message
        for message in query.unread_messages
        if message.source == TargetMode.CLIENT and any(marker in message.content for marker in TRACKER_MARKERS)
    ]
    assert replies == [], [message.content for message in replies]


def leaderboard_entries(message):
    entries = []
    for line in message.content.splitlines():
        match = LEADERBOARD_LINE.match(line)
        if match is not None:
            entries.append((int(match.group(1)), match.group(2).strip()))
    return entries


def move_to(used_query, clid, cid):
    assert used_query.commands.clientmove(clid=clid, cid=cid).error_id == 0
    wait_until(
        lambda: int(used_query.commands.clientinfo(clid=clid).data[0]["cid"]) == cid,
        timeout=10,
        message="client was not moved to the expected channel",
    )


def test_time_tracker_lifecycle_and_private_public_routing(fresh_client, fresh_query, used_query, tmp_path):
    afk_cid = channel_create(used_query, unique_name("tracker-afk"))
    data_dir = tmp_path / "time_tracker"
    identity = whoami(fresh_query)
    uid = identity["client_unique_identifier"]
    try:
        move_to(used_query, identity["client_id"], afk_cid)
        enable_tracker_events(fresh_query)

        with running_plugins(fresh_client, tracker_config(data_dir, afk_channel_ids=[afk_cid])):
            wait_for_tracker_ready(fresh_query)
            drain_messages(fresh_query)

            data = wait_for_profile(
                data_dir,
                uid,
                lambda item: item["total_seconds"] > 0 and item["afk_seconds"] > 0,
            )
            assert_profile_schema(data, uid)

            send_text(fresh_query, "!tracker me")
            me = wait_for_private(fresh_query, "Time tracking for")
            for expected in ("Total:", "Idle:", "AFK:", "Sessions:", "Rank:", "Tracking: enabled", "Last seen:"):
                assert expected in me.content
            assert_no_server_replies(fresh_query)

            send_text(fresh_query, "!tracker top")
            top = wait_for_server(fresh_query, "Top tracked time (total):")
            assert leaderboard_entries(top)
            assert_no_private_replies(fresh_query)

            send_text(fresh_query, "!tracker top idle")
            assert "(idle)" in wait_for_server(fresh_query, "Top tracked time (idle):").content

            send_text(fresh_query, "!tracker top afk")
            assert "(afk)" in wait_for_server(fresh_query, "Top tracked time (afk):").content

        persisted = json.loads(profile_file(data_dir, uid).read_text())
        assert_profile_schema(persisted, uid)
        assert persisted["total_seconds"] > 0
        assert persisted["afk_seconds"] > 0
    finally:
        channel_delete(used_query, afk_cid)


def test_time_tracker_idle_threshold_and_accumulation(fresh_client, fresh_query, tmp_path):
    data_dir = tmp_path / "time_tracker"
    identity = whoami(fresh_query)
    uid = identity["client_unique_identifier"]
    enable_tracker_events(fresh_query)

    with running_plugins(fresh_client, tracker_config(data_dir, idle_threshold=3600)):
        wait_for_tracker_ready(fresh_query)
        drain_messages(fresh_query)
        data = wait_for_profile(data_dir, uid, lambda item: item["total_seconds"] > 0)
        assert data["idle_seconds"] == 0

    fresh_query.stop_polling()
    with running_plugins(fresh_client, tracker_config(data_dir, idle_threshold=0)):
        data = wait_for_profile(data_dir, uid, lambda item: item["idle_seconds"] > 0)
        assert data["idle_seconds"] <= data["total_seconds"]

        fresh_query.start_polling(0.05)
        drain_messages(fresh_query)
        wait_for_tracker_ready(fresh_query)
        send_text(fresh_query, "!tracker me")
        me = wait_for_private(fresh_query, "Time tracking for")
        assert "Idle:" in me.content


def test_time_tracker_opt_out_opt_in_and_visibility(fresh_client, fresh_query, tmp_path):
    data_dir = tmp_path / "time_tracker"
    identity = whoami(fresh_query)
    uid = identity["client_unique_identifier"]
    enable_tracker_events(fresh_query)

    with running_plugins(fresh_client, tracker_config(data_dir, idle_threshold=3600)):
        wait_for_tracker_ready(fresh_query)
        drain_messages(fresh_query)
        wait_for_profile(data_dir, uid, lambda item: item["total_seconds"] > 0)

        send_text(fresh_query, "!tracker optout")
        assert "Time tracking disabled." in wait_for_private(fresh_query, "Time tracking disabled.").content
        data = wait_for_profile(data_dir, uid, lambda item: item["do_not_track"] is True)
        captured_total = data["total_seconds"]
        time.sleep(0.5)
        data = profile_data(data_dir, uid)
        assert data is not None
        assert data["total_seconds"] <= captured_total + 1.0
        assert all(profile.uid != uid for profile in get_store(data_dir).leaderboard(10))

        send_text(fresh_query, "!tracker top")
        wait_for_server_any(fresh_query, ("Top tracked time", "No tracked total time"))

        send_text(fresh_query, "!tracker me")
        me = wait_for_private(fresh_query, "Time tracking for")
        assert "Tracking: disabled" in me.content
        assert "Rank: hidden (opted out)" in me.content

        send_text(fresh_query, "!tracker optin")
        assert "Time tracking enabled." in wait_for_private(fresh_query, "Time tracking enabled.").content
        wait_for_profile(data_dir, uid, lambda item: item["do_not_track"] is False)
        wait_for_profile(data_dir, uid, lambda item: item["total_seconds"] > captured_total + 0.5)
        assert any(profile.uid == uid for profile in get_store(data_dir).leaderboard(10))

        send_text(fresh_query, "!tracker top")
        assert "Top tracked time" in wait_for_server(fresh_query, "Top tracked time").content


def test_time_tracker_leaderboard_metrics_and_persisted_players(fresh_client, fresh_query, tmp_path):
    data_dir = tmp_path / "time_tracker"
    seed_profile(data_dir, "seed-a", "Seed A", total=100_000, idle=50_000, afk=10_000)
    seed_profile(data_dir, "seed-b", "Seed B", total=90_000, idle=60_000, afk=5_000)
    seed_profile(data_dir, "seed-c", "Seed C", total=80_000, idle=40_000, afk=20_000)
    seed_profile(data_dir, "seed-hidden", "Hidden Seed", total=999_999, idle=999_999, afk=999_999, do_not_track=True)
    identity = whoami(fresh_query)
    uid = identity["client_unique_identifier"]
    enable_tracker_events(fresh_query)

    with running_plugins(fresh_client, tracker_config(data_dir, idle_threshold=3600, leaderboard_size=2)):
        wait_for_tracker_ready(fresh_query)
        drain_messages(fresh_query)
        wait_for_profile(data_dir, uid, lambda item: item["total_seconds"] > 0)

        send_text(fresh_query, "!tracker top")
        top = wait_for_server(fresh_query, "Top tracked time (total):")
        assert [index for index, _ in leaderboard_entries(top)] == [1, 2]
        assert [name for _, name in leaderboard_entries(top)] == ["Seed A", "Seed B"]
        assert "Hidden Seed" not in top.content
        assert_no_private_replies(fresh_query)

        send_text(fresh_query, "!tracker top idle")
        idle_top = wait_for_server(fresh_query, "Top tracked time (idle):")
        assert [name for _, name in leaderboard_entries(idle_top)] == ["Seed B", "Seed A"]

        send_text(fresh_query, "!tracker top afk")
        afk_top = wait_for_server(fresh_query, "Top tracked time (afk):")
        assert [name for _, name in leaderboard_entries(afk_top)] == ["Seed C", "Seed A"]

        send_text(fresh_query, "!tracker me")
        me = wait_for_private(fresh_query, "Time tracking for")
        assert "Rank: #" in me.content

    for seeded_uid in ("seed-a", "seed-b", "seed-c", "seed-hidden"):
        data = json.loads(profile_file(data_dir, seeded_uid).read_text())
        assert_profile_schema(data, seeded_uid)
        assert data["do_not_track"] == (seeded_uid == "seed-hidden")


def test_time_tracker_rejects_invalid_commands_without_state_change(fresh_client, fresh_query, tmp_path):
    data_dir = tmp_path / "time_tracker"
    identity = whoami(fresh_query)
    uid = identity["client_unique_identifier"]
    enable_tracker_events(fresh_query)

    with running_plugins(fresh_client, tracker_config(data_dir, idle_threshold=3600)):
        wait_for_tracker_ready(fresh_query)
        drain_messages(fresh_query)
        wait_for_profile(data_dir, uid, lambda item: item["total_seconds"] > 0)

        send_text(fresh_query, "!tracker top steps")
        assert "Unknown metric: steps." in wait_for_private(fresh_query, "Unknown metric: steps.").content
        assert_no_server_replies(fresh_query)

        send_text(fresh_query, "!tracker nonsense")
        assert "Tracker commands:" in wait_for_private(fresh_query, "Tracker commands:").content

        data = profile_data(data_dir, uid)
        assert data is not None
        assert_profile_schema(data, uid)
        assert data["do_not_track"] is False
        assert data["total_seconds"] > 0


def test_time_tracker_excludes_query_clients_by_default(fresh_client, fresh_query, tmp_path):
    data_dir = tmp_path / "time_tracker"
    identity = whoami(fresh_query)
    uid = identity["client_unique_identifier"]
    enable_tracker_events(fresh_query)

    with running_plugins(fresh_client, tracker_config(data_dir, include_query_clients=False)):
        wait_for_tracker_ready(fresh_query)
        drain_messages(fresh_query)
        time.sleep(0.5)
        assert profile_data(data_dir, uid) is None

        send_text(fresh_query, "!tracker me")
        assert "No tracking data yet." in wait_for_private(fresh_query, "No tracking data yet.").content

        send_text(fresh_query, "!tracker top")
        assert "No tracked total time yet." in wait_for_server(fresh_query, "No tracked total time yet.").content


def test_time_tracker_custom_trigger_and_leaderboard_size(fresh_client, fresh_query, tmp_path):
    data_dir = tmp_path / "time_tracker"
    seed_profile(data_dir, "seed-top", "Top Seed", total=100_000, idle=10_000, afk=1_000)
    seed_profile(data_dir, "seed-second", "Second Seed", total=50_000, idle=5_000, afk=500)
    identity = whoami(fresh_query)
    uid = identity["client_unique_identifier"]
    enable_tracker_events(fresh_query)

    with running_plugins(
        fresh_client, tracker_config(data_dir, trigger="time", idle_threshold=3600, leaderboard_size=1)
    ):
        wait_for_tracker_ready(fresh_query, trigger="time")
        drain_messages(fresh_query)
        wait_for_profile(data_dir, uid, lambda item: item["total_seconds"] > 0)

        send_text(fresh_query, "!time top")
        top = wait_for_server(fresh_query, "Top tracked time (total):")
        assert [index for index, _ in leaderboard_entries(top)] == [1]
        assert "Top Seed" in top.content
        assert "Second Seed" not in top.content

        send_text(fresh_query, "!time me")
        me = wait_for_private(fresh_query, "Time tracking for")
        assert "Time tracking for " in me.content


def test_time_tracker_survives_restart(fresh_client, fresh_query, tmp_path):
    data_dir = tmp_path / "time_tracker"
    identity = whoami(fresh_query)
    uid = identity["client_unique_identifier"]
    enable_tracker_events(fresh_query)

    with running_plugins(fresh_client, tracker_config(data_dir, idle_threshold=3600)):
        wait_for_tracker_ready(fresh_query)
        drain_messages(fresh_query)
        first = wait_for_profile(data_dir, uid, lambda item: item["total_seconds"] > 0)
        assert_profile_schema(first, uid)

    before_restart = profile_data(data_dir, uid)
    assert before_restart is not None
    first_total = before_restart["total_seconds"]
    first_sessions = before_restart["session_count"]

    with running_plugins(fresh_client, tracker_config(data_dir, idle_threshold=3600)):
        wait_for_tracker_ready(fresh_query)
        drain_messages(fresh_query)
        second = wait_for_profile(
            data_dir,
            uid,
            lambda item: item["total_seconds"] > first_total,
            timeout=10,
        )
        assert second["total_seconds"] >= first_total
        assert second["total_seconds"] - first_total < 10
        assert second["session_count"] >= first_sessions
        assert_profile_schema(second, uid)

        send_text(fresh_query, "!tracker me")
        assert "Total:" in wait_for_private(fresh_query, "Time tracking for").content

        send_text(fresh_query, "!tracker top")
        assert leaderboard_entries(wait_for_server(fresh_query, "Top tracked time (total):"))

    final = json.loads(profile_file(data_dir, uid).read_text())
    assert_profile_schema(final, uid)
    assert final["total_seconds"] >= first_total


def test_time_tracker_quarantines_corrupt_profile(fresh_client, fresh_query, tmp_path):
    data_dir = tmp_path / "time_tracker"
    identity = whoami(fresh_query)
    uid = identity["client_unique_identifier"]
    name = identity["client_nickname"]
    seed_profile(data_dir, uid, name, total=5, idle=0, afk=0)
    corrupt_path = data_dir / "profiles" / "corrupt.json"
    corrupt_path.write_text("{not json")
    enable_tracker_events(fresh_query)

    with running_plugins(fresh_client, tracker_config(data_dir, idle_threshold=3600)):
        wait_for_tracker_ready(fresh_query)
        drain_messages(fresh_query)
        data = wait_for_profile(data_dir, uid, lambda item: item["total_seconds"] > 5)
        assert_profile_schema(data, uid)
        assert not corrupt_path.exists()
        quarantined = list((data_dir / "profiles").glob(".corrupt-*"))
        assert len(quarantined) == 1

        send_text(fresh_query, "!tracker me")
        assert "Time tracking for " in wait_for_private(fresh_query, "Time tracking for").content

    persisted = json.loads(profile_file(data_dir, uid).read_text())
    assert_profile_schema(persisted, uid)
