# Welcomer

This plugin sends a welcome message to users when they join the server.

## Configuration

The following configuration options are available:

| Option      | Type        | Description                                                   |
| ----------- | ----------- | ------------------------------------------------------------- |
| `messages`* | `list[str]` | A list of choices from which a random message will be chosen. |

Options marked with an asterisk (`*`) are required.

## Usage

To use this plugin, simply enable it by adding it to the `config.py` file.

```python
PLUGINS_CONFIG = {
    "Welcomer": {
        "messages": ["Howdy!", "Hi there!"],
    },
}
```

## Notes

/
