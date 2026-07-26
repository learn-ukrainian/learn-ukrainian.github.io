"""Regression coverage for the BIO preparation gate (#4431), rebooted for #5766.

Before #5766 this file defended a *selection* mechanism: a ``changes`` job computed a
``preparation`` path filter, and a dedicated ``bio-preparation-data`` job ran only when that
filter matched. Two of the original four tests asserted directly on those YAML path filters.

#5766 deletes changed-files selection entirely — every gate job now runs on every PR — so those
two tests lost their subject. The invariant they defended ("editing a BIO capsule surface reaches
the preparation validator") did not disappear; it became unconditional and true by construction,
which is strictly stronger than a path filter that had to be kept in sync by hand.

What genuinely still needs defending, and is covered here:

* the validator survived the move into the ``contracts`` job and is reachable from the one
  required gate (``ci-gate``);
* nothing can silently skip it — no ``if:`` on either the job or the step;
* its internal change detection is intact (rename decomposition + registry-entry tracking);
* the path classifier deciding *which* BIO files it validates still recognises every capsule
  surface. That logic moved out of the YAML filter and into the embedded script, so it is
  extracted and exercised directly rather than asserted textually.
"""

from __future__ import annotations

import ast
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
CI_WORKFLOW = REPO_ROOT / ".github/workflows/ci.yml"

VALIDATOR_STEP_NAME = "Validate BIO preparation capsules and active holds"

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


def _workflow() -> dict:
    return yaml.safe_load(CI_WORKFLOW.read_text(encoding="utf-8"))


def _validator_job_and_step() -> tuple[str, dict, dict]:
    """Locate the validator wherever it lives, so a future move fails loudly, not silently."""
    workflow = _workflow()
    for job_name, job in workflow["jobs"].items():
        for step in job.get("steps", []):
            if step.get("name") == VALIDATOR_STEP_NAME:
                return job_name, job, step
    raise AssertionError(
        f"the BIO preparation validator step {VALIDATOR_STEP_NAME!r} is not in ci.yml at all — "
        "the gate has been deleted, not moved"
    )


def _validator_python_body() -> str:
    """Strip the ``python - <<'PY' ... PY`` heredoc wrapper off the embedded script."""
    _, _, step = _validator_job_and_step()
    lines = step["run"].splitlines()
    assert lines[0].endswith("<<'PY'"), f"unexpected validator invocation: {lines[0]!r}"
    assert lines[-1].strip() == "PY", f"unexpected heredoc terminator: {lines[-1]!r}"
    return "\n".join(lines[1:-1])


def _classifier():
    """Compile ``is_bio_preparation_path`` out of the embedded script and bind its closure."""
    tree = ast.parse(_validator_python_body())
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == "is_bio_preparation_path":
            namespace: dict = {"Path": Path, "manifest_set": MANIFEST_SET}
            module = ast.Module(body=[node], type_ignores=[])
            exec(compile(module, filename="<ci.yml embedded validator>", mode="exec"), namespace)
            return namespace["is_bio_preparation_path"]
    raise AssertionError("is_bio_preparation_path() is no longer defined in the embedded validator script")


def _registry_entries(root: Path, registry_rel: str, subprocess_module):
    """Compile the embedded registry reader with controllable I/O."""
    tree = ast.parse(_validator_python_body())
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == "registry_entries":
            namespace = {
                "root": root,
                "registry_rel": registry_rel,
                "subprocess": subprocess_module,
                "yaml": yaml,
            }
            module = ast.Module(body=[node], type_ignores=[])
            exec(compile(module, filename="<ci.yml embedded validator>", mode="exec"), namespace)
            return namespace["registry_entries"]
    raise AssertionError("registry_entries() is no longer defined in the embedded validator script")


def test_bio_preparation_validator_is_reachable_from_the_required_gate() -> None:
    job_name, _, _ = _validator_job_and_step()
    required = _workflow()["jobs"]["ci-gate"]["needs"]
    assert job_name in required, (
        f"the BIO preparation validator runs in job {job_name!r}, which CI Gate does not require "
        f"(requires: {required}) — CI Gate could pass while BIO preparation validation failed"
    )


def test_nothing_can_skip_the_bio_preparation_validator() -> None:
    job_name, job, step = _validator_job_and_step()
    assert "if" not in job, (
        f"job {job_name!r} carries an `if:` — the BIO preparation gate must not be conditional now "
        "that changed-files selection is gone (#5766)"
    )
    assert "if" not in step, f"the {VALIDATOR_STEP_NAME!r} step carries an `if:` and could be skipped"


def test_validator_change_detection_is_intact() -> None:
    script = _validator_python_body()
    assert '["git", "diff", "--name-only", "--no-renames", base_sha, "HEAD"]' in script
    assert '"--name-status", "--no-renames", base_sha, "HEAD", "--", registry_rel' not in script
    assert '"git", "show", f"{ref}:{registry_rel}"' in script
    assert "except (FileNotFoundError, subprocess.CalledProcessError):" in script
    assert "registry_changed_slugs" in script
    assert "changed_slugs.update(registry_changed_slugs)" in script


def test_registry_reader_tolerates_absent_historical_or_head_registry(tmp_path: Path) -> None:
    reader = _registry_entries(tmp_path, "promotion-evidence.yaml", subprocess)

    assert reader("historical-sha") == {}
    assert reader("HEAD") == {}


def test_registry_reader_uses_the_ref_it_received(tmp_path: Path) -> None:
    observed: list[list[str]] = []

    class FakeSubprocess:
        CalledProcessError = subprocess.CalledProcessError

        @staticmethod
        def run(arguments: list[str], **_kwargs) -> SimpleNamespace:
            observed.append(arguments)
            return SimpleNamespace(stdout="version: 1\nentries:\n  demo: {}\n")

    reader = _registry_entries(tmp_path, "promotion-evidence.yaml", FakeSubprocess)

    assert reader("historical-sha") == {"demo": {}}
    assert observed == [["git", "show", "historical-sha:promotion-evidence.yaml"]]


@pytest.mark.parametrize("raw_path", BIO_PREPARATION_PATHS)
def test_path_classifier_recognises_every_bio_capsule_surface(raw_path: str) -> None:
    assert _classifier()(raw_path) is True, (
        f"{raw_path} is a BIO capsule surface but the validator does not classify it as one"
    )


@pytest.mark.parametrize("raw_path", NON_PREPARATION_PATHS)
def test_path_classifier_does_not_over_claim(raw_path: str) -> None:
    assert _classifier()(raw_path) is False, (
        f"{raw_path} is not a BIO preparation surface but the validator classifies it as one"
    )
