import pytest

from ts3client.utils import validators

FAMILY_VALIDATORS = [
    pytest.param(validators._validate_channel_kwargs, "channel_topic", id="channel"),
    pytest.param(validators._validate_client_kwargs, "client_description", id="client"),
    pytest.param(
        validators._validate_server_instance_kwargs,
        "serverinstance_filetransfer_port",
        id="server-instance",
    ),
    pytest.param(validators._validate_virtual_server_kwargs, "virtualserver_name", id="virtual-server"),
]


def test_validate_kwargs_checks_scalar_values():
    for value in ("text", 1, 1.5):
        validators._validate_kwargs({"property": value})

    for value in (None, [], {}, object()):
        with pytest.raises(ValueError):
            validators._validate_kwargs({"property": value})


@pytest.mark.parametrize(("validator", "property_name"), FAMILY_VALIDATORS)
def test_validators_accept_known_and_reject_unknown_properties(validator, property_name):
    assert validator({property_name: "value"}) == {property_name: "value"}

    with pytest.raises(ValueError):
        validator({"not_a_real_property": "value"})


@pytest.mark.parametrize(
    "property_name",
    [
        "serverinstance_pending_connections_per_ip",
        "serverinstance_serverquery_max_connections_per_ip",
    ],
)
def test_server_instance_validator_accepts_query_connection_limits(property_name):
    assert validators._validate_server_instance_kwargs({property_name: "64"}) == {property_name: "64"}


def test_changeable_kwargs_are_lowercased_and_unique():
    assert validators._validate_channel_kwargs({"CHANNEL_TOPIC": "news"}) == {"channel_topic": "news"}

    with pytest.raises(ValueError, match="Duplicate argument"):
        validators._validate_channel_kwargs({"CHANNEL_TOPIC": "a", "channel_topic": "b"})
