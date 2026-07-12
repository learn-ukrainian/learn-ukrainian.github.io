"""Regression checks for the GitHub Pages deployment workflow."""

from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "deploy-pages.yml"
REQUIREMENTS_LOCK = REPO_ROOT / "requirements-lock.txt"


def test_pages_build_installs_atlas_python_dependencies() -> None:
    """The deploy venv must satisfy imports used by ``npm run build:full``."""
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
