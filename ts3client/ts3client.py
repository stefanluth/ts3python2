from classes.event import Event
from classes.message import Message
from ts3client.client_response import ClientResponse
from utils.logger import get_logger
from ts3query.ts3query import TS3Query

logger = get_logger("main")


class TS3Client:
    """A wrapper class for the TS3Query"""

    query: TS3Query = None

    def connect(
        self,
        host: str,
        port: int,
        login: str = None,
        password: str = None,
        timeout: int = 10,
    ) -> None:
        self.query = TS3Query(host, port, login, password, timeout)

    def disconnect(self) -> None:
        self.query.exit()
        self.query = None

    def login(self, login: str, password: str) -> None:
        self.query.login(login, password)

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

    def get_clients(self) -> ClientResponse:
        return ClientResponse(self.query.commands.clientlist(uid=True))

    def get_client(self, id: int) -> ClientResponse:
        return ClientResponse(self.query.commands.clientinfo(clid=id))

    def find_client(self, name: str) -> ClientResponse:
        return ClientResponse(self.query.commands.clientfind(pattern=name))

    def set_name(self, name: str) -> ClientResponse:
        return ClientResponse(self.query.commands.clientupdate(client_nickname=name))

    def send_message(self, message: str, id: int) -> ClientResponse:
        return ClientResponse(self.query.commands.sendtextmessage(targetmode=1, target=id, msg=message))

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
