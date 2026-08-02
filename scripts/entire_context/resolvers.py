"""Explicit, local-only typed resolvers for context-link bootstrap and re-verify.

Every resolver maps one exact, caller-supplied identifier to a body-free
canonical projection: a deterministic digest over public metadata, never over
subjects, prompts, transcripts, or any composed text. Resolution is fully
local — read-only ``git`` plumbing, the existing body-free ACP terminal
receipt verifier, the existing read-only rollover-registry verifier, and
read-only SQLite over existing canonical Fleet/Monitor caches — and fails
closed: a source that cannot be verified raises :class:`ResolutionError` with
a machine reason and nothing is fabricated.

Real resolvers in this slice:

- ``git_commit`` — an exact full commit SHA in a local repository resolves to
  parents, touched paths, committer timestamp, and author (public metadata,
  no commit subject/body).
- ``acp_conversation`` — an exact ACP conversation ID resolves through
  :func:`scripts.agent_runtime.acpx_discuss.verify_discussion_receipt` to
  body-free terminal metadata with ``content_included: false``.
- ``rollover`` — an exact ``(agent, lineage_id, rollover_id)`` triple resolves
  through
  :func:`scripts.orchestration.task_family.rollover_registry.load_record` to a
  strict body-free projection of the registry record: schema/key, lifecycle
  state/boundary, sub-lifecycle states, ``cleanup_authorized``, timestamps, and
  non-body routing (stream epic, issue number, lifecycle state). Titles,
  task/thread IDs, reasons, filesystem paths, history, receipts, evidence, and
  nested native/readback payloads are excluded.
- ``github_issue`` — an exact issue number resolves against the fresh local
  ``batch_state/issue_stream_audit.json`` cache. Projects issue number and
  unique stream/epic membership only. Cache freshness is verification evidence,
  never locator identity; no issue body or title is read.
- ``github_pr`` — an exact ``(repository, pr_number, head_sha, gate_kind)``
  quadruple resolves against a completed formal-review job plus its durable
  ``github_publications`` row in the Fleet Comms SQLite store, and verifies the
  head commit exists in local Git. Projects repository, PR number, head SHA,
  gate/state, and publication timestamp/context only.
- ``formal_review`` — an exact review ID resolves against a completed
  formal-review job in the Fleet Comms SQLite store, loads and hash-checks the
  sealed-verdict blob read-only, parses it with the existing strict parser, and
  re-checks job binding. Projects review ID, repository, PR, head SHA, gate,
  state, verdict token, model/family/harness, attempt count/completion states,
  and publication state only. Never exposes artifact IDs or payload
  text/findings.
- ``fleet_receipt`` — an exact request ID resolves against one canonical
  ``requests`` row in the Fleet Comms SQLite store. Projects request ID,
  requested/resolved recipient, terminal state, completion state, and
  expiry/created/updated timestamps only. Never reads or exposes invocation
  JSON or message bodies.
- ``monitor_run`` — an exact lease token resolves against a terminal
  ``agent_leases`` row in the Agent Process Monitor SQLite store. Projects
  lease ID, agent ID, task name, terminal status, created/last-heartbeat
  timestamps, and a bounded RAM bucket only. Excludes PID and process-create
  time.

All SQLite reads use URI ``mode=ro``; no migrations, WAL changes, pruning, or
service calls are performed.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import sqlite3
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from scripts.agent_runtime.acpx_discuss import (
    AcpxDiscussionError,
    AcpxDiscussionNotFoundError,
    verify_discussion_receipt,
)
from scripts.fleet_comms.review_publication import parse_sealed_verdict_payload
from scripts.orchestration.task_family.rollover_registry import (
    load_record as load_rollover_record,
)
from scripts.orchestration.task_family.rollover_registry import (
    record_path as rollover_record_path,
)

from .model import (
    GIT_SHA_RE,
    ROLLOVER_NAMESPACE,
    ContextLink,
    LinkKind,
    SchemaError,
    VerificationEvidence,
    VerificationStatus,
    canonical_json,
    isoformat_z,
    parse_timestamp,
    sha256_text,
    utc_now,
    validate_facets,
    validate_identity,
)
from .paths import shared_repository_root

GIT_TIMEOUT_SECONDS = 30

ACP_CONVERSATION_ID_RE = re.compile(r"^conversation_[0-9a-f]{32}$")
GITHUB_REPOSITORY_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*/[A-Za-z0-9][A-Za-z0-9._-]*$")
SHA256_HEX_RE = re.compile(r"^[0-9a-f]{64}$")
GITHUB_ORIGIN_RE = re.compile(
    r"^(?:git@github\.com:|ssh://git@github\.com/|https://github\.com/)"
    r"(?P<repository>[A-Za-z0-9][A-Za-z0-9._-]*/[A-Za-z0-9][A-Za-z0-9._-]*?)(?:\.git)?/?$"
)

#: Kinds with a real local resolver in this slice. Everything else fails closed.
SUPPORTED_RESOLVER_KINDS = frozenset(
    {
        LinkKind.GIT_COMMIT,
        LinkKind.ACP_CONVERSATION,
        LinkKind.ROLLOVER,
        LinkKind.GITHUB_ISSUE,
        LinkKind.GITHUB_PR,
        LinkKind.FORMAL_REVIEW,
        LinkKind.FLEET_RECEIPT,
        LinkKind.MONITOR_RUN,
    }
)

#: Body-free machine reasons a resolution or re-verification can end with.
REASON_SOURCE_MISSING = "source_missing"
REASON_DIGEST_MISMATCH = "digest_mismatch"
REASON_PARTIAL_TERMINAL = "partial_terminal"
REASON_UNSUPPORTED_KIND = "unsupported_kind"
REASON_RESOLUTION_ERROR = "resolution_error"
REASON_PUBLICATION_MISSING = "publication_missing"

#: Maximum age (seconds) for the issue-stream-audit cache before it is stale.
MAX_ISSUE_CACHE_AGE_SECONDS = 3600
#: Maximum acceptable clock skew (cache generated_at ahead of wall-clock).
MAX_CACHE_SKEW_SECONDS = 300

#: Terminal request states in the Fleet Comms ``requests`` table.
_TERMINAL_REQUEST_STATES = frozenset(
    {"complete", "incomplete", "failed", "expired", "dead_lettered"}
)
_REQUEST_STATES = frozenset({"queued", "running", *_TERMINAL_REQUEST_STATES})

#: Terminal lease statuses in the Agent Process Monitor ``agent_leases`` table.
_TERMINAL_LEASE_STATUSES = frozenset({"RELEASED", "EXPIRED"})
_COMPLETION_STATES = frozenset({"complete", "length_limited", "transport_incomplete", "failed"})
_REQUEST_COMPLETION_STATES = frozenset({*_COMPLETION_STATES, "unknown"})
_FORMAL_VERDICTS = frozenset({"APPROVED", "CHANGES_REQUESTED", "BLOCKED"})
_FORMAL_JOB_STATES = frozenset({"open", "running", "complete", "failed", "blocked"})
_EARLIEST_TIMESTAMP = 946_684_800  # 2000-01-01T00:00:00Z
_LATEST_TIMESTAMP = 4_102_444_800  # 2100-01-01T00:00:00Z


class ResolutionError(ValueError):
    """Fail-closed resolver outcome with a body-free machine reason."""

    def __init__(self, reason: str, detail: str = "") -> None:
        super().__init__(reason if not detail else f"{reason}: {detail}")
        self.reason = reason


@dataclass(frozen=True, slots=True)
class Resolution:
    """One verified body-free canonical projection plus admission evidence."""

    link: ContextLink
    verification: VerificationEvidence
    excerpt: dict[str, Any]


def _token_bucket(token_count: int | None) -> str:
    if token_count is None or token_count <= 0:
        return "none"
    if token_count < 10_000:
        return "small"
    if token_count < 100_000:
        return "medium"
    return "large"


# ── git_commit ───────────────────────────────────────────────────────────────


def _run_git(repo: Path, *args: str) -> str:
    """Run one read-only git plumbing command; fail closed on any error."""
    try:
        completed = subprocess.run(
            ["git", "-C", str(repo), *args],
            capture_output=True,
            text=True,
            check=False,
            timeout=GIT_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ResolutionError(REASON_RESOLUTION_ERROR, f"git unavailable: {type(exc).__name__}") from exc
    if completed.returncode != 0:
        raise ResolutionError(REASON_SOURCE_MISSING, "git object or repository not resolvable")
    return completed.stdout


def _origin_url(repo: Path) -> str | None:
    try:
        completed = subprocess.run(
            ["git", "-C", str(repo), "config", "--get", "remote.origin.url"],
            capture_output=True,
            text=True,
            check=False,
            timeout=GIT_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if completed.returncode != 0:
        return None
    return completed.stdout.strip() or None


def _origin_namespace(repo: Path) -> str | None:
    url = _origin_url(repo)
    if url is None:
        return None
    match = re.search(r"[:/]([A-Za-z0-9._-]+/[A-Za-z0-9._-]+?)(?:\.git)?$", url)
    if match is None:
        return None
    return f"git:{match.group(1)}"


def git_commit_projection(repo: Path, sha: str) -> dict[str, Any]:
    """Resolve one exact commit SHA to its body-free canonical projection.

    The projection covers the SHA, parent SHAs, touched paths, and committer
    timestamp — never the commit subject or body.
    """
    if not GIT_SHA_RE.fullmatch(sha):
        raise ResolutionError(REASON_RESOLUTION_ERROR, "identifier is not a full 40-hex commit SHA")
    repo = Path(repo)
    object_type = _run_git(repo, "cat-file", "-t", sha).strip()
    if object_type != "commit":
        raise ResolutionError(REASON_SOURCE_MISSING, "git object is not a commit")
    header = _run_git(repo, "show", "-s", "--format=%P%n%ct%n%an", sha)
    lines = header.split("\n")
    if len(lines) < 3:
        raise ResolutionError(REASON_RESOLUTION_ERROR, "unexpected git show output shape")
    parent_order = [parent for parent in lines[0].split() if parent]
    parents = sorted(parent_order)
    try:
        commit_ts = int(lines[1].strip())
    except ValueError as exc:
        raise ResolutionError(REASON_RESOLUTION_ERROR, "unparseable commit timestamp") from exc
    author = lines[2].strip()
    if parents:
        # A commit's public touched-path projection is its change relative to
        # the first parent. This is explicit for merges; plain `diff-tree SHA`
        # suppresses merge diffs and would silently emit an empty path set.
        touched = _run_git(
            repo,
            "diff-tree",
            "--no-commit-id",
            "--name-only",
            "-r",
            parent_order[0],
            sha,
        )
    else:
        touched = _run_git(repo, "diff-tree", "--root", "--no-commit-id", "--name-only", "-r", sha)
    touched_paths = sorted({path for path in touched.split("\n") if path.strip()})
    return {
        "schema": "git-commit-projection.v1",
        "sha": sha,
        "parents": parents,
        "touched_paths": touched_paths,
        "commit_ts": commit_ts,
        "author": author,
    }


def git_projection_digest(projection: dict[str, Any]) -> str:
    """Deterministic digest over the body-free commit projection only."""
    return "sha256:" + sha256_text(
        canonical_json(
            {
                "schema": projection["schema"],
                "sha": projection["sha"],
                "parents": projection["parents"],
                "touched_paths": projection["touched_paths"],
                "commit_ts": projection["commit_ts"],
                "author": projection["author"],
            }
        )
    )


def resolve_git_commit(
    sha: str,
    *,
    repo: Path,
    namespace: str | None = None,
    now: datetime | None = None,
) -> Resolution:
    """Resolve an exact commit SHA into a verified body-free context link."""
    projection = git_commit_projection(Path(repo), sha)
    resolved_namespace = namespace or _origin_namespace(Path(repo)) or f"git:local/{Path(repo).resolve().name}"
    digest = git_projection_digest(projection)
    facets = {
        "source_kind": "git_commit",
        "touched_paths": projection["touched_paths"],
        "actor": projection["author"],
        "event_ts": str(projection["commit_ts"]),
    }
    if resolved_namespace.startswith("git:") and not resolved_namespace.startswith("git:local/"):
        facets["repository"] = resolved_namespace.removeprefix("git:")
    validate_facets(facets)
    try:
        link = ContextLink(
            kind=LinkKind.GIT_COMMIT,
            canonical_namespace=resolved_namespace,
            canonical_id=sha,
            canonical_digest=digest,
            git_sha=sha,
            facets=facets,
        )
        link.validate()
    except SchemaError as exc:
        raise ResolutionError(REASON_RESOLUTION_ERROR, f"projection violates body-free schema: {exc}") from exc
    verification = VerificationEvidence(
        verifier="git",
        canonical_digest=digest,
        status=VerificationStatus.VERIFIED,
        evidence_locator=f"git:commit/{sha}",
        checked_at=isoformat_z(now or utc_now()),
    )
    excerpt = {
        "source": f"git:commit/{sha}",
        "parents": projection["parents"],
        "touched_paths": projection["touched_paths"],
        "commit_ts": projection["commit_ts"],
        "author": projection["author"],
    }
    return Resolution(link=link, verification=verification, excerpt=excerpt)


# ── acp_conversation ─────────────────────────────────────────────────────────


def acp_receipt_projection(receipt: dict[str, Any], *, git_sha: str | None = None) -> dict[str, Any]:
    """Extract the body-free terminal metadata covered by the digest."""
    projection = {
        "schema": "acp-receipt-projection.v1",
        "conversation_id": receipt["conversation_id"],
        "state": receipt["state"],
        "participants": sorted(receipt["participants"]),
        "rounds_requested": receipt["rounds_requested"],
        "rounds_observed": receipt["rounds_observed"],
        "successful_rounds": receipt["successful_rounds"],
        "participant_outcomes": receipt["participant_outcomes"],
        "synthesis_outcome": receipt["synthesis_outcome"],
        "duplicate_suppressed_count": receipt["duplicate_suppressed_count"],
        "created_at": receipt["created_at"],
        "updated_at": receipt["updated_at"],
        "duration_ms": receipt["duration_ms"],
        "token_count": receipt["token_count"],
    }
    if git_sha is not None:
        projection["git_sha_correlation"] = git_sha
    return projection


def acp_projection_digest(projection: dict[str, Any]) -> str:
    return "sha256:" + sha256_text(canonical_json(projection))


def _verified_acp_receipt(acp_root: Path, conversation_id: str) -> dict[str, Any]:
    if not ACP_CONVERSATION_ID_RE.fullmatch(conversation_id):
        raise ResolutionError(REASON_RESOLUTION_ERROR, "identifier is not a canonical ACP conversation ID")
    try:
        receipt = verify_discussion_receipt(root=Path(acp_root), conversation_id=conversation_id)
    except AcpxDiscussionNotFoundError as exc:
        raise ResolutionError(REASON_SOURCE_MISSING) from exc
    except AcpxDiscussionError as exc:
        raise ResolutionError(REASON_RESOLUTION_ERROR, type(exc).__name__) from exc
    if receipt.get("content_included") is not False:
        raise ResolutionError(REASON_RESOLUTION_ERROR, "receipt violates the body-free contract")
    if receipt.get("verified") is not True:
        raise ResolutionError(REASON_PARTIAL_TERMINAL, ",".join(receipt.get("reasons") or []))
    return receipt


def _verify_acp_git_correlation(acp_root: Path, conversation_id: str, git_sha: str | None) -> None:
    """Prove an optional ACP-to-commit join from canonical correlation metadata."""
    if git_sha is None:
        return
    if not GIT_SHA_RE.fullmatch(git_sha):
        raise ResolutionError(REASON_RESOLUTION_ERROR, "git_sha must be a full 40-hex commit SHA")
    db_path = Path(acp_root).expanduser().resolve() / "comms.sqlite3"
    if not db_path.is_file():
        raise ResolutionError(REASON_SOURCE_MISSING)
    try:
        with sqlite3.connect(f"{db_path.as_uri()}?mode=ro", uri=True) as connection:
            row = connection.execute(
                "SELECT correlation_digest FROM acp_conversations WHERE conversation_id = ?",
                (conversation_id,),
            ).fetchone()
    except sqlite3.Error as exc:
        raise ResolutionError(REASON_RESOLUTION_ERROR, "ACP correlation metadata unreadable") from exc
    if row is None:
        raise ResolutionError(REASON_SOURCE_MISSING)
    if not isinstance(row[0], str) or row[0] != sha256_text(git_sha):
        raise ResolutionError(REASON_DIGEST_MISMATCH, "ACP correlation does not bind this commit")


def resolve_acp_conversation(
    conversation_id: str,
    *,
    acp_root: Path,
    git_sha: str | None = None,
    now: datetime | None = None,
) -> Resolution:
    """Resolve an exact ACP conversation ID through the terminal receipt verifier."""
    receipt = _verified_acp_receipt(Path(acp_root), conversation_id)
    _verify_acp_git_correlation(Path(acp_root), conversation_id, git_sha)
    projection = acp_receipt_projection(receipt, git_sha=git_sha)
    digest = acp_projection_digest(projection)
    facets = {
        "source_kind": "acp_conversation",
        "state": str(receipt["state"]),
        "participants": sorted(receipt["participants"]),
        "token_bucket": _token_bucket(receipt["token_count"]),
        "event_ts": str(receipt["updated_at"]),
    }
    validate_facets(facets)
    try:
        link = ContextLink(
            kind=LinkKind.ACP_CONVERSATION,
            canonical_namespace="acp:conversations",
            canonical_id=conversation_id,
            canonical_digest=digest,
            git_sha=git_sha,
            facets=facets,
        )
        link.validate()
    except SchemaError as exc:
        raise ResolutionError(REASON_RESOLUTION_ERROR, f"projection violates body-free schema: {exc}") from exc
    verification = VerificationEvidence(
        verifier="acp-receipt",
        canonical_digest=digest,
        status=VerificationStatus.VERIFIED,
        evidence_locator=f"acp:conversation/{conversation_id}",
        checked_at=isoformat_z(now or utc_now()),
    )
    excerpt = {
        "source": f"acp:conversation/{conversation_id}",
        "state": receipt["state"],
        "participants": sorted(receipt["participants"]),
        "rounds_requested": receipt["rounds_requested"],
        "successful_rounds": receipt["successful_rounds"],
        "synthesis_outcome": receipt["synthesis_outcome"],
        "created_at": receipt["created_at"],
        "updated_at": receipt["updated_at"],
        "token_bucket": _token_bucket(receipt["token_count"]),
        "content_included": False,
    }
    if git_sha is not None:
        excerpt["git_sha_correlation"] = git_sha
    return Resolution(link=link, verification=verification, excerpt=excerpt)


# ── rollover ─────────────────────────────────────────────────────────────────


#: Sub-lifecycle objects whose ``state`` field is body-free and digest-covered.
_ROLLOVER_SUB_STATE_KEYS = (
    "strict_recall",
    "canary",
    "confirmation",
    "predecessor_archival",
    "heartbeat",
)


def _split_rollover_canonical_id(identifier: str) -> tuple[str, str, str]:
    """Split ``<agent>/<lineage_id>/<rollover_id>`` into its exact components."""
    parts = identifier.split("/")
    if len(parts) != 3 or not all(part.strip() for part in parts):
        raise ResolutionError(
            REASON_RESOLUTION_ERROR,
            "rollover canonical ID must be '<agent>/<lineage_id>/<rollover_id>'",
        )
    return parts[0], parts[1], parts[2]


def rollover_projection(record: dict[str, Any]) -> dict[str, Any]:
    """Extract the strict body-free projection covered by the digest.

    The allowlist is deliberately narrow: schema/key, lifecycle state and
    boundary, the ``state`` sub-field of each sub-lifecycle object,
    ``cleanup_authorized``, timestamps, and non-body routing (stream epic,
    issue number, lifecycle state). Titles, task/thread IDs, reasons, paths,
    history, receipts, evidence, scores, and nested native/readback payloads
    are excluded.
    """
    key = record["key"]
    identity = record["task_identity"]
    projection: dict[str, Any] = {
        "schema": "rollover-projection.v1",
        "key": {
            "agent": key["agent"],
            "lineage_id": key["lineage_id"],
            "rollover_id": key["rollover_id"],
        },
        "state": record["state"],
        "last_successful_boundary": record["last_successful_boundary"],
        "lifecycle_state": identity["lifecycle_state"],
        "stream_epic": identity["stream_epic"],
        "github_issue_number": identity["github_issue_number"],
        "cleanup_authorized": record["heartbeat"]["cleanup_authorized"],
        "prepared_at": record["timestamps"]["prepared_at"],
        "updated_at": record["timestamps"]["updated_at"],
    }
    for sub_key in _ROLLOVER_SUB_STATE_KEYS:
        projection[f"{sub_key}_state"] = record[sub_key]["state"]
    return projection


def rollover_projection_digest(projection: dict[str, Any]) -> str:
    """Deterministic digest over the body-free rollover projection only."""
    return "sha256:" + sha256_text(canonical_json(projection))


def resolve_rollover(
    agent: str,
    lineage_id: str,
    rollover_id: str,
    *,
    state_root: Path,
    now: datetime | None = None,
) -> Resolution:
    """Resolve an exact ``(agent, lineage_id, rollover_id)`` triple.

    Reads the canonical registry record through the existing read-only
    :func:`load_record` verifier (which validates the schema, canonical path,
    and task identity). The registry state root is never mutated.
    """
    try:
        path = rollover_record_path(Path(state_root), agent=agent, lineage_id=lineage_id, rollover_id=rollover_id)
    except ValueError as exc:
        raise ResolutionError(REASON_RESOLUTION_ERROR, "rollover identity is not canonical") from exc
    if not path.is_file():
        raise ResolutionError(REASON_SOURCE_MISSING)
    try:
        record = load_rollover_record(Path(state_root), agent=agent, lineage_id=lineage_id, rollover_id=rollover_id)
    except ValueError as exc:
        raise ResolutionError(REASON_RESOLUTION_ERROR, "rollover record failed validation") from exc
    canonical_id = f"{agent}/{lineage_id}/{rollover_id}"
    projection = rollover_projection(record)
    digest = rollover_projection_digest(projection)
    facets: dict[str, Any] = {
        "source_kind": "rollover",
        "state": str(record["state"]),
    }
    stream_epic = record["task_identity"].get("stream_epic")
    if isinstance(stream_epic, int):
        facets["stream_epic"] = stream_epic
    validate_facets(facets)
    try:
        link = ContextLink(
            kind=LinkKind.ROLLOVER,
            canonical_namespace=ROLLOVER_NAMESPACE,
            canonical_id=canonical_id,
            canonical_digest=digest,
            facets=facets,
        )
        link.validate()
    except SchemaError as exc:
        raise ResolutionError(REASON_RESOLUTION_ERROR, f"projection violates body-free schema: {exc}") from exc
    verification = VerificationEvidence(
        verifier="rollover-registry",
        canonical_digest=digest,
        status=VerificationStatus.VERIFIED,
        evidence_locator=f"{ROLLOVER_NAMESPACE}/{canonical_id}",
        checked_at=isoformat_z(now or utc_now()),
    )
    excerpt = {
        "source": f"{ROLLOVER_NAMESPACE}/{canonical_id}",
        **projection,
    }
    return Resolution(link=link, verification=verification, excerpt=excerpt)


# ── typed dispatch and re-verification gate ──────────────────────────────────


def _open_readonly_sqlite(db_path: Path) -> sqlite3.Connection:
    """Open one SQLite database read-only via URI ``mode=ro``; fail closed."""
    path = Path(db_path).expanduser().resolve()
    if not path.is_file():
        raise ResolutionError(REASON_SOURCE_MISSING)
    try:
        connection = sqlite3.connect(f"{path.as_uri()}?mode=ro", uri=True)
    except sqlite3.Error as exc:
        raise ResolutionError(REASON_RESOLUTION_ERROR, "sqlite unreadable") from exc
    connection.row_factory = sqlite3.Row
    return connection


#: Default formal-review gate kind / publication context used by Fleet Comms.
DEFAULT_GATE_KIND = "cross-family-review"
DEFAULT_STATUS_CONTEXT = "fleet/cross-family-review"

#: Relative path segments for canonical local stores under the primary checkout.
_FLEET_COMMS_REL = Path("batch_state") / "fleet-comms" / "v1"
_MONITOR_DB_NAME = "agent_monitor.sqlite3"
_ISSUE_CACHE_NAME = "issue_stream_audit.json"


def default_fleet_root(repo: Path | str) -> Path:
    """Resolve the shared Fleet Comms plane root beneath the primary checkout."""
    return shared_repository_root(repo) / _FLEET_COMMS_REL


def default_monitor_root(repo: Path | str) -> Path:
    """Resolve the shared Agent Process Monitor state root beneath the primary checkout."""
    return shared_repository_root(repo) / "batch_state"


def default_monitor_db(repo: Path | str) -> Path:
    """Resolve the shared Agent Process Monitor database beneath its state root."""
    return default_monitor_root(repo) / _MONITOR_DB_NAME


def default_issue_cache(repo: Path | str) -> Path:
    """Resolve the shared issue-stream-audit cache beneath the primary checkout."""
    return shared_repository_root(repo) / "batch_state" / _ISSUE_CACHE_NAME


def _fleet_db_path(fleet_root: Path | str) -> Path:
    return Path(fleet_root).expanduser().resolve() / "comms.sqlite3"


def _blob_path_for(fleet_root: Path, digest: str) -> Path:
    """Compute the content-addressed sealed-verdict blob path (matches ArtifactStore)."""
    lowered = digest.lower()
    return Path(fleet_root).expanduser().resolve() / "blobs" / "sha256" / lowered[:2] / lowered


def _github_namespace(repo: Path) -> str:
    """Derive ``github:<owner/repo>`` from a public local origin, or fail closed."""
    origin = _origin_url(Path(repo))
    match = GITHUB_ORIGIN_RE.fullmatch(origin or "")
    if match is not None:
        return "github:" + match.group("repository")
    raise ResolutionError(REASON_SOURCE_MISSING, "public GitHub origin unavailable")


def _github_repository(namespace: str) -> str:
    """Validate an explicit ``github:<owner/repo>`` namespace and return its repository."""
    if not namespace.startswith("github:"):
        raise ResolutionError(REASON_RESOLUTION_ERROR, "github namespace is required")
    repository = namespace.removeprefix("github:")
    if not GITHUB_REPOSITORY_RE.fullmatch(repository):
        raise ResolutionError(REASON_RESOLUTION_ERROR, "github namespace must identify owner/repository")
    return repository


def _repository_from_namespace(namespace: str) -> str:
    """Extract ``<owner/repo>`` from a ``github:<owner/repo>`` namespace."""
    return _github_repository(namespace)


def _ram_bucket(reserved_mb: int) -> str:
    """Bound the exact reserved-RAM value into a coarse bucket."""
    if reserved_mb <= 0:
        return "none"
    if reserved_mb <= 512:
        return "small"
    if reserved_mb <= 1024:
        return "medium"
    if reserved_mb <= 2048:
        return "large"
    return "xlarge"


def _require_identity(value: object, *, field: str) -> str:
    """Accept one projected identifier only when the shared body-free guard does."""
    if not isinstance(value, str):
        raise ResolutionError(REASON_RESOLUTION_ERROR, f"{field} is not an identity")
    try:
        validate_identity(value, field_name=field)
    except SchemaError as exc:
        raise ResolutionError(REASON_RESOLUTION_ERROR, f"{field} is not body-free") from exc
    return value


def _require_state(value: object, *, field: str, allowed: frozenset[str]) -> str:
    """Require one finite, documented state token before projection."""
    if not isinstance(value, str) or value not in allowed:
        raise ResolutionError(REASON_RESOLUTION_ERROR, f"{field} is not an allowed state")
    return value


def _require_timestamp(value: object, *, field: str) -> str:
    """Validate and canonicalize a bounded ISO-8601 timestamp for projection."""
    text = _require_identity(value, field=field)
    try:
        parsed = parse_timestamp(text)
    except (TypeError, ValueError) as exc:
        raise ResolutionError(REASON_RESOLUTION_ERROR, f"{field} is not a timestamp") from exc
    epoch = parsed.timestamp()
    if not math.isfinite(epoch) or not _EARLIEST_TIMESTAMP <= epoch <= _LATEST_TIMESTAMP:
        raise ResolutionError(REASON_RESOLUTION_ERROR, f"{field} is outside the supported range")
    return isoformat_z(parsed)


def _require_epoch(value: object, *, field: str) -> float:
    """Validate a finite Unix epoch in the same bounded timestamp range."""
    if isinstance(value, bool) or not isinstance(value, int | float) or not math.isfinite(value):
        raise ResolutionError(REASON_RESOLUTION_ERROR, f"{field} is not a finite timestamp")
    epoch = float(value)
    if not _EARLIEST_TIMESTAMP <= epoch <= _LATEST_TIMESTAMP:
        raise ResolutionError(REASON_RESOLUTION_ERROR, f"{field} is outside the supported range")
    return epoch


def _require_monitor_ram(value: object) -> int:
    """Validate the monitor's bounded reservation before collapsing it to a bucket."""
    if isinstance(value, bool) or not isinstance(value, int) or not 64 <= value <= 3072:
        raise ResolutionError(REASON_RESOLUTION_ERROR, "reserved_ram_mb is not an allowed reservation")
    return value


# ── github_issue ─────────────────────────────────────────────────────────────


def _parse_issue_number(identifier: str) -> int:
    """Parse ``issue/<number>`` or a bare positive integer into an issue number."""
    text = identifier.strip()
    if text.startswith("issue/"):
        text = text[len("issue/"):]
    if not text.isdigit():
        raise ResolutionError(REASON_RESOLUTION_ERROR, "issue canonical_id must be issue/<number>")
    number = int(text)
    if number <= 0:
        raise ResolutionError(REASON_RESOLUTION_ERROR, "issue number must be positive")
    return number


def github_issue_projection(
    issue_number: int,
    *,
    stream_epic: int,
    stream: str,
    via: str,
) -> dict[str, Any]:
    """Body-free identity projection of one verified open issue.

    Cache freshness proves that the membership was checked, but is not part of
    the issue identity.  In particular, a harmless cache refresh must not
    create a new locator or tombstone a previously verified issue link.
    """
    return {
        "schema": "github-issue-projection.v1",
        "issue_number": issue_number,
        "stream_epic": stream_epic,
        "stream": stream,
        "via": via,
    }


def github_issue_projection_digest(projection: dict[str, Any]) -> str:
    return "sha256:" + sha256_text(canonical_json(projection))


def resolve_github_issue(
    issue_number: int,
    *,
    cache_path: Path,
    repo: Path,
    namespace: str | None = None,
    now: datetime | None = None,
) -> Resolution:
    """Resolve one exact issue number against the fresh local stream-audit cache.

    Reads ``batch_state/issue_stream_audit.json`` read-only. A stale, missing,
    or malformed cache, or a closed/missing/orphaned/multi-homed issue fails
    closed. Projects issue number and unique stream/epic membership only;
    cache freshness is verification evidence, never identity.
    """
    if not isinstance(issue_number, int) or issue_number <= 0:
        raise ResolutionError(REASON_RESOLUTION_ERROR, "issue number must be a positive integer")
    path = Path(cache_path).expanduser().resolve()
    if not path.is_file():
        raise ResolutionError(REASON_SOURCE_MISSING)
    try:
        raw = path.read_text(encoding="utf-8")
        report = json.loads(raw)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ResolutionError(REASON_RESOLUTION_ERROR, "issue cache unreadable") from exc
    if not isinstance(report, dict):
        raise ResolutionError(REASON_RESOLUTION_ERROR, "issue cache malformed")

    generated_at = report.get("generated_at")
    if (
        isinstance(generated_at, bool)
        or not isinstance(generated_at, int | float)
        or not math.isfinite(generated_at)
    ):
        raise ResolutionError(REASON_RESOLUTION_ERROR, "issue cache missing generated_at")
    moment = now or utc_now()
    now_epoch = moment.timestamp()
    if now_epoch + MAX_CACHE_SKEW_SECONDS < generated_at:
        raise ResolutionError(REASON_RESOLUTION_ERROR, "issue cache future-skewed")
    if now_epoch - generated_at > MAX_ISSUE_CACHE_AGE_SECONDS:
        raise ResolutionError(REASON_PARTIAL_TERMINAL, "issue cache stale")

    open_numbers = report.get("open_issue_numbers")
    if not isinstance(open_numbers, list) or not all(
        isinstance(number, int) and not isinstance(number, bool) and number > 0
        for number in open_numbers
    ):
        raise ResolutionError(REASON_RESOLUTION_ERROR, "issue cache missing open_issue_numbers")
    open_set = set(open_numbers)
    if issue_number not in open_set:
        raise ResolutionError(REASON_SOURCE_MISSING)

    index = report.get("effective_membership")
    if not isinstance(index, dict):
        raise ResolutionError(REASON_RESOLUTION_ERROR, "issue cache missing effective_membership")
    entry = index.get(str(issue_number))
    if not isinstance(entry, dict):
        raise ResolutionError(REASON_SOURCE_MISSING)
    epics = entry.get("epics")
    streams = entry.get("streams")
    via = entry.get("via")
    unique = entry.get("unique_stream")
    if (
        not isinstance(epics, list)
        or len(epics) != 1
        or not isinstance(epics[0], int)
        or isinstance(epics[0], bool)
        or epics[0] <= 0
        or not isinstance(streams, list)
        or len(streams) != 1
        or not isinstance(streams[0], str)
        or not streams[0]
        or via not in {"native", "body"}
        or unique is not True
    ):
        raise ResolutionError(REASON_RESOLUTION_ERROR, "issue is ambiguous or not uniquely owned")
    stream_epic = epics[0]
    stream = _require_identity(streams[0], field="stream")
    via_value = via

    resolved_namespace = namespace or _github_namespace(Path(repo))
    _github_repository(resolved_namespace)
    canonical_id = f"issue/{issue_number}"
    projection = github_issue_projection(
        issue_number,
        stream_epic=stream_epic,
        stream=stream,
        via=via_value,
    )
    digest = github_issue_projection_digest(projection)
    facets: dict[str, Any] = {
        "source_kind": "github_issue",
        "stream_epic": stream_epic,
        "state": "open",
    }
    validate_facets(facets)
    try:
        link = ContextLink(
            kind=LinkKind.GITHUB_ISSUE,
            canonical_namespace=resolved_namespace,
            canonical_id=canonical_id,
            canonical_digest=digest,
            facets=facets,
        )
        link.validate()
    except SchemaError as exc:
        raise ResolutionError(REASON_RESOLUTION_ERROR, f"projection violates body-free schema: {exc}") from exc
    verification = VerificationEvidence(
        verifier="issue-stream-cache",
        canonical_digest=digest,
        status=VerificationStatus.VERIFIED,
        evidence_locator=f"issue-cache:issue/{issue_number}",
        checked_at=isoformat_z(moment),
    )
    excerpt = {
        "source": f"issue-cache:issue/{issue_number}",
        **projection,
    }
    return Resolution(link=link, verification=verification, excerpt=excerpt)


# ── github_pr ────────────────────────────────────────────────────────────────


def _split_github_pr_canonical_id(identifier: str) -> tuple[int, str]:
    """Split ``pr/<pr_number>/<gate_kind>`` into ``(pr_number, gate_kind)``."""
    parts = identifier.split("/", 2)
    if len(parts) != 3 or parts[0] != "pr" or not parts[1].isdigit():
        raise ResolutionError(REASON_RESOLUTION_ERROR, "github_pr canonical_id must be pr/<number>/<gate>")
    number = int(parts[1])
    if number <= 0:
        raise ResolutionError(REASON_RESOLUTION_ERROR, "pr number must be positive")
    if not parts[2].strip():
        raise ResolutionError(REASON_RESOLUTION_ERROR, "gate_kind must be non-empty")
    return number, parts[2]


def github_pr_projection(
    *,
    repository: str,
    pr_number: int,
    head_sha: str,
    gate_kind: str,
    job_state: str,
    published: bool,
    publication_context: str,
    published_at: str,
) -> dict[str, Any]:
    return {
        "schema": "github-pr-projection.v1",
        "repository": repository,
        "pr_number": pr_number,
        "head_sha": head_sha,
        "gate_kind": gate_kind,
        "job_state": job_state,
        "published": published,
        "publication_context": publication_context,
        "published_at": published_at,
    }


def github_pr_projection_digest(projection: dict[str, Any]) -> str:
    return "sha256:" + sha256_text(canonical_json(projection))


def resolve_github_pr(
    repository: str,
    pr_number: int,
    head_sha: str,
    *,
    gate_kind: str = DEFAULT_GATE_KIND,
    fleet_root: Path,
    repo: Path,
    now: datetime | None = None,
) -> Resolution:
    """Resolve a PR/head pair from a completed formal-review job + publication row.

    Reads the Fleet Comms SQLite store read-only (``mode=ro``), verifies the
    job is complete and has a durable ``github_publications`` row, and verifies
    the exact head commit exists in local Git. Never exposes publication IDs
    or artifact/raw captures.
    """
    if not repository or not GITHUB_REPOSITORY_RE.fullmatch(repository):
        raise ResolutionError(REASON_RESOLUTION_ERROR, "repository must identify owner/repository")
    _require_identity(repository, field="repository")
    if not isinstance(pr_number, int) or pr_number <= 0:
        raise ResolutionError(REASON_RESOLUTION_ERROR, "pr_number must be a positive integer")
    sha = head_sha.lower()
    if not GIT_SHA_RE.fullmatch(sha):
        raise ResolutionError(REASON_RESOLUTION_ERROR, "head_sha must be a full 40-hex commit SHA")
    gate_kind = _require_state(gate_kind, field="gate_kind", allowed=frozenset({DEFAULT_GATE_KIND}))
    moment = now or utc_now()
    db_path = _fleet_db_path(Path(fleet_root))

    # Verify the head commit exists in local Git.
    object_type = _run_git(Path(repo), "cat-file", "-t", sha).strip()
    if object_type != "commit":
        raise ResolutionError(REASON_SOURCE_MISSING, "head_sha is not a local commit")

    connection = _open_readonly_sqlite(db_path)
    try:
        try:
            job_row = connection.execute(
                "SELECT review_id, repository, pr_number, head_sha, gate_kind, state,"
                " sealed_verdict_artifact_id, created_at"
                " FROM formal_review_jobs"
                " WHERE repository = ? AND pr_number = ? AND head_sha = ? AND gate_kind = ?",
                (repository, pr_number, sha, gate_kind),
            ).fetchone()
        except sqlite3.Error as exc:
            raise ResolutionError(REASON_RESOLUTION_ERROR, "formal_review_jobs unreadable") from exc
        if job_row is None:
            raise ResolutionError(REASON_SOURCE_MISSING)
        job_state = _require_state(job_row["state"], field="job_state", allowed=_FORMAL_JOB_STATES)
        if job_state != "complete":
            raise ResolutionError(REASON_PARTIAL_TERMINAL)
        review_id = _require_identity(job_row["review_id"], field="review_id")
        try:
            pub_row = connection.execute(
                "SELECT status_context, published_at FROM github_publications"
                " WHERE review_id = ? AND head_sha = ? AND status_context = ?",
                (review_id, sha, DEFAULT_STATUS_CONTEXT),
            ).fetchone()
        except sqlite3.Error as exc:
            raise ResolutionError(REASON_RESOLUTION_ERROR, "github_publications unreadable") from exc
        if pub_row is None:
            raise ResolutionError(REASON_PUBLICATION_MISSING)
    finally:
        connection.close()

    published_context = _require_state(
        pub_row["status_context"], field="publication_context", allowed=frozenset({DEFAULT_STATUS_CONTEXT})
    )
    published_at = _require_timestamp(pub_row["published_at"], field="published_at")
    namespace = f"github:{repository}"
    canonical_id = f"pr/{pr_number}/{gate_kind}"
    projection = github_pr_projection(
        repository=repository,
        pr_number=pr_number,
        head_sha=sha,
        gate_kind=gate_kind,
        job_state=job_state,
        published=True,
        publication_context=published_context,
        published_at=published_at,
    )
    digest = github_pr_projection_digest(projection)
    facets: dict[str, Any] = {
        "source_kind": "github_pr",
        "repository": repository,
        "state": job_state,
        "event_ts": published_at,
    }
    validate_facets(facets)
    try:
        link = ContextLink(
            kind=LinkKind.GITHUB_PR,
            canonical_namespace=namespace,
            canonical_id=canonical_id,
            canonical_digest=digest,
            git_sha=sha,
            facets=facets,
        )
        link.validate()
    except SchemaError as exc:
        raise ResolutionError(REASON_RESOLUTION_ERROR, f"projection violates body-free schema: {exc}") from exc
    verification = VerificationEvidence(
        verifier="fleet-formal-review",
        canonical_digest=digest,
        status=VerificationStatus.VERIFIED,
        evidence_locator=f"fleet:pr/{pr_number}/head/{sha}",
        checked_at=isoformat_z(moment),
    )
    excerpt = {
        "source": f"fleet:pr/{pr_number}/head/{sha}",
        **projection,
    }
    return Resolution(link=link, verification=verification, excerpt=excerpt)


# ── formal_review ────────────────────────────────────────────────────────────


def formal_review_projection(
    *,
    review_id: str,
    repository: str,
    pr_number: int,
    head_sha: str,
    gate_kind: str,
    job_state: str,
    verdict: str,
    model: str,
    family: str,
    harness: str,
    attempt_count: int,
    completion_states: list[str],
    published: bool,
    publication_context: str | None,
    published_at: str | None,
) -> dict[str, Any]:
    return {
        "schema": "formal-review-projection.v1",
        "review_id": review_id,
        "repository": repository,
        "pr_number": pr_number,
        "head_sha": head_sha,
        "gate_kind": gate_kind,
        "job_state": job_state,
        "verdict": verdict,
        "model": model,
        "family": family,
        "harness": harness,
        "attempt_count": attempt_count,
        "completion_states": completion_states,
        "published": published,
        "publication_context": publication_context,
        "published_at": published_at,
    }


def formal_review_projection_digest(projection: dict[str, Any]) -> str:
    return "sha256:" + sha256_text(canonical_json(projection))


def resolve_formal_review(
    review_id: str,
    *,
    fleet_root: Path,
    now: datetime | None = None,
) -> Resolution:
    """Resolve a completed formal-review job, hash-check its sealed verdict, and project.

    Reads the Fleet Comms SQLite store read-only, loads the sealed-verdict blob
    from the content-addressed store, hash-checks it, parses it with the
    existing strict parser, and re-checks job binding. Never exposes sealed /
    snapshot / raw artifact IDs or payload text / findings.
    """
    if not review_id or not review_id.strip():
        raise ResolutionError(REASON_RESOLUTION_ERROR, "review_id is required")
    rid = _require_identity(review_id.strip(), field="review_id")
    moment = now or utc_now()
    root = Path(fleet_root).expanduser().resolve()
    db_path = _fleet_db_path(root)

    connection = _open_readonly_sqlite(db_path)
    try:
        try:
            job_row = connection.execute(
                "SELECT review_id, repository, pr_number, head_sha, gate_kind, state,"
                " sealed_verdict_artifact_id, created_at"
                " FROM formal_review_jobs WHERE review_id = ?",
                (rid,),
            ).fetchone()
        except sqlite3.Error as exc:
            raise ResolutionError(REASON_RESOLUTION_ERROR, "formal_review_jobs unreadable") from exc
        if job_row is None:
            raise ResolutionError(REASON_SOURCE_MISSING)
        job_state = _require_state(job_row["state"], field="job_state", allowed=_FORMAL_JOB_STATES)
        if job_state != "complete":
            raise ResolutionError(REASON_PARTIAL_TERMINAL)
        sealed_artifact_id = job_row["sealed_verdict_artifact_id"]
        if sealed_artifact_id is None:
            raise ResolutionError(REASON_SOURCE_MISSING, "job has no sealed verdict")
        try:
            art_row = connection.execute(
                "SELECT sha256 FROM artifacts WHERE artifact_id = ?",
                (str(sealed_artifact_id),),
            ).fetchone()
        except sqlite3.Error as exc:
            raise ResolutionError(REASON_RESOLUTION_ERROR, "artifacts unreadable") from exc
        if art_row is None:
            raise ResolutionError(REASON_SOURCE_MISSING)
        try:
            pub_row = connection.execute(
                "SELECT head_sha, status_context, published_at FROM github_publications WHERE review_id = ?",
                (rid,),
            ).fetchone()
        except sqlite3.Error as exc:
            raise ResolutionError(REASON_RESOLUTION_ERROR, "github_publications unreadable") from exc
        try:
            attempt_rows = connection.execute(
                "SELECT attempt_number, completion_state FROM formal_review_attempts"
                " WHERE review_id = ? ORDER BY attempt_number",
                (rid,),
            ).fetchall()
        except sqlite3.Error as exc:
            raise ResolutionError(REASON_RESOLUTION_ERROR, "formal_review_attempts unreadable") from exc
    finally:
        connection.close()

    # Hash-check the sealed-verdict blob read-only (never via ArtifactStore).
    digest_hex = str(art_row["sha256"]).lower()
    if not SHA256_HEX_RE.fullmatch(digest_hex):
        raise ResolutionError(REASON_RESOLUTION_ERROR, "sealed-verdict digest is malformed")
    blob_path = _blob_path_for(root, digest_hex)
    if not blob_path.is_file():
        raise ResolutionError(REASON_SOURCE_MISSING, "sealed-verdict blob missing")
    try:
        blob_bytes = blob_path.read_bytes()
    except OSError as exc:
        raise ResolutionError(REASON_RESOLUTION_ERROR, "sealed-verdict blob unreadable") from exc
    if hashlib.sha256(blob_bytes).hexdigest() != digest_hex:
        raise ResolutionError(REASON_DIGEST_MISMATCH, "sealed-verdict blob digest drift")

    # Parse with the existing strict parser and re-check job binding.
    try:
        sealed = parse_sealed_verdict_payload(blob_bytes)
    except Exception as exc:
        raise ResolutionError(REASON_RESOLUTION_ERROR, "sealed-verdict parse failed") from exc
    job_repo = job_row["repository"]
    if not isinstance(job_repo, str) or not GITHUB_REPOSITORY_RE.fullmatch(job_repo):
        raise ResolutionError(REASON_RESOLUTION_ERROR, "repository must identify owner/repository")
    _require_identity(job_repo, field="repository")
    job_pr = job_row["pr_number"]
    if isinstance(job_pr, bool) or not isinstance(job_pr, int) or job_pr <= 0:
        raise ResolutionError(REASON_RESOLUTION_ERROR, "pr_number must be a positive integer")
    job_sha = str(job_row["head_sha"]).lower()
    if not GIT_SHA_RE.fullmatch(job_sha):
        raise ResolutionError(REASON_RESOLUTION_ERROR, "head_sha must be a full 40-hex commit SHA")
    job_gate = _require_state(job_row["gate_kind"], field="gate_kind", allowed=frozenset({DEFAULT_GATE_KIND}))
    sealed_review_id = _require_identity(sealed.review_id, field="sealed_review_id")
    sealed_repository = sealed.repository
    if not GITHUB_REPOSITORY_RE.fullmatch(sealed_repository):
        raise ResolutionError(REASON_RESOLUTION_ERROR, "sealed repository must identify owner/repository")
    _require_identity(sealed_repository, field="sealed_repository")
    sealed_verdict = _require_state(sealed.verdict, field="verdict", allowed=_FORMAL_VERDICTS)
    sealed_model = _require_identity(sealed.model, field="model")
    sealed_family = _require_identity(sealed.family, field="family")
    sealed_harness = _require_identity(sealed.harness, field="harness")
    if (
        sealed_review_id != rid
        or sealed_repository != job_repo
        or sealed.pr_number != job_pr
        or sealed.head_sha.lower() != job_sha
        or sealed.gate_kind != job_gate
    ):
        raise ResolutionError(REASON_DIGEST_MISMATCH, "sealed-verdict job binding drift")

    published = pub_row is not None
    publication_context = (
        _require_state(pub_row["status_context"], field="publication_context", allowed=frozenset({DEFAULT_STATUS_CONTEXT}))
        if pub_row is not None
        else None
    )
    published_at = _require_timestamp(pub_row["published_at"], field="published_at") if pub_row is not None else None
    if pub_row is not None:
        publication_head = str(pub_row["head_sha"]).lower()
        if not GIT_SHA_RE.fullmatch(publication_head):
            raise ResolutionError(REASON_RESOLUTION_ERROR, "publication head is not a full commit SHA")
        if publication_head != job_sha:
            raise ResolutionError(REASON_DIGEST_MISMATCH, "publication head drift")
    completion_states = [
        _require_state(row["completion_state"], field="completion_state", allowed=_COMPLETION_STATES)
        for row in attempt_rows
    ]
    canonical_id = rid
    namespace = "fleet:formal-reviews"
    projection = formal_review_projection(
        review_id=rid,
        repository=job_repo,
        pr_number=job_pr,
        head_sha=job_sha,
        gate_kind=job_gate,
        job_state=job_state,
        verdict=sealed_verdict,
        model=sealed_model,
        family=sealed_family,
        harness=sealed_harness,
        attempt_count=len(attempt_rows),
        completion_states=completion_states,
        published=published,
        publication_context=publication_context,
        published_at=published_at,
    )
    digest = formal_review_projection_digest(projection)
    facets: dict[str, Any] = {
        "source_kind": "formal_review",
        "repository": job_repo,
        "state": job_state,
        "model": sealed_model,
        "harness": sealed_harness,
    }
    validate_facets(facets)
    try:
        link = ContextLink(
            kind=LinkKind.FORMAL_REVIEW,
            canonical_namespace=namespace,
            canonical_id=canonical_id,
            canonical_digest=digest,
            git_sha=job_sha,
            facets=facets,
        )
        link.validate()
    except SchemaError as exc:
        raise ResolutionError(REASON_RESOLUTION_ERROR, f"projection violates body-free schema: {exc}") from exc
    verification = VerificationEvidence(
        verifier="fleet-formal-review",
        canonical_digest=digest,
        status=VerificationStatus.VERIFIED,
        evidence_locator=f"fleet:review/{rid}",
        checked_at=isoformat_z(moment),
    )
    excerpt = {
        "source": f"fleet:review/{rid}",
        **projection,
    }
    return Resolution(link=link, verification=verification, excerpt=excerpt)


# ── fleet_receipt ────────────────────────────────────────────────────────────


def fleet_receipt_projection(
    *,
    request_id: str,
    requested_recipient: str,
    resolved_recipient: str,
    state: str,
    completion_state: str,
    expires_at: str,
    created_at: str,
    updated_at: str,
) -> dict[str, Any]:
    return {
        "schema": "fleet-receipt-projection.v1",
        "request_id": request_id,
        "requested_recipient": requested_recipient,
        "resolved_recipient": resolved_recipient,
        "state": state,
        "completion_state": completion_state,
        "expires_at": expires_at,
        "created_at": created_at,
        "updated_at": updated_at,
    }


def fleet_receipt_projection_digest(projection: dict[str, Any]) -> str:
    return "sha256:" + sha256_text(canonical_json(projection))


def resolve_fleet_receipt(
    request_id: str,
    *,
    fleet_root: Path,
    now: datetime | None = None,
) -> Resolution:
    """Resolve one canonical ``requests`` row from the Fleet Comms SQLite store.

    Projects request ID, requested/resolved recipient, terminal state,
    completion state, and expiry/created/updated timestamps only. Never reads
    or exposes invocation JSON or message bodies. Nonterminal state or unknown
    completion fails closed.
    """
    if not request_id or not request_id.strip():
        raise ResolutionError(REASON_RESOLUTION_ERROR, "request_id is required")
    rid = _require_identity(request_id.strip(), field="request_id")
    moment = now or utc_now()
    db_path = _fleet_db_path(Path(fleet_root))

    connection = _open_readonly_sqlite(db_path)
    try:
        try:
            row = connection.execute(
                "SELECT request_id, requested_recipient, resolved_recipient, state,"
                " completion_state, expires_at, created_at, updated_at"
                " FROM requests WHERE request_id = ?",
                (rid,),
            ).fetchone()
        except sqlite3.Error as exc:
            raise ResolutionError(REASON_RESOLUTION_ERROR, "requests unreadable") from exc
    finally:
        connection.close()
    if row is None:
        raise ResolutionError(REASON_SOURCE_MISSING)

    state = _require_state(row["state"], field="request_state", allowed=_REQUEST_STATES)
    completion = _require_state(row["completion_state"], field="completion_state", allowed=_REQUEST_COMPLETION_STATES)
    if state not in _TERMINAL_REQUEST_STATES:
        raise ResolutionError(REASON_PARTIAL_TERMINAL)
    if completion == "unknown":
        raise ResolutionError(REASON_PARTIAL_TERMINAL)
    requested_recipient = _require_identity(row["requested_recipient"], field="requested_recipient")
    resolved_recipient = _require_identity(row["resolved_recipient"], field="resolved_recipient")
    expires_at = _require_timestamp(row["expires_at"], field="expires_at")
    created_at = _require_timestamp(row["created_at"], field="created_at")
    updated_at = _require_timestamp(row["updated_at"], field="updated_at")
    if (
        parse_timestamp(updated_at) < parse_timestamp(created_at)
        or parse_timestamp(expires_at) < parse_timestamp(created_at)
    ):
        raise ResolutionError(REASON_RESOLUTION_ERROR, "request timestamps are inconsistent")

    canonical_id = rid
    namespace = "fleet:requests"
    projection = fleet_receipt_projection(
        request_id=rid,
        requested_recipient=requested_recipient,
        resolved_recipient=resolved_recipient,
        state=state,
        completion_state=completion,
        expires_at=expires_at,
        created_at=created_at,
        updated_at=updated_at,
    )
    digest = fleet_receipt_projection_digest(projection)
    facets: dict[str, Any] = {
        "source_kind": "fleet_receipt",
        "state": state,
        "event_ts": updated_at,
    }
    validate_facets(facets)
    try:
        link = ContextLink(
            kind=LinkKind.FLEET_RECEIPT,
            canonical_namespace=namespace,
            canonical_id=canonical_id,
            canonical_digest=digest,
            facets=facets,
        )
        link.validate()
    except SchemaError as exc:
        raise ResolutionError(REASON_RESOLUTION_ERROR, f"projection violates body-free schema: {exc}") from exc
    verification = VerificationEvidence(
        verifier="fleet-requests",
        canonical_digest=digest,
        status=VerificationStatus.VERIFIED,
        evidence_locator=f"fleet:request/{rid}",
        checked_at=isoformat_z(moment),
    )
    excerpt = {
        "source": f"fleet:request/{rid}",
        **projection,
    }
    return Resolution(link=link, verification=verification, excerpt=excerpt)


# ── monitor_run ──────────────────────────────────────────────────────────────


def monitor_run_projection(
    *,
    lease_token: str,
    agent_id: str,
    task_name: str,
    status: str,
    created_at: float,
    last_heartbeat: float,
    ram_bucket: str,
) -> dict[str, Any]:
    return {
        "schema": "monitor-run-projection.v1",
        "lease_token": lease_token,
        "agent_id": agent_id,
        "task_name": task_name,
        "status": status,
        "created_at": created_at,
        "last_heartbeat": last_heartbeat,
        "ram_bucket": ram_bucket,
    }


def monitor_run_projection_digest(projection: dict[str, Any]) -> str:
    return "sha256:" + sha256_text(canonical_json(projection))


def resolve_monitor_run(
    lease_token: str,
    *,
    monitor_root: Path,
    now: datetime | None = None,
) -> Resolution:
    """Resolve a terminal Agent Process Monitor lease row as a local run receipt.

    Projects lease ID, agent ID, task name, terminal status,
    created/last-heartbeat timestamps, and a bounded RAM bucket only. Excludes
    PID and process-create time. Active/nonterminal rows fail closed.
    """
    if not lease_token or not lease_token.strip():
        raise ResolutionError(REASON_RESOLUTION_ERROR, "lease_token is required")
    token = _require_identity(lease_token.strip(), field="lease_token")
    moment = now or utc_now()
    db_path = Path(monitor_root).expanduser().resolve() / _MONITOR_DB_NAME

    connection = _open_readonly_sqlite(db_path)
    try:
        try:
            row = connection.execute(
                "SELECT lease_token, agent_id, task_name, status, created_at,"
                " last_heartbeat, reserved_ram_mb"
                " FROM agent_leases WHERE lease_token = ?",
                (token,),
            ).fetchone()
        except sqlite3.Error as exc:
            raise ResolutionError(REASON_RESOLUTION_ERROR, "agent_leases unreadable") from exc
    finally:
        connection.close()
    if row is None:
        raise ResolutionError(REASON_SOURCE_MISSING)

    status = _require_state(
        row["status"], field="lease_status", allowed=frozenset({"APPROVED", *_TERMINAL_LEASE_STATUSES})
    )
    if status not in _TERMINAL_LEASE_STATUSES:
        raise ResolutionError(REASON_PARTIAL_TERMINAL)

    agent_id = _require_identity(row["agent_id"], field="agent_id")
    task_name = _require_identity(row["task_name"], field="task_name")
    created_at = _require_epoch(row["created_at"], field="created_at")
    last_heartbeat = _require_epoch(row["last_heartbeat"], field="last_heartbeat")
    if last_heartbeat < created_at:
        raise ResolutionError(REASON_RESOLUTION_ERROR, "last_heartbeat precedes created_at")
    reserved_mb = _require_monitor_ram(row["reserved_ram_mb"])
    canonical_id = token
    namespace = "monitor:leases"
    projection = monitor_run_projection(
        lease_token=token,
        agent_id=agent_id,
        task_name=task_name,
        status=status,
        created_at=created_at,
        last_heartbeat=last_heartbeat,
        ram_bucket=_ram_bucket(reserved_mb),
    )
    digest = monitor_run_projection_digest(projection)
    facets: dict[str, Any] = {
        "source_kind": "monitor_run",
        "state": status.lower(),
        "event_ts": str(last_heartbeat),
    }
    validate_facets(facets)
    try:
        link = ContextLink(
            kind=LinkKind.MONITOR_RUN,
            canonical_namespace=namespace,
            canonical_id=canonical_id,
            canonical_digest=digest,
            facets=facets,
        )
        link.validate()
    except SchemaError as exc:
        raise ResolutionError(REASON_RESOLUTION_ERROR, f"projection violates body-free schema: {exc}") from exc
    verification = VerificationEvidence(
        verifier="monitor-lease",
        canonical_digest=digest,
        status=VerificationStatus.VERIFIED,
        evidence_locator=f"monitor:lease/{token}",
        checked_at=isoformat_z(moment),
    )
    excerpt = {
        "source": f"monitor:lease/{token}",
        **projection,
    }
    return Resolution(link=link, verification=verification, excerpt=excerpt)


def resolve_bootstrap(
    kind: LinkKind,
    identifier: str,
    *,
    repo: Path,
    acp_root: Path | None,
    rollover_root: Path | None = None,
    fleet_root: Path | None = None,
    monitor_root: Path | None = None,
    issue_cache_path: Path | None = None,
    namespace: str | None = None,
    git_sha: str | None = None,
    now: datetime | None = None,
) -> Resolution:
    """Resolve one explicit typed identifier for bootstrap/index admission."""
    if kind is LinkKind.GIT_COMMIT:
        return resolve_git_commit(identifier, repo=repo, namespace=namespace, now=now)
    if kind is LinkKind.ACP_CONVERSATION:
        if acp_root is None:
            raise ResolutionError(REASON_SOURCE_MISSING, "no ACP receipt root available")
        return resolve_acp_conversation(identifier, acp_root=acp_root, git_sha=git_sha, now=now)
    if kind is LinkKind.ROLLOVER:
        if rollover_root is None:
            raise ResolutionError(REASON_SOURCE_MISSING, "no rollover registry root available")
        agent, lineage_id, rollover_id = _split_rollover_canonical_id(identifier)
        return resolve_rollover(agent, lineage_id, rollover_id, state_root=rollover_root, now=now)
    if kind is LinkKind.GITHUB_ISSUE:
        issue_number = _parse_issue_number(identifier)
        cache = issue_cache_path or default_issue_cache(repo)
        return resolve_github_issue(issue_number, cache_path=cache, repo=repo, namespace=namespace, now=now)
    if kind is LinkKind.GITHUB_PR:
        if fleet_root is None:
            raise ResolutionError(REASON_SOURCE_MISSING, "no fleet comms root available")
        pr_number, gate_kind = _split_github_pr_canonical_id(identifier)
        repository = _repository_from_namespace(namespace or _github_namespace(repo))
        return resolve_github_pr(
            repository,
            pr_number,
            str(git_sha or ""),
            gate_kind=gate_kind,
            fleet_root=fleet_root,
            repo=repo,
            now=now,
        )
    if kind is LinkKind.FORMAL_REVIEW:
        if fleet_root is None:
            raise ResolutionError(REASON_SOURCE_MISSING, "no fleet comms root available")
        return resolve_formal_review(identifier, fleet_root=fleet_root, now=now)
    if kind is LinkKind.FLEET_RECEIPT:
        if fleet_root is None:
            raise ResolutionError(REASON_SOURCE_MISSING, "no fleet comms root available")
        return resolve_fleet_receipt(identifier, fleet_root=fleet_root, now=now)
    if kind is LinkKind.MONITOR_RUN:
        if monitor_root is None:
            raise ResolutionError(REASON_SOURCE_MISSING, "no monitor root available")
        return resolve_monitor_run(identifier, monitor_root=monitor_root, now=now)
    raise ResolutionError(REASON_UNSUPPORTED_KIND, kind.value)


def reverify_link(
    link: dict[str, Any],
    *,
    repo: Path,
    acp_root: Path | None,
    rollover_root: Path | None = None,
    fleet_root: Path | None = None,
    monitor_root: Path | None = None,
    issue_cache_path: Path | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Re-resolve one stored link and recompute its canonical digest.

    Returns the fresh body-free excerpt, or raises :class:`ResolutionError`
    with a machine reason. Missing sources, partial-terminal receipts,
    unsupported kinds, and digest mismatches all fail closed.
    """
    try:
        kind = LinkKind(str(link["kind"]))
    except ValueError as exc:
        raise ResolutionError(REASON_UNSUPPORTED_KIND, str(link.get("kind"))) from exc
    stored_namespace = str(link["canonical_namespace"])
    stored_git_sha = link.get("git_sha")
    resolution = resolve_bootstrap(
        kind,
        str(link["canonical_id"]),
        repo=repo,
        acp_root=acp_root,
        rollover_root=rollover_root,
        fleet_root=fleet_root,
        monitor_root=monitor_root,
        issue_cache_path=issue_cache_path,
        namespace=stored_namespace,
        git_sha=stored_git_sha if kind in (LinkKind.ACP_CONVERSATION, LinkKind.GITHUB_PR) else None,
        now=now,
    )
    fresh = resolution.link
    # Git and github namespaces may be explicit organizational labels, so
    # re-resolution preserves them instead of deriving them anew. ACP,
    # rollover, formal-review, fleet-receipt, and monitor namespaces are
    # canonical resolver output and are compared.
    namespace_mismatch = (
        kind not in (LinkKind.GIT_COMMIT, LinkKind.GITHUB_ISSUE)
        and fresh.canonical_namespace != stored_namespace
    )
    if fresh.canonical_digest != link["canonical_digest"] or namespace_mismatch:
        raise ResolutionError(REASON_DIGEST_MISMATCH)
    return resolution.excerpt
