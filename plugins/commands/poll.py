from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from typing import Any

from ts3client import TS3Client
from ts3client.constants import TargetMode
from ts3client.message import Message

from ..command import Command
from ..poll_store import Poll as StoredPoll
from ..poll_store import PollError, PollStore

DURATION_FLAG_PATTERN = re.compile(r"--duration(?:=|\s+)(\S+)")
FLAG_PATTERN = re.compile(r"--(anonymous|multi|server|channel)\b")
DURATION_PATTERN = re.compile(r"^(\d+)([smhd]?)$")
OPTION_PATTERN = re.compile(r"^[a-z]+$")
MESSAGE_LIMIT = 900
MAX_LISTED_VOTERS = 5

ALIASES = {
    "create": "create",
    "c": "create",
    "vote": "vote",
    "v": "vote",
    "results": "results",
    "r": "results",
    "list": "list",
    "l": "list",
    "end": "end",
    "e": "end",
    "close": "end",
    "delete": "delete",
    "d": "delete",
    "help": "help",
    "h": "help",
}

DURATION_SECONDS = {"": 1, "s": 1, "m": 60, "h": 3600, "d": 86400}


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Poll(Command):
    def __init__(
        self,
        client: TS3Client,
        trigger: str,
        polls_dir: str = "polls",
        max_options: int = 10,
        max_question_length: int = 200,
        default_duration: Any = None,
        notify_users: bool = True,
        notify_query_clients: bool = False,
        prefix: str = "!",
        description: str | None = None,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__(client, trigger)
        self.store = PollStore(polls_dir, logger=self.logger)
        self.max_options = max(2, min(int(max_options), 26))
        self.max_question_length = max(1, int(max_question_length))
        self.default_duration = default_duration
        self.notify_users = notify_users
        self.notify_query_clients = notify_query_clients
        self.prefix = prefix
        self._last_prefix = prefix

    def run(self, message: Message) -> None:
        try:
            prefix = self._derive_prefix(message)
            self._last_prefix = prefix
            self._dispatch(message, prefix)
        except PollError as error:
            self._reply(message, str(error))
        except Exception:
            self.logger.exception("Poll command failed.")
            self._reply(message, "Poll command failed.")

    def tick(self) -> None:
        now = utcnow()
        try:
            closed = self.store.close_expired(now)
        except Exception:
            self.logger.exception("Failed to close expired polls.")
            return
        for poll in closed:
            try:
                results = self._format_results(poll, now=now)
                prefix = getattr(self, "_last_prefix", self.prefix)
                announcement = f"{results}\nResults: {prefix}{self.trigger} results {poll.id}"
                self._send_to_scope(poll, self._truncate(announcement))
                self._notify_ended(poll, results)
            except Exception:
                self.logger.exception(f"Failed to announce ended poll {poll.id}.")

    def stop(self) -> None:
        pass

    def _dispatch(self, message: Message, prefix: str) -> None:
        parts = message.content.split(None, 1)
        args = parts[1] if len(parts) > 1 else ""
        tokens = args.split()
        if not tokens:
            self._help(message)
            return
        subcommand = ALIASES.get(tokens[0].lower())
        if subcommand is None:
            self._help(message)
            return
        arguments = tokens[1:]
        if subcommand == "create":
            raw = args.split(None, 1)[1] if len(tokens) > 1 else ""
            self._create(message, raw, prefix)
        elif subcommand == "vote":
            self._vote(message, arguments)
        elif subcommand == "results":
            self._results(message, arguments)
        elif subcommand == "list":
            self._list(message, arguments)
        elif subcommand == "end":
            self._end(message, arguments)
        elif subcommand == "delete":
            self._delete(message, arguments)
        else:
            self._help(message)

    def _derive_prefix(self, message: Message) -> str:
        content = message.content.strip()
        head = content.split(None, 1)[0] if content else ""
        if self.trigger and head.endswith(self.trigger):
            return head[: -len(self.trigger)]
        return self.prefix

    def _create(self, message: Message, raw: str, prefix: str) -> None:
        duration_value = None
        duration_match = DURATION_FLAG_PATTERN.search(raw)
        if duration_match:
            duration_value = duration_match.group(1)
            raw = raw[: duration_match.start()] + raw[duration_match.end() :]

        anonymous = re.search(r"--anonymous\b", raw) is not None
        multi_choice = re.search(r"--multi\b", raw) is not None
        server_flag = re.search(r"--server\b", raw) is not None
        channel_flag = re.search(r"--channel\b", raw) is not None
        raw = FLAG_PATTERN.sub("", raw)

        segments = [segment.strip() for segment in raw.split("|")]
        if len(segments) < 3:
            raise PollError("Use: create <question> | <option> | <option> ...")
        question = segments[0]
        options = segments[1:]

        if not question:
            raise PollError("Question cannot be empty.")
        if len(question) > self.max_question_length:
            raise PollError(f"Question cannot be longer than {self.max_question_length} characters.")
        if len(options) < 2:
            raise PollError("A poll needs at least two options.")
        if len(options) > self.max_options:
            raise PollError(f"A poll can have at most {self.max_options} options.")
        for option in options:
            if not option:
                raise PollError("Options cannot be empty.")
            if len(option) > self.max_question_length:
                raise PollError(f"Options cannot be longer than {self.max_question_length} characters.")
        if server_flag and channel_flag:
            raise PollError("Use either --server or --channel, not both.")

        scope = "server"
        channel_id = None
        if message.targetmode == TargetMode.CHANNEL.value:
            scope = "channel"
            channel_id = self._invoker_cid(message)
            if channel_id is None:
                raise PollError("Could not determine your channel.")
        if server_flag:
            scope = "server"
            channel_id = None
        if channel_flag:
            scope = "channel"
            channel_id = self._invoker_cid(message)
            if channel_id is None:
                raise PollError("Could not determine your channel.")

        channel_name = None
        if scope == "channel":
            if channel_id is None:
                raise PollError("Could not determine your channel.")
            channel_name = self._resolve_channel_name(channel_id)

        duration = self._select_duration(duration_value)
        now = utcnow()
        expires_at = now + duration if duration is not None else None

        poll = self.store.create(
            question=question,
            options=options,
            creator_uid=self._invoker_uid(message),
            creator_name=message.invokername,
            scope=scope,
            channel_id=channel_id,
            channel_name=channel_name,
            anonymous=anonymous,
            multi_choice=multi_choice,
            expires_at=expires_at,
            now=now,
        )

        announcement = self._announcement(poll, prefix, now=now)
        self._send_to_scope(poll, announcement)
        self._reply(message, self._confirmation(poll, prefix, now=now))
        self._notify_users(poll, announcement, creator_clid=message.invokerid)

    def _vote(self, message: Message, tokens: list[str]) -> None:
        if not tokens:
            raise PollError("Use: vote <poll id> <options>.")
        poll = self.store.get(tokens[0])
        if poll is None:
            raise PollError("Poll not found.")

        raw = "".join(tokens[1:]).replace(",", "").replace(" ", "").lower()
        if not OPTION_PATTERN.fullmatch(raw):
            raise PollError("Options must be letters such as a or a,c.")
        indices = [ord(character) - ord("a") for character in raw]
        if len(set(indices)) != len(indices):
            raise PollError("Options cannot be selected more than once.")
        if any(index < 0 or index >= len(poll.options) for index in indices):
            raise PollError("Invalid option.")
        if not poll.multi_choice and len(indices) != 1:
            raise PollError("Only one option can be selected.")

        if poll.scope == "channel":
            invoker_cid = self._invoker_cid(message)
            if invoker_cid != poll.channel_id:
                raise PollError(f"This poll is for {self._channel_display(poll)} only.")

        uid = self._invoker_uid(message)
        poll = self.store.vote(poll.id, uid, indices, voter_name=message.invokername, now=utcnow())
        letters = ", ".join(chr(ord("a") + index) for index in sorted(indices))

        if poll.anonymous:
            self._reply(message, f"Vote recorded for {poll.id}.")
        else:
            self._reply(message, f"Vote recorded for {poll.id}: {letters}.")

        if uid == poll.creator_uid:
            return
        creator_clid = self._find_clid_by_uid(poll.creator_uid)
        if creator_clid is None:
            return
        if poll.anonymous:
            text = f"Anonymous vote received on poll {poll.id}. Total voters: {poll.total_voters()}."
        else:
            text = f"{message.invokername} voted on poll {poll.id}: {letters}. Total voters: {poll.total_voters()}."
        self._send_private(creator_clid, text)

    def _results(self, message: Message, tokens: list[str]) -> None:
        if not tokens:
            raise PollError("Use: results <poll id>.")
        poll = self.store.get(tokens[0])
        if poll is None:
            raise PollError("Poll not found.")
        self._reply(message, self._format_results(poll))

    def _list(self, message: Message, tokens: list[str]) -> None:
        include_closed = any(token.lower() == "all" for token in tokens)
        invoker_cid = self._invoker_cid(message)
        groups: dict[str, list[StoredPoll]] = {}
        order: list[str] = []
        for poll in self.store.list_polls(include_closed=include_closed):
            if poll.scope == "server":
                key = "Server"
            elif invoker_cid is not None and poll.channel_id == invoker_cid:
                key = self._channel_display(poll)
            else:
                continue
            if key not in groups:
                groups[key] = []
                order.append(key)
            groups[key].append(poll)

        if not groups:
            self._reply(message, "No polls.")
            return

        lines = ["Polls:"]
        for key in order:
            lines.append(key)
            for poll in groups[key]:
                suffix = " (ended)" if poll.closed else ""
                lines.append(f"  {poll.id} - {poll.question}{suffix}")
        self._reply(message, "\n".join(lines))

    def _end(self, message: Message, tokens: list[str]) -> None:
        if not tokens:
            raise PollError("Use: end <poll id>.")
        poll = self.store.get(tokens[0])
        if poll is None:
            raise PollError("Poll not found.")
        if self._invoker_uid(message) != poll.creator_uid:
            raise PollError("Only the poll creator can end this poll.")
        if poll.closed:
            self._reply(message, self._format_results(poll))
            return

        poll = self.store.close(poll.id, now=utcnow())
        results = self._format_results(poll)
        self._send_to_scope(poll, results)
        self._notify_ended(poll, results, creator_clid=message.invokerid)

    def _delete(self, message: Message, tokens: list[str]) -> None:
        if not tokens:
            raise PollError("Use: delete <poll id>.")
        poll = self.store.get(tokens[0])
        if poll is None:
            raise PollError("Poll not found.")
        if self._invoker_uid(message) != poll.creator_uid:
            raise PollError("Only the poll creator can delete this poll.")
        if not poll.closed:
            raise PollError("End the poll before deleting it.")
        self.store.delete(poll.id)
        self._reply(message, f"Deleted poll {poll.id}.")

    def _help(self, message: Message) -> None:
        text = "\n".join(
            [
                "Poll commands:",
                "  create <question> | <option> | <option> [--duration 5m] [--anonymous] [--multi] [--server|--channel]",
                "  vote <id> <letters>",
                "  results <id>",
                "  list [all]",
                "  end <id>",
                "  delete <id>",
                "  help",
                "Flags: --duration, --anonymous, --multi, --server, --channel",
            ]
        )
        self._reply(message, text)

    def _announcement(self, poll: StoredPoll, prefix: str, now: datetime | None = None) -> str:
        lines = [f"[{poll.scope} poll {poll.id}{self._scope_suffix(poll)}] {poll.question}"]
        for index, option in enumerate(poll.options):
            lines.append(f"  {chr(ord('a') + index)}) {option}")
        if poll.anonymous:
            lines.append("Anonymous poll.")
        if poll.multi_choice:
            lines.append("Multiple choices allowed.")
        remaining = self._remaining_text(poll, now)
        if remaining:
            lines.append(f"Ends in {remaining}.")
        lines.append(f"Vote: {prefix}{self.trigger} vote {poll.id} a")
        return self._truncate("\n".join(lines))

    def _confirmation(self, poll: StoredPoll, prefix: str, now: datetime | None = None) -> str:
        location = f" in {self._channel_display(poll)}" if poll.scope == "channel" else ""
        text = f"Created {poll.scope} poll {poll.id}{location}."
        if poll.anonymous:
            text += " Anonymous poll."
        if poll.multi_choice:
            text += " Multiple choices allowed."
        remaining = self._remaining_text(poll, now)
        if remaining:
            text += f" Ends in {remaining}."
        text += f"\nVote: {prefix}{self.trigger} vote {poll.id} a"
        return self._truncate(text)

    def _format_results(self, poll: StoredPoll, now: datetime | None = None) -> str:
        current = now or utcnow()
        lines = [f"Poll {poll.id}: {poll.question}"]
        if poll.closed:
            lines.append("Status: ended")
        else:
            remaining = self._remaining_text(poll, current)
            if remaining:
                lines.append(f"Status: open ({remaining} left)")
            else:
                lines.append("Status: open")

        counts = poll.counts()
        percentages = poll.percentages()
        names = self._voter_names_by_index(poll)
        for index, option in enumerate(poll.options):
            line = f"  {chr(ord('a') + index)}) {option}: {counts[index]} ({percentages[index]:g}%)"
            if names.get(index):
                line += f" - {', '.join(names[index])}"
            lines.append(line)

        lines.append(f"Total voters: {poll.total_voters()}")
        if poll.multi_choice:
            lines.append(f"Total selections: {poll.total_selections()}")
        if poll.closed:
            winners = poll.winners()
            if winners:
                label = "Winner" if len(winners) == 1 else "Winners"
                options = ", ".join(f"{chr(ord('a') + index)}) {poll.options[index]}" for index in winners)
                lines.append(f"{label}: {options}")
            else:
                lines.append("No votes.")
        return self._truncate("\n".join(lines))

    def _voter_names_by_index(self, poll: StoredPoll) -> dict[int, list[str]]:
        if poll.anonymous:
            return {}
        names: dict[int, list[str]] = {}
        for key, indices in poll.votes.items():
            name = poll.voter_names.get(key, key)
            for index in indices:
                names.setdefault(index, []).append(name)
        for index, values in names.items():
            if len(values) > MAX_LISTED_VOTERS:
                extra = len(values) - MAX_LISTED_VOTERS
                names[index] = [*values[:MAX_LISTED_VOTERS], f"+{extra} more"]
        return names

    def _send_to_scope(self, poll: StoredPoll, text: str) -> None:
        try:
            if poll.scope == "server":
                self.client.send_server_message(text)
            else:
                channel_id = poll.channel_id
                if channel_id is None:
                    self.logger.error(f"Poll {poll.id} has no channel.")
                    return
                self.client.send_message(channel_id, TargetMode.CHANNEL, text)
        except Exception:
            self.logger.exception(f"Failed to announce poll {poll.id}.")

    def _notify_users(self, poll: StoredPoll, text: str, *, creator_clid: int | None = None) -> None:
        if not self.notify_users:
            return
        bot_clid = self._bot_clid()
        seen: set[int] = set()
        for user in self._get_users():
            clid = getattr(user, "clid", None)
            if clid is None or clid in seen:
                continue
            if bot_clid is not None and clid == bot_clid:
                continue
            if creator_clid is not None and clid == creator_clid:
                continue
            if getattr(user, "client_type", None) == 1 and not self.notify_query_clients:
                continue
            if poll.scope == "channel":
                cid = getattr(user, "cid", None)
                if cid is None:
                    cid = self._user_cid(clid)
                if cid != poll.channel_id:
                    continue
            seen.add(clid)
            self._send_private(clid, text, poll_id=poll.id)

    def _notify_ended(self, poll: StoredPoll, text: str, creator_clid: int | None = None) -> None:
        sent: set[int] = set()
        bot_clid = self._bot_clid()
        if creator_clid is None:
            creator_clid = self._find_clid_by_uid(poll.creator_uid)
        if creator_clid is not None:
            sent.add(creator_clid)
            self._send_private(creator_clid, text, poll_id=poll.id)
        for user in self._get_users():
            clid = getattr(user, "clid", None)
            if clid is None or clid in sent:
                continue
            if bot_clid is not None and clid == bot_clid:
                continue
            uid = getattr(user, "client_unique_identifier", None)
            if uid is None:
                continue
            if self.store.voter_key(poll, uid) not in poll.votes:
                continue
            sent.add(clid)
            self._send_private(clid, text, poll_id=poll.id)

    def _reply(self, message: Message, text: str) -> None:
        self._send_private(message.invokerid, text)

    def _send_private(self, clid: int, text: str, poll_id: str | None = None) -> None:
        try:
            self.client.send_private_message(clid, self._truncate(text))
        except Exception:
            if poll_id is None:
                self.logger.exception("Failed to send poll reply.")
            else:
                self.logger.exception(f"Failed to send poll {poll_id} to {clid}.")

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

    def _invoker_cid(self, message: Message) -> int | None:
        if message.targetmode == TargetMode.CHANNEL.value and message.target:
            return message.target
        try:
            return self.client.get_user_info(message.invokerid).cid
        except Exception:
            self.logger.exception("Failed to resolve invoker channel.")
            return None

    def _user_cid(self, clid: int) -> int | None:
        try:
            return self.client.get_user_info(clid).cid
        except Exception:
            self.logger.exception(f"Failed to resolve channel for {clid}.")
            return None

    def _find_clid_by_uid(self, uid: str) -> int | None:
        for user in self._get_users():
            if getattr(user, "client_unique_identifier", None) == uid:
                clid = getattr(user, "clid", None)
                if clid is not None:
                    return clid
        return None

    def _get_users(self) -> list[Any]:
        try:
            return list(self.client.get_users())
        except Exception:
            self.logger.exception("Failed to get users.")
            return []

    def _bot_clid(self) -> int | None:
        try:
            return self.client.id
        except Exception:
            return None

    def _resolve_channel_name(self, channel_id: int) -> str:
        try:
            for channel in self.client.get_channels():
                if channel.cid == channel_id:
                    return channel.channel_name or f"#{channel_id}"
        except Exception:
            self.logger.exception(f"Failed to resolve channel name for {channel_id}.")
        return f"#{channel_id}"

    def _channel_display(self, poll: StoredPoll) -> str:
        name = poll.channel_name or f"#{poll.channel_id}"
        if name.startswith("#"):
            return name
        return f"#{name}"

    def _scope_suffix(self, poll: StoredPoll) -> str:
        if poll.scope == "channel":
            return f" {self._channel_display(poll)}"
        return ""

    def _remaining_text(self, poll: StoredPoll, now: datetime | None = None) -> str | None:
        if not poll.expires_at:
            return None
        try:
            expires = datetime.fromisoformat(poll.expires_at)
        except ValueError:
            return None
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        seconds = int((expires - (now or utcnow())).total_seconds())
        if seconds <= 0:
            return "0s"
        return self._format_duration(seconds)

    def _format_duration(self, seconds: int) -> str:
        if seconds % 86400 == 0 and seconds >= 86400:
            return f"{seconds // 86400}d"
        if seconds % 3600 == 0 and seconds >= 3600:
            return f"{seconds // 3600}h"
        if seconds % 60 == 0 and seconds >= 60:
            return f"{seconds // 60}m"
        return f"{seconds}s"

    def _select_duration(self, value: str | None) -> timedelta | None:
        candidate = value if value is not None else self.default_duration
        if candidate is None:
            return None
        if isinstance(candidate, timedelta):
            return candidate
        match = DURATION_PATTERN.fullmatch(str(candidate).strip().lower())
        if not match:
            raise PollError(f"Invalid duration: {candidate}.")
        amount = int(match.group(1))
        if amount <= 0:
            raise PollError(f"Invalid duration: {candidate}.")
        return timedelta(seconds=amount * DURATION_SECONDS[match.group(2)])

    def _truncate(self, text: str) -> str:
        if len(text) <= MESSAGE_LIMIT:
            return text
        return f"{text[: MESSAGE_LIMIT - 3]}..."
