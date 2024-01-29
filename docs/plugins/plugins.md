# Plugins

In this directory, you'll find plugins that are ready to be used and everything you need to know about writing plugins.

## Creating a Plugin

You can extend the bot by creating new plugins.

To do this, you need to create a new Python file in the `plugins` directory and define a subclass of
the `Plugin` class located in `plugin.py`.

```python
from ..plugin import Plugin

class MyPlugin(Plugin):
```

The new plugin class must implement a method named `run`, which is then
automatically called by the bot/plugin manager when the plugin is initialized.
This method should perform the specific task of the plugin, such as fetching data from an API or processing user input.

```python
from ..plugin import Plugin


class MyPlugin(Plugin):
    def run(self):
        # do something
```

To listen for events or perform periodic actions, plugins need to run continuously.
To ensure the loop doesn't run indefinitely, you can use the `event` property of the `Plugin` class to stop it.

To provide the functionality to stop the loop gracefully when the plugin manager wants it to stop,
you can use the following code:

```python
from ..plugin import Plugin


class MyPlugin(Plugin):
    def run(self):
        while not self.event.is_set():
            # do something or listen for events
            # i.e. the main functionality of your plugin
            self.event.wait(interval)
```

_Note: In the example code provided, `self.event.wait(interval)` is used to pause the execution of the loop
for a given interval. Using a too short or too long interval can impact the performance of your plugin
and the overall responsiveness of the bot._

The `PluginManager.stop()` method automatically sets the `event` which will stop the plugin.
Alternatively, you can manually set `event` yourself using the following line somewhere in your code:

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

Replace `my_plugin` with the name of your plugin module, and `MyPlugin` with the name of your plugin class.

Once you've completed these steps, your new plugin should be ready and can now be enabled in the `config.py` file.

### Plugin Configuration: `config.py`

When developing plugins, configuration options can be provided in the configuration file named `config.py`.
This allows for easy customization of the plugin's behavior without requiring changes to the plugin's code.

The configuration for each plugin is specified in the `PLUGINS_CONFIG` dictionary,
where the name of the plugin class serves as the key and a dictionary of configuration options serves as the value.

See this example configuration specified in the `config.py` file for the `AFK_Mover` plugin:

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

These correspond to the arguments of the `run` method of the `AFK_Mover` plugin:

```python
class AFK_Mover(Plugin):
    def run(
        self,
        afk_channel_id: int,
        afk_time: int,
        check_interval: int = 1,
        ignore_channels: list[int] = [],
        move_message: str = "You have been moved to the AFK channel.",
    ):
        # do something
```

The `afk_channel_id` and `afk_time` configuration options are the only ones required for the `AFK_Mover` plugin to work.
The other configuration options are optional as they have default values specified in the `run` method.
