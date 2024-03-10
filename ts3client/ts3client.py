import logging
from typing import Optional

from .channel import Channel, ChannelInfo
from .constants import NotifyRegisterType, ReasonIdentifier, TargetMode
from .event import ClientEnterViewEvent, Event
from .message import Message
from .ts3client_response import TS3ClientResponse
from .ts3query import TS3Query
from .user import User, UserInfo
from .utils.logger import create_logger


class TS3Client:
    """A higher level abstraction of the TS3Query class.
    If no host and port are provided, the TS3Client will not connect to a server.
    Instead you can use the TS3Client.connect() method to connect to a server.
    If no login and password are provided, the query client will not be logged in.
    You can login with the TS3Client.login() method after the TS3Client has been instantiated instead.

    :param host: The host of the TeamSpeak 3 server, defaults to None.
    :type host: str, optional
    :param port: The port of the TeamSpeak 3 server, defaults to None
    :type port: int, optional
    :param login: The login of the TeamSpeak 3 server, defaults to None
    :type login: str, optional
    :param password: The password of the TeamSpeak 3 server, defaults to None
    :type password: str, optional
    :param timeout: The timeout of the TeamSpeak 3 server, defaults to 10
    :type timeout: int, optional
    """

    query: Optional[TS3Query] = None

    def __init__(
        self,
        host: str = None,
        port: int = None,
        login: str = None,
        password: str = None,
        timeout: int = 10,
        logger: logging.Logger = None,
    ) -> None:
        self.logger = logger or create_logger("TS3Client", "logs/main.log")
        if not host or not port:
            self.logger.info("No host and/or port provided, not connecting to a server")
            return

        self.connect(host, port, timeout)

        if not login or not password:
            self.logger.info("No login and/or password provided, not logging in")
            return

        self.login(login, password)
        self.enable_message_events()

    def whoami(self) -> TS3ClientResponse:
        return TS3ClientResponse(self.query.commands.whoami())[0]

    @property
    def name(self) -> str:
        """Get the client's nickname."""
        return self.whoami().get("client_nickname")

    @property
    def description(self) -> str:
        """Get the client's description."""
        return self.whoami().get("client_description")

    @property
    def id(self) -> int:
        """Get the client's ID."""
        return self.whoami().get("client_id")

    @property
    def unique_id(self) -> str:
        """Get the client's unique ID."""
        return self.whoami().get("client_unique_identifier")

    @property
    def database_id(self) -> int:
        """Get the client's database ID."""
        return self.whoami().get("client_database_id")

    @property
    def server_id(self) -> int:
        """Get the client's server ID."""
        return self.query.commands.serverinfo().data[0].get("virtualserver_id")

    @property
    def server_unique_id(self) -> str:
        """Get the client's server unique ID."""
        return self.query.commands.serverinfo().data[0].get("virtualserver_unique_identifier")

    @property
    def server_name(self) -> str:
        """Get the client's server name."""
        return self.query.commands.serverinfo().data[0].get("virtualserver_name")

    @property
    def server_port(self) -> int:
        """Get the client's server port."""
        return self.query.commands.serverinfo().data[0].get("virtualserver_port")

    def connect(self, host: str, port: int, timeout: int = 10) -> None:
        """Connect to a TeamSpeak 3 server.

        :param host: Hostname or IP address of the TeamSpeak 3 server.
        :type host: str
        :param port: UDP port of the TeamSpeak 3 server.
        :type port: int
        :param timeout: Timeout for the connection, defaults to 10.
        :type timeout: int, optional
        """
        self.logger.info(f"Connecting to {host}:{port}...")
        self.query = TS3Query(host, port, timeout)
        self.logger.info("Connected")

    def disconnect(self) -> None:
        """Disconnect from the TeamSpeak 3 server."""
        self.logger.info("Disconnecting...")
        if self.query is None:
            return
        self.query.exit()
        self.query = None

    def login(self, login: str, password: str) -> None:
        """Login to the TeamSpeak 3 server.

        :param login: Username to login with.
        :type login: str
        :param password: Password to login with.
        :type password: str
        """
        self.logger.info(f"Logging in as {login}...")
        self.query.login(login, password)
        self.logger.info("Logged in")

    def logout(self) -> None:
        """Logout from the TeamSpeak 3 server."""
        self.query.logout()

    def select_server(self, id: int) -> None:
        """Use a server ID to connect to a server.

        :param id: Database ID of the virtual server to connect to.
        :type id: int
        """
        self.query.commands.use(sid=id)

    def select_server_by_port(self, port: int = 9987) -> None:
        """Use a server port to connect to a server.

        :param port: UDP port the virtual server is listening on. (Default: 9987)
        :type port: int
        """
        self.query.commands.use(port=port)

    def set_name(self, name: str) -> TS3ClientResponse | None:
        """Set the name of the TS3Client.

        :param name: New name of the client.
        :type name: str
        :return: Response from the server or None if the name is the same.
        :rtype: TS3ClientResponse | None
        """
        if self.name == name:
            return None

        return TS3ClientResponse(self.query.commands.clientupdate(client_nickname=name))

    def set_description(self, description: str) -> TS3ClientResponse:
        """Set the description of the TS3Client.

        :param description: New description of the client.
        :type description: str
        :return: Response from the server.
        :rtype: TS3ClientResponse
        """
        return TS3ClientResponse(self.query.commands.clientedit(clid=self.id, client_description=description))

    def get_users(self) -> list[User]:
        """Get a list of all connected users.

        :return: Response from the server.
        :rtype: TS3ClientResponse
        """
        return [User(**client) for client in TS3ClientResponse(self.query.commands.clientlist(uid=True))]

    def get_user_info(self, id: int) -> UserInfo:
        """Get information about a user.

        :param id: User ID.
        :type id: int
        :return: Response from the server.
        :rtype: TS3ClientResponse
        """
        return UserInfo(**TS3ClientResponse(self.query.commands.clientinfo(clid=id))[0])

    def set_user_description(self, id: int, description: str) -> TS3ClientResponse:
        """Set the description of a user.

        :param id: User ID.
        :type id: int
        :param description: New description of the client.
        :type description: str
        :return: Response from the server.
        :rtype: TS3ClientResponse
        """

        return TS3ClientResponse(self.query.commands.clientedit(clid=id, client_description=description))

    def find_users(self, name: str) -> list[User]:
        """Find users by name.

        :param name: Name of the client.
        :type name: str
        :return: Response from the server.
        :rtype: TS3ClientResponse
        """
        return [User(**client) for client in TS3ClientResponse(self.query.commands.clientfind(pattern=name))]

    def rename_user(self, id: int, name: str) -> TS3ClientResponse:
        """Rename a user.

        :param id: User ID.
        :type id: int
        :param name: New name of the client.
        :type name: str
        :return: Response from the server.
        :rtype: TS3ClientResponse
        """
        return TS3ClientResponse(self.query.commands.clientedit(clid=id, client_nickname=name))

    def move_user(self, id: int, channel_id: int, channel_pw: Optional[str] = None) -> TS3ClientResponse:
        """Move a user to a channel.

        :param id: User ID.
        :type id: int
        :param channel_id: Channel ID.
        :type channel_id: int
        :param channel_pw: Channel password, defaults to None
        :type channel_pw: str
        :return: Response from the server.
        :rtype: TS3ClientResponse
        """
        return TS3ClientResponse(self.query.commands.clientmove(clid=id, cid=channel_id, cpw=channel_pw))

    def kick_user_from_channel(self, id: int, reason: Optional[str] = None) -> TS3ClientResponse:
        """Kick a user from the channel.

        :param id: User ID.
        :type id: int
        :param reason: Reason for the kick, defaults to None
        :type reason: str, optional
        :return: Response from the server.
        :rtype: TS3ClientResponse
        """
        return TS3ClientResponse(
            self.query.commands.clientkick(clid=id, reasonid=ReasonIdentifier.REASON_KICK_CHANNEL, reasonmsg=reason)
        )

    def kick_user_from_server(self, id: int, reason: Optional[str] = None) -> TS3ClientResponse:
        """Kick a user from the server.

        :param id: User ID.
        :type id: int
        :param reason: Reason for the kick, defaults to None
        :type reason: str, optional
        :return: Response from the server.
        :rtype: TS3ClientResponse
        """
        return TS3ClientResponse(
            self.query.commands.clientkick(clid=id, reasonid=ReasonIdentifier.REASON_KICK_SERVER, reasonmsg=reason)
        )

    def ban_user(self, id: int, time: int, reason: Optional[str] = None) -> TS3ClientResponse:
        """Ban a user.

        :param id: User ID.
        :type id: int
        :param time: Time in seconds the client should be banned.
        :type time: int
        :param reason: Reason for the ban, defaults to None
        :type reason: str, optional
        :return: Response from the server.
        :rtype: TS3ClientResponse
        """
        return TS3ClientResponse(self.query.commands.banclient(clid=id, time=time, banreason=reason))

    def get_channels(self) -> list[Channel]:
        """Get a list of all channels.

        :return: Response from the server.
        :rtype: TS3ClientResponse
        """
        return [Channel(**channel) for channel in TS3ClientResponse(self.query.commands.channellist())]

    def get_channel_info(self, id: int) -> ChannelInfo:
        """Get information about a channel.

        :param id: Channel ID.
        :type id: int
        :return: Response from the server.
        :rtype: TS3ClientResponse
        """
        return ChannelInfo(**TS3ClientResponse(self.query.commands.channelinfo(cid=id))[0])

    def find_channel(self, name: str) -> list[Channel]:
        """Find channels by name.

        :param name: Name of the channel.
        :type name: str
        :return: Response from the server.
        :rtype: TS3ClientResponse
        """
        return Channel(**TS3ClientResponse(self.query.commands.channelfind(pattern=name))[0])

    def get_messages(self) -> list[Message]:
        """Get a list of all messages.

        :return: A list of all messages.
        :rtype: list[Message]
        """
        return self.query.messages

    def get_unread_messages(self) -> list[Message]:
        """Get a list of all unread messages.

        :return: A list of all unread messages.
        :rtype: list[Message]
        """
        return self.query.unread_messages

    def get_events(self) -> list[Event]:
        """Get a list of all events.

        :return: A list of all events.
        :rtype: list[Event]
        """
        return self.query.events

    def get_unread_events(self) -> list[Event]:
        """Get a list of all unread events.

        :return: A list of all unread events.
        :rtype: list[Event]
        """
        return self.query.unread_events

    def get_user_entered_events(self) -> list[ClientEnterViewEvent]:
        """Get a list of all client enter view events.

        :return: A list of all client enter view events.
        :rtype: list[Event]
        """
        return [event for event in self.query.events if isinstance(event, ClientEnterViewEvent) and not event.used]

    def send_server_message(self, message: str) -> TS3ClientResponse:
        """Send a message to the server.

        :param message: Message to send.
        :type message: str
        :return: Response from the server.
        :rtype: TS3ClientResponse
        """
        return TS3ClientResponse(self.query.commands.sendtextmessage(targetmode=TargetMode.SERVER, msg=message))

    def send_channel_message(self, message: str) -> TS3ClientResponse:
        """Send a message to the current channel.

        :param message: Message to send.
        :type message: str
        :return: Response from the server.
        :rtype: TS3ClientResponse
        """
        return TS3ClientResponse(self.query.commands.sendtextmessage(targetmode=TargetMode.CHANNEL, msg=message))

    def send_private_message(self, id: int, message: str) -> TS3ClientResponse:
        """Send a private message to a user.

        :param id: User ID.
        :type id: int
        :param message: Message to send.
        :type message: str
        :return: Response from the server.
        :rtype: TS3ClientResponse
        """
        return TS3ClientResponse(
            self.query.commands.sendtextmessage(targetmode=TargetMode.CLIENT, target=id, msg=message)
        )

    def send_message(self, target: int, target_mode: TargetMode, message: str) -> TS3ClientResponse:
        """Send a message to a target.

        :param message: Message to send.
        :type target: int
        :param target_mode: Target mode.
        :type target_mode: TargetMode
        :type message: str
        :param target: Target ID.
        :return: Response from the server.
        :rtype: TS3ClientResponse
        """
        return TS3ClientResponse(
            self.query.commands.sendtextmessage(targetmode=target_mode, target=target, msg=message)
        )

    def enable_message_events(self) -> None:
        """Enable receiving all message events."""
        self.start_polling()
        self.query.commands.servernotifyregister(event=NotifyRegisterType.TEXT_SERVER)
        self.query.commands.servernotifyregister(event=NotifyRegisterType.TEXT_CHANNEL)
        self.query.commands.servernotifyregister(event=NotifyRegisterType.TEXT_PRIVATE)

    def disable_message_events(self) -> None:
        """Disable receiving all message events."""
        self.query.commands.servernotifyunregister(event=NotifyRegisterType.TEXT_SERVER)
        self.query.commands.servernotifyunregister(event=NotifyRegisterType.TEXT_CHANNEL)
        self.query.commands.servernotifyunregister(event=NotifyRegisterType.TEXT_PRIVATE)

    def enable_server_events(self) -> None:
        """Enable receiving server events."""
        self.start_polling()
        self.query.commands.servernotifyregister(event=NotifyRegisterType.SERVER)

    def disable_server_events(self) -> None:
        """Disable receiving server events."""
        self.query.commands.servernotifyunregister(event=NotifyRegisterType.SERVER)

    def enable_channel_events(self) -> None:
        """Enable receiving channel events."""
        self.start_polling()
        self.query.commands.servernotifyregister(event=NotifyRegisterType.CHANNEL)

    def disable_channel_events(self) -> None:
        """Disable receiving channel events."""
        self.query.commands.servernotifyunregister(event=NotifyRegisterType.CHANNEL)

    def enable_events_and_messages(self) -> None:
        """Enable receiving all events."""
        self.start_polling()
        self.query.commands.servernotifyregister(event=NotifyRegisterType.TEXT_SERVER)
        self.query.commands.servernotifyregister(event=NotifyRegisterType.TEXT_CHANNEL)
        self.query.commands.servernotifyregister(event=NotifyRegisterType.TEXT_PRIVATE)
        self.query.commands.servernotifyregister(event=NotifyRegisterType.SERVER)
        self.query.commands.servernotifyregister(event=NotifyRegisterType.CHANNEL)

    def disable_events_and_messages(self) -> None:
        """Disable receiving all events."""
        self.stop_polling()
        self.query.commands.servernotifyunregister(event=NotifyRegisterType.TEXT_SERVER)
        self.query.commands.servernotifyunregister(event=NotifyRegisterType.TEXT_CHANNEL)
        self.query.commands.servernotifyunregister(event=NotifyRegisterType.TEXT_PRIVATE)
        self.query.commands.servernotifyunregister(event=NotifyRegisterType.SERVER)
        self.query.commands.servernotifyunregister(event=NotifyRegisterType.CHANNEL)

    def start_polling(self, interval: int = 1) -> None:
        """Start polling for events and messages.

        :param interval: Polling interval in seconds, defaults to 1
        :type interval: int, optional
        """
        self.query.start_polling(interval)

    def keep_alive(self) -> None:
        """Keep the connection alive."""
        self.query.keep_alive()

    def stop_polling(self) -> None:
        """Stop polling for events and messages."""
        self.query.stop_polling()
