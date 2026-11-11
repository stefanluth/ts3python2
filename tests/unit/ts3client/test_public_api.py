import pytest

from ts3client import TS3Client
from ts3client.ts3query import TS3Query
from ts3client.ts3query.ts3query_command import CommandsWrapper


@pytest.mark.parametrize("cls", [TS3Query, TS3Client, CommandsWrapper])
def test_public_api_has_no_login_or_logout(cls):
    assert not hasattr(cls, "login"), f"{cls.__name__} still exposes login"
    assert not hasattr(cls, "logout"), f"{cls.__name__} still exposes logout"
