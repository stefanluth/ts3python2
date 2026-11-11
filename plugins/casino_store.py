from __future__ import annotations

import hashlib
import json
import logging
import math
import os
import pathlib
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone

SCHEMA_VERSION = 1
PLAYERS_DIRNAME = "players"


class CasinoError(Exception):
    """A casino error that can be shown to the user."""


@dataclass
class Player:
    uid: str
    name: str
    balance: int = 0
    created_at: str = ""
    last_daily_at: str | None = None
    games_played: int = 0
    wins: int = 0
    losses: int = 0
    pushes: int = 0
    total_wagered: int = 0
    total_won: int = 0
    biggest_win: int = 0
    ledger_total: int = 0
    transactions: list[dict] = field(default_factory=list)
    blackjack: dict | None = None


class CasinoStore:
    def __init__(
        self,
        data_dir: str | pathlib.Path = "casino",
        *,
        starting_balance: int = 500,
        daily_reward: int = 100,
        daily_cooldown: int = 86400,
        transaction_limit: int = 500,
        logger: logging.Logger | None = None,
    ):
        self.data_dir = pathlib.Path(data_dir)
        self.players_dir = self.data_dir / PLAYERS_DIRNAME
        self.starting_balance = starting_balance
        self.daily_reward = daily_reward
        self.daily_cooldown = daily_cooldown
        self.transaction_limit = transaction_limit
        self.logger = logger
        self._players: dict[str, Player] = {}
        self.load()

    def load(self) -> None:
        self._players = {}
        if not self.players_dir.is_dir():
            return
        for path in sorted(self.players_dir.glob("*.json")):
            player = self._read_player(path)
            if player is not None:
                self._players[player.uid] = player

    def get_or_create(self, uid: str, name: str, now: datetime | None = None) -> Player:
        player = self._players.get(uid)
        if player is not None:
            if player.name != name:
                player.name = name
                self.save(player)
            return player
        created_at = _to_iso(now or utcnow())
        player = Player(
            uid=uid,
            name=name,
            balance=self.starting_balance,
            created_at=created_at,
            ledger_total=self.starting_balance,
            transactions=[
                {
                    "at": created_at,
                    "reason": "starting_balance",
                    "amount": self.starting_balance,
                    "balance": self.starting_balance,
                }
            ],
        )
        self._trim_transactions(player)
        self._players[uid] = player
        self.save(player)
        return player

    def get(self, uid: str) -> Player | None:
        return self._players.get(uid)

    def balance(self, uid: str) -> int:
        player = self._players.get(uid)
        return player.balance if player is not None else 0

    def claim_daily(self, uid: str, now: datetime | None = None) -> int:
        player = self._require(uid)
        current = _normalize_datetime(now or utcnow())
        if player.last_daily_at is not None:
            last = _parse_datetime(player.last_daily_at)
            if last is not None:
                elapsed = (current - last).total_seconds()
                if elapsed < self.daily_cooldown:
                    remaining = max(1, math.ceil(self.daily_cooldown - elapsed))
                    raise CasinoError(f"Daily reward is not ready yet. Try again in {_format_duration(remaining)}.")
        player.last_daily_at = _to_iso(current)
        self._record(player, "daily", self.daily_reward, current)
        self._trim_transactions(player)
        self.save(player)
        return self.daily_reward

    def leaderboard(self, limit: int) -> list[Player]:
        if limit <= 0:
            return []
        return self._sorted_players()[:limit]

    def rank(self, uid: str) -> int | None:
        if uid not in self._players:
            return None
        for index, player in enumerate(self._sorted_players(), start=1):
            if player.uid == uid:
                return index
        return None

    def settle_round(
        self,
        uid: str,
        *,
        game: str,
        wager: int,
        payout: int,
        now: datetime | None = None,
    ) -> Player:
        player = self._require(uid)
        _validate_positive(wager, "Wager")
        _validate_payout(payout)
        if wager > player.balance:
            raise CasinoError("Not enough balance.")
        current = _normalize_datetime(now or utcnow())
        self._record(player, f"{game} wager", -wager, current)
        self._record(player, f"{game} payout", payout, current)
        self._update_stats(player, wager, payout)
        self._trim_transactions(player)
        self.save(player)
        return player

    def start_blackjack(self, uid: str, session: dict, now: datetime | None = None) -> Player:
        player = self._require(uid)
        if player.blackjack is not None:
            raise CasinoError("You already have an active blackjack hand.")
        bet = _session_bet(session)
        if bet > player.balance:
            raise CasinoError("Not enough balance.")
        current = _normalize_datetime(now or utcnow())
        self._record(player, "blackjack wager", -bet, current)
        player.blackjack = dict(session)
        self._trim_transactions(player)
        self.save(player)
        return player

    def update_blackjack(
        self,
        uid: str,
        session: dict,
        *,
        extra_wager: int = 0,
        now: datetime | None = None,
    ) -> Player:
        player = self._require(uid)
        if player.blackjack is None:
            raise CasinoError("No active blackjack hand.")
        _validate_extra(extra_wager)
        if extra_wager > player.balance:
            raise CasinoError("Not enough balance.")
        current = _normalize_datetime(now or utcnow())
        if extra_wager > 0:
            self._record(player, "blackjack double", -extra_wager, current)
        player.blackjack = dict(session)
        self._trim_transactions(player)
        self.save(player)
        return player

    def settle_blackjack(
        self,
        uid: str,
        *,
        wager: int,
        payout: int,
        extra_wager: int = 0,
        now: datetime | None = None,
    ) -> Player:
        player = self._require(uid)
        if player.blackjack is None:
            raise CasinoError("No active blackjack hand.")
        _validate_positive(wager, "Wager")
        _validate_payout(payout)
        _validate_extra(extra_wager)
        if extra_wager > player.balance:
            raise CasinoError("Not enough balance.")
        current = _normalize_datetime(now or utcnow())
        if extra_wager > 0:
            self._record(player, "blackjack double", -extra_wager, current)
        self._record(player, "blackjack payout", payout, current)
        player.blackjack = None
        self._update_stats(player, wager, payout)
        self._trim_transactions(player)
        self.save(player)
        return player

    def blackjack(self, uid: str) -> dict | None:
        player = self._players.get(uid)
        return player.blackjack if player is not None else None

    def audit(self, uid: str) -> bool:
        player = self._players.get(uid)
        return player is not None and player.balance == player.ledger_total

    def save(self, player: Player) -> None:
        target = self._path_for(player.uid)
        temporary = target.with_name(f".{target.stem}.{os.getpid()}.tmp")
        try:
            self.players_dir.mkdir(parents=True, exist_ok=True)
            with temporary.open("w", encoding="utf-8") as handle:
                json.dump(_player_to_dict(player), handle, indent=2)
                handle.write("\n")
            os.replace(temporary, target)
        except OSError:
            self._get_logger().exception(f"Failed to save player file {target}.")
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass

    def _require(self, uid: str) -> Player:
        player = self._players.get(uid)
        if player is None:
            raise CasinoError("Player not found.")
        return player

    def _record(self, player: Player, reason: str, amount: int, at: datetime) -> None:
        player.balance += amount
        player.ledger_total += amount
        player.transactions.append(
            {
                "at": _to_iso(at),
                "reason": reason,
                "amount": amount,
                "balance": player.balance,
            }
        )

    def _update_stats(self, player: Player, wager: int, payout: int) -> None:
        player.games_played += 1
        if payout > wager:
            player.wins += 1
        elif payout < wager:
            player.losses += 1
        else:
            player.pushes += 1
        player.total_wagered += wager
        player.total_won += payout
        net = payout - wager
        if net > player.biggest_win:
            player.biggest_win = net

    def _trim_transactions(self, player: Player) -> None:
        limit = max(0, self.transaction_limit)
        if len(player.transactions) <= limit:
            return
        player.transactions = player.transactions[-limit:] if limit else []

    def _sorted_players(self) -> list[Player]:
        return sorted(
            self._players.values(),
            key=lambda player: (-player.balance, -player.wins, player.name.casefold(), player.uid),
        )

    def _path_for(self, uid: str) -> pathlib.Path:
        digest = hashlib.sha256(uid.encode("utf-8")).hexdigest()
        return self.players_dir / f"{digest}.json"

    def _read_player(self, path: pathlib.Path) -> Player | None:
        try:
            with path.open(encoding="utf-8") as handle:
                data = json.load(handle)
        except OSError, ValueError:
            self._quarantine(path)
            return None
        player = _player_from_dict(data, self.transaction_limit)
        if player is None:
            self._get_logger().warning(f"Skipping malformed player file {path}.")
        return player

    def _quarantine(self, path: pathlib.Path) -> None:
        target = self.players_dir / f".corrupt-{path.stem}-{time.time_ns()}.json"
        try:
            os.replace(path, target)
        except OSError:
            self._get_logger().exception(f"Failed to quarantine player file {path}.")
            return
        self._get_logger().warning(f"Quarantined corrupt player file {path} as {target}.")

    def _get_logger(self) -> logging.Logger:
        if self.logger is None:
            self.logger = logging.getLogger("plugins.casino_store")
        return self.logger


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _normalize_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _parse_datetime(value: str) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(value)
    except TypeError, ValueError:
        return None
    return _normalize_datetime(parsed)


def _to_iso(value: datetime) -> str:
    return _normalize_datetime(value).isoformat()


def _format_duration(seconds: int) -> str:
    seconds = max(0, int(seconds))
    days, remainder = divmod(seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, remaining = divmod(remainder, 60)
    parts: list[str] = []
    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    if remaining or not parts:
        parts.append(f"{remaining}s")
    return " ".join(parts)


def _validate_positive(value: int, label: str) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise CasinoError(f"{label} must be a positive integer.")


def _validate_payout(value: int) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise CasinoError("Payout cannot be negative.")


def _validate_extra(value: int) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise CasinoError("Extra wager cannot be negative.")


def _session_bet(session: dict) -> int:
    if not isinstance(session, dict):
        raise CasinoError("Invalid blackjack session.")
    for key in ("bet", "wager", "stake"):
        if key in session:
            value = session[key]
            _validate_positive(value, "Wager")
            return value
    raise CasinoError("Invalid blackjack session.")


def _integer(value: object, minimum: int | None = None) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError("not an integer")
    if minimum is not None and value < minimum:
        raise ValueError("integer below minimum")
    return value


def _timestamp(value: object) -> str:
    if not isinstance(value, str) or _parse_datetime(value) is None:
        raise ValueError("not a timestamp")
    return value


def _transactions(value: object) -> list[dict]:
    if not isinstance(value, list):
        raise ValueError("transactions is not a list")
    transactions: list[dict] = []
    for entry in value:
        if not isinstance(entry, dict):
            raise ValueError("transaction is not a dict")
        at = _timestamp(entry.get("at"))
        reason = entry.get("reason")
        if not isinstance(reason, str):
            raise ValueError("transaction reason is not a string")
        amount = _integer(entry.get("amount"))
        balance = _integer(entry.get("balance"), minimum=0)
        transactions.append({"at": at, "reason": reason, "amount": amount, "balance": balance})
    return transactions


def _player_from_dict(data: object, transaction_limit: int) -> Player | None:
    if not isinstance(data, dict):
        return None
    if data.get("schema_version") != SCHEMA_VERSION:
        return None
    try:
        uid = data.get("uid")
        if not isinstance(uid, str) or not uid:
            raise ValueError("invalid uid")
        name = data.get("name")
        if not isinstance(name, str):
            raise ValueError("invalid name")
        created_at = _timestamp(data.get("created_at"))
        last_daily_at = data.get("last_daily_at")
        if last_daily_at is not None:
            last_daily_at = _timestamp(last_daily_at)
        balance = _integer(data.get("balance"), minimum=0)
        ledger_total = _integer(data.get("ledger_total"), minimum=0)
        games_played = _integer(data.get("games_played"), minimum=0)
        wins = _integer(data.get("wins"), minimum=0)
        losses = _integer(data.get("losses"), minimum=0)
        pushes = _integer(data.get("pushes"), minimum=0)
        total_wagered = _integer(data.get("total_wagered"), minimum=0)
        total_won = _integer(data.get("total_won"), minimum=0)
        biggest_win = _integer(data.get("biggest_win"), minimum=0)
        transactions = _transactions(data.get("transactions"))
        blackjack = data.get("blackjack")
        if blackjack is not None and not isinstance(blackjack, dict):
            raise ValueError("invalid blackjack session")
    except TypeError, ValueError:
        return None
    limit = max(0, transaction_limit)
    if len(transactions) > limit:
        transactions = transactions[-limit:] if limit else []
    return Player(
        uid=uid,
        name=name,
        balance=balance,
        created_at=created_at,
        last_daily_at=last_daily_at,
        games_played=games_played,
        wins=wins,
        losses=losses,
        pushes=pushes,
        total_wagered=total_wagered,
        total_won=total_won,
        biggest_win=biggest_win,
        ledger_total=ledger_total,
        transactions=transactions,
        blackjack=blackjack,
    )


def _player_to_dict(player: Player) -> dict:
    return {
        "schema_version": SCHEMA_VERSION,
        "uid": player.uid,
        "name": player.name,
        "balance": player.balance,
        "created_at": player.created_at,
        "last_daily_at": player.last_daily_at,
        "games_played": player.games_played,
        "wins": player.wins,
        "losses": player.losses,
        "pushes": player.pushes,
        "total_wagered": player.total_wagered,
        "total_won": player.total_won,
        "biggest_win": player.biggest_win,
        "ledger_total": player.ledger_total,
        "transactions": [dict(entry) for entry in player.transactions],
        "blackjack": dict(player.blackjack) if player.blackjack is not None else None,
    }
