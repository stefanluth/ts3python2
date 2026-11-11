from datetime import datetime as real_datetime

import plugins.plugins.doodler as doodler_module
from plugins.plugins.doodler import Doodler, date_range
from tests.support.fakes import FakeClient, FakeLogger, FakeResponse, FakeStopEvent

TODAY = "25-12-2025"


class FixedDatetime(real_datetime):
    @classmethod
    def today(cls):
        return cls(2025, 12, 25, 12, 0)


def make_doodler(monkeypatch, client, stop):
    monkeypatch.setattr(doodler_module, "datetime", FixedDatetime)
    monkeypatch.setattr("plugins.plugin.create_logger", lambda *args, **kwargs: FakeLogger())
    return Doodler(client, stop)


def make_client(current_banner):
    client = FakeClient()
    client.query.commands.responses["serverinfo"] = FakeResponse(
        data={0: {"virtualserver_hostbanner_gfx_url": current_banner}}
    )
    return client


def test_date_range_is_inclusive():
    assert list(date_range("01-01-2025", "03-01-2025")) == ["01-01-2025", "02-01-2025", "03-01-2025"]
    assert list(date_range("01-01-2025", "01-01-2025")) == ["01-01-2025"]
    assert list(date_range("03-01-2025", "01-01-2025")) == []


def test_doodler_sets_the_banner_for_a_matching_date(monkeypatch):
    doodle_url = "https://example.com/christmas.png"
    client = make_client("https://example.com/default.png")
    plugin = make_doodler(monkeypatch, client, FakeStopEvent(stop_after_waits=1))

    plugin.run(default="https://example.com/default.png", doodles=[{"date": TODAY, "url": doodle_url}])

    assert client.query.commands.called("serveredit") == [
        (
            "serveredit",
            (),
            {"virtualserver_hostbanner_gfx_url": doodle_url, "virtualserver_hostbanner_mode": 2},
        )
    ]


def test_doodler_sets_the_banner_inside_a_date_range(monkeypatch):
    doodle_url = "https://example.com/holiday.png"
    client = make_client("https://example.com/default.png")
    plugin = make_doodler(monkeypatch, client, FakeStopEvent(stop_after_waits=1))

    plugin.run(
        default="https://example.com/default.png",
        doodles=[{"startDate": "24-12-2025", "endDate": "26-12-2025", "url": doodle_url}],
    )

    assert client.query.commands.called("serveredit")[0][2]["virtualserver_hostbanner_gfx_url"] == doodle_url


def test_doodler_falls_back_to_default_without_an_edit_when_it_matches(monkeypatch):
    default_url = "https://example.com/default.png"
    client = make_client(default_url)
    plugin = make_doodler(monkeypatch, client, FakeStopEvent(stop_after_waits=1))

    plugin.run(default=default_url, doodles=[{"date": "01-01-2026", "url": "https://example.com/new-year.png"}])

    assert client.query.commands.called("serveredit") == []


class FlakyServerInfoClient(FakeClient):
    def __init__(self):
        super().__init__()
        self.calls = 0

        def serverinfo():
            self.calls += 1
            if self.calls == 1:
                raise RuntimeError("boom")
            return FakeResponse(data={0: {"virtualserver_hostbanner_gfx_url": "https://example.com/default.png"}})

        self.query.commands.responses["serverinfo"] = serverinfo


def test_doodler_survives_a_failed_check(monkeypatch):
    client = FlakyServerInfoClient()
    plugin = make_doodler(monkeypatch, client, FakeStopEvent(stop_after_waits=2))

    plugin.run(default="https://example.com/default.png", doodles=[])

    assert client.calls == 2
