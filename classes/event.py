from dataclasses import dataclass
from typing import Optional
from constants import EventType


class Event:
    """
    Represents a TeamSpeak event.
    """

    event_type: str = None
    used: bool = False


@dataclass
class ChannelCreatedEvent(Event):
    event_type = EventType.CHANNEL_CREATED
    channel_topic: Optional[str] = None
    cid: Optional[int] = None
    invokerid: Optional[int] = None
    invokername: Optional[str] = None
    invokeruid: Optional[str] = None
    reasonid: Optional[int] = None


@dataclass
class ChannelDeletedEvent(Event):
    event_type = EventType.CHANNEL_DELETED
    cid: Optional[int] = None
    invokerid: Optional[int] = None
    invokername: Optional[str] = None
    invokeruid: Optional[str] = None
    reasonid: Optional[int] = None


@dataclass
class ChannelDescriptionChangedEvent(Event):
    event_type = EventType.CHANNEL_DESCRIPTION_CHANGED
    cid: Optional[int] = None


@dataclass
class ChannelEditedEvent(Event):
    event_type = EventType.CHANNEL_EDITED
    cid: Optional[int] = None
    invokerid: Optional[int] = None
    invokername: Optional[str] = None
    invokeruid: Optional[str] = None
    reasonid: Optional[int] = None
    channel_codec_is_unencrypted: Optional[bool] = None
    channel_codec_latency_factor: Optional[int] = None
    channel_codec_quality: Optional[int] = None
    channel_codec: Optional[int] = None
    channel_delete_delay: Optional[int] = None
    channel_flag_default: Optional[bool] = None
    channel_flag_maxclients_unlimited: Optional[bool] = None
    channel_flag_maxfamilyclients_inherited: Optional[bool] = None
    channel_flag_maxfamilyclients_unlimited: Optional[bool] = None
    channel_flag_password: Optional[bool] = None
    channel_flag_permanent: Optional[bool] = None
    channel_flag_semi_permanent: Optional[bool] = None
    channel_icon_id: Optional[int] = None
    channel_maxclients: Optional[int] = None
    channel_maxfamilyclients: Optional[int] = None
    channel_name_phonetic: Optional[str] = None
    channel_name: Optional[str] = None
    channel_needed_talk_power: Optional[int] = None
    channel_order: Optional[int] = None
    channel_topic: Optional[str] = None


@dataclass
class ChannelMovedEvent(Event):
    event_type = EventType.CHANNEL_MOVED
    cid: Optional[int] = None
    cpid: Optional[int] = None
    order: Optional[int] = None
    invokerid: Optional[int] = None
    invokername: Optional[str] = None
    invokeruid: Optional[str] = None


@dataclass
class ChannelPasswordChangedEvent(Event):
    event_type = EventType.CHANNEL_PASSWORD_CHANGED
    cid: Optional[int] = None


@dataclass
class ClientEnterViewEvent(Event):
    event_type = EventType.CLIENT_ENTER_VIEW
    cfid: Optional[int] = None
    clid: Optional[int] = None
    client_away_message: Optional[str] = None
    client_away: Optional[int] = None
    client_badges: Optional[str] = None
    client_channel_group_id: Optional[int] = None
    client_channel_group_inherited_channel_id: Optional[int] = None
    client_country: Optional[str] = None
    client_database_id: Optional[int] = None
    client_description: Optional[str] = None
    client_flag_avatar: Optional[str] = None
    client_icon_id: Optional[int] = None
    client_input_hardware: Optional[int] = None
    client_input_muted: Optional[int] = None
    client_is_channel_commander: Optional[int] = None
    client_is_priority_speaker: Optional[int] = None
    client_is_recording: Optional[int] = None
    client_is_talker: Optional[int] = None
    client_meta_data: Optional[str] = None
    client_needed_serverquery_view_power: Optional[int] = None
    client_nickname_phonetic: Optional[str] = None
    client_nickname: Optional[str] = None
    client_output_hardware: Optional[int] = None
    client_output_muted: Optional[int] = None
    client_outputonly_muted: Optional[int] = None
    client_servergroups: Optional[str] = None
    client_talk_power: Optional[int] = None
    client_talk_request_msg: Optional[str] = None
    client_talk_request: Optional[int] = None
    client_type: Optional[int] = None
    client_unique_identifier: Optional[str] = None
    client_unread_messages: Optional[int] = None
    ctid: Optional[int] = None
    reasonid: Optional[int] = None


@dataclass
class ClientLeftViewEvent(Event):
    event_type = EventType.CLIENT_LEFT_VIEW
    bantime: Optional[int] = None
    cfid: Optional[int] = None
    clid: Optional[int] = None
    ctid: Optional[int] = None
    invokerid: Optional[int] = None
    invokername: Optional[str] = None
    invokeruid: Optional[str] = None
    reasonid: Optional[int] = None
    reasonmsg: Optional[str] = None


@dataclass
class ClientMovedEvent(Event):
    event_type = EventType.CLIENT_MOVED
    clid: Optional[int] = None
    ctid: Optional[int] = None
    reasonid: Optional[int] = None
    invokerid: Optional[int] = None
    invokername: Optional[str] = None
    invokeruid: Optional[str] = None


@dataclass
class ServerEditedEvent(Event):
    event_type = EventType.SERVER_EDITED
    invokerid: Optional[int] = None
    invokername: Optional[str] = None
    invokeruid: Optional[str] = None
    reasonid: Optional[int] = None
    virtualserver_channel_temp_delete_delay_default: Optional[int] = None
    virtualserver_codec_encryption_mode: Optional[int] = None
    virtualserver_default_channel_group: Optional[int] = None
    virtualserver_default_server_group: Optional[int] = None
    virtualserver_hostbanner_gfx_interval: Optional[int] = None
    virtualserver_hostbanner_gfx_url: Optional[str] = None
    virtualserver_hostbanner_mode: Optional[int] = None
    virtualserver_hostbanner_url: Optional[str] = None
    virtualserver_hostbutton_gfx_url: Optional[str] = None
    virtualserver_hostbutton_tooltip: Optional[str] = None
    virtualserver_hostbutton_url: Optional[str] = None
    virtualserver_icon_id: Optional[int] = None
    virtualserver_name_phonetic: Optional[str] = None
    virtualserver_name: Optional[str] = None
    virtualserver_priority_speaker_dimm_modificator: Optional[int] = None


@dataclass
class TokenUsedEvent(Event):
    event_type = EventType.TOKEN_USED
    clid: Optional[int] = None
    cldbid: Optional[int] = None
    cluid: Optional[str] = None
    token: Optional[str] = None
    tokencustomset: Optional[str] = None
    token1: Optional[str] = None
    token2: Optional[str] = None
