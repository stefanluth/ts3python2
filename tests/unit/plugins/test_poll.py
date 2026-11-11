import json
from datetime import datetime, timedelta, timezone

import pytest

import plugins.commands.poll as poll_module
from plugins.commands.poll import Poll
from tests.support.fakes import FakeClient, FakeLogger, FakeMessage
from ts3client.channel import Channel
from ts3client.constants import TargetMode
from ts3client.user import User, UserInfo

NOW = datetime(2026, 11, 12, 12, 0, tzinfo=timezone.utc)


class PollClient(FakeClient):
    def __init__(self):
        super().__init__()
        self.channels = []

    def get_channels(self):
        return self.channels


@pytest.fixture(autouse=True)
def fixed_time(monkeypatch):
    monkeypatch.setattr(poll_module, "utcnow", lambda: NOW)


def make_poll(tmp_path, client=None, **kwargs):
    client = client if client is not None else PollClient()
    poll = Poll(client, "poll", polls_dir=str(tmp_path), **kwargs)
    poll.logger = FakeLogger()
    poll.store.logger = FakeLogger()
    return poll


def make_user(clid, name="User", uid=None, cid=10, client_type=0):
    return User(
        clid=clid,
        client_nickname=name,
        cid=cid,
        client_type=client_type,
        client_unique_identifier=uid or f"uid-{clid}",
    )


def only_poll(command):
    polls = command.store.list_polls(include_closed=True)
    assert len(polls) == 1
    return polls[0]


def messages_to(client, clid):
    return [text for target, text in client.sent if target == clid]


def test_create_server_poll_announces_and_notifies(tmp_path):
    client = PollClient()
    client.users = [
        make_user(1, "Bot", "bot-uid"),
        make_user(2, "Creator", "creator-uid"),
        make_user(3, "Alice", "uid-3"),
        make_user(4, "Query", "query-uid", client_type=1),
    ]
    poll = make_poll(tmp_path, client)
    message = FakeMessage(
        "!poll create Lunch? | Pizza | Sushi",
        invokername="Creator",
        invokerid=2,
        invokeruid="creator-uid",
    )

    poll.run(message)

    stored = only_poll(poll)
    assert stored.scope == "server"
    assert (tmp_path / f"{stored.id}.json").exists()
    assert len(client.server_sent) == 1
    announcement = client.server_sent[0]
    assert "[server poll" in announcement
    assert stored.id in announcement
    assert "Lunch?" in announcement
    assert announcement.count("Vote:") == 1
    assert "Vote: !poll vote" in announcement
    assert [target for target, _ in client.sent] == [2, 3]
    assert messages_to(client, 3) == [announcement]
    assert any("Created server poll" in text for text in messages_to(client, 2))
    assert messages_to(client, 4) == []
    assert messages_to(client, 1) == []


def test_create_channel_poll_uses_target_and_only_notifies_channel(tmp_path):
    client = PollClient()
    client.channels = [Channel(cid=10, channel_name="Lobby")]
    client.users = [
        make_user(1, "Bot", "bot-uid"),
        make_user(2, "Creator", "creator-uid", cid=10),
        make_user(3, "Alice", "uid-3", cid=10),
        make_user(5, "Outsider", "uid-5", cid=20),
        make_user(6, "Query", "query-uid", cid=10, client_type=1),
    ]
    poll = make_poll(tmp_path, client)
    message = FakeMessage(
        "!poll create Lunch? | Pizza | Sushi",
        invokername="Creator",
        invokerid=2,
        invokeruid="creator-uid",
        targetmode=TargetMode.CHANNEL.value,
        target=10,
    )

    poll.run(message)

    stored = only_poll(poll)
    assert stored.scope == "channel"
    assert stored.channel_id == 10
    assert stored.channel_name == "Lobby"
    assert len(client.messages_sent) == 1
    target, mode, announcement = client.messages_sent[0]
    assert target == 10
    assert mode == TargetMode.CHANNEL
    assert f"[channel poll {stored.id} #Lobby]" in announcement
    assert [target for target, _ in client.sent] == [2, 3]
    assert messages_to(client, 5) == []
    assert messages_to(client, 6) == []


def test_channel_message_without_target_resolves_invoker_channel(tmp_path):
    client = PollClient()
    client.channels = [Channel(cid=10, channel_name="Lobby")]
    client.users = [
        make_user(2, "Creator", "creator-uid", cid=10),
        make_user(3, "Alice", "uid-3", cid=10),
    ]
    client.user_infos[2] = UserInfo(clid=2, cid=10, client_unique_identifier="creator-uid")
    poll = make_poll(tmp_path, client)

    poll.run(
        FakeMessage(
            "!poll create Lunch? | Pizza | Sushi",
            invokername="Creator",
            invokerid=2,
            invokeruid="creator-uid",
            targetmode=TargetMode.CHANNEL.value,
            target=0,
        )
    )

    stored = only_poll(poll)
    assert stored.scope == "channel"
    assert stored.channel_id == 10
    assert client.messages_sent[0][0] == 10


def test_other_connection_with_creator_uid_receives_creation_pm(tmp_path):
    client = PollClient()
    client.users = [
        make_user(1, "Bot", "bot-uid"),
        make_user(2, "Creator", "shared-uid"),
        make_user(3, "CreatorOther", "shared-uid"),
    ]
    poll = make_poll(tmp_path, client)
    message = FakeMessage(
        "!poll create Lunch? | Pizza | Sushi",
        invokername="Creator",
        invokerid=2,
        invokeruid="shared-uid",
    )

    poll.run(message)

    announcement = client.server_sent[0]
    assert (3, announcement) in client.sent
    assert any(target == 2 and "Created server poll" in text for target, text in client.sent)


def test_scope_overrides_for_channel_and_private_messages(tmp_path):
    client = PollClient()
    client.channels = [Channel(cid=10, channel_name="Lobby")]
    client.users = [make_user(2, "Creator", "creator-uid", cid=10)]
    client.user_infos[2] = UserInfo(clid=2, cid=10, client_unique_identifier="creator-uid")
    poll = make_poll(tmp_path, client)

    poll.run(
        FakeMessage(
            "!poll create Server? | A | B --server",
            invokername="Creator",
            invokerid=2,
            invokeruid="creator-uid",
            targetmode=TargetMode.CHANNEL.value,
            target=10,
        )
    )
    server_poll = only_poll(poll)
    assert server_poll.scope == "server"
    assert len(client.server_sent) == 1
    assert client.messages_sent == []

    poll.run(
        FakeMessage(
            "!poll create Private? | A | B --channel",
            invokername="Creator",
            invokerid=2,
            invokeruid="creator-uid",
        )
    )
    channel_poll = poll.store.get(server_poll.id)
    channel_polls = [item for item in poll.store.list_polls(include_closed=True) if item.scope == "channel"]
    assert channel_polls
    assert channel_polls[0].channel_id == 10
    assert channel_polls[0].channel_name == "Lobby"
    assert client.messages_sent[0][0] == 10
    assert "#Lobby" in client.messages_sent[0][2]
    assert channel_poll is not None


def test_conflicting_scope_flags_are_rejected(tmp_path):
    client = PollClient()
    client.users = [make_user(2, "Creator", "creator-uid")]
    poll = make_poll(tmp_path, client)

    poll.run(
        FakeMessage(
            "!poll create Nope? | A | B --server --channel",
            invokername="Creator",
            invokerid=2,
            invokeruid="creator-uid",
        )
    )

    assert poll.store.list_polls(include_closed=True) == []
    assert "either --server or --channel" in client.sent[-1][1]


def test_pm_failure_does_not_stop_fanout(tmp_path):
    client = PollClient()
    client.users = [
        make_user(2, "Creator", "creator-uid"),
        make_user(3, "Alice", "uid-3"),
        make_user(4, "Bob", "uid-4"),
    ]
    original = client.send_private_message

    def flaky(clid, message):
        if clid == 3:
            raise RuntimeError("send failed")
        original(clid, message)

    client.send_private_message = flaky
    poll = make_poll(tmp_path, client)

    poll.run(
        FakeMessage(
            "!poll create Lunch? | Pizza | Sushi",
            invokername="Creator",
            invokerid=2,
            invokeruid="creator-uid",
        )
    )

    assert client.server_sent
    assert any(target == 4 for target, _ in client.sent)
    assert any(target == 2 for target, _ in client.sent)
    assert all(target != 3 for target, _ in client.sent)


def test_vote_single_choice_confirms_voter_and_creator(tmp_path):
    client = PollClient()
    client.users = [
        make_user(2, "Creator", "creator-uid"),
        make_user(3, "Alice", "uid-3"),
    ]
    poll = make_poll(tmp_path, client)
    poll.run(
        FakeMessage(
            "!poll create Lunch? | Pizza | Sushi",
            invokername="Creator",
            invokerid=2,
            invokeruid="creator-uid",
        )
    )
    stored = only_poll(poll)
    client.sent.clear()

    poll.run(
        FakeMessage(
            f"!poll vote {stored.id} a",
            invokername="Alice",
            invokerid=3,
            invokeruid="uid-3",
        )
    )

    updated = poll.store.get(stored.id)
    assert updated is not None
    assert updated.counts() == [1, 0]
    assert updated.votes == {"uid-3": [0]}
    assert any(f"Vote recorded for {stored.id}: a." in text for _, text in client.sent)
    assert any("Alice voted on poll" in text for text in messages_to(client, 2))


@pytest.mark.parametrize("form", ["ac", "a,c", "a c"], ids=["joined", "comma", "spaced"])
def test_multi_choice_accepts_equivalent_option_tokens(tmp_path, form):
    client = PollClient()
    client.users = [make_user(3, "Alice", "uid-3")]
    poll = make_poll(tmp_path, client)
    poll.run(
        FakeMessage(
            "!poll create Pick | A | B | C --multi",
            invokername="Creator",
            invokerid=2,
            invokeruid="creator-uid",
        )
    )
    stored = only_poll(poll)

    poll.run(
        FakeMessage(
            f"!poll vote {stored.id} {form}",
            invokername="Alice",
            invokerid=3,
            invokeruid="uid-3",
        )
    )

    updated = poll.store.get(stored.id)
    assert updated is not None
    assert updated.votes == {"uid-3": [0, 2]}


def test_numeric_option_tokens_are_rejected(tmp_path):
    client = PollClient()
    client.users = [make_user(3, "Alice", "uid-3")]
    poll = make_poll(tmp_path, client)
    poll.run(
        FakeMessage(
            "!poll create Pick | A | B",
            invokername="Creator",
            invokerid=2,
            invokeruid="creator-uid",
        )
    )
    stored = only_poll(poll)

    poll.run(
        FakeMessage(
            f"!poll vote {stored.id} 12",
            invokername="Alice",
            invokerid=3,
            invokeruid="uid-3",
        )
    )

    updated = poll.store.get(stored.id)
    assert updated is not None
    assert updated.votes == {}
    assert "letters" in client.sent[-1][1]


def test_invalid_unknown_and_closed_polls_reply_privately(tmp_path):
    client = PollClient()
    poll = make_poll(tmp_path, client)

    poll.run(FakeMessage("!poll vote zzz a", invokerid=7, invokeruid="uid-7"))
    assert client.sent[-1][0] == 7
    assert "Poll not found." in client.sent[-1][1]

    created = poll.store.create(
        question="Lunch?",
        options=["Pizza", "Sushi"],
        creator_uid="creator-uid",
        creator_name="Creator",
        scope="server",
        now=NOW,
    )
    poll.store.close(created.id, now=NOW)
    poll.run(FakeMessage(f"!poll vote {created.id} a", invokerid=7, invokeruid="uid-7"))
    assert client.sent[-1][0] == 7
    assert "Poll has ended." in client.sent[-1][1]

    poll.run(FakeMessage("!poll results zzz", invokerid=7, invokeruid="uid-7"))
    assert client.sent[-1][0] == 7
    assert "Poll not found." in client.sent[-1][1]


def test_second_vote_replaces_first_and_keeps_one_voter(tmp_path):
    client = PollClient()
    client.users = [make_user(3, "Alice", "uid-3")]
    poll = make_poll(tmp_path, client)
    poll.run(
        FakeMessage(
            "!poll create Lunch? | Pizza | Sushi",
            invokername="Creator",
            invokerid=2,
            invokeruid="creator-uid",
        )
    )
    stored = only_poll(poll)

    poll.run(FakeMessage(f"!poll vote {stored.id} a", invokerid=3, invokeruid="uid-3"))
    poll.run(FakeMessage(f"!poll vote {stored.id} b", invokerid=3, invokeruid="uid-3"))

    updated = poll.store.get(stored.id)
    assert updated is not None
    assert updated.total_voters() == 1
    assert updated.counts() == [0, 1]
    assert updated.votes == {"uid-3": [1]}


def test_channel_poll_rejects_outsider(tmp_path):
    client = PollClient()
    client.user_infos[20] = UserInfo(clid=20, cid=20, client_unique_identifier="uid-20")
    poll = make_poll(tmp_path, client)
    created = poll.store.create(
        question="Lunch?",
        options=["Pizza", "Sushi"],
        creator_uid="creator-uid",
        creator_name="Creator",
        scope="channel",
        channel_id=10,
        channel_name="Lobby",
        now=NOW,
    )

    poll.run(
        FakeMessage(
            f"!poll vote {created.id} a",
            invokerid=20,
            invokeruid="uid-20",
        )
    )

    assert created.votes == {}
    assert "only" in client.sent[-1][1]
    assert "#Lobby" in client.sent[-1][1]


def test_anonymous_poll_hides_voter_details(tmp_path):
    client = PollClient()
    client.users = [
        make_user(2, "Creator", "creator-uid"),
        make_user(3, "Alice", "uid-3"),
    ]
    poll = make_poll(tmp_path, client)
    poll.run(
        FakeMessage(
            "!poll create Secret? | A | B --anonymous",
            invokername="Creator",
            invokerid=2,
            invokeruid="creator-uid",
        )
    )
    stored = only_poll(poll)
    assert "Anonymous poll." in client.server_sent[0]
    assert "Anonymous poll." in client.sent[-1][1]
    client.sent.clear()

    poll.run(
        FakeMessage(
            f"!poll vote {stored.id} a",
            invokername="Alice",
            invokerid=3,
            invokeruid="uid-3",
        )
    )
    assert "Anonymous vote received" in messages_to(client, 2)[0]
    assert "Alice" not in messages_to(client, 2)[0]

    poll.run(FakeMessage(f"!poll results {stored.id}", invokerid=4, invokeruid="uid-4"))
    results = client.sent[-1][1]
    assert "Alice" not in results
    assert "uid-3" not in results

    data = json.loads((tmp_path / f"{stored.id}.json").read_text())
    assert data["voter_names"] == {}
    assert data["votes"]
    for key in data["votes"]:
        assert len(key) == 64
        assert set(key) <= set("0123456789abcdef")


def test_results_include_counts_percentages_total_and_winner(tmp_path):
    client = PollClient()
    poll = make_poll(tmp_path, client)
    created = poll.store.create(
        question="Lunch?",
        options=["Pizza", "Sushi"],
        creator_uid="creator-uid",
        creator_name="Creator",
        scope="server",
        now=NOW,
    )
    poll.store.vote(created.id, "u1", [0], voter_name="Alice", now=NOW)
    poll.store.vote(created.id, "u2", [0], voter_name="Bob", now=NOW)
    poll.store.vote(created.id, "u3", [1], voter_name="Cara", now=NOW)
    poll.store.close(created.id, now=NOW)

    poll.run(FakeMessage(f"!poll results {created.id}", invokerid=9, invokeruid="uid-9"))

    results = client.sent[-1][1]
    assert "Status: ended" in results
    assert "Pizza: 2 (66.67%)" in results
    assert "Sushi: 1 (33.33%)" in results
    assert "Total voters: 3" in results
    assert "Winner: a) Pizza" in results


def test_list_shows_server_and_current_channel_only(tmp_path):
    client = PollClient()
    client.user_infos[2] = UserInfo(clid=2, cid=10, client_unique_identifier="uid-2")
    poll = make_poll(tmp_path, client)
    server = poll.store.create(
        question="Server question",
        options=["A", "B"],
        creator_uid="creator-uid",
        creator_name="Creator",
        scope="server",
        now=NOW,
    )
    channel = poll.store.create(
        question="Channel question",
        options=["A", "B"],
        creator_uid="creator-uid",
        creator_name="Creator",
        scope="channel",
        channel_id=10,
        channel_name="Lobby",
        now=NOW + timedelta(seconds=1),
    )
    other = poll.store.create(
        question="Other channel",
        options=["A", "B"],
        creator_uid="creator-uid",
        creator_name="Creator",
        scope="channel",
        channel_id=20,
        channel_name="Elsewhere",
        now=NOW + timedelta(seconds=2),
    )
    closed = poll.store.create(
        question="Closed question",
        options=["A", "B"],
        creator_uid="creator-uid",
        creator_name="Creator",
        scope="server",
        now=NOW + timedelta(seconds=3),
    )
    poll.store.close(closed.id, now=NOW + timedelta(seconds=4))

    poll.run(FakeMessage("!poll list", invokerid=2, invokeruid="uid-2"))
    listed = client.sent[-1][1]
    assert "Server" in listed
    assert "#Lobby" in listed
    assert server.id in listed
    assert channel.id in listed
    assert other.id not in listed
    assert closed.id not in listed

    poll.run(FakeMessage("!poll list all", invokerid=2, invokeruid="uid-2"))
    listed_all = client.sent[-1][1]
    assert closed.id in listed_all
    assert "(ended)" in listed_all


def test_end_is_creator_only_and_notifies_scope_creator_and_voters(tmp_path):
    client = PollClient()
    client.users = [
        make_user(2, "Creator", "creator-uid"),
        make_user(3, "Alice", "uid-3"),
    ]
    poll = make_poll(tmp_path, client)
    created = poll.store.create(
        question="Lunch?",
        options=["Pizza", "Sushi"],
        creator_uid="creator-uid",
        creator_name="Creator",
        scope="server",
        now=NOW,
    )
    poll.store.vote(created.id, "uid-3", [0], voter_name="Alice", now=NOW)

    poll.run(FakeMessage(f"!poll end {created.id}", invokerid=3, invokeruid="uid-3"))
    assert "Only the poll creator" in client.sent[-1][1]
    assert created.closed is False

    client.sent.clear()
    poll.run(FakeMessage(f"!poll end {created.id}", invokerid=2, invokeruid="creator-uid"))

    assert created.closed is True
    assert client.server_sent
    assert "Status: ended" in client.server_sent[-1]
    assert {target for target, _ in client.sent} == {2, 3}


def test_delete_is_creator_only_and_requires_ended(tmp_path):
    client = PollClient()
    poll = make_poll(tmp_path, client)
    created = poll.store.create(
        question="Lunch?",
        options=["Pizza", "Sushi"],
        creator_uid="creator-uid",
        creator_name="Creator",
        scope="server",
        now=NOW,
    )
    path = tmp_path / f"{created.id}.json"

    poll.run(FakeMessage(f"!poll delete {created.id}", invokerid=3, invokeruid="uid-3"))
    assert "Only the poll creator" in client.sent[-1][1]
    assert path.exists()

    poll.run(FakeMessage(f"!poll delete {created.id}", invokerid=2, invokeruid="creator-uid"))
    assert "End the poll before deleting it." in client.sent[-1][1]
    assert path.exists()

    poll.store.close(created.id, now=NOW)
    client.sent.clear()
    poll.run(FakeMessage(f"!poll delete {created.id}", invokerid=2, invokeruid="creator-uid"))

    assert not path.exists()
    assert poll.store.get(created.id) is None
    assert "Deleted poll" in client.sent[-1][1]


def test_tick_closes_expired_poll_and_notifies(tmp_path, monkeypatch):
    client = PollClient()
    client.users = [
        make_user(2, "Creator", "creator-uid"),
        make_user(3, "Alice", "uid-3"),
    ]
    poll = make_poll(tmp_path, client)
    poll._last_prefix = "!"
    created = poll.store.create(
        question="Lunch?",
        options=["Pizza", "Sushi"],
        creator_uid="creator-uid",
        creator_name="Creator",
        scope="server",
        expires_at=NOW,
        now=NOW - timedelta(minutes=5),
    )
    poll.store.vote(created.id, "uid-3", [0], voter_name="Alice", now=NOW - timedelta(minutes=4))
    monkeypatch.setattr(poll_module, "utcnow", lambda: NOW + timedelta(seconds=1))

    poll.tick()

    assert created.closed is True
    assert client.server_sent
    assert "Status: ended" in client.server_sent[-1]
    assert "Results: !poll results" in client.server_sent[-1]
    assert {target for target, _ in client.sent} == {2, 3}


def test_tick_swallows_per_poll_errors(tmp_path, monkeypatch):
    client = PollClient()
    poll = make_poll(tmp_path, client)
    created = poll.store.create(
        question="Lunch?",
        options=["Pizza", "Sushi"],
        creator_uid="creator-uid",
        creator_name="Creator",
        scope="server",
        expires_at=NOW,
        now=NOW - timedelta(minutes=5),
    )
    monkeypatch.setattr(poll_module, "utcnow", lambda: NOW + timedelta(seconds=1))

    def fail(message):
        raise RuntimeError("send failed")

    client.send_server_message = fail

    poll.tick()

    assert created.closed is True


def test_full_word_and_shortcut_subcommands_match(tmp_path):
    client = PollClient()
    client.users = [make_user(2, "Creator", "creator-uid")]
    poll = make_poll(tmp_path, client)

    for subcommand in ("create", "c"):
        poll.run(
            FakeMessage(
                f"!poll {subcommand} Question {subcommand}? | A | B",
                invokername="Creator",
                invokerid=2,
                invokeruid="creator-uid",
            )
        )
    polls = poll.store.list_polls(include_closed=True)
    assert len(polls) == 2
    first, second = polls

    for subcommand, target in (("vote", first), ("v", second)):
        poll.run(
            FakeMessage(
                f"!poll {subcommand} {target.id} a",
                invokername="Creator",
                invokerid=2,
                invokeruid="creator-uid",
            )
        )
    assert all(item.total_voters() == 1 for item in poll.store.list_polls(include_closed=True))

    for subcommand, target in (("results", first), ("r", second)):
        poll.run(FakeMessage(f"!poll {subcommand} {target.id}", invokerid=2, invokeruid="creator-uid"))
        assert target.id in client.sent[-1][1]

    for subcommand in ("list", "l"):
        poll.run(FakeMessage(f"!poll {subcommand}", invokerid=2, invokeruid="creator-uid"))
        assert first.id in client.sent[-1][1]
        assert second.id in client.sent[-1][1]

    for subcommand in ("help", "h"):
        poll.run(FakeMessage(f"!poll {subcommand}", invokerid=2, invokeruid="creator-uid"))
        assert "create" in client.sent[-1][1]
        assert "vote" in client.sent[-1][1]

    for subcommand, target in (("end", first), ("e", second)):
        poll.run(FakeMessage(f"!poll {subcommand} {target.id}", invokerid=2, invokeruid="creator-uid"))
        assert target.closed is True

    for subcommand, target in (("delete", first), ("d", second)):
        poll.run(FakeMessage(f"!poll {subcommand} {target.id}", invokerid=2, invokeruid="creator-uid"))
        assert poll.store.get(target.id) is None


def test_help_lists_subcommands_and_flags(tmp_path):
    client = PollClient()
    poll = make_poll(tmp_path, client)

    poll.run(FakeMessage("!poll help", invokerid=7, invokeruid="uid-7"))

    text = client.sent[-1][1]
    for word in ("create", "vote", "results", "list", "end", "delete", "help"):
        assert word in text
    for flag in ("--duration", "--anonymous", "--multi", "--server", "--channel"):
        assert flag in text


def test_unknown_subcommand_sends_usage_privately(tmp_path):
    client = PollClient()
    poll = make_poll(tmp_path, client)

    poll.run(FakeMessage("!poll nope", invokerid=7, invokeruid="uid-7"))

    assert client.sent[-1][0] == 7
    assert "Poll commands:" in client.sent[-1][1]


def test_notify_query_clients_can_be_enabled(tmp_path):
    client = PollClient()
    client.users = [
        make_user(1, "Bot", "bot-uid"),
        make_user(2, "Creator", "creator-uid"),
        make_user(3, "Alice", "uid-3"),
        make_user(4, "Query", "query-uid", client_type=1),
    ]
    poll = make_poll(tmp_path, client, notify_query_clients=True)

    poll.run(
        FakeMessage(
            "!poll create Lunch? | Pizza | Sushi",
            invokername="Creator",
            invokerid=2,
            invokeruid="creator-uid",
        )
    )

    announcement = client.server_sent[0]
    assert messages_to(client, 4) == [announcement]
    assert messages_to(client, 3) == [announcement]
    assert announcement not in messages_to(client, 2)
    assert messages_to(client, 1) == []


def test_notify_users_false_skips_fanout(tmp_path):
    client = PollClient()
    client.users = [
        make_user(2, "Creator", "creator-uid"),
        make_user(3, "Alice", "uid-3"),
    ]
    poll = make_poll(tmp_path, client, notify_users=False)

    poll.run(
        FakeMessage(
            "!poll create Lunch? | Pizza | Sushi",
            invokername="Creator",
            invokerid=2,
            invokeruid="creator-uid",
        )
    )

    assert messages_to(client, 3) == []
    assert client.server_sent
    assert any("Created server poll" in text for text in messages_to(client, 2))


def test_channel_fanout_resolves_missing_cid(tmp_path):
    client = PollClient()
    client.channels = [Channel(cid=10, channel_name="Lobby")]
    client.users = [
        make_user(2, "Creator", "creator-uid", cid=10),
        make_user(3, "Resolved", "uid-3", cid=None),
        make_user(4, "Elsewhere", "uid-4", cid=None),
    ]
    client.user_infos[3] = UserInfo(clid=3, cid=10, client_unique_identifier="uid-3")
    client.user_infos[4] = UserInfo(clid=4, cid=20, client_unique_identifier="uid-4")
    poll = make_poll(tmp_path, client)

    poll.run(
        FakeMessage(
            "!poll create Lunch? | Pizza | Sushi",
            invokername="Creator",
            invokerid=2,
            invokeruid="creator-uid",
            targetmode=TargetMode.CHANNEL.value,
            target=10,
        )
    )

    announcement = client.messages_sent[0][2]
    assert messages_to(client, 3) == [announcement]
    assert messages_to(client, 4) == []
