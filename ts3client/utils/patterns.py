from re import compile

RESPONSE_END = compile(r"(\n\r)?error id=(?P<id>\d+) msg=(?P<msg>\S+) ?(extra_msg=(?P<extramsg>\S+))?\n\r")
RESPONSE_END_BYTES = compile(rb"(\n\r)?error id=(?P<id>\d+) msg=(?P<msg>\S+) ?(extra_msg=(?P<extramsg>\S+))?\n\r")
MESSAGE = compile(
    r"notifytextmessage targetmode=(?P<targetmode>\d) msg=(?P<msg>\S+) target=(?P<target>\d+) invokerid=(?P<invokerid>\d+) invokername=(?P<invokername>\S+) invokeruid=(?P<invokeruid>\S+)\n\r"
)
EVENT = compile(
    r"notify(?P<event>(cliententerview|clientleftview|clientmoved|serveredited|channeldescriptionchanged|channeledited|channelcreated|channeldeleted|channelmoved|channelpasswordchanged)) .+\n\r"
)
