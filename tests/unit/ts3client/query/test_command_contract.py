import pytest

from tests.support.fakes import FakeResponse
from ts3client.constants import (
    LogLevel,
    NotifyRegisterType,
    PermissionGroupDatabaseType,
    ReasonIdentifier,
    Subsystem,
    TargetMode,
)
from ts3client.ts3query.ts3query_command import CommandsWrapper
from ts3client.ts3query.ts3query_response import TS3QueryResponse
from ts3client.utils import patterns


class RecordingQuery:
    def __init__(self, responses=None):
        self.sent = []
        self.responses = responses or {}

    def send(self, command):
        self.sent.append(command)
        return self.responses.get(command.command, FakeResponse())


def encode(method, *args, **kwargs):
    query = RecordingQuery()
    getattr(CommandsWrapper(query), method)(*args, **kwargs)

    assert len(query.sent) == 1
    return query.sent[0].encoded


@pytest.mark.parametrize(
    ("method", "args", "kwargs", "expected"),
    [
        ("bindinglist", (), {}, b"bindinglist subsystem=voice\n"),
        ("bindinglist", (Subsystem.QUERY,), {}, b"bindinglist subsystem=query\n"),
        ("logadd", (LogLevel.LOGLEVEL_INFO, "hi"), {}, b"logadd loglevel=4 logmsg=hi\n"),
        (
            "servernotifyregister",
            (NotifyRegisterType.TEXT_PRIVATE,),
            {},
            b"servernotifyregister event=textprivate\n",
        ),
        (
            "servernotifyregister",
            (NotifyRegisterType.CHANNEL,),
            {"id": 0},
            b"servernotifyregister event=channel id=0\n",
        ),
        (
            "clientkick",
            (1, ReasonIdentifier.REASON_KICK_CHANNEL, "bye"),
            {},
            b"clientkick clid=1 reasonid=4 reasonmsg=bye\n",
        ),
        ("channeldelete", (1,), {"force": True}, b"channeldelete cid=1 force=1\n"),
        ("channeldelete", (1,), {"force": False}, b"channeldelete cid=1 force=0\n"),
        ("messageupdateflag", (1, True), {}, b"messageupdateflag msgid=1 flag=1\n"),
        (
            "channelgroupadd",
            ("x", PermissionGroupDatabaseType.PERMGROUP_DB_TYPE_TEMPLATE),
            {},
            b"channelgroupadd name=x type=0\n",
        ),
        ("channelgroupadd", ("x",), {}, b"channelgroupadd name=x\n"),
        ("use", (), {"sid": 1, "port": None}, b"use sid=1\n"),
        ("use", (), {"port": 9987, "virtual": True}, b"use -virtual port=9987\n"),
        ("channellist", (), {"topic": True, "flags": False}, b"channellist -topic\n"),
        ("servergrouppermlist", (1,), {"permsid": True}, b"servergrouppermlist -permsid sgid=1\n"),
        (
            "servergroupaddperm",
            (1, 10),
            {"permsid": "b_permission"},
            b"servergroupaddperm sgid=1 permvalue=10 permsid=b_permission permnegated=0 permskip=0\n",
        ),
        (
            "sendtextmessage",
            (TargetMode.SERVER, 0, "hello world"),
            {},
            b"sendtextmessage targetmode=3 target=0 msg=hello\\sworld\n",
        ),
        ("channeledit", (1,), {"CHANNEL_TOPIC": "news"}, b"channeledit cid=1 channel_topic=news\n"),
        ("channeledit", (1,), {"channel_icon_id": 5}, b"channeledit cid=1 channel_icon_id=5\n"),
        (
            "instanceedit",
            (),
            {"serverinstance_template_channeldefault_group": 3},
            b"instanceedit serverinstance_template_channeldefault_group=3\n",
        ),
    ],
)
def test_command_encoding_contract(method, args, kwargs, expected):
    assert encode(method, *args, **kwargs) == expected


def test_help_reparses_the_response_body():
    payload = b"help text\n\rerror id=0 msg=ok\n\r"
    match = patterns.RESPONSE_END_BYTES.search(payload)
    assert match is not None
    query = RecordingQuery(responses={"help": TS3QueryResponse(0, match, payload)})

    response = CommandsWrapper(query).help()

    assert response.data["help"] == "help text"
    assert response.error_id == 0
