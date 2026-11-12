# Time Tracker

This plugin samples the connected clients and keeps track of how long every user has been connected to the server. It records total connection time, idle time, AFK-channel time, session count, and last-seen metadata.

The tracker is local to the bot. It does not publish anything to a website.

## Configuration

The following configuration options are available:

| Option                  | Type        | Description                                                                                     |
| ----------------------- | ----------- | ----------------------------------------------------------------------------------------------- |
| `data_dir`              | `str`       | Directory where tracked profiles are stored. Defaults to `"time_tracker"`.                      |
| `check_interval`        | `int`       | Seconds between samples. Defaults to `60`.                                                       |
| `idle_threshold`        | `int`       | Seconds of inactivity before time starts counting as idle. Defaults to `900`.                    |
| `afk_channel_ids`       | `list[int]` | Channel IDs whose members accumulate AFK time. Defaults to `[]`, which disables AFK tracking.   |
| `include_query_clients` | `bool`      | Include query clients in tracking. Defaults to `False`; the bot itself is never tracked.         |

## Usage

Enable the plugin in `config.py`:

```python
PLUGINS_CONFIG = {
    "TimeTracker": {
        "data_dir": "time_tracker",
        "check_interval": 60,
        "idle_threshold": 900,
        "afk_channel_ids": [],
        "include_query_clients": False,
    },
}
```

The `data_dir` must match the `data_dir` used by the `Tracker` command, otherwise the command reads a different store.

## Accounting

For every sample, the plugin adds the time since the previous sample to the user's total. Idle time is the part of that interval after the configured idle threshold:

```text
idle += clamp(client_idle_time_ms - idle_threshold_ms, 0, elapsed_ms) / 1000
```

AFK time is counted separately while the user is in one of the configured `afk_channel_ids`. Idle and AFK can overlap, and both are independent of the total.

Sessions are counted when a user is first seen. A disconnect is recorded when the user disappears from the client list.

## Storage

Profiles are stored as one JSON file per user:

```text
time_tracker/profiles/<sha256(uid)>.json
```

Each file contains `schema_version: 1`, the real `uid`, the display name, total/idle/AFK seconds, session metadata, and the `do_not_track` flag. Writes use a temporary file plus `os.replace`. Corrupt JSON files are quarantined as `.corrupt-<hash>-<timestamp>.json` and skipped on the next start.

The plugin and the `Tracker` command share one in-memory store per process, so samples are immediately visible to commands.

## Limitations

- Time is counted only while the bot process is running. The first sample after a restart starts at zero.
- A long stall is capped at three sampling intervals.
- Idle time begins only after `idle_threshold` seconds of inactivity.
- AFK tracking requires configured channel IDs.
- Sampling can miss very short connect/disconnect cycles between samples.
- Query clients are excluded by default.
- Run one bot process per data directory; the store does not coordinate multiple processes.
- Opt-out stops accumulation and hides the user from the public leaderboard, but existing totals are retained.
