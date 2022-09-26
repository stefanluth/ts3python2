from re import compile

RESPONSE = compile(rb"error id=(?P<id>\d+) msg=(?P<msg>\S+)\n\r")
TEXT_MSG = compile(
    r"notifytextmessage targetmode=(?P<targetmode>\d) msg=(?P<msg>\S+) target=(?P<target>\d+) invokerid=(?P<invokerid>\d+) invokername=(?P<invokername>\S+) invokeruid=(?P<invokeruid>\S+)\n\r"
)
