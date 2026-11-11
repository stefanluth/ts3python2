#!/usr/bin/env python3
"""Verify that the parallel integration run is faster and properly isolated."""

from __future__ import annotations

import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SUCCESS_MARKER = "parallel speedup verified"
WORKER_LOG_PATTERN = "logs/gw*/main.log"
SHARED_LOG = ROOT / "logs" / "main.log"
MIN_WORKER_LOGS = 4
MAX_FAILURE_OUTPUT = 4000


class VerificationError(Exception):
    """Raised when the parallel run fails a verification requirement."""


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
        raise VerificationError("docker executable not found; cannot verify parallel speedup")

    completed = _docker("ps")
    if completed.returncode != 0:
        detail = completed.stderr.strip() or f"exit code {completed.returncode}"
        raise VerificationError(f"docker is not available: {detail}")


def _failure_output(completed: subprocess.CompletedProcess[str]) -> str:
    combined = f"{completed.stdout or ''}{completed.stderr or ''}".strip()
    if not combined:
        return "<no output>"
    return combined[-MAX_FAILURE_OUTPUT:]


def run_make(jobs: int) -> float:
    command = ["make", "test-integration", f"JOBS={jobs}"]
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


def shared_log_mtime() -> float | None:
    try:
        return SHARED_LOG.stat().st_mtime
    except FileNotFoundError:
        return None
    except OSError as error:
        raise VerificationError(f"could not stat logs/main.log: {error}") from error


def check_no_leftover_containers() -> None:
    completed = _docker("ps", "--filter", "name=ts3-test-", "--format", "{{.Names}}")
    if completed.returncode != 0:
        detail = completed.stderr.strip() or f"exit code {completed.returncode}"
        raise VerificationError(f"could not list leftover containers: {detail}")

    leftover = sorted(line.strip() for line in completed.stdout.splitlines() if line.strip())
    if leftover:
        raise VerificationError(f"leftover ts3-test- containers: {', '.join(leftover)}")


def check_worker_logs(parallel_start: float) -> None:
    fresh_logs = []
    for path in ROOT.glob(WORKER_LOG_PATTERN):
        try:
            modified = path.stat().st_mtime
        except OSError as error:
            raise VerificationError(f"could not stat {path.relative_to(ROOT)}: {error}") from error
        if modified >= parallel_start:
            fresh_logs.append(path)

    if len(fresh_logs) < MIN_WORKER_LOGS:
        found = ", ".join(str(path.relative_to(ROOT)) for path in sorted(fresh_logs)) or "none"
        raise VerificationError(
            f"expected at least {MIN_WORKER_LOGS} worker logs matching "
            f"{WORKER_LOG_PATTERN} to be modified after the parallel run started; "
            f"found {len(fresh_logs)}: {found}"
        )


def check_shared_log_untouched(shared_before: float | None) -> None:
    shared_after = shared_log_mtime()
    if shared_before is None:
        if shared_after is not None:
            raise VerificationError("logs/main.log was created during the parallel run")
        return
    if shared_after is None:
        raise VerificationError("logs/main.log was deleted during the parallel run")
    if shared_after != shared_before:
        raise VerificationError("logs/main.log was modified during the parallel run")


def main() -> int:
    try:
        require_docker()

        sequential = run_make(1)

        shared_before = shared_log_mtime()
        parallel_start = time.time()
        parallel = run_make(4)

        check_no_leftover_containers()
        check_worker_logs(parallel_start)
        check_shared_log_untouched(shared_before)
    except VerificationError as error:
        print(f"parallel speedup verification failed: {error}", file=sys.stderr)
        return 1

    if parallel >= sequential:
        print(
            f"parallel speedup verification failed: parallel run ({parallel:.2f}s) "
            f"was not faster than sequential run ({sequential:.2f}s)",
            file=sys.stderr,
        )
        return 1

    print(f"sequential={sequential:.2f}s parallel={parallel:.2f}s")
    print(SUCCESS_MARKER)
    return 0


if __name__ == "__main__":
    sys.exit(main())
