"""Regression coverage for the BIO preparation-only CI lane (#4431)."""

from __future__ import annotations

import fnmatch
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
CI_WORKFLOW = REPO_ROOT / ".github/workflows/ci.yml"
FILTER_ACTION = REPO_ROOT / ".github/actions/paths-filter-retry/action.yml"

BIO_PREPARATION_PATHS = (
    "curriculum/l2-uk-en/plans/bio/knyahynia-olha.yaml",
    "curriculum/l2-uk-en/bio/discovery/knyahynia-olha.yaml",
    "curriculum/l2-uk-en/bio/promotion-evidence.yaml",
    "docs/research/bio/knyahynia-olha.md",
    "wiki/figures/knyahynia-olha.md",
    "wiki/figures/knyahynia-olha.sources.yaml",
)

RUNTIME_CURRICULUM_GLOBS = {
    "curriculum/l2-uk-en/curriculum.yaml",
    "curriculum/l2-uk-en/!(plans|bio)/**",
    "curriculum/l2-uk-en/plans/!(bio)/**",
    "curriculum/l2-uk-en/bio/!(*promotion-evidence.yaml|discovery)/**",
}


def _workflow() -> dict:
    return yaml.safe_load(CI_WORKFLOW.read_text(encoding="utf-8"))


def _filters() -> dict[str, list[str]]:
    workflow = _workflow()
    filter_step = next(
        step for step in workflow["jobs"]["changes"]["steps"] if step.get("id") == "filter"
    )
    return yaml.safe_load(filter_step["with"]["filters"])


def test_preparation_filter_covers_every_bio_capsule_surface() -> None:
    globs = _filters()["preparation"]
    uncovered = [
        path for path in BIO_PREPARATION_PATHS if not any(fnmatch.fnmatch(path, glob) for glob in globs)
    ]
    assert not uncovered


def test_preparation_routing_is_advisory_only() -> None:
    """#5744: path routing may inform reporting, never required-job selection."""
    workflow = _workflow()
    assert workflow["jobs"]["changes"]["name"] == "Advisory path classification"
    required = workflow["jobs"]["ci-gate"]["needs"]
    assert "changes" not in required
    assert "preparation" in _filters()


def test_preparation_output_is_exposed_for_advisory_consumers() -> None:
    action = yaml.safe_load(FILTER_ACTION.read_text(encoding="utf-8"))
    assert "preparation" in action["outputs"]

    jobs = _workflow()["jobs"]
    assert jobs["changes"]["outputs"]["preparation"] == "${{ steps.filter.outputs.preparation }}"
    assert "changes" not in jobs["ci-gate"]["needs"]


def test_required_suite_does_not_use_preparation_selection() -> None:
    workflow = _workflow()
    for job_name in workflow["jobs"]["ci-gate"]["needs"]:
        assert "needs.changes.outputs.preparation" not in str(workflow["jobs"][job_name])
