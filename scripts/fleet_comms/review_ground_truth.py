"""Orchestrator-verified PR change surface for review-gate integrity (#5802).

Layer 3 failure mode: a confident review asserts deletions (or other path
claims) that only appear in a **two-dot** diff against a moved base tip. GitHub's
PR ``files`` list and three-dot ``merge-base...HEAD`` are the truth; two-dot
``base..HEAD`` invents deletions of everything main gained since the fork.

This module:

1. Fetches the PR file inventory via ``gh`` (three-dot / merge-base semantics).
2. Formats a compact ground-truth block for review briefs.
3. Mechanically refuses findings whose paths fall outside that surface.
"""

from __future__ import annotations

import json
import re
import subprocess
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from scripts.fleet_comms.review_publication import ReviewEvidence, ReviewPublicationError
from scripts.fleet_comms.review_publisher import ReviewPublisherError, split_repository

Runner = Callable[..., subprocess.CompletedProcess[str]]

_SHA_RE = re.compile(r"^[0-9a-f]{7,64}$", re.IGNORECASE)
_KNOWN_CHANGE_TYPES = frozenset(
    {"ADDED", "DELETED", "MODIFIED", "RENAMED", "COPIED", "CHANGED"}
)
# Path lines are optional and only appended when they fit the prompt budget.
# Default sample is tiny — review_pr prompts have ~0.5 KiB headroom after the
# checklist + read-only contract (#5802).
_MAX_BRIEF_FILES = 12


class ReviewGroundTruthError(RuntimeError):
    """PR ground-truth lookup or validation failed closed."""


@dataclass(frozen=True, slots=True)
class PrFileChange:
    """One path on the PR's three-dot changed surface."""

    path: str
    change_type: str

    def to_dict(self) -> dict[str, str]:
        return {"path": self.path, "change_type": self.change_type}


@dataclass(frozen=True, slots=True)
class PrChangeInventory:
    """Orchestrator-verified PR file surface (GitHub three-dot semantics)."""

    repository: str
    pr_number: int
    head_sha: str
    base_ref_oid: str
    files: tuple[PrFileChange, ...]

    @property
    def paths(self) -> frozenset[str]:
        return frozenset(entry.path for entry in self.files)

    @property
    def deleted_paths(self) -> frozenset[str]:
        return frozenset(
            entry.path for entry in self.files if entry.change_type == "DELETED"
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "repository": self.repository,
            "pr_number": self.pr_number,
            "head_sha": self.head_sha,
            "base_ref_oid": self.base_ref_oid,
            "files": [entry.to_dict() for entry in self.files],
            "path_count": len(self.files),
            "deleted_path_count": len(self.deleted_paths),
        }


def _single_line(value: str, *, label: str) -> str:
    normalized = " ".join(value.split())
    if not normalized:
        raise ReviewGroundTruthError(f"missing_{label}")
    return normalized


def _normalize_sha(value: Any, *, field: str) -> str:
    if not isinstance(value, str):
        raise ReviewGroundTruthError(f"invalid_{field}: {value!r}")
    sha = _single_line(value, label=field).lower()
    if not _SHA_RE.fullmatch(sha):
        raise ReviewGroundTruthError(f"invalid_{field}: {sha!r}")
    return sha


def _normalize_change_type(raw: Any) -> str:
    if not isinstance(raw, str) or not raw.strip():
        raise ReviewGroundTruthError(f"invalid_change_type: {raw!r}")
    change_type = raw.strip().upper()
    if change_type not in _KNOWN_CHANGE_TYPES:
        raise ReviewGroundTruthError(f"invalid_change_type: {raw!r}")
    return change_type


def parse_pr_change_inventory(
    payload: Mapping[str, Any],
    *,
    repository: str,
    pr_number: int,
) -> PrChangeInventory:
    """Parse a ``gh pr view --json`` payload into a frozen inventory."""
    if pr_number < 1:
        raise ReviewGroundTruthError(f"invalid_pr: {pr_number}")
    try:
        split_repository(repository)
    except ReviewPublisherError as exc:
        raise ReviewGroundTruthError(str(exc)) from exc

    head_sha = _normalize_sha(payload.get("headRefOid"), field="head_sha")
    base_ref_oid = _normalize_sha(payload.get("baseRefOid"), field="base_ref_oid")
    raw_files = payload.get("files")
    if not isinstance(raw_files, list):
        raise ReviewGroundTruthError("pr_files_invalid: expected a list")

    files: list[PrFileChange] = []
    seen: set[str] = set()
    for index, entry in enumerate(raw_files):
        if not isinstance(entry, Mapping):
            raise ReviewGroundTruthError(f"pr_files_entry_invalid: index={index}")
        path = entry.get("path")
        if not isinstance(path, str) or not path.strip():
            raise ReviewGroundTruthError(f"pr_files_path_invalid: index={index}")
        path = path.strip()
        if path.startswith("/") or "\\" in path or ".." in path.split("/"):
            raise ReviewGroundTruthError(f"pr_files_path_unsafe: {path!r}")
        if path in seen:
            raise ReviewGroundTruthError(f"pr_files_path_duplicate: {path!r}")
        seen.add(path)
        files.append(
            PrFileChange(
                path=path,
                change_type=_normalize_change_type(entry.get("changeType")),
            )
        )

    return PrChangeInventory(
        repository=repository,
        pr_number=pr_number,
        head_sha=head_sha,
        base_ref_oid=base_ref_oid,
        files=tuple(files),
    )


def fetch_pr_change_inventory(
    *,
    repository: str,
    pr_number: int,
    runner: Runner = subprocess.run,
) -> PrChangeInventory:
    """Return the live PR three-dot file inventory via ``gh``."""
    if pr_number < 1:
        raise ReviewGroundTruthError(f"invalid_pr: {pr_number}")
    try:
        owner, repo = split_repository(repository)
    except ReviewPublisherError as exc:
        raise ReviewGroundTruthError(str(exc)) from exc

    completed = runner(
        [
            "gh",
            "pr",
            "view",
            str(pr_number),
            "--repo",
            f"{owner}/{repo}",
            "--json",
            "headRefOid,baseRefOid,files",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        stderr = (completed.stderr or "").strip()
        raise ReviewGroundTruthError(
            f"gh_pr_files_lookup_failed: pr={pr_number} repo={owner}/{repo} "
            f"exit={completed.returncode}"
            + (f" stderr={stderr[:200]}" if stderr else "")
        )
    try:
        payload = json.loads(completed.stdout or "")
    except json.JSONDecodeError as exc:
        raise ReviewGroundTruthError(
            f"gh_pr_files_json_invalid: pr={pr_number}"
        ) from exc
    if not isinstance(payload, dict):
        raise ReviewGroundTruthError("gh_pr_files_json_invalid: expected an object")
    return parse_pr_change_inventory(
        payload, repository=repository, pr_number=pr_number
    )


def _change_marker(change_type: str) -> str:
    return {
        "ADDED": "A",
        "DELETED": "D",
        "MODIFIED": "M",
        "RENAMED": "R",
        "COPIED": "C",
        "CHANGED": "M",
    }.get(change_type, "?")


def format_ground_truth_brief(
    inventory: PrChangeInventory,
    *,
    max_bytes: int | None = None,
    max_files: int | None = None,
) -> str:
    """Render a pointer-budgeted ground-truth block for review briefs.

    Always includes repo/PR/SHAs/path *count* plus an instruction to read the
    sealed snapshot or ``gh pr view --json files``. Path inventory lines are
    appended only while they fit under ``max_bytes`` (when set) and
    ``max_files`` (default ``_MAX_BRIEF_FILES``).
    """
    path_count = len(inventory.files)
    deleted_count = len(inventory.deleted_paths)
    header = "\n".join(
        [
            "### Orchestrator-verified PR surface (three-dot / merge-base)",
            f"**PR:** #{inventory.pr_number} (`{inventory.repository}`)",
            f"**Head SHA:** `{inventory.head_sha}`",
            f"**Base tip OID:** `{inventory.base_ref_oid}` "
            "(informational — never two-dot against this tip)",
            f"**Changed paths:** {path_count} ({deleted_count} deleted)",
            (
                "Authoritative list: sealed snapshot or "
                f"`gh pr view {inventory.pr_number} --json files`. "
                "Never two-dot `git diff <base-tip>..<head>`."
            ),
        ]
    )
    compact = header + "\n"
    if max_bytes is not None and len(compact.encode("utf-8")) > max_bytes:
        # Last-resort stub: still carry the SHAs + count that fit.
        stub = (
            f"### PR surface (three-dot / #5802)\n"
            f"`{inventory.repository}` #{inventory.pr_number} "
            f"head=`{inventory.head_sha}` base=`{inventory.base_ref_oid}` "
            f"paths={path_count} ({deleted_count} deleted). "
            f"Read sealed snapshot / `gh pr view {inventory.pr_number} --json files`.\n"
        )
        if len(stub.encode("utf-8")) <= max_bytes:
            return stub
        raw = stub.encode("utf-8")[: max(0, max_bytes)]
        return raw.decode("utf-8", errors="ignore")

    file_cap = _MAX_BRIEF_FILES if max_files is None else max(0, max_files)
    if file_cap <= 0 or not inventory.files:
        return compact

    lines = [header, "", "Sample paths (truncated; full list via gh / sealed snapshot):"]
    shown = 0
    for entry in inventory.files:
        if shown >= file_cap:
            break
        line = f"- `{_change_marker(entry.change_type)}` `{entry.path}`"
        candidate = "\n".join([*lines, line]) + "\n"
        if max_bytes is not None and len(candidate.encode("utf-8")) > max_bytes:
            break
        lines.append(line)
        shown += 1
    omitted = path_count - shown
    if omitted and shown:
        omit_line = f"- … and {omitted} more paths (omitted under prompt budget)"
        candidate = "\n".join([*lines, omit_line]) + "\n"
        if max_bytes is None or len(candidate.encode("utf-8")) <= max_bytes:
            lines.append(omit_line)
    if shown == 0:
        return compact
    return "\n".join(lines) + "\n"


def validate_findings_against_inventory(
    evidence: ReviewEvidence,
    inventory: PrChangeInventory,
    *,
    expected_head_sha: str | None = None,
) -> None:
    """Refuse findings that cite paths outside the PR's three-dot surface.

    Empty findings (clean APPROVED evidence) pass. Every cited path must appear
    in the inventory. Whole-file deletion claims (`change_type=DELETED` surface)
    are additionally required when the finding's claim_type is ``missing`` **and**
    the path is absent from non-deleted inventory entries — i.e. a missing-path
    claim on a path the PR did not touch fails here via the path check; a
    missing-path claim on a MODIFIED file remains allowed (contextual absence).
    """
    if expected_head_sha is not None:
        expected = expected_head_sha.strip().lower()
        if expected and expected != inventory.head_sha:
            raise ReviewPublicationError(
                f"review_ground_truth_head_mismatch: "
                f"expected={expected} inventory={inventory.head_sha}"
            )

    if not evidence.findings:
        return

    allowed = inventory.paths
    offenders: list[str] = []
    for finding in evidence.findings:
        if finding.path not in allowed:
            offenders.append(f"{finding.finding_id}:{finding.path}")

    if offenders:
        sample = ", ".join(offenders[:8])
        more = "" if len(offenders) <= 8 else f" (+{len(offenders) - 8} more)"
        raise ReviewPublicationError(
            "review_finding_path_outside_pr_surface: "
            f"paths not in three-dot PR files: {sample}{more}. "
            "Likely two-dot-diff artifact (#5802); refuse gate."
        )


def inventory_from_path_status(
    *,
    repository: str,
    pr_number: int,
    head_sha: str,
    base_ref_oid: str,
    entries: Sequence[tuple[str, str]] | Iterable[tuple[str, str]],
) -> PrChangeInventory:
    """Test helper: build an inventory from ``(path, change_type)`` pairs."""
    files = tuple(
        PrFileChange(path=path, change_type=_normalize_change_type(change_type))
        for path, change_type in entries
    )
    return PrChangeInventory(
        repository=repository,
        pr_number=pr_number,
        head_sha=_normalize_sha(head_sha, field="head_sha"),
        base_ref_oid=_normalize_sha(base_ref_oid, field="base_ref_oid"),
        files=files,
    )


__all__ = [
    "PrChangeInventory",
    "PrFileChange",
    "ReviewGroundTruthError",
    "fetch_pr_change_inventory",
    "format_ground_truth_brief",
    "inventory_from_path_status",
    "parse_pr_change_inventory",
    "validate_findings_against_inventory",
]
