import pytest

from ts3client.utils.formatters import query_to_string, string_to_query


@pytest.mark.bug
def test_round_trip_backslash_before_s():
    assert query_to_string(string_to_query(r"C:\steam")) == r"C:\steam"


@pytest.mark.bug
def test_round_trip_preserves_leading_and_trailing_space():
    assert query_to_string(string_to_query(" foo ")) == " foo "


def test_encode_escapes_pipe_slash_newline_and_tab():
    assert string_to_query("a|b/c\nd\te") == r"a\pb\/c\nd\te"
