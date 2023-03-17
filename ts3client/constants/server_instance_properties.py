"""
Parsed from the TeamSpeak 3 Server Query documentation
"""

SERVER_INSTANCE_PROPERTIES = {
    "INSTANCE_UPTIME": {
        "description": "Uptime in seconds",
        "changeable": False,
    },
    "HOST_TIMESTAMP_UTC": {
        "description": "Current server date and time as UTC timestamp",
        "changeable": False,
    },
    "VIRTUALSERVERS_RUNNING_TOTAL": {
        "description": "Number of virtual servers running",
        "changeable": False,
    },
    "CONNECTION_FILETRANSFER_BANDWIDTH_SENT": {
        "description": "Current bandwidth used for outgoing file transfers (Bytes/s)",
        "changeable": False,
    },
    "CONNECTION_FILETRANSFER_BANDWIDTH_RECEIVED": {
        "description": "Current bandwidth used for incoming file transfers (Bytes/s)",
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
    "SERVERINSTANCE_DATABASE_VERSION": {
        "description": "Database revision number",
        "changeable": False,
    },
    "SERVERINSTANCE_GUEST_SERVERQUERY_GROUP": {
        "description": "Default ServerQuery group ID",
        "changeable": True,
    },
    "SERVERINSTANCE_TEMPLATE_SERVERADMIN_GROUP": {
        "description": "Default template group ID for administrators on new virtual servers (used to create initial token)",
        "changeable": True,
    },
    "SERVERINSTANCE_FILETRANSFER_PORT": {
        "description": "TCP port used for file transfers",
        "changeable": True,
    },
    "SERVERINSTANCE_MAX_DOWNLOAD_TOTAL_BANDWITDH": {
        "description": "Max bandwidth available for outgoing file transfers (Bytes/s)",
        "changeable": True,
    },
    "SERVERINSTANCE_MAX_UPLOAD_TOTAL_BANDWITDH": {
        "description": "Max bandwidth available for incoming file transfers (Bytes/s)",
        "changeable": True,
    },
    "SERVERINSTANCE_TEMPLATE_SERVERDEFAULT_GROUP": {
        "description": "Default server group ID used in templates",
        "changeable": True,
    },
    "SERVERINSTANCE_TEMPLATE_CHANNELDEFAULT_GROUP ": {
        "description": "Default channel group ID used in templates",
        "changeable": True,
    },
    "SERVERINSTANCE_TEMPLATE_CHANNELADMIN_GROUP": {
        "description": "Default channel administrator group ID used in templates",
        "changeable": True,
    },
    "VIRTUALSERVERS_TOTAL_MAXCLIENTS": {
        "description": "Max number of clients for all virtual servers",
        "changeable": False,
    },
    "VIRTUALSERVERS_TOTAL_CLIENTS_ONLINE": {
        "description": "Number of clients online on all virtual servers",
        "changeable": False,
    },
    "VIRTUALSERVERS_TOTAL_CHANNELS_ONLINE": {
        "description": "Number of channels on all virtual servers",
        "changeable": False,
    },
    "SERVERINSTANCE_SERVERQUERY_FLOOD_COMMANDS": {
        "description": "Max number of commands allowed in seconds",
        "changeable": True,
    },
    "SERVERINSTANCE_SERVERQUERY_FLOOD_TIME": {
        "description": "Timeframe in seconds for commands",
        "changeable": True,
    },
    "SERVERINSTANCE_SERVERQUERY_FLOOD_BAN_TIME": {
        "description": "Time in seconds used for automatic bans triggered by the ServerQuery flood protection",
        "changeable": True,
    },
}

CHANGEABLE_SERVER_INSTANCE_PROPERTIES = [
    key.lower() for key, value in SERVER_INSTANCE_PROPERTIES.items() if value["changeable"]
]
