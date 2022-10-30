import re

from classes.event import (
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
from classes.message import Message
from query.definitions import EventType
from utils.formatters import query_to_string, string_to_query


def boolean_to_option(boolean: bool) -> str:
    return f"-{boolean=}".split("=")[0] if boolean else ""


def boolean_to_literal(boolean: bool) -> str:
    return "1" if boolean else "0"


def response_to_dict(response: str) -> dict:
    r_dict = dict()

    for key_value_pair in response.split():
        key = key_value_pair.split("=")[0]
        value = key_value_pair[len(key) + 1 :]

        try:
            r_dict[key] = int(value)
        except ValueError:
            r_dict[key] = query_to_string(value)

    return r_dict


def dict_to_query_parameters(parameters: dict) -> list[str]:
    return [
        f"{key}={boolean_to_literal(value) if isinstance(value, bool) else string_to_query(value)}"
        for key, value in parameters.items()
    ]


def parse_response_match(response: bytes) -> dict:
    response = response.decode()

    if response.find("|"):
        return [response_to_dict(r) for r in response.split("|")]
    else:
        return [response_to_dict(response)]


def parse_event_match(match: re.Match[str]) -> Event:
    event_type = EventType(match.group("event"))
    data = response_to_dict(match.group()[match.group().index(" ") + 1 :])

    match event_type:
        case EventType.CHANNEL_CREATED:
            return ChannelCreatedEvent(**data)
        case EventType.CHANNEL_DELETED:
            return ChannelDeletedEvent(**data)
        case EventType.CHANNEL_DESCRIPTION_CHANGED:
            return ChannelDescriptionChangedEvent(**data)
        case EventType.CHANNEL_EDITED:
            return ChannelEditedEvent(**data)
        case EventType.CHANNEL_MOVED:
            return ChannelMovedEvent(**data)
        case EventType.CHANNEL_PASSWORD_CHANGED:
            return ChannelPasswordChangedEvent(**data)
        case EventType.CLIENT_ENTERVIEW:
            return ClientEnterViewEvent(**data)
        case EventType.CLIENT_LEFTVIEW:
            return ClientLeftViewEvent(**data)
        case EventType.CLIENT_MOVED:
            return ClientMovedEvent(**data)
        case EventType.SERVER_EDITED:
            return ServerEditedEvent(**data)
        case EventType.TOKEN_USED:
            return TokenUsedEvent(**data)
        case _:
            return Event()


def parse_message_match(match: re.Match[str]) -> Message:
    return Message(
        targetmode=int(match.group("targetmode")),
        msg=match.group("msg"),
        target=int(match.group("target")),
        invokerid=int(match.group("invokerid")),
        invokername=match.group("invokername"),
        invokeruid=match.group("invokeruid"),
    )
