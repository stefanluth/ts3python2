import pytest

from ts3client.event import ChannelCreatedEvent, TokenUsedEvent
from ts3client.utils import parsers


@pytest.mark.parametrize(
    ("payload", "expected_data", "event_type", "event_field", "message_expected"),
    [
        (
            b"clid=1 client_nickname=foo\\sbar|clid=2\n\rerror id=0 msg=ok\n\r",
            {0: {"clid": 1, "client_nickname": "foo bar"}, 1: {"clid": 2}},
            None,
            None,
            None,
        ),
        (
            b"notifytokenused clid=1 cldbid=2 cluid=abc token=xyz\n\rversion=1\n\rerror id=0 msg=ok\n\r",
            {0: {"version": 1}},
            TokenUsedEvent,
            ("clid", 1),
            None,
        ),
        (
            b"notifychannelcreated cid=1 future_field=1\n\rversion=1\n\rerror id=0 msg=ok\n\r",
            {0: {"version": 1}},
            ChannelCreatedEvent,
            ("cid", 1),
            None,
        ),
        (
            b"notifytextmessage targetmode=1 msg=hello\\sworld target=1 invokerid=2 invokername=foo\\sbar "
            b"invokeruid=abc\n\rversion=1\n\rerror id=0 msg=ok\n\r",
            {0: {"version": 1}},
            None,
            None,
            ("hello world", "foo bar", 1),
        ),
        pytest.param(
            b"notifytextmessage targetmode=1 msg=hello\\sworld invokerid=2 invokername=foo\\sbar "
            b"invokeruid=abc\n\rversion=1\n\rerror id=0 msg=ok\n\r",
            {0: {"version": 1}},
            None,
            None,
            ("hello world", "foo bar", 0),
            marks=pytest.mark.bug,
        ),
    ],
    ids=["multiple-rows", "tokenused", "unknown-field-ignored", "message-with-target", "message-without-target"],
)
def test_parse_response(payload, expected_data, event_type, event_field, message_expected):
    data, events, messages = parsers.parse_response(payload)

    assert data == expected_data

    if event_type is None:
        assert events == []
    else:
        assert len(events) == 1
        assert isinstance(events[0], event_type)
        assert getattr(events[0], event_field[0]) == event_field[1]

    if message_expected is None:
        assert messages == []
    else:
        assert len(messages) == 1
        assert (messages[0].content, messages[0].invokername, messages[0].target) == message_expected


def test_response_to_dict_handles_empty_duplicate_and_embedded_equals():
    assert parsers.response_to_dict("a= b=x=y c") == {"a": "", "b": "x=y", "c": ""}
    assert parsers.response_to_dict("a=1 a=2") == {"a": 2}


def test_identical_notifications_are_all_kept():
    message = b"notifytextmessage targetmode=1 msg=hi target=1 invokerid=2 invokername=u invokeruid=x\n\r"
    payload = message + message + b"version=1\n\rerror id=0 msg=ok\n\r"

    data, events, messages = parsers.parse_response(payload)

    assert data == {0: {"version": 1}}
    assert [parsed.content for parsed in messages] == ["hi", "hi"]
