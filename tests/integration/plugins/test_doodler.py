from datetime import date, timedelta

import pytest

from tests.support.integration import (
    restore_server_banner,
    running_plugins,
    server_banner,
    ts3_date,
    unique_name,
    wait_until,
)

pytestmark = pytest.mark.integration


@pytest.mark.parametrize(
    ("kind", "expected"),
    [
        ("date", "doodle"),
        ("range", "doodle"),
        ("fallback", "default"),
    ],
)
def test_doodler_selects_the_banner_for_today(fresh_client, used_query, kind, expected):
    original = server_banner(used_query)
    default_url = f"https://example.com/{unique_name('default')}.png"
    doodle_url = f"https://example.com/{unique_name('doodle')}.png"
    try:
        with running_plugins(fresh_client, {"Doodler": doodle_config(kind, default_url, doodle_url)}):
            wait_for_banner(used_query, doodle_url if expected == "doodle" else default_url)
    finally:
        restore_server_banner(used_query, original)


def wait_for_banner(used_query, expected_url):
    wait_until(
        lambda: server_banner(used_query)["url"] == expected_url,
        timeout=15,
        message=f"server banner was not set to {expected_url!r}",
    )
    assert server_banner(used_query)["mode"] == 2


def doodle_config(kind, default_url, doodle_url):
    if kind == "date":
        return {"default": default_url, "doodles": [{"date": ts3_date(date.today()), "url": doodle_url}]}
    if kind == "range":
        start = date.today() - timedelta(days=1)
        end = date.today() + timedelta(days=1)
        return {
            "default": default_url,
            "doodles": [{"startDate": ts3_date(start), "endDate": ts3_date(end), "url": doodle_url}],
        }
    other_day = date.today() + timedelta(days=30)
    return {"default": default_url, "doodles": [{"date": ts3_date(other_day), "url": doodle_url}]}
