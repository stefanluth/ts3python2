# TS3Client

## Introduction

The `TS3Client` class provides a high-level abstraction for interacting with the TeamSpeak 3 server.

It is built on top of the `TS3Query` class and provides a more intuitive interface for performing common tasks such
as moving users, receiving and sending messages. The client uses SSH ServerQuery on port `10022` by default.

## Initialization

If no host, port, or SSH login and password are provided, the TS3Client will not connect to a server. Instead you can
use the `TS3Client.connect()` method to connect to a server.
The SSH credentials authenticate when the connection is established; there is no separate login or logout step.

The SSH host key is verified by default. Pass `known_hosts` to use a specific known hosts file,
`use_system_host_keys=False` to skip the system known hosts file, or `accept_all_keys=True` to disable verification.
`accept_all_keys` is intended for first-run testing only. Pin the host key with:

```bash
ssh-keyscan -p 10022 host > known_hosts
```

## Methods

### Public methods

- `__init__(host: str = None, port: int = None, login: str = None, password: str = None, timeout: int = 10, logger: logging.Logger = None, known_hosts: str = None, accept_all_keys: bool = False, use_system_host_keys: bool = True)`:
Initializes a new TS3Client instance with a given host, SSH query port, and SSH login and password to be used for
authentication. `known_hosts`, `accept_all_keys`, and `use_system_host_keys` control SSH host key verification. A
logger object can also be optionally passed.
- `whoami()`: Returns information about the client (the bot).
- `connect(host: str, port: int, login: str, password: str, timeout: int = 10, known_hosts: str = None, accept_all_keys: bool = False, use_system_host_keys: bool = True)`:
Connects to a TeamSpeak 3 server over SSH with the given credentials.
- `disconnect()`: Disconnects from the TeamSpeak 3 server.
- `select_server(id: int)`: Selects a server by its ID.
- `select_server_by_port(port: int)`: Selects a server by its port.
- `set_name(name: str)`: Sets the client's nickname.
- `set_description(description: str)`: Sets the client's description.
- `get_users()`: Returns a list of all users on the server.
- `get_user_info(id: int)`: Returns information about a user by its ID.
- `find_user(name: str)`: Returns users whose nickname matches the given name.
- `rename_user(id: int, name: str)`: Renames a user by its ID.
- `move_user(id: int, channel_id: int, channel_pw: str = None)`: Moves a user by its ID to a channel by its ID.
Optionally, a channel password can be provided to move the user to a password-protected channel.
- `kick_user_from_channel(id: int, reason: str = None)`: Kicks a user by its ID from the channel they are in.
Optionally, a reason can be provided.
- `kick_user_from_server(id: int, reason: str = None)`: Kicks a user by its ID from the server.
Optionally, a reason can be provided.
- `ban_user(id: int, time: int, reason: str = None)`: Bans a user by its ID for a given amount of time.
Optionally, a reason can be provided.
- `get_channels()`: Returns a list of all channels on the server.
- `get_channel_info(id: int)`: Returns information about a channel by its ID.
- `find_channel(name: str)`: Returns channels whose name matches the given name.
- `get_messages()`: Returns a list of all messages received by the bot.
- `get_unread_messages()`: Returns a list of all unread messages received by the bot.
- `get_events()`: Returns a list of all events received by the bot.
- `get_unread_events()`: Returns a list of all unread events received by the bot.
- `get_user_entered_events()`: Returns a list of all unread user entered events received by the bot.
- `send_server_message(message: str)`: Sends a message to the server.
- `send_channel_message(message: str)`: Sends a message to the channel the bot is in.
- `send_private_message(id: int, message: str)`: Sends a private message to a user by its ID.
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

- `name`: The client's nickname.
- `description`: The client's description.
- `id`: The client's ID.
- `unique_id`: The client's unique ID.
- `database_id`: The client's database ID.
- `server_id`: The server ID.
- `server_unique_id`: The server unique ID.
- `server_name`: The server name.
- `server_port`: The server port.
