# Plugins

```text
plugins
├── command.py
├── commands
│   ├── __init__.py
│   └── help.py
│   └── weather.py
├── plugin_manager.py
├── plugin.py
└── plugins
    ├── __init__.py
    ├── afk_mover.py
    ├── command_handler.py
    └── welcomer.py
```

## Files

### Commands Bundle: `commands/__init__.py`

This file should import all commands contained in the `commands` directory and the imported class name should be
added to the `__all__` variable.

### Help Command: `commands/help.py`

The Help command, triggered by `!help` or `!help <command>`,
returns a list of available commands.

### Weather Command: `commands/weather.py`

The Weather command, triggered by `!weather <location>`,
fetches the current weather for a given location and returns it to the user.

The Weather command is an example of how to create commands for the Teamspeak bot.
It can be used as a guide for other developers who want to create their own commands for the bot.

The configuration options, e.g. the command trigger for the Weather command are specified in the `config.py` file.

### Plugins Bundle: `plugins/__init__.py`

This file should import all plugins contained in the `plugins` directory and the imported class name should be
added to the `__all__` variable.

### AFK Mover Plugin: `plugins/afk_mover.py`

The AFK Mover plugin moves users who are idle in a specified AFK channel to their original channel
after a specified amount of time.

The AFK Mover plugin is an example of how to create plugins for the Teamspeak bot.
It can be used as a guide for other developers who want to create their own plugins for the bot.

### Command Handler Plugin: `plugins/command_handler.py`

The Command Handler plugin listens for messages that start with the command trigger and
passes the message to the specific command for processing.

### Welcomer Plugin: `plugins/welcomer.py`

The Welcomer plugin messages users who join the server with a custom message.

The Welcomer plugin is an example of how to create plugins for the Teamspeak bot.
It can be used as a guide for other developers who want to create their own plugins for the bot.

### Command: `command.py`

This file defines the `Command` class that all commands must inherit from.

The `Command` class is the base class that provides a structure for creating new commands.
It contains various methods that can be overridden to customize the command's behavior.

The most important method is the `run` method.
This is the method that will be called when the command is triggered,
and it should perform the specific task of the command.

For example, if the command is designed to respond to a user's input, e.g. `!weather <location>`,
the `run` method should parse the user's input and perform the appropriate action.

### Plugin Manager: `plugin_manager.py`

This module is responsible for managing the plugins.
It reads the configuration for the plugins, creates instances of the plugins, and starts them in separate threads.

### Plugin: `plugin.py`

This file defines the `Plugin` class that all plugins must inherit from.

The `Plugin` class is the base class that provides a structure for creating new plugins.
It contains various methods that can be overridden to customize the plugin's behavior.

The most important method is the `run` method.
This is the method that will be called when the plugin is initialized,
and it should perform the specific task of the plugin.

For example, if the plugin is designed to respond to certain events, e.g. a user joining the server,
the `run` method should listen for these events and perform the appropriate action.

## How to extend

### Creating a Plugin

You can extend the bot by creating new plugins.

To do this, you need to create a new Python file in the `plugins` directory and define a subclass of
the `Plugin` class located in `plugin.py`. The new plugin class must implement a method named `run`, which is called
by the bot/plugin manager when the plugin is initialized. This method should perform the specific task
of the plugin, such as fetching data from an API or processing user input.

To listen for events or perform periodic actions, plugins need to run continuously.
To ensure the loop doesn't run indefinitely, you can use the `event` property of the `Plugin` class to stop it.

To provide the functionality to stop the loop gracefully when the plugin manager wants it to stop,
you can use the following code:

```python
def run(self):
    while not self.event.is_set():
        # do something or listen for events
        # i.e. the main functionality of your plugin
        time.sleep(interval)
```

_Note: In the example code provided, `time.sleep(interval)` is used to pause the execution of the loop
for a given interval. Using a too short or too long interval can impact the performance of your plugin
and the overall responsiveness of the bot._

The `PluginManager.stop()` method automatically sets the `event` which will stop the plugin.
Alternatively, you can manually set `event` yourself using the following code:

```python
self.event.set()
```

This will stop the loop at the next iteration.

After creating your plugin class, you'll need to import the class in the `plugins.py` file and
add it to the `__all__` list to make it available to the bot.

```python
from .afk_mover import AFK_Mover
from .my_plugin import MyPlugin

__all__ = ["AFK_Mover", "MyPlugin"]
```

Replace my_plugin with the name of your plugin module, and MyPlugin with the name of your plugin class.

Once you've completed these steps, your new plugin should be available to the bot and
can be enabled by adding it to the `PLUGINS_CONFIG` in the `config.py` file.

### Plugin Configuration: `config.py`

When developing plugins, configuration options can be provided in the configuration file named `config.py`.
This allows for easy customization of the plugin's behavior without requiring changes to the plugin's code.

The configuration options for each plugin are specified in a dictionary format,
where the name of the plugin class serves as the key and a dictionary of configuration options serves as the value.
These configuration options can then be passed as arguments to the `run` method of the plugin class.

For example, in the `AFK_Mover` plugin, the `run` method takes the following arguments:

```python
def run(
    self,
    afk_channel_id: int,
    afk_time: int,
    check_interval: int = 1,
    ignore_channels: list[int] = [],
    move_message: str = "You have been moved to the AFK channel.",
)
```

These arguments correspond to the configuration options specified in the `config.py` file for the `AFK_Mover` plugin:

```python
PLUGINS_CONFIG = {
    "AFK_Mover": {
        "afk_channel_id": 357515,
        "afk_time": 30 * 60,
        "check_interval": 5,
        "ignore_channels": [425000, 357512, 357513, 357514],
    },
}
```

The `afk_channel_id` and `afk_time` configuration options are required for the `AFK_Mover` plugin to work.
The other configuration options are optional and have default values specified in the `run` method.

### Creating a Command

You can extend the bot by creating new commands.

To do this, you need to create a new Python file in the `commands` directory and define a subclass of
the `Command` class located in `command.py`. The new command class must implement a method named `run`, which is called
by the bot/command handler when the command is triggered. This method should perform the specific task
of the command, such as fetching data from an API or processing user input.

The Command Manager will automatically pass the `Message` object to the `run` method when the command is triggered.

The `run` method must only take the following arguments:

```python
def run(self, message: Message):
```

The `message` argument is an instance of the `Message` class located in `ts3client/message.py`.
This class contains various properties that can be used to access the message's data.

For example, the `message.content` property contains the text of the message.
The `message.invokerid` property contains the ID of the user who sent the message.
The `message.invokername` property contains the name of the user who sent the message.

So if you wanted to respond to the user who sent the message, you could use the following code:

```python
def run(self, message: Message):
    self.client.send_private_message(
        message.invokerid,
        f"Hello {message.invokername}, I'm a bot!",
    )
```

The configuration options for each command are specified in a dictionary format inside the
`CommandHandler` configuration, within the `commands` dictionary.

The name of the command class serves as the key and a dictionary of configuration options serves as the value.

```python
    "CommandHandler": {
        "prefix": "!",
        "check_interval": 1,
        "commands": {
            "Weather": {
                "trigger": "weather",
                "api_key": os.getenv("WEATHERAPI_COM_API_KEY"),
            },
        },
    },
```

The trigger for the command is specified in the `trigger` configuration option.
Other configuration options can be specified in the same dictionary and will be passed to the `run` method
as seen in the Weather plugin example.
