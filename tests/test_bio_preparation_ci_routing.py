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


def test_bio_preparation_is_removed_from_broad_python_and_frontend_routes() -> None:
    filters = _filters()
    for route in ("python", "frontend"):
        globs = set(filters[route])
        assert "curriculum/l2-uk-en/**" not in globs
        assert globs >= RUNTIME_CURRICULUM_GLOBS

    # Mixed PRs remain fail-open: application/test paths still select Python,
    # and BIO learner bundles still select both broad runtime routes.
    assert "scripts/**/*.py" in filters["python"]
    assert "tests/**/*.py" in filters["python"]


def test_preparation_output_and_required_gate_are_wired_end_to_end() -> None:
    action = yaml.safe_load(FILTER_ACTION.read_text(encoding="utf-8"))
    assert "preparation" in action["outputs"]

    jobs = _workflow()["jobs"]
    assert jobs["changes"]["outputs"]["preparation"] == "${{ steps.filter.outputs.preparation }}"
    assert jobs["bio-preparation-data"]["if"] == "needs.changes.outputs.preparation == 'true'"
    assert "bio-preparation-data" in jobs["ci-gate"]["needs"]


def test_preparation_gate_tracks_registry_entry_changes_and_decomposes_renames() -> None:
    steps = _workflow()["jobs"]["bio-preparation-data"]["steps"]
    validator = next(step for step in steps if step.get("name") == "Validate BIO preparation capsules and active holds")
    script = validator["run"]

    assert script.count('"--no-renames"') == 2
    assert '"git", "show", f"{base_sha}:{registry_rel}"' in script
    assert "registry_changed_slugs" in script
    assert "changed_slugs.update(registry_changed_slugs)" in script
