# Weather

This command uses the [WeatherAPI](https://www.weatherapi.com/) to fetch the current weather for a given location.

## Configuration

The following configuration options are available:

| Option     | Type  | Description                                          |
| ---------- | ----- | ---------------------------------------------------- |
| `trigger`* | `str` | The trigger that will be used to invoke the command. |
| `api_key`* | `str` | The API key that will be used to fetch weather data. |

Options marked with an asterisk (`*`) are required.

## Usage

To use this command, simply enable it by adding it to `CommandHandler.commands` section in the `config.py` file.

```python
PLUGINS_CONFIG = {
    "CommandHandler": {
        "prefix": "!",
        "check_interval": 1,
        "commands": {
            "Weather": {
                "trigger": "weather",
                "api_key": os.getenv("WEATHERAPI_COM_API_KEY"),
                "description": "Get the weather for a location.",
            },
        },
    },
}
```

## Notes

- This command requires an API key from [WeatherAPI](https://www.weatherapi.com/). You can get a free API key by signing up for an account on their website. Once you have an API key, you can set it as an environment variable named `WEATHERAPI_COM_API_KEY` or replace `os.getenv("WEATHERAPI_COM_API_KEY")` with your API key in the `config.py` file.
