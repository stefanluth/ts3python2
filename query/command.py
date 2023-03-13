from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Literal, Optional

from query.definitions import *
from query.properties import *
from utils import parsers

if TYPE_CHECKING:
    from query.response import QueryResponse
    from query.ts3query import TS3Query


@dataclass
class QueryCommand:
    command: str
    args: Optional[tuple[tuple[str, bool]]] = field(default_factory=tuple)
    kwargs: Optional[dict] = field(default_factory=dict)
    encoded: bytes = field(init=False)

    def __post_init__(self):
        args = [parsers.boolean_to_option(option, value) for option, value in self.args]

        kwargs = {k: v for k, v in self.kwargs.items() if v is not None}

        cmd = " ".join(
            [
                self.command,
                *args,
                *parsers.dict_to_query_kwargs(kwargs),
            ]
        )

        self.encoded = f"{cmd.strip()}\n".encode()


class CommandsWrapper:
    """
    Provides a wrapper for all commands that can be sent to a TeamSpeak 3 Server
    instance using the ServerQuery interface. For more information, see the
    TeamSpeak 3 Server ServerQuery documentation.

    :param query: A Telnet object that is connected to a TeamSpeak 3 Server instance.
    """

    def __init__(self, query: TS3Query) -> None:
        self.query = query

    def help(self) -> QueryResponse:
        """
        Provides information about ServerQuery commands. Used without parameters,
        help lists and briefly describes every command.
        """

        return self.query.send(QueryCommand("help"))

    def quit(self) -> QueryResponse:
        return self.query.send(QueryCommand("quit"))

    def login(
        self, client_login_name: str, client_login_password: str
    ) -> QueryResponse:
        """
        Authenticates with the TeamSpeak 3 Server instance using given ServerQuery
        login credentials.
        """

        return self.query.send(
            QueryCommand(
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

        return self.query.send(QueryCommand("logout"))

    def version(self) -> QueryResponse:
        """
        Displays the servers version information including platform and build number.
        """

        return self.query.send(QueryCommand("version"))

    def hostinfo(self) -> QueryResponse:
        """
        Displays detailed connection information about the server instance including
        uptime, number of virtual servers online, traffic information, etc. For detailed
        information, see Server Instance Properties.
        """

        return self.query.send(QueryCommand("hostinfo"))

    def instanceinfo(self) -> QueryResponse:
        """
        Displays the server instance configuration including database revision number,
        the file transfer port, default group IDs, etc. For detailed information, see
        Server Instance Properties.
        """

        return self.query.send(QueryCommand("instanceinfo"))

    def instanceedit(self, **kwargs) -> QueryResponse:
        """
        Changes the server instance configuration using given properties. For detailed
        information, see Server Instance Properties.
        """

        _validate_server_instance_kwargs(kwargs)

        return self.query.send(QueryCommand("instanceedit", kwargs=kwargs))

    def bindinglist(self, subsystem: Optional[Subsystem] = None) -> QueryResponse:
        """
        Displays a list of IP addresses used by the server instance on multi-homed
        machines. If no subsystem is specified, "voice" is used by default.
        """

        return self.query.send(
            QueryCommand(
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

        return self.query.send(
            QueryCommand(
                "use", args=(("virtual", virtual),), kwargs={"sid": sid, "port": port}
            )
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
            QueryCommand(
                "serverlist",
                args=(
                    ("uid", uid),
                    ("short", short),
                    ("all", all),
                    ("onlyoffline", onlyoffline),
                ),
            )
        )

    def serveridgetbyport(self, virtualserver_port: int) -> QueryResponse:
        """
        Displays the database ID of the virtual server running on the UDP port specified
        by virtualserver_port.
        """

        return self.query.send(
            QueryCommand(
                "serveridgetbyport", kwargs={"virtualserver_port": virtualserver_port}
            )
        )

    def serverdelete(self, sid: int) -> QueryResponse:
        """
        Deletes the virtual server specified with sid. Please note that only virtual
        servers in stopped state can be deleted.
        """

        return self.query.send(QueryCommand("serverdelete", kwargs={"sid": sid}))

    def servercreate(self, **kwargs) -> QueryResponse:
        """
        Creates a new virtual server using the given properties and displays its ID,
        port and initial administrator privilege key. If virtualserver_port is not
        specified, the server will test for the first unused UDP port. The first virtual
        server will be running on UDP port 9987 by default. Subsequently started virtual
        servers will be running on increasing UDP port numbers. For detailed
        information, see Virtual Server Properties.
        """

        _validate_virtual_server_kwargs(kwargs)

        return self.query.send(QueryCommand("servercreate", kwargs={**kwargs}))

    def serverstart(self, sid: int) -> QueryResponse:
        """
        Starts the virtual server specified with sid. Depending on your permissions,
        you're able to start either your own virtual server only or all virtual servers
        in the server instance.
        """

        return self.query.send(QueryCommand("serverstart", kwargs={"sid": sid}))

    def serverstop(self, sid: int) -> QueryResponse:
        """
        Stops the virtual server specified with sid. Depending on your permissions,
        you're able to stop either your own virtual server only or all virtual servers
        in the server instance.
        """

        return self.query.send(QueryCommand("serverstop", kwargs={"sid": sid}))

    def serverprocessstop(self) -> QueryResponse:
        """
        Stops the entire TeamSpeak 3 Server instance by shutting down the process.
        """

        return self.query.send(QueryCommand("serverprocessstop"))

    def serverinfo(self) -> QueryResponse:
        """
        Displays detailed configuration information about the selected virtual server
        including unique ID, number of clients online, configuration, etc. For detailed
        information, see Virtual Server Properties.
        """

        return self.query.send(QueryCommand("serverinfo"))

    def serverrequestconnectioninfo(self) -> QueryResponse:
        """
        Displays detailed connection information about the selected virtual server
        including uptime, traffic information, etc.
        """

        return self.query.send(QueryCommand("serverrequestconnectioninfo"))

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
            QueryCommand(
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

        return self.query.send(QueryCommand("servertemppassworddel", kwargs={"pw": pw}))

    def servertemppasswordlist(self) -> QueryResponse:
        """

        Returns a list of active temporary server passwords. The output contains the
        clear-text password, the nickname and unique identifier of the creating client.
        """

        return self.query.send(QueryCommand("servertemppasswordlist"))

    def serveredit(self, **kwargs) -> QueryResponse:
        """
        Changes the selected virtual servers configuration using given properties.
        Note that this command accepts multiple properties which means that you're able
        to change all settings of the selected virtual server at once. For detailed
        information, see Virtual Server Properties.
        """

        _validate_virtual_server_kwargs(kwargs)

        return self.query.send(QueryCommand("serveredit", kwargs=kwargs))

    def servergrouplist(self) -> QueryResponse:
        """
        Displays a list of server groups available. Depending on your permissions,
        the output may also contain global ServerQuery groups and template groups.
        """

        return self.query.send(QueryCommand("servergrouplist"))

    def servergroupadd(
        self, name: str, type: Optional[PermissionGroupDatabaseType] = None
    ) -> QueryResponse:
        """
        Creates a new server group using the name specified with name and displays its
        ID. The optional type parameter can be used to create ServerQuery groups and
        template groups. For detailed information, see Definitions.
        """

        return self.query.send(
            QueryCommand(
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
            QueryCommand("servergroupdel", kwargs={"sgid": sgid, "force": force})
        )

    def servergroupcopy(
        self, ssgid: int, tsgid: int, name: str, type: PermissionGroupDatabaseType
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
            QueryCommand(
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
            QueryCommand("servergrouprename", kwargs={"sgid": sgid, "name": name})
        )

    def servergrouppermlist(self, sgid: int, permsid: bool = False) -> QueryResponse:
        """
        Displays a list of permissions assigned to the server group specified with sgid.
        If the -permsid option is specified, the output will contain the permission
        names instead of the internal IDs.
        """

        return self.query.send(
            QueryCommand(
                "servergrouppermlist",
                args=(("permsid", permsid),),
                kwargs={"sgid": sgid},
            )
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
            QueryCommand(
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
            QueryCommand(
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
            QueryCommand(
                "servergroupaddclient", kwargs={"sgid": sgid, "cldbid": cldbid}
            )
        )

    def servergroupdelclient(self, sgid: int, cldbid: int) -> QueryResponse:
        """
        Removes a client specified with cldbid from the server group specified with
        sgid.
        """

        return self.query.send(
            QueryCommand(
                "servergroupdelclient", kwargs={"sgid": sgid, "cldbid": cldbid}
            )
        )

    def servergroupclientlist(self, sgid: int, names: bool = False) -> QueryResponse:
        """
        Displays the IDs of all clients currently residing in the server group specified
        with sgid. If you're using the optional -names option, the output will also
        contain the last known nickname and the unique identifier of the clients.
        """

        return self.query.send(
            QueryCommand(
                "servergroupclientlist", args=(("names", names),), kwargs={"sgid": sgid}
            )
        )

    def servergroupsbyclientid(self, cldbid: int) -> QueryResponse:
        """
        Displays all server groups the client specified with cldbid is currently
        residing in.
        """

        return self.query.send(
            QueryCommand("servergroupsbyclientid", kwargs={"cldbid": cldbid})
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
            QueryCommand(
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
            QueryCommand(
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

        return self.query.send(QueryCommand("serversnapshotcreate"))

    def serversnapshotdeploy(
        self, hash: str, mapping: bool = False, **kwargs
    ) -> QueryResponse:
        """
        Restores the selected virtual servers configuration using the data from a
        previously created server snapshot. Please note that the TeamSpeak 3 Server does
        NOT check for necessary permissions while deploying a snapshot so the command
        could be abused to gain additional privileges.
        """

        return self.query.send(
            QueryCommand(
                "serversnapshotdeploy",
                args=(("mapping", mapping),),
                kwargs={"hash": hash, **kwargs},
            )
        )

    def servernotifyregister(
        self, event: NotifyRegisterType, id: Optional[int] = None
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
            QueryCommand(
                "servernotifyregister", kwargs={"event": event.value, "id": id}
            )
        )

    def servernotifyunregister(self) -> QueryResponse:
        """
        Unregisters all events previously registered with servernotifyregister so you
        will no longer receive notification messages.
        """

        return self.query.send(QueryCommand("servernotifyunregister"))

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
            QueryCommand(
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
            QueryCommand(
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
            QueryCommand(
                "logadd", kwargs={"loglevel": loglevel.value, "logmsg": logmsg}
            )
        )

    def gm(self, msg: str) -> QueryResponse:
        """
        Sends a text message to all clients on all virtual servers in the TeamSpeak 3
        Server instance.
        """

        return self.query.send(QueryCommand("gm", kwargs={"msg": msg}))

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
            QueryCommand(
                "channellist",
                args=(
                    ("topic", topic),
                    ("flags", flags),
                    ("voice", voice),
                    ("limits", limits),
                    ("icon", icon),
                    ("secondsempty", secondsempty),
                ),
            )
        )

    def channelinfo(self, cid: int) -> QueryResponse:
        """
        Displays detailed configuration information about a channel including ID, topic,
        description, etc. For detailed information, see Channel Properties.
        """

        return self.query.send(QueryCommand("channelinfo", kwargs={"cid": cid}))

    def channelfind(self, pattern: str) -> QueryResponse:
        """
        Displays a list of channels matching a given name pattern.
        """

        return self.query.send(QueryCommand("channelfind", kwargs={"pattern": pattern}))

    def channelmove(
        self, cid: int, cpid: int, order: Optional[int] = None
    ) -> QueryResponse:
        """
        Moves a channel to a new parent channel with the ID cpid. If order is specified,
        the channel will be sorted right under the channel with the specified ID. If
        order is set to 0, the channel will be sorted right below the new parent.
        """

        return self.query.send(
            QueryCommand(
                "channelmove", kwargs={"cid": cid, "cpid": cpid, "order": order}
            )
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
            QueryCommand(
                "channelcreate", kwargs={"channel_name": channel_name, **kwargs}
            )
        )

    def channeldelete(self, cid: int, force: bool = False) -> QueryResponse:
        """
        Deletes an existing channel by ID. If force is set to 1, the channel will be
        deleted even if there are clients within. The clients will be kicked to the
        default channel with an appropriate reason message.
        """

        return self.query.send(
            QueryCommand("channeldelete", kwargs={"cid": cid, "force": force})
        )

    def channeledit(self, cid: int, **kwargs) -> QueryResponse:
        """
        Changes a channels configuration using given properties. Note that this command
        accepts multiple properties which means that you're able to change all settings
        of the channel specified with cid at once. For detailed information, see Channel
        Properties.
        """

        _validate_channel_kwargs(kwargs)

        return self.query.send(
            QueryCommand("channeledit", kwargs={"cid": cid, **kwargs})
        )

    def channelgrouplist(self) -> QueryResponse:
        """
        Displays a list of channel groups available on the selected virtual server.
        """

        return self.query.send(QueryCommand("channelgrouplist"))

    def channelgroupadd(
        self, name: str, type: Optional[PermissionGroupDatabaseType] = None
    ) -> QueryResponse:
        """
        Creates a new channel group using a given name and displays its ID. The optional
        type parameter can be used to create template groups. For detailed information,
        see Definitions.
        """

        return self.query.send(
            QueryCommand(
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
            QueryCommand("channelgroupdel", kwargs={"cgid": cgid, "force": force})
        )

    def channelgroupcopy(
        self, scgid: int, tsgid: int, name: str, type: PermissionGroupDatabaseType
    ) -> QueryResponse:
        """
        Creates a copy of the channel group specified with scgid. If tcgid is set to 0,
        the server will create a new group. To overwrite an existing group, simply set
        tcgid to the ID of a designated target group. If a target group is set, the name
        parameter will be ignored. The type parameter can be used to create template
        groups. For detailed information, see Definitions.
        """

        return self.query.send(
            QueryCommand(
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
            QueryCommand("channelgrouprename", kwargs={"cgid": cgid, "name": name})
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
            QueryCommand(
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
            QueryCommand(
                "channelgrouppermlist",
                args=(("permsid", permsid),),
                kwargs={"cgid": cgid},
            )
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
            QueryCommand(
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
            QueryCommand(
                "channelgroupclientlist",
                kwargs={"cid": cid, "cldbid": cldbid, "cgid": cgid},
            )
        )

    def setclientchannelgroup(self, cgid: int, cid: int, cldbid: int) -> QueryResponse:
        """
        Sets the channel group of a client to the ID specified with cgid.
        """

        return self.query.send(
            QueryCommand(
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
            QueryCommand(
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

        return self.query.send(QueryCommand("tokendelete", kwargs={"token": token}))

    def tokenlist(self) -> QueryResponse:
        """
        Alias for privilegekeylist.
        """

        return self.query.send(QueryCommand("tokenlist"))

    def tokenuse(self, token: str) -> QueryResponse:
        """
        Alias for privilegekeyuse.
        """

        return self.query.send(QueryCommand("tokenuse", kwargs={"token": token}))

    def channelpermlist(self, cid: int, permsid: bool = False) -> QueryResponse:
        """
        Displays a list of permissions defined for a channel.
        """

        return self.query.send(
            QueryCommand(
                "channelpermlist", args=(("permsid", permsid),), kwargs={"cid": cid}
            )
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
            QueryCommand(
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
            QueryCommand(
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
            QueryCommand(
                "clientlist",
                args=(
                    ("uid", uid),
                    ("away", away),
                    ("voice", voice),
                    ("times", times),
                    ("groups", groups),
                    ("info", info),
                    ("country", country),
                    ("ip", ip),
                    ("badge", badge),
                ),
            )
        )

    def clientinfo(self, clid: int) -> QueryResponse:
        """
        Displays detailed configuration information about a client including unique ID,
        nickname, client version, etc.
        """

        return self.query.send(QueryCommand("clientinfo", kwargs={"clid": clid}))

    def clientfind(self, pattern: str) -> QueryResponse:
        """
        Displays a list of clients matching a given name pattern.
        """

        return self.query.send(QueryCommand("clientfind", kwargs={"pattern": pattern}))

    def clientedit(self, clid: int, **kwargs) -> QueryResponse:
        """
        Changes a clients settings using given properties. For detailed information, see
        Client Properties.
        """

        _validate_client_kwargs(kwargs)

        return self.query.send(
            QueryCommand("clientedit", kwargs={"clid": clid, **kwargs})
        )

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
            QueryCommand(
                "clientdblist",
                args=(("count", count),),
                kwargs={"start": start, "duration": duration},
            )
        )

    def clientdbinfo(self, cldbid: int) -> QueryResponse:
        """
        Displays detailed database information about a client including unique ID,
        creation date, etc.
        """

        return self.query.send(QueryCommand("clientdbinfo", kwargs={"cldbid": cldbid}))

    def clientdbfind(self, pattern: str, uid: bool = False) -> QueryResponse:
        """
        Displays a list of client database IDs matching a given pattern. You can either
        search for a clients last known nickname or his unique identity by using the
        -uid option. The pattern parameter can include regular characters and SQL
        wildcard characters (e.g. %).
        """

        return self.query.send(
            QueryCommand(
                "clientdbfind", args=(("uid", uid),), kwargs={"pattern": pattern}
            )
        )

    def clientdbedit(self, cldbid: int, **kwargs) -> QueryResponse:
        """
        Changes a clients settings using given properties. For detailed information,
        see Client Properties.
        """

        _validate_client_kwargs(kwargs)

        return self.query.send(
            QueryCommand("clientdbedit", kwargs={"cldbid": cldbid, **kwargs})
        )

    def clientdbdelete(self, cldbid: int) -> QueryResponse:
        """
        Deletes a clients properties from the database.
        """

        return self.query.send(
            QueryCommand("clientdbdelete", kwargs={"cldbid": cldbid})
        )

    def clientgetids(self, cluid: str) -> QueryResponse:
        """
        Displays all client IDs matching the unique identifier specified by cluid.
        """

        return self.query.send(QueryCommand("clientgetids", kwargs={"cluid": cluid}))

    def clientgetdbidfromuid(self, cluid: str) -> QueryResponse:
        """
        Displays the database ID matching the unique identifier specified by cluid.
        """

        return self.query.send(
            QueryCommand("clientgetdbidfromuid", kwargs={"cluid": cluid})
        )

    def clientgetnamefromuid(self, cluid: str) -> QueryResponse:
        """
        Displays the database ID and nickname matching the unique identifier specified
        by cluid.
        """

        return self.query.send(
            QueryCommand("clientgetnamefromuid", kwargs={"cluid": cluid})
        )

    def clientgetuidfromclid(self, clid: int) -> QueryResponse:
        """
        Displays the unique identifier matching the clientID specified by clid.
        """

        return self.query.send(
            QueryCommand("clientgetuidfromclid", kwargs={"clid": clid})
        )

    def clientgetnamefromdbid(self, cldbid: int) -> QueryResponse:
        """
        Displays the unique identifier and nickname matching the database ID specified
        by cldbid.
        """

        return self.query.send(
            QueryCommand("clientgetnamefromdbid", kwargs={"cldbid": cldbid})
        )

    def clientsetserverquerylogin(self, client_login_name: str) -> QueryResponse:
        """
        Updates your own ServerQuery login credentials using a specified username. The
        password will be auto-generated.
        """

        return self.query.send(
            QueryCommand(
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

        return self.query.send(QueryCommand("clientupdate", kwargs=kwargs))

    def clientmove(
        self, clid: int, cid: int, cpw: Optional[str] = None
    ) -> QueryResponse:
        """
        Moves one or more clients specified with clid to the channel with ID cid. If the
        target channel has a password, it needs to be specified with cpw. If the channel
        has no password, the parameter can be omitted.
        """

        return self.query.send(
            QueryCommand("clientmove", kwargs={"clid": clid, "cid": cid, "cpw": cpw})
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
            QueryCommand(
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
            QueryCommand("clientpoke", kwargs={"clid": clid, "msg": msg})
        )

    def clientpermlist(self, cldbid: int, permsid: bool = False) -> QueryResponse:
        """
        Displays a list of permissions defined for a client.
        """

        return self.query.send(
            QueryCommand(
                "clientpermlist",
                args=(("permsid", permsid),),
                kwargs={"cldbid": cldbid},
            )
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
            QueryCommand(
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
            QueryCommand(
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
            QueryCommand(
                "channelclientpermlist",
                args=(("permsid", permsid),),
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
            QueryCommand(
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
            QueryCommand(
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

        return self.query.send(QueryCommand("permissionlist"))

    def permidgetbyname(self, permsid: str) -> QueryResponse:
        """
        Displays the database ID of one or more permissions specified by permsid.
        """

        return self.query.send(
            QueryCommand("permidgetbyname", kwargs={"permsid": permsid})
        )

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
            QueryCommand(
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
            QueryCommand("permget", kwargs={"permid": permid, "permsid": permsid})
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
            QueryCommand("permfind", kwargs={"permid": permid, "permsid": permsid})
        )

    def permreset(self) -> QueryResponse:
        """
        Restores the default permission settings on the selected virtual server and
        creates a new initial administrator token. Please note that in case of an error
        during the permreset call - e.g. when the database has been modified or
        corrupted - the virtual server will be deleted from the database.
        """

        return self.query.send(QueryCommand("permreset"))

    def privilegekeylist(self) -> QueryResponse:
        """
        Displays a list of privilege keys available including their type and group IDs.
        Tokens can be used to gain access to specified server or channel groups. A
        privilege key is similar to a client with administrator privileges that adds
        you to a certain permission group, but without the necessity of a such a client
        with administrator privileges to actually exist. It is a long (random looking)
        string that can be used as a ticket into a specific server group.
        """

        return self.query.send(QueryCommand("privilegekeylist"))

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
            QueryCommand(
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

        return self.query.send(
            QueryCommand("privilegekeydelete", kwargs={"token": token})
        )

    def privilegekeyuse(self, token: str) -> QueryResponse:
        """
        Use a token key gain access to a server or channel group. Please note that the
        server will automatically delete the token after it has been used.
        """

        return self.query.send(QueryCommand("privilegekeyuse", kwargs={"token": token}))

    def messagelist(self) -> QueryResponse:
        """
        Displays a list of offline messages you've received. The output contains the
        senders unique identifier, the messages subject, etc.
        """

        return self.query.send(QueryCommand("messagelist"))

    def messageadd(self) -> QueryResponse:
        """
        Sends an offline message to the client specified by cluid.
        """

        return self.query.send(QueryCommand("messageadd"))

    def messagedel(self, msgid: int) -> QueryResponse:
        """
        Deletes an existing offline message with ID msgid from your inbox.
        """

        return self.query.send(QueryCommand("messagedel", kwargs={"msgid": msgid}))

    def messageget(self, msgid: int) -> QueryResponse:
        """
        Displays an existing offline message with ID msgid from your inbox. Please note
        that this does not automatically set the flag_read property of the message.
        """

        return self.query.send(QueryCommand("messageget", kwargs={"msgid": msgid}))

    def messageupdateflag(self, msgid: int, flag: bool) -> QueryResponse:
        """
        Updates the flag_read property of the offline message specified with msgid. If
        flag is set to 1, the message will be marked as read.
        """

        return self.query.send(
            QueryCommand("messageupdateflag", kwargs={"msgid": msgid, "flag": flag})
        )

    def complainlist(self, tcldbid: Optional[int]) -> QueryResponse:
        """
        Displays a list of complaints on the selected virtual server. If tcldbid is
        specified, only complaints about the targeted client will be shown.
        """

        return self.query.send(
            QueryCommand("complainlist", kwargs={"tcldbid": tcldbid})
        )

    def complainadd(self, tcldbid: int, message: str) -> QueryResponse:
        """
        Submits a complaint about a connected client with database ID tcldbid to the
        server.
        """

        return self.query.send(
            QueryCommand("complainadd", kwargs={"tcldbid": tcldbid, "message": message})
        )

    def complaindelall(self, tcldbid: int) -> QueryResponse:
        """
        Deletes all complaints about the client with database ID tcldbid from the
        server.
        """

        return self.query.send(
            QueryCommand("complaindelall", kwargs={"tcldbid": tcldbid})
        )

    def complaindel(self, tcldbid: int, fcldbid: int) -> QueryResponse:
        """
        Deletes the complaint about the client with ID tcldbid submitted by the client
        with ID fcldbid from the server.
        """

        return self.query.send(
            QueryCommand("complaindel", kwargs={"tcldbid": tcldbid, "fcldbid": fcldbid})
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
            QueryCommand(
                "banclient", kwargs={"clid": clid, "time": time, "banreason": banreason}
            )
        )

    def banlist(self) -> QueryResponse:
        """
        Displays a list of active bans on the selected virtual server.
        """

        return self.query.send(QueryCommand("banlist"))

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
            QueryCommand(
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

        return self.query.send(QueryCommand("bandel", kwargs={"banid": banid}))

    def bandelall(self) -> QueryResponse:
        """
        Deletes all active ban rules from the server.
        """

        return self.query.send(QueryCommand("bandelall"))

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
            QueryCommand(
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
            QueryCommand(
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

        return self.query.send(QueryCommand("ftlist"))

    def ftgetfilelist(self, cid: int, cpw: str, path: str) -> QueryResponse:
        """
        Displays a list of files and directories stored in the specified channels file
        repository.
        """

        return self.query.send(
            QueryCommand("ftgetfilelist", kwargs={"cid": cid, "cpw": cpw, "path": path})
        )

    def ftgetfileinfo(self, cid: int, cpw: str, name: str) -> QueryResponse:
        """
        Displays detailed information about one or more specified files stored in a
        channels file repository.
        """

        return self.query.send(
            QueryCommand("ftgetfileinfo", kwargs={"cid": cid, "cpw": cpw, "name": name})
        )

    def ftstop(self, serverftfid: int, delete: Optional[bool]) -> QueryResponse:
        """
        Stops the running file transfer with server-side ID serverftfid.
        """

        return self.query.send(
            QueryCommand(
                "ftstop", kwargs={"serverftfid": serverftfid, "delete": delete}
            )
        )

    def ftdeletefile(self, cid: int, cpw: str, name: str) -> QueryResponse:
        """
        Deletes one or more files stored in a channels file repository.
        """

        return self.query.send(
            QueryCommand("ftdeletefile", kwargs={"cid": cid, "cpw": cpw, "name": name})
        )

    def ftcreatedir(self, cid: int, cpw: str, dirname: str) -> QueryResponse:
        """
        Creates new directory in a channels file repository.
        """

        return self.query.send(
            QueryCommand(
                "ftcreatedir", kwargs={"cid": cid, "cpw": cpw, "dirname": dirname}
            )
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
            QueryCommand(
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
            QueryCommand("customsearch", kwargs={"ident": ident, "value": value})
        )

    def custominfo(self, cldbid: int) -> QueryResponse:
        """
        Displays a list of custom properties for the client specified with cldbid.
        """

        return self.query.send(QueryCommand("custominfo", kwargs={"cldbid": cldbid}))

    def whoami(self) -> QueryResponse:
        """
        Displays information about your current ServerQuery connection including your
        loginname, etc.
        """

        return self.query.send(QueryCommand("whoami"))


def _validate_kwargs(args: dict) -> None:
    """Validates the arguments passed to a query command.

    :param args: Arguments to validate.
    :type args: dict
    :raises ValueError: Raised if any argument value is not a string, integer or float.
    """
    if not all([isinstance(arg, (str, int, float)) for arg in args.values()]):
        raise ValueError("All argument values must be strings, integers or floats.")


def _validate_server_instance_kwargs(args: dict) -> None:
    """Validates the arguments passed to a server instance query command.

    :param args: Arguments to validate.
    :type args: dict
    :raises ValueError: Raised if any argument is not a valid changeable server instance property.
    """
    _validate_kwargs(args)

    for key in args.keys():
        if str(key).upper() not in ChangeableServerInstanceProperties.keys():
            raise ValueError(
                f"Invalid argument: {key}\n\
                \rValid arguments: {ChangeableServerInstanceProperties.keys()}"
            )


def _validate_channel_kwargs(args: dict) -> None:
    """Validates the arguments passed to a channel query command.

    :param args: Arguments to validate.
    :type args: dict
    :raises ValueError: Raised if any argument is not a valid changeable channel property.
    """
    _validate_kwargs(args)

    for key in args.keys():
        if str(key).upper() not in ChangeableChannelProperties.keys():
            raise ValueError(
                f"Invalid argument: {key}\n\
                \rValid arguments: {ChangeableChannelProperties.keys()}"
            )


def _validate_client_kwargs(args: dict) -> None:
    """Validates the arguments passed to a client query command.

    :param args: Arguments to validate.
    :type args: dict
    :raises ValueError: Raised if any argument is not a valid changeable client property.
    """
    _validate_kwargs(args)

    for key in args.keys():
        if str(key).upper() not in ChangeableClientProperties.keys():
            raise ValueError(
                f"Invalid argument: {key}\n\
                \rValid arguments: {ChangeableClientProperties.keys()}"
            )


def _validate_virtual_server_kwargs(args: dict) -> None:
    """Validates the arguments passed to a virtual server query command.

    :param args: Arguments to validate.
    :type args: dict
    :raises ValueError: Raised if any argument is not a valid changeable virtual server property.
    """
    _validate_kwargs(args)

    for key in args.keys():
        if str(key).upper() not in ChangeableVirtualServerProperties.keys():
            raise ValueError(
                f"Invalid argument: {key}\n\
                \rValid arguments: {ChangeableVirtualServerProperties.keys()}"
            )
