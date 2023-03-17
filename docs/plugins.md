# Plugins

```text
plugins
├── __init__.py
├── afk_mover.py
├── plugin_manager.py
├── plugin.py
└── plugins.py
```

## AFK Mover: `plugins/afk_mover.py`

The AFK Mover plugin moves users who are idle in a specified AFK channel to their original channel
after a specified amount of time.

The AFK Mover plugin is an example of how to create plugins for the Teamspeak bot.
It can be used as a guide for other developers who want to create their own plugins for the bot.

## Plugin Manager: `plugins/plugin_manager.py`

This module is responsible for managing the plugins.
It reads the configuration for the plugins, creates instances of the plugins, and starts them in separate threads.

## Plugin: `plugins/plugin.py`

This module defines the `Plugin` class that all plugins must inherit from.

The `Plugin` class is the base class that provides a structure for creating new plugins.
It contains various methods that can be overridden to customize the plugin's behavior.

The most important method is the `run` method.
This is the method that will be called when the plugin is initialized,
and it should perform the specific task of the plugin.

For example, if the plugin is designed to respond to certain commands,
the `run` method might listen for incoming messages and respond appropriately.

## Plugins: `plugins/plugins.py`

This module contains the available plugins.

## How to extend

You can extend the bot by creating new plugins.

To do this, you need to create a new Python module in the `plugins` directory and define a subclass of
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

## Plugin Configuration: `config.py`

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
