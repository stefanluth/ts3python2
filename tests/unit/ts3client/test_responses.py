import pytest

from tests.support.fakes import FakeResponse
from ts3client.errors import TS3Error
from ts3client.ts3client_response import TS3ClientResponse
from ts3client.ts3query.ts3query_response import TS3QueryResponse
from ts3client.utils import patterns


def test_query_response_parses_data_and_unescapes_the_message():
    response = make_query_response(b"clid=1 client_nickname=foo\\sbar\n\rerror id=0 msg=ok\n\r")

    assert response.error_id == 0
    assert response.msg == "ok"
    assert response.extra_msg is None
    assert response.data == {0: {"clid": 1, "client_nickname": "foo bar"}}


def test_query_response_parses_extra_message():
    response = make_query_response(b"error id=1 msg=invalid\\sid extra_msg=bad\\sthing\n\r")

    assert response.error_id == 1
    assert response.msg == "invalid id"
    assert response.extra_msg == "bad thing"
    assert response.data == {}


def test_client_response_raises_for_server_errors():
    with pytest.raises(TS3Error) as raised:
        TS3ClientResponse(FakeResponse(error_id=512, msg="invalid clientID"))

    assert raised.value.id == 512
    assert raised.value.msg == "invalid clientID"


def test_client_response_replaces_empty_data_with_the_message():
    response = TS3ClientResponse(FakeResponse(data={}, msg="ok"))

    assert response.to_dict() == {"msg": "ok"}
    assert response["msg"] == "ok"


def test_client_response_behaves_like_a_mapping():
    response = TS3ClientResponse(FakeResponse(data={0: {"clid": 1}, 1: {"clid": 2}}))

    assert len(response) == 2
    assert list(response) == [{"clid": 1}, {"clid": 2}]
    assert 0 in response
    assert response.get("missing", "fallback") == "fallback"
    assert repr(response) == repr(response.data)
    assert response == {0: {"clid": 1}, 1: {"clid": 2}}
    assert response != {0: {"clid": 1}}

    response["new"] = "value"
    assert response["new"] == "value"
    del response["new"]
    assert "new" not in response


def make_query_response(payload):
    match = patterns.RESPONSE_END_BYTES.search(payload)
    assert match is not None
    return TS3QueryResponse(0, match, payload)
