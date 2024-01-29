# Commands

You can also extend the bot by creating new commands. Commands are triggered by a specific message sent by a user.

## Creating a Command

Creating a new command is similar to creating a new plugin.

First, you need to create a new Python file in the `commands` directory and define a subclass of the `Command` class.

```python
from ..command import Command

class MyCommand(Command):
```

The new command class must implement a method named `run`,
which is called by the bot/command handler when the command is triggered.
This method should perform the specific task of the command,
such as fetching data from an API or processing user input.

```python
from ..command import Command

class MyCommand(Command):
    def run(self, message: Message):
        # do something
```

The Command Manager will automatically pass the `Message` object to the `run` method when the command is triggered.

The `run` method must only take the `message` argument.

The `message` argument is an instance of the `Message` class located in `ts3client/message.py`.
This class contains various properties that can be used to access the message's data.

For example, the `message.content` property contains the text of the message.
The `message.invokerid` property contains the ID of the user who sent the message.
The `message.invokername` property contains the name of the user who sent the message.

So if you wanted to respond to the user who sent the message, you could use the following code:

```python
from ..command import Command

class MyCommand(Command):
    def run(self, message: Message):
        self.client.send_private_message(
            message.invokerid,
            f"Hello {message.invokername}, I'm a bot!",
        )
```

After creating your command class, you'll need to import the class in the `commands/__init__.py` file and
add it to the `__all__` list to make it available to the bot.

```python
from .weather import Weather
from .my_command import MyCommand

__all__ = ["Weather", "MyCommand"]
```

Replace `my_command` with the name of your command module, and `MyCommand` with the name of your command class.

Once you've completed these steps, your new command should be ready and can now be enabled in the `config.py` file.

### Command Configuration: `config.py`

Enable your command by simply adding it to the `commands` dictionary within the `CommandHandler` configuration in the
`config.py` file, as seen in the example below.

```python
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
```

The trigger for the command is specified in the aptly named `trigger` configuration option and is the only option
required for a command to work.

Other configuration options can be specified in the same dictionary and will be passed to the `__init__` method.
For this, you'll need to add an `__init__` method to your command class, as seen in the `Weather` plugin example,
where the `api_key` is passed to the `__init__` method:

```python
class Weather(Command):
    def __init__(self, client: TS3Client, trigger: str, api_key: str, *args, **kwargs):
        super().__init__(client, trigger)
        self.api_key = api_key
```

_Note: The `client` argument is automatically passed to the `__init__` method by the Command Handler and
should not be specified in the configuration options._

_Note: The `client` and `trigger` arguments must be passed to the `super().__init__` method._

_Note: The `description` configuration option is optional and is used to provide a description of the command
that can be used by the `help` command. If you don't provide a `description`, the `*args, **kwargs` arguments can be
removed from the `__init__` method._
