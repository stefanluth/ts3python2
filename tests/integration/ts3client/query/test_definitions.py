import pytest

from tests.support.integration import (
    channel_create,
    channel_delete,
    open_used_query,
    unique_name,
    whoami,
)
from ts3client.constants import (
    Codec,
    CodecEncryptionMode,
    HostBannerMode,
    HostMessageMode,
    LogLevel,
    NotifyRegisterType,
    PermissionGroupDatabaseType,
    ReasonIdentifier,
    Subsystem,
    TokenType,
)

pytestmark = pytest.mark.integration

SUPPORTED_CODECS = [Codec.CODEC_OPUS_VOICE, Codec.CODEC_OPUS_MUSIC]
LEGACY_CODECS = [
    Codec.CODEC_SPEEX_NARROWBAND,
    Codec.CODEC_SPEEX_WIDEBAND,
    Codec.CODEC_SPEEX_ULTRAWIDEBAND,
    Codec.CODEC_CELT_MONO,
]


@pytest.mark.parametrize("subsystem", list(Subsystem), ids=lambda value: value.name)
def test_bindinglist_subsystems(used_query, subsystem):
    response = used_query.commands.bindinglist(subsystem=subsystem)

    assert response.error_id == 0, response


@pytest.mark.parametrize("level", list(LogLevel), ids=lambda value: value.name)
def test_log_levels(used_query, level):
    response = used_query.commands.logadd(loglevel=level, logmsg=unique_name("log-entry"))

    assert response.error_id == 0, response
    assert used_query.commands.logview(lines=1).error_id == 0


@pytest.mark.parametrize("notify_type", list(NotifyRegisterType), ids=lambda value: value.name)
def test_notify_register_types(fresh_query, notify_type):
    kwargs = {"event": notify_type}
    if notify_type in (NotifyRegisterType.CHANNEL, NotifyRegisterType.TEXT_CHANNEL):
        kwargs["id"] = 0

    response = fresh_query.commands.servernotifyregister(**kwargs)

    assert response.error_id == 0, response


@pytest.mark.parametrize("group_type", list(PermissionGroupDatabaseType), ids=lambda value: value.name)
def test_server_group_database_types(used_query, group_type):
    response = used_query.commands.servergroupadd(name=unique_name("sg"), type=group_type)

    assert response.error_id == 0, response
    sgid = int(response.data[0]["sgid"])
    try:
        groups = used_query.commands.servergrouplist().data
        assert any(int(entry["sgid"]) == sgid for entry in groups.values())
    finally:
        used_query.commands.servergroupdel(sgid=sgid, force=True)


@pytest.mark.parametrize(
    "group_type",
    [PermissionGroupDatabaseType.PERMGROUP_DB_TYPE_TEMPLATE, PermissionGroupDatabaseType.PERMGROUP_DB_TYPE_REGULAR],
    ids=["template", "regular"],
)
def test_channel_group_database_types(used_query, group_type):
    response = used_query.commands.channelgroupadd(name=unique_name("cg"), type=group_type)

    assert response.error_id == 0, response
    cgid = int(response.data[0]["cgid"])
    try:
        groups = used_query.commands.channelgrouplist().data
        assert any(int(entry["cgid"]) == cgid for entry in groups.values())
    finally:
        used_query.commands.channelgroupdel(cgid=cgid, force=True)


@pytest.mark.parametrize("token_type", list(TokenType), ids=lambda value: value.name)
def test_token_types(
    used_query,
    regular_server_group_ids,
    regular_channel_group_ids,
    token_type,
):
    cid = channel_create(used_query, unique_name("token-channel"))
    try:
        if token_type is TokenType.TOKEN_SERVER_GROUP:
            tokenid1 = regular_server_group_ids[0]
            tokenid2 = 0
        else:
            tokenid1 = regular_channel_group_ids[0]
            tokenid2 = cid

        response = used_query.commands.tokenadd(
            tokentype=token_type.value,
            tokenid1=tokenid1,
            tokenid2=tokenid2,
            tokendescription=unique_name("token"),
        )

        assert response.error_id == 0, response
        token = response.data[0]["token"]
        try:
            tokens = used_query.commands.tokenlist().data
            assert any(entry["token"] == token for entry in tokens.values())
        finally:
            used_query.commands.tokendelete(token=token)
    finally:
        channel_delete(used_query, cid)


@pytest.mark.parametrize("codec", SUPPORTED_CODECS, ids=lambda value: value.name)
def test_supported_codec_values(used_query, codec):
    cid = channel_create(used_query, unique_name("codec-channel"))
    before = used_query.commands.channelinfo(cid=cid).data[0]["channel_codec"]
    try:
        response = used_query.commands.channeledit(cid=cid, channel_codec=codec.value)

        assert response.error_id == 0, response
        info = used_query.commands.channelinfo(cid=cid).data[0]
        assert info["channel_codec"] == codec.value
    finally:
        used_query.commands.channeledit(cid=cid, channel_codec=before)
        channel_delete(used_query, cid)


@pytest.mark.parametrize("codec", LEGACY_CODECS, ids=lambda value: value.name)
def test_legacy_codec_values_are_rejected(used_query, codec):
    cid = channel_create(used_query, unique_name("legacy-codec-channel"))
    try:
        response = used_query.commands.channeledit(cid=cid, channel_codec=codec.value)

        assert response.error_id == 1538, response
    finally:
        channel_delete(used_query, cid)


@pytest.mark.parametrize(
    ("property_name", "values"),
    [
        ("virtualserver_hostmessage_mode", list(HostMessageMode)),
        ("virtualserver_hostbanner_mode", list(HostBannerMode)),
        ("virtualserver_codec_encryption_mode", list(CodecEncryptionMode)),
    ],
    ids=["hostmessage-mode", "hostbanner-mode", "codec-encryption-mode"],
)
def test_virtual_server_enum_values(used_query, property_name, values):
    before = used_query.commands.serverinfo().data[0][property_name]
    try:
        for value in values:
            response = used_query.commands.serveredit(**{property_name: value.value})

            assert response.error_id == 0, response
            info = used_query.commands.serverinfo().data[0]
            assert info[property_name] == value.value
    finally:
        used_query.commands.serveredit(**{property_name: before})


def test_kick_channel_reason_identifier(server, used_query):
    target = open_used_query(server.host, server.query_port, server.server_port, server.password)
    cid = channel_create(used_query, unique_name("kick-channel"))
    try:
        clid = whoami(target)["client_id"]
        assert used_query.commands.clientmove(clid=clid, cid=cid).error_id == 0

        response = used_query.commands.clientkick(
            clid=clid,
            reasonid=ReasonIdentifier.REASON_KICK_CHANNEL,
            reasonmsg="integration",
        )

        assert response.error_id == 0, response
    finally:
        target.exit()
        channel_delete(used_query, cid)
