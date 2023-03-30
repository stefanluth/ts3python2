# TS3Client

## Introduction

The `TS3Client` class provides a high-level abstraction for interacting with the TeamSpeak 3 server.

It is built on top of the `TS3Query` class and provides a more intuitive interface for performing common tasks such
as moving clients, receiving and sending messages.

## Initialization

If no host and port are provided, the TS3Client will not connect to a server. Instead you can use the
`TS3Client.connect()` method to connect to a server.
If no login and password are provided, the query client will not be logged in.
You can login with the `TS3Client.login()` method after the TS3Client has been instantiated instead.

## Methods

### Public methods

- `__init__(host: str = None, port: int = None, login: str = None, password: str = None, timeout: int = 10, logger: logging.Logger = None)`:
Initializes a new TS3Client instance with a given host, port, and optionally, login and password to be used for
authentication. A logger object can also be optionally passed.
- `whoami()`: Returns information about the client (the bot).
- `connect(host: str, port: int, timeout: int = 10)`: Connects to a TeamSpeak 3 server.
- `disconnect()`: Disconnects from the TeamSpeak 3 server.
- `login(login: str, password: str)`: Attempts to login to the TeamSpeak 3 server with the given login and password.
- `logout()`: Attempts to logout from the TeamSpeak 3 server.
- `select_server(id: int)`: Selects a server by its ID.
- `select_server_by_port(port: int)`: Selects a server by its port.
- `set_name(name: str)`: Sets the client's (the bot's) nickname.
- `set_description(description: str)`: Sets the client's (the bot's) description.
- `get_clients()`: Returns a list of all clients on the server.
- `get_client_info(id: int)`: Returns information about a client by its ID.
- `find_client(name: str)`: Returns clients whose nickname matches the given name.
- `rename_client(id: int, name: str)`: Renames a client by its ID.
- `move_client(id: int, channel_id: int, channel_pw: str = None)`: Moves a client by its ID to a channel by its ID.
Optionally, a channel password can be provided to move the client to a password-protected channel.
- `kick_client_from_channel(id: int, reason: str = None)`: Kicks a client by its ID from the channel they are in.
Optionally, a reason can be provided.
- `kick_client_from_server(id: int, reason: str = None)`: Kicks a client by its ID from the server.
Optionally, a reason can be provided.
- `ban_client(id: int, time: int, reason: str = None)`: Bans a client by its ID for a given amount of time.
Optionally, a reason can be provided.
- `get_channels()`: Returns a list of all channels on the server.
- `get_channel_info(id: int)`: Returns information about a channel by its ID.
- `find_channel(name: str)`: Returns channels whose name matches the given name.
- `get_messages()`: Returns a list of all messages received by the bot.
- `get_unread_messages()`: Returns a list of all unread messages received by the bot.
- `get_events()`: Returns a list of all events received by the bot.
- `get_unread_events()`: Returns a list of all unread events received by the bot.
- `get_client_entered_events()`: Returns a list of all unread client entered events received by the bot.
- `send_server_message(message: str)`: Sends a message to the server.
- `send_channel_message(message: str)`: Sends a message to the channel the bot is in.
- `send_private_message(client_id: int, message: str)`: Sends a private message to a client by its ID.
- `send_message(target: int, target_mode: TargetMode, message: str)`: Sends a message to a target with a given target mode.
- `enable_message_events()`: Enables receiving message events.
- `disable_message_events()`: Disables receiving message events.
- `enable_server_events()`: Enables receiving server events.
- `disable_server_events()`: Disables receiving server events.
- `enable_channel_events()`: Enables receiving channel events.
- `disable_channel_events()`: Disables receiving channel events.
- `enable_events_and_messages()`: Enables receiving events and messages.
- `disable_events_and_messages()`: Disables receiving events and messages.
- `start_polling()`: Starts polling for events and messages.
- `stop_polling()`: Stops polling for events and messages.

### Public properties

- `name`: The client's (the bot's) nickname.
- `id`: The client's ID.
- `unique_id`: The client's unique ID.
- `database_id`: The client's database ID.
- `server_id`: The server ID.
- `server_unique_id`: The server unique ID.
- `server_name`: The server name.
- `server_port`: The server port.
