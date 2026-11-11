from __future__ import annotations

import random
from numbers import Real
from typing import Any

from ts3client import TS3Client
from ts3client.message import Message

from ..casino_games import (
    BlackjackSession,
    GameError,
    SlotsConfig,
    default_slots_config,
    double,
    hand_value,
    hit,
    parse_roulette_selection,
    spin_roulette,
    spin_slots,
    stand,
    start_blackjack,
)
from ..casino_store import CasinoError, CasinoStore
from ..command import Command
from ..errors import ConfigurationError

MESSAGE_LIMIT = 900
PLUGIN_NAME = "Casino"

ALIASES = {
    "help": "help",
    "?": "help",
    "balance": "balance",
    "bal": "balance",
    "daily": "daily",
    "profile": "profile",
    "leaderboard": "leaderboard",
    "lb": "leaderboard",
    "top": "leaderboard",
    "roulette": "roulette",
    "rl": "roulette",
    "slots": "slots",
    "slot": "slots",
    "blackjack": "blackjack",
    "bj": "blackjack",
    "hit": "hit",
    "h": "hit",
    "stand": "stand",
    "s": "stand",
    "double": "double",
    "d": "double",
}

OUTCOME_LABELS = {
    "blackjack": "blackjack",
    "win": "win",
    "push": "push",
    "loss": "loss",
    "bust": "bust",
}


class Casino(Command):
    def __init__(
        self,
        client: TS3Client,
        trigger: str,
        data_dir: str = "casino",
        currency_name: str = "chips",
        currency_symbol: str = "",
        starting_balance: int = 500,
        daily_reward: int = 100,
        daily_cooldown: int = 86400,
        min_bet: int = 1,
        max_bet: int = 10000,
        leaderboard_size: int = 10,
        blackjack_payout: float = 1.5,
        blackjack_decks: int = 1,
        dealer_hits_soft_17: bool = False,
        slots_symbols: list[str] | tuple[str, ...] | None = None,
        slots_weights: list[int] | tuple[int, ...] | None = None,
        slots_payouts: dict[str, int] | None = None,
        slots_two_cherry_payout: int = 2,
        description: str | None = None,
        rng: random.Random | None = None,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__(client, trigger)
        self.data_dir = data_dir
        self.currency_name = currency_name
        self.currency_symbol = currency_symbol
        self.starting_balance = starting_balance
        self.daily_reward = daily_reward
        self.daily_cooldown = daily_cooldown
        self.min_bet = min_bet
        self.max_bet = max_bet
        self.leaderboard_size = leaderboard_size
        self.blackjack_payout = blackjack_payout
        self.blackjack_decks = blackjack_decks
        self.dealer_hits_soft_17 = dealer_hits_soft_17
        self.slots_two_cherry_payout = slots_two_cherry_payout
        self.description = description
        self.rng = rng if rng is not None else random.SystemRandom()
        self.prefix = "!"
        self.store = CasinoStore(
            data_dir,
            starting_balance=starting_balance,
            daily_reward=daily_reward,
            daily_cooldown=daily_cooldown,
            logger=self.logger,
        )
        self.slots_config = self._build_slots_config(
            slots_symbols,
            slots_weights,
            slots_payouts,
            slots_two_cherry_payout,
        )
        self._validate_config()

    def run(self, message: Message) -> None:
        try:
            prefix = self._derive_prefix(message)
            uid = self._invoker_uid(message)
            self.store.get_or_create(uid, message.invokername)
            self._dispatch(message, uid, prefix)
        except (CasinoError, GameError) as error:
            self._reply(message, str(error))
        except Exception:
            self.logger.exception("Casino command failed.")
            self._reply(message, "Casino command failed.")

    def tick(self) -> None:
        pass

    def stop(self) -> None:
        pass

    def _dispatch(self, message: Message, uid: str, prefix: str) -> None:
        parts = message.content.split(None, 1)
        args = parts[1] if len(parts) > 1 else ""
        tokens = args.split()
        if not tokens:
            self._help(message, prefix)
            return
        subcommand = ALIASES.get(tokens[0].lower())
        if subcommand is None:
            self._help(message, prefix)
            return
        arguments = tokens[1:]
        if subcommand == "help":
            self._help(message, prefix)
        elif subcommand == "balance":
            self._balance(message, uid)
        elif subcommand == "daily":
            self._daily(message, uid)
        elif subcommand == "profile":
            self._profile(message, uid)
        elif subcommand == "leaderboard":
            self._leaderboard(message, arguments)
        elif subcommand == "roulette":
            self._roulette(message, uid, arguments, prefix)
        elif subcommand == "slots":
            self._slots(message, uid, arguments, prefix)
        elif subcommand == "blackjack":
            self._blackjack(message, uid, arguments, prefix)
        elif subcommand == "hit":
            self._hit(message, uid, prefix)
        elif subcommand == "stand":
            self._stand(message, uid)
        elif subcommand == "double":
            self._double(message, uid)
        else:
            self._help(message, prefix)

    def _derive_prefix(self, message: Message) -> str:
        content = message.content.strip()
        head = content.split(None, 1)[0] if content else ""
        if self.trigger and head.endswith(self.trigger):
            return head[: -len(self.trigger)]
        return self.prefix

    def _help(self, message: Message, prefix: str) -> None:
        usage = f"{prefix}{self.trigger}"
        lines = [
            "Casino commands:",
            f"  {usage} help - show this help",
            f"  {usage} balance - show your balance",
            f"  {usage} daily - claim your daily reward",
            f"  {usage} profile - show your stats",
            f"  {usage} leaderboard [count] - show the top players",
            f"  {usage} roulette <bet> <selection> - spin the roulette wheel",
            f"  {usage} slots <bet> - spin the slots",
            f"  {usage} blackjack [bet] - start or show a blackjack hand",
            f"  {usage} hit|stand|double - play your blackjack hand",
            "Aliases: ?, bal, lb, top, rl, slot, bj, h, s, d",
        ]
        self._reply(message, "\n".join(lines))

    def _balance(self, message: Message, uid: str) -> None:
        player = self._player(uid)
        self._reply(message, f"Balance: {self._money(player.balance)}")

    def _daily(self, message: Message, uid: str) -> None:
        reward = self.store.claim_daily(uid)
        player = self._player(uid)
        self._reply(
            message,
            f"Daily reward: {self._money(reward)}\nBalance: {self._money(player.balance)}",
        )

    def _profile(self, message: Message, uid: str) -> None:
        player = self._player(uid)
        rank = self.store.rank(uid)
        rank_text = str(rank) if rank is not None else "unranked"
        lines = [
            f"Profile: {player.name}",
            f"Balance: {self._money(player.balance)}",
            f"Rank: {rank_text}",
            f"Games: {player.games_played}",
            f"Wins: {player.wins}",
            f"Losses: {player.losses}",
            f"Pushes: {player.pushes}",
            f"Total wagered: {self._money(player.total_wagered)}",
            f"Biggest win: {self._money(player.biggest_win)}",
        ]
        self._reply(message, "\n".join(lines))

    def _leaderboard(self, message: Message, tokens: list[str]) -> None:
        size = self.leaderboard_size
        if tokens:
            raw = tokens[0]
            if not raw.isdigit() or int(raw) <= 0:
                raise CasinoError("Leaderboard count must be a positive integer.")
            size = min(int(raw), self.leaderboard_size)
        players = self.store.leaderboard(size)
        if not players:
            self._reply(message, "No players yet.")
            return
        lines = ["Leaderboard:"]
        for index, player in enumerate(players, start=1):
            lines.append(f"{index}. {player.name} - {self._money(player.balance)}")
        self._reply(message, "\n".join(lines))

    def _roulette(self, message: Message, uid: str, tokens: list[str], prefix: str) -> None:
        if len(tokens) < 2:
            raise CasinoError(f"Use: {prefix}{self.trigger} roulette <bet> <selection>.")
        player = self._player(uid)
        bet = self._parse_bet(tokens[0], player)
        selection = parse_roulette_selection(" ".join(tokens[1:]))
        result = spin_roulette(bet, selection, rng=self.rng)
        player = self.store.settle_round(uid, game="roulette", wager=bet, payout=result.payout)
        net = result.payout - bet
        outcome = "win" if result.won else "loss"
        lines = [
            f"Roulette: {result.number} {result.color}",
            f"Bet: {self._money(bet)} on {result.label}",
            f"Result: {outcome}",
            f"Net: {self._signed_money(net)}",
            f"Balance: {self._money(player.balance)}",
        ]
        self._reply(message, "\n".join(lines))

    def _slots(self, message: Message, uid: str, tokens: list[str], prefix: str) -> None:
        if not tokens:
            raise CasinoError(f"Use: {prefix}{self.trigger} slots <bet>.")
        player = self._player(uid)
        bet = self._parse_bet(tokens[0], player)
        result = spin_slots(bet, self.slots_config, rng=self.rng)
        player = self.store.settle_round(uid, game="slots", wager=bet, payout=result.payout)
        net = result.payout - bet
        outcome = "win" if result.payout > 0 else "loss"
        lines = [
            f"Slots: {result.label}",
            f"Result: {outcome} (x{result.multiplier})",
            f"Net: {self._signed_money(net)}",
            f"Balance: {self._money(player.balance)}",
        ]
        self._reply(message, "\n".join(lines))

    def _blackjack(self, message: Message, uid: str, tokens: list[str], prefix: str) -> None:
        active = self.store.blackjack(uid)
        if not tokens:
            if active is None:
                self._blackjack_usage(message, prefix)
                return
            session = BlackjackSession.from_dict(active)
            self._reply(message, self._format_blackjack_active(session, self._player(uid), prefix))
            return
        if active is not None:
            raise CasinoError("Finish your current hand with hit, stand, or double.")
        player = self._player(uid)
        bet = self._parse_bet(tokens[0], player)
        session = start_blackjack(
            bet,
            decks=self.blackjack_decks,
            dealer_hits_soft_17=self.dealer_hits_soft_17,
            blackjack_payout=self.blackjack_payout,
            rng=self.rng,
        )
        if session.done:
            player = self.store.settle_round(uid, game="blackjack", wager=bet, payout=session.payout)
            self._reply(message, self._format_blackjack_result(session, player))
            return
        player = self.store.start_blackjack(uid, session.to_dict())
        self._reply(message, self._format_blackjack_active(session, player, prefix))

    def _hit(self, message: Message, uid: str, prefix: str) -> None:
        session = self._load_blackjack(uid)
        hit(session, self.dealer_hits_soft_17)
        if session.done:
            player = self.store.settle_blackjack(uid, wager=session.bet, payout=session.payout)
            self._reply(message, self._format_blackjack_result(session, player))
            return
        player = self.store.update_blackjack(uid, session.to_dict())
        self._reply(message, self._format_blackjack_active(session, player, prefix))

    def _stand(self, message: Message, uid: str) -> None:
        session = self._load_blackjack(uid)
        stand(session, self.dealer_hits_soft_17, self.blackjack_payout)
        player = self.store.settle_blackjack(uid, wager=session.bet, payout=session.payout)
        self._reply(message, self._format_blackjack_result(session, player))

    def _double(self, message: Message, uid: str) -> None:
        session = self._load_blackjack(uid)
        player = self._player(uid)
        if player.balance < session.bet:
            raise CasinoError("Not enough balance to double.")
        double(session, self.dealer_hits_soft_17, self.blackjack_payout)
        player = self.store.settle_blackjack(
            uid,
            wager=session.bet,
            payout=session.payout,
            extra_wager=session.bet // 2,
        )
        self._reply(message, self._format_blackjack_result(session, player))

    def _load_blackjack(self, uid: str) -> BlackjackSession:
        data = self.store.blackjack(uid)
        if data is None:
            raise CasinoError("No active blackjack hand.")
        return BlackjackSession.from_dict(data)

    def _blackjack_usage(self, message: Message, prefix: str) -> None:
        self._reply(message, f"Use: {prefix}{self.trigger} blackjack <bet>.")

    def _format_blackjack_active(self, session: BlackjackSession, player: Any, prefix: str) -> str:
        usage = f"{prefix}{self.trigger}"
        player_total, _ = hand_value(session.player)
        lines = [
            "Blackjack:",
            f"Your hand: {' '.join(session.player)} ({player_total})",
            f"Dealer shows: {session.dealer[0]}",
            f"Bet: {self._money(session.bet)}",
            f"Balance: {self._money(player.balance)}",
            f"Use {usage} hit, {usage} stand, or {usage} double.",
        ]
        return "\n".join(lines)

    def _format_blackjack_result(self, session: BlackjackSession, player: Any) -> str:
        player_total, _ = hand_value(session.player)
        dealer_total, _ = hand_value(session.dealer)
        outcome = OUTCOME_LABELS.get(session.outcome or "", "finished")
        net = session.payout - session.bet
        lines = [
            "Blackjack result:",
            f"Your hand: {' '.join(session.player)} ({player_total})",
            f"Dealer hand: {' '.join(session.dealer)} ({dealer_total})",
            f"Result: {outcome}",
            f"Payout: {self._money(session.payout)}",
            f"Net: {self._signed_money(net)}",
            f"Balance: {self._money(player.balance)}",
        ]
        return "\n".join(lines)

    def _parse_bet(self, token: str, player: Any) -> int:
        if not token.isdigit():
            raise CasinoError("Bet must be a positive integer.")
        bet = int(token)
        if bet < self.min_bet or bet > self.max_bet:
            raise CasinoError(f"Bet must be between {self.min_bet} and {self.max_bet}.")
        if bet > player.balance:
            raise CasinoError("Not enough balance.")
        return bet

    def _player(self, uid: str) -> Any:
        player = self.store.get(uid)
        if player is None:
            raise CasinoError("Player not found.")
        return player

    def _invoker_uid(self, message: Message) -> str:
        uid = getattr(message, "invokeruid", None)
        if uid:
            return uid
        try:
            info = self.client.get_user_info(message.invokerid)
            if info.client_unique_identifier:
                return info.client_unique_identifier
        except Exception:
            self.logger.exception("Failed to resolve invoker uid.")
        return f"clid:{message.invokerid}"

    def _money(self, amount: int) -> str:
        if self.currency_symbol:
            return f"{self.currency_symbol}{amount:,}"
        return f"{amount:,} {self.currency_name}"

    def _signed_money(self, amount: int) -> str:
        if amount > 0:
            return f"+{self._money(amount)}"
        return self._money(amount)

    def _reply(self, message: Message, text: str) -> None:
        try:
            self.client.send_private_message(message.invokerid, self._truncate(text))
        except Exception:
            self.logger.exception("Failed to send casino reply.")

    def _truncate(self, text: str) -> str:
        if len(text) <= MESSAGE_LIMIT:
            return text
        return f"{text[: MESSAGE_LIMIT - 3]}..."

    def _validate_config(self) -> None:
        _require_int(self.min_bet, "Minimum bet", minimum=1)
        _require_int(self.max_bet, "Maximum bet", minimum=self.min_bet)
        _require_int(self.starting_balance, "Starting balance", minimum=0)
        _require_int(self.daily_reward, "Daily reward", minimum=0)
        _require_int(self.daily_cooldown, "Daily cooldown", minimum=0)
        _require_int(self.leaderboard_size, "Leaderboard size", minimum=1)
        _require_int(self.blackjack_decks, "Blackjack decks", minimum=1)
        if isinstance(self.blackjack_payout, bool) or not isinstance(self.blackjack_payout, Real):
            raise ConfigurationError(PLUGIN_NAME, "Blackjack payout must be a positive number.")
        if self.blackjack_payout <= 0:
            raise ConfigurationError(PLUGIN_NAME, "Blackjack payout must be a positive number.")
        if not isinstance(self.dealer_hits_soft_17, bool):
            raise ConfigurationError(PLUGIN_NAME, "Dealer hits soft 17 must be a boolean.")

    def _build_slots_config(
        self,
        slots_symbols: list[str] | tuple[str, ...] | None,
        slots_weights: list[int] | tuple[int, ...] | None,
        slots_payouts: dict[str, int] | None,
        two_cherry_payout: int,
    ) -> SlotsConfig:
        defaults = default_slots_config()
        if slots_symbols is None:
            symbols = defaults.symbols
        else:
            if not isinstance(slots_symbols, (list, tuple)):
                raise ConfigurationError(PLUGIN_NAME, "Slots symbols must be a list or tuple.")
            symbols = tuple(slots_symbols)
        if slots_weights is None:
            weights = defaults.weights
        else:
            if not isinstance(slots_weights, (list, tuple)):
                raise ConfigurationError(PLUGIN_NAME, "Slots weights must be a list or tuple.")
            weights = tuple(slots_weights)
        if slots_payouts is None:
            payouts = dict(defaults.triple_payouts)
        else:
            if not isinstance(slots_payouts, dict):
                raise ConfigurationError(PLUGIN_NAME, "Slots payouts must be a mapping.")
            payouts = dict(slots_payouts)

        if not symbols:
            raise ConfigurationError(PLUGIN_NAME, "Slots must have at least one symbol.")
        if any(not isinstance(symbol, str) or not symbol for symbol in symbols):
            raise ConfigurationError(PLUGIN_NAME, "Slots symbols must be non-empty text.")
        if len(set(symbols)) != len(symbols):
            raise ConfigurationError(PLUGIN_NAME, "Slots symbols must be unique.")
        if len(symbols) != len(weights):
            raise ConfigurationError(PLUGIN_NAME, "Slots symbols and weights must have the same length.")
        if any(isinstance(weight, bool) or not isinstance(weight, int) or weight <= 0 for weight in weights):
            raise ConfigurationError(PLUGIN_NAME, "Slots weights must be positive integers.")
        for symbol in symbols:
            payout = payouts.get(symbol)
            if isinstance(payout, bool) or not isinstance(payout, int) or payout < 0:
                raise ConfigurationError(
                    PLUGIN_NAME,
                    "Slots triple payouts must be non-negative integers for every symbol.",
                )
        _require_int(two_cherry_payout, "Slots two-cherry payout", minimum=0)
        return SlotsConfig(
            symbols=symbols,
            weights=weights,
            triple_payouts=payouts,
            two_cherry_payout=two_cherry_payout,
        )


def _require_int(value: object, label: str, minimum: int | None = None) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ConfigurationError(PLUGIN_NAME, f"{label} must be an integer.")
    if minimum is not None and value < minimum:
        raise ConfigurationError(PLUGIN_NAME, f"{label} must be at least {minimum}.")
