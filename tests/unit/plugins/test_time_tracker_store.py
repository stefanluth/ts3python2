import hashlib
import json
from datetime import datetime, timedelta, timezone

import pytest

from plugins.time_tracker_store import TimeTrackerStore, TrackerError, format_duration, get_store, reset_stores
from tests.support.fakes import FakeLogger

NOW = datetime(2026, 11, 12, 12, 0, tzinfo=timezone.utc)
LATER = NOW + timedelta(hours=1)


def make_store(tmp_path):
    return TimeTrackerStore(tmp_path / "time_tracker", logger=FakeLogger())


def profile_path(data_dir, uid):
    digest = hashlib.sha256(uid.encode("utf-8")).hexdigest()
    return data_dir / "profiles" / f"{digest}.json"


def test_accumulation_clamps_counters_and_keeps_invariants(tmp_path):
    store = make_store(tmp_path)

    profile = store.record_interval(
        "uid-1",
        "Alice",
        elapsed=60,
        idle_elapsed=30,
        afk_elapsed=20,
        new_session=True,
        now=NOW,
    )

    assert profile is not None
    assert profile.total_seconds == 60
    assert profile.idle_seconds == 30
    assert profile.afk_seconds == 20
    assert profile.session_count == 1
    assert profile.last_connected_at == NOW.isoformat()
    assert profile.last_seen_at == NOW.isoformat()

    profile = store.record_interval(
        "uid-1",
        "Alice",
        elapsed=100,
        idle_elapsed=200,
        afk_elapsed=50,
        now=LATER,
    )

    assert profile is not None
    assert profile.total_seconds == 160
    assert profile.idle_seconds == 130
    assert profile.afk_seconds == 70
    assert profile.idle_seconds <= profile.total_seconds
    assert profile.afk_seconds <= profile.total_seconds
    assert profile.session_count == 1
    assert profile.last_seen_at == LATER.isoformat()


@pytest.mark.parametrize(
    ("elapsed", "idle_elapsed", "afk_elapsed", "message"),
    [
        (-1, 0, 0, "Elapsed time must be a non-negative number."),
        (10, -1, 0, "Idle time must be a non-negative number."),
        (10, 0, -1, "AFK time must be a non-negative number."),
        (True, 0, 0, "Elapsed time must be a non-negative number."),
        (float("nan"), 0, 0, "Elapsed time must be a non-negative number."),
    ],
)
def test_record_interval_rejects_invalid_seconds(tmp_path, elapsed, idle_elapsed, afk_elapsed, message):
    store = make_store(tmp_path)

    with pytest.raises(TrackerError, match=message):
        store.record_interval("uid-1", "Alice", elapsed=elapsed, idle_elapsed=idle_elapsed, afk_elapsed=afk_elapsed)

    assert store.get("uid-1") is None


def test_profile_files_are_hashed_and_reload_after_restart(tmp_path):
    data_dir = tmp_path / "time_tracker"
    store = TimeTrackerStore(data_dir, logger=FakeLogger())
    uid = "server/viewer+one=two/../three"

    store.record_interval(uid, "Odd User", elapsed=12.345, idle_elapsed=2.0, afk_elapsed=1.0, new_session=True, now=NOW)
    store.record_interval("uid-2", "Second", elapsed=5, now=NOW)

    files = sorted(path.name for path in (data_dir / "profiles").glob("*.json"))
    assert files == sorted(
        [
            f"{hashlib.sha256(uid.encode('utf-8')).hexdigest()}.json",
            f"{hashlib.sha256(b'uid-2').hexdigest()}.json",
        ]
    )
    data = json.loads(profile_path(data_dir, uid).read_text())
    assert data["uid"] == uid
    assert data["schema_version"] == 1
    assert data["total_seconds"] == 12.35

    restarted = TimeTrackerStore(data_dir, logger=FakeLogger())

    loaded = restarted.get(uid)
    assert loaded is not None
    assert loaded.total_seconds == 12.35
    assert loaded.idle_seconds == 2.0
    assert loaded.afk_seconds == 1.0
    assert loaded.session_count == 1
    assert loaded.created_at == NOW.isoformat()


def test_shared_store_returns_one_instance_per_resolved_directory(tmp_path):
    reset_stores()
    try:
        first = get_store(tmp_path / "time_tracker")
        second = get_store(tmp_path / "time_tracker")
        other = get_store(tmp_path / "other")

        assert first is second
        assert first is not other

        first.record_interval("uid-1", "Alice", elapsed=10, now=NOW)
        assert second.get("uid-1") is not None
        assert other.get("uid-1") is None
    finally:
        reset_stores()


def test_corrupt_profile_is_quarantined_without_losing_other_profiles(tmp_path):
    data_dir = tmp_path / "time_tracker"
    store = TimeTrackerStore(data_dir, logger=FakeLogger())
    store.record_interval("uid-good", "Good", elapsed=30, now=NOW)
    store.record_interval("uid-bad", "Bad", elapsed=30, now=NOW)
    bad_path = profile_path(data_dir, "uid-bad")
    bad_path.write_text("{not json")
    malformed_path = (data_dir / "profiles") / "malformed.json"
    malformed_path.write_text(json.dumps({"schema_version": 1, "uid": "uid-missing"}))

    restarted = TimeTrackerStore(data_dir, logger=FakeLogger())

    good = restarted.get("uid-good")
    assert good is not None
    assert good.total_seconds == 30
    assert restarted.get("uid-bad") is None
    quarantined = [path for path in (data_dir / "profiles").iterdir() if path.name.startswith(".corrupt-")]
    assert len(quarantined) == 1
    assert bad_path.stem in quarantined[0].name
    assert not bad_path.exists()
    assert malformed_path.exists()


def test_opt_out_halts_accumulation_and_hides_leaderboard(tmp_path):
    store = make_store(tmp_path)
    store.record_interval("uid-1", "Alice", elapsed=60, new_session=True, now=NOW)

    profile = store.set_do_not_track("uid-1", True, now=LATER)

    assert profile.do_not_track is True
    assert store.is_tracked("uid-1") is False
    result = store.record_interval("uid-1", "Alice", elapsed=60, now=LATER)
    assert result is None
    assert store.get("uid-1").total_seconds == 60
    assert store.leaderboard(10) == []
    assert store.rank("uid-1") is None

    assert store.toggle_do_not_track("uid-1", now=LATER) is False
    assert store.is_tracked("uid-1") is True
    assert store.leaderboard(10)[0].uid == "uid-1"


def test_session_metadata_and_disconnect_are_recorded(tmp_path):
    store = make_store(tmp_path)
    store.record_interval("uid-1", "Alice", elapsed=0, new_session=True, now=NOW)
    store.record_interval("uid-1", "Alice", elapsed=10, now=NOW)
    assert store.get("uid-1").session_count == 1

    disconnected = store.end_session("uid-1", now=LATER)

    assert disconnected is not None
    assert disconnected.last_disconnected_at == LATER.isoformat()

    store.record_interval("uid-1", "Alice", elapsed=0, new_session=True, now=LATER)
    assert store.get("uid-1").session_count == 2


def test_leaderboard_ordering_ties_limit_and_rank(tmp_path):
    store = make_store(tmp_path)
    store.record_interval("uid-alice", "Alice", elapsed=300, idle_elapsed=100, afk_elapsed=50, now=NOW)
    store.record_interval("uid-bob", "Bob", elapsed=300, idle_elapsed=200, afk_elapsed=10, now=NOW)
    store.record_interval("uid-carol", "Carol", elapsed=100, idle_elapsed=100, afk_elapsed=100, now=NOW)
    store.record_interval("uid-same-a", "Same", elapsed=50, idle_elapsed=50, now=NOW)
    store.record_interval("uid-same-b", "Same", elapsed=50, idle_elapsed=50, now=NOW)

    assert [profile.uid for profile in store.leaderboard(10)] == [
        "uid-alice",
        "uid-bob",
        "uid-carol",
        "uid-same-a",
        "uid-same-b",
    ]
    assert [profile.uid for profile in store.leaderboard(10, metric="idle")] == [
        "uid-bob",
        "uid-alice",
        "uid-carol",
        "uid-same-a",
        "uid-same-b",
    ]
    assert [profile.uid for profile in store.leaderboard(10, metric="afk")] == [
        "uid-carol",
        "uid-alice",
        "uid-bob",
    ]
    assert [profile.uid for profile in store.leaderboard(2)] == ["uid-alice", "uid-bob"]
    assert store.leaderboard(0) == []
    assert store.rank("uid-alice") == 1
    assert store.rank("uid-carol") == 3
    assert store.rank("uid-same-b") == 5
    assert store.rank("uid-missing") is None


def test_invalid_metric_and_limit_are_rejected(tmp_path):
    store = make_store(tmp_path)

    with pytest.raises(TrackerError, match="Unknown metric: steps."):
        store.leaderboard(10, metric="steps")
    with pytest.raises(TrackerError, match="Limit must be a non-negative integer."):
        store.leaderboard(-1)
    with pytest.raises(TrackerError, match="Limit must be a non-negative integer."):
        store.leaderboard(True)


def test_profile_names_and_optional_metadata_survive_restart(tmp_path):
    data_dir = tmp_path / "time_tracker"
    store = TimeTrackerStore(data_dir, logger=FakeLogger())
    store.record_interval("uid-1", "Alice", elapsed=10, new_session=True, now=NOW)
    store.end_session("uid-1", now=LATER)

    restarted = TimeTrackerStore(data_dir, logger=FakeLogger())
    profile = restarted.get("uid-1")

    assert profile is not None
    assert profile.name == "Alice"
    assert profile.last_connected_at == NOW.isoformat()
    assert profile.last_seen_at == NOW.isoformat()
    assert profile.last_disconnected_at == LATER.isoformat()


def test_format_duration():
    assert format_duration(0) == "0s"
    assert format_duration(59) == "59s"
    assert format_duration(60) == "1m"
    assert format_duration(3661) == "1h 1m 1s"
    assert format_duration(90061) == "1d 1h 1m 1s"
