import hashlib
import json
from datetime import datetime, timedelta, timezone

import pytest

import plugins.poll_store as poll_store_module
from plugins.poll_store import CODE_ALPHABET, PollError, PollStore
from tests.support.fakes import FakeLogger

NOW = datetime(2026, 11, 12, 12, 0, tzinfo=timezone.utc)
LATER = NOW + timedelta(hours=1)


def make_store(polls_dir=None):
    return PollStore(polls_dir, logger=FakeLogger())


def create_poll(store, **overrides):
    values = {
        "question": "Best fruit?",
        "options": ["Apple", "Pear"],
        "creator_uid": "creator-uid",
        "creator_name": "Creator",
        "scope": "server",
        "now": NOW,
    }
    values.update(overrides)
    return store.create(**values)


def test_create_generates_short_code_and_get_is_case_insensitive(tmp_path):
    store = make_store(tmp_path)

    poll = create_poll(store)

    assert len(poll.id) == 3
    assert set(poll.id) <= set(CODE_ALPHABET)
    assert store.get(poll.id) is poll
    assert store.get(poll.id.upper()) is poll


def test_create_writes_poll_file_with_results(tmp_path):
    store = make_store(tmp_path)

    poll = create_poll(store, question="  Best fruit?  ", options=[" Apple ", "Pear"])

    data = json.loads((tmp_path / f"{poll.id}.json").read_text())
    assert data["schema_version"] == 1
    assert data["question"] == "Best fruit?"
    assert data["options"] == ["Apple", "Pear"]
    assert data["creator"] == {"uid": "creator-uid", "name": "Creator"}
    assert data["results"] == {
        "counts": [0, 0],
        "percentages": [0.0, 0.0],
        "total_voters": 0,
        "total_selections": 0,
        "winner": [],
    }


def test_collision_retry_produces_a_unique_id(tmp_path, monkeypatch):
    store = make_store(tmp_path)
    first = create_poll(store)
    candidate = "zzz" if first.id != "zzz" else "yyy"
    choices = iter([*first.id, *candidate])
    monkeypatch.setattr(poll_store_module.random, "choice", lambda alphabet: next(choices))

    second = create_poll(store)

    assert second.id == candidate
    assert second.id != first.id


def test_in_memory_store_writes_nothing(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    store = make_store()

    poll = create_poll(store)

    assert poll.id
    assert list(tmp_path.iterdir()) == []


def test_load_round_trip_restores_poll(tmp_path):
    store = make_store(tmp_path)
    poll = create_poll(store, expires_at=NOW + timedelta(days=1))
    store.vote(poll.id, "uid-1", [1], voter_name="Alice", now=NOW)
    store.close(poll.id, now=LATER)

    loaded = make_store(tmp_path)
    restored = loaded.get(poll.id)

    assert restored is not None
    assert restored.question == poll.question
    assert restored.options == poll.options
    assert restored.creator_uid == poll.creator_uid
    assert restored.creator_name == poll.creator_name
    assert restored.created_at == poll.created_at
    assert restored.expires_at == poll.expires_at
    assert restored.closed_at == poll.closed_at
    assert restored.closed is True
    assert restored.votes == {"uid-1": [1]}
    assert restored.voter_names == {"uid-1": "Alice"}
    assert restored.counts() == [0, 1]
    assert restored.percentages() == [0.0, 100.0]
    assert restored.winners() == [1]


def test_load_skips_corrupt_files_and_keeps_others(tmp_path):
    store = make_store(tmp_path)
    poll = create_poll(store)
    (tmp_path / "broken.json").write_text("{not json")
    (tmp_path / "mismatch.json").write_text(json.dumps({"id": "different"}))

    loaded = make_store(tmp_path)

    assert loaded.get(poll.id) is not None
    assert len(loaded.list_polls()) == 1


def test_atomic_save_leaves_no_temporary_file(tmp_path):
    store = make_store(tmp_path)

    poll = create_poll(store)

    assert (tmp_path / f"{poll.id}.json").exists()
    assert list(tmp_path.glob("*.tmp")) == []


def test_delete_removes_poll_and_file(tmp_path):
    store = make_store(tmp_path)
    poll = create_poll(store)
    path = tmp_path / f"{poll.id}.json"

    assert store.delete(poll.id.upper()) is True
    assert not path.exists()
    assert store.get(poll.id) is None
    assert store.delete(poll.id) is False


def test_vote_rejects_missing_poll(tmp_path):
    store = make_store(tmp_path)

    with pytest.raises(PollError, match="Poll not found."):
        store.vote("abc", "uid-1", [0], now=NOW)


def test_vote_rejects_closed_poll(tmp_path):
    store = make_store(tmp_path)
    poll = create_poll(store)
    store.close(poll.id, now=NOW)

    with pytest.raises(PollError, match="Poll has ended."):
        store.vote(poll.id, "uid-1", [0], now=LATER)


def test_vote_closes_expired_poll_before_rejecting(tmp_path):
    store = make_store(tmp_path)
    poll = create_poll(store, expires_at=NOW)

    with pytest.raises(PollError, match="Poll has ended."):
        store.vote(poll.id, "uid-1", [0], now=NOW + timedelta(seconds=1))

    assert poll.closed is True
    data = json.loads((tmp_path / f"{poll.id}.json").read_text())
    assert data["closed"] is True


@pytest.mark.parametrize(
    "indices", [[], [2], [-1], [0, 0], [0, 1]], ids=["empty", "out-of-range", "negative", "dupe", "many"]
)
def test_vote_rejects_invalid_single_choice_indices(tmp_path, indices):
    store = make_store(tmp_path)
    poll = create_poll(store)

    with pytest.raises(PollError):
        store.vote(poll.id, "uid-1", indices, now=NOW)

    assert poll.votes == {}


def test_multi_choice_allows_multiple_options(tmp_path):
    store = make_store(tmp_path)
    poll = create_poll(store, multi_choice=True)

    store.vote(poll.id, "uid-1", [1, 0], now=NOW)

    assert poll.votes == {"uid-1": [0, 1]}
    assert poll.total_selections() == 2
    with pytest.raises(PollError):
        store.vote(poll.id, "uid-1", [0, 0], now=NOW)


def test_second_vote_replaces_the_first(tmp_path):
    store = make_store(tmp_path)
    poll = create_poll(store)
    store.vote(poll.id, "uid-1", [0], voter_name="Alice", now=NOW)

    store.vote(poll.id, "uid-1", [1], voter_name="Alice", now=NOW)

    assert poll.votes == {"uid-1": [1]}
    assert poll.counts() == [0, 1]
    assert poll.total_voters() == 1
    assert poll.total_selections() == 1


def test_anonymous_votes_store_only_hashed_keys(tmp_path):
    store = make_store(tmp_path)
    poll = create_poll(store, anonymous=True)
    uid = "raw-voter-uid"
    name = "Raw Voter Name"

    store.vote(poll.id, uid, [1], voter_name=name, now=NOW)

    path = tmp_path / f"{poll.id}.json"
    text = path.read_text()
    assert uid not in text
    assert name not in text
    data = json.loads(text)
    expected = hashlib.sha256(f"{uid}:{poll.id}".encode()).hexdigest()
    assert list(data["votes"]) == [expected]
    assert data["voter_names"] == {}
    assert poll.voter_names == {}
    assert all(len(key) == 64 and set(key) <= set("0123456789abcdef") for key in data["votes"])

    other = create_poll(store, anonymous=True, now=LATER)
    store.vote(other.id, uid, [0], now=LATER)
    assert store.voter_key(poll, uid) != store.voter_key(other, uid)


def test_anonymous_vote_dedupes_and_survives_reload(tmp_path):
    store = make_store(tmp_path)
    uid = "raw-voter-uid"
    poll = create_poll(store, anonymous=True)
    expected = hashlib.sha256(f"{uid}:{poll.id}".encode()).hexdigest()

    store.vote(poll.id, uid, [0], now=NOW)
    store.vote(poll.id, uid, [1], now=NOW)

    loaded = make_store(tmp_path)
    restored = loaded.get(poll.id)
    assert restored is not None
    assert restored.total_voters() == 1
    assert restored.votes == {expected: [1]}

    loaded.vote(restored.id, uid, [0], now=LATER)
    restored = loaded.get(poll.id)
    assert restored is not None
    assert restored.total_voters() == 1
    assert restored.counts() == [1, 0]


def test_load_drops_voter_names_from_anonymous_polls(tmp_path):
    store = make_store(tmp_path)
    poll = create_poll(store, anonymous=True)
    path = tmp_path / f"{poll.id}.json"
    data = json.loads(path.read_text())
    data["votes"] = {"raw-voter-uid": [0]}
    data["voter_names"] = {"raw-voter-uid": "Alice"}
    path.write_text(json.dumps(data))

    loaded = make_store(tmp_path)
    restored = loaded.get(poll.id)

    assert restored is not None
    assert restored.anonymous is True
    assert restored.voter_names == {}
    assert restored.votes == {"raw-voter-uid": [0]}

    loaded.save(restored)

    saved = json.loads(path.read_text())
    assert saved["voter_names"] == {}
    assert saved["votes"] == {"raw-voter-uid": [0]}


def test_public_vote_stores_voter_name(tmp_path):
    store = make_store(tmp_path)
    poll = create_poll(store)

    store.vote(poll.id, "uid-1", [0], voter_name="Alice", now=NOW)

    data = json.loads((tmp_path / f"{poll.id}.json").read_text())
    assert data["votes"] == {"uid-1": [0]}
    assert data["voter_names"] == {"uid-1": "Alice"}
    assert poll.voter_names == {"uid-1": "Alice"}


def test_close_sets_closed_at_and_winners(tmp_path):
    store = make_store(tmp_path)
    poll = create_poll(store, options=["Apple", "Pear", "Plum"])
    store.vote(poll.id, "a", [0], now=NOW)
    store.vote(poll.id, "b", [0], now=NOW)
    store.vote(poll.id, "c", [1], now=NOW)

    closed = store.close(poll.id, now=LATER)

    assert closed.closed is True
    assert closed.closed_at == LATER.isoformat()
    assert closed.winners() == [0]

    store.close(poll.id, now=LATER + timedelta(hours=1))
    assert closed.closed_at == LATER.isoformat()


def test_winners_includes_ties(tmp_path):
    store = make_store(tmp_path)
    poll = create_poll(store, options=["Apple", "Pear", "Plum"])
    store.vote(poll.id, "a", [0], now=NOW)
    store.vote(poll.id, "b", [1], now=NOW)
    store.vote(poll.id, "c", [2], now=NOW)

    assert poll.winners() == [0, 1, 2]


def test_close_expired_closes_due_polls_in_created_order(tmp_path):
    store = make_store(tmp_path)
    late = create_poll(store, now=NOW + timedelta(minutes=5), expires_at=NOW + timedelta(minutes=6))
    early = create_poll(store, now=NOW, expires_at=NOW + timedelta(minutes=1))
    active = create_poll(store, now=NOW + timedelta(minutes=2), expires_at=NOW + timedelta(days=1))

    closed = store.close_expired(NOW + timedelta(minutes=10))

    assert [poll.id for poll in closed] == [early.id, late.id]
    assert early.closed is True
    assert late.closed is True
    assert active.closed is False


def test_list_filters_and_orders_newest_first(tmp_path):
    store = make_store(tmp_path)
    server = create_poll(store, now=NOW, scope="server")
    channel_10 = create_poll(
        store,
        now=NOW + timedelta(seconds=1),
        scope="channel",
        channel_id=10,
        channel_name="Ten",
    )
    channel_20 = create_poll(
        store,
        now=NOW + timedelta(seconds=2),
        scope="channel",
        channel_id=20,
        channel_name="Twenty",
    )
    closed = create_poll(store, now=NOW + timedelta(seconds=3))
    store.close(closed.id, now=LATER)

    assert [poll.id for poll in store.list_polls()] == [channel_20.id, channel_10.id, server.id]
    assert {poll.id for poll in store.list_polls(scope="channel")} == {channel_10.id, channel_20.id}
    assert [poll.id for poll in store.list_polls(channel_id=10)] == [channel_10.id]
    assert {poll.id for poll in store.list_polls(include_closed=True)} == {
        server.id,
        channel_10.id,
        channel_20.id,
        closed.id,
    }


def test_closed_polls_are_never_auto_deleted(tmp_path):
    store = make_store(tmp_path)
    poll = create_poll(store, expires_at=NOW)

    store.close_expired(NOW + timedelta(seconds=1))

    path = tmp_path / f"{poll.id}.json"
    assert poll.closed is True
    assert path.exists()
    store.close_expired(NOW + timedelta(days=1))
    assert path.exists()
    assert store.get(poll.id) is not None
