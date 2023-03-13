"""
Parsed from the TeamSpeak 3 Server Query documentation
"""

CHANNEL_PROPERTIES = {
    "CHANNEL_NAME": {
        "description": "Name of the channel",
        "changeable": True,
    },
    "CHANNEL_TOPIC": {
        "description": "Topic of the channel",
        "changeable": True,
    },
    "CHANNEL_DESCRIPTION": {
        "description": "Description of the channel",
        "changeable": True,
    },
    "CHANNEL_PASSWORD": {
        "description": "Password of the channel",
        "changeable": True,
    },
    "CHANNEL_FLAG_PASSWORD": {
        "description": "Indicates whether the channel has a password set or not",
        "changeable": False,
    },
    "CHANNEL_CODEC": {
        "description": "Codec used by the channel Definitions",
        "changeable": True,
    },
    "CHANNEL_CODEC_QUALITY": {
        "description": "Codec quality used by the channel",
        "changeable": True,
    },
    "CHANNEL_MAXCLIENTS": {
        "description": "Individual max number of clients for the channel",
        "changeable": True,
    },
    "CHANNEL_MAXFAMILYCLIENTS": {
        "description": "Individual max number of clients for the channel family",
        "changeable": True,
    },
    "CHANNEL_ORDER": {
        "description": "ID of the channel below which the channel is positioned",
        "changeable": True,
    },
    "CHANNEL_FLAG_PERMANENT": {
        "description": "Indicates whether the channel is permanent or not",
        "changeable": True,
    },
    "CHANNEL_FLAG_SEMI_PERMANENT": {
        "description": "Indicates whether the channel is semi-permanent or not",
        "changeable": True,
    },
    "CHANNEL_FLAG_TEMPORARY": {
        "description": "Indicates whether the channel is temporary or not",
        "changeable": True,
    },
    "CHANNEL_FLAG_DEFAULT": {
        "description": "Indicates whether the channel is the virtual servers default channel or not",
        "changeable": True,
    },
    "CHANNEL_FLAG_MAXCLIENTS_UNLIMITED": {
        "description": "Indicates whether the channel has a max clients limit or not",
        "changeable": True,
    },
    "CHANNEL_FLAG_MAXFAMILYCLIENTS_UNLIMITED": {
        "description": "Indicates whether the channel has a max family clients limit or not",
        "changeable": True,
    },
    "CHANNEL_FLAG_MAXFAMILYCLIENTS_INHERITED": {
        "description": "Indicates whether the channel inherits the max family clients from his parent channel or not",
        "changeable": True,
    },
    "CHANNEL_NEEDED_TALK_POWER": {
        "description": "Needed talk power for this channel",
        "changeable": True,
    },
    "CHANNEL_NAME_PHONETIC": {
        "description": "Phonetic name of the channel",
        "changeable": True,
    },
    "CHANNEL_FILEPATH": {
        "description": "Path of the channels file repository",
        "changeable": False,
    },
    "CHANNEL_FORCED_SILENCE": {
        "description": "Indicates whether the channel is silenced or not",
        "changeable": False,
    },
    "CHANNEL_ICON_ID ": {
        "description": "CRC32 checksum of the channel icon",
        "changeable": True,
    },
    "CHANNEL_CODEC_IS_UNENCRYPTED": {
        "description": "Indicates whether speech data transmitted in this channel is encrypted or not",
        "changeable": True,
    },
    "CPID": {
        "description": "The channels parent ID",
        "changeable": True,
    },
    "CID": {
        "description": "The channels ID",
        "changeable": False,
    },
}

CHANGEABLE_CHANNEL_PROPERTIES = {
    key: value for key, value in CHANNEL_PROPERTIES.items() if value["changeable"]
}
