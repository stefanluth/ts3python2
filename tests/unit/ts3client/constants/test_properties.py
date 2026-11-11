import pytest

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

FAMILIES = [
    pytest.param("channel", ChannelProperties, ChangeableChannelProperties, id="channel"),
    pytest.param("client", ClientProperties, ChangeableClientProperties, id="client"),
    pytest.param("server-instance", ServerInstanceProperties, ChangeableServerInstanceProperties, id="server-instance"),
    pytest.param("virtual-server", VirtualServerProperties, ChangeableVirtualServerProperties, id="virtual-server"),
]


@pytest.mark.parametrize(("name", "properties", "changeable"), FAMILIES)
def test_property_keys_are_normalized(name, properties, changeable):
    for key in properties:
        assert key == key.strip(), f"{name} property {key!r} has surrounding whitespace"
        assert key == key.upper(), f"{name} property {key!r} is not uppercase"


@pytest.mark.parametrize(("name", "properties", "changeable"), FAMILIES)
def test_changeable_properties_are_lowercase_full_names(name, properties, changeable):
    full_names = {key.lower() for key in properties}

    assert len(changeable) == len(set(changeable)), f"{name} has duplicate changeable properties"
    assert all(value == value.lower() for value in changeable)
    assert set(changeable) <= full_names, f"{name} advertises properties that do not exist"


@pytest.mark.bug
def test_icon_and_template_group_properties_are_changeable():
    assert "channel_icon_id" in ChangeableChannelProperties
    assert "serverinstance_template_channeldefault_group" in ChangeableServerInstanceProperties
