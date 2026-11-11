import os
import re
import socket
import time

import paramiko


class SSHTransport:
    """SSH-backed byte stream transport for the ServerQuery interface."""

    _BUFFER_SIZE = 4096

    def __init__(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        timeout: float = 10,
        known_hosts: str = None,
        accept_all_keys: bool = False,
        use_system_host_keys: bool = True,
    ) -> None:
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.timeout = timeout
        self.known_hosts = known_hosts
        self.accept_all_keys = accept_all_keys
        self.use_system_host_keys = use_system_host_keys

        self._buffer = b""
        self._eof = False
        self._closed = False
        self._channel = None
        self._client = paramiko.SSHClient()

        if use_system_host_keys:
            self._client.load_system_host_keys()

        if known_hosts and os.path.exists(known_hosts):
            self._client.load_host_keys(known_hosts)

        if accept_all_keys:
            self._client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        else:
            self._client.set_missing_host_key_policy(paramiko.RejectPolicy())

        try:
            self._client.connect(
                hostname=host,
                port=port,
                username=username,
                password=password,
                look_for_keys=False,
                allow_agent=False,
                timeout=timeout,
                banner_timeout=timeout,
                auth_timeout=timeout,
            )

            transport = self._client.get_transport()
            if transport is None:
                raise paramiko.SSHException("SSH transport unavailable after connect")

            transport.set_keepalive(30)
            self._channel = self._client.invoke_shell("raw")
            self._channel.settimeout(timeout)

            if accept_all_keys and known_hosts:
                self._save_host_keys()
        except Exception:
            self.close()
            raise

    def _save_host_keys(self) -> None:
        directory = os.path.dirname(os.path.abspath(self.known_hosts))
        if directory:
            os.makedirs(directory, exist_ok=True)
        self._client.save_host_keys(self.known_hosts)

    def connected(self) -> bool:
        if self._closed or self._eof or self._channel is None:
            return False

        if self._channel.closed:
            return False

        transport = self._client.get_transport()
        return transport is not None and transport.is_active()

    def _recv(self, timeout: float):
        if self._closed or self._eof or self._channel is None:
            return b""

        previous_timeout = self._channel.gettimeout()
        self._channel.settimeout(timeout)
        try:
            return self._channel.recv(self._BUFFER_SIZE)
        except (socket.timeout, TimeoutError):
            return None
        except (EOFError, paramiko.SSHException):
            if self._channel is None or self._channel.closed:
                return b""
            raise
        finally:
            if self._channel is not None and not self._channel.closed:
                self._channel.settimeout(previous_timeout)

    def _remaining(self, deadline):
        if deadline is None:
            return None
        return deadline - time.monotonic()

    def _drain_buffer(self) -> bytes:
        data = self._buffer
        self._buffer = b""
        return data

    def read_until(self, delimiter: bytes, timeout: float = None) -> bytes:
        if timeout is None:
            timeout = self.timeout

        deadline = None if timeout is None else time.monotonic() + timeout

        while True:
            index = self._buffer.find(delimiter)
            if index >= 0:
                end = index + len(delimiter)
                data = self._buffer[:end]
                self._buffer = self._buffer[end:]
                return data

            remaining = self._remaining(deadline)
            if remaining is not None and remaining <= 0:
                return self._drain_buffer()

            data = self._recv(remaining)
            if data is None:
                continue

            if not data:
                self._eof = True
                if not self._buffer:
                    raise EOFError("SSH connection closed")
                return self._drain_buffer()

            self._buffer += data

    def _find_match(self, patterns):
        for index, pattern in enumerate(patterns):
            match = pattern.search(self._buffer)
            if match is not None:
                return index, match
        return None

    def expect(self, patterns, timeout: float = None):
        if hasattr(patterns, "search"):
            patterns = [patterns]

        compiled = [pattern if hasattr(pattern, "search") else re.compile(pattern) for pattern in patterns]

        if timeout is None:
            timeout = self.timeout

        deadline = None if timeout is None else time.monotonic() + timeout

        while True:
            found = self._find_match(compiled)
            if found is not None:
                index, match = found
                end = match.end()
                text = self._buffer[:end]
                self._buffer = self._buffer[end:]
                return index, match, text

            remaining = self._remaining(deadline)
            if remaining is not None and remaining <= 0:
                return -1, None, self._drain_buffer()

            data = self._recv(remaining)
            if data is None:
                continue

            if not data:
                self._eof = True
                if not self._buffer:
                    raise EOFError("SSH connection closed")
                return -1, None, self._drain_buffer()

            self._buffer += data

    def write(self, data: bytes) -> None:
        if self._closed or self._eof or self._channel is None:
            raise ConnectionError("SSH connection is closed")
        self._channel.sendall(data)

    def close(self) -> None:
        if self._closed:
            return

        self._closed = True
        self._buffer = b""

        channel = self._channel
        self._channel = None
        if channel is not None:
            try:
                channel.close()
            except Exception:
                pass

        client = self._client
        self._client = None
        if client is not None:
            try:
                client.close()
            except Exception:
                pass
