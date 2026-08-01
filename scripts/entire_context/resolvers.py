"""Explicit, local-only typed resolvers for context-link bootstrap and re-verify.

Every resolver maps one exact, caller-supplied identifier to a body-free
canonical projection: a deterministic digest over public metadata, never over
subjects, prompts, transcripts, or any composed text. Resolution is fully
local — read-only ``git`` plumbing and the existing body-free ACP terminal
receipt verifier — and fails closed: a source that cannot be verified raises
:class:`ResolutionError` with a machine reason and nothing is fabricated.

Real resolvers in this slice:

- ``git_commit`` — an exact full commit SHA in a local repository resolves to
  parents, touched paths, committer timestamp, and author (public metadata,
  no commit subject/body).
- ``acp_conversation`` — an exact ACP conversation ID resolves through
  :func:`scripts.agent_runtime.acpx_discuss.verify_discussion_receipt` to
  body-free terminal metadata with ``content_included: false``.

``github_issue``, ``github_pr``, ``fleet_receipt``, ``rollover``,
``formal_review``, and ``monitor_run`` remain explicitly unsupported here:
this slice has no local canonical store for them that is verifiable without
network access or protected-rail mutation, so they fail closed with
``unsupported_kind`` instead of fabricating coverage.
"""

from __future__ import annotations

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

from .model import (
    GIT_SHA_RE,
    ContextLink,
    LinkKind,
    SchemaError,
    VerificationEvidence,
    VerificationStatus,
    canonical_json,
    isoformat_z,
    sha256_text,
    utc_now,
    validate_facets,
)

GIT_TIMEOUT_SECONDS = 30

ACP_CONVERSATION_ID_RE = re.compile(r"^conversation_[0-9a-f]{32}$")

#: Kinds with a real local resolver in this slice. Everything else fails closed.
SUPPORTED_RESOLVER_KINDS = frozenset({LinkKind.GIT_COMMIT, LinkKind.ACP_CONVERSATION})

#: Body-free machine reasons a resolution or re-verification can end with.
REASON_SOURCE_MISSING = "source_missing"
REASON_DIGEST_MISMATCH = "digest_mismatch"
REASON_PARTIAL_TERMINAL = "partial_terminal"
REASON_UNSUPPORTED_KIND = "unsupported_kind"
REASON_RESOLUTION_ERROR = "resolution_error"


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


def _origin_namespace(repo: Path) -> str | None:
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
    url = completed.stdout.strip()
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


# ── typed dispatch and re-verification gate ──────────────────────────────────


def resolve_bootstrap(
    kind: LinkKind,
    identifier: str,
    *,
    repo: Path,
    acp_root: Path | None,
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
    raise ResolutionError(REASON_UNSUPPORTED_KIND, kind.value)


def reverify_link(
    link: dict[str, Any],
    *,
    repo: Path,
    acp_root: Path | None,
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
    resolution = resolve_bootstrap(
        kind,
        str(link["canonical_id"]),
        repo=repo,
        acp_root=acp_root,
        namespace=str(link["canonical_namespace"]),
        git_sha=link.get("git_sha") if kind is LinkKind.ACP_CONVERSATION else None,
        now=now,
    )
    fresh = resolution.link
    # Git namespaces may be explicit organizational labels, so re-resolution
    # deliberately preserves them instead of pretending to derive them anew.
    # ACP namespaces are canonical resolver output and can be compared.
    namespace_mismatch = kind is not LinkKind.GIT_COMMIT and fresh.canonical_namespace != link["canonical_namespace"]
    if fresh.canonical_digest != link["canonical_digest"] or namespace_mismatch:
        raise ResolutionError(REASON_DIGEST_MISMATCH)
    return resolution.excerpt
