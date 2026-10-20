"""The slow nightly verifies the Atlas manifest only inside its locked project venv (#11030).

Run 39240184497 failed because the manifest check ran with the setup-python
interpreter before ``Install dependencies`` created ``.venv``. The loader then
imported ``jsonschema`` and died, so no slow test ever ran.

These tests execute the workflow's own ``run`` scripts in workflow order in an
offline sandbox. A ``python`` shim stands in for setup-python: it has no project
dependencies. Its ``-m venv`` creates a ``.venv/bin/python`` that gains the
project's packages only after ``pip install -r`` receives a file carrying the
locked ``jsonschema`` pin. The verification step then reaches the real
``load_manifest()`` against controlled pointer and manifest fixtures.
"""

from __future__ import annotations

import copy
import gzip
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "pytest-slow-nightly.yml"
REQUIREMENTS_LOCK = REPO_ROOT / "requirements-lock.txt"
JOB = "pytest-slow"
INSTALL_STEP = "Install dependencies"
VERIFY_STEP = "Verify Atlas manifest matches pointer (rehydrate if stale)"
VERIFIED = "Atlas manifest verified against pointer"
# Verification step as it stood before #11030, ahead of Install dependencies.
ORIGINAL_VERIFY_RUN = (
    "python -c \"import sys; sys.path.insert(0, 'scripts'); "
    "from lexicon.manifest_io import load_manifest; load_manifest(); "
    "print('Atlas manifest verified against pointer')\"\n"
)
# Nothing listens on the discard port, so a hydrate attempt fails offline.
OFFLINE_ASSET_URL = "http://127.0.0.1:9/lexicon-manifest.json.gz"
VALID_MANIFEST = {"generated_at": "2026-01-01T00:00:00+00:00", "entries": []}
# Steps outside the venv/manifest boundary (services, Stanza, network) are not run.
EXECUTED_STEPS = frozenset({INSTALL_STEP})


def _load_workflow() -> dict:
    workflow = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    assert isinstance(workflow, dict), "slow nightly workflow did not parse to a mapping"
    return workflow


def _steps(workflow: dict) -> list[dict]:
    return workflow["jobs"][JOB]["steps"]


def _step(workflow: dict, name: str) -> dict:
    return next(step for step in _steps(workflow) if step.get("name") == name)


def _verify_steps(steps: list[dict]) -> list[dict]:
    return [step for step in steps if "lexicon.manifest_io" in step.get("run", "")]


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _locked_jsonschema() -> str:
    return next(
        line for line in REQUIREMENTS_LOCK.read_text(encoding="utf-8").splitlines() if line.startswith("jsonschema==")
    )


def _write_executable(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")
    path.chmod(0o755)


def _build_sandbox(root: Path, control: str) -> tuple[Path, dict[str, str]]:
    """Create an offline workspace whose manifest loader resolves inside ``root``."""
    workspace = root / "workspace"
    scripts = workspace / "scripts"
    lexicon = scripts / "lexicon"
    lexicon.mkdir(parents=True)
    # Other submodules come from the real packages; only the loader is local,
    # because it resolves its own path to find site/src/data.
    for package, real in ((scripts, REPO_ROOT / "scripts"), (lexicon, REPO_ROOT / "scripts" / "lexicon")):
        (package / "__init__.py").write_text(f"__path__.append({str(real)!r})\n", encoding="utf-8")
    shutil.copy2(REPO_ROOT / "scripts" / "lexicon" / "manifest_io.py", lexicon / "manifest_io.py")
    shutil.copy2(REQUIREMENTS_LOCK, workspace / "requirements-lock.txt")

    data_dir = workspace / "site" / "src" / "data"
    data_dir.mkdir(parents=True)
    cache_dir = root / "manifest-cache"
    cache_dir.mkdir()
    released = json.dumps(VALID_MANIFEST).encode("utf-8")
    gz_bytes = gzip.compress(released, mtime=0)
    if control == "malformed":
        released = b"[]\n"
    (data_dir / "lexicon-manifest.pointer.json").write_text(
        json.dumps(
            {
                "asset_url": OFFLINE_ASSET_URL,
                "release_tag": "atlas-manifest",
                "gz_sha256": _sha256(gz_bytes),
                "json_sha256": _sha256(released),
                "gz_bytes": len(gz_bytes),
                "json_bytes": len(released),
            }
        ),
        encoding="utf-8",
    )
    manifest = data_dir / "lexicon-manifest.json"
    if control in {"valid", "malformed"}:
        manifest.write_bytes(released)
    elif control == "cached":
        (cache_dir / f"{_sha256(gz_bytes)}.json").write_bytes(released)
    elif control == "mismatched":
        manifest.write_bytes(json.dumps({**VALID_MANIFEST, "entries": [{"lemma": "x"}]}).encode())
        (cache_dir / f"{_sha256(gz_bytes)}.json").write_bytes(b'{"entries": "corrupt"}')
    else:
        assert control == "missing", control

    bin_dir = root / "bin"
    bin_dir.mkdir()
    real = sys.executable
    # A venv python with the project packages only after the locked install.
    venv_python = f"""#!/usr/bin/env bash
venv="$(cd "$(dirname "$0")/.." && pwd)"
if [[ "$1 $2 $3" == "-m pip install" ]]; then
  shift 3
  echo "$*" >> "$venv/pip-installs.log"
  while (( $# )); do
    if [[ "$1" == "-r" ]] && grep -qxF '{_locked_jsonschema()}' "$2"; then
      touch "$venv/locked-dependencies"
    fi
    shift
  done
  exit 0
fi
if [[ -e "$venv/locked-dependencies" ]]; then exec '{real}' "$@"; fi
exec '{real}' -S "$@"
"""
    (root / "venv-python").write_text(venv_python, encoding="utf-8")
    # setup-python stand-in: stdlib only, and it can create the venv.
    _write_executable(
        bin_dir / "python",
        f"""#!/usr/bin/env bash
if [[ "$1" == "-m" && "$2" == "venv" ]]; then
  mkdir -p "$3/bin"
  install -m 0755 '{root / "venv-python"}' "$3/bin/python"
  exit 0
fi
exec '{real}' -S "$@"
""",
    )
    runner_temp = root / "runner-temp"
    runner_temp.mkdir()
    home = root / "home"
    home.mkdir()
    env = {
        "PATH": f"{bin_dir}{os.pathsep}/usr/bin{os.pathsep}/bin",
        "HOME": str(home),
        "XDG_CACHE_HOME": str(home / ".cache"),
        "RUNNER_TEMP": str(runner_temp),
        "LU_LEXICON_MANIFEST_CACHE": str(cache_dir),
        "LU_GITHUB_CACHE_DIR": str(home / "github-cache"),
        "PYTHONDONTWRITEBYTECODE": "1",
    }
    return workspace, env


def _run_until_verification(steps: list[dict], root: Path, control: str) -> subprocess.CompletedProcess[str]:
    """Run the job's steps in order and return the manifest verification result."""
    workspace, env = _build_sandbox(root, control)
    for step in steps:
        run = step.get("run")
        if run is None or (step not in _verify_steps(steps) and step.get("name") not in EXECUTED_STEPS):
            continue
        # GitHub's default `run` shell on Linux runners.
        result = subprocess.run(
            ["bash", "--noprofile", "--norc", "-eo", "pipefail", "-c", run],
            cwd=workspace,
            env=env,
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
        if step in _verify_steps(steps):
            return result
        assert result.returncode == 0, f"{step.get('name')} failed in sandbox: {result.stderr}"
    raise AssertionError("no manifest verification step ran")


def _verified(result: subprocess.CompletedProcess[str]) -> bool:
    return result.returncode == 0 and VERIFIED in result.stdout


# (control, must verify): the loader accepts a pinned or cache-rehydrated manifest
# and refuses a missing, mismatched or malformed one.
CONTROLS = (("valid", True), ("cached", True), ("missing", False), ("mismatched", False), ("malformed", False))


def gate_violations(workflow: dict, root: Path) -> list[str]:
    """Return how ``workflow`` fails the fail-closed, venv-ordered manifest gate."""
    steps = _steps(workflow)
    verify = _verify_steps(steps)
    if len(verify) != 1:
        return [f"expected one manifest verification step, found {len(verify)}"]
    violations = []
    if "if" in verify[0] or verify[0].get("continue-on-error"):
        violations.append("manifest verification is conditional or non-blocking")
    slow_tests = next(index for index, step in enumerate(steps) if step.get("id") == "pytest-slow")
    if steps.index(verify[0]) > slow_tests:
        violations.append("manifest verification runs after the slow tests")
    for control, must_verify in CONTROLS:
        result = _run_until_verification(steps, root / control, control)
        if _verified(result) is not must_verify:
            violations.append(f"{control} control: rc={result.returncode} stderr={result.stderr[-400:]!r}")
            break
    return violations


def _move_before(workflow: dict, name: str, anchor: str) -> dict:
    mutated = copy.deepcopy(workflow)
    steps = _steps(mutated)
    step = steps.pop(steps.index(_step(mutated, name)))
    steps.insert(steps.index(_step(mutated, anchor)), step)
    return mutated


def _edit_step(workflow: dict, name: str, **changes: object) -> dict:
    mutated = copy.deepcopy(workflow)
    _step(mutated, name).update(changes)
    return mutated


def _original(workflow: dict) -> dict:
    """The pre-#11030 order: setup interpreter, before the venv exists."""
    mutated = _move_before(workflow, VERIFY_STEP, "Restore pip wheel cache")
    _step(mutated, VERIFY_STEP)["run"] = ORIGINAL_VERIFY_RUN
    return mutated


def test_repaired_workflow_verifies_manifest_in_locked_venv_and_fails_closed(tmp_path: Path) -> None:
    workflow = _load_workflow()
    assert gate_violations(workflow, tmp_path) == []

    steps = _steps(workflow)
    verify = _step(workflow, VERIFY_STEP)
    assert steps.index(_step(workflow, INSTALL_STEP)) < steps.index(verify)
    assert verify["run"].startswith(".venv/bin/python ")


def test_original_order_reproduces_run_39240184497_failure(tmp_path: Path) -> None:
    result = _run_until_verification(_steps(_original(_load_workflow())), tmp_path, "valid")

    assert result.returncode == 1
    assert "ModuleNotFoundError: No module named 'jsonschema'" in result.stderr
    assert "from scripts.atlas.word_card_certification import guard_card_inventory" in result.stderr
    assert gate_violations(_original(_load_workflow()), tmp_path / "gate")


def test_valid_control_records_locked_install_before_loader(tmp_path: Path) -> None:
    result = _run_until_verification(_steps(_load_workflow()), tmp_path, "valid")

    assert _verified(result), result.stderr
    installs = (tmp_path / "workspace" / ".venv" / "pip-installs.log").read_text(encoding="utf-8")
    assert f"--no-deps -r {tmp_path / 'runner-temp' / 'requirements-ci.txt'}" in installs
    assert (tmp_path / "workspace" / ".venv" / "locked-dependencies").exists()


@pytest.mark.parametrize(
    ("control", "refusal"),
    [
        ("missing", "failed to download Atlas manifest release asset"),
        ("mismatched", "failed to download Atlas manifest release asset"),
        ("malformed", "must contain a JSON object"),
    ],
)
def test_repaired_workflow_refuses_bad_manifest(tmp_path: Path, control: str, refusal: str) -> None:
    result = _run_until_verification(_steps(_load_workflow()), tmp_path, control)

    assert result.returncode != 0
    assert VERIFIED not in result.stdout
    assert refusal in result.stderr


def test_cached_control_rehydrates_the_pinned_manifest(tmp_path: Path) -> None:
    result = _run_until_verification(_steps(_load_workflow()), tmp_path, "cached")

    assert _verified(result), result.stderr
    manifest = tmp_path / "workspace" / "site" / "src" / "data" / "lexicon-manifest.json"
    assert json.loads(manifest.read_text(encoding="utf-8")) == VALID_MANIFEST


def _drop_locked_install(workflow: dict) -> dict:
    run = _step(workflow, INSTALL_STEP)["run"]
    kept = "\n".join(line for line in run.splitlines() if '-r "${RUNNER_TEMP}' not in line)
    return _edit_step(workflow, INSTALL_STEP, run=kept + "\n")


def _skip_loader_call(workflow: dict) -> dict:
    run = _step(workflow, VERIFY_STEP)["run"]
    return _edit_step(workflow, VERIFY_STEP, run=re.sub(r"(?m)^load_manifest\(\)\n", "", run))


def _setup_interpreter(workflow: dict) -> dict:
    run = _step(workflow, VERIFY_STEP)["run"]
    return _edit_step(workflow, VERIFY_STEP, run=run.replace(".venv/bin/python -", "python -", 1))


def _drop_verification(workflow: dict) -> dict:
    mutated = copy.deepcopy(workflow)
    _steps(mutated).remove(_step(mutated, VERIFY_STEP))
    return mutated


MUTATIONS = {
    "original-order-and-interpreter": _original,
    "verify-before-install": lambda wf: _move_before(wf, VERIFY_STEP, INSTALL_STEP),
    "verify-with-setup-interpreter": _setup_interpreter,
    "install-without-locked-requirements": _drop_locked_install,
    "verification-removed": _drop_verification,
    "loader-call-removed": _skip_loader_call,
    "continue-on-error": lambda wf: _edit_step(wf, VERIFY_STEP, **{"continue-on-error": True}),
    "conditional-verification": lambda wf: _edit_step(wf, VERIFY_STEP, **{"if": "false"}),
    "verify-after-slow-tests": lambda wf: _move_before(wf, VERIFY_STEP, "Exercise quarantined tests without reruns"),
}


@pytest.mark.parametrize("mutation", sorted(MUTATIONS))
def test_gate_detects_moved_or_suppressed_verification(tmp_path: Path, mutation: str) -> None:
    mutated = MUTATIONS[mutation](_load_workflow())

    assert mutated != _load_workflow()
    assert gate_violations(mutated, tmp_path), f"{mutation} was not detected"


def test_slow_selection_and_failure_reporting_are_preserved() -> None:
    workflow = _load_workflow()
    job = workflow["jobs"][JOB]
    steps = _steps(workflow)

    assert workflow["permissions"] == {"contents": "read"}
    assert job["permissions"] == {"actions": "read", "contents": "read", "issues": "write"}
    assert job["timeout-minutes"] == 120
    assert workflow["concurrency"] == {"group": "pytest-slow-nightly", "cancel-in-progress": False}
    for step in steps:
        if "uses" in step:
            assert re.fullmatch(r"[\w./-]+@[0-9a-f]{40}", step["uses"]), step["uses"]

    slow = next(step for step in steps if step.get("id") == "pytest-slow")
    assert "-m 'slow and not atlas_release'" in slow["run"]
    assert "--timeout=120" in slow["run"]
    assert "if" not in slow
    for name in (
        "Exercise quarantined tests without reruns",
        "Build flake ledger and update expired fix issues",
        "Upload slow pytest evidence",
    ):
        assert _step(workflow, name)["if"] == "always()"
    assert "scripts/ci/flake_ledger.py" in _step(workflow, "Build flake ledger and update expired fix issues")["run"]
