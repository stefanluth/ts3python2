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


@pytest.mark.bug
def test_weather_request_is_safe_and_replied_to(monkeypatch):
    captured = []
    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen(captured))
    weather = make_weather()

    weather.run(FakeMessage("!weather New York", invokerid=7))

    assert weather.client.sent == [
        (
            7,
            "Current weather for New York: Sunny, 20°C, feels like 19°C, humidity 50%, wind 10 kph, N.",
        )
    ]

    url, timeout = captured[0]
    assert url.startswith("https://")
    assert " " not in url
    assert "New%20York" in url or "New+York" in url
    assert timeout is not None
    assert timeout > 0


def test_prompts_for_a_location_without_calling_the_api(monkeypatch):
    captured = []
    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen(captured))
    weather = make_weather()

    weather.run(FakeMessage("!weather", invokerid=7))

    assert weather.client.sent == [(7, "Please provide a location.")]
    assert captured == []


@pytest.mark.parametrize(
    ("error", "expected_reply"),
    [
        (urllib.error.HTTPError("https://example.com", 404, "Not Found", EmailMessage(), None), "Location not found."),
        pytest.param(urllib.error.URLError("network down"), "Weather service unavailable.", marks=pytest.mark.bug),
    ],
    ids=["http-error", "network-error"],
)
def test_network_failure_replies_instead_of_crashing(monkeypatch, error, expected_reply):
    def fail(url, timeout=None):
        raise error

    monkeypatch.setattr("urllib.request.urlopen", fail)
    weather = make_weather()

    weather.run(FakeMessage("!weather Atlantis", invokerid=7))

    assert weather.client.sent == [(7, expected_reply)]


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
