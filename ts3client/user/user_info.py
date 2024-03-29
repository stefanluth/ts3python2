from dataclasses import dataclass
from typing import Optional


@dataclass
class UserInfo:
    cid: Optional[int] = None
    client_idle_time: Optional[int] = None
    client_unique_identifier: Optional[str] = None
    client_nickname: Optional[str] = None
    client_version: Optional[str] = None
    client_platform: Optional[str] = None
    client_input_muted: Optional[int] = None
    client_output_muted: Optional[int] = None
    client_outputonly_muted: Optional[int] = None
    client_input_hardware: Optional[int] = None
    client_output_hardware: Optional[int] = None
    client_default_channel: Optional[str] = None
    client_meta_data: Optional[str] = None
    client_is_recording: Optional[int] = None
    client_version_sign: Optional[str] = None
    client_security_hash: Optional[str] = None
    client_login_name: Optional[str] = None
    client_database_id: Optional[int] = None
    client_channel_group_id: Optional[int] = None
    client_servergroups: Optional[int] = None
    client_created: Optional[int] = None
    client_lastconnected: Optional[int] = None
    client_totalconnections: Optional[int] = None
    client_away: Optional[int] = None
    client_away_message: Optional[str] = None
    client_type: Optional[int] = None
    client_flag_avatar: Optional[str] = None
    client_talk_power: Optional[int] = None
    client_talk_request: Optional[int] = None
    client_talk_request_msg: Optional[str] = None
    client_description: Optional[str] = None
    client_is_talker: Optional[int] = None
    client_month_bytes_uploaded: Optional[int] = None
    client_month_bytes_downloaded: Optional[int] = None
    client_total_bytes_uploaded: Optional[int] = None
    client_total_bytes_downloaded: Optional[int] = None
    client_is_priority_speaker: Optional[int] = None
    client_unread_messages: Optional[int] = None
    client_nickname_phonetic: Optional[str] = None
    client_needed_serverquery_view_power: Optional[int] = None
    client_default_token: Optional[str] = None
    client_icon_id: Optional[int] = None
    client_is_channel_commander: Optional[int] = None
    client_country: Optional[str] = None
    client_channel_group_inherited_channel_id: Optional[int] = None
    client_badges: Optional[str] = None
    client_myteamspeak_id: Optional[str] = None
    client_integrations: Optional[str] = None
    client_myteamspeak_avatar: Optional[str] = None
    client_signed_badges: Optional[str] = None
    client_base64HashClientUID: Optional[str] = None
    connection_filetransfer_bandwidth_sent: Optional[int] = None
    connection_filetransfer_bandwidth_received: Optional[int] = None
    connection_packets_sent_total: Optional[int] = None
    connection_bytes_sent_total: Optional[int] = None
    connection_packets_received_total: Optional[int] = None
    connection_bytes_received_total: Optional[int] = None
    connection_bandwidth_sent_last_second_total: Optional[int] = None
    connection_bandwidth_sent_last_minute_total: Optional[int] = None
    connection_bandwidth_received_last_second_total: Optional[int] = None
    connection_bandwidth_received_last_minute_total: Optional[int] = None
    connection_connected_time: Optional[int] = None
    connection_client_ip: Optional[str] = None
