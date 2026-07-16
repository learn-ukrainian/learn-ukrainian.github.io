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

import hashlib
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any

from . import _monitor_cache as cache

DEFAULT_BASE_URL = "http://localhost:8765"
DEFAULT_TIMEOUT_S = 3.0

_KNOWLEDGE_MANIFEST_PATH = "/api/knowledge/manifest"
_KNOWLEDGE_COLD_START_PATH = "/api/knowledge/cold-start"

# Bound the consumer label before it ever reaches a hash or a filesystem path.
_MAX_CONSUMER_LEN = 128


def _canonical_context(
    role: str | None,
    task_family: str | None,
    track: str | None,
    owned_paths: list[str] | None,
) -> dict[str, Any]:
    """Normalize a task context deterministically (mirrors ``registry.normalize_context``).

    Blank/whitespace scalars collapse to ``None``; owned paths are stripped,
    de-duplicated, and sorted. Kept dependency-light (no registry import) so the
    cold-start client stays pure-stdlib.
    """

    def _norm(value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None

    paths = sorted({p.strip() for p in (owned_paths or []) if p and p.strip()})
    return {
        "role": _norm(role),
        "task_family": _norm(task_family),
        "track": _norm(track),
        "owned_paths": paths,
    }


def _bounded_consumer(consumer: str | None) -> str:
    """Cap + sanitize the consumer label before it ever reaches a hash or a
    filesystem path. Never used verbatim in a cache key/filename (ADR-011 P3)."""
    if not isinstance(consumer, str):
        return ""
    return consumer.strip()[:_MAX_CONSUMER_LEN]


def _context_fingerprint(consumer: str | None, context: dict[str, Any]) -> str:
    """One full SHA-256 fingerprint over the bounded consumer + canonical context.

    Folds ``consumer`` into the same digest as the context rather than splicing
    the raw string into the cache key — a cache filename must never carry the raw
    consumer, role, or owned paths (ADR-011 P3 privacy contract). Uses the full
    64-hex digest, never a truncated prefix: a truncated digest is a needless
    collision risk once enough distinct (consumer, context) pairs accumulate.
    """
    payload = {"consumer": _bounded_consumer(consumer), "context": context}
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _parse_projection(body: str) -> dict[str, Any]:
    """Best-effort parse of a ``{"enabled":bool,"records":[...]}`` projection body.

    Malformed/non-JSON/non-dict input degrades to the empty, disabled shape rather
    than raising — this feeds a diff, not a validator.
    """
    try:
        data = json.loads(body)
    except (json.JSONDecodeError, TypeError):
        return {"enabled": False, "records": []}
    if not isinstance(data, dict):
        return {"enabled": False, "records": []}
    records = data.get("records")
    return {
        "enabled": bool(data.get("enabled")),
        "records": [rec for rec in records if isinstance(rec, dict)] if isinstance(records, list) else [],
    }


def _serialize_projection(enabled: bool, records: list[dict[str, Any]]) -> str:
    return json.dumps(
        {"enabled": enabled, "records": records}, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    )


def _diff_changed_pointers(*, previous_body: str | None, new_body: str) -> str:
    """New/changed pointers only, diffed by canonical pointer content (the only
    fields a projection carries: id/state/content_hash/routing).

    ``previous_body`` is ``None`` on a cold fetch (nothing cached yet) — every
    pointer in the fresh projection counts as changed/new. A record present in
    ``previous_body`` but absent from ``new_body`` (removed, or no longer matches
    this context) is NOT surfaced as a change — ADR-011 P3 defines no tombstone
    contract; the caller's cache write below still drops it from the stored
    snapshot, so it simply stops appearing in future diffs.
    """
    new_proj = _parse_projection(new_body)
    if previous_body is None:
        changed = new_proj["records"]
    else:
        previous_by_id = {rec.get("id"): rec for rec in _parse_projection(previous_body)["records"]}
        changed = [rec for rec in new_proj["records"] if previous_by_id.get(rec.get("id")) != rec]
    return _serialize_projection(new_proj["enabled"], changed)


def _empty_changed_projection(cached_body: str) -> str:
    """Zero-changed-pointers projection for a warm, unchanged (``304``) fetch."""
    proj = _parse_projection(cached_body)
    return _serialize_projection(proj["enabled"], [])


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
        session_id: str | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_s = timeout_s
        # SessionStart persists Claude Code's documented ``session_id`` as a
        # project-private value. Non-Claude callers retain their own explicit thread
        # identities; no route falls back to another session's newest transcript.
        self.session_id = (
            session_id
            or os.environ.get("LEARN_UKRAINIAN_SESSION_ID")
            or os.environ.get("CODEX_THREAD_ID")
            or os.environ.get("CODEX_SESSION_ID")
            or None
        )

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
        merged_headers = dict(headers or {})
        # Only inject when the caller has not already supplied the header in ANY case — urllib
        # title-cases header keys, so a caller's ``x-session-id`` would otherwise collide with and
        # be clobbered by the injected value. An explicit caller header always wins.
        if self.session_id and not any(k.lower() == "x-session-id" for k in merged_headers):
            merged_headers["X-Session-Id"] = self.session_id
        req = urllib.request.Request(url, headers=merged_headers)
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
            default_url="/api/session/current?agent=orchestrator&format=markdown",
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

    # -- ADR-011 P3 filtered research projection --------------------

    def _fetch_changed_projection(self, *, key: str, url: str) -> ComponentResult:
        """Shared fetch/diff/cache path for a filtered or cold-start pointer
        projection. The on-disk cache stores the COMPLETE latest projection; the
        returned ``ComponentResult.body`` carries only the added/changed pointers.

        Contract (ADR-011 P3):

        * cold (nothing cached for this key) → the first ``200`` returns every
          pointer in the fresh projection (``source="network"``, all "changed").
        * warm + unchanged → ``If-None-Match`` yields a bodyless ``304``; the
          returned body is a valid EMPTY pointer projection (zero changed) —
          even after an unrelated global registry edit, because the server's
          filtered ETag only moves for contexts the edited record routes to.
        * warm + changed → a fresh ``200`` diffs the new projection's pointers
          against the previously cached full snapshot by canonical content
          (id/state/content_hash/routing — the only fields a pointer carries) and
          returns only the new/changed ones, then replaces the cached full
          snapshot with the fresh one. A record that disappeared (removed, or no
          longer matches) updates the cache but is NOT surfaced as a change — P3
          defines no tombstone contract.

        Fails soft to an empty component (``source="error:*"``) on any transport
        failure (including unreachable-server ``URLError``, a superclass HTTPError
        doesn't cover) or cache read/write failure — this is an optional boundary
        and must never crash ``bootstrap()``.
        """
        try:
            cached = cache.peek(key)
            headers: dict[str, str] = {}
            if cached is not None and cached.hash:
                headers["If-None-Match"] = f'"{cached.hash}"'

            status, body, resp_headers = self._get(url, headers=headers)
            if status == 304:
                if cached is None:
                    # Defensive only — unreachable in practice: we only ever send
                    # If-None-Match when `cached` is populated, so the server has
                    # no ETag to 304 against otherwise (Gemini review, dead branch).
                    return ComponentResult(key=key, body="", hash="", source="error:304-no-cache")
                return ComponentResult(
                    key=key,
                    body=_empty_changed_projection(cached.body),
                    hash=cached.hash,
                    source="not-modified",
                )

            if status >= 400 or not body:
                return ComponentResult(key=key, body="", hash="", source=f"error:{status}")

            etag = (resp_headers.get("etag") or "").strip('"')
            changed_body = _diff_changed_pointers(
                previous_body=cached.body if cached is not None else None,
                new_body=body,
            )
            cache.put(key, body, body_hash=etag, url=url)
            return ComponentResult(key=key, body=changed_body, hash=etag, source="network")
        except Exception as exc:
            return ComponentResult(key=key, body="", hash="", source=f"error:{type(exc).__name__}")

    def research(
        self,
        *,
        role: str | None = None,
        task_family: str | None = None,
        track: str | None = None,
        owned_paths: list[str] | None = None,
        consumer: str = "orchestrator",
    ) -> ComponentResult:
        """Fetch the task-scoped, pointer-only filtered research projection.

        POINTERS ONLY — this never fetches record bodies; the projection carries
        IDs/states/hashes/routing, and bodies are pulled on demand elsewhere. This
        is the full **AND**-matcher context (``/api/knowledge/manifest``) — use it
        when at least one of ``task_family``/``track``/``owned_paths`` is known. A
        ``role``-only context with none of those has no family/track/path for the
        AND matcher to satisfy and belongs in :meth:`cold_start` instead.

        Caching is keyed on a fingerprint over the bounded ``consumer`` plus the
        canonical context — never raw owned paths or role text — and returns only
        the changed/new pointers since the last call for this exact key (see
        :meth:`_fetch_changed_projection`).
        """
        context = _canonical_context(role, task_family, track, owned_paths)
        fingerprint = _context_fingerprint(consumer, context)
        key = f"research__{fingerprint}"

        params: list[tuple[str, str]] = []
        if context["role"]:
            params.append(("role", context["role"]))
        if context["task_family"]:
            params.append(("task_family", context["task_family"]))
        if context["track"]:
            params.append(("track", context["track"]))
        params.extend(("owned_path", p) for p in context["owned_paths"])
        url = _KNOWLEDGE_MANIFEST_PATH
        if params:
            url = f"{url}?{urllib.parse.urlencode(params)}"

        return self._fetch_changed_projection(key=key, url=url)

    def cold_start(self, *, role: str, consumer: str = "orchestrator") -> ComponentResult:
        """Fetch the role-only cold-start pointer projection (``cold_start_roles``).

        Distinct from :meth:`research`: this NEVER runs the AND matcher. It hits
        the dedicated ``GET /api/knowledge/cold-start`` announcer, which matches
        solely on the role's opt-in ``cold_start_roles`` list — a record that only
        declares ``cold_start_roles`` (and not ``routing.roles``/``task_families``/
        ...) still announces here even though it would fail the AND matcher on the
        missing family/track/path dimensions a bare role can't supply.

        Cached + diffed the same way as :meth:`research` (changed pointers only,
        full snapshot cached) under its own key prefix so it never shares a cache
        entry with an AND-matched ``research()`` call for the same role text.
        """
        normalized_role = (role or "").strip()
        context = {"role": normalized_role, "task_family": None, "track": None, "owned_paths": []}
        fingerprint = _context_fingerprint(consumer, context)
        key = f"cold_start__{fingerprint}"

        url = _KNOWLEDGE_COLD_START_PATH
        if normalized_role:
            url = f"{url}?{urllib.parse.urlencode([('role', normalized_role)])}"

        return self._fetch_changed_projection(key=key, url=url)

    # -- convenience bootstrap -------------------------------------

    def bootstrap(
        self,
        *,
        role: str | None = None,
        task_family: str | None = None,
        track: str | None = None,
        owned_paths: list[str] | None = None,
        consumer: str = "orchestrator",
    ) -> dict[str, ComponentResult]:
        """One-shot: manifest + every cached component.

        With no arguments this returns **exactly** ``{"rules", "session"}`` — the
        pre-P3 shape, byte-for-byte. Passing any research context opts in an extra
        ``"research"`` key. A ``role`` given ALONE (no ``task_family``/``track``/
        ``owned_paths``) routes through the role-only cold-start pointer path
        (:meth:`cold_start` — ``cold_start_roles``, never the AND matcher, which
        would silently under-match cold-start-only records given a bare role with
        no other dimension). Any other combination routes through the full
        AND-matched :meth:`research` context.

            client = MonitorClient()
            boot = client.bootstrap()                     # rules + session only
            boot = client.bootstrap(role="quality")       # + cold-start pointers
        """
        man = self.manifest()
        result = {
            "rules": self.rules(manifest=man),
            "session": self.session(manifest=man),
        }
        if role and not (task_family or track or owned_paths):
            result["research"] = self.cold_start(role=role, consumer=consumer)
        elif role or task_family or track or owned_paths:
            result["research"] = self.research(
                role=role,
                task_family=task_family,
                track=track,
                owned_paths=owned_paths,
                consumer=consumer,
            )
        return result
