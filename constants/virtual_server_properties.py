"""
Parsed from the TeamSpeak 3 Server Query documentation
"""

VIRTUAL_SERVER_PROPERTIES = {
    "VIRTUALSERVER_NAME": {
        "description": "Name of the virtual server",
        "changeable": True,
    },
    "VIRTUALSERVER_WELCOMEMESSAGE": {
        "description": "Welcome message of the virtual server",
        "changeable": True,
    },
    "VIRTUALSERVER_MAXCLIENTS": {
        "description": "Number of slots available on the virtual server",
        "changeable": True,
    },
    "VIRTUALSERVER_PASSWORD": {
        "description": "Password of the virtual server",
        "changeable": True,
    },
    "VIRTUALSERVER_FLAG_PASSWORD": {
        "description": "Indicates whether the server has a password set or not",
        "changeable": False,
    },
    "VIRTUALSERVER_CLIENTSONLINE": {
        "description": "Number of clients connected to the virtual server",
        "changeable": False,
    },
    "VIRTUALSERVER_QUERYCLIENTSONLINE": {
        "description": "Number of ServerQuery clients connected to the virtual server",
        "changeable": False,
    },
    "VIRTUALSERVER_CHANNELSONLINE": {
        "description": "Number of channels created on the virtual server",
        "changeable": False,
    },
    "VIRTUALSERVER_CREATED": {
        "description": "Creation date and time of the virtual server as UTC timestamp",
        "changeable": False,
    },
    "VIRTUALSERVER_UPTIME": {
        "description": "Uptime in seconds",
        "changeable": False,
    },
    "VIRTUALSERVER_HOSTMESSAGE": {
        "description": "Host message of the virtual server",
        "changeable": True,
    },
    "VIRTUALSERVER_HOSTMESSAGE_MODE": {
        "description": "Host message mode of the virtual server Definitions",
        "changeable": True,
    },
    "VIRTUALSERVER_DEFAULT_SERVER_GROUP": {
        "description": "Default server group ID",
        "changeable": True,
    },
    "VIRTUALSERVER_DEFAULT_CHANNEL_GROUP": {
        "description": "Default channel group ID",
        "changeable": True,
    },
    "VIRTUALSERVER_DEFAULT_CHANNEL_ADMIN_GROUP": {
        "description": "Default channel administrator group ID",
        "changeable": True,
    },
    "VIRTUALSERVER_PLATFORM": {
        "description": "Operating system the server is running on",
        "changeable": False,
    },
    "VIRTUALSERVER_VERSION": {
        "description": "Server version information including build number",
        "changeable": False,
    },
    "VIRTUALSERVER_MAX_DOWNLOAD_TOTAL_BANDWIDTH ": {
        "description": "Max bandwidth for outgoing file transfers on the virtual server (Bytes/s)",
        "changeable": True,
    },
    "VIRTUALSERVER_MAX_UPLOAD_TOTAL_BANDWIDTH ": {
        "description": "Max bandwidth for incoming  file transfers on the virtual server (Bytes/s)",
        "changeable": True,
    },
    "VIRTUALSERVER_HOSTBANNER_URL": {
        "description": "Host banner URL opened on click",
        "changeable": True,
    },
    "VIRTUALSERVER_HOSTBANNER_GFX_URL": {
        "description": "Host banner URL used as image source",
        "changeable": True,
    },
    "VIRTUALSERVER_HOSTBANNER_GFX_INTERVAL": {
        "description": "Interval for reloading the banner on client-side",
        "changeable": True,
    },
    "VIRTUALSERVER_COMPLAIN_AUTOBAN_COUNT": {
        "description": "Number of complaints needed to ban a client automatically",
        "changeable": True,
    },
    "VIRTUALSERVER_COMPLAIN_AUTOBAN_TIME": {
        "description": "Time in seconds used for automatic bans triggered by complaints",
        "changeable": True,
    },
    "VIRTUALSERVER_COMPLAIN_REMOVE_TIME": {
        "description": "Time in seconds before a complaint is deleted automatically",
        "changeable": True,
    },
    "VIRTUALSERVER_MIN_CLIENTS_IN_CHANNEL_BEFORE_FORCED_SILENCE": {
        "description": "Number of clients in the same channel needed to force silence",
        "changeable": True,
    },
    "VIRTUALSERVER_PRIORITY_SPEAKER_DIMM_MODIFICATOR": {
        "description": "Client volume lowered automatically while a priority speaker is talking",
        "changeable": True,
    },
    "VIRTUALSERVER_ANTIFLOOD_POINTS_TICK_REDUCE": {
        "description": "Anti-flood points removed from a client for being good",
        "changeable": True,
    },
    "VIRTUALSERVER_ANTIFLOOD_POINTS_NEEDED_COMMAND_BLOCK": {
        "description": "Anti-flood points needed to block commands being executed by the client",
        "changeable": True,
    },
    "VIRTUALSERVER_ANTIFLOOD_POINTS_NEEDED_PLUGIN_BLOCK": {
        "description": "Anti-flood points needed to block plugin commands from the client; if set to 0, the same as VIRTUALSERVER_ANTIFLOOD_POINTS_NEEDED_COMMAND_BLOCK is used",
        "changeable": True,
    },
    "VIRTUALSERVER_ANTIFLOOD_POINTS_NEEDED_IP_BLOCK": {
        "description": "Anti-flood points needed to block incoming connections from the client",
        "changeable": True,
    },
    "VIRTUALSERVER_HOSTBANNER_MODE": {
        "description": "The display mode for the virtual servers hostbanner Definitions",
        "changeable": True,
    },
    "VIRTUALSERVER_ASK_FOR_PRIVILEGEKEY": {
        "description": "Indicates whether the initial privilege key for the virtual server has been used or not",
        "changeable": False,
    },
    "VIRTUALSERVER_CLIENT_CONNECTIONS": {
        "description": "Total number of clients connected to the virtual server since it was last started",
        "changeable": False,
    },
    "VIRTUALSERVER_QUERY_CLIENT_CONNECTIONS": {
        "description": "Total number of ServerQuery clients connected to the virtual server since it was last started",
        "changeable": False,
    },
    "VIRTUALSERVER_HOSTBUTTON_TOOLTIP": {
        "description": "Text used for the tooltip of the host button on client-side",
        "changeable": True,
    },
    "VIRTUALSERVER_HOSTBUTTON_GFX_URL": {
        "description": "Text used for the tooltip of the host button on client-side",
        "changeable": True,
    },
    "VIRTUALSERVER_HOSTBUTTON_URL": {
        "description": "URL opened on click on the host button",
        "changeable": True,
    },
    "VIRTUALSERVER_DOWNLOAD_QUOTA": {
        "description": "Download quota for the virtual server (MByte)",
        "changeable": True,
    },
    "VIRTUALSERVER_UPLOAD_QUOTA": {
        "description": "Download quota for the virtual server (MByte)",
        "changeable": True,
    },
    "VIRTUALSERVER_MONTH_BYTES_DOWNLOADED": {
        "description": "Number of bytes downloaded from the virtual server on the current month",
        "changeable": False,
    },
    "VIRTUALSERVER_MONTH_BYTES_UPLOADED": {
        "description": "Number of bytes uploaded to the virtual server on the current month",
        "changeable": False,
    },
    "VIRTUALSERVER_TOTAL_BYTES_DOWNLOADED": {
        "description": "Number of bytes downloaded from the virtual server since it was last started",
        "changeable": False,
    },
    "VIRTUALSERVER_TOTAL_BYTES_UPLOADED": {
        "description": "Number of bytes uploaded to the virtual server since it was last started",
        "changeable": False,
    },
    "VIRTUALSERVER_UNIQUE_IDENTIFIER": {
        "description": "Unique ID of the virtual server",
        "changeable": False,
    },
    "VIRTUALSERVER_ID": {
        "description": "Database ID of the virtual server",
        "changeable": False,
    },
    "VIRTUALSERVER_MACHINE_ID": {
        "description": "Machine ID identifying the server instance associated with the virtual server in the database",
        "changeable": True,
    },
    "VIRTUALSERVER_PORT": {
        "description": "UDP port the virtual server is listening on",
        "changeable": True,
    },
    "VIRTUALSERVER_AUTOSTART": {
        "description": "Indicates whether the server starts automatically with the server instance or not",
        "changeable": True,
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
    "VIRTUALSERVER_STATUS": {
        "description": "Status of the virtual server (online | virtual online | offline | booting up | shutting down | …)",
        "changeable": True,
    },
    "VIRTUALSERVER_LOG_CLIENT": {
        "description": "Indicates whether the server logs events related to clients or not",
        "changeable": True,
    },
    "VIRTUALSERVER_LOG_QUERY": {
        "description": "Indicates whether the server logs events related to ServerQuery clients or not",
        "changeable": True,
    },
    "VIRTUALSERVER_LOG_CHANNEL": {
        "description": "Indicates whether the server logs events related to channels or not",
        "changeable": True,
    },
    "VIRTUALSERVER_LOG_PERMISSIONS": {
        "description": "Indicates whether the server logs events related to permissions or not",
        "changeable": True,
    },
    "VIRTUALSERVER_LOG_SERVER": {
        "description": "Indicates whether the server logs events related to server changes or not",
        "changeable": True,
    },
    "VIRTUALSERVER_LOG_FILETRANSFER": {
        "description": "Indicates whether the server logs events related to file transfers or not",
        "changeable": True,
    },
    "VIRTUALSERVER_MIN_CLIENT_VERSION": {
        "description": "Minimal desktop client version required to connect",
        "changeable": True,
    },
    "VIRTUALSERVER_MIN_ANDROID_VERSION": {
        "description": "Minimal Android client version required to connect",
        "changeable": True,
    },
    "VIRTUALSERVER_MIN_IOS_VERSION": {
        "description": "Minimal iOS client version required to connect",
        "changeable": True,
    },
    "VIRTUALSERVER_MIN_WINPHONE_VERSION": {
        "description": "Place holder for the minimal Windows phone client version required to connect. Currently there are no plans to support Windows phone though",
        "changeable": True,
    },
    "VIRTUALSERVER_NEEDED_IDENTITY_SECURITY_LEVEL": {
        "description": "Minimum client identity  security level required to connect to the virtual server",
        "changeable": True,
    },
    "VIRTUALSERVER_NAME_PHONETIC ": {
        "description": "Phonetic name of the virtual server",
        "changeable": True,
    },
    "VIRTUALSERVER_ICON_ID ": {
        "description": "CRC32 checksum of the virtual server icon",
        "changeable": True,
    },
    "VIRTUALSERVER_RESERVED_SLOTS ": {
        "description": "Number of reserved slots available on the virtual server",
        "changeable": True,
    },
    "VIRTUALSERVER_TOTAL_PACKETLOSS_SPEECH ": {
        "description": "The average packet loss for speech data on the virtual server",
        "changeable": False,
    },
    "VIRTUALSERVER_TOTAL_PACKETLOSS_KEEPALIVE ": {
        "description": "The average packet loss for keepalive data on the virtual server",
        "changeable": False,
    },
    "VIRTUALSERVER_TOTAL_PACKETLOSS_CONTROL ": {
        "description": "The average packet loss for control data on the virtual server",
        "changeable": False,
    },
    "VIRTUALSERVER_TOTAL_PACKETLOSS_TOTAL ": {
        "description": "The average packet loss for all data on the virtual server",
        "changeable": False,
    },
    "VIRTUALSERVER_TOTAL_PING ": {
        "description": "The average ping of all clients connected to the virtual server",
        "changeable": False,
    },
    "VIRTUALSERVER_IP ": {
        "description": "The IPv4 address the virtual server is listening on",
        "changeable": False,
    },
    "VIRTUALSERVER_WEBLIST_ENABLED ": {
        "description": "Indicates whether the server appears in the global web server list or not",
        "changeable": True,
    },
    "VIRTUALSERVER_CODEC_ENCRYPTION_MODE ": {
        "description": "The global codec encryption mode of the virtual server",
        "changeable": True,
    },
    "VIRTUALSERVER_FILEBASE": {
        "description": "The directory where the virtual servers filebase is located",
        "changeable": False,
    },
}

CHANGEABLE_VIRTUAL_SERVER_PROPERTIES = {
    key: value for key, value in VIRTUAL_SERVER_PROPERTIES.items() if value["changeable"]
}
