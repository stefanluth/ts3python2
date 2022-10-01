from enum import Enum


class HostMessageMode(Enum):
    HostMessageMode_NONE = 0  # don't display anything
    HostMessageMode_LOG = 1  # display message in chatlog
    HostMessageMode_MODAL = 2  # display message in modal dialog
    HostMessageMode_MODALQUIT = 3  # display message in modal dialog & close connection


class HostBannerMode(Enum):
    HostBannerMode_NOADJUST = 0  # do not adjust
    HostBannerMode_IGNOREASPECT = 1  # adjust but ignore aspect ratio (like TeamSpeak 2)
    HostBannerMode_KEEPASPECT = 2  # adjust & keep aspect ratio


class Codec(Enum):
    CODEC_SPEEX_NARROWBAND = 0  # speex narrowband (mono, 16bit, 8kHz)
    CODEC_SPEEX_WIDEBAND = 1  # speex wideband (mono, 16bit, 16kHz)
    CODEC_SPEEX_ULTRAWIDEBAND = 2  # speex ultra-wideband (mono, 16bit, 32kHz)
    CODEC_CELT_MONO = 3  # celt mono (mono, 16bit, 48kHz)


class CodecEncryptionMode(Enum):
    CODEC_CRYPT_INDIVIDUAL = 0  # configure per channel
    CODEC_CRYPT_DISABLED = 1  # globally disabled
    CODEC_CRYPT_ENABLED = 2  # globally enabled


class TextMessageTargetMode(Enum):
    TextMessageTarget_CLIENT = 1  # target is a client
    TextMessageTarget_CHANNEL = 2  # target is a channel
    TextMessageTarget_SERVER = 3  # target is a virtual server


class LogLevel(Enum):
    LogLevel_ERROR = 1  # everything that is really bad
    LogLevel_WARNING = 2  # everything that might be bad
    LogLevel_DEBUG = 3  # output that might help find a problem
    LogLevel_INFO = 4  # informational output


class ReasonIdentifier(Enum):
    REASON_KICK_CHANNEL = 4  # kick client from channel
    REASON_KICK_SERVER = 5  # kick client from server


class PermissionGroupDatabaseType(Enum):
    PermGroupDBTypeTemplate = 0  # template group (used for new virtual servers)
    PermGroupDBTypeRegular = 1  # regular group (used for regular clients)
    PermGroupDBTypeQuery = 2  # global query group (used for ServerQuery clients)


class PermissionGroupType(Enum):
    PermGroupTypeServerGroup = 0  # server group permission
    PermGroupTypeGlobalClient = 1  # client specific permission
    PermGroupTypeChannel = 2  # channel specific permission
    PermGroupTypeChannelGroup = 3  # channel group permission
    PermGroupTypeChannelClient = 4  # channel-client specific permission


class TokenType(Enum):
    TokenServerGroup = 0  # server group token (id1={groupID} id2=0)
    TokenChannelGroup = 1  # channel group token (id1={groupID} id2={channelID})


class ServerGroupType(Enum):
    ChannelGuest = 10
    ServerGuest = 15
    QueryGuest = 20
    ChannelVoice = 25
    ServerNormal = 30
    ChannelOperator = 35
    ChannelAdmin = 40
    ServerAdmin = 45
    QueryAdmin = 50


class NotifyRegisterType(Enum):
    SERVER = "server"
    CHANNEL = "channel"
    TEXTSERVER = "textserver"
    TEXTCHANNEL = "textchannel"
    TEXTPRIVATE = "textprivate"


class TargetMode(Enum):
    CLIENT = 1
    CHANNEL = 2
    SERVER = 3


class Subsystem(Enum):
    VOICE = "voice"
    QUERY = "query"
    FILETRANSFER = "filetransfer"


class EventType(Enum):
    ChannelCreated = "channelcreated"
    ChannelDeleted = "channeldeleted"
    ChannelDescriptionChanged = "channeldescriptionchanged"
    ChannelEdited = "channeledited"
    ChannelMoved = "channelmoved"
    ChannelPasswordChanged = "channelpasswordchanged"
    ClientEnterView = "cliententerview"
    ClientLeftView = "clientleftview"
    ClientMoved = "clientmoved"
    ServerEdited = "serveredited"
