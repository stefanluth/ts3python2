from types import SimpleNamespace

import pytest

from tests.integration import conftest


@pytest.mark.parametrize(
    ("dist", "is_worker", "expected"),
    [
        ("no", False, False),
        ("load", False, True),
        ("load", True, False),
        ("no", True, False),
    ],
    ids=["in-process", "controller", "worker", "worker-without-distribution"],
)
def test_is_xdist_controller(dist, is_worker, expected):
    config = SimpleNamespace(option=SimpleNamespace(dist=dist))
    if is_worker:
        config.workerinput = {}

    assert conftest._is_xdist_controller(config) is expected


def test_integration_enabled_requires_environment(monkeypatch):
    config = SimpleNamespace(getvalue=lambda _: False)
    monkeypatch.setenv("TS3_INTEGRATION", "1")
    monkeypatch.delenv("QUERY_ADMIN_PASSWORD", raising=False)

    assert conftest._integration_enabled(config) is False

    monkeypatch.setenv("QUERY_ADMIN_PASSWORD", "secret")

    assert conftest._integration_enabled(config) is True


def test_integration_enabled_is_false_for_collection_only(monkeypatch):
    config = SimpleNamespace(getvalue=lambda _: True)
    monkeypatch.setenv("TS3_INTEGRATION", "1")
    monkeypatch.setenv("QUERY_ADMIN_PASSWORD", "secret")

    assert conftest._integration_enabled(config) is False
