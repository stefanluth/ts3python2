import hashlib
import json
import re
from datetime import datetime, timedelta, timezone

import pytest

from plugins.casino_store import CasinoError, CasinoStore
from tests.support.fakes import FakeLogger
from tests.support.paths import hashed_path

NOW = datetime(2026, 11, 12, 12, 0, tzinfo=timezone.utc)
LATER = NOW + timedelta(hours=1)


def make_store(tmp_path, **overrides):
    return CasinoStore(tmp_path, logger=FakeLogger(), **overrides)


def create_player(store, uid="uid-1", name="Alice", now=NOW):
    return store.get_or_create(uid, name, now=now)


def player_path(players_dir, uid):
    return hashed_path(players_dir, uid)


def test_creation_sets_starting_balance_and_ledger(tmp_path):
    store = make_store(tmp_path)

    player = create_player(store)

    assert player.uid == "uid-1"
    assert player.name == "Alice"
    assert player.balance == 500
    assert player.ledger_total == 500
    assert player.created_at == NOW.isoformat()
    assert player.last_daily_at is None
    assert player.games_played == 0
    assert player.blackjack is None
    assert player.transactions == [{"at": NOW.isoformat(), "reason": "starting_balance", "amount": 500, "balance": 500}]
    assert store.audit("uid-1") is True

    data = json.loads(player_path(tmp_path / "players", "uid-1").read_text())
    assert data["schema_version"] == 1
    assert data["uid"] == "uid-1"
    assert data["balance"] == 500
    assert data["transactions"][0]["reason"] == "starting_balance"


def test_name_update_persists_without_resetting_state(tmp_path):
    store = make_store(tmp_path)
    create_player(store)

    updated = store.get_or_create("uid-1", "Alice Cooper", now=LATER)

    assert updated.name == "Alice Cooper"
    assert updated.balance == 500
    assert updated.created_at == NOW.isoformat()
    data = json.loads(player_path(tmp_path / "players", "uid-1").read_text())
    assert data["name"] == "Alice Cooper"
    assert data["created_at"] == NOW.isoformat()
    assert data["balance"] == 500
    assert len(data["transactions"]) == 1
    assert len(list((tmp_path / "players").glob("*.json"))) == 1


def test_balance_and_audit_track_the_ledger(tmp_path):
    store = make_store(tmp_path)
    create_player(store)

    assert store.balance("uid-1") == 500
    store.settle_round("uid-1", game="roulette", wager=100, payout=250, now=NOW)

    player = store.get("uid-1")
    assert player is not None
    assert player.balance == 650
    assert player.ledger_total == 650
    assert store.balance("uid-1") == 650
    assert store.audit("uid-1") is True


def test_missing_player_lookups_are_empty(tmp_path):
    store = make_store(tmp_path)

    assert store.get("nobody") is None
    assert store.balance("nobody") == 0
    assert store.blackjack("nobody") is None
    assert store.rank("nobody") is None
    assert store.audit("nobody") is False
    with pytest.raises(CasinoError, match="Player not found."):
        store.claim_daily("nobody", now=NOW)
    with pytest.raises(CasinoError, match="Player not found."):
        store.settle_round("nobody", game="roulette", wager=10, payout=20, now=NOW)


def test_claim_daily_credits_reward_and_records_timestamp(tmp_path):
    store = make_store(tmp_path)
    create_player(store)

    reward = store.claim_daily("uid-1", now=NOW)

    assert reward == 100
    player = store.get("uid-1")
    assert player is not None
    assert player.balance == 600
    assert player.ledger_total == 600
    assert player.last_daily_at == NOW.isoformat()
    assert player.transactions[-1] == {
        "at": NOW.isoformat(),
        "reason": "daily",
        "amount": 100,
        "balance": 600,
    }
    assert store.audit("uid-1") is True


def test_claim_daily_cooldown_rejection_reports_remaining_time(tmp_path):
    store = make_store(tmp_path)
    create_player(store)
    store.claim_daily("uid-1", now=NOW)

    with pytest.raises(CasinoError, match=r"Try again in 23h\."):
        store.claim_daily("uid-1", now=NOW + timedelta(hours=1))

    assert store.balance("uid-1") == 600
    assert store.get("uid-1").transactions[-1]["reason"] == "daily"


def test_claim_daily_allows_claim_after_cooldown(tmp_path):
    store = make_store(tmp_path)
    create_player(store)
    store.claim_daily("uid-1", now=NOW)

    reward = store.claim_daily("uid-1", now=NOW + timedelta(seconds=86400))

    assert reward == 100
    assert store.balance("uid-1") == 700
    assert store.get("uid-1").last_daily_at == (NOW + timedelta(seconds=86400)).isoformat()
    assert store.audit("uid-1") is True


def test_settle_round_win_loss_push_updates_stats(tmp_path):
    store = make_store(tmp_path)
    create_player(store)

    won = store.settle_round("uid-1", game="roulette", wager=100, payout=250, now=NOW)
    assert won.balance == 650
    assert (won.games_played, won.wins, won.losses, won.pushes) == (1, 1, 0, 0)
    assert won.total_wagered == 100
    assert won.total_won == 250
    assert won.biggest_win == 150
    assert [entry["reason"] for entry in won.transactions[-2:]] == ["roulette wager", "roulette payout"]
    assert [entry["amount"] for entry in won.transactions[-2:]] == [-100, 250]

    lost = store.settle_round("uid-1", game="slots", wager=50, payout=0, now=NOW)
    assert lost.balance == 600
    assert (lost.games_played, lost.wins, lost.losses, lost.pushes) == (2, 1, 1, 0)
    assert lost.total_wagered == 150
    assert lost.total_won == 250
    assert lost.biggest_win == 150

    pushed = store.settle_round("uid-1", game="blackjack", wager=50, payout=50, now=NOW)
    assert pushed.balance == 600
    assert (pushed.games_played, pushed.wins, pushed.losses, pushed.pushes) == (3, 1, 1, 1)
    assert pushed.total_wagered == 200
    assert pushed.total_won == 300
    assert pushed.biggest_win == 150
    assert store.audit("uid-1") is True


@pytest.mark.parametrize(
    ("wager", "payout", "message"),
    [
        (0, 100, "Wager must be a positive integer."),
        (-5, 100, "Wager must be a positive integer."),
        (100, -1, "Payout cannot be negative."),
        (501, 100, "Not enough balance."),
    ],
)
def test_settle_round_rejects_invalid_bets(tmp_path, wager, payout, message):
    store = make_store(tmp_path)
    create_player(store)

    with pytest.raises(CasinoError, match=re.escape(message)):
        store.settle_round("uid-1", game="roulette", wager=wager, payout=payout, now=NOW)

    player = store.get("uid-1")
    assert player is not None
    assert player.balance == 500
    assert player.games_played == 0
    assert len(player.transactions) == 1


def test_transaction_cap_keeps_ledger_total_correct(tmp_path):
    store = make_store(tmp_path, transaction_limit=3)
    create_player(store)

    for _ in range(5):
        store.settle_round("uid-1", game="roulette", wager=10, payout=20, now=NOW)

    player = store.get("uid-1")
    assert player is not None
    assert len(player.transactions) == 3
    assert player.balance == 550
    assert player.ledger_total == 550
    assert player.transactions[-1]["balance"] == 550
    assert player.transactions[-1]["reason"] == "roulette payout"
    assert store.audit("uid-1") is True


def test_leaderboard_order_ties_limit_and_rank(tmp_path):
    store = make_store(tmp_path)
    create_player(store, "uid-alice", "Alice")
    create_player(store, "uid-bob", "Bob")
    create_player(store, "uid-dave", "Dave")
    create_player(store, "uid-alpha", "alpha")
    create_player(store, "uid-beta", "Beta")
    create_player(store, "uid-carol", "Carol")
    create_player(store, "uid-same-a", "Same")
    create_player(store, "uid-same-b", "Same")
    store.settle_round("uid-alice", game="roulette", wager=100, payout=200, now=NOW)
    store.settle_round("uid-bob", game="roulette", wager=100, payout=200, now=NOW)
    store.claim_daily("uid-dave", now=NOW)
    store.settle_round("uid-carol", game="roulette", wager=100, payout=100, now=NOW)

    order = [player.uid for player in store.leaderboard(10)]

    assert order == [
        "uid-alice",
        "uid-bob",
        "uid-dave",
        "uid-alpha",
        "uid-beta",
        "uid-carol",
        "uid-same-a",
        "uid-same-b",
    ]
    assert [player.uid for player in store.leaderboard(3)] == ["uid-alice", "uid-bob", "uid-dave"]
    assert store.leaderboard(0) == []
    assert store.rank("uid-alice") == 1
    assert store.rank("uid-carol") == 6
    assert store.rank("uid-same-b") == 8
    assert store.rank("uid-missing") is None


def test_per_user_files_and_writing_one_does_not_rewrite_another(tmp_path):
    store = make_store(tmp_path)
    create_player(store, "uid-one", "One")
    create_player(store, "uid-two", "Two")
    players_dir = tmp_path / "players"

    assert len(list(players_dir.glob("*.json"))) == 2
    first = player_path(players_dir, "uid-one")
    second = player_path(players_dir, "uid-two")
    first_before = first.stat()
    first_bytes = first.read_bytes()
    second_before = second.stat()

    store.settle_round("uid-two", game="slots", wager=10, payout=20, now=NOW)

    first_after = first.stat()
    second_after = second.stat()
    assert first_after.st_ino == first_before.st_ino
    assert first_after.st_mtime_ns == first_before.st_mtime_ns
    assert first.read_bytes() == first_bytes
    assert second_after.st_ino != second_before.st_ino
    assert json.loads(second.read_text())["balance"] == 510


def test_safe_filename_for_uid_with_special_characters(tmp_path):
    store = make_store(tmp_path)
    uid = "server/viewer+one=two/../three"

    player = create_player(store, uid, "Odd User")

    players_dir = tmp_path / "players"
    files = list(players_dir.glob("*.json"))
    assert len(files) == 1
    name = files[0].name
    assert name == f"{hashlib.sha256(uid.encode('utf-8')).hexdigest()}.json"
    assert "/" not in name
    assert "+" not in name
    assert "=" not in name
    assert not any(path.is_dir() for path in players_dir.iterdir())

    restarted = make_store(tmp_path)
    loaded = restarted.get(uid)
    assert loaded is not None
    assert loaded.uid == uid
    assert loaded.balance == player.balance


def test_restart_loads_balances_and_stats(tmp_path):
    store = make_store(tmp_path)
    create_player(store)
    store.claim_daily("uid-1", now=NOW)
    store.settle_round("uid-1", game="roulette", wager=100, payout=300, now=LATER)
    created = store.get("uid-1")

    restarted = make_store(tmp_path)
    loaded = restarted.get("uid-1")

    assert created is not None
    assert loaded is not None
    assert loaded.balance == created.balance == 800
    assert loaded.ledger_total == 800
    assert loaded.created_at == NOW.isoformat()
    assert loaded.last_daily_at == NOW.isoformat()
    assert loaded.games_played == 1
    assert loaded.wins == 1
    assert loaded.total_wagered == 100
    assert loaded.total_won == 300
    assert loaded.biggest_win == 200
    assert loaded.transactions == created.transactions
    assert restarted.audit("uid-1") is True


def test_corrupt_file_is_quarantined_and_others_load(tmp_path):
    store = make_store(tmp_path)
    create_player(store, "uid-good", "Good")
    create_player(store, "uid-bad", "Bad")
    players_dir = tmp_path / "players"
    bad_path = player_path(players_dir, "uid-bad")
    bad_path.write_text("{not json")
    malformed_path = players_dir / "malformed.json"
    malformed_path.write_text(json.dumps({"schema_version": 1, "uid": "uid-missing"}))

    restarted = make_store(tmp_path)

    good = restarted.get("uid-good")
    assert good is not None
    assert good.balance == 500
    assert restarted.get("uid-bad") is None
    assert [player.uid for player in restarted.leaderboard(10)] == ["uid-good"]
    quarantined = [path for path in players_dir.iterdir() if path.name.startswith(".corrupt-")]
    assert len(quarantined) == 1
    assert bad_path.stem in quarantined[0].name
    assert not bad_path.exists()
    assert malformed_path.exists()

    again = make_store(tmp_path)
    assert again.get("uid-good") is not None
    assert len([path for path in players_dir.iterdir() if path.name.startswith(".corrupt-")]) == 1


def test_audit_detects_ledger_mismatch(tmp_path):
    store = make_store(tmp_path)
    create_player(store)
    path = player_path(tmp_path / "players", "uid-1")
    data = json.loads(path.read_text())
    data["ledger_total"] = 501
    path.write_text(json.dumps(data))

    restarted = make_store(tmp_path)

    player = restarted.get("uid-1")
    assert player is not None
    assert player.balance == 500
    assert restarted.audit("uid-1") is False


def test_blackjack_start_update_settle_and_clear_session(tmp_path):
    store = make_store(tmp_path)
    create_player(store)
    session = {"bet": 100, "player": ["A"], "dealer": ["K"]}

    started = store.start_blackjack("uid-1", session, now=NOW)

    assert started.balance == 400
    assert started.ledger_total == 400
    assert started.blackjack == session
    assert started.transactions[-1] == {
        "at": NOW.isoformat(),
        "reason": "blackjack wager",
        "amount": -100,
        "balance": 400,
    }
    data = json.loads(player_path(tmp_path / "players", "uid-1").read_text())
    assert data["blackjack"] == session

    updated_session = {"bet": 100, "player": ["A", "5"], "dealer": ["K", "9"]}
    updated = store.update_blackjack("uid-1", updated_session, extra_wager=50, now=LATER)

    assert updated.balance == 350
    assert updated.blackjack == updated_session

    settled = store.settle_blackjack("uid-1", wager=150, payout=300, now=LATER)

    assert settled.balance == 650
    assert settled.blackjack is None
    assert (settled.games_played, settled.wins, settled.losses, settled.pushes) == (1, 1, 0, 0)
    assert settled.total_wagered == 150
    assert settled.total_won == 300
    assert settled.biggest_win == 150
    assert settled.ledger_total == 650
    assert store.blackjack("uid-1") is None
    assert store.audit("uid-1") is True
    data = json.loads(player_path(tmp_path / "players", "uid-1").read_text())
    assert data["blackjack"] is None


def test_settle_blackjack_with_extra_wager_uses_total_wager(tmp_path):
    store = make_store(tmp_path)
    create_player(store)
    store.start_blackjack("uid-1", {"bet": 100}, now=NOW)

    settled = store.settle_blackjack("uid-1", wager=200, payout=0, extra_wager=100, now=LATER)

    assert settled.balance == 300
    assert (settled.games_played, settled.wins, settled.losses, settled.pushes) == (1, 0, 1, 0)
    assert settled.total_wagered == 200
    assert settled.total_won == 0
    assert settled.biggest_win == 0
    assert settled.blackjack is None
    assert [entry["reason"] for entry in settled.transactions[-2:]] == [
        "blackjack double",
        "blackjack payout",
    ]
    assert store.audit("uid-1") is True


def test_blackjack_rejects_active_and_missing_sessions(tmp_path):
    store = make_store(tmp_path)
    create_player(store)

    with pytest.raises(CasinoError, match="No active blackjack hand."):
        store.update_blackjack("uid-1", {"bet": 10}, now=NOW)
    with pytest.raises(CasinoError, match="No active blackjack hand."):
        store.settle_blackjack("uid-1", wager=10, payout=20, now=NOW)

    store.start_blackjack("uid-1", {"bet": 10}, now=NOW)

    with pytest.raises(CasinoError, match="You already have an active blackjack hand."):
        store.start_blackjack("uid-1", {"bet": 10}, now=NOW)
    assert store.balance("uid-1") == 490
    assert store.blackjack("uid-1") == {"bet": 10}


def test_blackjack_rejects_insufficient_balance(tmp_path):
    store = make_store(tmp_path)
    create_player(store)

    with pytest.raises(CasinoError, match="Not enough balance."):
        store.start_blackjack("uid-1", {"bet": 501}, now=NOW)

    assert store.balance("uid-1") == 500
    assert store.blackjack("uid-1") is None

    store.start_blackjack("uid-1", {"bet": 400}, now=NOW)

    with pytest.raises(CasinoError, match="Not enough balance."):
        store.update_blackjack("uid-1", {"bet": 400}, extra_wager=101, now=NOW)
    with pytest.raises(CasinoError, match="Not enough balance."):
        store.settle_blackjack("uid-1", wager=400, payout=800, extra_wager=101, now=NOW)

    assert store.balance("uid-1") == 100
    assert store.blackjack("uid-1") == {"bet": 400}


def test_restart_resumes_active_blackjack_session(tmp_path):
    store = make_store(tmp_path)
    create_player(store)
    session = {"bet": 150, "player": [10, 7], "dealer": [9]}
    store.start_blackjack("uid-1", session, now=NOW)

    restarted = make_store(tmp_path)

    assert restarted.balance("uid-1") == 350
    assert restarted.blackjack("uid-1") == session

    restarted.settle_blackjack("uid-1", wager=150, payout=300, now=LATER)

    assert restarted.balance("uid-1") == 650
    assert restarted.audit("uid-1") is True
    assert make_store(tmp_path).blackjack("uid-1") is None
