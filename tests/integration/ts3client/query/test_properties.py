import pytest

from tests.support.integration import (
    channel_create,
    channel_delete,
    default_channel_id,
    unique_name,
    whoami,
)
from tests.support.property_cases import (
    CHANNEL_CASES,
    CLIENT_CASES,
    SERVER_INSTANCE_CASES,
    VSERVER_CASES,
    Context,
)
from ts3client.channel import Channel, ChannelInfo
from ts3client.constants import (
    ChangeableChannelProperties,
    ChangeableClientProperties,
    ChangeableServerInstanceProperties,
    ChangeableVirtualServerProperties,
    ChannelProperties,
    ClientProperties,
    ServerInstanceProperties,
    VirtualServerProperties,
)
from ts3client.user import User, UserInfo

pytestmark = pytest.mark.integration

UNREPORTED_CHANNEL_PROPERTIES = {"channel_password", "cpid", "channel_delete_delay"}
UNREPORTED_VIRTUAL_SERVER_PROPERTIES = {"virtualserver_password", "virtualserver_min_winphone_version"}


@pytest.mark.parametrize("case", list(CHANNEL_CASES.values()), ids=lambda case: case.property)
def test_channel_property_round_trip(
    used_query,
    regular_server_group_ids,
    query_server_group_ids,
    template_server_group_ids,
    regular_channel_group_ids,
    template_channel_group_ids,
    case,
):
    if case.mode == "skip":
        pytest.skip(case.note)

    parent = channel_create(used_query, unique_name("property-parent")) if case.needs_parent else None
    cid = None
    before = {}
    sent = {}
    try:
        if case.target == "default":
            cid = default_channel_id(used_query)
            before = used_query.commands.channelinfo(cid=cid).data[0]
            ctx = _channel_context(
                before,
                regular_server_group_ids,
                query_server_group_ids,
                template_server_group_ids,
                regular_channel_group_ids,
                template_channel_group_ids,
                parent,
            )
            sent = case.kwargs(ctx)
            response = used_query.commands.channeledit(cid=cid, **sent)
        elif case.command == "create":
            ctx = _channel_context(
                {},
                regular_server_group_ids,
                query_server_group_ids,
                template_server_group_ids,
                regular_channel_group_ids,
                template_channel_group_ids,
                parent,
            )
            sent = case.kwargs(ctx)
            response = used_query.commands.channelcreate(
                channel_name=unique_name("property-created"),
                **sent,
            )
            assert response.error_id == 0, response
            cid = int(response.data[0]["cid"])
            before = used_query.commands.channelinfo(cid=cid).data[0]
        else:
            cid = channel_create(used_query, unique_name("property-channel"))
            before = used_query.commands.channelinfo(cid=cid).data[0]
            if case.mode == "noop" and case.property not in before:
                pytest.skip(f"{case.property} is not reported by this server")
            ctx = _channel_context(
                before,
                regular_server_group_ids,
                query_server_group_ids,
                template_server_group_ids,
                regular_channel_group_ids,
                template_channel_group_ids,
                parent,
            )
            sent = case.kwargs(ctx)
            response = used_query.commands.channeledit(cid=cid, **sent)

        assert response.error_id == 0, response
        after = used_query.commands.channelinfo(cid=cid).data[0]
        for key, value in expected_values(case, ctx, sent).items():
            assert values_match(after[key], value), f"{case.property} did not change {key}"
    finally:
        if cid is not None and case.target != "default":
            if case.command != "create":
                restore = restore_payload(case, before, sent)
                if restore:
                    response = used_query.commands.channeledit(cid=cid, **restore)
                    assert response.error_id == 0, response
            channel_delete(used_query, cid)
        if parent is not None:
            channel_delete(used_query, parent)


@pytest.mark.parametrize("case", list(CLIENT_CASES.values()), ids=lambda case: case.property)
def test_client_property_round_trip(fresh_query, case):
    if case.mode == "skip":
        pytest.skip(case.note)

    clid = whoami(fresh_query)["client_id"]
    before = fresh_query.commands.clientinfo(clid=clid).data[0]
    if case.mode == "noop" and case.property not in before:
        pytest.skip(f"{case.property} is not reported by this server")
    ctx = Context(info=before)
    sent = case.kwargs(ctx)
    try:
        response = apply_client_case(fresh_query, clid, case, sent)

        assert response.error_id == 0, response
        after = fresh_query.commands.clientinfo(clid=clid).data[0]
        for key, value in expected_values(case, ctx, sent).items():
            assert values_match(after[key], value), f"{case.property} did not change {key}"
    finally:
        restore = restore_payload(case, before, sent)
        if restore:
            response = apply_client_case(fresh_query, clid, case, restore)
            assert response.error_id == 0, response


@pytest.mark.parametrize("case", list(SERVER_INSTANCE_CASES.values()), ids=lambda case: case.property)
def test_server_instance_property_round_trip(
    used_query,
    regular_server_group_ids,
    query_server_group_ids,
    template_server_group_ids,
    regular_channel_group_ids,
    template_channel_group_ids,
    case,
):
    if case.mode == "skip":
        pytest.skip(case.note)

    before = used_query.commands.instanceinfo().data[0]
    if case.mode == "noop" and case.property not in before:
        pytest.skip(f"{case.property} is not reported by this server")
    ctx = Context(
        info=before,
        regular_server_groups=regular_server_group_ids,
        query_server_groups=query_server_group_ids,
        template_server_groups=template_server_group_ids,
        regular_channel_groups=regular_channel_group_ids,
        template_channel_groups=template_channel_group_ids,
    )
    sent = case.kwargs(ctx)
    try:
        response = used_query.commands.instanceedit(**sent)

        assert response.error_id == 0, response
        after = used_query.commands.instanceinfo().data[0]
        for key, value in expected_values(case, ctx, sent).items():
            assert values_match(after[key], value), f"{case.property} did not change {key}"
    finally:
        restore = restore_payload(case, before, sent)
        if restore:
            response = used_query.commands.instanceedit(**restore)
            assert response.error_id == 0, response


@pytest.mark.parametrize("case", list(VSERVER_CASES.values()), ids=lambda case: case.property)
def test_virtual_server_property_round_trip(
    used_query,
    regular_server_group_ids,
    query_server_group_ids,
    template_server_group_ids,
    regular_channel_group_ids,
    template_channel_group_ids,
    case,
):
    if case.mode == "skip":
        pytest.skip(case.note)

    before = used_query.commands.serverinfo().data[0]
    if case.property == "virtualserver_password" and before["virtualserver_flag_password"]:
        pytest.skip("the server already has a password that cannot be read back")
    if case.mode == "noop" and case.property not in before:
        pytest.skip(f"{case.property} is not reported by this server")
    ctx = Context(
        info=before,
        regular_server_groups=regular_server_group_ids,
        query_server_groups=query_server_group_ids,
        template_server_groups=template_server_group_ids,
        regular_channel_groups=regular_channel_group_ids,
        template_channel_groups=template_channel_group_ids,
    )
    sent = case.kwargs(ctx)
    try:
        response = used_query.commands.serveredit(**sent)

        assert response.error_id == 0, response
        after = used_query.commands.serverinfo().data[0]
        for key, value in expected_values(case, ctx, sent).items():
            assert values_match(after[key], value), f"{case.property} did not change {key}"
    finally:
        restore = restore_payload(case, before, sent)
        if restore:
            response = used_query.commands.serveredit(**restore)
            assert response.error_id == 0, response


def test_channel_info_only_returns_documented_properties(used_query):
    cid = channel_create(used_query, unique_name("property-info"))
    try:
        info = used_query.commands.channelinfo(cid=cid).data[0]
    finally:
        channel_delete(used_query, cid)

    documented = {key.lower() for key in ChannelProperties}
    assert set(info) <= documented


def test_channel_info_returns_every_changeable_property(used_query):
    cid = channel_create(used_query, unique_name("property-info"))
    try:
        info = used_query.commands.channelinfo(cid=cid).data[0]
    finally:
        channel_delete(used_query, cid)

    assert set(ChangeableChannelProperties) - UNREPORTED_CHANNEL_PROPERTIES <= set(info)
    assert "pid" in info


def test_channel_list_only_returns_documented_properties(used_query):
    documented = {key.lower() for key in ChannelProperties}
    channels = used_query.commands.channellist().data

    assert channels
    for channel in channels.values():
        assert set(channel) <= documented


def test_client_list_only_returns_documented_properties(used_query):
    documented = {key.lower() for key in ClientProperties}
    clients = used_query.commands.clientlist(uid=True).data

    assert clients
    for client in clients.values():
        assert set(client) <= documented


def test_whoami_only_returns_documented_properties(used_query):
    documented = {key.lower() for key in ClientProperties}
    identity = whoami(used_query)

    assert {key.lower() for key in identity if key.startswith("client_")} <= documented


def test_client_info_only_returns_documented_properties(used_query):
    info = used_query.commands.clientinfo(clid=whoami(used_query)["client_id"]).data[0]

    documented = {key.lower() for key in ClientProperties}
    assert {key.lower() for key in info} <= documented


def test_client_info_returns_every_changeable_property(used_query):
    info = used_query.commands.clientinfo(clid=whoami(used_query)["client_id"]).data[0]

    assert set(ChangeableClientProperties) <= set(info)


def test_server_info_only_returns_documented_properties(used_query):
    info = used_query.commands.serverinfo().data[0]

    documented = {key.lower() for key in VirtualServerProperties}
    assert set(info) <= documented


def test_server_info_returns_every_changeable_property(used_query):
    info = used_query.commands.serverinfo().data[0]

    assert set(ChangeableVirtualServerProperties) - UNREPORTED_VIRTUAL_SERVER_PROPERTIES <= set(info)


def test_instance_info_only_returns_documented_properties(used_query):
    info = used_query.commands.instanceinfo().data[0]

    documented = {key.lower() for key in ServerInstanceProperties}
    assert set(info) <= documented


def test_instance_info_returns_every_changeable_property(used_query):
    info = used_query.commands.instanceinfo().data[0]

    assert set(ChangeableServerInstanceProperties) <= set(info)


def test_client_scalar_properties_match_query(bot_client):
    identity = bot_client.whoami()
    info = bot_client.get_user_info(bot_client.id)
    server = bot_client.query.commands.serverinfo().data[0]

    assert bot_client.name == identity["client_nickname"]
    assert bot_client.description == (info.client_description or "")
    assert bot_client.id == identity["client_id"]
    assert bot_client.unique_id == identity["client_unique_identifier"]
    assert bot_client.database_id == identity["client_database_id"]
    assert bot_client.server_id == server["virtualserver_id"]
    assert bot_client.server_unique_id == server["virtualserver_unique_identifier"]
    assert bot_client.server_name == server["virtualserver_name"]
    assert bot_client.server_port == server["virtualserver_port"]


def test_client_hydrates_live_dataclasses(bot_client):
    channels = bot_client.get_channels()
    assert channels
    assert isinstance(channels[0], Channel)

    channel_info = bot_client.get_channel_info(channels[0].cid)
    assert isinstance(channel_info, ChannelInfo)
    assert channel_info.cid == channels[0].cid

    users = bot_client.get_users()
    assert users
    assert all(isinstance(user, User) for user in users)

    me = next(user for user in users if user.client_unique_identifier == bot_client.unique_id)
    user_info = bot_client.get_user_info(me.clid)
    assert isinstance(user_info, UserInfo)
    assert user_info.clid == me.clid


def values_match(actual, expected):
    if isinstance(expected, (int, float)) and isinstance(actual, str):
        try:
            return float(actual) == float(expected)
        except ValueError:
            return False
    return actual == expected


def expected_values(case, ctx, sent):
    return case.verify(ctx, sent) if case.verify is not None else sent


def restore_payload(case, before, sent):
    if case.mode != "cycle" or not before:
        return {}
    if case.restore is not None:
        return case.restore(before)
    return {key: before[key] for key in sent if key in before}


def apply_client_case(query, clid, case, payload):
    if case.command == "clientupdate":
        return query.commands.clientupdate(**payload)
    return query.commands.clientedit(clid=clid, **payload)


def _channel_context(
    before,
    server_groups,
    query_groups,
    template_server_groups,
    channel_groups,
    template_channel_groups,
    parent,
):
    return Context(
        info=before,
        regular_server_groups=server_groups,
        query_server_groups=query_groups,
        template_server_groups=template_server_groups,
        regular_channel_groups=channel_groups,
        template_channel_groups=template_channel_groups,
        parent_cid=parent,
    )
