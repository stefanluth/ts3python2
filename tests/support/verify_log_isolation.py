#!/usr/bin/env python3
"""Verify that simulated xdist workers write to isolated log directories."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONFTEST = ROOT / "tests" / "conftest.py"
SUCCESS_MARKER = "parallel log isolation verified"
WORKERS = ("gw0", "gw1")

CHILD_SCRIPT = """
import logging
import runpy

runpy.run_path(%r)

from ts3client.utils.logger import create_logger, log_path

path = log_path("main.log")
logger = create_logger("worker", path)
logger.info("worker writing to %%s", path)
logging.shutdown()
""" % str(CONFTEST)


def worker_environment(worker: str) -> dict[str, str]:
    env = os.environ.copy()
    for name in ("TS3_LOG_DIR", "PYTEST_XDIST_WORKER", "TS3_INTEGRATION"):
        env.pop(name, None)
    env["PYTHONPATH"] = str(ROOT)
    env["TS3_INTEGRATION"] = "1"
    env["PYTEST_XDIST_WORKER"] = worker
    return env


def start_worker(worker: str, cwd: Path) -> subprocess.Popen[str]:
    return subprocess.Popen(
        [sys.executable, "-c", CHILD_SCRIPT],
        cwd=cwd,
        env=worker_environment(worker),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="ts3-log-isolation-") as directory:
        workdir = Path(directory)

        processes = {worker: start_worker(worker, workdir) for worker in WORKERS}
        results = {worker: process.communicate() for worker, process in processes.items()}

        problems = []

        for worker, process in processes.items():
            stdout, stderr = results[worker]
            if process.returncode != 0:
                problems.append(
                    f"worker {worker} exited with code {process.returncode}\nstdout:\n{stdout}\nstderr:\n{stderr}"
                )

        for worker in WORKERS:
            path = workdir / "logs" / worker / "main.log"
            if not path.is_file():
                problems.append(f"missing {path.relative_to(workdir)}")
            elif path.stat().st_size == 0:
                problems.append(f"empty {path.relative_to(workdir)}")

        shared = workdir / "logs" / "main.log"
        if shared.exists():
            problems.append("unexpected shared log logs/main.log")

        if problems:
            print("parallel log isolation verification failed:", file=sys.stderr)
            for problem in problems:
                print(f"- {problem}", file=sys.stderr)
            return 1

    print(SUCCESS_MARKER)
    return 0


if __name__ == "__main__":
    sys.exit(main())
