import pytest

from ts3client.ts3query.ts3query_command import TS3QueryCommand


@pytest.mark.parametrize(
    ("command", "expected"),
    [
        (TS3QueryCommand("use", kwargs={"sid": 1, "port": None}), b"use sid=1\n"),
        (TS3QueryCommand("x", kwargs={"a": True, "b": False}), b"x a=1 b=0\n"),
        (TS3QueryCommand("x", args=(("enabled", True), ("disabled", False))), b"x -enabled\n"),
        (TS3QueryCommand("use", args=(("virtual", False),), kwargs={"sid": 1}), b"use sid=1\n"),
        (TS3QueryCommand("x", args=(("a", False), ("b", False))), b"x\n"),
    ],
    ids=[
        "filters-none-kwargs",
        "encodes-bools",
        "encodes-positional-options",
        "disabled-positional-option-is-omitted",
        "all-disabled-positional-options-are-omitted",
    ],
)
def test_command_encoding(command, expected):
    assert command.encoded == expected
