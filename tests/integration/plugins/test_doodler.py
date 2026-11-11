from datetime import date, timedelta

import pytest

from tests.support.integration import (
    restore_server_banner,
    running_plugins,
    server_banner,
    today_ts3,
    ts3_date,
    unique_name,
    wait_until,
)

pytestmark = pytest.mark.integration


def wait_for_banner(used_query, expected_url):
    wait_until(
        lambda: server_banner(used_query)["url"] == expected_url,
        timeout=15,
        message=f"server banner was not set to {expected_url!r}",
    )
    assert server_banner(used_query)["mode"] == 2


def test_doodler_applies_a_doodle_for_today(fresh_client, used_query):
    original = server_banner(used_query)
    default_url = f"https://example.com/{unique_name('default')}.png"
    doodle_url = f"https://example.com/{unique_name('doodle')}.png"
    try:
        with running_plugins(
            fresh_client,
            {
                "Doodler": {
                    "default": default_url,
                    "doodles": [{"date": today_ts3(), "url": doodle_url}],
                }
            },
        ):
            wait_for_banner(used_query, doodle_url)
    finally:
        restore_server_banner(used_query, original)


def test_doodler_applies_a_doodle_range_that_contains_today(fresh_client, used_query):
    original = server_banner(used_query)
    default_url = f"https://example.com/{unique_name('default')}.png"
    doodle_url = f"https://example.com/{unique_name('range')}.png"
    start = date.today() - timedelta(days=1)
    end = date.today() + timedelta(days=1)
    try:
        with running_plugins(
            fresh_client,
            {
                "Doodler": {
                    "default": default_url,
                    "doodles": [
                        {
                            "startDate": ts3_date(start),
                            "endDate": ts3_date(end),
                            "url": doodle_url,
                        }
                    ],
                }
            },
        ):
            wait_for_banner(used_query, doodle_url)
    finally:
        restore_server_banner(used_query, original)


def test_doodler_falls_back_to_the_default_banner(fresh_client, used_query):
    original = server_banner(used_query)
    default_url = f"https://example.com/{unique_name('default')}.png"
    doodle_url = f"https://example.com/{unique_name('other-day')}.png"
    other_day = date.today() + timedelta(days=30)
    try:
        with running_plugins(
            fresh_client,
            {
                "Doodler": {
                    "default": default_url,
                    "doodles": [{"date": ts3_date(other_day), "url": doodle_url}],
                }
            },
        ):
            wait_for_banner(used_query, default_url)
    finally:
        restore_server_banner(used_query, original)
