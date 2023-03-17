from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional
from constants import ChangeableClientProperties
from dataclasses import dataclass, field


@dataclass
class ClientInfo:
    cid: int
    client_idle_time: int
    client_unique_identifier: str
    client_nickname: str
    client_version: str
    client_platform: str
    client_input_muted: int
    client_output_muted: int
    client_outputonly_muted: int
    client_input_hardware: int
    client_output_hardware: int
    client_default_channel: str
    client_meta_data: str
    client_is_recording: int
    client_version_sign: str
    client_security_hash: str
    client_login_name: str
    client_database_id: int
    client_channel_group_id: int
    client_servergroups: int
    client_created: int
    client_lastconnected: int
    client_totalconnections: int
    client_away: int
    client_away_message: str
    client_type: int
    client_flag_avatar: str
    client_talk_power: int
    client_talk_request: int
    client_talk_request_msg: str
    client_description: str
    client_is_talker: int
    client_month_bytes_uploaded: int
    client_month_bytes_downloaded: int
    client_total_bytes_uploaded: int
    client_total_bytes_downloaded: int
    client_is_priority_speaker: int
    client_unread_messages: int
    client_nickname_phonetic: str
    client_needed_serverquery_view_power: int
    client_default_token: str
    client_icon_id: int
    client_is_channel_commander: int
    client_country: str
    client_channel_group_inherited_channel_id: int
    client_badges: str
    client_myteamspeak_id: str
    client_integrations: str
    client_myteamspeak_avatar: str
    client_signed_badges: str
    client_base64HashClientUID: str
    connection_filetransfer_bandwidth_sent: int
    connection_filetransfer_bandwidth_received: int
    connection_packets_sent_total: int
    connection_bytes_sent_total: int
    connection_packets_received_total: int
    connection_bytes_received_total: int
    connection_bandwidth_sent_last_second_total: int
    connection_bandwidth_sent_last_minute_total: int
    connection_bandwidth_received_last_second_total: int
    connection_bandwidth_received_last_minute_total: int
    connection_connected_time: int
    connection_client_ip: str
