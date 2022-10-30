from dataclasses import dataclass


class Event:
    """
    Represents a TeamSpeak event.
    """

    pass


@dataclass
class ChannelCreatedEvent(Event):
    channel_topic: str
    cid: int
    invokerid: int
    invokername: str
    invokeruid: str
    reasonid: int


@dataclass
class ChannelDeletedEvent(Event):
    cid: int
    invokerid: int
    invokername: str
    invokeruid: str
    reasonid: int


@dataclass
class ChannelDescriptionChangedEvent(Event):
    cid: int


@dataclass
class ChannelEditedEvent(Event):
    cid: int
    invokerid: int
    invokername: str
    invokeruid: str
    reasonid: int
    channel_codec_is_unencrypted: bool
    channel_codec_latency_factor: int
    channel_codec_quality: int
    channel_codec: int
    channel_delete_delay: int
    channel_flag_default: bool
    channel_flag_maxclients_unlimited: bool
    channel_flag_maxfamilyclients_inherited: bool
    channel_flag_maxfamilyclients_unlimited: bool
    channel_flag_password: bool
    channel_flag_permanent: bool
    channel_flag_semi_permanent: bool
    channel_icon_id: int
    channel_maxclients: int
    channel_maxfamilyclients: int
    channel_name_phonetic: str
    channel_name: str
    channel_needed_talk_power: int
    channel_order: int
    channel_topic: str


@dataclass
class ChannelMovedEvent(Event):
    cid: int
    cpid: int
    order: int
    invokerid: int
    invokername: str
    invokeruid: str


@dataclass
class ChannelPasswordChangedEvent(Event):
    cid: int


@dataclass
class ClientEnterViewEvent(Event):
    cfid: int
    clid: int
    client_away_message: str
    client_away: int
    client_badges: str
    client_channel_group_id: int
    client_channel_group_inherited_channel_id: int
    client_country: str
    client_database_id: int
    client_description: str
    client_flag_avatar: str
    client_icon_id: int
    client_input_hardware: int
    client_input_muted: int
    client_is_channel_commander: int
    client_is_priority_speaker: int
    client_is_recording: int
    client_is_talker: int
    client_meta_data: str
    client_needed_serverquery_view_power: int
    client_nickname_phonetic: str
    client_nickname: str
    client_output_hardware: int
    client_output_muted: int
    client_outputonly_muted: int
    client_servergroups: str
    client_talk_power: int
    client_talk_request_msg: str
    client_talk_request: int
    client_type: int
    client_unique_identifier: str
    client_unread_messages: int
    ctid: int
    reasonid: int


@dataclass
class ClientLeftViewEvent(Event):
    bantime: int
    cfid: int
    clid: int
    ctid: int
    invokerid: int
    invokername: str
    invokeruid: str
    reasonid: int
    reasonmsg: str


@dataclass
class ClientMovedEvent(Event):
    clid: int
    ctid: int
    invokerid: int
    invokername: str
    invokeruid: str
    reasonid: int


@dataclass
class ServerEditedEvent(Event):
    invokerid: int
    invokername: str
    invokeruid: str
    reasonid: int
    virtualserver_channel_temp_delete_delay_default: int
    virtualserver_codec_encryption_mode: int
    virtualserver_default_channel_group: int
    virtualserver_default_server_group: int
    virtualserver_hostbanner_gfx_interval: int
    virtualserver_hostbanner_gfx_url: str
    virtualserver_hostbanner_mode: int
    virtualserver_hostbanner_url: str
    virtualserver_hostbutton_gfx_url: str
    virtualserver_hostbutton_tooltip: str
    virtualserver_hostbutton_url: str
    virtualserver_icon_id: int
    virtualserver_name_phonetic: str
    virtualserver_name: str
    virtualserver_priority_speaker_dimm_modificator: int


@dataclass
class TokenUsedEvent(Event):
    clid: int
    cldbid: int
    cluid: str
    token: str
    tokencustomset: str
    token1: str
    token2: str
