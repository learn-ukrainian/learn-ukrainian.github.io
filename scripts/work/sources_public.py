"""Public-only source collectors for the Work projection.

Warm path rules (frozen):
- at most two GitHub list enumerations per repository (issues + PRs)
- no per-item issue/PR/comment/check detail calls
- class-4 only: delegate/active, delegate/tasks, fleet/reviews
- streams only via the public-stripped issues/streams projection
- never read delegate result bodies or sealed review blobs
- never fetch, proxy, or persist private-repository data
"""

from __future__ import annotations

import json
import subprocess
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from scripts.work import SOURCE_PRIVATE, SOURCE_PUBLIC

GH_ENUM_LIMIT = 1000
DELEGATE_TASK_LIMIT = 500
FLEET_REVIEW_PAGE = 100
FLEET_REVIEW_HARD_CAP = 2000
SECTION_TIMEOUT_S = 4.5  # leave headroom under the 5s typed-degradation budget
# Sole public repository for the Work projection. Closed identity: not overridable
# by environment, config, or free-form caller input (privacy boundary).
DEFAULT_PUBLIC_REPOSITORY = "learn-ukrainian/learn-ukrainian.github.io"
# Authoritative repository-attribution fields accepted from a delegate task row.
# Paths, branch names, cwd, worktree_path, and task_id are never used for admission.
DELEGATE_REPOSITORY_ATTR_FIELDS = ("repository_id", "repository")


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _iso_now() -> str:
    return _utc_now().isoformat().replace("+00:00", "Z")


def public_repository_id() -> str:
    """Return the sole public repository identity.

    Closed and non-overridable in production. Environment variables (including
    any historical ``WORK_PUBLIC_REPOSITORY``) and free-form configuration must
    never repoint collectors or the public projection at another repository.
    """
    return DEFAULT_PUBLIC_REPOSITORY


def admit_public_repository_id(repository_id: str | None = None) -> str:
    """Admit only the canonical public repository; fail closed on any other id.

    Returns the sole public repository when *repository_id* is omitted or
    exactly matches. Raises ``ValueError`` for any other value so callers cannot
    silently repoint GitHub enumerations, fleet-review filters, cache identity,
    or emitted projection rows at a private repository.
    """
    allowed = public_repository_id()
    if repository_id is None or repository_id == "":
        return allowed
    if repository_id != allowed:
        raise ValueError(f"public repository_id must be exactly {allowed!r}; got {repository_id!r}")
    return allowed


def _authoritative_delegate_repository(row: dict[str, Any]) -> str | None:
    """Return the single authoritative repository claim from a delegate row.

    Only ``repository_id`` and ``repository`` are accepted. When both are
    present they must agree after strip. Missing, empty, or conflicting claims
    are unclassified (``None``). Callers must never fall back to path, branch,
    cwd, worktree, or task_id inference.
    """
    claimed: list[str] = []
    for attr_name in DELEGATE_REPOSITORY_ATTR_FIELDS:
        raw = row.get(attr_name)
        if raw is None or raw == "":
            continue
        text = str(raw).strip()
        if not text:
            continue
        claimed.append(text)
    if not claimed:
        return None
    unique = set(claimed)
    if len(unique) != 1:
        return None
    return claimed[0]


def admit_delegate_task_row(
    row: dict[str, Any],
    *,
    repository_id: str | None = None,
    trusted_scoped: bool = False,
) -> dict[str, Any] | None:
    """Admit one delegate summary row for the public projection.

    When *trusted_scoped* is false (normalize, mixed inventory, or any
    caller-injected loader), requires an exact canonical public-repository
    claim via the authoritative attribution fields. Foreign, missing,
    ambiguous, or non-dict rows are omitted.

    When *trusted_scoped* is true, use only for the fixed production loader
    path that already filtered by repository before pagination and redacted
    claim fields from the generic summary shape. Missing claims are then
    admitted under that contract and stamped with the closed public singleton.
    Present claims still face defense-in-depth exact-match admission so a
    misbehaving loader cannot pass foreign identity through. Never reads
    result bodies; only copies the public-safe summary allowlist plus Work's
    own admitted repository metadata (never re-emits raw repository_id).
    """
    if not isinstance(row, dict):
        return None
    allowed = admit_public_repository_id(repository_id)
    claimed = _authoritative_delegate_repository(row)
    if claimed is None:
        if not trusted_scoped:
            return None
        admitted = allowed
    else:
        try:
            admitted = admit_public_repository_id(claimed)
        except ValueError:
            return None
        if admitted != allowed:
            return None
    return {
        "task_id": row.get("task_id"),
        "agent": row.get("agent"),
        "model": row.get("model"),
        "effort": row.get("effort"),
        "status": row.get("status"),
        "started_at": row.get("started_at"),
        "duration_s": row.get("duration_s"),
        "age_s": row.get("age_s"),
        "alive": row.get("alive"),
        # Always the closed public singleton — never echo a foreign claim.
        "repository": admitted,
    }


def filter_public_delegate_tasks(
    rows: list[Any] | None,
    *,
    repository_id: str | None = None,
    limit: int | None = None,
    trusted_scoped: bool = False,
    upstream_total: int | None = None,
) -> tuple[list[dict[str, Any]], int, bool]:
    """Filter delegate rows to public-admitted summaries before count/truncation.

    Returns ``(page_rows, public_total, truncated)``.

    *trusted_scoped* matches :func:`admit_delegate_task_row`: use true only for
    the fixed production scoped loaders (claim fields may be absent after
    generic API redaction). Caller-injected loaders must pass false.

    Count contract:
    - Trusted production path with *upstream_total*: preserve that
      repository-scoped public total (never recompute it from the capped page).
      When *limit* is set, ``truncated = total > admitted_page_count`` so a
      501-public / 500-row page reports total 501 and truncated true. When
      *limit* is None (complete active inventory), never invent truncation.
    - Injected/untrusted loaders (or trusted without upstream total): derive
      total/truncation only from rows that pass public admission; never trust
      a supplied total (dishonest totals and private rows must not influence
      the public count).
    """
    allowed = admit_public_repository_id(repository_id)
    admitted: list[dict[str, Any]] = []
    for row in rows or []:
        summary = admit_delegate_task_row(row, repository_id=allowed, trusted_scoped=trusted_scoped)
        if summary is not None:
            admitted.append(summary)

    admitted_page_count = len(admitted)
    if trusted_scoped and upstream_total is not None:
        try:
            total = int(upstream_total)
        except (TypeError, ValueError):
            total = admitted_page_count
        if total < admitted_page_count:
            total = admitted_page_count
        if limit is None:
            # Complete upstream path (active) — do not invent truncation.
            return admitted, total, False
        cap = max(0, int(limit))
        page = admitted[:cap]
        # Truncation is relative to the authoritative scoped total vs the
        # admitted page actually returned, not a recompute of page length alone.
        truncated = total > len(page)
        return page, total, truncated

    # Untrusted / no upstream total: count only admitted rows.
    total = admitted_page_count
    if limit is None:
        return admitted, total, False
    cap = max(0, int(limit))
    truncated = total > cap
    return admitted[:cap], total, truncated


@dataclass
class SectionResult:
    name: str
    status: str
    payload: Any = None
    reason: str | None = None
    age_s: float | None = 0.0
    observed_at: str | None = field(default_factory=_iso_now)
    count: int = 0
    truncated: bool = False


def _run_gh(args: list[str], timeout_s: float = SECTION_TIMEOUT_S) -> tuple[int, str, str]:
    try:
        proc = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=timeout_s,
            check=False,
        )
        return proc.returncode, proc.stdout, proc.stderr
    except subprocess.TimeoutExpired as exc:
        return 124, "", f"TimeoutExpired after {exc.timeout}s"
    except (FileNotFoundError, PermissionError, OSError) as exc:
        return 127, "", f"{type(exc).__name__}: {exc}"


def fetch_open_issues(
    repository_id: str | None = None,
    *,
    limit: int = GH_ENUM_LIMIT,
    runner: Callable[[list[str], float], tuple[int, str, str]] | None = None,
) -> SectionResult:
    """One open-issue list enumeration (no per-item detail calls).

    *repository_id* is admitted against the closed public identity before any
    runner or GitHub invocation. Foreign, cased, suffixed, or whitespace-padded
    ids fail closed and never reach ``gh``.
    """
    repo = admit_public_repository_id(repository_id)
    run = runner or _run_gh
    code, stdout, stderr = run(
        [
            "gh",
            "issue",
            "list",
            "--repo",
            repo,
            "--state",
            "open",
            "--limit",
            str(limit),
            "--json",
            "number,title,labels,body,createdAt,updatedAt,assignees,url,state",
        ],
        SECTION_TIMEOUT_S,
    )
    if code == 124:
        return SectionResult("issues", "timeout", reason="gh_issue_list_timeout")
    if code != 0:
        return SectionResult(
            "issues",
            "unavailable",
            reason=(stderr.strip() or "gh_issue_list_failed")[:200],
        )
    try:
        payload = json.loads(stdout or "[]")
    except json.JSONDecodeError as exc:
        return SectionResult("issues", "degraded", reason=f"invalid_gh_json:{exc}")
    if not isinstance(payload, list):
        return SectionResult("issues", "degraded", reason="gh_issue_list_not_list")
    truncated = len(payload) >= limit
    return SectionResult(
        "issues",
        "truncated" if truncated else "ok",
        payload=payload,
        count=len(payload),
        truncated=truncated,
    )


def fetch_open_prs(
    repository_id: str | None = None,
    *,
    limit: int = GH_ENUM_LIMIT,
    runner: Callable[[list[str], float], tuple[int, str, str]] | None = None,
) -> SectionResult:
    """One open-PR list enumeration with rollup fields only (no detail fan-out).

    *repository_id* is admitted against the closed public identity before any
    runner or GitHub invocation. Foreign, cased, suffixed, or whitespace-padded
    ids fail closed and never reach ``gh``.
    """
    repo = admit_public_repository_id(repository_id)
    run = runner or _run_gh
    code, stdout, stderr = run(
        [
            "gh",
            "pr",
            "list",
            "--repo",
            repo,
            "--state",
            "open",
            "--limit",
            str(limit),
            "--json",
            "number,title,state,isDraft,headRefName,headRefOid,updatedAt,createdAt,"
            "reviewDecision,statusCheckRollup,mergeStateStatus,labels,assignees,url",
        ],
        SECTION_TIMEOUT_S,
    )
    if code == 124:
        return SectionResult("prs", "timeout", reason="gh_pr_list_timeout")
    if code != 0:
        return SectionResult(
            "prs",
            "unavailable",
            reason=(stderr.strip() or "gh_pr_list_failed")[:200],
        )
    try:
        payload = json.loads(stdout or "[]")
    except json.JSONDecodeError as exc:
        return SectionResult("prs", "degraded", reason=f"invalid_gh_json:{exc}")
    if not isinstance(payload, list):
        return SectionResult("prs", "degraded", reason="gh_pr_list_not_list")
    truncated = len(payload) >= limit
    return SectionResult(
        "prs",
        "truncated" if truncated else "ok",
        payload=payload,
        count=len(payload),
        truncated=truncated,
    )


_ISSUE_STATE_CACHE: dict[tuple[str, int], tuple[float, str | None]] = {}
_ISSUE_STATE_CACHE_TTL_S = 300.0


def clear_issue_state_cache() -> None:
    """Clear the batched issue state cache (for tests)."""
    _ISSUE_STATE_CACHE.clear()


def fetch_issue_states_batched(
    numbers: list[int] | set[int],
    repository_id: str | None = None,
    *,
    runner: Callable[[list[str], float], tuple[int, str, str]] | None = None,
    timeout_s: float = SECTION_TIMEOUT_S,
    cache_ttl_s: float = _ISSUE_STATE_CACHE_TTL_S,
) -> dict[str, str]:
    """Fetch lifecycles for specific issue numbers in one batched GraphQL query.

    Warm-path compliant: single request using GraphQL field aliases; never
    enumerates or loops per item.

    Returns a mapping of `{work_id: "closed" | "open", str(number): "closed" | "open"}`.
    If the lookup fails, times out, or an issue is not found, it is omitted
    from the returned mapping so callers conservatively treat it as an unknown blocker.
    """
    if not numbers:
        return {}
    repo = admit_public_repository_id(repository_id)
    owner, name = repo.split("/", 1)

    unique_numbers = sorted({int(n) for n in numbers if int(n) > 0})
    if not unique_numbers:
        return {}

    from scripts.work.relations import issue_work_id

    now = time.monotonic()
    states: dict[str, str] = {}
    needed: list[int] = []

    # If runner is not custom injected, check in-memory cache
    if runner is None and cache_ttl_s > 0:
        for num in unique_numbers:
            cached = _ISSUE_STATE_CACHE.get((repo, num))
            if cached is not None:
                cached_at, cached_state = cached
                if now - cached_at < cache_ttl_s:
                    if cached_state is not None:
                        states[issue_work_id(repo, num)] = cached_state
                        states[str(num)] = cached_state
                    continue
            needed.append(num)
    else:
        needed = list(unique_numbers)

    if not needed:
        return states

    aliases = "\n".join(
        f"    i{num}: issue(number: {num}) {{ number state }}"
        for num in needed
    )
    query = (
        f"query {{\n"
        f"  repository(owner: {json.dumps(owner)}, name: {json.dumps(name)}) {{\n"
        f"{aliases}\n"
        f"  }}\n"
        f"}}"
    )

    run = runner or _run_gh
    code, stdout, _stderr = run(
        ["gh", "api", "graphql", "-f", f"query={query}"],
        timeout_s,
    )
    if code == 124 or not stdout:
        return states

    try:
        payload = json.loads(stdout)
    except (json.JSONDecodeError, TypeError):
        return states

    if not isinstance(payload, dict):
        return states

    data = payload.get("data")
    if not isinstance(data, dict):
        return states

    repo_data = data.get("repository")
    if not isinstance(repo_data, dict):
        return states

    for num in needed:
        entry = repo_data.get(f"i{num}")
        if isinstance(entry, dict) and "state" in entry:
            state_str = str(entry["state"]).lower()
            states[issue_work_id(repo, num)] = state_str
            states[str(num)] = state_str
            if runner is None and cache_ttl_s > 0:
                _ISSUE_STATE_CACHE[(repo, num)] = (now, state_str)
        else:
            if runner is None and cache_ttl_s > 0:
                _ISSUE_STATE_CACHE[(repo, num)] = (now, None)

    return states


def registry_stream_names(report: dict[str, Any] | None) -> frozenset[str]:
    """Stream keys admitted by the public registry map in a streams payload."""
    if not isinstance(report, dict):
        return frozenset()
    registry = report.get("streams")
    if not isinstance(registry, dict):
        return frozenset()
    return frozenset(str(k) for k in registry if isinstance(k, str) and k)


def allowlist_stream_names(names: Any, known: frozenset[str]) -> list[str]:
    """Return sorted registry-known stream names; empty known → fail closed."""
    if not known or not isinstance(names, list):
        return []
    return sorted({str(s) for s in names if isinstance(s, str) and s and s in known})


def allowlist_open_stream_membership(membership: Any, known: frozenset[str]) -> dict[str, list[str]]:
    """Re-validate a pre-set / derived issue→streams map against the registry."""
    if not isinstance(membership, dict) or not known:
        return {}
    out: dict[str, list[str]] = {}
    for key, names in membership.items():
        try:
            number = int(key)
        except (TypeError, ValueError):
            continue
        clean = allowlist_stream_names(names, known)
        if clean:
            out[str(number)] = clean
    return out


def public_open_stream_membership(report: dict[str, Any]) -> dict[str, list[str]]:
    """Public-safe issue→stream-names map for OPEN issues only (#6880 / #6890).

    Derived from the ADR-011 P4 private index BEFORE it is stripped. Keeps only
    stream NAMES that also appear in the public registry ``streams`` key — derive
    time re-allowlists so a typo or private-index drift cannot mint unknown
    lanes into the projection. Epic ownership, closed issues, and the
    via/uniqueness proofs never leave the private cache.
    """
    known = registry_stream_names(report)
    membership = report.get("effective_membership")
    open_numbers = report.get("open_issue_numbers")
    if not known or not isinstance(membership, dict) or not isinstance(open_numbers, list):
        return {}
    open_set: set[int] = set()
    for n in open_numbers:
        try:
            open_set.add(int(n))
        except (TypeError, ValueError):
            continue
    out: dict[str, list[str]] = {}
    for key, entry in membership.items():
        try:
            number = int(key)
        except (TypeError, ValueError):
            continue
        if number not in open_set or not isinstance(entry, dict):
            continue
        streams = allowlist_stream_names(entry.get("streams"), known)
        if streams:
            out[str(number)] = streams
    return out


def _admit_open_stream_membership(payload: dict[str, Any]) -> dict[str, list[str]]:
    """Derive-or-revalidate membership; always overwrite untrusted pre-sets (#6890)."""
    known = registry_stream_names(payload)
    derived = public_open_stream_membership(payload)
    if derived:
        return derived
    return allowlist_open_stream_membership(payload.get("open_stream_membership"), known)


def fetch_streams_projection(
    loader: Callable[[], dict[str, Any]] | None = None,
) -> SectionResult:
    """Consume the complete public streams projection (private keys stripped)."""

    def _default_loader() -> dict[str, Any]:
        from scripts.api.issues_router import _strip_private_index, _with_refresh
        from scripts.orchestration import issue_stream_audit as audit

        report = audit.read_cache(max_age_s=3600)
        stale = None if report is not None else audit.read_cache(max_age_s=7 * 24 * 3600)
        state = audit.schedule_refresh(force=False) if report is None else audit.read_refresh_state()
        if report is not None:
            payload = _strip_private_index(report)
            membership = public_open_stream_membership(report)
            status = "ok"
        elif stale is not None:
            payload = {**_strip_private_index(stale), "stale": True}
            membership = public_open_stream_membership(stale)
            status = "stale"
        else:
            payload = {"status": "no-cache", "ok": None}
            membership = {}
            status = "unavailable"
        if membership:
            payload["open_stream_membership"] = membership
        else:
            payload.pop("open_stream_membership", None)
        return {"_status": status, **_with_refresh(payload, state)}

    try:
        payload = (loader or _default_loader)()
    except Exception as exc:
        return SectionResult("streams", "unavailable", reason=f"streams_error:{type(exc).__name__}")

    status = str(payload.pop("_status", "ok"))
    # Injected loaders may hand up a raw audit report; derive the public-safe
    # membership map before the hard gate drops the private index below.
    # Always re-validate pre-set open_stream_membership against the registry
    # (residual #2) — never leave an unallowlisted map in the public payload.
    membership = _admit_open_stream_membership(payload)
    # Privacy hard gate: never forward private index keys even if a loader errs.
    from scripts.orchestration.issue_stream_audit import PRIVATE_CACHE_KEYS

    for key in PRIVATE_CACHE_KEYS:
        payload.pop(key, None)
    if membership:
        payload["open_stream_membership"] = membership
    else:
        payload.pop("open_stream_membership", None)
    if payload.get("stale"):
        status = "stale"
    if payload.get("error") or payload.get("status") == "no-cache":
        status = "unavailable" if status == "ok" else status
    age_s = None
    generated = payload.get("generated_at")
    if isinstance(generated, (int, float)):
        age_s = max(0.0, time.time() - float(generated))
    return SectionResult(
        "streams",
        status,
        payload=payload,
        reason=str(payload.get("error") or "") or None,
        age_s=age_s,
        count=int(payload.get("open_total") or 0),
    )


def fetch_delegate_active(
    loader: Callable[[str], dict[str, Any]] | None = None,
    *,
    repository_id: str | None = None,
) -> SectionResult:
    """Summarize active delegate tasks for the exact public repository only.

    The admitted public repository is passed into the production loader so
    filtering and total construction happen **before** any page budget is
    consumed. Trust is selected from the call shape, not payload content:
    ``loader is None`` uses the fixed production path
    (``active_delegate_tasks(repository=allowed)``), which already filtered
    upstream and redacts repository fields; those claim-less redacted rows
    may be stamped with Work's admitted public singleton under
    ``trusted_scoped=True``. Any caller-supplied/injected loader is untrusted
    (``trusted_scoped=False``): every retained row must carry an exact
    authoritative public ``repository`` / ``repository_id`` claim (with the
    existing ambiguity/foreign checks). Present foreign claims are always
    dropped. Paths/branches/task IDs are never used for repository
    attribution. Bodies and result files are never read. Work stamps only
    its own admitted repository metadata on retained rows; generic delegate
    summaries never re-emit repository identity.
    """
    allowed = admit_public_repository_id(repository_id)
    # Provenance is unforgeable via payload shape: only the fixed production
    # path (no injectable loader) is trusted_scoped.
    trusted_scoped = loader is None

    def _default_active(repository: str) -> dict[str, Any]:
        from scripts.api.delegate_router import active_delegate_tasks

        return active_delegate_tasks(repository=repository)

    try:
        page_fn = loader if loader is not None else _default_active
        payload = page_fn(allowed)
    except Exception as exc:
        return SectionResult(
            "delegate_active",
            "unavailable",
            reason=f"delegate_active_error:{type(exc).__name__}",
        )
    tasks = payload.get("tasks") if isinstance(payload, dict) else None
    if not isinstance(tasks, list):
        return SectionResult("delegate_active", "degraded", reason="delegate_active_shape")
    # Active inventory is complete (no page budget). Preserve trusted upstream
    # scoped total; never invent truncation. Injected loaders derive total only
    # from admitted rows.
    upstream_total: int | None = None
    if trusted_scoped and isinstance(payload, dict) and payload.get("total") is not None:
        try:
            upstream_total = int(payload["total"])
        except (TypeError, ValueError):
            upstream_total = None
    summary, total, truncated = filter_public_delegate_tasks(
        tasks,
        repository_id=allowed,
        trusted_scoped=trusted_scoped,
        upstream_total=upstream_total,
    )
    return SectionResult(
        "delegate_active",
        "ok",
        payload={"total": total, "tasks": summary},
        count=total,
        truncated=truncated,
    )


def fetch_delegate_tasks(
    loader: Callable[[str], dict[str, Any]] | None = None,
    *,
    repository_id: str | None = None,
) -> SectionResult:
    """Summarize delegate task inventory for the exact public repository only.

    The admitted public repository is passed into the production loader so
    repository filtering, total, and limit slicing happen **before** the
    public enumeration cap is applied. Private/unclassified volume therefore
    cannot starve public rows or inflate totals/truncation. Trust is selected
    from the call shape, not payload content: ``loader is None`` uses the
    fixed production path (``list_delegate_tasks(..., repository=allowed)``),
    which already filtered upstream and redacts repository fields; those
    claim-less redacted rows may be stamped under ``trusted_scoped=True`` and
    the authoritative scoped public ``total`` is preserved
    (``truncated = total > admitted_page_count``). Any caller-supplied/injected
    loader is untrusted: every retained row must carry an exact authoritative
    public ``repository`` / ``repository_id`` claim (with ambiguity/foreign
    checks), and total/truncation are derived only from admitted rows (never
    from a supplied total). Never reads result bodies. Work stamps only its
    own admitted repository metadata; generic delegate summaries never re-emit
    repository identity.
    """
    allowed = admit_public_repository_id(repository_id)
    # Provenance is unforgeable via payload shape: only the fixed production
    # path (no injectable loader) is trusted_scoped.
    trusted_scoped = loader is None

    def _default_tasks(repository: str) -> dict[str, Any]:
        from scripts.api.delegate_router import list_delegate_tasks

        return list_delegate_tasks(status="all", limit=DELEGATE_TASK_LIMIT, repository=repository)

    try:
        page_fn = loader if loader is not None else _default_tasks
        payload = page_fn(allowed)
    except Exception as exc:
        return SectionResult(
            "delegate_tasks",
            "unavailable",
            reason=f"delegate_tasks_error:{type(exc).__name__}",
        )
    tasks = payload.get("tasks") if isinstance(payload, dict) else None
    if not isinstance(tasks, list):
        return SectionResult("delegate_tasks", "degraded", reason="delegate_tasks_shape")
    # Trusted production: keep the scoped loader's public total. Injected
    # loaders: recompute total from admitted rows only (ignore payload total).
    upstream_total: int | None = None
    if trusted_scoped and isinstance(payload, dict) and payload.get("total") is not None:
        try:
            upstream_total = int(payload["total"])
        except (TypeError, ValueError):
            upstream_total = None
    summary, total, truncated = filter_public_delegate_tasks(
        tasks,
        repository_id=allowed,
        limit=DELEGATE_TASK_LIMIT,
        trusted_scoped=trusted_scoped,
        upstream_total=upstream_total,
    )
    return SectionResult(
        "delegate_tasks",
        "truncated" if truncated else "ok",
        payload={"total": total, "tasks": summary},
        count=len(summary),
        truncated=truncated,
    )


def fetch_fleet_reviews(
    loader: Callable[[int, int, str], dict[str, Any]] | None = None,
    *,
    repository_id: str | None = None,
) -> SectionResult:
    """Page fleet review summaries for the exact public repository only.

    The admitted public repository is passed into the loader so filtering,
    COUNT, and pagination happen *before* the hard scan cap. Injectable
    loaders must honor ``repository`` the same way (pre-pagination filter).

    Never open sealed verdict blobs. Rows whose ``repository`` is missing or
    not exactly the canonical public repository are dropped (defense in depth;
    no suffix match).
    """
    allowed = admit_public_repository_id(repository_id)

    def _default_page(limit: int, offset: int, repository: str) -> dict[str, Any]:
        from scripts.api.fleet_router import fleet_reviews

        # SQL WHERE + count + limit all see the exact public singleton.
        return fleet_reviews(limit=limit, offset=offset, repository=repository)

    page_fn = loader or _default_page
    items: list[dict[str, Any]] = []
    total = 0
    offset = 0
    raw_seen = 0
    try:
        while offset < FLEET_REVIEW_HARD_CAP:
            page = page_fn(FLEET_REVIEW_PAGE, offset, allowed)
            if not isinstance(page, dict):
                return SectionResult("fleet_reviews", "degraded", reason="fleet_reviews_shape")
            batch = page.get("reviews") or page.get("items") or []
            if not isinstance(batch, list):
                return SectionResult("fleet_reviews", "degraded", reason="fleet_reviews_items")
            # Prefer the repository-scoped total from the loader / SQL count.
            total = int(page.get("total") or total or len(batch))
            for row in batch:
                if not isinstance(row, dict):
                    continue
                raw_seen += 1
                if str(row.get("repository") or "") != allowed:
                    # Defense in depth: a misbehaving loader must not leak foreign rows.
                    continue
                # Explicit allowlist — sealed blobs never enter the projection.
                items.append(
                    {
                        "review_id": row.get("review_id"),
                        "repository": allowed,
                        "pr_number": row.get("pr_number"),
                        "head_sha": row.get("head_sha"),
                        "gate_kind": row.get("gate_kind"),
                        "state": row.get("state"),
                        "created_at": row.get("created_at"),
                        "attempt_count": row.get("attempt_count"),
                        "latest_attempt_state": row.get("latest_attempt_state"),
                        "publication_count": row.get("publication_count"),
                        "sealed_verdict_available": bool(row.get("sealed_verdict_available")),
                    }
                )
            if not batch or raw_seen >= total or len(batch) < FLEET_REVIEW_PAGE:
                break
            offset += FLEET_REVIEW_PAGE
    except Exception as exc:
        return SectionResult(
            "fleet_reviews",
            "unavailable",
            reason=f"fleet_reviews_error:{type(exc).__name__}",
        )
    # Truncation is relative to the repository-filtered total / scan budget.
    # Private volume must not appear in total or force truncated=true.
    truncated = total > raw_seen
    return SectionResult(
        "fleet_reviews",
        "truncated" if truncated else "ok",
        payload={"total": len(items), "reviews": items},
        count=len(items),
        truncated=truncated,
    )


def private_capability_seam() -> dict[str, Any]:
    """Truthful optional private-source capability (public server never fetches it)."""
    return {
        "source_id": SOURCE_PRIVATE,
        "available": False,
        "schema_version": "work-projection.v1",
        "schema_digest_sha256": None,
        "public_schema_commit": None,
        "endpoint": None,
        "capabilities": [],
        "redaction": "allowlist_v1",
        "reason_if_unavailable": "not_configured",
    }


def collect_public_sections(
    *,
    repository_id: str | None = None,
    gh_runner: Callable[[list[str], float], tuple[int, str, str]] | None = None,
    streams_loader: Callable[[], dict[str, Any]] | None = None,
    delegate_active_loader: Callable[[str], dict[str, Any]] | None = None,
    delegate_tasks_loader: Callable[[str], dict[str, Any]] | None = None,
    fleet_reviews_loader: Callable[[int, int, str], dict[str, Any]] | None = None,
    max_workers: int = 6,
) -> dict[str, SectionResult]:
    """Collect all public sections with independent typed degradation."""
    repo = admit_public_repository_id(repository_id)
    jobs: dict[str, Callable[[], SectionResult]] = {
        "issues": lambda: fetch_open_issues(repo, runner=gh_runner),
        "prs": lambda: fetch_open_prs(repo, runner=gh_runner),
        "streams": lambda: fetch_streams_projection(loader=streams_loader),
        "delegate_active": lambda: fetch_delegate_active(loader=delegate_active_loader, repository_id=repo),
        "delegate_tasks": lambda: fetch_delegate_tasks(loader=delegate_tasks_loader, repository_id=repo),
        "fleet_reviews": lambda: fetch_fleet_reviews(loader=fleet_reviews_loader, repository_id=repo),
    }
    results: dict[str, SectionResult] = {}
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {pool.submit(fn): name for name, fn in jobs.items()}
        for future in as_completed(futures):
            name = futures[future]
            try:
                results[name] = future.result(timeout=SECTION_TIMEOUT_S + 0.5)
            except Exception as exc:
                results[name] = SectionResult(
                    name,
                    "timeout" if "timeout" in type(exc).__name__.lower() else "unavailable",
                    reason=f"{name}_collect_error:{type(exc).__name__}",
                )
    for name in jobs:
        results.setdefault(
            name,
            SectionResult(name, "unavailable", reason=f"{name}_missing"),
        )
    return results


def public_source_envelope(sections: dict[str, SectionResult]) -> dict[str, Any]:
    """Build the public-monitor source envelope from section results."""
    section_meta: dict[str, Any] = {}
    worst = "ok"
    rank = {
        "ok": 0,
        "truncated": 1,
        "stale": 2,
        "degraded": 3,
        "timeout": 4,
        "permission_denied": 5,
        "unavailable": 6,
        "unsupported_version": 7,
    }
    ages: list[float] = []
    for name, section in sections.items():
        meta: dict[str, Any] = {"status": section.status, "count": section.count}
        if section.reason:
            meta["reason"] = section.reason
        if section.age_s is not None:
            meta["age_s"] = section.age_s
            ages.append(float(section.age_s))
        section_meta[name] = meta
        if rank.get(section.status, 0) > rank.get(worst, 0):
            worst = section.status
    issues = sections.get("issues")
    prs = sections.get("prs")
    core_ok = (
        issues is not None
        and issues.status in {"ok", "truncated"}
        and prs is not None
        and prs.status in {"ok", "truncated"}
    )
    source_status = "degraded" if core_ok and rank.get(worst, 0) > rank.get("degraded", 0) else worst
    return {
        "source_id": SOURCE_PUBLIC,
        "status": source_status,
        "freshness": {
            "observed_at": _iso_now(),
            "age_s": max(ages) if ages else 0.0,
        },
        "capabilities": {"mutation": False, "private_fields": False},
        "truncation": {
            "issues": bool(issues and issues.truncated),
            "prs": bool(prs and prs.truncated),
            "limit": GH_ENUM_LIMIT,
        },
        "sections": section_meta,
    }


def private_source_envelope() -> dict[str, Any]:
    return {
        "source_id": SOURCE_PRIVATE,
        "status": "unavailable",
        "freshness": {"observed_at": None, "age_s": None},
        "capabilities": {"mutation": False, "private_fields": False},
        "truncation": {"issues": False, "prs": False, "limit": GH_ENUM_LIMIT},
        "sections": {},
        "reason": "not_configured",
    }
