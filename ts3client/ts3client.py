from typing import Optional

from classes.event import Event
from classes.message import Message
from constants import EventType, NotifyRegisterType, ReasonIdentifier, TargetMode
from ts3client.client_response import ClientResponse
from ts3query.ts3query import TS3Query
from utils.logger import create_logger

logger = create_logger("TS3Client", "main.log")


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

    query: TS3Query = None

    def __init__(self, host: str = None, port: int = None, login: str = None, password: str = None, timeout=10) -> None:
        if not host or not port:
            logger.info("No host and/or port provided, not connecting to a server")
            return

        self.connect(host, port)

        if not login or not password:
            logger.info("No login and/or password provided, not logging in")
            return

        self.login(login, password)

    def whoami(self) -> ClientResponse:
        return ClientResponse(self.query.commands.whoami())

    @property
    def messages(self) -> list[Message]:
        return self.query.messages

    @property
    def unread_messages(self) -> list[Message]:
        return self.query.unread_messages

    @property
    def events(self) -> list[Event]:
        return self.query.events

    @property
    def unread_events(self) -> list[Event]:
        return self.query.unread_events

    @property
    def client_entered_events(self) -> list[Event]:
        return [event for event in self.query.events if event.event_type == EventType.CLIENT_ENTER_VIEW]

    @property
    def name(self) -> str:
        return self.whoami().get("client_nickname")

    @property
    def id(self) -> int:
        return self.whoami().get("clid")

    @property
    def unique_id(self) -> str:
        return self.whoami().get("client_unique_identifier")

    @property
    def database_id(self) -> int:
        return self.whoami().get("client_database_id")

    @property
    def server_id(self) -> int:
        return self.query.commands.serverinfo().data.get("virtualserver_id")

    @property
    def server_unique_id(self) -> str:
        return self.query.commands.serverinfo().data.get("virtualserver_unique_identifier")

    @property
    def server_name(self) -> str:
        return self.query.commands.serverinfo().data.get("virtualserver_name")

    @property
    def server_port(self) -> int:
        return self.query.commands.serverinfo().data.get("virtualserver_port")

    def connect(self, host: str, port: int, timeout: int = 10) -> None:
        """Connect to a TeamSpeak 3 server.

        :param host: Hostname or IP address of the TeamSpeak 3 server.
        :type host: str
        :param port: UDP port of the TeamSpeak 3 server.
        :type port: int
        :param timeout: Timeout for the connection, defaults to 10.
        :type timeout: int, optional
        """
        logger.info(f"Connecting to {host}:{port}...")
        self.query = TS3Query(host, port, timeout)
        logger.info("Connected")

    def disconnect(self) -> None:
        """Disconnect from the TeamSpeak 3 server."""
        self.query.exit()
        self.query = None

    def login(self, login: str, password: str) -> None:
        """Login to the TeamSpeak 3 server.

        :param login: Username to login with.
        :type login: str
        :param password: Password to login with.
        :type password: str
        """
        logger.info(f"Logging in as {login}...")
        self.query.login(login, password)
        logger.info("Logged in")

    def logout(self) -> None:
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

    def set_name(self, name: str) -> ClientResponse:
        """Set the name of the TS3Client.

        :param name: New name of the client.
        :type name: str
        :return: Response from the server.
        :rtype: ClientResponse
        """
        return ClientResponse(self.query.commands.clientupdate(client_nickname=name))

    def set_description(self, description: str) -> ClientResponse:
        """Set the description of the TS3Client.

        :param description: New description of the client.
        :type description: str
        :return: Response from the server.
        :rtype: ClientResponse
        """
        return ClientResponse(self.query.commands.clientupdate(client_description=description))

    def get_clients(self) -> ClientResponse:
        """Get a list of all clients.

        :return: Response from the server.
        :rtype: ClientResponse
        """
        return ClientResponse(self.query.commands.clientlist(uid=True))

    def get_client_info(self, id: int) -> ClientResponse:
        """Get information about a client.

        :param id: Client ID.
        :type id: int
        :return: Response from the server.
        :rtype: ClientResponse
        """
        return ClientResponse(self.query.commands.clientinfo(clid=id))

    def find_client(self, name: str) -> ClientResponse:
        """Find a client by name.

        :param name: Name of the client.
        :type name: str
        :return: Response from the server.
        :rtype: ClientResponse
        """
        return ClientResponse(self.query.commands.clientfind(pattern=name))

    def rename_client(self, id: int, name: str) -> ClientResponse:
        """Rename a client.

        :param id: Client ID.
        :type id: int
        :param name: New name of the client.
        :type name: str
        :return: Response from the server.
        :rtype: ClientResponse
        """
        return ClientResponse(self.query.commands.clientedit(clid=id, client_nickname=name))

    def move_client(self, id: int, channel_id: int, channel_pw: Optional[str] = None) -> ClientResponse:
        """Move a client to a channel.

        :param id: Client ID.
        :type id: int
        :param channel_id: Channel ID.
        :type channel_id: int
        :param channel_pw: Channel password, defaults to None
        :type channel_pw: str
        :return: Response from the server.
        :rtype: ClientResponse
        """
        return ClientResponse(self.query.commands.clientmove(clid=id, cid=channel_id, cpw=channel_pw))

    def kick_client_from_channel(self, id: int, reason: Optional[str] = None) -> ClientResponse:
        """Kick a client from the channel.

        :param id: Client ID.
        :type id: int
        :param reason: Reason for the kick, defaults to None
        :type reason: str, optional
        :return: Response from the server.
        :rtype: ClientResponse
        """
        return ClientResponse(
            self.query.commands.clientkick(clid=id, reasonid=ReasonIdentifier.REASON_KICK_CHANNEL, reasonmsg=reason)
        )

    def kick_client_from_server(self, id: int, reason: Optional[str] = None) -> ClientResponse:
        """Kick a client from the server.

        :param id: Client ID.
        :type id: int
        :param reason: Reason for the kick, defaults to None
        :type reason: str, optional
        :return: Response from the server.
        :rtype: ClientResponse
        """
        return ClientResponse(
            self.query.commands.clientkick(clid=id, reasonid=ReasonIdentifier.REASON_KICK_SERVER, reasonmsg=reason)
        )

    def ban_client(self, id: int, time: int, reason: Optional[str] = None) -> ClientResponse:
        """Ban a client.

        :param id: Client ID.
        :type id: int
        :param time: Time in seconds the client should be banned.
        :type time: int
        :param reason: Reason for the ban, defaults to None
        :type reason: str, optional
        :return: Response from the server.
        :rtype: ClientResponse
        """
        return ClientResponse(self.query.commands.banclient(clid=id, banreason=reason))

    def get_channels(self) -> ClientResponse:
        """Get a list of all channels.

        :return: Response from the server.
        :rtype: ClientResponse
        """
        return ClientResponse(self.query.commands.channellist())

    def get_channel(self, id: int) -> ClientResponse:
        """Get information about a channel.

        :param id: Channel ID.
        :type id: int
        :return: Response from the server.
        :rtype: ClientResponse
        """
        return ClientResponse(self.query.commands.channelinfo(cid=id))

    def find_channel(self, name: str) -> ClientResponse:
        """Find a channel by name.

        :param name: Name of the channel.
        :type name: str
        :return: Response from the server.
        :rtype: ClientResponse
        """
        return ClientResponse(self.query.commands.channelfind(pattern=name))

    def send_server_message(self, message: str) -> ClientResponse:
        """Send a message to the server.

        :param message: Message to send.
        :type message: str
        :return: Response from the server.
        :rtype: ClientResponse
        """
        return ClientResponse(self.query.commands.sendtextmessage(targetmode=TargetMode.SERVER, msg=message))

    def send_channel_message(self, message: str) -> ClientResponse:
        """Send a message to the current channel.

        :param message: Message to send.
        :type message: str
        :return: Response from the server.
        :rtype: ClientResponse
        """
        return ClientResponse(self.query.commands.sendtextmessage(targetmode=TargetMode.CHANNEL, msg=message))

    def send_private_message(self, id: int, message: str) -> ClientResponse:
        """Send a private message to a client.

        :param id: Client ID.
        :type id: int
        :param message: Message to send.
        :type message: str
        :return: Response from the server.
        :rtype: ClientResponse
        """
        return ClientResponse(self.query.commands.sendtextmessage(targetmode=TargetMode.CLIENT, target=id, msg=message))

    def send_message(self, target: int, target_mode: TargetMode, message: str) -> ClientResponse:
        """Send a message to a target.

        :param message: Message to send.
        :type target: int
        :param target_mode: Target mode.
        :type target_mode: TargetMode
        :type message: str
        :param target: Target ID.
        :return: Response from the server.
        :rtype: ClientResponse
        """
        return ClientResponse(self.query.commands.sendtextmessage(targetmode=target_mode, target=target, msg=message))

    def enable_message_events(self) -> None:
        """Enable receiving all message events."""
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
        self.query.commands.servernotifyregister(event=NotifyRegisterType.SERVER)

    def disable_server_events(self) -> None:
        """Disable receiving server events."""
        self.query.commands.servernotifyunregister(event=NotifyRegisterType.SERVER)

    def enable_channel_events(self) -> None:
        """Enable receiving channel events."""
        self.query.commands.servernotifyregister(event=NotifyRegisterType.CHANNEL)

    def disable_channel_events(self) -> None:
        """Disable receiving channel events."""
        self.query.commands.servernotifyunregister(event=NotifyRegisterType.CHANNEL)

    def enable_all_events(self) -> None:
        """Enable receiving all events."""
        self.query.commands.servernotifyregister(event=NotifyRegisterType.TEXT_SERVER)
        self.query.commands.servernotifyregister(event=NotifyRegisterType.TEXT_CHANNEL)
        self.query.commands.servernotifyregister(event=NotifyRegisterType.TEXT_PRIVATE)
        self.query.commands.servernotifyregister(event=NotifyRegisterType.SERVER)
        self.query.commands.servernotifyregister(event=NotifyRegisterType.CHANNEL)

    def disable_all_events(self) -> None:
        """Disable receiving all events."""
        self.query.commands.servernotifyunregister(event=NotifyRegisterType.TEXT_SERVER)
        self.query.commands.servernotifyunregister(event=NotifyRegisterType.TEXT_CHANNEL)
        self.query.commands.servernotifyunregister(event=NotifyRegisterType.TEXT_PRIVATE)
        self.query.commands.servernotifyunregister(event=NotifyRegisterType.SERVER)
        self.query.commands.servernotifyunregister(event=NotifyRegisterType.CHANNEL)
