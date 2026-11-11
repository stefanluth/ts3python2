import pytest

from tests.support.fakes import FakeResponse
from ts3client.errors import TS3Error
from ts3client.ts3client_response import TS3ClientResponse


def test_error_response_raises_ts3_error():
    with pytest.raises(TS3Error) as error:
        TS3ClientResponse(FakeResponse(error_id=520, msg="invalid loginname or password"))

    assert error.value.id == 520
    assert error.value.msg == "invalid loginname or password"


def test_empty_response_exposes_msg():
    response = TS3ClientResponse(FakeResponse(data={}, msg="ok"))

    assert response.get("msg") == "ok"
    assert response.to_dict() == {"msg": "ok"}


def test_response_behaves_like_a_dict():
    response = TS3ClientResponse(FakeResponse(data={0: {"clid": 1}, 1: {"clid": 2}}))

    assert len(response) == 2
    assert 0 in response
    assert response[1] == {"clid": 2}
    assert list(response) == [{"clid": 1}, {"clid": 2}]
    assert response == {0: {"clid": 1}, 1: {"clid": 2}}
    assert response != {}

    response[2] = {"clid": 3}
    assert response[2] == {"clid": 3}

    del response[2]
    assert 2 not in response
    assert repr(response) == repr({0: {"clid": 1}, 1: {"clid": 2}})
