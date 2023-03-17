from dataclasses import dataclass
from typing import Optional


@dataclass
class ChannelInfo:
    pid: Optional[int] = None
    channel_name: Optional[str] = None
    channel_topic: Optional[str] = None
    channel_description: Optional[str] = None
    channel_password: Optional[str] = None
    channel_codec: Optional[int] = None
    channel_codec_quality: Optional[int] = None
    channel_maxclients: Optional[int] = None
    channel_maxfamilyclients: Optional[int] = None
    channel_order: Optional[int] = None
    channel_flag_permanent: Optional[int] = None
    channel_flag_semi_permanent: Optional[int] = None
    channel_flag_default: Optional[int] = None
    channel_flag_password: Optional[int] = None
    channel_codec_latency_factor: Optional[int] = None
    channel_codec_is_unencrypted: Optional[int] = None
    channel_security_salt: Optional[str] = None
    channel_delete_delay: Optional[int] = None
    channel_unique_identifier: Optional[str] = None
    channel_flag_maxclients_unlimited: Optional[int] = None
    channel_flag_maxfamilyclients_unlimited: Optional[int] = None
    channel_flag_maxfamilyclients_inherited: Optional[int] = None
    channel_filepath: Optional[str] = None
    channel_needed_talk_power: Optional[int] = None
    channel_forced_silence: Optional[int] = None
    channel_name_phonetic: Optional[str] = None
    channel_icon_id: Optional[int] = None
    channel_banner_gfx_url: Optional[str] = None
    channel_banner_mode: Optional[int] = None
    seconds_empty: Optional[int] = None
