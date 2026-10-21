"""Unit tests for the top-level package-wide socket-guard (#6968)."""

from __future__ import annotations

import socket

import pytest

from tests.conftest import (
    SocketBlockedError,
)


@pytest.fixture(scope="module")
def probe_module_fixture_blocked() -> str:
    """Adversarial module-scoped fixture probe verifying guard is active before module fixtures."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        with pytest.raises(SocketBlockedError):
            s.connect_ex(("198.51.100.1", 80))
        return "blocked_verified"
    finally:
        s.close()


def test_adversarial_module_scoped_fixture_probe_is_blocked(probe_module_fixture_blocked: str) -> None:
    """The socket guard must be installed before module-scoped fixtures execute (#6968)."""
    assert probe_module_fixture_blocked == "blocked_verified"


def test_unmarked_socket_connect_to_external_ip_fails() -> None:
    """An unmarked socket.connect to a non-localhost IP must fail closed."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        with pytest.raises(SocketBlockedError) as exc_info:
            s.connect(("198.51.100.1", 80))
        assert "Outbound network connection to '198.51.100.1' blocked by socket-guard" in str(exc_info.value)
    finally:
        s.close()


def test_unmarked_socket_connect_ex_fails() -> None:
    """An unmarked socket.connect_ex to a non-localhost host must fail closed."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        with pytest.raises(SocketBlockedError) as exc_info:
            s.connect_ex(("198.51.100.1", 80))
        assert "blocked by socket-guard" in str(exc_info.value)
    finally:
        s.close()


def test_unmarked_socket_sendto_fails() -> None:
    """An unmarked socket.sendto to an external address must fail closed."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        with pytest.raises(SocketBlockedError) as exc_info:
            s.sendto(b"ping", ("8.8.8.8", 53))
        assert "Outbound network connection to '8.8.8.8' blocked by socket-guard" in str(exc_info.value)
    finally:
        s.close()


def test_unmarked_socket_sendmsg_fails() -> None:
    """An unmarked socket.sendmsg to an external address must fail closed."""
    if not hasattr(socket.socket, "sendmsg"):
        pytest.skip("socket.sendmsg not supported on this platform")
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        with pytest.raises(SocketBlockedError) as exc_info:
            s.sendmsg([b"ping"], [], 0, ("8.8.8.8", 53))
        assert "Outbound network connection to '8.8.8.8' blocked by socket-guard" in str(exc_info.value)
    finally:
        s.close()


def test_localhost_loopback_connection_permitted() -> None:
    """Loopback socket operations on 127.0.0.1 remain fully functional."""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("127.0.0.1", 0))
    server.listen(1)
    port = server.getsockname()[1]

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client.connect(("127.0.0.1", port))
        conn, _ = server.accept()
        conn.close()
    finally:
        client.close()
        server.close()
