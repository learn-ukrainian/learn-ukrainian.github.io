"""ADR-011 P2 — Project Research Registry runtime layer.

P1 (``scripts/audit/check_research_registry.py``) is the source of truth for the
schema, the canonical digest projection/hash, drift detection, lifecycle, path
safety, and record validity. This module is the *runtime* layer that the bounded
discovery API (``scripts/api/knowledge_router.py``) and the cold-start manifest
component build on. It deliberately **reuses** P1's primitives — it does not
re-implement a second normalization, fence parser, schema, or content-hash
algorithm.

Runtime contract (ADR-011 §"Runtime kill switch", §"Failure / degradation"):

* **Disabled by default.** While disabled the registry is never loaded or parsed.
* **Fail-open.** Enabled + a missing/malformed/invalid registry yields *no*
  research surface and a logged warning — never a boot or API 500. An unexpected
  exception anywhere in the load path degrades the same way, via
  :func:`load_runtime_safe`.
* **Per-record isolation is drift-only.** ADR-011 grants isolation to a single
  invariant: a ``content_hash`` that no longer matches its digest. That record is
  excluded while healthy records keep routing. Any other semantic defect P1
  reports (broken provenance, a lifecycle/consumer/ownership violation, a
  duplicate id, a supersession cycle, an over-cap cold-start role) hides the
  *whole* registry — it is not safe to isolate per record.
* **No side effects at request time.** No GitHub, subprocess, network,
  ``sources.db``, or embeddings access — only local file reads.

Everything here is deterministic: identical inputs → identical bytes → identical
ETag.
"""

from __future__ import annotations

import fnmatch
import json
import logging
import math
import os
import re
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any

import yaml

from scripts.audit import check_research_registry as crr

logger = logging.getLogger("research.registry")

# --------------------------------------------------------------------------- #
# Kill switch (ADR-011 §"Runtime kill switch")
# --------------------------------------------------------------------------- #
ENV_FLAG = "LEARN_UK_RESEARCH_REGISTRY_ENABLED"
LIVE_FLAG_RELATIVE = Path(".runtime") / "api" / "research-registry.json"

# Strict boolean spellings for the environment override. Case-insensitive.
_ENV_TRUE = frozenset({"true", "1", "yes", "on"})
_ENV_FALSE = frozenset({"false", "0", "no", "off"})

# --------------------------------------------------------------------------- #
# Budgets (ADR-011 §"Budgets and selection helper"). Serialized UTF-8 bytes are
# the normative gate; tokens are a pinned ceil(bytes/2) estimate.
# --------------------------------------------------------------------------- #
MAX_STATE_MANIFEST_BYTES = 2048  # total /api/state/manifest response
MAX_RESEARCH_COMPONENT_BYTES = 512  # the {hash,url} manifest component
MAX_FILTERED_BYTES = 1536  # /api/knowledge/manifest filtered projection
MAX_FILTERED_RECORDS = 5  # top-N pointers per context
MAX_RECORD_BYTES = 4096  # one /api/knowledge/record/{id} body (mirrors P1)
MAX_SELECTED_BODIES_BYTES = 8192  # automatic selected-body helper total (P3 consumer)

# Request-side caps (ADR-011 §"Pure AND context matcher": bound the work).
MAX_QUERY_VALUE_LEN = 128
MAX_OWNED_PATH_LEN = 512
MAX_OWNED_PATHS = 64

KNOWLEDGE_MANIFEST_URL = "/api/knowledge/manifest"

# Record-id shape — mirrors the JSON Schema ``slug`` pattern. Used to reject
# traversal/slash/junk ids before any registry lookup.
_SLUG_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")

# Test/consumer seam: override the live repo root without importing the API config.
_ROOT_OVERRIDE: Path | None = None


def est_tokens(utf8_bytes: int) -> int:
    """Pinned conservative token estimate: ``ceil(utf8_bytes / 2)`` (ADR-011)."""
    return math.ceil(utf8_bytes / 2)


def _live_repo_root() -> Path:
    """The live git checkout that hosts the registry and the runtime flag file.

    Uses the API's ``LIVE_REPO_ROOT`` (the real checkout, where ``docs/`` is a
    real directory rather than a release-snapshot symlink), unless a test sets an
    explicit override. The import is lazy so non-API consumers of the pure matcher
    do not pull in the API config.
    """
    if _ROOT_OVERRIDE is not None:
        return _ROOT_OVERRIDE
    from scripts.api.config import LIVE_REPO_ROOT  # lazy-ok: decouple matcher from API config

    return LIVE_REPO_ROOT


def _registry_path(root: Path) -> Path:
    return root / "docs" / "references" / "research-registry.yaml"


def _live_flag_path(root: Path) -> Path:
    return root / LIVE_FLAG_RELATIVE


def _parse_bool_strict(raw: str) -> bool | None:
    """Return True/False for an accepted spelling, or None for anything else."""
    value = raw.strip().lower()
    if value in _ENV_TRUE:
        return True
    if value in _ENV_FALSE:
        return False
    return None


def is_enabled(*, root: Path | None = None) -> bool:
    """Resolve the feature flag dynamically, most-specific layer wins.

    1. environment variable ``LEARN_UK_RESEARCH_REGISTRY_ENABLED`` (strict);
    2. live gitignored file ``<root>/.runtime/api/research-registry.json``;
    3. compiled default ``False``.

    An invalid higher-precedence value (bad env spelling, malformed/unreadable
    live file) warns and resolves to ``False`` — it never falls through to a
    lower, possibly-enabled layer.
    """
    env_value = os.environ.get(ENV_FLAG)
    if env_value is not None:
        parsed = _parse_bool_strict(env_value)
        if parsed is None:
            logger.warning(
                "research registry: invalid %s=%r; treating as disabled", ENV_FLAG, env_value
            )
            return False
        return parsed

    root = root if root is not None else _live_repo_root()
    flag_path = _live_flag_path(root)
    if not flag_path.exists():
        return False
    try:
        raw = flag_path.read_text("utf-8")
        data = json.loads(raw)
    except (OSError, ValueError) as exc:
        logger.warning(
            "research registry: live flag %s is unreadable/malformed (%s); disabled",
            flag_path,
            exc,
        )
        return False
    try:
        value = data["research_registry"]["enabled"]
    except (KeyError, TypeError):
        logger.warning(
            "research registry: live flag %s missing research_registry.enabled; disabled",
            flag_path,
        )
        return False
    if isinstance(value, bool):
        return value
    logger.warning(
        "research registry: live flag %s enabled is not a boolean (%r); disabled",
        flag_path,
        value,
    )
    return False


# --------------------------------------------------------------------------- #
# Deterministic JSON serialization (single source for body bytes + ETag)
# --------------------------------------------------------------------------- #
def canonical_json_bytes(payload: Any) -> bytes:
    """Serialize deterministically: sorted keys, compact separators, UTF-8.

    The knowledge endpoints send exactly these bytes and compute their ETag over
    them, so byte-identical projections for two unrelated contexts produce a
    byte-identical response and a matching ETag.
    """
    return json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


# --------------------------------------------------------------------------- #
# Runtime loading + per-record validity (reuses P1)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class RegistryRuntime:
    """A loaded, schema-valid registry snapshot with per-record validity flags."""

    root: Path
    pairs: tuple[tuple[dict[str, Any], bool], ...]  # (record, is_valid)

    @property
    def valid_records(self) -> list[dict[str, Any]]:
        return [rec for rec, valid in self.pairs if valid]

    def valid_by_id(self, record_id: str) -> dict[str, Any] | None:
        for rec, valid in self.pairs:
            if valid and rec["id"] == record_id:
                return rec
        return None

    def global_hash(self) -> str:
        """Single registry-wide hash over the routing-relevant projection.

        Covers each record's id, state, stored ``content_hash``, runtime validity,
        access class, and routing dimensions — never digest bodies, YAML
        formatting/ordering, or ``generated_at``. Editing any record's routed
        metadata, state, content hash, or validity flips it; a pure YAML
        reorder/reformat does not.
        """
        items = []
        for rec, valid in self.pairs:
            routing = rec.get("routing") or {}
            items.append(
                {
                    "id": rec["id"],
                    "state": rec["state"],
                    "content_hash": rec["content_hash"],
                    "valid": valid,
                    "access_class": rec["access_class"],
                    "cold_start_roles": sorted(rec.get("cold_start_roles") or []),
                    "roles": sorted(routing.get("roles") or []),
                    "task_families": sorted(routing.get("task_families") or []),
                    "tracks": sorted(routing.get("tracks") or []),
                    "owned_paths": sorted(routing.get("owned_paths") or []),
                }
            )
        items.sort(key=lambda item: item["id"])
        return sha256(canonical_json_bytes(items)).hexdigest()


def load_runtime(*, root: Path | None = None) -> RegistryRuntime | None:
    """Load the registry and validate it via P1's ``validate_registry`` — the single
    semantic authority for schema, lifecycle, supersession, consumer, ownership, and
    digest-policy invariants (this module never duplicates that logic).

    Returns ``None`` (fail-open: omit the whole research surface) when the file is
    missing/unreadable/malformed, or when P1 reports any *non-drift* error — a
    structural schema violation, broken provenance, a lifecycle/consumer/ownership
    violation, a duplicate id, a supersession cycle, or an over-cap cold-start role.
    ADR-011 grants per-record isolation only to ``content_hash`` drift: when P1
    reports drift and nothing else, the runtime is still built and only the drifted
    ids are marked ``valid=False`` so healthy records keep routing.
    """
    root = root if root is not None else _live_repo_root()
    path = _registry_path(root)
    try:
        raw, data = crr.load_registry(path)
    except (OSError, ValueError, yaml.YAMLError, RecursionError) as exc:
        logger.warning("research registry: cannot load %s (%s); no research surface", path, exc)
        return None
    try:
        result = crr.validate_registry(data, project_root=root, raw_text=raw)
    except (OSError, ValueError, yaml.YAMLError, RecursionError, KeyError, TypeError) as exc:
        logger.warning(
            "research registry: %s failed validation (%s); no research surface",
            path,
            type(exc).__name__,
        )
        return None
    if result.errors:
        logger.warning(
            "research registry: %s fails semantic validation (%d error(s)); no research surface",
            path,
            len(result.errors),
        )
        return None
    records = data.get("records") or []
    drifted = set(result.drift)
    pairs = tuple((rec, rec["id"] not in drifted) for rec in records)
    return RegistryRuntime(root=root, pairs=pairs)


def load_runtime_safe(*, root: Path | None = None) -> RegistryRuntime | None:
    """Fail-open boundary around :func:`load_runtime` for every HTTP-facing caller.

    ``load_runtime`` already turns known-bad input (missing file, malformed YAML,
    semantic errors) into ``None``, but a pathological/injected failure (e.g. a
    parser resource error we didn't anticipate, or a defect in a future P1 change)
    must still never surface as an API 500. Catches any unexpected ``Exception``
    and logs only the exception type — never registry or digest contents. Callers
    must check :func:`is_enabled` first; this function does not gate on the flag.
    """
    try:
        return load_runtime(root=root)
    except Exception as exc:
        logger.warning(
            "research registry: unexpected %s loading runtime; no research surface",
            type(exc).__name__,
        )
        return None


def research_manifest_component(*, root: Path | None = None) -> dict[str, str] | None:
    """The ``{hash, url}`` research component for ``/api/state/manifest``.

    Returns ``None`` (omit the component, preserving pre-P2 clients) when the
    feature is disabled or the registry cannot be exposed. Never loads the
    registry while disabled.
    """
    if not is_enabled(root=root):
        return None
    runtime = load_runtime_safe(root=root)
    if runtime is None:
        return None
    return {"hash": runtime.global_hash(), "url": KNOWLEDGE_MANIFEST_URL}


# --------------------------------------------------------------------------- #
# Pure AND context matcher (ADR-011 §"Routing algebra")
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class Context:
    """A normalized task context. Single role/family/track, a set of owned paths."""

    role: str | None
    task_family: str | None
    track: str | None
    owned_paths: tuple[str, ...]

    def is_empty(self) -> bool:
        return (
            self.role is None
            and self.task_family is None
            and self.track is None
            and not self.owned_paths
        )


def normalize_context(
    role: str | None,
    task_family: str | None,
    track: str | None,
    owned_paths: list[str] | None,
) -> Context:
    """Deduplicate/reorder so semantically identical contexts are byte-identical."""

    def _norm(value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None

    paths = sorted({p.strip() for p in (owned_paths or []) if p and p.strip()})
    return Context(_norm(role), _norm(task_family), _norm(track), tuple(paths))


def matches(routing: dict[str, Any], ctx: Context) -> bool:
    """Conjunctive match: every dimension present on the record must be satisfied.

    A dimension omitted from the record is a wildcard. A record dimension the
    context lacks fails the match (track alone never surfaces a family-scoped
    record). ``owned_paths`` intersect via deterministic, case-sensitive globbing.
    """
    roles = routing.get("roles")
    if roles is not None and (ctx.role is None or ctx.role not in roles):
        return False
    families = routing.get("task_families")
    if families is not None and (ctx.task_family is None or ctx.task_family not in families):
        return False
    tracks = routing.get("tracks")
    if tracks is not None and (ctx.track is None or ctx.track not in tracks):
        return False
    globs = routing.get("owned_paths")
    if globs is not None:
        if not ctx.owned_paths:
            return False
        if not any(fnmatch.fnmatchcase(path, glob) for path in ctx.owned_paths for glob in globs):
            return False
    return True


# --------------------------------------------------------------------------- #
# Projections (allowlisted — never leak bodies/summaries/prose)
# --------------------------------------------------------------------------- #
def pointer(record: dict[str, Any]) -> dict[str, Any]:
    """The bounded, allowlisted filtered-manifest pointer for one record.

    IDs, lifecycle state, P1 content hash, and routing metadata only — never
    summary, digest path/body, source URL, ownership prose, timestamps, the global
    hash, or telemetry.
    """
    routing = record.get("routing") or {}
    routing_out = {
        key: sorted(routing[key])
        for key in ("roles", "task_families", "tracks", "owned_paths")
        if key in routing
    }
    return {
        "id": record["id"],
        "state": record["state"],
        "content_hash": record["content_hash"],
        "routing": routing_out,
    }


def _apply_caps(matched: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
    """The single deterministic cap renderer shared by every pointer selector.

    Takes an already-sorted list of matched records; returns (pointers, dropped_ids)
    honouring ``MAX_FILTERED_RECORDS`` (top-N) then ``MAX_FILTERED_BYTES`` (measured
    on the exact serialized response). Both the dispatch AND matcher and the
    role-only cold-start announcer route through here so the two surfaces cannot
    drift apart on cap semantics. Logging the drop is the caller's job so the log
    line names which surface truncated.
    """
    dropped: list[str] = []
    if len(matched) > MAX_FILTERED_RECORDS:
        dropped.extend(rec["id"] for rec in matched[MAX_FILTERED_RECORDS:])
        matched = matched[:MAX_FILTERED_RECORDS]
    pointers = [pointer(rec) for rec in matched]
    while pointers and len(canonical_json_bytes(_manifest_payload(pointers))) > MAX_FILTERED_BYTES:
        dropped.append(pointers[-1]["id"])
        pointers = pointers[:-1]
    return pointers, dropped


def select_pointers(runtime: RegistryRuntime, ctx: Context) -> tuple[list[dict[str, Any]], list[str]]:
    """Return (pointers, dropped_ids). No context → zero records (never "show all").

    Deterministically sorted by record id, capped via the shared
    :func:`_apply_caps` renderer. Every dropped id is logged — never a silent
    truncation.
    """
    if ctx.is_empty():
        return [], []
    matched = sorted(
        (rec for rec in runtime.valid_records if matches(rec.get("routing") or {}, ctx)),
        key=lambda rec: rec["id"],
    )
    pointers, dropped = _apply_caps(matched)
    if dropped:
        logger.warning(
            "research registry: knowledge manifest dropped record id(s) over budget: %s",
            ", ".join(dropped),
        )
    return pointers, dropped


def select_cold_start_pointers(
    runtime: RegistryRuntime, role: str | None
) -> tuple[list[dict[str, Any]], list[str]]:
    """Return (pointers, dropped_ids) for the role-only cold-start announcer.

    ADR-011 §"Cold-start algebra (role only)": cold start has no task family,
    track, or owned paths, so it MUST NOT run the full AND matcher (which would
    fail closed on the missing dimensions anyway). It uses **only** the opt-in
    top-level ``cold_start_roles`` allow-list: a record announces a pointer to a
    role solely when it lists that role. A missing/blank role, or a role no record
    opts into, yields zero pointers. Bodies are never announced — pointers only.
    Shares the exact deterministic cap renderer with :func:`select_pointers`.
    """
    role = (role or "").strip()
    if not role:
        return [], []
    matched = sorted(
        (rec for rec in runtime.valid_records if role in (rec.get("cold_start_roles") or [])),
        key=lambda rec: rec["id"],
    )
    pointers, dropped = _apply_caps(matched)
    if dropped:
        logger.warning(
            "research registry: cold-start pointers dropped record id(s) over budget for role %r: %s",
            role,
            ", ".join(dropped),
        )
    return pointers, dropped


def context_fingerprint(ctx: Context) -> str:
    """A stable, opaque digest of a normalized context for cache keys / persistence.

    Hashes the canonical ``{role, task_family, track, owned_paths}`` projection so
    two byte-identical contexts share a fingerprint and two different ones do not.
    Because only the digest is ever persisted or used as a cache-key component, the
    raw owned paths never leave the caller — ADR-011 P3 forbids persisting or
    keying on raw paths, role, or task text.
    """
    payload = {
        "role": ctx.role,
        "task_family": ctx.task_family,
        "track": ctx.track,
        "owned_paths": list(ctx.owned_paths),
    }
    return sha256(canonical_json_bytes(payload)).hexdigest()


def _manifest_payload(pointers: list[dict[str, Any]]) -> dict[str, Any]:
    return {"enabled": True, "records": pointers}


@dataclass(frozen=True)
class ManifestResponse:
    body: bytes
    etag_hex: str
    dropped: tuple[str, ...]


def filtered_manifest(runtime: RegistryRuntime, ctx: Context) -> ManifestResponse:
    """Build the exact response bytes + strong ETag for a filtered manifest."""
    pointers, dropped = select_pointers(runtime, ctx)
    body = canonical_json_bytes(_manifest_payload(pointers))
    return ManifestResponse(body=body, etag_hex=sha256(body).hexdigest(), dropped=tuple(dropped))


def disabled_manifest_bytes() -> bytes:
    """The deterministic disabled projection ``{"enabled":false,"records":[]}``."""
    return canonical_json_bytes({"enabled": False, "records": []})


def empty_manifest_response() -> ManifestResponse:
    """Enabled-but-no-surface projection (registry failed to load), still 200."""
    body = canonical_json_bytes(_manifest_payload([]))
    return ManifestResponse(body=body, etag_hex=sha256(body).hexdigest(), dropped=())


# --------------------------------------------------------------------------- #
# Per-record compact body + honest ETag (ADR-011 §"Per-record endpoint")
# --------------------------------------------------------------------------- #
def _slug_ok(record_id: str) -> bool:
    """Accept only the P1 slug shape; reject traversal, slashes, and junk."""
    return _SLUG_RE.fullmatch(record_id) is not None


def record_body(runtime: RegistryRuntime, record_id: str) -> tuple[str, str] | None:
    """Return (markdown_body, etag_hex) for a record, or ``None`` if unavailable.

    ``None`` (→ generic 404 at the API) covers: malformed id, unknown/invalid/
    drifted record, ``private-local`` access class, an unsafe digest path, or an
    over-budget body. Lookup resolves only through validated registry ids — never
    a direct path join.
    """
    if not _slug_ok(record_id):
        return None
    record = runtime.valid_by_id(record_id)
    if record is None:
        return None
    if record.get("access_class") == "private-local":
        return None
    try:
        raw_projection = crr._record_projection(record, runtime.root)
        body = crr.normalize_digest_projection(raw_projection)
    except crr.ProvenanceError:
        return None
    body_bytes = body.encode("utf-8")
    if len(body_bytes) > MAX_RECORD_BYTES:
        logger.warning(
            "research registry: record %r body is %d bytes (max %d); refusing",
            record_id,
            len(body_bytes),
            MAX_RECORD_BYTES,
        )
        return None
    # The digest is re-read from disk on every call, but ``record`` (and its
    # ``content_hash``) is a snapshot captured at load_runtime() time. If the
    # digest changed on disk in between (a TOCTOU window), the freshly-read body
    # no longer matches that snapshot hash — refuse rather than inventing a new
    # ETag and serving unreconciled bytes. A fresh load_runtime() call would
    # exclude this record entirely; this call must not do less.
    stored = record["content_hash"]
    if crr.compute_content_hash(body) != stored:
        logger.warning(
            "research registry: record %r content changed since load_runtime(); refusing to serve",
            record_id,
        )
        return None
    return body, stored.split(":", 1)[1]


# --------------------------------------------------------------------------- #
# Automatic selected-body helper (ADR-011 §"Budgets and selection helper").
# P3 is its first runtime consumer; implemented + tested here so the budget is
# proven in P2.
# --------------------------------------------------------------------------- #
def select_bodies(runtime: RegistryRuntime, record_ids: list[str]) -> tuple[list[dict[str, str]], list[str]]:
    """Return (selected, dropped_ids); total body bytes ≤ ``MAX_SELECTED_BODIES_BYTES``.

    Preserves request order, never truncates a body, and logs every dropped id
    (unavailable record or budget exhaustion) — never the body content.
    """
    selected: list[dict[str, str]] = []
    dropped: list[str] = []
    total = 0
    for record_id in record_ids:
        result = record_body(runtime, record_id)
        if result is None:
            dropped.append(record_id)
            continue
        body, _etag = result
        size = len(body.encode("utf-8"))
        if total + size > MAX_SELECTED_BODIES_BYTES:
            dropped.append(record_id)
            continue
        total += size
        selected.append({"id": record_id, "body": body})
    if dropped:
        logger.warning(
            "research registry: select_bodies dropped record id(s): %s", ", ".join(dropped)
        )
    return selected, dropped
