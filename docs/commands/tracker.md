# Tracker

This command lets users inspect their tracked connection time, see the server leaderboard, and opt out of tracking.

## Configuration

The following configuration options are available:

| Option             | Type  | Description                                                                 |
| ------------------ | ----- | --------------------------------------------------------------------------- |
| `trigger`\*        | `str` | The trigger that will be used to invoke the command.                        |
| `description`      | `str` | The description shown by the help command.                                  |
| `data_dir`         | `str` | The directory shared with the `TimeTracker` plugin. Defaults to `"time_tracker"`. |
| `leaderboard_size` | `int` | The maximum number of entries on the leaderboard. Defaults to `10`.         |

Options marked with an asterisk (`*`) are required.

The default metric is hardcoded to `total`, and the top list is always posted server-wide. Neither is configurable.

## Usage

Enable the command in `config.py`:

```python
PLUGINS_CONFIG = {
    "CommandHandler": {
        "prefix": "!",
        "check_interval": 1,
        "commands": {
            "Tracker": {
                "trigger": "tracker",
                "description": "Show connection, idle, and AFK time.",
                "data_dir": "time_tracker",
                "leaderboard_size": 10,
            },
        },
    },
}
```

The `data_dir` must match the `TimeTracker` plugin's `data_dir`.

## Syntax

```text
!tracker
!tracker me
!tracker top
!tracker top idle
!tracker top afk
!tracker optout
!tracker optin
!tracker help
```

| Command                | Behavior                                                                 |
| ---------------------- | ------------------------------------------------------------------------ |
| `!tracker` / `me`      | Show your total, idle, AFK, session count, rank, and last-seen time privately. |
| `!tracker top`         | Post the server-wide leaderboard for total time.                         |
| `!tracker top idle`    | Post the server-wide leaderboard for idle time.                          |
| `!tracker top afk`     | Post the server-wide leaderboard for AFK time.                           |
| `!tracker optout`      | Stop tracking your time and hide you from the leaderboard.               |
| `!tracker optin`       | Resume tracking your time.                                               |
| `!tracker help`        | Show the command list.                                                   |

Aliases: `stats`, `lb`, `off`, `on`, and `?`.

All replies except the top list are private. The top list never includes opted-out users. If the `TimeTracker` plugin is not running, the command still shows persisted data.
