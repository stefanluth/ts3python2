from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from ts3client import TS3Client
from ts3client.message import Message

from ..command import Command
from ..errors import ConfigurationError
from ..time_tracker_store import TrackerError, format_duration, get_store

DEFAULT_METRIC = "total"
TOP_SCOPE = "server"
MESSAGE_LIMIT = 900
METRICS = ("total", "idle", "afk")

_METRIC_ATTRIBUTES = {
    "total": "total_seconds",
    "idle": "idle_seconds",
    "afk": "afk_seconds",
}

ALIASES = {
    "me": "me",
    "stats": "me",
    "stat": "me",
    "time": "me",
    "top": "top",
    "leaderboard": "top",
    "lb": "top",
    "ranking": "top",
    "optout": "optout",
    "off": "optout",
    "disable": "optout",
    "optin": "optin",
    "on": "optin",
    "enable": "optin",
    "help": "help",
    "?": "help",
    "h": "help",
}


class Tracker(Command):
    def __init__(
        self,
        client: TS3Client,
        trigger: str,
        data_dir: str = "time_tracker",
        leaderboard_size: int = 10,
        description: str | None = None,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__(client, trigger)
        if isinstance(leaderboard_size, bool) or not isinstance(leaderboard_size, int) or leaderboard_size <= 0:
            raise ConfigurationError("Tracker", "leaderboard_size must be a positive integer.")
        self.data_dir = data_dir
        self.leaderboard_size = leaderboard_size
        self.description = description
        self.store = get_store(data_dir, logger=self.logger)

    def run(self, message: Message) -> None:
        try:
            self._dispatch(message)
        except TrackerError as error:
            self._reply(message, str(error))
        except Exception:
            self.logger.exception("Tracker command failed.")
            self._reply(message, "Tracker command failed.")

    def _dispatch(self, message: Message) -> None:
        parts = message.content.split(None, 1)
        args = parts[1] if len(parts) > 1 else ""
        tokens = args.split()
        if not tokens:
            self._me(message)
            return
        subcommand = ALIASES.get(tokens[0].lower())
        if subcommand is None:
            self._help(message)
            return
        if subcommand == "me":
            self._me(message)
        elif subcommand == "top":
            self._top(message, tokens[1:])
        elif subcommand == "optout":
            self._set_tracking(message, False)
        elif subcommand == "optin":
            self._set_tracking(message, True)
        else:
            self._help(message)

    def _me(self, message: Message) -> None:
        uid = self._invoker_uid(message)
        profile = self.store.get(uid)
        if profile is None:
            self._reply(message, "No tracking data yet.")
            return
        self._reply(message, self._format_profile(profile))

    def _top(self, message: Message, tokens: list[str]) -> None:
        metric = tokens[0].lower() if tokens else DEFAULT_METRIC
        if metric not in METRICS:
            raise TrackerError(f"Unknown metric: {metric}.")
        profiles = self.store.leaderboard(self.leaderboard_size, metric=metric)
        if not profiles:
            text = f"No tracked {metric} time yet."
        else:
            lines = [f"Top tracked time ({metric}):"]
            for index, profile in enumerate(profiles, start=1):
                value = getattr(profile, _METRIC_ATTRIBUTES[metric])
                lines.append(f"  {index}. {profile.name or profile.uid} - {format_duration(value)}")
            text = "\n".join(lines)
        self._send_top(self._truncate(text))

    def _set_tracking(self, message: Message, enabled: bool) -> None:
        uid = self._invoker_uid(message)
        self.store.get_or_create(uid, message.invokername or "")
        self.store.set_do_not_track(uid, not enabled)
        if enabled:
            self._reply(message, "Time tracking enabled.")
        else:
            self._reply(message, "Time tracking disabled. Existing totals are kept and hidden from the leaderboard.")

    def _format_profile(self, profile) -> str:
        lines = [f"Time tracking for {profile.name or profile.uid}:"]
        lines.append(f"  Total: {format_duration(profile.total_seconds)}")
        lines.append(f"  Idle: {format_duration(profile.idle_seconds)}")
        lines.append(f"  AFK: {format_duration(profile.afk_seconds)}")
        lines.append(f"  Sessions: {profile.session_count}")
        if profile.do_not_track:
            lines.append("  Rank: hidden (opted out)")
            lines.append("  Tracking: disabled")
        else:
            rank = self.store.rank(profile.uid)
            if rank is None:
                lines.append("  Rank: unranked")
            else:
                lines.append(f"  Rank: #{rank}")
            lines.append("  Tracking: enabled")
        if profile.last_seen_at is not None:
            lines.append(f"  Last seen: {_format_timestamp(profile.last_seen_at)}")
        return "\n".join(lines)

    def _help(self, message: Message) -> None:
        text = "\n".join(
            [
                "Tracker commands:",
                "  me - Show your total, idle, and AFK time.",
                "  top [total|idle|afk] - Show the server leaderboard.",
                "  optout - Stop tracking your time.",
                "  optin - Resume tracking your time.",
                "  help - Show this message.",
            ]
        )
        self._reply(message, text)

    def _send_top(self, text: str) -> None:
        try:
            if TOP_SCOPE == "server":
                self.client.send_server_message(text)
            else:
                self.client.send_channel_message(text)
        except Exception:
            self.logger.exception("Failed to send the tracker leaderboard.")

    def _reply(self, message: Message, text: str) -> None:
        try:
            self.client.send_private_message(message.invokerid, self._truncate(text))
        except Exception:
            self.logger.exception("Failed to send the tracker reply.")

    def _invoker_uid(self, message: Message) -> str:
        uid = getattr(message, "invokeruid", None)
        if uid:
            return uid
        try:
            info = self.client.get_user_info(message.invokerid)
            if info.client_unique_identifier:
                return info.client_unique_identifier
        except Exception:
            self.logger.exception("Failed to resolve the invoker uid.")
        return f"clid:{message.invokerid}"

    def _truncate(self, text: str) -> str:
        if len(text) <= MESSAGE_LIMIT:
            return text
        return f"{text[: MESSAGE_LIMIT - 3]}..."


def _format_timestamp(value: str) -> str:
    try:
        parsed = datetime.fromisoformat(value)
    except TypeError, ValueError:
        return "unknown"
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
