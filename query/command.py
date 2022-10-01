from dataclasses import dataclass, field
import logging
from telnetlib import Telnet
from typing import Literal, Optional

from query.definitions import *
from query.properties import *
from query.response import QueryResponse
from utils import parsers


logger = logging.getLogger("commands")
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
file_handler = logging.FileHandler("ts3python2.log")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


@dataclass
class QueryCmd:
    command: str
    args: Optional[tuple] = field(default_factory=tuple)
    kwargs: Optional[dict] = field(default_factory=dict)
    encoded: bytes = field(init=False)

    def __post_init__(self):
        args = [
            parsers.boolean_to_option(arg) if isinstance(arg, bool) else arg
            for arg in self.args
        ]

        kwargs = {k: v for k, v in self.kwargs.items() if v is not None}

        cmd = " ".join(
            [
                self.command,
                *args,
                *parsers.dict_to_query_parameters(kwargs),
            ]
        )

        self.encoded = f"{cmd.strip()}\n".encode()


class CommandsWrapper:
    def __init__(self, query: Telnet) -> None:
        self.query = query

    def help(self) -> QueryResponse:
        """
        Provides information about ServerQuery commands. Used without parameters,
        help lists and briefly describes every command.
        """

        return self.query.send(QueryCmd("help"))

    def quit(self) -> QueryResponse:
        logger.debug("Quitting")

        return self.query.send(QueryCmd("quit"))

    def login(
        self, client_login_name: str, client_login_password: str
    ) -> QueryResponse:
        """
        Authenticates with the TeamSpeak 3 Server instance using given ServerQuery
        login credentials.
        """
        logger.debug("Logging in")

        return self.query.send(
            QueryCmd(
                "login",
                kwargs={
                    "client_login_name": client_login_name,
                    "client_login_password": client_login_password,
                },
            )
        )

    def logout(self) -> QueryResponse:
        """
        Deselects the active virtual server and logs out from the server instance.
        """
        logger.debug("Logging out")

        return self.query.send(QueryCmd("logout"))

    def version(self) -> QueryResponse:
        """
        Displays the servers version information including platform and build number.
        """

        return self.query.send(QueryCmd("version"))

    def hostinfo(self) -> QueryResponse:
        """
        Displays detailed connection information about the server instance including
        uptime, number of virtual servers online, traffic information, etc. For detailed
        information, see Server Instance Properties.
        """

        return self.query.send(QueryCmd("hostinfo"))

    def instanceinfo(self) -> QueryResponse:
        """
        Displays the server instance configuration including database revision number,
        the file transfer port, default group IDs, etc. For detailed information, see
        Server Instance Properties.
        """

        return self.query.send(QueryCmd("instanceinfo"))

    def instanceedit(self, *args, **kwargs) -> QueryResponse:
        """
        Changes the server instance configuration using given properties. For detailed
        information, see Server Instance Properties.
        """

        _validate_server_instance_kwargs(kwargs)

        return self.query.send(QueryCmd("instanceedit", args=args, kwargs=kwargs))

    def bindinglist(self, subsystem: Optional[Subsystem] = None) -> QueryResponse:
        """
        Displays a list of IP addresses used by the server instance on multi-homed
        machines. If no subsystem is specified, "voice" is used by default.
        """

        return self.query.send(
            QueryCmd(
                "bindinglist", kwargs={"subsystem": subsystem.value or Subsystem.VOICE}
            )
        )

    def use(
        self,
        sid: Optional[int] = None,
        port: Optional[int] = None,
        virtual: bool = False,
    ) -> QueryResponse:
        """
        Selects the virtual server specified with sid or port to allow further
        interaction. The ServerQuery client will appear on the virtual server and acts
        like a real TeamSpeak 3 Client, except it's unable to send or receive voice
        data. If your database contains multiple virtual servers using the same UDP
        port, use will select a random virtual server using the specified port.
        """
        logger.debug("Selecting server")

        return self.query.send(
            QueryCmd("use", args=(virtual,), kwargs={"sid": sid, "port": port})
        )

    def serverlist(
        self,
        uid: bool = False,
        short: bool = False,
        all: bool = False,
        onlyoffline: bool = False,
    ) -> QueryResponse:
        """
        Displays a list of virtual servers including their ID, status, number of clients
        online, etc. If you're using the -all option, the server will list all virtual
        servers stored in the database. This can be useful when multiple server
        instances with different machine IDs are using the same database. The machine ID
        is used to identify the server instance a virtual server is associated with.
        The status of a virtual server can be either online, offline, booting up,
        shutting down or virtual online. While most of them are self-explanatory,
        virtual online is a bit more complicated. Whenever you select a virtual server
        which is currently stopped with the -virtual parameter, it will be started in
        virtual mode which means you are able to change its configuration, create
        channels or change permissions, but no regular TeamSpeak 3 Client can connect.
        As soon as the last ServerQuery client deselects the virtual server, its status
        will be changed back to offline.
        """

        return self.query.send(
            QueryCmd("serverlist", args=(uid, short, all, onlyoffline))
        )

    def serveridgetbyport(self, virtualserver_port: int) -> QueryResponse:
        """
        Displays the database ID of the virtual server running on the UDP port specified
        by virtualserver_port.
        """

        return self.query.send(
            QueryCmd(
                "serveridgetbyport", kwargs={"virtualserver_port": virtualserver_port}
            )
        )

    def serverdelete(self, sid: int) -> QueryResponse:
        """
        Deletes the virtual server specified with sid. Please note that only virtual
        servers in stopped state can be deleted.
        """

        return self.query.send(QueryCmd("serverdelete", kwargs={"sid": sid}))

    def servercreate(self, virtualserver_name: str, **kwargs) -> QueryResponse:
        """
        Creates a new virtual server using the given properties and displays its ID,
        port and initial administrator privilege key. If virtualserver_port is not
        specified, the server will test for the first unused UDP port. The first virtual
        server will be running on UDP port 9987 by default. Subsequently started virtual
        servers will be running on increasing UDP port numbers. For detailed
        information, see Virtual Server Properties.
        """

        _validate_virtual_server_kwargs(kwargs)

        return self.query.send(
            QueryCmd(
                "servercreate",
                kwargs={"virtualserver_name": virtualserver_name, **kwargs},
            )
        )

    def serverstart(self, sid: int) -> QueryResponse:
        """
        Starts the virtual server specified with sid. Depending on your permissions,
        you're able to start either your own virtual server only or all virtual servers
        in the server instance.
        """

        return self.query.send(QueryCmd("serverstart", kwargs={"sid": sid}))

    def serverstop(self, sid: int) -> QueryResponse:
        """
        Stops the virtual server specified with sid. Depending on your permissions,
        you're able to stop either your own virtual server only or all virtual servers
        in the server instance.
        """

        return self.query.send(QueryCmd("serverstop", kwargs={"sid": sid}))

    def serverprocessstop(self) -> QueryResponse:
        """
        Stops the entire TeamSpeak 3 Server instance by shutting down the process.
        """

        return self.query.send(QueryCmd("serverprocessstop"))

    def serverinfo(self) -> QueryResponse:
        """
        Displays detailed configuration information about the selected virtual server
        including unique ID, number of clients online, configuration, etc. For detailed
        information, see Virtual Server Properties.
        """

        return self.query.send(QueryCmd("serverinfo"))

    def serverrequestconnectioninfo(self) -> QueryResponse:
        """
        Displays detailed connection information about the selected virtual server
        including uptime, traffic information, etc.
        """

        return self.query.send(QueryCmd("serverrequestconnectioninfo"))

    def servertemppasswordadd(
        self, pw: str, desc: str, duration: int, tcid: int, tcpw: str
    ) -> QueryResponse:
        """
        Sets a new temporary server password specified with pw. The temporary password
        will be valid for the number of seconds specified with duration. The client
        connecting with this password will automatically join the channel specified with
        tcid. If tcid is set to 0, the client will join the default channel.
        """

        return self.query.send(
            QueryCmd(
                "servertemppasswordadd",
                kwargs={
                    "pw": pw,
                    "desc": desc,
                    "duration": duration,
                    "tcid": tcid,
                    "tcpw": tcpw,
                },
            )
        )

    def servertemppassworddel(self, pw: str) -> QueryResponse:
        """
        Deletes the temporary server password specified with pw.
        """

        return self.query.send(QueryCmd("servertemppassworddel", kwargs={"pw": pw}))

    def servertemppasswordlist(self) -> QueryResponse:
        """

        Returns a list of active temporary server passwords. The output contains the
        clear-text password, the nickname and unique identifier of the creating client.
        """

        return self.query.send(QueryCmd("servertemppasswordlist"))

    def serveredit(self, **kwargs) -> QueryResponse:
        """
        Changes the selected virtual servers configuration using given properties.
        Note that this command accepts multiple properties which means that you're able
        to change all settings of the selected virtual server at once. For detailed
        information, see Virtual Server Properties.
        """

        _validate_virtual_server_kwargs(kwargs)

        return self.query.send(QueryCmd("serveredit", kwargs=kwargs))

    def servergrouplist(self) -> QueryResponse:
        """
        Displays a list of server groups available. Depending on your permissions,
        the output may also contain global ServerQuery groups and template groups.
        """

        return self.query.send(QueryCmd("servergrouplist"))

    def servergroupadd(
        self, name: str, type: Optional[PermissionGroupDatabaseTypes] = None
    ) -> QueryResponse:
        """
        Creates a new server group using the name specified with name and displays its
        ID. The optional type parameter can be used to create ServerQuery groups and
        template groups. For detailed information, see Definitions.
        """

        return self.query.send(
            QueryCmd(
                "servergroupadd",
                kwargs={"name": name, "type": type.value if type else None},
            )
        )

    def servergroupdel(self, sgid: int, force: bool = False) -> QueryResponse:
        """
        Deletes the server group specified with sgid. If force is set to 1, the server
        group will be deleted even if there are clients within.
        """

        return self.query.send(
            QueryCmd("servergroupdel", kwargs={"sgid": sgid, "force": force})
        )

    def servergroupcopy(
        self, ssgid: int, tsgid: int, name: str, type: PermissionGroupDatabaseTypes
    ) -> QueryResponse:
        """
        Creates a copy of the server group specified with ssgid. If tsgid is set to 0,
        the server will create a new group. To overwrite an existing group, simply set
        tsgid to the ID of a designated target group. If a target group is set, the
        name parameter will be ignored. The type parameter can be used to create
        ServerQuery groups and template groups. For detailed information, see
        Definitions.
        """

        return self.query.send(
            QueryCmd(
                "servergroupcopy",
                kwargs={
                    "ssgid": ssgid,
                    "tsgid": tsgid,
                    "name": name,
                    "type": type.value,
                },
            )
        )

    def servergrouprename(self, sgid: int, name: str) -> QueryResponse:
        """
        Changes the name of the server group specified with sgid.
        """

        return self.query.send(
            QueryCmd("servergrouprename", kwargs={"sgid": sgid, "name": name})
        )

    def servergrouppermlist(self, sgid: int, permsid: bool = False) -> QueryResponse:
        """
        Displays a list of permissions assigned to the server group specified with sgid.
        If the -permsid option is specified, the output will contain the permission
        names instead of the internal IDs.
        """

        return self.query.send(
            QueryCmd("servergrouppermlist", args=(permsid,), kwargs={"sgid": sgid})
        )

    def servergroupaddperm(
        self,
        sgid: int,
        permvalue: int,
        permid: Optional[int] = None,
        permsid: Optional[str] = None,
        permnegated: bool = False,
        permskip: bool = False,
    ) -> QueryResponse:
        """
        Adds a set of specified permissions to the server group specified with sgid.
        Multiple permissions can be added by providing the four parameters of each
        permission. A permission can be specified by permid or permsid.
        """

        return self.query.send(
            QueryCmd(
                "servergroupaddperm",
                kwargs={
                    "sgid": sgid,
                    "permvalue": permvalue,
                    "permid": permid,
                    "permsid": permsid,
                    "permnegated": permnegated,
                    "permskip": permskip,
                },
            )
        )

    def servergroupdelperm(
        self, sgid: int, permid: Optional[int] = None, permsid: Optional[str] = None
    ) -> QueryResponse:
        """
        Removes a set of specified permissions from the server group specified with
        sgid. Multiple permissions can be removed at once. A permission can be specified
        by permid or permsid.
        """

        return self.query.send(
            QueryCmd(
                "servergroupdelperm",
                kwargs={"sgid": sgid, "permid": permid, "permsid": permsid},
            )
        )

    def servergroupaddclient(self, sgid: int, cldbid: int) -> QueryResponse:
        """
        Adds a client to the server group specified with sgid. Please note that a client
        cannot be added to default groups or template groups.
        """

        return self.query.send(
            QueryCmd("servergroupaddclient", kwargs={"sgid": sgid, "cldbid": cldbid})
        )

    def servergroupdelclient(self, sgid: int, cldbid: int) -> QueryResponse:
        """
        Removes a client specified with cldbid from the server group specified with
        sgid.
        """

        return self.query.send(
            QueryCmd("servergroupdelclient", kwargs={"sgid": sgid, "cldbid": cldbid})
        )

    def servergroupclientlist(self, sgid: int, names: bool = False) -> QueryResponse:
        """
        Displays the IDs of all clients currently residing in the server group specified
        with sgid. If you're using the optional -names option, the output will also
        contain the last known nickname and the unique identifier of the clients.
        """

        return self.query.send(
            QueryCmd("servergroupclientlist", args=(names,), kwargs={"sgid": sgid})
        )

    def servergroupsbyclientid(self, cldbid: int) -> QueryResponse:
        """
        Displays all server groups the client specified with cldbid is currently
        residing in.
        """

        return self.query.send(
            QueryCmd("servergroupsbyclientid", kwargs={"cldbid": cldbid})
        )

    def servergroupautoaddperm(
        self,
        sgtype: ServerGroupType,
        permvalue: int,
        permid: Optional[int] = None,
        permsid: Optional[str] = None,
        permnegated: bool = False,
        permskip: bool = False,
    ) -> QueryResponse:
        """
        Adds a set of specified permissions to *ALL* regular server groups on all
        virtual servers. The target groups will be identified by the value of their
        i_group_auto_update_type permission specified with sgtype. Multiple permissions
        can be added at once. A permission can be specified by permid or permsid.
        The known values for sgtype are: 10: Channel Guest 15: Server Guest 20: Query
        Guest 25: Channel Voice 30: Server Normal 35: Channel Operator 40: Channel Admin
        45: Server Admin 50: Query Admin
        """

        return self.query.send(
            QueryCmd(
                "servergroupautoaddperm",
                kwargs={
                    "sgtype": sgtype.value,
                    "permid": permid,
                    "permsid": permsid,
                    "permvalue": permvalue,
                    "permnegated": permnegated,
                    "permskip": permskip,
                },
            )
        )

    def servergroupautodelperm(
        self,
        sgtype: ServerGroupType,
        permid: Optional[int] = None,
        permsid: Optional[str] = None,
    ) -> QueryResponse:
        """
        Removes a set of specified permissions from *ALL* regular server groups on all
        virtual servers. The target groups will be identified by the value of their
        i_group_auto_update_type permission specified with sgtype. Multiple permissions
        can be removed at once. A permission can be specified by permid or permsid. The
        known values for sgtype are: 10: Channel Guest 15: Server Guest 20: Query Guest
        25: Channel Voice 30: Server Normal 35: Channel Operator 40: Channel Admin 45:
        Server Admin 50: Query Admin
        """

        return self.query.send(
            QueryCmd(
                "servergroupautodelperm",
                kwargs={
                    "sgtype": sgtype.value,
                    "permid": permid,
                    "permsid": permsid,
                },
            )
        )

    def serversnapshotcreate(self) -> QueryResponse:
        """
        Displays a snapshot of the selected virtual server containing all settings,
        groups and known client identities. The data from a server snapshot can be used
        to restore a virtual servers configuration, channels and permissions using the
        serversnapshotdeploy command.
        """

        return self.query.send(QueryCmd("serversnapshotcreate"))

    def serversnapshotdeploy(
        self, hash: str, mapping: bool = False, **kwargs
    ) -> QueryResponse:
        """
        Restores the selected virtual servers configuration using the data from a
        previously created server snapshot. Please note that the TeamSpeak 3 Server does
        NOT check for necessary permissions while deploying a snapshot so the command
        could be abused to gain additional privileges.
        """

        _validate_virtual_server_kwargs(kwargs)

        return self.query.send(
            QueryCmd(
                "serversnapshotdeploy", args=(mapping,), kwargs={"hash": hash, **kwargs}
            )
        )

    def servernotifyregister(
        self, event: NotifyRegisterTypes, id: Optional[int] = None
    ) -> QueryResponse:
        """
        Registers for a specified category of events on a virtual server to receive
        notification messages. Depending on the notifications you've registered for,
        the server will send you a message on every event in the view of your
        ServerQuery client (e.g. clients joining your channel, incoming text messages,
        server configuration changes, etc). The event source is declared by the event
        parameter while id can be used to limit the notifications to a specific channel.
        """

        return self.query.send(
            QueryCmd("servernotifyregister", kwargs={"event": event.value, "id": id})
        )

    def servernotifyunregister(self) -> QueryResponse:
        """
        Unregisters all events previously registered with servernotifyregister so you
        will no longer receive notification messages.
        """

        return self.query.send(QueryCmd("servernotifyunregister"))

    def sendtextmessage(
        self, targetmode: TargetMode, target: int, msg: str
    ) -> QueryResponse:
        """
        Sends a text message to a specified target. If targetmode is set to 1, a message
        is sent to the client with the ID specified by target. If targetmode is set to 2
        or 3, the target parameter will be ignored and a message is sent to the current
        channel or server respectively.
        """

        return self.query.send(
            QueryCmd(
                "sendtextmessage",
                kwargs={"targetmode": targetmode.value, "target": target, "msg": msg},
            )
        )

    def logview(
        self,
        lines: Optional[int] = None,
        reverse: bool = False,
        instance: bool = False,
        begin_pos: Optional[int] = None,
    ) -> QueryResponse:
        """
        Displays a specified number of entries from the servers log. If instance is set
        to 1, the server will return lines from the master logfile (ts3server_0.log)
        instead of the selected virtual server logfile.
        """

        return self.query.send(
            QueryCmd(
                "logview",
                kwargs={
                    "lines": lines,
                    "reverse": reverse,
                    "instance": instance,
                    "begin_pos": begin_pos,
                },
            )
        )

    def logadd(self, loglevel: LogLevel, logmsg: str) -> QueryResponse:
        """
        Writes a custom entry into the servers log. Depending on your permissions,
        you'll be able to add entries into the server instance log and/or your virtual
        servers log. The loglevel parameter specifies the type of the entry. For
        detailed information, see Definitions.
        """

        return self.query.send(
            QueryCmd("logadd", kwargs={"loglevel": loglevel.value, "logmsg": logmsg})
        )

    def gm(self, msg: str) -> QueryResponse:
        """
        Sends a text message to all clients on all virtual servers in the TeamSpeak 3
        Server instance.
        """

        return self.query.send(QueryCmd("gm", kwargs={"msg": msg}))

    def channellist(
        self,
        topic: bool = False,
        flags: bool = False,
        voice: bool = False,
        limits: bool = False,
        icon: bool = False,
        secondsempty: bool = False,
    ) -> QueryResponse:
        """
        Displays a list of channels created on a virtual server including their ID,
        order, name, etc. The output can be modified using several command options.
        """

        return self.query.send(
            QueryCmd(
                "channellist", args=(topic, flags, voice, limits, icon, secondsempty)
            )
        )

    def channelinfo(self, cid: int) -> QueryResponse:
        """
        Displays detailed configuration information about a channel including ID, topic,
        description, etc. For detailed information, see Channel Properties.
        """

        return self.query.send(QueryCmd("channelinfo", kwargs={"cid": cid}))

    def channelfind(self, pattern: str) -> QueryResponse:
        """
        Displays a list of channels matching a given name pattern.
        """

        return self.query.send(QueryCmd("channelfind", kwargs={"pattern": pattern}))

    def channelmove(
        self, cid: int, cpid: int, order: Optional[int] = None
    ) -> QueryResponse:
        """
        Moves a channel to a new parent channel with the ID cpid. If order is specified,
        the channel will be sorted right under the channel with the specified ID. If
        order is set to 0, the channel will be sorted right below the new parent.
        """

        return self.query.send(
            QueryCmd("channelmove", kwargs={"cid": cid, "cpid": cpid, "order": order})
        )

    def channelcreate(self, channel_name: str, **kwargs) -> QueryResponse:
        """
        Creates a new channel using the given properties and displays its ID. Note that
        this command accepts multiple properties which means that you're able to
        specifiy all settings of the new channel at once. For detailed information,
        see Channel Properties.
        """

        _validate_channel_kwargs(kwargs)

        return self.query.send(
            QueryCmd("channelcreate", kwargs={"channel_name": channel_name, **kwargs})
        )

    def channeldelete(self, cid: int, force: bool = False) -> QueryResponse:
        """
        Deletes an existing channel by ID. If force is set to 1, the channel will be
        deleted even if there are clients within. The clients will be kicked to the
        default channel with an appropriate reason message.
        """

        return self.query.send(
            QueryCmd("channeldelete", kwargs={"cid": cid, "force": force})
        )

    def channeledit(self, cid: int, **kwargs) -> QueryResponse:
        """
        Changes a channels configuration using given properties. Note that this command
        accepts multiple properties which means that you're able to change all settings
        of the channel specified with cid at once. For detailed information, see Channel
        Properties.
        """

        _validate_channel_kwargs(kwargs)

        return self.query.send(QueryCmd("channeledit", kwargs={"cid": cid, **kwargs}))

    def channelgrouplist(self) -> QueryResponse:
        """
        Displays a list of channel groups available on the selected virtual server.
        """

        return self.query.send(QueryCmd("channelgrouplist"))

    def channelgroupadd(
        self, name: str, type: Optional[PermissionGroupDatabaseTypes] = None
    ) -> QueryResponse:
        """
        Creates a new channel group using a given name and displays its ID. The optional
        type parameter can be used to create template groups. For detailed information,
        see Definitions.
        """

        return self.query.send(
            QueryCmd(
                "channelgroupadd",
                kwargs={"name": name, "type": type.value if type else None},
            )
        )

    def channelgroupdel(self, cgid: int, force: bool = False) -> QueryResponse:
        """
        Deletes a channel group by ID. If force is set to 1, the channel group will be
        deleted even if there are clients within.
        """

        return self.query.send(
            QueryCmd("channelgroupdel", kwargs={"cgid": cgid, "force": force})
        )

    def channelgroupcopy(
        self, scgid: int, tsgid: int, name: str, type: PermissionGroupDatabaseTypes
    ) -> QueryResponse:
        """
        Creates a copy of the channel group specified with scgid. If tcgid is set to 0,
        the server will create a new group. To overwrite an existing group, simply set
        tcgid to the ID of a designated target group. If a target group is set, the name
        parameter will be ignored. The type parameter can be used to create template
        groups. For detailed information, see Definitions.
        """

        return self.query.send(
            QueryCmd(
                "channelgroupcopy",
                kwargs={
                    "scgid": scgid,
                    "tsgid": tsgid,
                    "name": name,
                    "type": type.value,
                },
            )
        )

    def channelgrouprename(self, cgid: int, name: str) -> QueryResponse:
        """
        Changes the name of a specified channel group.
        """

        return self.query.send(
            QueryCmd("channelgrouprename", kwargs={"cgid": cgid, "name": name})
        )

    def channelgroupaddperm(
        self,
        cgid: int,
        permvalue: int,
        permid: Optional[int] = None,
        permsid: Optional[str] = None,
    ) -> QueryResponse:
        """
        Adds a set of specified permissions to a channel group. Multiple permissions can
        be added by providing the two parameters of each permission. A permission can be
        specified by permid or permsid.
        """

        return self.query.send(
            QueryCmd(
                "channelgroupaddperm",
                kwargs={
                    "cgid": cgid,
                    "permid": permid,
                    "permsid": permsid,
                    "permvalue": permvalue,
                },
            )
        )

    def channelgrouppermlist(self, cgid: int, permsid: bool = False) -> QueryResponse:
        """
        Displays a list of permissions assigned to the channel group specified with
        cgid. If the -permsid option is specified, the output will contain the
        permission names instead of the internal IDs.
        """

        return self.query.send(
            QueryCmd("channelgrouppermlist", args=(permsid,), kwargs={"cgid": cgid})
        )

    def channelgroupdelperm(
        self, cgid: int, permid: Optional[int] = None, permsid: Optional[str] = None
    ) -> QueryResponse:
        """
        Removes a set of specified permissions from the channel group. Multiple
        permissions can be removed at once. A permission can be specified by permid or
        permsid.
        """

        return self.query.send(
            QueryCmd(
                "channelgroupdelperm",
                kwargs={"cgid": cgid, "permid": permid, "permsid": permsid},
            )
        )

    def channelgroupclientlist(
        self,
        cid: Optional[int] = None,
        cldbid: Optional[int] = None,
        cgid: Optional[int] = None,
    ) -> QueryResponse:
        """
        Displays all the client and/or channel IDs currently assigned to channel groups.
        All three parameters are optional so you're free to choose the most suitable
        combination for your requirements.
        """

        return self.query.send(
            QueryCmd(
                "channelgroupclientlist",
                kwargs={"cid": cid, "cldbid": cldbid, "cgid": cgid},
            )
        )

    def setclientchannelgroup(self, cgid: int, cid: int, cldbid: int) -> QueryResponse:
        """
        Sets the channel group of a client to the ID specified with cgid.
        """

        return self.query.send(
            QueryCmd(
                "setclientchannelgroup",
                kwargs={"cgid": cgid, "cid": cid, "cldbid": cldbid},
            )
        )

    def tokenadd(
        self,
        tokentype: Literal[0, 1],
        tokenid1: int,
        tokenid2: int,
        tokendescription: Optional[str] = None,
        tokencustomset: Optional[str] = None,
    ) -> QueryResponse:
        """
        Alias for privilegekeyadd.
        """

        return self.query.send(
            QueryCmd(
                "tokenadd",
                kwargs={
                    "tokentype": tokentype,
                    "tokenid1": tokenid1,
                    "tokenid2": tokenid2,
                    "tokendescription": tokendescription,
                    "tokencustomset": tokencustomset,
                },
            )
        )

    def tokendelete(self, token: str) -> QueryResponse:
        """
        Alias for privilegekeydelete
        """

        return self.query.send(QueryCmd("tokendelete", kwargs={"token": token}))

    def tokenlist(self) -> QueryResponse:
        """
        Alias for privilegekeylist.
        """

        return self.query.send(QueryCmd("tokenlist"))

    def tokenuse(self, token: str) -> QueryResponse:
        """
        Alias for privilegekeyuse.
        """

        return self.query.send(QueryCmd("tokenuse", kwargs={"token": token}))

    def channelpermlist(self, cid: int, permsid: bool = False) -> QueryResponse:
        """
        Displays a list of permissions defined for a channel.
        """

        return self.query.send(
            QueryCmd("channelpermlist", args=(permsid,), kwargs={"cid": cid})
        )

    def channeladdperm(
        self,
        cid: int,
        permvalue: int,
        permid: Optional[int] = None,
        permsid: Optional[str] = None,
    ) -> QueryResponse:
        """
        Adds a set of specified permissions to a channel. Multiple permissions can be
        added by providing the two parameters of each permission. A permission can be
        specified by permid or permsid.
        """

        return self.query.send(
            QueryCmd(
                "channeladdperm",
                kwargs={
                    "cid": cid,
                    "permid": permid,
                    "permsid": permsid,
                    "permvalue": permvalue,
                },
            )
        )

    def channeldelperm(
        self, cid: int, permid: Optional[int] = None, permsid: Optional[str] = None
    ) -> QueryResponse:
        """
        Removes a set of specified permissions from a channel. Multiple permissions can
        be removed at once. A permission can be specified by permid or permsid.
        """

        return self.query.send(
            QueryCmd(
                "channeldelperm",
                kwargs={"cid": cid, "permid": permid, "permsid": permsid},
            )
        )

    def clientlist(
        self,
        uid: bool = False,
        away: bool = False,
        voice: bool = False,
        times: bool = False,
        groups: bool = False,
        info: bool = False,
        country: bool = False,
        ip: bool = False,
        badge: bool = False,
    ) -> QueryResponse:
        """
        Displays a list of clients online on a virtual server including their ID,
        nickname, status flags, etc. The output can be modified using several command
        options. Please note that the output will only contain clients which are
        currently in channels you're able to subscribe to.
        """

        return self.query.send(
            QueryCmd(
                "clientlist",
                args=(uid, away, voice, times, groups, info, country, ip, badge),
            )
        )

    def clientinfo(self, clid: int) -> QueryResponse:
        """
        Displays detailed configuration information about a client including unique ID,
        nickname, client version, etc.
        """

        return self.query.send(QueryCmd("clientinfo", kwargs={"clid": clid}))

    def clientfind(self, pattern: str) -> QueryResponse:
        """
        Displays a list of clients matching a given name pattern.
        """

        return self.query.send(QueryCmd("clientfind", kwargs={"pattern": pattern}))

    def clientedit(self, clid: int, **kwargs) -> QueryResponse:
        """
        Changes a clients settings using given properties. For detailed information, see
        Client Properties.
        """

        _validate_client_kwargs(kwargs)

        return self.query.send(QueryCmd("clientedit", kwargs={"clid": clid, **kwargs}))

    def clientdblist(
        self,
        start: Optional[int] = None,
        duration: Optional[int] = None,
        count: bool = False,
    ) -> QueryResponse:
        """
        Displays a list of client identities known by the server including their
        database ID, last nickname, etc.
        """

        return self.query.send(
            QueryCmd(
                "clientdblist",
                args=(count,),
                kwargs={"start": start, "duration": duration},
            )
        )

    def clientdbinfo(self, cldbid: int) -> QueryResponse:
        """
        Displays detailed database information about a client including unique ID,
        creation date, etc.
        """

        return self.query.send(QueryCmd("clientdbinfo", kwargs={"cldbid": cldbid}))

    def clientdbfind(self, pattern: str, uid: bool = False) -> QueryResponse:
        """
        Displays a list of client database IDs matching a given pattern. You can either
        search for a clients last known nickname or his unique identity by using the
        -uid option. The pattern parameter can include regular characters and SQL
        wildcard characters (e.g. %).
        """

        return self.query.send(
            QueryCmd("clientdbfind", args=(uid,), kwargs={"pattern": pattern})
        )

    def clientdbedit(self, cldbid: int, **kwargs) -> QueryResponse:
        """
        Changes a clients settings using given properties. For detailed information,
        see Client Properties.
        """

        _validate_client_kwargs(kwargs)

        return self.query.send(
            QueryCmd("clientdbedit", kwargs={"cldbid": cldbid, **kwargs})
        )

    def clientdbdelete(self, cldbid: int) -> QueryResponse:
        """
        Deletes a clients properties from the database.
        """

        return self.query.send(QueryCmd("clientdbdelete", kwargs={"cldbid": cldbid}))

    def clientgetids(self, cluid: str) -> QueryResponse:
        """
        Displays all client IDs matching the unique identifier specified by cluid.
        """

        return self.query.send(QueryCmd("clientgetids", kwargs={"cluid": cluid}))

    def clientgetdbidfromuid(self, cluid: str) -> QueryResponse:
        """
        Displays the database ID matching the unique identifier specified by cluid.
        """

        return self.query.send(
            QueryCmd("clientgetdbidfromuid", kwargs={"cluid": cluid})
        )

    def clientgetnamefromuid(self, cluid: str) -> QueryResponse:
        """
        Displays the database ID and nickname matching the unique identifier specified
        by cluid.
        """

        return self.query.send(
            QueryCmd("clientgetnamefromuid", kwargs={"cluid": cluid})
        )

    def clientgetuidfromclid(self, clid: int) -> QueryResponse:
        """
        Displays the unique identifier matching the clientID specified by clid.
        """

        return self.query.send(QueryCmd("clientgetuidfromclid", kwargs={"clid": clid}))

    def clientgetnamefromdbid(self, cldbid: int) -> QueryResponse:
        """
        Displays the unique identifier and nickname matching the database ID specified
        by cldbid.
        """

        return self.query.send(
            QueryCmd("clientgetnamefromdbid", kwargs={"cldbid": cldbid})
        )

    def clientsetserverquerylogin(self, client_login_name: str) -> QueryResponse:
        """
        Updates your own ServerQuery login credentials using a specified username. The
        password will be auto-generated.
        """

        return self.query.send(
            QueryCmd(
                "clientsetserverquerylogin",
                kwargs={"client_login_name": client_login_name},
            )
        )

    def clientupdate(self, **kwargs) -> QueryResponse:
        """
        Change your ServerQuery clients settings using given properties. For detailed
        information, see Client Properties.
        """

        _validate_client_kwargs(kwargs)

        return self.query.send(QueryCmd("clientupdate", kwargs=kwargs))

    def clientmove(
        self, clid: int, cid: int, cpw: Optional[str] = None
    ) -> QueryResponse:
        """
        Moves one or more clients specified with clid to the channel with ID cid. If the
        target channel has a password, it needs to be specified with cpw. If the channel
        has no password, the parameter can be omitted.
        """

        return self.query.send(
            QueryCmd("clientmove", kwargs={"clid": clid, "cid": cid, "cpw": cpw})
        )

    def clientkick(
        self, clid: int, reasonid: ReasonIdentifier, reasonmsg: Optional[str] = None
    ) -> QueryResponse:
        """
        Kicks one or more clients specified with clid from their currently joined
        channel or from the server, depending on reasonid. The reasonmsg parameter
        specifies a text message sent to the kicked clients. This parameter is optional
        and may only have a maximum of 40 characters. For detailed information, see
        Definitions.
        """

        return self.query.send(
            QueryCmd(
                "clientkick",
                kwargs={
                    "clid": clid,
                    "reasonid": reasonid.value,
                    "reasonmsg": reasonmsg,
                },
            )
        )

    def clientpoke(self, clid: int, msg: str) -> QueryResponse:
        """
        Sends a poke message to the client specified with clid.
        """

        return self.query.send(
            QueryCmd("clientpoke", kwargs={"clid": clid, "msg": msg})
        )

    def clientpermlist(self, cldbid: int, permsid: bool = False) -> QueryResponse:
        """
        Displays a list of permissions defined for a client.
        """

        return self.query.send(
            QueryCmd("clientpermlist", args=(permsid,), kwargs={"cldbid": cldbid})
        )

    def clientaddperm(
        self,
        cldbid: int,
        permvalue: int,
        permid: Optional[int] = None,
        permsid: Optional[str] = None,
        permskip: bool = False,
    ) -> QueryResponse:
        """
        Adds a set of specified permissions to a client. Multiple permissions can be
        added by providing the three parameters of each permission. A permission can be
        specified by permid or permsid.
        """

        return self.query.send(
            QueryCmd(
                "clientaddperm",
                kwargs={
                    "cldbid": cldbid,
                    "permid": permid,
                    "permsid": permsid,
                    "permvalue": permvalue,
                    "permskip": permskip,
                },
            )
        )

    def clientdelperm(
        self, cldbid: int, permsid: Optional[str], permid: Optional[int] = None
    ) -> QueryResponse:
        """
        Removes a set of specified permissions from a client. Multiple permissions can
        be removed at once. A permission can be specified by permid or permsid.
        """

        return self.query.send(
            QueryCmd(
                "clientdelperm",
                kwargs={"cldbid": cldbid, "permid": permid, "permsid": permsid},
            )
        )

    def channelclientpermlist(
        self, cid: int, cldbid: int, permsid: bool = False
    ) -> QueryResponse:
        """
        Displays a list of permissions defined for a client in a specific channel.
        """

        return self.query.send(
            QueryCmd(
                "channelclientpermlist",
                args=(permsid,),
                kwargs={"cid": cid, "cldbid": cldbid},
            )
        )

    def channelclientaddperm(
        self,
        cid: int,
        cldbid: int,
        permvalue: int,
        permid: Optional[int] = None,
        permsid: Optional[str] = None,
    ) -> QueryResponse:
        """
        Adds a set of specified permissions to a client in a specific channel. Multiple
        permissions can be added by providing the three parameters of each permission.
        A permission can be specified by permid or permsid.
        """

        return self.query.send(
            QueryCmd(
                "channelclientaddperm",
                kwargs={
                    "cid": cid,
                    "cldbid": cldbid,
                    "permid": permid,
                    "permsid": permsid,
                    "permvalue": permvalue,
                },
            )
        )

    def channelclientdelperm(
        self,
        cid: int,
        cldbid: int,
        permsid: Optional[str],
        permid: Optional[int] = None,
    ) -> QueryResponse:
        """
        Removes a set of specified permissions from a client in a specific channel.
        Multiple permissions can be removed at once. A permission can be specified by
        permid or permsid.
        """

        return self.query.send(
            QueryCmd(
                "channelclientdelperm",
                kwargs={
                    "cid": cid,
                    "cldbid": cldbid,
                    "permid": permid,
                    "permsid": permsid,
                },
            )
        )

    def permissionlist(self) -> QueryResponse:
        """
        Displays a list of permissions available on the server instance including ID,
        name and description.
        """

        return self.query.send(QueryCmd("permissionlist"))

    def permidgetbyname(self, permsid: str) -> QueryResponse:
        """
        Displays the database ID of one or more permissions specified by permsid.
        """

        return self.query.send(QueryCmd("permidgetbyname", kwargs={"permsid": permsid}))

    def permoverview(
        self,
        cid: int,
        cldbid: int,
        permsid: Optional[str],
        permid: Optional[int] = None,
    ) -> QueryResponse:
        """
        Displays detailed information about all assignments of the permission specified
        with permid. The output is similar to permoverview which includes the type and
        the ID of the client, channel or group associated with the permission. A
        permission can be specified by permid or permsid.
        """

        return self.query.send(
            QueryCmd(
                "permoverview",
                kwargs={
                    "cid": cid,
                    "cldbid": cldbid,
                    "permid": permid,
                    "permsid": permsid,
                },
            )
        )

    def permget(
        self, permid: Optional[int] = None, permsid: Optional[str] = None
    ) -> QueryResponse:
        """
        Displays detailed information about all assignments of the permission specified
        with permid. The output is similar to permoverview which includes the type and
        the ID of the client, channel or group associated with the permission. A
        permission can be specified by permid or permsid.
        """

        return self.query.send(
            QueryCmd("permget", kwargs={"permid": permid, "permsid": permsid})
        )

    def permfind(
        self, permid: Optional[int] = None, permsid: Optional[str] = None
    ) -> QueryResponse:
        """
        Displays detailed information about all assignments of the permission specified
        with permid. The output is similar to permoverview which includes the type and
        the ID of the client, channel or group associated with the permission. A
        permission can be specified by permid or permsid.
        """

        return self.query.send(
            QueryCmd("permfind", kwargs={"permid": permid, "permsid": permsid})
        )

    def permreset(self) -> QueryResponse:
        """
        Restores the default permission settings on the selected virtual server and
        creates a new initial administrator token. Please note that in case of an error
        during the permreset call - e.g. when the database has been modified or
        corrupted - the virtual server will be deleted from the database.
        """

        return self.query.send(QueryCmd("permreset"))

    def privilegekeylist(self) -> QueryResponse:
        """
        Displays a list of privilege keys available including their type and group IDs.
        Tokens can be used to gain access to specified server or channel groups. A
        privilege key is similar to a client with administrator privileges that adds
        you to a certain permission group, but without the necessity of a such a client
        with administrator privileges to actually exist. It is a long (random looking)
        string that can be used as a ticket into a specific server group.
        """

        return self.query.send(QueryCmd("privilegekeylist"))

    def privilegekeyadd(
        self,
        tokentype: Literal[0, 1],
        tokenid1: int,
        tokenid2: int,
        tokendescription: Optional[str] = None,
        tokencustomset: Optional[str] = None,
    ) -> QueryResponse:
        """
        Create a new token. If tokentype is set to 0, the ID specified with tokenid1
        will be a server group ID. Otherwise, tokenid1 is used as a channel group ID
        and you need to provide a valid channel ID using tokenid2. The tokencustomset
        parameter allows you to specify a set of custom client properties. This feature
        can be used when generating tokens to combine a website account database with a
        TeamSpeak user. The syntax of the value needs to be escaped using the
        ServerQuery escape patterns and has to follow the general syntax of:
        ident=ident1 value=value1|ident=ident2 value=value2|ident=ident3 value=value3
        """

        return self.query.send(
            QueryCmd(
                "privilegekeyadd",
                kwargs={
                    "tokentype": tokentype,
                    "tokenid1": tokenid1,
                    "tokenid2": tokenid2,
                    "tokendescription": tokendescription,
                    "tokencustomset": tokencustomset,
                },
            )
        )

    def privilegekeydelete(self, token: str) -> QueryResponse:
        """
        Deletes an existing token matching the token key specified with token.
        """

        return self.query.send(QueryCmd("privilegekeydelete", kwargs={"token": token}))

    def privilegekeyuse(self, token: str) -> QueryResponse:
        """
        Use a token key gain access to a server or channel group. Please note that the
        server will automatically delete the token after it has been used.
        """

        return self.query.send(QueryCmd("privilegekeyuse", kwargs={"token": token}))

    def messagelist(self) -> QueryResponse:
        """
        Displays a list of offline messages you've received. The output contains the
        senders unique identifier, the messages subject, etc.
        """

        return self.query.send(QueryCmd("messagelist"))

    def messageadd(self) -> QueryResponse:
        """
        Sends an offline message to the client specified by cluid.
        """

        return self.query.send(QueryCmd("messageadd"))

    def messagedel(self, msgid: int) -> QueryResponse:
        """
        Deletes an existing offline message with ID msgid from your inbox.
        """

        return self.query.send(QueryCmd("messagedel", kwargs={"msgid": msgid}))

    def messageget(self, msgid: int) -> QueryResponse:
        """
        Displays an existing offline message with ID msgid from your inbox. Please note
        that this does not automatically set the flag_read property of the message.
        """

        return self.query.send(QueryCmd("messageget", kwargs={"msgid": msgid}))

    def messageupdateflag(self, msgid: int, flag: bool) -> QueryResponse:
        """
        Updates the flag_read property of the offline message specified with msgid. If
        flag is set to 1, the message will be marked as read.
        """

        return self.query.send(
            QueryCmd("messageupdateflag", kwargs={"msgid": msgid, "flag": flag})
        )

    def complainlist(self, tcldbid: Optional[int]) -> QueryResponse:
        """
        Displays a list of complaints on the selected virtual server. If tcldbid is
        specified, only complaints about the targeted client will be shown.
        """

        return self.query.send(QueryCmd("complainlist", kwargs={"tcldbid": tcldbid}))

    def complainadd(self, tcldbid: int, message: str) -> QueryResponse:
        """
        Submits a complaint about a connected client with database ID tcldbid to the
        server.
        """

        return self.query.send(
            QueryCmd("complainadd", kwargs={"tcldbid": tcldbid, "message": message})
        )

    def complaindelall(self, tcldbid: int) -> QueryResponse:
        """
        Deletes all complaints about the client with database ID tcldbid from the
        server.
        """

        return self.query.send(QueryCmd("complaindelall", kwargs={"tcldbid": tcldbid}))

    def complaindel(self, tcldbid: int, fcldbid: int) -> QueryResponse:
        """
        Deletes the complaint about the client with ID tcldbid submitted by the client
        with ID fcldbid from the server.
        """

        return self.query.send(
            QueryCmd("complaindel", kwargs={"tcldbid": tcldbid, "fcldbid": fcldbid})
        )

    def banclient(
        self, clid: int, time: Optional[int] = None, banreason: Optional[str] = None
    ) -> QueryResponse:
        """
        Bans the client specified with ID clid from the server. Please note that this
        will create two separate ban rules for the targeted clients IP address and his
        unique identifier.
        """

        return self.query.send(
            QueryCmd(
                "banclient", kwargs={"clid": clid, "time": time, "banreason": banreason}
            )
        )

    def banlist(self) -> QueryResponse:
        """
        Displays a list of active bans on the selected virtual server.
        """

        return self.query.send(QueryCmd("banlist"))

    def banadd(
        self,
        ip: Optional[str] = None,
        name: Optional[str] = None,
        uid: Optional[str] = None,
        time: Optional[int] = None,
        banreason: Optional[str] = None,
    ) -> QueryResponse:
        """
        Adds a new ban rule on the selected virtual server. All parameters are optional
        but at least one of the following must be set: ip, name, or uid.
        """

        return self.query.send(
            QueryCmd(
                "banadd",
                kwargs={
                    "ip": ip,
                    "name": name,
                    "uid": uid,
                    "time": time,
                    "banreason": banreason,
                },
            )
        )

    def bandel(self, banid: int) -> QueryResponse:
        """
        Deletes the ban rule with ID banid from the server.
        """

        return self.query.send(QueryCmd("bandel", kwargs={"banid": banid}))

    def bandelall(self) -> QueryResponse:
        """
        Deletes all active ban rules from the server.
        """

        return self.query.send(QueryCmd("bandelall"))

    def ftinitupload(
        self,
        clientftfid: int,
        name: str,
        cid: int,
        cpw: str,
        size: int,
        overwrite: Optional[bool],
        resume: Optional[bool],
        proto: Optional[Literal[0, 1]],
    ) -> QueryResponse:
        """
        Initializes a file transfer upload. clientftfid is an arbitrary ID to identify
        the file transfer on client-side. On success, the server generates a new ftkey
        which is required to start uploading the file through TeamSpeak 3's file
        transfer interface. Since version 3.0.13 there is an optional proto parameter.
        The client can request a protocol version with it. Currently only 0 and 1 are
        supported which only differ in the way they handle some timings. The server will
        reply which protocol version it will support. The server will reply with an ip
        parameter if it determines the filetransfer subsystem is not reachable by the ip
        that is currently being used for the query connection.
        """

        return self.query.send(
            QueryCmd(
                "ftinitupload",
                kwargs={
                    "clientftfid": clientftfid,
                    "name": name,
                    "cid": cid,
                    "cpw": cpw,
                    "size": size,
                    "overwrite": overwrite,
                    "resume": resume,
                    "proto": proto,
                },
            )
        )

    def ftinitdownload(
        self,
        clientftfid: int,
        name: str,
        cid: int,
        cpw: str,
        seekpos: int,
        proto: Optional[Literal[0, 1]],
    ) -> QueryResponse:
        """
        Initializes a file transfer download. clientftfid is an arbitrary ID to identify
        the file transfer on client-side. On success, the server generates a new ftkey
        which is required to start downloading the file through TeamSpeak 3's file
        transfer interface. Since version 3.0.13 there is an optional proto parameter.
        The client can request a protocol version with it. Currently only 0 and 1 are
        supported which only differ in the way they handle some timings. The server will
        reply which protocol version it will support. The server will reply with an ip
        parameter if it determines the filetransfer subsystem is not reachable by the ip
        that is currently being used for the query connection.
        """

        return self.query.send(
            QueryCmd(
                "ftinitdownload",
                kwargs={
                    "clientftfid": clientftfid,
                    "name": name,
                    "cid": cid,
                    "cpw": cpw,
                    "seekpos": seekpos,
                    "proto": proto,
                },
            )
        )

    def ftlist(self) -> QueryResponse:
        """
        Displays a list of running file transfers on the selected virtual server. The
        output contains the path to which a file is uploaded to, the current transfer
        rate in bytes per second, etc.
        """

        return self.query.send(QueryCmd("ftlist"))

    def ftgetfilelist(self, cid: int, cpw: str, path: str) -> QueryResponse:
        """
        Displays a list of files and directories stored in the specified channels file
        repository.
        """

        return self.query.send(
            QueryCmd("ftgetfilelist", kwargs={"cid": cid, "cpw": cpw, "path": path})
        )

    def ftgetfileinfo(self, cid: int, cpw: str, name: str) -> QueryResponse:
        """
        Displays detailed information about one or more specified files stored in a
        channels file repository.
        """

        return self.query.send(
            QueryCmd("ftgetfileinfo", kwargs={"cid": cid, "cpw": cpw, "name": name})
        )

    def ftstop(self, serverftfid: int, delete: Optional[bool]) -> QueryResponse:
        """
        Stops the running file transfer with server-side ID serverftfid.
        """

        return self.query.send(
            QueryCmd("ftstop", kwargs={"serverftfid": serverftfid, "delete": delete})
        )

    def ftdeletefile(self, cid: int, cpw: str, name: str) -> QueryResponse:
        """
        Deletes one or more files stored in a channels file repository.
        """

        return self.query.send(
            QueryCmd("ftdeletefile", kwargs={"cid": cid, "cpw": cpw, "name": name})
        )

    def ftcreatedir(self, cid: int, cpw: str, dirname: str) -> QueryResponse:
        """
        Creates new directory in a channels file repository.
        """

        return self.query.send(
            QueryCmd("ftcreatedir", kwargs={"cid": cid, "cpw": cpw, "dirname": dirname})
        )

    def ftrenamefile(
        self,
        cid: int,
        cpw: str,
        oldname: str,
        newname: str,
        tcid: Optional[int] = None,
        tcpw: Optional[str] = None,
    ) -> QueryResponse:
        """
        Renames a file in a channels file repository. If the two parameters tcid and
        tcpw are specified, the file will be moved into another channels file
        repository.
        """

        return self.query.send(
            QueryCmd(
                "ftrenamefile",
                kwargs={
                    "cid": cid,
                    "cpw": cpw,
                    "tcid": tcid,
                    "tcpw": tcpw,
                    "oldname": oldname,
                    "newname": newname,
                },
            )
        )

    def customsearch(self, ident: str, value: str) -> QueryResponse:
        """
        Searches for custom client properties specified by ident and value. The value
        parameter can include regular characters and SQL wildcard characters (e.g. %).
        """

        return self.query.send(
            QueryCmd("customsearch", kwargs={"ident": ident, "value": value})
        )

    def custominfo(self, cldbid: int) -> QueryResponse:
        """
        Displays a list of custom properties for the client specified with cldbid.
        """

        return self.query.send(QueryCmd("custominfo", kwargs={"cldbid": cldbid}))

    def whoami(self) -> QueryResponse:
        """
        Displays information about your current ServerQuery connection including your
        loginname, etc.
        """

        return self.query.send(QueryCmd("whoami"))


def _validate_kwargs(args: dict) -> None:
    if not all([isinstance(arg, (str, int, float)) for arg in args.values()]):
        raise ValueError("All argument values must be strings, integers or floats.")


def _validate_server_instance_kwargs(args: dict) -> None:
    """
    Validates the given arguments and returns a dictionary with the valid arguments
    """
    _validate_kwargs(args)

    for key in args.keys():
        if str(key).upper() not in ChangeableServerInstanceProperties.keys():
            raise ValueError(
                f"Invalid argument: {key}\n\
                \rValid arguments: {ChangeableServerInstanceProperties.keys()}"
            )


def _validate_channel_kwargs(args: dict) -> None:
    """
    Validates the given arguments and returns a dictionary with the valid arguments
    """
    _validate_kwargs(args)

    for key in args.keys():
        if str(key).upper() not in ChangeableChannelProperties.keys():
            raise ValueError(
                f"Invalid argument: {key}\n\
                \rValid arguments: {ChangeableChannelProperties.keys()}"
            )


def _validate_client_kwargs(args: dict) -> None:
    """
    Validates the given arguments and returns a dictionary with the valid arguments
    """
    _validate_kwargs(args)

    for key in args.keys():
        if str(key).upper() not in ChangeableClientProperties.keys():
            raise ValueError(
                f"Invalid argument: {key}\n\
                \rValid arguments: {ChangeableClientProperties.keys()}"
            )


def _validate_virtual_server_kwargs(args: dict) -> None:
    """
    Validates the given arguments and returns a dictionary with the valid arguments
    """
    _validate_kwargs(args)

    for key in args.keys():
        if str(key).upper() not in ChangeableVirtualServerProperties.keys():
            raise ValueError(
                f"Invalid argument: {key}\n\
                \rValid arguments: {ChangeableVirtualServerProperties.keys()}"
            )
