# TS3Query

The `TS3Query` class facilitates communication with the TeamSpeak 3 ServerQuery interface by establishing a
connection to the server upon instantiation.

If login credentials are provided, the client is automatically logged in.

This class provides methods for logging in and out, sending commands to the server, and exiting the server.

Responses from the server are received and parsed into a `TS3QueryResponse` object using the `_receive()` method,
which is used internally.

To prevent race conditions, the class uses a thread-safe locking mechanism, and flood protection is implemented
primarily to prevent the server from being flooded with too many requests and receiving errors as a result.

The `TS3Query` class works in conjunction with other classes from the ts3query module, including CommandsWrapper,
TS3QueryCommand, and `TS3QueryResponse`.

## Note

It is important to note that the `TS3Query` class is a rather low-level implementation,
providing direct access to the TeamSpeak 3 ServerQuery interface.

As such, it requires a deep understanding of the protocol and its intricacies to use effectively.

For this reason, it is recommended to use the `TS3Client` class instead, which provides a higher-level abstraction
and simplifies the process of interacting with the TeamSpeak 3 server.

The `TS3Client` class is built on top of the `TS3Query` class and provides a more intuitive interface
for performing common tasks such as joining channels, moving clients and sending messages.

This is particularly important because the TeamSpeak 3 ServerQuery interface can behave unintuitively at times,
which can lead to unexpected results if not handled properly. By using the `TS3Client` class,
developers can abstract away these complexities and focus on their application logic,
which leads to more efficient development and more maintainable code.

## Methods

### Public methods

- `__init__(host: str, port: int, login: str = None, password: str = None, timeout=10, logger: logging.Logger = None)`:
Initializes a new TS3Query instance with a given host, port, and optionally, login and password to be used for
authentication. A logger object can also be optionally passed for logging purposes.
- `connected()`: Checks whether the query client is connected to the TeamSpeak 3 server.
- `login(login: str, password: str)`: Attempts to login to the TeamSpeak 3 server with the given login and password.
- `logout()`: Attempts to logout from the TeamSpeak 3 server.
- `exit()`: Exits the server, closes the connection, and stops polling.
- `send(command: TS3QueryCommand)`: Sends a command to the server and returns the server's response.
- `start_polling(polling_rate: int)`: Starts polling the server for events and messages with a given polling rate.
- `stop_polling()`: Stops polling the server for events and messages.
- `enable_flood_protection()`: Enables flood protection.
- `disable_flood_protection()`: Disables flood protection.
- `set_messages_limit(limit: int)`: Sets the maximum number of messages the client can store.
- `set_events_limit(limit: int)`: Sets the maximum number of events the client can store.

### Private methods

The private methods are intended for internal use only and should not be accessed publicly.

- `__del__()`: Closes the connection and exits the server.
- `_receive()`: Receives and parses the server's response to a previously sent command.
- `_poll(stop: threading.Event, polling_rate: float)`: Polls the server for events and messages with a given
polling rate.
- `_add_events(events: list[Event], limit: int)`: Adds the received events to the events list,
trimming it if it exceeds the limit.
- `_add_messages(messages: list[Message], limit: int)`: Adds the received messages to the messages list,
trimming it if it exceeds the limit.
- `_skip_greeting()`: Skips the initial welcome message received from the TeamSpeak 3 ServerQuery interface.

### Properties

- `flood_protection -> bool`: Retrieves whether flood protection is enabled or not.
- `messages -> list[Message]`: Retrieves a list of all messages the client has received.
- `messages_limit -> int`: Retrieves the maximum number of messages the client can store.
- `unread_messages -> list[Message]`: Retrieves a list of all unread messages the client has received.
- `events -> list[Event]`: Retrieves a list of all events the client has received.
- `events_limit -> int`: Retrieves the maximum number of events the client can store.
- `unread_events -> list[Event]`: Retrieves a list of all unread events the client has received.
