"""
Stands in for the ssh program in tests.

It takes the command line the SSH transport builds and does on this machine what
ssh would do on the remote one: run the command, or forward a port. A host whose
name starts with ``unreachable`` refuses the connection, and one starting with
``nopython3`` has no ``python3``, so the transport's fallbacks can be tested.
"""
from __future__ import annotations

import shlex
import socket
import subprocess  # nosec B404 - a test helper: it runs what the transport under test asked for
import sys
import threading

REFUSED = 255
NOT_FOUND = 127
_BUFFER = 65536
_PYTHONS = ("python3", "python")


def _pump(source: socket.socket, target: socket.socket) -> None:
    try:
        while True:
            data = source.recv(_BUFFER)
            if not data:
                break
            target.sendall(data)
    except OSError:
        pass
    finally:
        target.close()


def _relay(spec: str) -> int:
    """``127.0.0.1:local:host:remote``: accept on the local port and pass bytes both ways."""
    _bind, local_port, host, remote_port = spec.rsplit(":", 3)
    with socket.socket() as server:
        server.bind(("127.0.0.1", int(local_port)))
        server.listen()
        while True:
            client, _address = server.accept()
            upstream = socket.create_connection((host, int(remote_port)))
            threading.Thread(target=_pump, args=(client, upstream), daemon=True).start()
            threading.Thread(target=_pump, args=(upstream, client), daemon=True).start()


def main(arguments: list[str]) -> int:
    forward = ""
    index = 0
    while arguments[index] != "--":
        if arguments[index] == "-L":
            forward = arguments[index + 1]
        index += 2 if arguments[index] in ("-o", "-p", "-L") else 1
    destination = arguments[index + 1].rsplit("@", 1)[-1]
    if destination.startswith("unreachable"):
        sys.stderr.write(f"ssh: connect to host {destination} port 22: Connection refused")
        return REFUSED
    if forward:
        return _relay(forward)
    command = shlex.split(arguments[index + 2])
    if command[0] in _PYTHONS:
        if destination.startswith("nopython3") and command[0] == "python3":
            sys.stderr.write("sh: python3: command not found")
            return NOT_FOUND
        command[0] = sys.executable
    return subprocess.call(command)  # nosemgrep  # noqa: S603  # nosec B603


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
