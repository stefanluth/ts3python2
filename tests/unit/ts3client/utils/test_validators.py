import pytest

from ts3client.utils.validators import _validate_client_kwargs, _validate_kwargs


@pytest.mark.parametrize("value", [None, [], {}, object()])
def test_validate_kwargs_rejects_other_types(value):
    with pytest.raises(ValueError):
        _validate_kwargs({"a": value})


def test_client_changeable_rejects_unknown_property():
    with pytest.raises(ValueError):
        _validate_client_kwargs({"not_a_property": "x"})


def test_validate_kwargs_accepts_supported_types():
    _validate_kwargs({"text": "x", "integer": 1, "floating": 1.5})


def test_client_changeable_matches_case_insensitively():
    _validate_client_kwargs({"CLIENT_NICKNAME": "name"})
