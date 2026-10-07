"""The ``hermetic_monitor`` fixture keeps hook and launcher tests off a live Monitor (#9711)."""

from __future__ import annotations

import os
import socket

import pytest

from tests.helpers.monitor import UNREACHABLE_MONITOR_URL, UNREACHABLE_TOOL_TIMING_URL


@pytest.mark.usefixtures("hermetic_monitor")
def test_hermetic_monitor_pins_every_monitor_endpoint_to_a_dead_port() -> None:
    assert os.environ["LU_MONITOR_LOOPBACK"] == UNREACHABLE_MONITOR_URL
    assert os.environ["DELEGATE_MONITOR_API"] == UNREACHABLE_MONITOR_URL
    assert os.environ["TOOL_TIMING_API_URL"] == UNREACHABLE_TOOL_TIMING_URL
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.settimeout(2)
        assert probe.connect_ex(("127.0.0.1", 1)) != 0, "the pinned Monitor port must refuse connections"
