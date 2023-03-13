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
from utils import patterns
from utils.formatters import query_to_string, string_to_query


def boolean_to_option(option: str, value: bool) -> str:
    return f"-{option}" if value else ""


def boolean_to_literal(boolean: bool) -> str:
    return "1" if boolean else "0"


def response_to_dict(response: str) -> dict:
    """
    Converts a query response to a dict.
    """
    response_dict = dict()

    for key_value_pair in response.split():
        key = key_value_pair.split("=")[0]
        value = key_value_pair[len(key) + 1 :]

        try:
            response_dict[key] = int(value)
        except ValueError:
            response_dict[key] = query_to_string(value)

    return response_dict


def dict_to_query_kwargs(parameters: dict) -> list[str]:
    """
    Converts a dict to a list of query kwargs.
    """
    return [
        f"{key}={boolean_to_literal(value) if isinstance(value, bool) else string_to_query(value)}"
        for key, value in parameters.items()
    ]


def parse_response(response: bytes) -> tuple[dict, list[Event], list[Message]]:
    """
    Parses a query response to a dict, a list of events and a list of messages.
    """
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

    if "|" not in response_str:
        data = response_to_dict(response_str)
    else:
        data = {
            i: response_to_dict(data) for i, data in enumerate(response_str.split("|"))
        }

    return data, events, messages


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
