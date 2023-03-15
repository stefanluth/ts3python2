import types
from utils.logger import get_logger
from query.ts3query import TS3Query

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

    def get_clients(self) -> list[dict]:
        return self.query.commands.clientlist(uid=True).data

    def get_client(self, id: int) -> dict:
        return self.query.commands.clientinfo(clid=id).data

    def find_client(self, name: str) -> dict:
        return self.query.commands.clientfind(pattern=name).data

    def set_name(self, name: str) -> None:
        self.query.commands.clientupdate(client_nickname=name)
