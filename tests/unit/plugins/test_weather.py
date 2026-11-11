import json
import urllib.error
from email.message import Message as EmailMessage
from typing import cast

import pytest

from plugins.commands.weather import Weather
from tests.support.fakes import FakeClient, FakeLogger, FakeMessage
from ts3client import TS3Client

PAYLOAD = {
    "location": {"name": "New York"},
    "current": {
        "condition": {"text": "Sunny"},
        "temp_c": 20,
        "feelslike_c": 19,
        "humidity": 50,
        "wind_kph": 10,
        "wind_dir": "N",
    },
}


class FakeHTTPResponse:
    def __init__(self, payload=None):
        self.payload = json.dumps(PAYLOAD if payload is None else payload).encode()

    def read(self):
        return self.payload

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def make_weather():
    weather = Weather(cast(TS3Client, FakeClient()), "weather", "KEY")
    weather.logger = FakeLogger()
    return weather


def fake_urlopen(captured):
    def call(url, timeout=None):
        captured.append((url, timeout))
        return FakeHTTPResponse()

    return call


def test_replies_with_the_current_weather(monkeypatch):
    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen([]))
    weather = make_weather()

    weather.run(FakeMessage("!weather New York", invokerid=7))

    assert weather.client.sent == [
        (
            7,
            "Current weather for New York: Sunny, 20°C, feels like 19°C, humidity 50%, wind 10 kph, N.",
        )
    ]


def test_prompts_for_a_location_without_calling_the_api(monkeypatch):
    captured = []
    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen(captured))
    weather = make_weather()

    weather.run(FakeMessage("!weather", invokerid=7))

    assert weather.client.sent == [(7, "Please provide a location.")]
    assert captured == []


def test_http_error_replies_location_not_found(monkeypatch):
    def fail(url, timeout=None):
        raise urllib.error.HTTPError(url, 404, "Not Found", EmailMessage(), None)

    monkeypatch.setattr("urllib.request.urlopen", fail)
    weather = make_weather()

    weather.run(FakeMessage("!weather Atlantis", invokerid=7))

    assert weather.client.sent == [(7, "Location not found.")]


@pytest.mark.bug
def test_uses_https(monkeypatch):
    captured = []
    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen(captured))
    weather = make_weather()

    weather.run(FakeMessage("!weather New York", invokerid=7))

    assert captured[0][0].startswith("https://")


@pytest.mark.bug
def test_url_encodes_location(monkeypatch):
    captured = []
    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen(captured))
    weather = make_weather()

    weather.run(FakeMessage("!weather New York", invokerid=7))

    assert " " not in captured[0][0]
    assert "New%20York" in captured[0][0] or "New+York" in captured[0][0]


@pytest.mark.bug
def test_passes_timeout(monkeypatch):
    captured = []
    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen(captured))
    weather = make_weather()

    weather.run(FakeMessage("!weather New York", invokerid=7))

    assert captured[0][1] is not None
    assert captured[0][1] > 0


@pytest.mark.bug
def test_network_error_replies_instead_of_crashing(monkeypatch):
    def fail(url, timeout=None):
        raise urllib.error.URLError("network down")

    monkeypatch.setattr("urllib.request.urlopen", fail)
    weather = make_weather()

    weather.run(FakeMessage("!weather New York", invokerid=7))

    assert weather.client.sent[0][1] != ""
