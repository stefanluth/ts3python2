import pytest

from ts3client.utils.formatters import query_to_string, string_to_query


@pytest.mark.parametrize(
    ("value", "encoded"),
    [
        pytest.param(r"C:\steam", r"C:\\steam", marks=pytest.mark.bug, id="backslash-before-s"),
        pytest.param(" foo ", r"\sfoo\s", marks=pytest.mark.bug, id="leading-and-trailing-space"),
        pytest.param("a|b/c\nd\te", r"a\pb\/c\nd\te", id="pipe-slash-newline-tab"),
    ],
)
def test_encode_escapes_and_round_trips(value, encoded):
    assert string_to_query(value) == encoded
    assert query_to_string(encoded) == value
