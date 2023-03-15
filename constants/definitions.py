from enum import Enum

"""
Parsed from the TeamSpeak 3 Server Query documentation
"""


class HostMessageMode(Enum):
    HOST_MESSAGE_MODE_NONE = 0
    HOST_MESSAGE_MODE_LOG = 1
    HOST_MESSAGE_MODE_MODAL = 2
    HOST_MESSAGE_MODE_MODALQUIT = 3


class HostBannerMode(Enum):
    HOST_BANNER_MODE_NOADJUST = 0
    HOST_BANNER_MODE_IGNOREASPECT = 1
    HOST_BANNER_MODE_KEEPASPECT = 2


class Codec(Enum):
    CODEC_SPEEX_NARROWBAND = 0
    CODEC_SPEEX_WIDEBAND = 1
    CODEC_SPEEX_ULTRAWIDEBAND = 2
    CODEC_CELT_MONO = 3


class CodecEncryptionMode(Enum):
    CODEC_CRYPT_INDIVIDUAL = 0
    CODEC_CRYPT_DISABLED = 1
    CODEC_CRYPT_ENABLED = 2


class TextMessageTargetMode(Enum):
    TEXT_MESSAGE_TARGET_CLIENT = 1
    TEXT_MESSAGE_TARGET_CHANNEL = 2
    TEXT_MESSAGE_TARGET_SERVER = 3


class LogLevel(Enum):
    LOGLEVEL_ERROR = 1
    LOGLEVEL_WARNING = 2
    LOGLEVEL_DEBUG = 3
    LOGLEVEL_INFO = 4


class ReasonIdentifier(Enum):
    JOIN_SERVER_OR_CHANGE_CHANNEL = 0
    MOVE_CLIENT__OR_CHANNEL = 1
    TIMEOUT = 3
    REASON_KICK_CHANNEL = 4
    REASON_KICK_SERVER = 5
    BAN = 6
    LEAVE_SERVER = 8
    EDIT_CHANNEL_OR_SERVER = 10
    SHUTDOWN_SERVER = 11


class PermissionGroupDatabaseType(Enum):
    PERMGROUP_DB_TYPE_TEMPLATE = 0
    PERMGROUP_DB_TYPE_REGULAR = 1
    PERMGROUP_DB_TYPE_QUERY = 2


class PermissionGroupType(Enum):
    PERMGROUP_TYPE_SERVER_GROUP = 0
    PERMGROUP_TYPE_GLOBALCLIENT = 1
    PERMGROUP_TYPE_CHANNEL = 2
    PERMGROUP_TYPE_CHANNEL_GROUP = 3
    PERMGROUP_TYPE_CHANNEL_CLIENT = 4


class TokenType(Enum):
    TOKEN_SERVER_GROUP = 0
    TOKEN_CHANNEL_GROUP = 1


class ServerGroupType(Enum):
    CHANNEL_GUEST = 10
    SERVER_GUEST = 15
    QUERY_GUEST = 20
    CHANNEL_VOICE = 25
    SERVER_NORMAL = 30
    CHANNEL_OPERATOR = 35
    CHANNEL_ADMIN = 40
    SERVER_ADMIN = 45
    QUERY_ADMIN = 50


class NotifyRegisterType(Enum):
    SERVER = "server"
    CHANNEL = "channel"
    TEXT_SERVER = "textserver"
    TEXT_CHANNEL = "textchannel"
    TEXT_PRIVATE = "textprivate"


class TargetMode(Enum):
    CLIENT = 1
    CHANNEL = 2
    SERVER = 3


class Subsystem(Enum):
    VOICE = "voice"
    QUERY = "query"
    FILE_TRANSFER = "filetransfer"


class EventType(Enum):
    CHANNEL_CREATED = "channelcreated"
    CHANNEL_DELETED = "channeldeleted"
    CHANNEL_DESCRIPTION_CHANGED = "channeldescriptionchanged"
    CHANNEL_EDITED = "channeledited"
    CHANNEL_MOVED = "channelmoved"
    CHANNEL_PASSWORD_CHANGED = "channelpasswordchanged"
    CLIENT_ENTER_VIEW = "cliententerview"
    CLIENT_LEFT_VIEW = "clientleftview"
    CLIENT_MOVED = "clientmoved"
    SERVER_EDITED = "serveredited"
    TOKEN_USED = "tokenused"
