"""ACPX launcher-copy cleanup logs must not retain caller-controlled names (#10751)."""

from __future__ import annotations

import errno
import logging
import os
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from scripts.agent_runtime.adapters import acpx as acpx_module

_SECRET_COPY = "launch-secret12"
_SECRET_LABEL = "secret-looking-adapter-label"
_SECRET_ERRNO_TEXT = "secret-looking-os-error-text"
_SECRET_REFUSAL = "secret-looking-refusal-text"
_PRIVATE_VALUES = (_SECRET_COPY, "secret12", _SECRET_LABEL, _SECRET_ERRNO_TEXT, _SECRET_REFUSAL)


@pytest.fixture
def copy_base(tmp_path, monkeypatch):
    """A caller-owned copy base holding one secret-named copy directory."""
    base = tmp_path / "copies"
    base.mkdir(mode=0o700)
    (base / _SECRET_COPY).mkdir(mode=0o700)
    monkeypatch.setattr(acpx_module, "_CLAUDE_ACP_LAUNCHER_COPY_BASE", base)
    # The ancestor-trust walk is covered elsewhere; these tests exercise the log calls after it.
    monkeypatch.setattr(
        acpx_module,
        "_open_claude_acp_copy_base",
        lambda path, *, adapter_label: os.open(path, os.O_RDONLY | os.O_DIRECTORY),
    )
    return base


def _only_record(caplog, level):
    records = [
        record
        for record in caplog.records
        if record.name == acpx_module.__name__ and record.levelno == level
    ]
    assert len(records) == 1
    return records[0]


def _assert_constant(record, expected_message):
    assert record.getMessage() == expected_message
    assert record.args == ()
    assert record.exc_info is None
    for value in _PRIVATE_VALUES:
        assert value not in record.getMessage()
        assert value not in repr(vars(record))


def _cleanup_error(copy_base, caplog):
    with caplog.at_level(logging.DEBUG), pytest.raises(acpx_module.ClaudeAcpLauncherCleanupError) as raised:
        acpx_module._remove_claude_acp_copy_dir(_SECRET_COPY, adapter_label=_SECRET_LABEL)
    return raised.value


def _sweep(copy_base):
    old = time.time() - acpx_module._CLAUDE_ACP_LAUNCHER_COPY_MAX_AGE_S - 60
    os.utime(copy_base / _SECRET_COPY, (old, old))
    base_fd = os.open(copy_base, os.O_RDONLY | os.O_DIRECTORY)
    try:
        acpx_module._sweep_stale_claude_acp_launcher_copies(base_fd, copy_base)
    finally:
        os.close(base_fd)


def test_sweep_keeping_a_held_copy_logs_a_constant_message(copy_base, monkeypatch, caplog):
    monkeypatch.setattr(acpx_module, "_claude_acp_copies_in_use", lambda _base: {_SECRET_COPY})
    with caplog.at_level(logging.DEBUG):
        _sweep(copy_base)
    _assert_constant(
        _only_record(caplog, logging.INFO),
        "Claude ACP launcher sweep kept a stale copy: a live process holds it",
    )
    assert (copy_base / _SECRET_COPY).exists()


def test_sweep_failing_to_remove_a_copy_logs_a_constant_message(copy_base, monkeypatch, caplog):
    def refuse(_fd, _name):
        raise OSError(errno.EACCES, _SECRET_ERRNO_TEXT)

    monkeypatch.setattr(acpx_module, "_claude_acp_copies_in_use", lambda _base: set())
    monkeypatch.setattr(acpx_module, "_remove_claude_acp_copy_entry", refuse)
    with caplog.at_level(logging.DEBUG):
        _sweep(copy_base)
    _assert_constant(
        _only_record(caplog, logging.WARNING),
        "Claude ACP launcher sweep could not remove a stale copy",
    )


def test_cleanup_refusing_the_copy_base_logs_a_constant_message(copy_base, monkeypatch, caplog):
    def refuse(_base, *, adapter_label):
        raise acpx_module.ClaudeCodeExecutableRefusal(
            f"{adapter_label} {_SECRET_COPY} {_SECRET_REFUSAL}", reason="untrusted_path"
        )

    monkeypatch.setattr(acpx_module, "_open_claude_acp_copy_base", refuse)
    error = _cleanup_error(copy_base, caplog)
    # The typed error still names the copy for the caller; only the log is constant.
    assert _SECRET_COPY in str(error)
    _assert_constant(
        _only_record(caplog, logging.ERROR),
        "Claude ACP launcher cleanup refused the private copy base",
    )


def test_cleanup_failing_to_open_the_copy_base_logs_a_constant_message(copy_base, monkeypatch, caplog):
    def refuse(_base, *, adapter_label):
        raise OSError(errno.EACCES, _SECRET_ERRNO_TEXT)

    monkeypatch.setattr(acpx_module, "_open_claude_acp_copy_base", refuse)
    error = _cleanup_error(copy_base, caplog)
    assert _SECRET_COPY in str(error)
    _assert_constant(
        _only_record(caplog, logging.ERROR),
        "Claude ACP launcher cleanup could not open the private copy base",
    )


_BUSY = (
    "Claude ACP launcher cleanup left the private launcher copy in place: "
    "a live process still holds it, or the process table is unreadable"
)
_FAILED = (
    "Claude ACP launcher cleanup failed: cannot remove private launcher copy "
    "(it is not removable, or not a 0700 directory the caller owns)"
)


@pytest.mark.parametrize(
    ("held", "reason", "expected_message"),
    [
        ({_SECRET_COPY}, "cleanup_busy", _BUSY),
        (None, "cleanup_busy", _BUSY),
    ],
)
def test_cleanup_leaving_a_copy_in_place_logs_a_constant_message(
    copy_base, monkeypatch, caplog, held, reason, expected_message
):
    monkeypatch.setattr(acpx_module, "_claude_acp_copies_in_use", lambda _base: held)
    error = _cleanup_error(copy_base, caplog)
    assert error.reason == reason
    assert _SECRET_COPY in str(error)
    _assert_constant(_only_record(caplog, logging.ERROR), expected_message)
    assert (copy_base / _SECRET_COPY).exists()


def test_cleanup_of_a_copy_the_caller_does_not_own_logs_a_constant_message(copy_base, monkeypatch, caplog):
    monkeypatch.setattr(acpx_module, "_claude_acp_copy_owned", lambda _stat: False)
    error = _cleanup_error(copy_base, caplog)
    assert error.reason == "cleanup_failed"
    assert _SECRET_COPY in str(error)
    _assert_constant(_only_record(caplog, logging.ERROR), _FAILED)


def test_cleanup_failing_to_remove_a_copy_logs_a_constant_message(copy_base, monkeypatch, caplog):
    def refuse(_fd, _name):
        raise OSError(errno.EACCES, _SECRET_ERRNO_TEXT)

    monkeypatch.setattr(acpx_module, "_claude_acp_copies_in_use", lambda _base: set())
    monkeypatch.setattr(acpx_module, "_remove_claude_acp_copy_entry", refuse)
    error = _cleanup_error(copy_base, caplog)
    assert error.reason == "cleanup_failed"
    assert _SECRET_COPY in str(error)
    assert _SECRET_ERRNO_TEXT in str(error)
    _assert_constant(_only_record(caplog, logging.ERROR), _FAILED)
