from collections.abc import Iterator
from typing import Any

from .errors import TS3Error
from .ts3query.ts3query_response import TS3QueryResponse
from .utils.logger import create_logger, log_path

logger = create_logger("ClientResponse", log_path("main.log"))


class TS3ClientResponse:
    """
    This class is used to handle the response from the TS3 server.
    It is a wrapper around the TS3QueryResponse class.

    :param response: The response from the TS3 server.
    :type response: TS3QueryResponse
    """

    def __init__(self, response: TS3QueryResponse) -> None:
        self.query_response = response
        self.error_id = response.error_id
        self.msg = response.msg
        self.data: dict[int | str, Any] = response.data
        self.events = response.events
        self.messages = response.messages

        if response.error_id != 0:
            raise TS3Error(response.error_id, response.msg)

        if response.data == {}:
            self.data = {"msg": response.msg}

    def to_dict(self) -> dict[int | str, Any]:
        return self.data

    def __repr__(self) -> str:
        return self.data.__repr__()

    def __getitem__(self, key: int | str) -> Any:
        return self.data[key]

    def __setitem__(self, key: int | str, value: Any) -> None:
        self.data[key] = value

    def __delitem__(self, key: int | str) -> None:
        del self.data[key]

    def __iter__(self) -> Iterator[Any]:
        return iter(self.data.values())

    def __len__(self) -> int:
        return len(self.data)

    def __contains__(self, key: int | str) -> bool:
        return key in self.data

    def __eq__(self, other: object) -> bool:
        return self.data == other

    def __ne__(self, other: object) -> bool:
        return self.data != other

    def get(self, key: int | str, default: Any = None) -> Any:
        return self.data.get(key, default)
