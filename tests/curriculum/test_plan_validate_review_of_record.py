"""Strict plan validation re-checks a promoted plan's review of record (#12114).

Defect class: an unreviewed plan passes strict. Only plan-promote writes the pack's sha256
into a plan, after an APPROVE recorded from a bound dispatch. Strict validation therefore runs
plan-promote's binding check on every promoted plan: a plan whose review has no matching
dispatch record fails strict on the host, and is not_checked only where the run declares the
host-local review state unavailable (CI), which still checks the committed promotion chain.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.build.fresh import plan_manifest, plan_promote
from scripts.curriculum.validate import codes
from scripts.curriculum.validate.report import Report
from scripts.curriculum.validate.validate import validate_plan
from scripts.review import findings_db
from tests.build.plan_review_records import record_plan_review
from tests.build.test_fresh_plan_review import fake_verify
from tests.curriculum.test_plan_validate import LEVEL, SLUG
from tests.helpers.plan_review_world import build_env, validate_provisional

REVIEW_OF_RECORD = {codes.PLAN_REVIEW_NOT_PROMOTED, codes.REVIEW_UNBOUND, codes.REVIEW_STATE_UNAVAILABLE}


def _review_of_record_scenario(root: Path) -> dict[str, Report]:
    """Promote a plan from a bound review, then take its evidence away step by step.

    Returns the strict report of each step, keyed by the step's name.
    """
    tasks = root / "batch_state" / "tasks"
    with pytest.MonkeyPatch.context() as patch:
        patch.setenv("LU_TASKS_DIR", str(tasks))
        patch.setattr(plan_manifest, "verify_pack_strict", fake_verify())
        env = build_env(root)
        assert validate_provisional(env) == 0
        _manifest, digest = plan_manifest.write_plan_manifest(LEVEL, SLUG, repo_root=env.root)
        record_plan_review(env.root, LEVEL, SLUG, digest)
        plan_promote.promote_plan(LEVEL, SLUG, repo_root=env.root)

        def strict(*, declared: bool = False) -> Report:
            return validate_plan(
                LEVEL, SLUG, plan_path=env.plan_path, strict=True, review_state_declared_unavailable=declared
            )

        reports = {"bound": strict()}
        (dispatch_record,) = tasks.glob("*.json")
        dispatch_record.unlink()
        reports["no_dispatch_record"] = strict()
        reports["no_dispatch_record_declared"] = strict(declared=True)
        findings_db.db_path(LEVEL, env.root).unlink()
        reports["no_review_state"] = strict()
        reports["no_review_state_declared"] = strict(declared=True)
        (env.state_dir / plan_manifest.RECEIPT_NAME).unlink()
        reports["no_promotion_receipt_declared"] = strict(declared=True)
    return reports


def produced_review_of_record_codes(root: Path) -> set[str]:
    """Every code the review-of-record check produces, for the code-registry test."""
    return set().union(*(report.codes() for report in _review_of_record_scenario(root).values()))


def _codes(outcomes: list) -> set[str]:
    return {outcome.code for outcome in outcomes} & REVIEW_OF_RECORD


def _message(outcomes: list, code: str) -> str:
    return next(outcome.message for outcome in outcomes if outcome.code == code)


def test_an_unreviewed_promoted_plan_fails_strict_unless_review_state_is_declared_unavailable(tmp_path: Path) -> None:
    reports = _review_of_record_scenario(tmp_path)

    bound = reports["bound"]
    assert _codes(bound.failures) == set() and _codes(bound.not_checked) == set()

    # On the host, a review with no matching dispatch record fails strict, declared or not:
    # the state is present, so the declaration does not apply.
    for name in ("no_dispatch_record", "no_dispatch_record_declared"):
        assert _codes(reports[name].failures) == {codes.REVIEW_UNBOUND}, name
        assert "no usable dispatch record" in _message(reports[name].failures, codes.REVIEW_UNBOUND)

    # Without the host-local review state the binding is undecided: a failure, unless declared.
    assert _codes(reports["no_review_state"].failures) == {codes.REVIEW_STATE_UNAVAILABLE}
    declared = reports["no_review_state_declared"]
    assert _codes(declared.failures) == set()
    assert _codes(declared.not_checked) == {codes.REVIEW_STATE_UNAVAILABLE}
    assert "declared by --not-checked-when-unavailable dispatch_records" in _message(
        declared.not_checked, codes.REVIEW_STATE_UNAVAILABLE
    )

    # The declaration never relaxes the committed chain: a pack hash without its receipt fails.
    assert _codes(reports["no_promotion_receipt_declared"].failures) == {codes.PLAN_REVIEW_NOT_PROMOTED}
