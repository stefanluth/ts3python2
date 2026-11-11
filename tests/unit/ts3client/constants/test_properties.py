from dataclasses import fields

import pytest

from tests.support.property_cases import (
    CHANNEL_CASES,
    CLIENT_CASES,
    SERVER_INSTANCE_CASES,
    VSERVER_CASES,
)
from ts3client.channel import Channel, ChannelInfo
from ts3client.constants import (
    ChangeableChannelProperties,
    ChangeableClientProperties,
    ChangeableServerInstanceProperties,
    ChangeableVirtualServerProperties,
    ChannelProperties,
    ClientProperties,
    Codec,
    ServerGroupType,
    ServerInstanceProperties,
    TargetMode,
    TextMessageTargetMode,
    VirtualServerProperties,
)
from ts3client.user import User, UserInfo

FAMILIES = [
    pytest.param("channel", ChannelProperties, ChangeableChannelProperties, CHANNEL_CASES, id="channel"),
    pytest.param("client", ClientProperties, ChangeableClientProperties, CLIENT_CASES, id="client"),
    pytest.param(
        "server-instance",
        ServerInstanceProperties,
        ChangeableServerInstanceProperties,
        SERVER_INSTANCE_CASES,
        id="server-instance",
    ),
    pytest.param(
        "virtual-server",
        VirtualServerProperties,
        ChangeableVirtualServerProperties,
        VSERVER_CASES,
        id="virtual-server",
    ),
]

DATACLASSES = [
    pytest.param(ChannelInfo, ChannelProperties, id="channel-info"),
    pytest.param(Channel, ChannelProperties, id="channel"),
    pytest.param(UserInfo, ClientProperties, id="user-info"),
    pytest.param(User, ClientProperties, id="user"),
]


@pytest.mark.parametrize(("name", "properties", "changeable", "cases"), FAMILIES)
def test_property_keys_are_normalized(name, properties, changeable, cases):
    for key in properties:
        assert key == key.strip(), f"{name} property {key!r} has surrounding whitespace"
        assert key == key.upper(), f"{name} property {key!r} is not uppercase"


@pytest.mark.parametrize(("name", "properties", "changeable", "cases"), FAMILIES)
def test_changeable_properties_are_lowercase_full_names(name, properties, changeable, cases):
    full_names = {key.lower() for key in properties}

    assert len(changeable) == len(set(changeable)), f"{name} has duplicate changeable properties"
    assert all(value == value.lower() for value in changeable)
    assert set(changeable) <= full_names, f"{name} advertises properties that do not exist"


@pytest.mark.parametrize(("name", "properties", "changeable", "cases"), FAMILIES)
def test_every_changeable_property_has_a_live_case(name, properties, changeable, cases):
    assert set(cases) == set(changeable), f"{name} changeable properties are not fully covered"

    for key, case in cases.items():
        assert case.property == key
        if case.mode == "noop":
            assert case.note, f"{name} noop case {key!r} does not explain why"


@pytest.mark.parametrize(("dataclass_type", "properties"), DATACLASSES)
def test_dataclass_fields_are_documented_properties(dataclass_type, properties):
    documented = {key.lower() for key in properties}
    used = {field.name.lower() for field in fields(dataclass_type)}

    assert used <= documented, f"{dataclass_type.__name__} uses undocumented properties"


def test_text_message_target_mode_matches_target_mode():
    assert {mode.value for mode in TextMessageTargetMode} == {mode.value for mode in TargetMode}


def test_codec_values_include_the_legacy_and_opus_families():
    assert {codec.value for codec in Codec} == set(range(6))


def test_server_group_types_are_auto_update_types():
    assert {group.value for group in ServerGroupType} == {10, 15, 20, 25, 30, 35, 40, 45, 50}


@pytest.mark.bug
def test_icon_and_template_group_properties_are_changeable():
    assert "channel_icon_id" in ChangeableChannelProperties
    assert "serverinstance_template_channeldefault_group" in ChangeableServerInstanceProperties
