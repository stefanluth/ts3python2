"""Tests for the per-worker log directory bootstrap in tests/conftest.py."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
CONFTEST = ROOT / "tests" / "conftest.py"

BOOTSTRAP_SCRIPT = """
import json
import os
import runpy

runpy.run_path(%r)
print(json.dumps({"TS3_LOG_DIR": os.environ.get("TS3_LOG_DIR")}))
""" % str(CONFTEST)

LOG_PATH_SCRIPT = """
import json
import runpy

runpy.run_path(%r)

from ts3client.utils.logger import log_path

print(json.dumps({"log_path": log_path("main.log")}))
""" % str(CONFTEST)


def _environment(**overrides: str) -> dict[str, str]:
    env = os.environ.copy()
    for name in ("TS3_INTEGRATION", "PYTEST_XDIST_WORKER", "TS3_LOG_DIR"):
        env.pop(name, None)
    env["PYTHONPATH"] = str(ROOT)
    env.update(overrides)
    return env


def _run_bootstrap(script: str, *, env: dict[str, str], cwd: Path) -> dict[str, Any]:
    completed = subprocess.run(
        [sys.executable, "-c", script],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    if completed.returncode != 0:
        raise AssertionError(
            f"bootstrap subprocess failed with exit code {completed.returncode}\n"
            f"stdout:\n{completed.stdout}\nstderr:\n{completed.stderr}"
        )

    lines = completed.stdout.strip().splitlines()
    if not lines:
        raise AssertionError("bootstrap subprocess produced no output")

    return json.loads(lines[-1])


def test_integration_worker_gets_own_log_dir(tmp_path):
    result = _run_bootstrap(
        BOOTSTRAP_SCRIPT,
        env=_environment(TS3_INTEGRATION="1", PYTEST_XDIST_WORKER="gw2"),
        cwd=tmp_path,
    )

    assert result["TS3_LOG_DIR"] == os.path.join("logs", "gw2")


def test_integration_without_worker_leaves_log_dir_unset(tmp_path):
    result = _run_bootstrap(
        BOOTSTRAP_SCRIPT,
        env=_environment(TS3_INTEGRATION="1"),
        cwd=tmp_path,
    )

    assert result["TS3_LOG_DIR"] is None


def test_non_integration_worker_leaves_log_dir_unset(tmp_path):
    result = _run_bootstrap(
        BOOTSTRAP_SCRIPT,
        env=_environment(PYTEST_XDIST_WORKER="gw2"),
        cwd=tmp_path,
    )

    assert result["TS3_LOG_DIR"] is None


def test_explicit_log_dir_is_preserved(tmp_path):
    result = _run_bootstrap(
        BOOTSTRAP_SCRIPT,
        env=_environment(
            TS3_INTEGRATION="1",
            PYTEST_XDIST_WORKER="gw2",
            TS3_LOG_DIR=os.path.join("custom", "logs"),
        ),
        cwd=tmp_path,
    )

    assert result["TS3_LOG_DIR"] == os.path.join("custom", "logs")


def test_logger_uses_bootstrapped_log_dir(tmp_path):
    result = _run_bootstrap(
        LOG_PATH_SCRIPT,
        env=_environment(TS3_INTEGRATION="1", PYTEST_XDIST_WORKER="gw2"),
        cwd=tmp_path,
    )

    assert result["log_path"] == os.path.join("logs", "gw2", "main.log")
