"""
Parsed from the TeamSpeak 3 Server Query documentation
"""

CLIENT_PROPERTIES = {
    "CLIENT_UNIQUE_IDENTIFIER": {
        "description": "Unique ID of the client",
        "changeable": False,
    },
    "CLIENT_NICKNAME": {
        "description": "Nickname of the client",
        "changeable": True,
    },
    "CLIENT_VERSION": {
        "description": "Client version information including build number",
        "changeable": False,
    },
    "CLIENT_PLATFORM": {
        "description": "Operating system the client is running on",
        "changeable": False,
    },
    "CLIENT_INPUT_MUTED": {
        "description": "Indicates whether the client has their microphone muted or not",
        "changeable": False,
    },
    "CLIENT_OUTPUT_MUTED": {
        "description": "Indicates whether the client has their speakers muted or not",
        "changeable": False,
    },
    "CLIENT_INPUT_HARDWARE": {
        "description": "Indicates whether the client has enabled their capture device or not",
        "changeable": False,
    },
    "CLIENT_OUTPUT_HARDWARE": {
        "description": "Indicates whether the client has enabled their playback device or not",
        "changeable": False,
    },
    "CLIENT_DEFAULT_CHANNEL": {
        "description": "Default channel of the client",
        "changeable": False,
    },
    "CLIENT_LOGIN_NAME": {
        "description": "Username of a ServerQuery client",
        "changeable": False,
    },
    "CLIENT_DATABASE_ID": {
        "description": "Database ID of the client",
        "changeable": False,
    },
    "CLIENT_CHANNEL_GROUP_ID": {
        "description": "Current channel group ID of the client",
        "changeable": False,
    },
    "CLIENT_SERVER_GROUPS": {
        "description": "Current server group IDs of the client separated by a comma",
        "changeable": False,
    },
    "CLIENT_CREATED": {
        "description": "Creation date and time of the clients first connection to the server as UTC timestamp",
        "changeable": False,
    },
    "CLIENT_LASTCONNECTED": {
        "description": "Creation date and time of the clients last connection to the server as UTC timestamp",
        "changeable": False,
    },
    "CLIENT_TOTALCONNECTIONS": {
        "description": "Total number of connections from this client since the server was started",
        "changeable": False,
    },
    "CLIENT_AWAY": {
        "description": "Indicates whether the client is away or not",
        "changeable": False,
    },
    "CLIENT_AWAY_MESSAGE": {
        "description": "Away message of the client",
        "changeable": False,
    },
    "CLIENT_TYPE": {
        "description": "Indicates whether the client is a ServerQuery client or not",
        "changeable": False,
    },
    "CLIENT_FLAG_AVATAR": {
        "description": "Indicates whether the client has set an avatar or not",
        "changeable": False,
    },
    "CLIENT_TALK_POWER": {
        "description": "The clients current talk power",
        "changeable": False,
    },
    "CLIENT_TALK_REQUEST": {
        "description": "Indicates whether the client is requesting talk power or not",
        "changeable": False,
    },
    "CLIENT_TALK_REQUEST_MSG": {
        "description": "The clients current talk power request message",
        "changeable": False,
    },
    "CLIENT_IS_TALKER": {
        "description": "Indicates whether the client is able to talk or not",
        "changeable": True,
    },
    "CLIENT_MONTH_BYTES_DOWNLOADED": {
        "description": "Number of bytes downloaded by the client on the current month",
        "changeable": False,
    },
    "CLIENT_MONTH_BYTES_UPLOADED": {
        "description": "Number of bytes uploaded by the client on the current month",
        "changeable": False,
    },
    "CLIENT_TOTAL_BYTES_DOWNLOADED": {
        "description": "Number of bytes downloaded by the client since the server was started",
        "changeable": False,
    },
    "CLIENT_TOTAL_BYTES_UPLOADED": {
        "description": "Number of bytes uploaded by the client since the server was started",
        "changeable": False,
    },
    "CLIENT_IS_PRIORITY_SPEAKER": {
        "description": "Indicates whether the client is a priority speaker or not",
        "changeable": False,
    },
    "CLIENT_UNREAD_MESSAGES": {
        "description": "Number of unread offline messages in this clients inbox",
        "changeable": False,
    },
    "CLIENT_NICKNAME_PHONETIC ": {
        "description": "Phonetic name of the client",
        "changeable": False,
    },
    "CLIENT_DESCRIPTION": {
        "description": "Brief description of the client",
        "changeable": True,
    },
    "CLIENT_NEEDED_SERVERQUERY_VIEW_POWER": {
        "description": "The clients current ServerQuery view power",
        "changeable": False,
    },
    "CONNECTION_FILETRANSFER_BANDWIDTH_SENT": {
        "description": "Current bandwidth used for outgoing  file transfers (Bytes/s)",
        "changeable": False,
    },
    "CONNECTION_FILETRANSFER_BANDWIDTH_RECEIVED": {
        "description": "Current bandwidth used for incoming  file transfers (Bytes/s)",
        "changeable": False,
    },
    "CONNECTION_PACKETS_SENT_TOTAL": {
        "description": "Total amount of packets sent",
        "changeable": False,
    },
    "CONNECTION_PACKETS_RECEIVED_TOTAL": {
        "description": "Total amount of packets received",
        "changeable": False,
    },
    "CONNECTION_BYTES_SENT_TOTAL": {
        "description": "Total amount of bytes sent",
        "changeable": False,
    },
    "CONNECTION_BYTES_RECEIVED_TOTAL": {
        "description": "Total amount of bytes received",
        "changeable": False,
    },
    "CONNECTION_BANDWIDTH_SENT_LAST_SECOND_TOTAL": {
        "description": "Average bandwidth used for outgoing data in the last second (Bytes/s)",
        "changeable": False,
    },
    "CONNECTION_BANDWIDTH_RECEIVED_LAST_SECOND_TOTAL": {
        "description": "Average bandwidth used for incoming data in the last second (Bytes/s)",
        "changeable": False,
    },
    "CONNECTION_BANDWIDTH_SENT_LAST_MINUTE_TOTAL": {
        "description": "Average bandwidth used for outgoing data in the last minute (Bytes/s)",
        "changeable": False,
    },
    "CONNECTION_BANDWIDTH_RECEIVED_LAST_MINUTE_TOTAL": {
        "description": "Average bandwidth used for incoming data in the last minute (Bytes/s)",
        "changeable": False,
    },
    "CONNECTION_CLIENT_IP ": {
        "description": "The IPv4 address of the client",
        "changeable": False,
    },
    "CLIENT_IS_CHANNEL_COMMANDER ": {
        "description": "Indicates whether the client is a channel commander or not",
        "changeable": True,
    },
    "CLIENT_ICON_ID ": {
        "description": "CRC32 checksum of the client icon",
        "changeable": True,
    },
    "CLIENT_COUNTRY ": {
        "description": "The country identifier of the client (i.e. DE)",
        "changeable": False,
    },
}

CHANGEABLE_CLIENT_PROPERTIES = {
    key: value for key, value in CLIENT_PROPERTIES.items() if value["changeable"]
}
