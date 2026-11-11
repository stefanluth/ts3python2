from ts3client.ts3query.ts3query_command import TS3QueryCommand


def test_command_filters_none_kwargs():
    assert TS3QueryCommand("use", kwargs={"sid": 1, "port": None}).encoded == b"use sid=1\n"


def test_command_encodes_bool_kwargs():
    assert TS3QueryCommand("x", kwargs={"a": True, "b": False}).encoded == b"x a=1 b=0\n"


def test_command_escapes_string_values():
    assert TS3QueryCommand("x", kwargs={"msg": "a b"}).encoded == b"x msg=a\\sb\n"


def test_command_encodes_positional_option_args():
    assert TS3QueryCommand("x", args=(("enabled", True), ("disabled", False))).encoded == b"x -enabled\n"


def test_command_encodes_args_before_kwargs():
    assert TS3QueryCommand("x", args=(("flag", True),), kwargs={"a": 1}).encoded == b"x -flag a=1\n"
