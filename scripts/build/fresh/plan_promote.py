"""plan-promote: after an APPROVE plan review, set the plan's ``evidence_ref.sha256`` to the reviewed provisional pack's.

Transactional (docs/epics/fresh-build-review-contracts.md, Contract 1 "Timing"):
the review must be an APPROVE of the current manifest; every manifest input is
re-hashed and the planned learner state recomputed (any difference means the
APPROVE is stale); the promoted bytes — the plan with only ``evidence_ref.sha256``
changed — pass the full ``--strict`` plan validation in memory; only then are the
reviewed-plan copy, the promotion receipt and, last, the promoted plan published,
each atomically, with the earlier writes undone if a later one fails.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from scripts.build.fresh import plan_manifest as pm
from scripts.build.fresh.path_guard import checked_path
from scripts.curriculum.evidence import lock
from scripts.curriculum.validate.validate import validate_plan


def _current_manifest(root: Path, level: str, slug: str) -> tuple[dict, str]:
    """The current manifest and its sha256, which must agree with its sidecar and history copy."""
    current, sidecar = pm.manifest_paths(root, level, slug)
    if not current.is_file():
        raise pm.PlanReviewError(
            pm.MANIFEST_HASH_MISMATCH, f"no current plan-review manifest: {pm._relative(root, current)}"
        )
    content = current.read_bytes()
    digest = pm.sha256_bytes(content)
    recorded = sidecar.read_text(encoding="ascii").strip() if sidecar.is_file() else None
    if recorded != digest:
        raise pm.PlanReviewError(
            pm.MANIFEST_HASH_MISMATCH,
            f"{pm._relative(root, sidecar)} records {recorded}, the current manifest hashes to {digest}",
        )
    manifest = yaml.safe_load(content)
    pm.validate_manifest_document(manifest)
    return manifest, digest


def promote_plan(level: str, slug: str, *, repo_root: Path, now: datetime | None = None) -> dict[str, Any]:
    """Promote the reviewed plan; returns the receipt (plus ``already_promoted``).

    Raises PlanReviewError, having written nothing, when the review is not an
    APPROVE of the current manifest, any input changed since the review, or the
    promoted bytes fail strict validation.
    """
    root = repo_root.resolve()
    review = pm.read_review(root, level, slug)
    manifest, digest = _current_manifest(root, level, slug)
    if review["manifest_sha256"] != digest:
        raise pm.PlanReviewError(
            pm.MANIFEST_HASH_MISMATCH,
            f"the review approved manifest {review['manifest_sha256']}, the current manifest is {digest}; "
            "a new review is needed",
        )

    freshness = pm.plan_review_freshness(root, manifest, digest)
    directory = pm.state_dir(root, level, slug)
    if freshness.state == "promoted":
        receipt = yaml.safe_load((directory / pm.RECEIPT_NAME).read_bytes())
        return {**receipt, "already_promoted": True}
    if freshness.state == "stale":
        raise pm.PlanReviewError(
            pm.INPUTS_CHANGED_SINCE_REVIEW,
            "the APPROVE is stale, a new review is needed; changed: "
            + "; ".join(f"{path} ({why})" for path, why in sorted(freshness.stale.items())),
            list(freshness.stale),
        )

    plan_path = checked_path(root, f"{pm.TREE}/lesson-plans/{level}/{slug}.yaml", f"{pm.TREE}/lesson-plans")
    pack_path = root / pm.TREE / "evidence" / level / f"{slug}.yaml"
    reviewed_bytes = plan_path.read_bytes()
    pack_sha = pm.file_sha256(pack_path)
    promoted_bytes = pm.promoted_plan_bytes(reviewed_bytes, pack_sha)

    report = validate_plan(level, slug, plan_path=plan_path, strict=True, plan_bytes=promoted_bytes)
    if report.failures or report.waivers:
        raise pm.PlanReviewError(
            pm.PROMOTED_PLAN_INVALID,
            "the promoted plan fails the strict plan validation, nothing was written: "
            + "; ".join(outcome.render() for outcome in (*report.failures, *report.waivers)),
        )

    reviewed_sha = pm.sha256_bytes(reviewed_bytes)
    moment = (now or datetime.now(UTC)).astimezone(UTC).isoformat(timespec="seconds")
    receipt = {
        "manifest_sha256": digest,
        "reviewed_plan_sha256": reviewed_sha,
        "promoted_plan_sha256": pm.sha256_bytes(promoted_bytes),
        "pack_sha256": pack_sha,
        "attempt_id": review["attempt_id"],
        "promoted_at": moment,
    }
    reviewed_copy = checked_path(
        root, (directory / f"plan-reviewed.{reviewed_sha}.yaml").relative_to(root), f"{pm.TREE}/evidence"
    )
    receipt_path = checked_path(root, (directory / pm.RECEIPT_NAME).relative_to(root), f"{pm.TREE}/evidence")
    _publish(
        [
            (reviewed_copy, reviewed_bytes, 0o644),
            (receipt_path, lock.yaml_bytes(receipt), 0o644),
            (plan_path, promoted_bytes, plan_path.stat().st_mode & 0o777),
        ]
    )
    return {**receipt, "already_promoted": False}


def _publish(writes: list[tuple[Path, bytes, int]]) -> None:
    """Write each file atomically, in order; if one fails, put every earlier one back and re-raise."""
    done: list[tuple[Path, bytes | None]] = []
    try:
        for path, content, mode in writes:
            previous = path.read_bytes() if path.is_file() else None
            if previous == content:
                continue
            lock.atomic_write(path, content, mode=mode)
            done.append((path, previous))
    except BaseException as error:
        for path, previous in reversed(done):
            if previous is None:
                path.unlink(missing_ok=True)
            else:
                lock.atomic_write(path, previous)
        if isinstance(error, Exception):
            raise pm.PlanReviewError(pm.PROMOTION_FAILED, f"publishing failed, nothing is promoted: {error}") from error
        raise
