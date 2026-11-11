# Poll

This command lets users create single-choice or multi-choice polls and surveys, vote in them, and view the results.

Polls can be server-wide or limited to a channel, can be anonymous, and can end manually or automatically after a time limit.

## Configuration

The following configuration options are available:

| Option                 | Type               | Description                                                                                     |
| ---------------------- | ------------------ | ----------------------------------------------------------------------------------------------- |
| `trigger`\*            | `str`              | The trigger that will be used to invoke the command.                                            |
| `polls_dir`            | `str`              | The directory where poll data is stored. Defaults to `"polls"`.                                 |
| `max_options`          | `int`              | The maximum number of options a poll may have. Defaults to `10`.                                |
| `max_question_length`  | `int`              | The maximum length of the question and each option. Defaults to `200`.                          |
| `default_duration`     | `int`/`str`/`None` | The default time limit in seconds or as a duration string such as `"5m"`. Defaults to `None`.   |
| `notify_users`         | `bool`             | Whether everyone in scope is sent a private message when a poll is created. Defaults to `True`. |
| `notify_query_clients` | `bool`             | Whether ServerQuery clients are included in private messages. Defaults to `False`.              |
| `prefix`               | `str`              | The command prefix to show in usage hints. Defaults to `"!"`.                                   |
| `description`          | `str`              | The description that will be displayed in the help command.                                     |

Options marked with an asterisk (`*`) are required.

## Usage

To use this command, enable it by adding it to the `CommandHandler.commands` section in the `config.py` file.

```python
PLUGINS_CONFIG = {
    "CommandHandler": {
        "prefix": "!",
        "check_interval": 1,
        "commands": {
            "Poll": {
                "trigger": "poll",
                "description": "Create and vote in polls and surveys.",
                "polls_dir": "polls",
                "max_options": 10,
                "max_question_length": 200,
                "default_duration": None,
                "notify_users": True,
                "notify_query_clients": False,
                "prefix": "!",
            },
        },
    },
}
```

## Syntax

Every subcommand can be written in full or as a single-letter shortcut.

```text
create <question> | <option> | <option> [--duration 5m] [--anonymous] [--multi] [--server|--channel]
c <question> | <option> | <option> [flags]
vote <id> <letters>
v <id> <letters>
results <id>
r <id>
list [all]
l [all]
end <id>
e <id>
close <id>
delete <id>
d <id>
help
h
```

- `create` starts a new poll. The question and options are separated by `|`.
- `vote` records or replaces your vote.
- `results` shows the current results.
- `list` shows open polls. Add `all` to include ended polls.
- `end` (or `close`) ends a poll and announces the results.
- `delete` removes an ended poll.
- `help` shows the command usage.

### Poll IDs

Poll IDs are three characters long, lowercase, and unambiguous. Characters that are easily confused, such as `i`, `l`, `o`, `0`, and `1`, are not used. IDs are case-insensitive, so `ABC` and `abc` refer to the same poll.

### Option IDs

Options are identified by single letters `a` through `z`. Numbers are not valid option IDs.

### Multi-choice input

For multi-choice polls, `ac`, `a,c`, and `a c` are equivalent and all select options `a` and `c`.

## Scope

By default, the scope is where the command is typed:

- A channel message creates a channel poll for that channel.
- A private or server message creates a server-wide poll.

Use `--server` or `--channel` to override the scope. `--channel` uses the invoker's current channel. `--server` and `--channel` cannot be combined.

## Creating a poll

When a poll is created, the announcement is posted in server or channel chat. In addition, everyone in scope receives a private message with the announcement:

- For server polls, every connected user is notified.
- For channel polls, only members of that channel are notified.

The bot, the connection that created the poll, and ServerQuery clients are excluded by default. Set `notify_query_clients` to `True` to include ServerQuery clients.

## Voting

Each user has one vote per poll. A second vote replaces the first, so voters can change their choice.

Anonymous polls hide voter identities in chat and results. The JSON file stores only a per-poll SHA-256 hash of the voter ID. Public polls show voter names in the results.

## Time limits

Use `--duration` with a value such as `30s`, `5m`, `2h`, or `1d`. The `default_duration` configuration option applies when `--duration` is omitted.

Expired polls end automatically. The results are announced in scope and sent as a private message to the creator and to connected voters.

## Results

Anyone who knows the poll code can view the results with `results <id>`. Results include counts, percentages, the total number of voters, and, once a poll has ended, the winner or winners.

## Deleting a poll

Only the poll creator can delete a poll, and only after it has ended.

## Persistence

Polls are stored as one JSON file per poll at `polls/<id>.json`. Each file contains the poll and a results snapshot. Writes are atomic, closed polls are retained, and corrupt files are skipped when the store is loaded.

A stored poll looks like this:

```json
{
  "schema_version": 1,
  "id": "abc",
  "question": "Lunch?",
  "options": ["Pizza", "Sushi"],
  "created_at": "2026-11-12T12:00:00+00:00",
  "expires_at": null,
  "closed": false,
  "closed_at": null,
  "anonymous": false,
  "multi_choice": false,
  "scope": "server",
  "channel_id": null,
  "channel_name": null,
  "creator": {
    "uid": "creator-uid",
    "name": "Creator"
  },
  "votes": {
    "voter-uid": [0]
  },
  "voter_names": {
    "voter-uid": "Alice"
  },
  "results": {
    "counts": [1, 0],
    "percentages": [100.0, 0.0],
    "total_voters": 1,
    "total_selections": 1,
    "winner": [0]
  }
}
```

## Limitations

- Options cannot contain `|`, because it is used as the separator.
- A poll can have at most 26 options, one for each letter of the alphabet.
- Private message fan-out is paced by the query flood protection, so notifying many users can take a while.
- Users who join after a poll is created see the chat announcement but do not receive a retroactive private message.
