import pytest

from ts3client.event import TokenUsedEvent
from ts3client.utils import parsers


def test_response_to_dict_converts_ints_and_unescapes():
    assert parsers.response_to_dict(r"clid=1 client_nickname=foo\sbar") == {
        "clid": 1,
        "client_nickname": "foo bar",
    }


def test_parse_response_multiple_rows():
    data, _, _ = parsers.parse_response(b"clid=1|clid=2\n\rerror id=0 msg=ok\n\r")
    assert data == {0: {"clid": 1}, 1: {"clid": 2}}


def test_parse_empty_response_has_no_rows():
    data, _, _ = parsers.parse_response(b"error id=0 msg=ok\n\r")
    assert data == {}


def test_parse_message_unescapes_msg():
    _, _, messages = parsers.parse_response(
        b"notifytextmessage targetmode=1 msg=hello\\sworld target=1 invokerid=2 "
        b"invokername=foo invokeruid=abc\n\rversion=1\n\rerror id=0 msg=ok\n\r"
    )
    assert messages[0].content == "hello world"


def test_parse_server_message_without_target():
    _, _, messages = parsers.parse_response(
        b"notifytextmessage targetmode=3 msg=hi invokerid=2 invokername=foo invokeruid=abc\n\r"
        b"version=1\n\rerror id=0 msg=ok\n\r"
    )
    assert messages[0].content == "hi"
    assert messages[0].target == 0


def test_parse_channel_message_without_target():
    _, _, messages = parsers.parse_response(
        b"notifytextmessage targetmode=2 msg=hi invokerid=2 invokername=foo invokeruid=abc\n\r"
        b"version=1\n\rerror id=0 msg=ok\n\r"
    )
    assert messages[0].content == "hi"
    assert messages[0].target == 0


@pytest.mark.bug
def test_parse_message_unescapes_invokername():
    _, _, messages = parsers.parse_response(
        b"notifytextmessage targetmode=1 msg=hi target=1 invokerid=2 "
        b"invokername=foo\\sbar invokeruid=abc\n\rversion=1\n\rerror id=0 msg=ok\n\r"
    )
    assert messages[0].invokername == "foo bar"


@pytest.mark.bug
def test_parse_response_tokenused_event():
    _, events, _ = parsers.parse_response(
        b"notifytokenused clid=1 cldbid=2 cluid=abc token=xyz\n\rversion=1\n\rerror id=0 msg=ok\n\r"
    )
    assert len(events) == 1
    assert isinstance(events[0], TokenUsedEvent)


def test_parse_response_keeps_last_notification():
    _, events, _ = parsers.parse_response(b"notifychannelcreated cid=1\n\rerror id=0 msg=ok\n\r")
    assert len(events) == 1
    assert events[0].cid == 1


def test_parse_event_ignores_unknown_field():
    _, events, _ = parsers.parse_response(
        b"notifychannelcreated cid=1 future_field=1\n\rversion=1\n\rerror id=0 msg=ok\n\r"
    )
    assert len(events) == 1
    assert events[0].cid == 1
