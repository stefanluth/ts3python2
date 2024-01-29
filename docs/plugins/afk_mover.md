# AFK Mover

This plugin moves users to a specified channel when they are inactive for a given amount of time.

## Configuration

The following configuration options are available:

| Option            | Type        | Description                                                        |
| ----------------- | ----------- | ------------------------------------------------------------------ |
| `afk_channel_id`* | `int`       | The ID of the channel to which users will be moved.                |
| `afk_time`*       | `int`       | The amount of time (in seconds) after which users will be moved.   |
| `check_interval`  | `int`       | The amount of time (in seconds) between checks for inactive users. |
| `ignore_channels` | `list[int]` | A list of channel IDs that will be ignored by the plugin.          |
| `move_message`    | `str`       | The message that will be sent to users when they are moved.        |

Options marked with an asterisk (`*`) are required.

## Usage

To use this plugin, simply enable it by adding it to the `config.py` file.

```python
PLUGINS_CONFIG = {
    "AFK_Mover": {
        "afk_channel_id": 357515,
        "afk_time": 30 * 60,
        "check_interval": 5,
        "ignore_channels": [425000, 357512, 357513, 357514],
    }
}
```

## Notes

- The `check_interval` configuration option is optional and defaults to `1`.
- The `ignore_channels` configuration option is optional and defaults to `[]`.
- The `move_message` configuration option is optional and defaults to `"You have been moved to the AFK channel."`.
