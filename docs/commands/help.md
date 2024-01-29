# Help

This command is used to display information and usage instructions for other commands.

## Configuration

The following configuration options are available:

| Option        | Type  | Description                                                 |
| ------------- | ----- | ----------------------------------------------------------- |
| `trigger`*    | `str` | The trigger that will be used to invoke the command.        |
| `description` | `str` | The description that will be displayed in the help command. |

Options marked with an asterisk (`*`) are required.

## Usage

To use this command, simply enable it by adding it to `CommandHandler.commands` section in the `config.py` file.

```python
PLUGINS_CONFIG = {
    "CommandHandler": {
        "prefix": "!",
        "check_interval": 1,
        "commands": {
            "Help": {
                "trigger": "help",
                "description": "Send a list of available commands.",
            },
        },
    },
}
```

## Notes

/
