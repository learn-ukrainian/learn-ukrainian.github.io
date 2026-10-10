"""Bounded JSON GET for fleet board sources.

Only http and https are requested. The timeout is an overall deadline and
cannot exceed two seconds. Callers must not copy the URL into a response.
"""

from __future__ import annotations

import contextlib
import json
import threading
import time
import urllib.parse
import urllib.request
from collections.abc import Callable
from typing import Any

HTTP_TIMEOUT_S = 2.0
_MAX_BYTES = 1_000_000
_CHUNK = 64 * 1024

Opener = Callable[..., Any]


def _netloc(parts: urllib.parse.SplitResult) -> str:
    host = parts.hostname or ""
    if ":" in host:
        host = f"[{host}]"
    if parts.port is not None:
        return f"{host}:{parts.port}"
    return host


def clean_url(url: str) -> str:
    """Return an http(s) URL without userinfo or a fragment."""
    if not isinstance(url, str) or any(char in url for char in "\r\n"):
        raise ValueError
    parts = urllib.parse.urlsplit(url.strip())
    if parts.scheme not in {"http", "https"} or not parts.hostname:
        raise ValueError
    path = parts.path or ""
    return urllib.parse.urlunsplit((parts.scheme, _netloc(parts), path, parts.query, ""))


def join_url(base: str, suffix: str) -> str:
    """Join a configured base and a fixed suffix.

    Userinfo, query, and fragment on the base are dropped so they cannot ride
    along into a link or a request.
    """
    if not isinstance(base, str) or not isinstance(suffix, str):
        raise ValueError
    if any(char in base for char in "\r\n") or any(char in suffix for char in "\r\n?#"):
        raise ValueError
    path_base = urllib.parse.urlsplit(base.strip())
    if path_base.scheme not in {"http", "https"} or not path_base.hostname:
        raise ValueError
    path = (path_base.path or "").rstrip("/")
    extra = suffix if suffix.startswith("/") else f"/{suffix}"
    return urllib.parse.urlunsplit((path_base.scheme, _netloc(path_base), f"{path}{extra}", "", ""))


class _DeadlineRedirect(urllib.request.HTTPRedirectHandler):
    """Follow at most two redirects, and only while the deadline remains."""

    max_redirections = 2

    def __init__(self, deadline: float) -> None:
        super().__init__()
        self._deadline = deadline

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if time.monotonic() >= self._deadline:
            raise TimeoutError
        cleaned = clean_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, cleaned)


def _remaining(deadline: float) -> float:
    left = deadline - time.monotonic()
    if left <= 0:
        raise TimeoutError
    return left


def _tighten(response: Any, deadline: float) -> None:
    left = _remaining(deadline)
    candidates = [response]
    fp = getattr(response, "fp", None)
    if fp is not None:
        candidates.append(fp)
        raw = getattr(fp, "raw", None)
        if raw is not None:
            candidates.append(raw)
    for candidate in candidates:
        settimeout = getattr(candidate, "settimeout", None)
        if callable(settimeout):
            with contextlib.suppress(OSError):
                settimeout(left)
        sock = getattr(candidate, "_sock", None) or getattr(candidate, "sock", None)
        if sock is not None:
            with contextlib.suppress(OSError):
                sock.settimeout(left)


def _read_all(response: Any, deadline: float) -> bytes:
    chunks: list[bytes] = []
    total = 0
    while total <= _MAX_BYTES:
        _tighten(response, deadline)
        chunk = response.read(_CHUNK)
        if not isinstance(chunk, (bytes, bytearray)):
            raise ValueError
        if not chunk:
            break
        total += len(chunk)
        if total > _MAX_BYTES:
            raise ValueError
        chunks.append(bytes(chunk))
    return b"".join(chunks)


def _open_default(request: urllib.request.Request, timeout: float, deadline: float) -> Any:
    opener = urllib.request.build_opener(_DeadlineRedirect(deadline))
    return opener.open(request, timeout=timeout)


def _load(open_fn: Opener, request: urllib.request.Request, deadline: float) -> Any:
    with open_fn(request, timeout=_remaining(deadline)) as response:
        status = getattr(response, "status", 200)
        if isinstance(status, int) and status >= 300:
            raise ValueError
        raw = _read_all(response, deadline)
    return json.loads(raw.decode("utf-8"))


def _run_until(deadline: float, load: Callable[[], Any]) -> Any:
    """Return ``load()`` or raise ``TimeoutError`` when the deadline passes."""
    box: dict[str, Any] = {}

    def run() -> None:
        try:
            box["value"] = load()
        except Exception as exc:
            box["error"] = exc

    worker = threading.Thread(target=run, daemon=True)
    worker.start()
    worker.join(max(0.0, deadline - time.monotonic()))
    if "error" in box:
        raise box["error"]
    if "value" in box:
        return box["value"]
    raise TimeoutError


def fetch_json(url: str, *, timeout_s: float = HTTP_TIMEOUT_S, opener: Opener | None = None) -> Any:
    """GET JSON. ``timeout_s`` is an overall deadline, capped at ``HTTP_TIMEOUT_S``."""
    cleaned = clean_url(url)
    budget = timeout_s if 0 < timeout_s <= HTTP_TIMEOUT_S else HTTP_TIMEOUT_S
    deadline = time.monotonic() + budget
    request = urllib.request.Request(cleaned, headers={"Accept": "application/json"}, method="GET")

    def open_fn(req: urllib.request.Request, timeout: float) -> Any:
        if opener is not None:
            return opener(req, timeout=timeout)
        return _open_default(req, timeout, deadline)

    return _run_until(deadline, lambda: _load(open_fn, request, deadline))
