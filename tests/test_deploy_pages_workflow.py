"""Regression checks for the GitHub Pages deployment workflow."""

from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "deploy-pages.yml"
REQUIREMENTS_LOCK = REPO_ROOT / "requirements-lock.txt"


def test_pages_build_installs_atlas_python_dependencies() -> None:
    """The deploy venv must satisfy imports used by ``npm run build``."""
    workflow = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    steps = workflow["jobs"]["deploy"]["steps"]
    create_venv = next(step for step in steps if step.get("name") == "Create Python venv")
    build_site = next(step for step in steps if step.get("name") == "Build Site")
    locked_pyyaml = next(
        line
        for line in REQUIREMENTS_LOCK.read_text(encoding="utf-8").splitlines()
        if line.startswith("PyYAML==")
    )

    assert f".venv/bin/python -m pip install {locked_pyyaml}" in create_venv["run"]
    assert steps.index(create_venv) < steps.index(build_site)


def test_pages_deploy_uses_normal_build_and_fail_closed_size_gate() -> None:
    """#5274: deploy must not run build:full; size gate before artifact upload."""
    workflow = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    steps = workflow["jobs"]["deploy"]["steps"]
    by_name = {step.get("name"): step for step in steps}

    build_site = by_name["Build Site"]
    assert "npm run build" in build_site["run"]
    assert "build:full" not in build_site["run"]

    size_gate = by_name["Check published-site size (fail-closed)"]
    assert size_gate["env"]["DEPLOY_PROFILE"] == "github-pages"
    assert "scripts/deploy/check_site_size.py" in size_gate["run"]

    upload = by_name["Upload artifact"]
    assert steps.index(size_gate) < steps.index(upload)
    assert steps.index(build_site) < steps.index(size_gate)
