"""Regression coverage for the BIO preparation gate (#4431, #5766).

The gate lives in ``scripts/ci/bio_preparation_gate.py`` and runs from
``scripts/ci/checks.sh`` in ci.yml's ``checks`` job on every event. What is
defended here:

* the validator is reachable from the one required gate (``ci-gate``) and
  nothing can skip it (no job-level or step-level ``if:``, and checks.sh runs
  every check unconditionally);
* its change detection is intact (rename decomposition + registry-entry tracking);
* the path classifier deciding *which* BIO files it validates still recognises
  every capsule surface, exercised directly.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from scripts.ci.bio_preparation_gate import is_bio_preparation_path

REPO_ROOT = Path(__file__).resolve().parents[1]
CI_WORKFLOW = REPO_ROOT / ".github/workflows/ci.yml"
CHECKS_SCRIPT = REPO_ROOT / "scripts/ci/checks.sh"
GATE_SCRIPT = REPO_ROOT / "scripts/ci/bio_preparation_gate.py"

pytestmark = [pytest.mark.repo_invariant, pytest.mark.reads_content]

VALIDATOR_CHECK = 'check "Validate BIO preparation capsules and active holds" .venv/bin/python -m scripts.ci.bio_preparation_gate'

BIO_PREPARATION_PATHS = (
    "curriculum/l2-uk-en/plans/bio/knyahynia-olha.yaml",
    "curriculum/l2-uk-en/bio/discovery/knyahynia-olha.yaml",
    "curriculum/l2-uk-en/bio/promotion-evidence.yaml",
    "docs/research/bio/knyahynia-olha.md",
    "wiki/figures/knyahynia-olha.md",
    "wiki/figures/knyahynia-olha.sources.yaml",
)

NON_PREPARATION_PATHS = (
    "scripts/build/v7_build.py",
    "tests/test_bio_preparation_ci_routing.py",
    "curriculum/l2-uk-en/plans/a1/greetings.yaml",
    "wiki/figures/not-in-the-bio-manifest.md",
)

MANIFEST_SET = {"knyahynia-olha"}


def _checks_job() -> tuple[dict, dict]:
    workflow = yaml.safe_load(CI_WORKFLOW.read_text(encoding="utf-8"))
    job = workflow["jobs"]["checks"]
    step = next(step for step in job["steps"] if "scripts/ci/checks.sh" in str(step.get("run", "")))
    return workflow, job | {"_step": step}


def test_bio_preparation_validator_is_reachable_from_the_required_gate() -> None:
    workflow, _ = _checks_job()
    assert "checks" in workflow["jobs"]["ci-gate"]["needs"]
    assert VALIDATOR_CHECK in CHECKS_SCRIPT.read_text(encoding="utf-8").splitlines()


def test_nothing_can_skip_the_bio_preparation_validator() -> None:
    _, job = _checks_job()
    # The one skip: a merge-queue run reusing a green full run of the identical
    # tree, whose Checks job (this validator included) already passed.
    assert job.get("if") == "${{ !cancelled() && needs.reuse.outputs.reuse != 'true' }}", (
        "the checks job may be skipped only on a recorded merge-queue reuse"
    )
    assert "if" not in job["_step"], "the checks.sh step carries an `if:` and could be skipped"
    # checks.sh runs every check at top level, never inside a condition.
    assert any(line == VALIDATOR_CHECK for line in CHECKS_SCRIPT.read_text(encoding="utf-8").splitlines())


def test_validator_change_detection_is_intact() -> None:
    script = GATE_SCRIPT.read_text(encoding="utf-8")
    assert '"--no-renames"' in script, "rename decomposition dropped"
    assert '_git_names(base_sha, head_sha, "AM")' in script
    assert '_git_names(base_sha, head_sha, "D")' in script
    assert '_show(f"{base_sha}:{REGISTRY_REL}"' in script
    assert "changed_slugs.update(registry_changed_slugs)" in script


@pytest.mark.parametrize("raw_path", BIO_PREPARATION_PATHS)
def test_path_classifier_recognises_every_bio_capsule_surface(raw_path: str) -> None:
    assert is_bio_preparation_path(raw_path, MANIFEST_SET) is True, (
        f"{raw_path} is a BIO capsule surface but the validator does not classify it as one"
    )


@pytest.mark.parametrize("raw_path", NON_PREPARATION_PATHS)
def test_path_classifier_does_not_over_claim(raw_path: str) -> None:
    assert is_bio_preparation_path(raw_path, MANIFEST_SET) is False, (
        f"{raw_path} is not a BIO preparation surface but the validator classifies it as one"
    )
