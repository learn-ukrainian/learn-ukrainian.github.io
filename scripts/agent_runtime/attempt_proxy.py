"""Byte-only stdio client for a parent-owned sources MCP connection.

This file is projected into the seat's runtime directory. It contains no
repository imports, receipt locations, or ability to start a host command.
"""

from __future__ import annotations

import os
import socket
import sys
import threading
from pathlib import Path


def main() -> None:
    with socket.socket(socket.AF_UNIX) as connection:
        endpoint = Path(sys.argv[1])
        os.chdir(endpoint.parent)
        connection.connect(endpoint.name)

        def send() -> None:
            while data := os.read(0, 65536):
                connection.sendall(data)
            connection.shutdown(socket.SHUT_WR)

        threading.Thread(target=send, daemon=True).start()
        while data := connection.recv(65536):
            sys.stdout.buffer.write(data)
            sys.stdout.buffer.flush()


if __name__ == "__main__":
    main()
