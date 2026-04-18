"""Wrap uvicorn's signal handlers so the API log records WHO killed the server.

Default uvicorn behaviour is silent: the access log shows the last request
served, then ``Shutting down`` appears with no signal name and no PID. After
the fact you can't tell whether it was Ctrl+C, ``services.sh stop``, a
parent-shell SIGHUP, or the OS jetsam killer (the latter is SIGKILL and
wouldn't reach this code, but the rest are indistinguishable in the log).

This module installs wrappers AFTER uvicorn has installed its own handlers
(via a FastAPI startup event), so the original ``Server.handle_exit`` still
runs — we just log a line first.
"""

from __future__ import annotations

import logging
import os
import signal
from collections.abc import Callable
from typing import Any

_LOG = logging.getLogger("api.signals")

_TRACKED_SIGNALS: tuple[int, ...] = (
    signal.SIGTERM,
    signal.SIGINT,
    signal.SIGHUP,
)

_installed = False


def _wrap(orig: Callable[..., Any] | int | None, signum: int) -> Callable[[int, Any], None]:
    def handler(received: int, frame: Any) -> None:
        try:
            name = signal.Signals(received).name
        except ValueError:
            name = f"signal:{received}"
        _LOG.warning(
            "received %s — pid=%d ppid=%d. Initiating graceful shutdown.",
            name,
            os.getpid(),
            os.getppid(),
        )
        # Delegate to whatever uvicorn (or the previous installer) had set.
        if callable(orig):
            orig(received, frame)
        elif orig == signal.SIG_DFL:
            # Restore default and re-raise so the signal takes effect.
            signal.signal(signum, signal.SIG_DFL)
            os.kill(os.getpid(), signum)
        # SIG_IGN: drop the signal as before.

    return handler


def install_signal_logging() -> None:
    """Idempotently wrap uvicorn's signal handlers with logging wrappers.

    Must be called from the main thread (only the main thread can call
    ``signal.signal``). FastAPI's startup hooks run in the main thread on
    the asyncio loop, which is fine.
    """
    global _installed
    if _installed:
        return
    for sig in _TRACKED_SIGNALS:
        try:
            existing = signal.getsignal(sig)
            signal.signal(sig, _wrap(existing, sig))
        except (ValueError, OSError) as exc:  # not main thread, or signal not supported
            _LOG.debug("cannot wrap %s: %s", sig, exc)
    _installed = True
    _LOG.info(
        "signal logging installed for %s",
        ", ".join(signal.Signals(s).name for s in _TRACKED_SIGNALS),
    )
