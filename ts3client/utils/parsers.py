import re
from dataclasses import fields
from typing import Any, cast

from ..constants import EventType
from ..event import (
    ChannelCreatedEvent,
    ChannelDeletedEvent,
    ChannelDescriptionChangedEvent,
    ChannelEditedEvent,
    ChannelMovedEvent,
    ChannelPasswordChangedEvent,
    ClientEnterViewEvent,
    ClientLeftViewEvent,
    ClientMovedEvent,
    Event,
    ServerEditedEvent,
    TokenUsedEvent,
)
from ..message import Message
from . import patterns
from .formatters import query_to_string, string_to_query


def boolean_to_option(option: str, value: bool) -> str:
    return f"-{option}" if value else ""


def boolean_to_literal(boolean: bool) -> str:
    return "1" if boolean else "0"


def response_to_dict(response: str) -> dict[str, str | int]:
    """Converts a query response to a dict."""
    response_dict = dict()

    for key_value_pair in response.split():
        key = key_value_pair.split("=")[0]
        value = key_value_pair[len(key) + 1 :]

        try:
            response_dict[key] = int(value)
        except ValueError:
            response_dict[key] = query_to_string(value)

    return response_dict


def dict_to_query_kwargs(parameters: dict[str, str | int | float | bool]) -> list[str]:
    """Converts a dict to a list of query kwargs."""
    return [
        f"{key}={boolean_to_literal(value) if isinstance(value, bool) else string_to_query(value)}"
        for key, value in parameters.items()
    ]


def parse_response(response: bytes) -> tuple[dict[int | str, Any], list[Event], list[Message]]:
    """Parses a query response to a dict, a list of events and a list of messages."""
    events = []
    messages = []
    response_str = response.decode()

    response_str = re.sub(patterns.RESPONSE_END, "", response_str)

    for match in re.finditer(patterns.MESSAGE, response_str):
        messages.append(parse_message_match(match))
        response_str = response_str.replace(match.group(), "")

    for match in re.finditer(patterns.EVENT, response_str):
        events.append(parse_event_match(match))
        response_str = response_str.replace(match.group(), "")

    chunks = [chunk for chunk in response_str.split("|") if chunk.strip()]
    data: dict[int | str, Any] = {i: response_to_dict(chunk) for i, chunk in enumerate(chunks)}

    return data, events, messages


EVENT_CLASSES = {
    EventType.CHANNEL_CREATED: ChannelCreatedEvent,
    EventType.CHANNEL_DELETED: ChannelDeletedEvent,
    EventType.CHANNEL_DESCRIPTION_CHANGED: ChannelDescriptionChangedEvent,
    EventType.CHANNEL_EDITED: ChannelEditedEvent,
    EventType.CHANNEL_MOVED: ChannelMovedEvent,
    EventType.CHANNEL_PASSWORD_CHANGED: ChannelPasswordChangedEvent,
    EventType.CLIENT_ENTER_VIEW: ClientEnterViewEvent,
    EventType.CLIENT_LEFT_VIEW: ClientLeftViewEvent,
    EventType.CLIENT_MOVED: ClientMovedEvent,
    EventType.SERVER_EDITED: ServerEditedEvent,
    EventType.TOKEN_USED: TokenUsedEvent,
}


def parse_event_match(re_match: re.Match[str]) -> Event:
    event_type = EventType(re_match.group("event"))
    data = response_to_dict(re_match.group()[re_match.group().index(" ") + 1 :])
    event_class = EVENT_CLASSES.get(event_type)
    if event_class is None:
        return Event()

    allowed = {field.name for field in fields(event_class)}
    return cast(Any, event_class)(**{key: value for key, value in data.items() if key in allowed})


def parse_message_match(match: re.Match[str]) -> Message:
    return Message(
        targetmode=int(match.group("targetmode")),
        msg=match.group("msg"),
        target=int(match.group("target") or 0),
        invokerid=int(match.group("invokerid")),
        invokername=query_to_string(match.group("invokername")),
        invokeruid=match.group("invokeruid"),
    )


def parse_help(help: bytes) -> tuple[dict[int | str, Any], list[Event], list[Message]]:
    """Parses the help response to a dict."""

    _, events, messages = parse_response(help)
    help_text = re.sub(patterns.RESPONSE_END, "", help.decode()).strip()
    data: dict[int | str, Any] = {
        "help": help_text,
    }

    return (data, events, messages)
