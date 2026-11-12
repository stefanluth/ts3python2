from __future__ import annotations

import hashlib
import json
import logging
import math
import os
import pathlib
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone

SCHEMA_VERSION = 1
PROFILES_DIRNAME = "profiles"
METRICS = ("total", "idle", "afk")

_METRIC_ATTRIBUTES = {
    "total": "total_seconds",
    "idle": "idle_seconds",
    "afk": "afk_seconds",
}


class TrackerError(Exception):
    """A tracker error that can be shown to the user."""


@dataclass
class Profile:
    uid: str
    name: str
    created_at: str
    updated_at: str
    total_seconds: float = 0.0
    idle_seconds: float = 0.0
    afk_seconds: float = 0.0
    session_count: int = 0
    last_connected_at: str | None = None
    last_seen_at: str | None = None
    last_disconnected_at: str | None = None
    do_not_track: bool = False


class TimeTrackerStore:
    def __init__(self, data_dir: str | pathlib.Path = "time_tracker", *, logger: logging.Logger | None = None):
        self.data_dir = pathlib.Path(data_dir)
        self.profiles_dir = self.data_dir / PROFILES_DIRNAME
        self.logger = logger
        self._profiles: dict[str, Profile] = {}
        self._lock = threading.RLock()
        self.load()

    def load(self) -> None:
        with self._lock:
            self._profiles = {}
            if not self.profiles_dir.is_dir():
                return
            for path in sorted(self.profiles_dir.glob("*.json")):
                profile = self._read_profile(path)
                if profile is None:
                    continue
                self._profiles[profile.uid] = profile

    def get_or_create(self, uid: str, name: str, now: datetime | None = None) -> Profile:
        _validate_uid(uid)
        with self._lock:
            return self._get_or_create_locked(uid, name, now)

    def get(self, uid: str) -> Profile | None:
        with self._lock:
            return self._profiles.get(uid)

    def all_profiles(self) -> list[Profile]:
        with self._lock:
            return sorted(self._profiles.values(), key=lambda profile: (profile.name.casefold(), profile.uid))

    def record_interval(
        self,
        uid: str,
        name: str,
        *,
        elapsed: float,
        idle_elapsed: float = 0.0,
        afk_elapsed: float = 0.0,
        new_session: bool = False,
        now: datetime | None = None,
    ) -> Profile | None:
        _validate_uid(uid)
        elapsed = _validate_seconds(elapsed, "Elapsed time")
        idle_elapsed = _validate_seconds(idle_elapsed, "Idle time")
        afk_elapsed = _validate_seconds(afk_elapsed, "AFK time")

        with self._lock:
            profile = self._get_or_create_locked(uid, name, now)
            if profile.do_not_track:
                return None

            current = _normalize_datetime(now or utcnow())
            timestamp = _to_iso(current)
            safe_name = _safe_name(name)
            if profile.name != safe_name:
                profile.name = safe_name

            idle_elapsed = min(idle_elapsed, elapsed)
            afk_elapsed = min(afk_elapsed, elapsed)
            profile.total_seconds = _round_seconds(profile.total_seconds + elapsed)
            profile.idle_seconds = _round_seconds(min(profile.total_seconds, profile.idle_seconds + idle_elapsed))
            profile.afk_seconds = _round_seconds(min(profile.total_seconds, profile.afk_seconds + afk_elapsed))
            profile.updated_at = timestamp
            profile.last_seen_at = timestamp
            if new_session:
                profile.session_count += 1
                profile.last_connected_at = timestamp
            self.save(profile)
            return profile

    def end_session(self, uid: str, now: datetime | None = None) -> Profile | None:
        with self._lock:
            profile = self._profiles.get(uid)
            if profile is None:
                return None
            if profile.do_not_track:
                return profile
            current = _normalize_datetime(now or utcnow())
            timestamp = _to_iso(current)
            profile.last_disconnected_at = timestamp
            profile.updated_at = timestamp
            self.save(profile)
            return profile

    def set_do_not_track(self, uid: str, enabled: bool, now: datetime | None = None) -> Profile:
        if not isinstance(enabled, bool):
            raise TrackerError("Tracking state must be a boolean.")
        with self._lock:
            profile = self._profiles.get(uid)
            if profile is None:
                raise TrackerError("Profile not found.")
            if profile.do_not_track == enabled:
                return profile
            current = _normalize_datetime(now or utcnow())
            profile.do_not_track = enabled
            profile.updated_at = _to_iso(current)
            self.save(profile)
            return profile

    def toggle_do_not_track(self, uid: str, now: datetime | None = None) -> bool:
        with self._lock:
            profile = self._profiles.get(uid)
            if profile is None:
                raise TrackerError("Profile not found.")
            profile = self.set_do_not_track(uid, not profile.do_not_track, now=now)
            return profile.do_not_track

    def is_tracked(self, uid: str) -> bool:
        with self._lock:
            profile = self._profiles.get(uid)
            return profile is not None and not profile.do_not_track

    def leaderboard(self, limit: int, metric: str = "total") -> list[Profile]:
        _validate_limit(limit)
        attribute = _metric_attribute(metric)
        with self._lock:
            profiles = [
                profile
                for profile in self._profiles.values()
                if not profile.do_not_track and getattr(profile, attribute) > 0
            ]
            profiles.sort(
                key=lambda profile: (
                    -getattr(profile, attribute),
                    -profile.total_seconds,
                    profile.name.casefold(),
                    profile.uid,
                )
            )
            return profiles[:limit]

    def rank(self, uid: str, metric: str = "total") -> int | None:
        _metric_attribute(metric)
        with self._lock:
            for index, profile in enumerate(self.leaderboard(len(self._profiles), metric=metric), start=1):
                if profile.uid == uid:
                    return index
            return None

    def save(self, profile: Profile) -> None:
        target = self._path_for(profile.uid)
        temporary = target.with_name(f".{target.stem}.{os.getpid()}.tmp")
        try:
            self.profiles_dir.mkdir(parents=True, exist_ok=True)
            with temporary.open("w", encoding="utf-8") as handle:
                json.dump(_profile_to_dict(profile), handle, indent=2)
                handle.write("\n")
            os.replace(temporary, target)
        except OSError:
            self._get_logger().exception(f"Failed to save profile file {target}.")
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass

    def _get_or_create_locked(self, uid: str, name: str, now: datetime | None) -> Profile:
        current = _normalize_datetime(now or utcnow())
        timestamp = _to_iso(current)
        safe_name = _safe_name(name)
        profile = self._profiles.get(uid)
        if profile is not None:
            if profile.name != safe_name:
                profile.name = safe_name
                profile.updated_at = timestamp
                self.save(profile)
            return profile

        profile = Profile(
            uid=uid,
            name=safe_name,
            created_at=timestamp,
            updated_at=timestamp,
        )
        self._profiles[uid] = profile
        self.save(profile)
        return profile

    def _path_for(self, uid: str) -> pathlib.Path:
        digest = hashlib.sha256(uid.encode("utf-8")).hexdigest()
        return self.profiles_dir / f"{digest}.json"

    def _read_profile(self, path: pathlib.Path) -> Profile | None:
        try:
            with path.open(encoding="utf-8") as handle:
                data = json.load(handle)
        except OSError, ValueError:
            self._quarantine(path)
            return None

        profile = _profile_from_dict(data)
        if profile is None:
            self._get_logger().warning(f"Skipping malformed profile file {path}.")
        return profile

    def _quarantine(self, path: pathlib.Path) -> None:
        target = self.profiles_dir / f".corrupt-{path.stem}-{time.time_ns()}.json"
        try:
            os.replace(path, target)
        except OSError:
            self._get_logger().exception(f"Failed to quarantine profile file {path}.")
            return
        self._get_logger().warning(f"Quarantined corrupt profile file {path} as {target}.")

    def _get_logger(self) -> logging.Logger:
        if self.logger is None:
            self.logger = logging.getLogger("plugins.time_tracker_store")
        return self.logger


_STORES: dict[str, TimeTrackerStore] = {}
_STORES_LOCK = threading.Lock()


def get_store(
    data_dir: str | pathlib.Path = "time_tracker", *, logger: logging.Logger | None = None
) -> TimeTrackerStore:
    key = str(pathlib.Path(data_dir).resolve())
    with _STORES_LOCK:
        store = _STORES.get(key)
        if store is None:
            store = TimeTrackerStore(data_dir, logger=logger)
            _STORES[key] = store
        elif logger is not None and store.logger is None:
            store.logger = logger
        return store


def reset_stores() -> None:
    with _STORES_LOCK:
        _STORES.clear()


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def format_duration(seconds: float) -> str:
    total = max(0, int(round(seconds)))
    days, remainder = divmod(total, 86400)
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


def _safe_name(name: str) -> str:
    return name if isinstance(name, str) else ""


def _validate_uid(uid: str) -> None:
    if not isinstance(uid, str) or not uid:
        raise TrackerError("Invalid unique identifier.")


def _validate_seconds(value: float, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise TrackerError(f"{label} must be a non-negative number.")
    number = float(value)
    if not math.isfinite(number) or number < 0:
        raise TrackerError(f"{label} must be a non-negative number.")
    return number


def _validate_limit(limit: int) -> None:
    if isinstance(limit, bool) or not isinstance(limit, int) or limit < 0:
        raise TrackerError("Limit must be a non-negative integer.")


def _metric_attribute(metric: str) -> str:
    try:
        return _METRIC_ATTRIBUTES[metric]
    except KeyError as error:
        raise TrackerError(f"Unknown metric: {metric}.") from error


def _round_seconds(value: float) -> float:
    return round(max(0.0, value), 2)


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


def _timestamp(value: object) -> str:
    if not isinstance(value, str) or _parse_datetime(value) is None:
        raise ValueError("not a timestamp")
    return value


def _seconds(value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise ValueError("not a number")
    number = float(value)
    if not math.isfinite(number) or number < 0:
        raise ValueError("negative or non-finite number")
    return _round_seconds(number)


def _integer(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError("not a non-negative integer")
    return value


def _optional_timestamp(value: object) -> str | None:
    if value is None:
        return None
    return _timestamp(value)


def _profile_to_dict(profile: Profile) -> dict:
    return {
        "schema_version": SCHEMA_VERSION,
        "uid": profile.uid,
        "name": profile.name,
        "created_at": profile.created_at,
        "updated_at": profile.updated_at,
        "total_seconds": profile.total_seconds,
        "idle_seconds": profile.idle_seconds,
        "afk_seconds": profile.afk_seconds,
        "session_count": profile.session_count,
        "last_connected_at": profile.last_connected_at,
        "last_seen_at": profile.last_seen_at,
        "last_disconnected_at": profile.last_disconnected_at,
        "do_not_track": profile.do_not_track,
    }


def _profile_from_dict(data: object) -> Profile | None:
    if not isinstance(data, dict) or data.get("schema_version") != SCHEMA_VERSION:
        return None
    try:
        uid = data.get("uid")
        if not isinstance(uid, str) or not uid:
            raise ValueError("invalid uid")
        name = data.get("name")
        if not isinstance(name, str):
            raise ValueError("invalid name")
        created_at = _timestamp(data.get("created_at"))
        updated_at = _timestamp(data.get("updated_at"))
        total_seconds = _seconds(data.get("total_seconds"))
        idle_seconds = _seconds(data.get("idle_seconds"))
        afk_seconds = _seconds(data.get("afk_seconds"))
        if idle_seconds > total_seconds or afk_seconds > total_seconds:
            raise ValueError("counter exceeds total")
        session_count = _integer(data.get("session_count"))
        last_connected_at = _optional_timestamp(data.get("last_connected_at"))
        last_seen_at = _optional_timestamp(data.get("last_seen_at"))
        last_disconnected_at = _optional_timestamp(data.get("last_disconnected_at"))
        do_not_track = data.get("do_not_track")
        if not isinstance(do_not_track, bool):
            raise ValueError("invalid tracking state")
    except TypeError, ValueError:
        return None

    return Profile(
        uid=uid,
        name=name,
        created_at=created_at,
        updated_at=updated_at,
        total_seconds=total_seconds,
        idle_seconds=idle_seconds,
        afk_seconds=afk_seconds,
        session_count=session_count,
        last_connected_at=last_connected_at,
        last_seen_at=last_seen_at,
        last_disconnected_at=last_disconnected_at,
        do_not_track=do_not_track,
    )
