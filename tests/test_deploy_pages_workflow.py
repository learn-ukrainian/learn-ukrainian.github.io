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


def test_pages_deploy_vendors_atlas_tree_after_build_before_size_gate() -> None:
    """PR3 D1/R1/R7: feature-flagged atlas vendoring between build and size gate."""
    workflow = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    steps = workflow["jobs"]["deploy"]["steps"]
    by_name = {step.get("name"): step for step in steps}

    build_site = by_name["Build Site"]
    vendor = by_name["Vendor Atlas runtime tree"]
    size_gate = by_name["Check published-site size (fail-closed)"]
    upload = by_name["Upload artifact"]

    assert "scripts/deploy/vendor_atlas_tree.py" in vendor["run"]
    assert vendor["env"]["ATLAS_TREE_ASSET_ID"] == "${{ vars.ATLAS_TREE_ASSET_ID }}"
    assert vendor["env"]["ATLAS_TREE_SHA256"] == "${{ vars.ATLAS_TREE_SHA256 }}"
    # Pin is asset id + digest — never a mutable release tag env.
    env_blob = yaml.safe_dump(vendor.get("env") or {})
    assert "ATLAS_TREE_TAG" not in env_blob
    assert "release_tag" not in env_blob

    assert steps.index(build_site) < steps.index(vendor)
    assert steps.index(vendor) < steps.index(size_gate)
    assert steps.index(size_gate) < steps.index(upload)
