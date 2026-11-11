import os
import subprocess
from dataclasses import dataclass, field
from typing import Callable

DOCKER = "docker"
IMAGE_LABEL = "ts3python.test=1"
CONTAINER_HOST = "127.0.0.1"
QUERY_PORT = 10022

Runner = Callable[..., subprocess.CompletedProcess]


def worker_name() -> str:
    return os.getenv("PYTEST_XDIST_WORKER") or "local"


@dataclass(frozen=True)
class ManagedContainer:
    name: str
    host: str
    query_port: int
    _runner: Runner = field(default=subprocess.run, repr=False, compare=False)

    def stop(self) -> None:
        _remove(self.name, self._runner)

    def logs(self) -> str:
        try:
            result = self._runner(
                [DOCKER, "logs", self.name],
                capture_output=True,
                text=True,
                check=False,
            )
        except Exception:
            return ""
        return result.stdout or ""


def start_container(image: str, password: str, runner: Runner = subprocess.run) -> ManagedContainer:
    name = f"ts3-test-{os.getpid()}-{worker_name()}"
    command = [
        DOCKER,
        "run",
        "-d",
        "--name",
        name,
        "--label",
        IMAGE_LABEL,
        "-p",
        f"{CONTAINER_HOST}::{QUERY_PORT}",
        "-e",
        "TS3SERVER_LICENSE=accept",
        "-e",
        "TS3SERVER_QUERY_PROTOCOLS=ssh",
        "-e",
        f"TS3SERVER_QUERY_SSH_PORT={QUERY_PORT}",
        "-e",
        f"TS3SERVER_SERVERADMIN_PASSWORD={password}",
        image,
    ]
    try:
        result = runner(command, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            raise RuntimeError(f"failed to start container {name}: {_detail(result)}")
        query_port = _discover_query_port(name, runner)
    except Exception:
        _remove(name, runner)
        raise
    return ManagedContainer(name=name, host=CONTAINER_HOST, query_port=query_port, _runner=runner)


def _discover_query_port(name: str, runner: Runner) -> int:
    try:
        result = runner(
            [DOCKER, "port", name, f"{QUERY_PORT}/tcp"],
            capture_output=True,
            text=True,
            check=False,
        )
    except Exception as error:
        raise RuntimeError(f"could not discover host query port for container {name}: {error}") from error

    output = result.stdout or ""
    if result.returncode != 0 or not output.strip():
        raise RuntimeError(f"could not discover host query port for container {name}: {_detail(result)}")

    for line in output.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            return int(line.rsplit(":", 1)[1])
        except IndexError, ValueError:
            continue

    raise RuntimeError(f"could not parse host query port from {output.strip()!r} for container {name}")


def _remove(name: str, runner: Runner) -> None:
    try:
        runner([DOCKER, "rm", "-f", name], capture_output=True, text=True, check=False)
    except Exception:
        pass


def _detail(result: subprocess.CompletedProcess) -> str:
    return (result.stderr or result.stdout or "").strip() or "docker command failed"
