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

Developers can extend the bot by creating new plugins. 
To create a new plugin, create a new Python module in the plugins directory, 
and define a subclass of the `Plugin` class defined in `plugin.py`. 

The new plugin class must implement a method named `run`.
The `run` method is the method that will be called by the bot when the plugin is initialized. 
This method should perform the specific task of the plugin, such as fetching data from an API or processing user input.

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
The plugins configuration file `config.py` allows you to customize the behavior of plugins in the TeamSpeak 3 bot. 

Each plugin is configured using a dictionary with the name of the plugin class as the key, 
and a dictionary of configuration options as the value. 

For example, the following code configures the `AFK_Mover` plugin:

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