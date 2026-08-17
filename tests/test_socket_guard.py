"""Unit tests for the top-level socket-guard autouse fixture (#6968)."""

from __future__ import annotations

import socket
import urllib.request
from unittest.mock import MagicMock

import pytest

from tests.conftest import (
    SocketBlockedError,
    _is_localhost_address,
    _is_localhost_host,
)


def test_is_localhost_host_resolution() -> None:
    """Verify loopback and local identifiers are recognized."""
    assert _is_localhost_host("localhost") is True
    assert _is_localhost_host("LOCALHOST") is True
    assert _is_localhost_host("127.0.0.1") is True
    assert _is_localhost_host("127.0.1.1") is True
    assert _is_localhost_host("::1") is True
    assert _is_localhost_host("0.0.0.0") is True
    assert _is_localhost_host("::") is True
    assert _is_localhost_host("subdomain.localhost") is True
    assert _is_localhost_host(socket.gethostname()) is True

    # External targets are not localhost
    assert _is_localhost_host("example.com") is False
    assert _is_localhost_host("api.github.com") is False
    assert _is_localhost_host("8.8.8.8") is False
    assert _is_localhost_host("93.184.216.34") is False
    assert _is_localhost_host("2606:2800:220:1:248:1893:25c8:1946") is False


def test_is_localhost_address_resolution() -> None:
    """Verify AF_UNIX and AF_INET addresses are resolved."""
    assert _is_localhost_address(None) is True
    assert _is_localhost_address("/tmp/test.sock") is True
    assert _is_localhost_address(b"/tmp/test.sock") is True
    assert _is_localhost_address(("127.0.0.1", 8080)) is True
    assert _is_localhost_address(("localhost", 443)) is True
    assert _is_localhost_address(("93.184.216.34", 80)) is False
    assert _is_localhost_address(("api.github.com", 443)) is False


def test_unmarked_socket_connect_to_external_ip_fails() -> None:
    """An unmarked socket.connect to a non-localhost IP must fail closed."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        with pytest.raises(SocketBlockedError) as exc_info:
            s.connect(("93.184.216.34", 80))
        assert "Outbound network connection to '93.184.216.34' blocked by socket-guard" in str(exc_info.value)
    finally:
        s.close()


def test_unmarked_socket_connect_to_external_host_fails() -> None:
    """An unmarked socket.connect to a hostname must fail closed."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        with pytest.raises(SocketBlockedError) as exc_info:
            s.connect(("example.com", 80))
        assert "Outbound network connection to 'example.com' blocked by socket-guard" in str(exc_info.value)
    finally:
        s.close()


def test_unmarked_socket_connect_ex_fails() -> None:
    """An unmarked socket.connect_ex to a non-localhost host must fail closed."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        with pytest.raises(SocketBlockedError) as exc_info:
            s.connect_ex(("93.184.216.34", 80))
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


def test_unmarked_urlopen_fails() -> None:
    """Higher-level urllib callers fail with SocketBlockedError when contacting external hosts."""
    with pytest.raises((SocketBlockedError, urllib.error.URLError)) as exc_info:
        urllib.request.urlopen("http://93.184.216.34", timeout=1.0)
    exc = exc_info.value
    if isinstance(exc, urllib.error.URLError) and exc.reason:
        assert isinstance(exc.reason, SocketBlockedError)
    else:
        assert isinstance(exc, SocketBlockedError)


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


def test_socketpair_permitted() -> None:
    """socket.socketpair (AF_UNIX) is permitted."""
    parent, child = socket.socketpair()
    try:
        parent.send(b"hello")
        assert child.recv(5) == b"hello"
    finally:
        parent.close()
        child.close()


@pytest.mark.live_network
def test_live_network_marker_bypasses_guard(monkeypatch: pytest.MonkeyPatch) -> None:
    """When a test is marked with @pytest.mark.live_network, the socket guard is bypassed."""
    mock_connect = MagicMock(return_value=None)
    monkeypatch.setattr(socket.socket, "connect", mock_connect)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect(("example.com", 80))
        mock_connect.assert_called_once_with(("example.com", 80))
    finally:
        s.close()
