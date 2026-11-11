from __future__ import annotations

import hashlib
import json
import logging
import os
import pathlib
import random
from dataclasses import dataclass, field
from datetime import datetime, timezone

from ts3client.utils.logger import create_logger

CODE_ALPHABET = "abcdefghjkmnpqrstuvwxyz23456789"
CODE_LENGTH = 3
SCHEMA_VERSION = 1
MAX_CODE_ATTEMPTS = 1000


class PollError(Exception):
    """A poll error that can be shown to the user."""


@dataclass
class Poll:
    id: str
    question: str
    options: list[str]
    creator_uid: str
    creator_name: str
    created_at: str
    expires_at: str | None = None
    closed_at: str | None = None
    anonymous: bool = False
    multi_choice: bool = False
    scope: str = "server"
    channel_id: int | None = None
    channel_name: str | None = None
    votes: dict[str, list[int]] = field(default_factory=dict)
    voter_names: dict[str, str] = field(default_factory=dict)

    @property
    def closed(self) -> bool:
        return self.closed_at is not None

    def counts(self) -> list[int]:
        counts = [0] * len(self.options)
        for indices in self.votes.values():
            for index in indices:
                counts[index] += 1
        return counts

    def percentages(self) -> list[float]:
        voters = self.total_voters()
        if voters == 0:
            return [0.0] * len(self.options)
        return [round(count / voters * 100, 2) for count in self.counts()]

    def total_voters(self) -> int:
        return len(self.votes)

    def total_selections(self) -> int:
        return sum(len(indices) for indices in self.votes.values())

    def winners(self) -> list[int]:
        counts = self.counts()
        if not counts:
            return []
        highest = max(counts)
        if highest == 0:
            return []
        return [index for index, count in enumerate(counts) if count == highest]

    def is_expired(self, now: datetime) -> bool:
        if self.closed or self.expires_at is None:
            return False
        expires = _parse_datetime(self.expires_at)
        if expires is None:
            return False
        return expires <= _normalize_datetime(now)


class PollStore:
    def __init__(self, polls_dir: str | pathlib.Path | None = None, logger: logging.Logger | None = None):
        self.polls_dir = pathlib.Path(polls_dir) if polls_dir is not None else None
        self.logger = logger
        self._polls: dict[str, Poll] = {}
        if self.polls_dir is not None:
            self.load()

    def load(self) -> None:
        self._polls = {}
        if self.polls_dir is None or not self.polls_dir.is_dir():
            return
        for path in sorted(self.polls_dir.glob("*.json")):
            poll = self._read_poll(path)
            if poll is None:
                continue
            key = poll.id.lower()
            if key in self._polls:
                continue
            self._polls[key] = poll
        self._polls = dict(sorted(self._polls.items(), key=lambda item: _created_sort_key(item[1])))

    def save(self, poll: Poll) -> None:
        if self.polls_dir is None:
            return
        target = self.polls_dir / f"{poll.id}.json"
        temporary = self.polls_dir / f".{poll.id}.tmp"
        try:
            self.polls_dir.mkdir(parents=True, exist_ok=True)
            with temporary.open("w", encoding="utf-8") as handle:
                json.dump(_poll_to_dict(poll), handle, indent=2)
                handle.write("\n")
            os.replace(temporary, target)
        except OSError:
            self._get_logger().exception(f"Failed to save poll {poll.id}.")
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass

    def create(
        self,
        *,
        question: str,
        options: list[str],
        creator_uid: str,
        creator_name: str,
        scope: str,
        channel_id: int | None = None,
        channel_name: str | None = None,
        anonymous: bool = False,
        multi_choice: bool = False,
        expires_at: datetime | None = None,
        now: datetime | None = None,
    ) -> Poll:
        question = question.strip()
        options = [option.strip() for option in options]
        if not question:
            raise PollError("Question cannot be empty.")
        if len(options) < 2:
            raise PollError("A poll needs at least two options.")
        if len(options) > 26:
            raise PollError("A poll can have at most 26 options.")
        if any(not option for option in options):
            raise PollError("Options cannot be empty.")
        if scope not in ("server", "channel"):
            raise PollError("Scope must be 'server' or 'channel'.")
        if scope == "channel" and channel_id is None:
            raise PollError("Channel polls need a channel.")

        poll_id = self._generate_id()
        poll = Poll(
            id=poll_id,
            question=question,
            options=options,
            creator_uid=creator_uid,
            creator_name=creator_name,
            created_at=_to_iso(now or datetime.now(timezone.utc)),
            expires_at=_to_iso(expires_at) if expires_at is not None else None,
            anonymous=anonymous,
            multi_choice=multi_choice,
            scope=scope,
            channel_id=channel_id,
            channel_name=channel_name,
        )
        self._polls[poll.id.lower()] = poll
        self.save(poll)
        return poll

    def get(self, poll_id: str) -> Poll | None:
        return self._polls.get(poll_id.lower())

    def list_polls(
        self,
        *,
        scope: str | None = None,
        channel_id: int | None = None,
        include_closed: bool = False,
    ) -> list[Poll]:
        polls = []
        for poll in self._polls.values():
            if not include_closed and poll.closed:
                continue
            if scope is not None and poll.scope != scope:
                continue
            if channel_id is not None and poll.channel_id != channel_id:
                continue
            polls.append(poll)
        return sorted(polls, key=_created_sort_key, reverse=True)

    def voter_key(self, poll: Poll, voter_uid: str) -> str:
        if poll.anonymous:
            return hashlib.sha256(f"{voter_uid}:{poll.id}".encode()).hexdigest()
        return voter_uid

    def vote(
        self,
        poll_id: str,
        voter_uid: str,
        option_indices: list[int],
        *,
        voter_name: str | None = None,
        now: datetime | None = None,
    ) -> Poll:
        poll = self.get(poll_id)
        if poll is None:
            raise PollError("Poll not found.")
        current = now or datetime.now(timezone.utc)
        if poll.closed:
            raise PollError("Poll has ended.")
        if poll.is_expired(current):
            self.close(poll_id, now=current)
            raise PollError("Poll has ended.")

        indices = list(option_indices)
        if not indices:
            raise PollError("Please select at least one option.")
        if any(not isinstance(index, int) or isinstance(index, bool) for index in indices):
            raise PollError("Invalid option.")
        if any(index < 0 or index >= len(poll.options) for index in indices):
            raise PollError("Invalid option.")
        if len(set(indices)) != len(indices):
            raise PollError("Options cannot be selected more than once.")
        if not poll.multi_choice and len(indices) != 1:
            raise PollError("Only one option can be selected.")

        key = self.voter_key(poll, voter_uid)
        poll.votes[key] = sorted(indices)
        if not poll.anonymous and voter_name is not None:
            poll.voter_names[key] = voter_name
        self.save(poll)
        return poll

    def close(self, poll_id: str, *, now: datetime | None = None) -> Poll:
        poll = self.get(poll_id)
        if poll is None:
            raise PollError("Poll not found.")
        if poll.closed_at is None:
            poll.closed_at = _to_iso(now or datetime.now(timezone.utc))
        self.save(poll)
        return poll

    def delete(self, poll_id: str) -> bool:
        poll = self.get(poll_id)
        if poll is None:
            return False
        self._polls.pop(poll.id.lower(), None)
        if self.polls_dir is not None:
            try:
                (self.polls_dir / f"{poll.id}.json").unlink(missing_ok=True)
            except OSError:
                self._get_logger().exception(f"Failed to delete poll {poll.id}.")
        return True

    def due(self, now: datetime) -> list[Poll]:
        current = _normalize_datetime(now)
        polls = []
        for poll in self._polls.values():
            if poll.closed or poll.expires_at is None:
                continue
            expires = _parse_datetime(poll.expires_at)
            if expires is not None and expires <= current:
                polls.append(poll)
        return sorted(polls, key=_created_sort_key)

    def close_expired(self, now: datetime) -> list[Poll]:
        closed = []
        for poll in self.due(now):
            self.close(poll.id, now=now)
            closed.append(poll)
        return closed

    def _generate_id(self) -> str:
        for _ in range(MAX_CODE_ATTEMPTS):
            poll_id = "".join(random.choice(CODE_ALPHABET) for _ in range(CODE_LENGTH))
            if not self._id_exists(poll_id):
                return poll_id
        raise PollError("Could not generate a unique poll id.")

    def _id_exists(self, poll_id: str) -> bool:
        if poll_id.lower() in self._polls:
            return True
        if self.polls_dir is not None and (self.polls_dir / f"{poll_id}.json").exists():
            return True
        return False

    def _read_poll(self, path: pathlib.Path) -> Poll | None:
        try:
            with path.open(encoding="utf-8") as handle:
                data = json.load(handle)
        except OSError, ValueError:
            self._get_logger().exception(f"Failed to read poll file {path}.")
            return None
        poll = _poll_from_dict(data, path.stem)
        if poll is None:
            self._get_logger().warning(f"Skipping malformed poll file {path}.")
        return poll

    def _get_logger(self) -> logging.Logger:
        if self.logger is None:
            self.logger = create_logger("PollStore", "logs/plugins.log")
        return self.logger


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


def _created_sort_key(poll: Poll) -> float:
    created = _parse_datetime(poll.created_at)
    return created.timestamp() if created is not None else 0.0


def _poll_to_dict(poll: Poll) -> dict:
    return {
        "schema_version": SCHEMA_VERSION,
        "id": poll.id,
        "question": poll.question,
        "options": poll.options,
        "created_at": poll.created_at,
        "expires_at": poll.expires_at,
        "closed": poll.closed,
        "closed_at": poll.closed_at,
        "anonymous": poll.anonymous,
        "multi_choice": poll.multi_choice,
        "scope": poll.scope,
        "channel_id": poll.channel_id,
        "channel_name": poll.channel_name,
        "creator": {"uid": poll.creator_uid, "name": poll.creator_name},
        "votes": poll.votes,
        "voter_names": poll.voter_names,
        "results": {
            "counts": poll.counts(),
            "percentages": poll.percentages(),
            "total_voters": poll.total_voters(),
            "total_selections": poll.total_selections(),
            "winner": poll.winners(),
        },
    }


def _poll_from_dict(data: object, expected_id: str) -> Poll | None:
    if not isinstance(data, dict):
        return None
    try:
        poll_id = data.get("id")
        if not isinstance(poll_id, str) or poll_id != expected_id:
            return None
        question = data.get("question")
        if not isinstance(question, str) or not question:
            return None
        options = data.get("options")
        if not isinstance(options, list) or not all(isinstance(option, str) for option in options):
            return None
        if len(options) < 2 or len(options) > 26 or any(not option for option in options):
            return None
        created_at = data.get("created_at")
        if not isinstance(created_at, str):
            return None
        creator = data.get("creator")
        if not isinstance(creator, dict):
            return None
        creator_uid = creator.get("uid")
        creator_name = creator.get("name")
        if not isinstance(creator_uid, str) or not isinstance(creator_name, str):
            return None
        expires_at = data.get("expires_at")
        if expires_at is not None and not isinstance(expires_at, str):
            return None
        closed_at = data.get("closed_at")
        if closed_at is not None and not isinstance(closed_at, str):
            return None
        if closed_at is None and data.get("closed") is True:
            closed_at = expires_at or created_at
        anonymous = data.get("anonymous", False)
        multi_choice = data.get("multi_choice", False)
        if not isinstance(anonymous, bool) or not isinstance(multi_choice, bool):
            return None
        scope = data.get("scope", "server")
        if scope not in ("server", "channel"):
            return None
        channel_id = data.get("channel_id")
        if channel_id is not None and not isinstance(channel_id, int):
            return None
        channel_name = data.get("channel_name")
        if channel_name is not None and not isinstance(channel_name, str):
            return None
        if scope == "channel" and channel_id is None:
            return None
        votes = _votes_from_dict(data.get("votes", {}), len(options))
        if votes is None:
            return None
        voter_names = _voter_names_from_dict(data.get("voter_names", {}))
        if voter_names is None:
            return None
        if anonymous:
            voter_names = {}
        return Poll(
            id=poll_id,
            question=question,
            options=options,
            creator_uid=creator_uid,
            creator_name=creator_name,
            created_at=created_at,
            expires_at=expires_at,
            closed_at=closed_at,
            anonymous=anonymous,
            multi_choice=multi_choice,
            scope=scope,
            channel_id=channel_id,
            channel_name=channel_name,
            votes=votes,
            voter_names=voter_names,
        )
    except TypeError, ValueError, KeyError:
        return None


def _votes_from_dict(data: object, option_count: int) -> dict[str, list[int]] | None:
    if not isinstance(data, dict):
        return None
    votes: dict[str, list[int]] = {}
    for key, indices in data.items():
        if not isinstance(key, str) or not isinstance(indices, list):
            return None
        if not all(
            isinstance(index, int) and not isinstance(index, bool) and 0 <= index < option_count for index in indices
        ):
            return None
        votes[key] = list(indices)
    return votes


def _voter_names_from_dict(data: object) -> dict[str, str] | None:
    if not isinstance(data, dict):
        return None
    names: dict[str, str] = {}
    for key, name in data.items():
        if not isinstance(key, str) or not isinstance(name, str):
            return None
        names[key] = name
    return names
