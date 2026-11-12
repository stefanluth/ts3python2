from __future__ import annotations

import time

from ..plugin import Plugin
from ..time_tracker_store import get_store, utcnow


class TimeTracker(Plugin):
    def run(
        self,
        data_dir: str = "time_tracker",
        check_interval: float | int = 60,
        idle_threshold: float | int = 900,
        afk_channel_ids: list[int] | None = None,
        include_query_clients: bool = False,
    ):
        """
        Track how long every connected client has been on the server.

        :param data_dir: Directory where tracked profiles are stored.
        :type data_dir: str
        :param check_interval: Seconds between samples.
        :type check_interval: float
        :param idle_threshold: Seconds of inactivity before time is counted as idle.
        :type idle_threshold: float
        :param afk_channel_ids: Channel IDs whose members accumulate AFK time.
        :type afk_channel_ids: list[int]
        :param include_query_clients: Include query clients in tracking.
        :type include_query_clients: bool
        """

        if afk_channel_ids is None:
            afk_channel_ids = []

        interval = max(0.0, float(check_interval))
        idle_threshold_ms = max(0.0, float(idle_threshold) * 1000)
        afk_channels = _afk_channels(afk_channel_ids)
        max_gap = max(interval * 3, 1.0)
        store = get_store(data_dir, logger=self.logger)
        bot_clid = self._bot_clid()
        previous: dict[int, tuple[str, float]] = {}
        counted_clids: set[int] = set()

        self.ready()

        while not self.event.is_set():
            sample_time = _monotonic()
            now = utcnow()

            try:
                users = list(self.client.get_users())
            except Exception:
                self.logger.exception("Failed to list clients for time tracking.")
                self.event.wait(interval)
                continue

            current: dict[int, tuple[str, str, int | None]] = {}
            for user in users:
                uid = getattr(user, "client_unique_identifier", None)
                clid = getattr(user, "clid", None)
                if not uid or clid is None:
                    continue
                clid = int(clid)
                if bot_clid is not None and clid == bot_clid:
                    continue
                if getattr(user, "client_type", None) == 1 and not include_query_clients:
                    continue
                current[clid] = (
                    uid,
                    getattr(user, "client_nickname", "") or "",
                    getattr(user, "cid", None),
                )

            for clid, (uid, name, cid) in current.items():
                previous_entry = previous.get(clid)
                is_new = previous_entry is None
                was_counted = clid in counted_clids
                elapsed = 0.0
                if previous_entry is not None and was_counted:
                    elapsed = sample_time - previous_entry[1]
                elapsed = max(0.0, min(elapsed, max_gap))

                idle_elapsed = 0.0
                afk_elapsed = elapsed if cid in afk_channels else 0.0
                try:
                    info = self.client.get_user_info(clid)
                    idle_ms = float(getattr(info, "client_idle_time", None) or 0)
                    idle_elapsed = max(0.0, min(elapsed, (idle_ms - idle_threshold_ms) / 1000))
                except Exception:
                    self.logger.exception(f"Failed to get client info for {name or uid}.")

                try:
                    profile = store.record_interval(
                        uid,
                        name,
                        elapsed=elapsed,
                        idle_elapsed=idle_elapsed,
                        afk_elapsed=afk_elapsed,
                        new_session=is_new,
                        now=now,
                    )
                except Exception:
                    self.logger.exception(f"Failed to record time for {name or uid}.")
                    continue

                if profile is None:
                    counted_clids.discard(clid)
                else:
                    counted_clids.add(clid)

            current_uids = {uid for uid, _, _ in current.values()}
            for clid, (uid, _) in previous.items():
                if clid in current:
                    continue
                counted_clids.discard(clid)
                if uid in current_uids:
                    continue
                try:
                    store.end_session(uid, now=now)
                except Exception:
                    self.logger.exception(f"Failed to end the session for {uid}.")

            previous = {clid: (uid, sample_time) for clid, (uid, _, _) in current.items()}
            self.event.wait(interval)

    def _bot_clid(self) -> int | None:
        try:
            return self.client.id
        except Exception:
            self.logger.exception("Failed to resolve the bot client id.")
            return None


def _monotonic() -> float:
    return time.monotonic()


def _afk_channels(values: list[int]) -> set[int]:
    channels: set[int] = set()
    for value in values:
        try:
            channels.add(int(value))
        except TypeError, ValueError:
            continue
    return channels
