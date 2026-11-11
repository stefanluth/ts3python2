from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Callable, Literal

from ts3client.constants import Codec

Mode = Literal["cycle", "noop", "skip"]
Command = Literal["edit", "create", "clientupdate"]
Target = Literal["scratch", "default"]
EditKwargs = Callable[["Context"], dict[str, Any]]
Verify = Callable[["Context", dict[str, Any]], dict[str, Any]]
Restore = Callable[[dict[str, Any]], dict[str, Any]]

SERVER_DEFAULT_GROUPS = (15, 30, 45)
CHANNEL_DEFAULT_GROUPS = (10, 25, 35, 40)
CHANNEL_ADMIN_GROUPS = (35, 40)
QUERY_SERVER_GROUPS = (20, 50)


@dataclass(frozen=True)
class Context:
    info: dict[str, Any]
    regular_server_groups: tuple[int, ...] = ()
    query_server_groups: tuple[int, ...] = ()
    template_server_groups: tuple[int, ...] = ()
    regular_channel_groups: tuple[int, ...] = ()
    template_channel_groups: tuple[int, ...] = ()
    parent_cid: int | None = None
    default_cid: int | None = None

    def unique(self, prefix: str) -> str:
        return f"{prefix}-{time.time_ns()}"

    def server_group(self, current: int | None, candidates: tuple[int, ...] = SERVER_DEFAULT_GROUPS) -> int:
        return _other_group(self.regular_server_groups, candidates, current)

    def query_group(self, current: int | None, candidates: tuple[int, ...] = QUERY_SERVER_GROUPS) -> int:
        return _other_group(self.query_server_groups, candidates, current)

    def template_server_group(self, current: int | None) -> int:
        return _other_group(self.template_server_groups, (), current)

    def channel_group(self, current: int | None, candidates: tuple[int, ...] = CHANNEL_DEFAULT_GROUPS) -> int:
        return _other_group(self.regular_channel_groups, candidates, current)

    def template_channel_group(self, current: int | None) -> int:
        return _other_group(self.template_channel_groups, (), current)


@dataclass(frozen=True)
class Case:
    property: str
    mode: Mode
    kwargs: EditKwargs
    verify: Verify | None = None
    restore: Restore | None = None
    command: Command = "edit"
    target: Target = "scratch"
    note: str = ""
    needs_parent: bool = False


def cycle(
    prop: str,
    value: Any,
    *,
    verify: Verify | None = None,
    restore: Restore | None = None,
    note: str = "",
    command: Command = "edit",
    target: Target = "scratch",
    needs_parent: bool = False,
) -> Case:
    return Case(
        property=prop,
        mode="cycle",
        kwargs=lambda ctx: {prop: value(ctx) if callable(value) else value},
        verify=verify,
        restore=restore,
        command=command,
        target=target,
        note=note,
        needs_parent=needs_parent,
    )


def cycle_many(
    prop: str,
    kwargs: EditKwargs,
    *,
    verify: Verify | None = None,
    restore: Restore | None = None,
    note: str = "",
    command: Command = "edit",
    target: Target = "scratch",
    needs_parent: bool = False,
) -> Case:
    return Case(
        property=prop,
        mode="cycle",
        kwargs=kwargs,
        verify=verify,
        restore=restore,
        command=command,
        target=target,
        note=note,
        needs_parent=needs_parent,
    )


def noop(prop: str, *, note: str = "", command: Command = "edit") -> Case:
    return Case(
        property=prop,
        mode="noop",
        kwargs=lambda ctx: {prop: ctx.info[prop]},
        command=command,
        note=note,
    )


def skip(prop: str, note: str) -> Case:
    return Case(property=prop, mode="skip", kwargs=lambda ctx: {}, note=note)


CHANNEL_CASES = {
    case.property: case
    for case in [
        cycle("channel_name", lambda ctx: ctx.unique("channel-name")),
        cycle("channel_topic", lambda ctx: ctx.unique("channel-topic")),
        cycle("channel_description", lambda ctx: ctx.unique("channel-description")),
        cycle(
            "channel_password",
            "integration-channel-password",
            verify=lambda ctx, sent: {"channel_flag_password": 1},
        ),
        cycle("channel_codec", Codec.CODEC_OPUS_VOICE.value),
        cycle("channel_codec_quality", lambda ctx: 5 if ctx.info["channel_codec_quality"] != 5 else 4),
        cycle("channel_codec_latency_factor", lambda ctx: 1 if ctx.info["channel_codec_latency_factor"] != 1 else 2),
        cycle("channel_maxclients", lambda ctx: _changed_number(ctx.info["channel_maxclients"], 32)),
        cycle("channel_maxfamilyclients", lambda ctx: 64 if ctx.info["channel_maxfamilyclients"] != 64 else 65),
        noop("channel_order", note="ordering is exercised by the channelmove tests"),
        noop("channel_flag_permanent", note="the scratch channel is created permanent"),
        cycle_many(
            "channel_flag_semi_permanent",
            lambda ctx: {"channel_flag_permanent": 0, "channel_flag_semi_permanent": 1},
            verify=lambda ctx, sent: {"channel_flag_semi_permanent": 1},
            command="create",
        ),
        cycle(
            "channel_flag_default",
            1,
            target="default",
            restore=lambda before: {},
        ),
        cycle_many(
            "channel_flag_maxclients_unlimited",
            lambda ctx: {"channel_maxclients": 32, "channel_flag_maxclients_unlimited": 0},
        ),
        cycle_many(
            "channel_flag_maxfamilyclients_unlimited",
            lambda ctx: {"channel_maxfamilyclients": 64, "channel_flag_maxfamilyclients_unlimited": 0},
        ),
        cycle_many(
            "channel_flag_maxfamilyclients_inherited",
            lambda ctx: {
                "channel_flag_maxfamilyclients_inherited": _toggled(
                    ctx.info["channel_flag_maxfamilyclients_inherited"]
                ),
                "channel_maxfamilyclients": 64,
            },
            verify=lambda ctx, sent: {
                "channel_flag_maxfamilyclients_inherited": sent["channel_flag_maxfamilyclients_inherited"]
            },
        ),
        cycle("channel_needed_talk_power", lambda ctx: _changed_number(ctx.info["channel_needed_talk_power"], 1)),
        cycle("channel_name_phonetic", lambda ctx: ctx.unique("channel-phonetic")),
        skip("channel_icon_id", "a channel icon needs an uploaded icon file"),
        cycle("channel_codec_is_unencrypted", lambda ctx: _toggled(ctx.info["channel_codec_is_unencrypted"])),
        cycle_many(
            "channel_delete_delay",
            lambda ctx: {
                "channel_flag_permanent": 0,
                "channel_flag_semi_permanent": 0,
                "channel_delete_delay": 5,
            },
            verify=lambda ctx, sent: {},
            restore=lambda before: {},
        ),
        cycle_many(
            "cpid",
            lambda ctx: {"cpid": ctx.parent_cid, "channel_flag_permanent": 1},
            verify=lambda ctx, sent: {"pid": sent["cpid"]},
            command="create",
            needs_parent=True,
        ),
    ]
}


CLIENT_CASES = {
    case.property: case
    for case in [
        cycle(
            "client_nickname",
            lambda ctx: ctx.unique("nick"),
            command="clientupdate",
            restore=lambda before: {},
        ),
        noop("client_is_talker", note="query clients cannot talk"),
        cycle(
            "client_description",
            lambda ctx: ctx.unique("description"),
        ),
        cycle(
            "client_is_channel_commander",
            lambda ctx: _toggled(ctx.info["client_is_channel_commander"]),
            command="clientupdate",
        ),
        skip("client_icon_id", "a client icon needs an uploaded icon file"),
    ]
}


SERVER_INSTANCE_CASES = {
    case.property: case
    for case in [
        cycle(
            "serverinstance_guest_serverquery_group",
            lambda ctx: ctx.query_group(ctx.info["serverinstance_guest_serverquery_group"]),
        ),
        cycle(
            "serverinstance_template_serveradmin_group",
            lambda ctx: ctx.template_server_group(ctx.info["serverinstance_template_serveradmin_group"]),
        ),
        noop("serverinstance_filetransfer_port", note="changing the file transfer port can break transfers"),
        cycle(
            "serverinstance_max_download_total_bandwidth",
            lambda ctx: _changed_number(ctx.info["serverinstance_max_download_total_bandwidth"], 1_000_000),
        ),
        cycle(
            "serverinstance_max_upload_total_bandwidth",
            lambda ctx: _changed_number(ctx.info["serverinstance_max_upload_total_bandwidth"], 1_000_000),
        ),
        cycle(
            "serverinstance_template_serverdefault_group",
            lambda ctx: ctx.template_server_group(ctx.info["serverinstance_template_serverdefault_group"]),
        ),
        cycle(
            "serverinstance_template_channeldefault_group",
            lambda ctx: ctx.template_channel_group(ctx.info["serverinstance_template_channeldefault_group"]),
        ),
        cycle(
            "serverinstance_template_channeladmin_group",
            lambda ctx: ctx.template_channel_group(ctx.info["serverinstance_template_channeladmin_group"]),
        ),
        cycle(
            "serverinstance_serverquery_flood_commands",
            lambda ctx: _changed_number(ctx.info["serverinstance_serverquery_flood_commands"], 10),
        ),
        cycle(
            "serverinstance_serverquery_flood_time",
            lambda ctx: _changed_number(ctx.info["serverinstance_serverquery_flood_time"], 3),
        ),
        cycle(
            "serverinstance_serverquery_ban_time",
            lambda ctx: _changed_number(ctx.info["serverinstance_serverquery_ban_time"], 3),
        ),
    ]
}


VSERVER_CASES = {
    case.property: case
    for case in [
        cycle("virtualserver_name", lambda ctx: ctx.unique("virtualserver-name")),
        cycle("virtualserver_welcomemessage", lambda ctx: ctx.unique("virtualserver-welcome")),
        cycle("virtualserver_maxclients", lambda ctx: _changed_number(ctx.info["virtualserver_maxclients"], 32)),
        cycle(
            "virtualserver_password",
            "integration-server-password",
            verify=lambda ctx, sent: {"virtualserver_flag_password": 1},
            restore=lambda before: {"virtualserver_password": ""},
        ),
        cycle("virtualserver_hostmessage", lambda ctx: ctx.unique("virtualserver-hostmessage")),
        cycle(
            "virtualserver_hostmessage_mode",
            lambda ctx: 2 if ctx.info["virtualserver_hostmessage_mode"] != 2 else 1,
        ),
        cycle(
            "virtualserver_default_server_group",
            lambda ctx: ctx.server_group(ctx.info["virtualserver_default_server_group"]),
        ),
        cycle(
            "virtualserver_default_channel_group",
            lambda ctx: ctx.channel_group(ctx.info["virtualserver_default_channel_group"]),
        ),
        cycle(
            "virtualserver_default_channel_admin_group",
            lambda ctx: ctx.channel_group(
                ctx.info["virtualserver_default_channel_admin_group"],
                CHANNEL_ADMIN_GROUPS,
            ),
        ),
        cycle(
            "virtualserver_max_download_total_bandwidth",
            lambda ctx: _changed_number(ctx.info["virtualserver_max_download_total_bandwidth"], 1_000_000),
        ),
        cycle(
            "virtualserver_max_upload_total_bandwidth",
            lambda ctx: _changed_number(ctx.info["virtualserver_max_upload_total_bandwidth"], 1_000_000),
        ),
        cycle("virtualserver_hostbanner_url", lambda ctx: ctx.unique("https://example.com/banner")),
        cycle("virtualserver_hostbanner_gfx_url", lambda ctx: ctx.unique("https://example.com/banner.png")),
        cycle(
            "virtualserver_hostbanner_gfx_interval",
            lambda ctx: 120 if ctx.info["virtualserver_hostbanner_gfx_interval"] != 120 else 60,
        ),
        cycle(
            "virtualserver_complain_autoban_count",
            lambda ctx: _changed_number(ctx.info["virtualserver_complain_autoban_count"], 3),
        ),
        cycle(
            "virtualserver_complain_autoban_time",
            lambda ctx: _changed_number(ctx.info["virtualserver_complain_autoban_time"], 1200),
        ),
        cycle(
            "virtualserver_complain_remove_time",
            lambda ctx: _changed_number(ctx.info["virtualserver_complain_remove_time"], 1800),
        ),
        cycle(
            "virtualserver_min_clients_in_channel_before_forced_silence",
            lambda ctx: _changed_number(
                ctx.info["virtualserver_min_clients_in_channel_before_forced_silence"],
                2,
            ),
        ),
        cycle(
            "virtualserver_priority_speaker_dimm_modificator",
            lambda ctx: -5 if _as_int(ctx.info["virtualserver_priority_speaker_dimm_modificator"]) != -5 else -10,
        ),
        cycle(
            "virtualserver_antiflood_points_tick_reduce",
            lambda ctx: _changed_number(ctx.info["virtualserver_antiflood_points_tick_reduce"], 1),
        ),
        cycle(
            "virtualserver_antiflood_points_needed_command_block",
            lambda ctx: _changed_number(ctx.info["virtualserver_antiflood_points_needed_command_block"], 1),
        ),
        cycle(
            "virtualserver_antiflood_points_needed_plugin_block",
            lambda ctx: _changed_number(ctx.info["virtualserver_antiflood_points_needed_plugin_block"], 1),
        ),
        cycle(
            "virtualserver_antiflood_points_needed_ip_block",
            lambda ctx: _changed_number(ctx.info["virtualserver_antiflood_points_needed_ip_block"], 1),
        ),
        cycle(
            "virtualserver_hostbanner_mode",
            lambda ctx: 2 if ctx.info["virtualserver_hostbanner_mode"] != 2 else 1,
        ),
        cycle("virtualserver_hostbutton_tooltip", lambda ctx: ctx.unique("hostbutton-tooltip")),
        cycle("virtualserver_hostbutton_gfx_url", lambda ctx: ctx.unique("https://example.com/button.png")),
        cycle("virtualserver_hostbutton_url", lambda ctx: ctx.unique("https://example.com/button")),
        cycle(
            "virtualserver_download_quota",
            lambda ctx: _changed_number(ctx.info["virtualserver_download_quota"], 1024),
        ),
        cycle(
            "virtualserver_upload_quota",
            lambda ctx: _changed_number(ctx.info["virtualserver_upload_quota"], 1024),
        ),
        noop("virtualserver_machine_id", note="the machine id identifies the server instance"),
        noop("virtualserver_port", note="changing the port would drop the active connection"),
        cycle("virtualserver_autostart", lambda ctx: _toggled(ctx.info["virtualserver_autostart"])),
        noop("virtualserver_status", note="the status is reported by the server"),
        cycle("virtualserver_log_client", lambda ctx: _toggled(ctx.info["virtualserver_log_client"])),
        cycle("virtualserver_log_query", lambda ctx: _toggled(ctx.info["virtualserver_log_query"])),
        cycle("virtualserver_log_channel", lambda ctx: _toggled(ctx.info["virtualserver_log_channel"])),
        cycle("virtualserver_log_permissions", lambda ctx: _toggled(ctx.info["virtualserver_log_permissions"])),
        cycle("virtualserver_log_server", lambda ctx: _toggled(ctx.info["virtualserver_log_server"])),
        cycle("virtualserver_log_filetransfer", lambda ctx: _toggled(ctx.info["virtualserver_log_filetransfer"])),
        noop("virtualserver_min_client_version", note="lowering this can lock clients out"),
        noop("virtualserver_min_android_version", note="lowering this can lock clients out"),
        noop("virtualserver_min_ios_version", note="lowering this can lock clients out"),
        noop("virtualserver_min_winphone_version", note="lowering this can lock clients out"),
        noop(
            "virtualserver_needed_identity_security_level",
            note="raising this can lock clients out",
        ),
        cycle("virtualserver_name_phonetic", lambda ctx: ctx.unique("virtualserver-phonetic")),
        noop("virtualserver_icon_id", note="a server icon needs an uploaded icon file"),
        cycle("virtualserver_reserved_slots", lambda ctx: ctx.info["virtualserver_reserved_slots"] + 1),
        cycle("virtualserver_weblist_enabled", lambda ctx: _toggled(ctx.info["virtualserver_weblist_enabled"])),
        cycle(
            "virtualserver_codec_encryption_mode",
            lambda ctx: 1 if ctx.info["virtualserver_codec_encryption_mode"] != 1 else 2,
        ),
        cycle(
            "virtualserver_channel_temp_delete_delay_default",
            lambda ctx: 1 if ctx.info["virtualserver_channel_temp_delete_delay_default"] != 1 else 2,
        ),
    ]
}


def _other_group(groups: tuple[int, ...], candidates: tuple[int, ...], current: int | None) -> int:
    for group in candidates:
        if group in groups and group != current:
            return group
    for group in groups:
        if group != current:
            return group
    raise AssertionError("no alternate group is available on the server")


def _toggled(value: int) -> int:
    return 0 if value else 1


def _as_int(value: Any) -> int:
    return int(float(value))


def _changed_number(value: Any, fallback: int) -> int:
    number = _as_int(value)
    if number <= 0:
        return fallback
    return number - 1 if number > 1 else number + 1
