"""Publish commit-bound rail authorization for GitHub branch protection.

The PR body supplies only an untrusted receipt locator. This module re-reads
the live PR head and changed paths, re-fetches the receipt from the provisioned
Monitor/bridge source, and publishes the result on that exact commit. GitHub
can then enforce ``fleet/rail-approval`` without depending on client hooks.
"""

from __future__ import annotations

import json
import os
import subprocess
from collections.abc import Callable
from dataclasses import dataclass

from scripts.orchestration import rail_path_guard as rail_guard

RAIL_STATUS_CONTEXT = "fleet/rail-approval"
Runner = Callable[..., subprocess.CompletedProcess[str]]


class RailStatusError(RuntimeError):
    """Live PR state or GitHub status publication could not be verified."""


@dataclass(frozen=True, slots=True)
class RailStatusResult:
    """One exact-head authorization decision and its published status state."""

    allowed: bool
    reason: str
    head_sha: str
    rail_paths: tuple[str, ...]
    receipt_id: str | None
    status_state: str


def _split_repository(repository: str) -> tuple[str, str]:
    parts = repository.strip().split("/")
    if len(parts) != 2 or not all(parts):
        raise RailStatusError(f"invalid_repository: expected owner/repo, got {repository!r}")
    return parts[0], parts[1]


def _gh_env() -> dict[str, str]:
    environment = os.environ.copy()
    environment.pop("GH_FORCE_TTY", None)
    environment["NO_COLOR"] = "1"
    return environment


def _fetch_pr_head_body(
    *, repository: str, pr_number: int, runner: Runner
) -> tuple[str, str, int]:
    owner, repo = _split_repository(repository)
    completed = runner(
        [
            "gh",
            "pr",
            "view",
            str(pr_number),
            "--repo",
            f"{owner}/{repo}",
            "--json",
            "headRefOid,body,changedFiles",
        ],
        capture_output=True,
        text=True,
        check=False,
        env=_gh_env(),
    )
    if completed.returncode != 0:
        raise RailStatusError(
            f"gh_pr_rail_snapshot_failed: pr={pr_number} exit={completed.returncode}"
        )
    try:
        payload = json.loads(completed.stdout or "")
    except json.JSONDecodeError as exc:
        raise RailStatusError("gh_pr_rail_snapshot_invalid_json") from exc
    if not isinstance(payload, dict):
        raise RailStatusError("gh_pr_rail_snapshot_invalid_shape")
    head_sha = payload.get("headRefOid")
    body = payload.get("body")
    changed_files = payload.get("changedFiles")
    if not isinstance(head_sha, str) or rail_guard.HEAD_SHA.fullmatch(head_sha) is None:
        raise RailStatusError("gh_pr_rail_snapshot_invalid_head")
    if not isinstance(body, str) or not isinstance(changed_files, int) or changed_files < 0:
        raise RailStatusError("gh_pr_rail_snapshot_invalid_shape")
    return head_sha.lower(), body, changed_files


def _fetch_pr_snapshot(
    *, repository: str, pr_number: int, runner: Runner
) -> tuple[str, str, tuple[str, ...]]:
    owner, repo = _split_repository(repository)
    first_head, _first_body, first_changed_files = _fetch_pr_head_body(
        repository=repository,
        pr_number=pr_number,
        runner=runner,
    )
    changed = runner(
        [
            "gh",
            "api",
            "--paginate",
            "--slurp",
            f"repos/{owner}/{repo}/pulls/{pr_number}/files?per_page=100",
        ],
        capture_output=True,
        text=True,
        check=False,
        env=_gh_env(),
    )
    if changed.returncode != 0:
        raise RailStatusError(
            f"gh_pr_rail_paths_failed: pr={pr_number} exit={changed.returncode}"
        )
    try:
        pages = json.loads(changed.stdout or "")
    except json.JSONDecodeError as exc:
        raise RailStatusError("gh_pr_rail_paths_invalid_json") from exc
    if not isinstance(pages, list):
        raise RailStatusError("gh_pr_rail_paths_invalid_shape")
    paths: list[str] = []
    file_count = 0
    for page in pages:
        if not isinstance(page, list):
            raise RailStatusError("gh_pr_rail_paths_invalid_shape")
        for item in page:
            if not isinstance(item, dict) or not isinstance(item.get("filename"), str):
                raise RailStatusError("gh_pr_rail_paths_invalid_file")
            file_count += 1
            paths.append(item["filename"])
            previous = item.get("previous_filename")
            if previous is not None:
                if not isinstance(previous, str):
                    raise RailStatusError("gh_pr_rail_paths_invalid_file")
                paths.append(previous)
    second_head, body, second_changed_files = _fetch_pr_head_body(
        repository=repository,
        pr_number=pr_number,
        runner=runner,
    )
    if second_head != first_head:
        raise RailStatusError(
            f"rail_snapshot_head_changed: before={first_head} after={second_head}"
        )
    if first_changed_files != second_changed_files or file_count != second_changed_files:
        raise RailStatusError(
            "rail_snapshot_file_count_mismatch: "
            f"before={first_changed_files} listed={file_count} after={second_changed_files}"
        )
    return second_head, body, tuple(dict.fromkeys(paths))


def decide_pr_rail_status(
    *,
    repository: str,
    pr_number: int,
    expected_head_sha: str,
    runner: Runner = subprocess.run,
    resolver: rail_guard.ApprovedRailApprovalReceiptResolver | None = None,
) -> RailStatusResult:
    """Resolve the live PR and return a production-backed rail decision."""
    head_sha, body, paths = _fetch_pr_snapshot(
        repository=repository,
        pr_number=pr_number,
        runner=runner,
    )
    if head_sha != expected_head_sha.lower():
        raise RailStatusError(
            f"stale_rail_status_head: expected={expected_head_sha.lower()} current={head_sha}"
        )
    rail_paths = rail_guard.rail_paths_from_candidates(paths)
    if not rail_paths:
        return RailStatusResult(
            allowed=True,
            reason="non_rail_paths",
            head_sha=head_sha,
            rail_paths=(),
            receipt_id=None,
            status_state="success",
        )

    declaration = rail_guard.parse_rail_approval_declaration(body)
    receipt_id = declaration.receipt_id if declaration.is_present else None
    if receipt_id is None:
        return RailStatusResult(
            allowed=False,
            reason=declaration.reason,
            head_sha=head_sha,
            rail_paths=rail_paths,
            receipt_id=None,
            status_state="failure",
        )

    decision = rail_guard.decide_rail_path_mutation_with_production_receipt(
        task_id=f"pr-{pr_number}",
        candidate_paths=paths,
        head_sha=head_sha,
        receipt_id=receipt_id,
        resolver=resolver,
        path_binding=rail_guard.RailApprovalPathBinding.PR_DIFF_EXACT_SET,
    )
    infrastructure_errors = {
        "rail_approval_receipt_unreadable",
        "rail_approval_validator_unavailable",
    }
    return RailStatusResult(
        allowed=decision.allowed,
        reason=decision.reason,
        head_sha=head_sha,
        rail_paths=decision.rail_paths,
        receipt_id=receipt_id,
        status_state=(
            "success"
            if decision.allowed
            else "error"
            if decision.reason in infrastructure_errors
            else "failure"
        ),
    )


def _post_status(
    *,
    repository: str,
    head_sha: str,
    state: str,
    description: str,
    runner: Runner,
) -> None:
    owner, repo = _split_repository(repository)
    completed = runner(
        [
            "gh",
            "api",
            f"repos/{owner}/{repo}/statuses/{head_sha}",
            "-f",
            f"state={state}",
            "-f",
            f"context={RAIL_STATUS_CONTEXT}",
            "-f",
            f"description={description[:140]}",
        ],
        capture_output=True,
        text=True,
        check=False,
        env=_gh_env(),
    )
    if completed.returncode != 0:
        raise RailStatusError(
            f"gh_rail_status_failed: sha={head_sha} state={state} exit={completed.returncode}"
        )


def publish_pr_rail_status(
    *,
    repository: str,
    pr_number: int,
    expected_head_sha: str,
    runner: Runner = subprocess.run,
    resolver: rail_guard.ApprovedRailApprovalReceiptResolver | None = None,
) -> RailStatusResult:
    """Decide and publish one rail status on the exact expected PR head."""
    result = decide_pr_rail_status(
        repository=repository,
        pr_number=pr_number,
        expected_head_sha=expected_head_sha,
        runner=runner,
        resolver=resolver,
    )
    description = f"{result.reason}"
    if result.receipt_id:
        description += f" receipt={result.receipt_id}"
    _post_status(
        repository=repository,
        head_sha=result.head_sha,
        state=result.status_state,
        description=description,
        runner=runner,
    )
    return result


__all__ = [
    "RAIL_STATUS_CONTEXT",
    "RailStatusError",
    "RailStatusResult",
    "decide_pr_rail_status",
    "publish_pr_rail_status",
]
