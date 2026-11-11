#!/usr/bin/env python3
"""Verify that repeated parallel integration runs stay stable and clean."""

from __future__ import annotations

import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SUCCESS_MARKER = "parallel stability verified"
JOBS = 4
RUNS = 3
MAX_FAILURE_OUTPUT = 4000


class VerificationError(Exception):
    """Raised when a stability run fails a verification requirement."""


def _docker(*arguments: str) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            ["docker", *arguments],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as error:
        raise VerificationError(f"could not run docker: {error}") from error


def require_docker() -> None:
    if shutil.which("docker") is None:
        raise VerificationError("docker executable not found; cannot verify parallel stability")

    completed = _docker("ps")
    if completed.returncode != 0:
        detail = completed.stderr.strip() or f"exit code {completed.returncode}"
        raise VerificationError(f"docker is not available: {detail}")


def _failure_output(completed: subprocess.CompletedProcess[str]) -> str:
    combined = f"{completed.stdout or ''}{completed.stderr or ''}".strip()
    if not combined:
        return "<no output>"
    return combined[-MAX_FAILURE_OUTPUT:]


def run_make() -> float:
    command = ["make", "test-integration", f"JOBS={JOBS}"]
    started = time.monotonic()
    try:
        completed = subprocess.run(
            command,
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as error:
        raise VerificationError(f"could not run `{' '.join(command)}`: {error}") from error
    elapsed = time.monotonic() - started
    if completed.returncode != 0:
        raise VerificationError(
            f"`{' '.join(command)}` failed with exit code {completed.returncode}:\n{_failure_output(completed)}"
        )
    return elapsed


def check_no_leftover_containers() -> None:
    completed = _docker("ps", "--filter", "name=ts3-test-", "--format", "{{.Names}}")
    if completed.returncode != 0:
        detail = completed.stderr.strip() or f"exit code {completed.returncode}"
        raise VerificationError(f"could not list leftover containers: {detail}")

    leftover = sorted(line.strip() for line in completed.stdout.splitlines() if line.strip())
    if leftover:
        raise VerificationError(f"leftover ts3-test- containers: {', '.join(leftover)}")


def main() -> int:
    durations = []
    try:
        require_docker()

        for index in range(1, RUNS + 1):
            durations.append(run_make())
            check_no_leftover_containers()
            print(f"run {index}/{RUNS}: {durations[-1]:.2f}s")
    except VerificationError as error:
        print(f"parallel stability verification failed: {error}", file=sys.stderr)
        return 1

    print(f"runs={RUNS} durations=" + ",".join(f"{duration:.2f}s" for duration in durations))
    print(SUCCESS_MARKER)
    return 0


if __name__ == "__main__":
    sys.exit(main())
