"""Monitor API client SDK — thin wrapper around the manifest + cache flow.

Agents (and ad-hoc scripts) should import this module instead of
hand-rolling their own HTTP calls. It implements the P1 + P3 contract
from GH #1309:

    1. Fetch ``/api/state/manifest`` — a ~1 KB index of per-component hashes.
    2. For each component the caller needs (rules, session, ...),
       consult the on-disk cache under ``.agent/cache/monitor/``.
       If the cache entry's hash matches the manifest's hash, skip the
       network call entirely.
    3. On miss, fetch the component with ``If-None-Match`` so the
       server can return ``304 Not Modified`` when the ETag hasn't
       changed — the response body is empty and we reuse the cache.
    4. Otherwise store the new body + hash + ETag for next time.

The goal is to make cold-start re-entry cheap: the fastest session is
one that downloads zero new bytes.

This is a pure-stdlib module — no httpx / requests dependency. The
Monitor API is always local (localhost:8765), so urllib is plenty.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any

from . import _monitor_cache as cache

DEFAULT_BASE_URL = "http://localhost:8765"
DEFAULT_TIMEOUT_S = 3.0


@dataclass
class ComponentResult:
    """One cached-or-fetched component + why we chose it."""

    key: str
    body: str
    hash: str
    source: str  # "cache" | "network" | "not-modified"


class MonitorClient:
    """Synchronous client. One instance per process is plenty.

    ``base_url`` defaults to localhost but is overridable so tests can
    spin up a fresh FastAPI TestClient and point the SDK at it.
    """

    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        *,
        timeout_s: float = DEFAULT_TIMEOUT_S,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_s = timeout_s

    # -- low-level HTTP --------------------------------------------

    def _get(
        self, path: str, *, headers: dict[str, str] | None = None
    ) -> tuple[int, str, dict[str, str]]:
        """Low-level GET. Never raises for ordinary HTTP status codes.

        The SDK runs during agent cold-start — an uncaught exception
        here prevents the agent from booting. We surface ALL HTTP
        status codes (2xx, 3xx, 4xx, 5xx) as a status + body + headers
        tuple so the caller can decide whether to degrade gracefully
        (e.g. fall back to reading a local file when the API has
        nothing useful to return). Only transport-level failures
        (socket, DNS, refused connection) still raise — those mean
        the API server is unreachable, which a caller wants to
        distinguish from "server up but resource missing".

        Reviewer CONCERN Gemini-A / #1309: previously a 404 from
        ``/api/session/current`` on a fresh checkout crashed
        ``bootstrap()`` with an unhandled ``HTTPError``.
        """
        url = self.base_url + path
        req = urllib.request.Request(url, headers=headers or {})
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_s) as resp:
                body = resp.read().decode("utf-8", errors="replace")
                resp_headers = {k.lower(): v for k, v in resp.headers.items()}
                return resp.status, body, resp_headers
        except urllib.error.HTTPError as exc:
            # 304 / 404 / 500 all come through here. Surface the
            # status + body so the caller can make a call.
            resp_headers = {
                k.lower(): v for k, v in (exc.headers or {}).items()
            }
            body = ""
            try:
                raw = exc.read()
                if raw:
                    body = raw.decode("utf-8", errors="replace")
            except Exception:
                pass
            return exc.code, body, resp_headers

    # -- high-level API --------------------------------------------

    def manifest(self) -> dict[str, Any]:
        """Fetch the cold-start manifest. Small, always current."""
        _, body, _ = self._get("/api/state/manifest")
        return json.loads(body)

    def rules(self, *, manifest: dict[str, Any] | None = None) -> ComponentResult:
        """Return the condensed rule text, cached by manifest hash."""
        return self._cached_component(
            key="rules",
            manifest_key="rules",
            manifest=manifest,
            default_url="/api/rules?format=markdown",
        )

    def session(self, *, manifest: dict[str, Any] | None = None) -> ComponentResult:
        """Return the condensed session summary, cached by manifest hash."""
        return self._cached_component(
            key="session",
            manifest_key="session",
            manifest=manifest,
            default_url="/api/session/current?format=markdown",
        )

    # -- internal shared path --------------------------------------

    def _cached_component(
        self,
        *,
        key: str,
        manifest_key: str,
        manifest: dict[str, Any] | None,
        default_url: str,
    ) -> ComponentResult:
        man = manifest if manifest is not None else self.manifest()
        entry = man.get(manifest_key) or {}
        expected_hash = entry.get("hash") or ""
        url = entry.get("url") or default_url

        cached = cache.get(key, expected_hash) if expected_hash else None
        if cached is not None:
            return ComponentResult(
                key=key, body=cached, hash=expected_hash, source="cache"
            )

        # Cache miss. Use If-None-Match so the server can 304 when the
        # ETag matches what we had on disk (useful after a
        # ``cache.invalidate`` or when the manifest hash advertised an
        # empty string because the rule files were momentarily
        # unreadable).
        headers: dict[str, str] = {}
        if expected_hash:
            headers["If-None-Match"] = f'"{expected_hash}"'

        status, body, resp_headers = self._get(url, headers=headers)
        if status == 304:
            # Server says "your cached version is still valid". Pull it.
            cached = cache.get(key, expected_hash)
            if cached is not None:
                return ComponentResult(
                    key=key, body=cached, hash=expected_hash, source="not-modified"
                )
            # 304 without a matching local cache — shouldn't happen,
            # but if it does, fall through to a fresh GET without
            # If-None-Match so we don't end up in a loop.
            status, body, resp_headers = self._get(url)

        if status >= 400 or not body:
            # Server reported a failure (404 on fresh checkout where
            # current.md is missing; 500 if collectors died). Return
            # an empty component rather than poisoning the cache with
            # an error payload — the caller can notice via
            # ``ComponentResult.source == "error"`` and degrade.
            return ComponentResult(
                key=key, body="", hash="", source=f"error:{status}"
            )

        etag = (resp_headers.get("etag") or "").strip('"') or expected_hash
        cache.put(key, body, body_hash=etag, url=url)
        return ComponentResult(key=key, body=body, hash=etag, source="network")

    # -- convenience bootstrap -------------------------------------

    def bootstrap(self) -> dict[str, ComponentResult]:
        """One-shot: manifest + every cached component.

        Returns a dict with keys ``rules`` and ``session``, each a
        ``ComponentResult``. Use this at the start of a session:

            client = MonitorClient()
            boot = client.bootstrap()
            rules_md = boot["rules"].body
        """
        man = self.manifest()
        return {
            "rules": self.rules(manifest=man),
            "session": self.session(manifest=man),
        }
