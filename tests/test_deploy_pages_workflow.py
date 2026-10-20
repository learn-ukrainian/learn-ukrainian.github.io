"""Regression checks for the GitHub Pages deployment workflow."""

from pathlib import Path

import pytest
import yaml

from scripts.deploy.auto_deploy_eligibility import (
    AutoDeployDecision,
    decide_auto_deploy,
    format_step_summary,
    main,
    read_nul_delimited_paths,
    write_step_summary,
)

pytestmark = pytest.mark.reads_content

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
        line for line in REQUIREMENTS_LOCK.read_text(encoding="utf-8").splitlines() if line.startswith("PyYAML==")
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


def test_auto_deploy_accepts_only_site_code_since_last_successful_deployment(tmp_path: Path) -> None:
    """#5356: content drift and unknown paths must keep Pages manual-only."""
    assert decide_auto_deploy(["site/src/components/Practice.tsx"]).deploy is True
    assert decide_auto_deploy(["site/src/content/docs/a1/hello.mdx"]).reason == "content_drift"
    assert decide_auto_deploy(["site/src/data/lexicon-manifest.json"]).reason == "content_drift"
    assert decide_auto_deploy(["site/src/lib/lexicon/curated-heteronyms.ts"]).reason == "content_drift"
    assert decide_auto_deploy(["curriculum/l2-uk-en/a1/01-hello.md"]).reason == "content_drift"
    assert decide_auto_deploy(["scripts/build/site.py"]).reason == "unknown_path"
    assert decide_auto_deploy([]).reason == "no_changed_paths"

    changed_paths = tmp_path / "changed-paths.nul"
    changed_paths.write_bytes(b"site/src/components/Practice.tsx\0site/src/styles/app.css\0")
    assert read_nul_delimited_paths(changed_paths) == (
        "site/src/components/Practice.tsx",
        "site/src/styles/app.css",
    )


def test_auto_deploy_allows_release_pointer_bumps_not_bulk_data() -> None:
    """#6733: practice-deck / manifest pointers are site-code; other data is drift."""
    practice_pointer = "site/src/data/lexicon-practice-deck.pointer.json"
    manifest_pointer = "site/src/data/lexicon-manifest.pointer.json"

    practice_only = decide_auto_deploy([practice_pointer])
    assert practice_only.deploy is True
    assert practice_only.reason == "site_code_only"

    manifest_only = decide_auto_deploy([manifest_pointer])
    assert manifest_only.deploy is True
    assert manifest_only.reason == "site_code_only"

    mixed = decide_auto_deploy([practice_pointer, "site/src/components/Practice.tsx"])
    assert mixed.deploy is True
    assert mixed.reason == "site_code_only"

    with_scripts = decide_auto_deploy([practice_pointer, "scripts/practice_deck/publish.py"])
    assert with_scripts.deploy is False
    assert with_scripts.reason == "unknown_path"

    assert decide_auto_deploy(["site/src/data/lexicon-manifest.json"]).reason == "content_drift"
    assert decide_auto_deploy(["site/src/data/lexicon-search-index.json"]).reason == "content_drift"


def test_auto_deploy_dispositions_activity_kit_and_data_paths() -> None:
    """#8306: packages/activity-kit is site code, data/ and registry/ are content drift."""
    # activity-kit alone or mixed with site code is allowed
    ak_component = "packages/activity-kit/src/components/TrueFalse.tsx"
    ak_package = "packages/activity-kit/package.json"
    ak_decision = decide_auto_deploy([ak_component, ak_package])
    assert ak_decision.deploy is True
    assert ak_decision.reason == "site_code_only"
    assert ak_decision.offending_paths == ()

    mixed_site_and_ak = decide_auto_deploy([ak_component, "site/src/pages/index.astro"])
    assert mixed_site_and_ak.deploy is True
    assert mixed_site_and_ak.reason == "site_code_only"

    # data/ and its tracked successor registry/ are content drift, denying auto-deploy
    data_deck = "registry/practice/noun_mechanics_deck.json"
    data_db = "data/sources.db"
    data_decision = decide_auto_deploy([data_deck, data_db])
    assert data_decision.deploy is False
    assert data_decision.reason == "content_drift"
    assert set(data_decision.offending_paths) == {data_deck, data_db}

    # unknown paths (e.g. docs, scripts) are tracked in offending_paths
    unknown_decision = decide_auto_deploy([ak_component, "docs/index.md", "scripts/test.py"])
    assert unknown_decision.deploy is False
    assert unknown_decision.reason == "unknown_path"
    assert set(unknown_decision.offending_paths) == {"docs/index.md", "scripts/test.py"}


def test_auto_deploy_step_summary_and_cli(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """#8306: Step summary and CLI warning output for eligible and skipped deploys."""
    eligible = AutoDeployDecision(deploy=True, reason="site_code_only")
    eligible_summary = format_step_summary(eligible)
    assert "### 🚀 Pages Auto-Deploy: Eligible" in eligible_summary

    skipped_drift = AutoDeployDecision(
        deploy=False,
        reason="content_drift",
        offending_paths=("registry/practice/deck.json", "curriculum/l2/01.md"),
    )
    drift_summary = format_step_summary(skipped_drift)
    assert "### ⚠️ Pages Auto-Deploy: Skipped" in drift_summary
    assert "- **Decision**: `content_drift`" in drift_summary
    assert "- **Offending Paths (2)**:" in drift_summary
    assert "  - `registry/practice/deck.json`" in drift_summary
    assert "  - `curriculum/l2/01.md`" in drift_summary

    # Test summary truncation past 20 items
    many_paths = tuple(f"unknown/file_{i}.txt" for i in range(25))
    overflow_summary = format_step_summary(
        AutoDeployDecision(deploy=False, reason="unknown_path", offending_paths=many_paths)
    )
    assert "- **Offending Paths (25)**:" in overflow_summary
    assert "  - `unknown/file_0.txt`" in overflow_summary
    assert "  - `unknown/file_19.txt`" in overflow_summary
    assert "  - `unknown/file_20.txt`" not in overflow_summary
    assert "  - *... and 5 more*" in overflow_summary

    # Test file writing
    summary_file = tmp_path / "step_summary.md"
    write_step_summary(summary_file, skipped_drift)
    assert summary_file.read_text(encoding="utf-8") == drift_summary

    # Test main CLI execution with skipped run
    changed_file = tmp_path / "changed.nul"
    changed_file.write_bytes(b"docs/readme.md\0")
    output_file = tmp_path / "github_output.txt"
    cli_summary_file = tmp_path / "cli_summary.md"

    main(
        [
            "--changed-paths",
            str(changed_file),
            "--github-output",
            str(output_file),
            "--github-step-summary",
            str(cli_summary_file),
        ]
    )

    captured = capsys.readouterr()
    assert "auto-deploy eligibility: unknown_path" in captured.out
    assert "::warning title=Pages Auto-Deploy Skipped::" in captured.out
    assert "offending: docs/readme.md" in captured.out
    assert "deploy=false\nreason=unknown_path\n" in output_file.read_text(encoding="utf-8")
    assert "### ⚠️ Pages Auto-Deploy: Skipped" in cli_summary_file.read_text(encoding="utf-8")


def test_pages_build_publishes_the_pinned_word_card_preview() -> None:
    """#11194: the standard build verifies the pinned release, then builds the preview from it."""
    workflow = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    steps = workflow["jobs"]["deploy"]["steps"]
    by_name = {step.get("name"): step for step in steps}

    prepare = by_name["Prepare pinned word-card preview release"]
    build_site = by_name["Build Site"]
    verify = by_name["Verify word-card preview routes"]
    assert prepare["id"] == "word-card-preview"
    assert prepare["working-directory"] == "."
    assert prepare["env"] == {"RELEASE_DIR": "${{ runner.temp }}/word-card-preview-release"}
    assert prepare["run"] == (
        ".venv/bin/python scripts/deploy/prepare_word_card_preview.py prepare "
        '--dest "$RELEASE_DIR" --github-output "$GITHUB_OUTPUT"'
    )

    assert build_site["env"] == {
        "ATLAS_WORD_CARD_PREVIEW": "1",
        "ATLAS_WORD_CARD_RELEASE_PATH": "${{ steps.word-card-preview.outputs.release-path }}",
        "ATLAS_WORD_CARD_RELEASE_PIN": "${{ steps.word-card-preview.outputs.pin }}",
    }
    assert 'if [[ -n "${PUBLIC_ATLAS_WORD_CARD_PREVIEW_CONTROLS+set}" ]]; then' in build_site["run"]
    assert build_site["run"].rstrip().endswith("npm run build")

    assert verify["working-directory"] == "."
    assert verify["env"] == {"RELEASE_DIR": "${{ steps.word-card-preview.outputs.release-path }}"}
    assert verify["run"] == (
        '.venv/bin/python scripts/deploy/prepare_word_card_preview.py verify-dist site/dist --release-dir "$RELEASE_DIR"'
    )

    order = [
        steps.index(by_name[name])
        for name in (
            "Create Python venv",
            "Prepare pinned word-card preview release",
            "Build Site",
            "Verify word-card preview routes",
            "Emit immutable deployment marker",
            "Vendor Atlas runtime tree",
            "Check published-site size (fail-closed)",
            "Upload artifact",
            "Deploy to GitHub Pages",
        )
    ]
    assert order == sorted(order)


def test_pages_preview_wiring_has_no_controls_flag_secrets_or_dispatch_inputs() -> None:
    """#11194: the test-only controls flag never reaches publication; no token or input drives the preview."""
    workflow_text = WORKFLOW.read_text(encoding="utf-8")
    workflow = yaml.safe_load(workflow_text)
    deploy = workflow["jobs"]["deploy"]
    steps = deploy["steps"]
    by_name = {step.get("name"): step for step in steps}

    for scope in (workflow, deploy, *steps):
        assert "PUBLIC_ATLAS_WORD_CARD_PREVIEW_CONTROLS" not in (scope.get("env") or {})
    assert "PUBLIC_ATLAS_WORD_CARD_PREVIEW_CONTROLS:" not in workflow_text
    # PyYAML reads the bare ``on`` key as boolean True.
    assert workflow[True]["workflow_dispatch"] is None
    assert deploy["permissions"] == {"contents": "read", "pages": "write", "id-token": "write"}

    for name in ("Prepare pinned word-card preview release", "Build Site", "Verify word-card preview routes"):
        step = by_name[name]
        assert "${{" not in step["run"], f"{name}: expressions must reach run scripts via env only"
        env_blob = yaml.safe_dump(step.get("env") or {})
        for forbidden in ("secrets.", "github.token", "GITHUB_TOKEN", "GH_TOKEN", "inputs.", "github.event"):
            assert forbidden not in env_blob, f"{name}: {forbidden}"

    # Vite also reads these dotenv files for a production build.
    for name in (".env", ".env.local", ".env.production", ".env.production.local", ".env.example"):
        env_file = REPO_ROOT / "site" / name
        if env_file.is_file():
            assert "PUBLIC_ATLAS_WORD_CARD_PREVIEW_CONTROLS" not in env_file.read_text(encoding="utf-8")


def test_preview_pin_changes_keep_manual_deployment_semantics() -> None:
    """#11194 leaves eligibility unchanged: a release-pin change is content drift, not auto-deployable."""
    pin = "site/src/data/word-card-preview-release.pin.json"
    assert (REPO_ROOT / pin).is_file()
    assert decide_auto_deploy([pin]).reason == "content_drift"
    assert decide_auto_deploy(["scripts/deploy/prepare_word_card_preview.py"]).reason == "unknown_path"
    assert decide_auto_deploy([".github/workflows/deploy-pages.yml"]).reason == "unknown_path"


def test_pages_workflow_uses_fail_closed_auto_deploy_preflight() -> None:
    """The manual certification route remains available beside the push preflight."""
    workflow_text = WORKFLOW.read_text(encoding="utf-8")
    trigger_block = workflow_text.split("on:\n", 1)[1].split("permissions:\n", 1)[0]
    workflow = yaml.safe_load(workflow_text)

    assert "push:\n    branches: [main]" in trigger_block
    assert "workflow_dispatch:" in trigger_block
    assert workflow["permissions"]["actions"] == "read"
    assert workflow["permissions"]["deployments"] == "read"

    eligibility = workflow["jobs"]["auto-deploy-eligibility"]
    assert eligibility["if"] == "github.event_name == 'push'"
    assert eligibility["outputs"]["deploy"] == "${{ steps.classify.outputs.deploy }}"

    deploy = workflow["jobs"]["deploy"]
    assert deploy["needs"] == "auto-deploy-eligibility"
    assert "workflow_dispatch" in deploy["if"]
    assert "outputs.deploy == 'true'" in deploy["if"]

    preflight = "\n".join(step.get("run", "") for step in eligibility["steps"])
    assert "deployments?environment=github-pages" in preflight
    assert "git cat-file -e" in preflight
    assert "git merge-base --is-ancestor" in preflight
    assert "git diff --no-renames --name-only --diff-filter=ACDMRT -z" in preflight
    assert "scripts/deploy/auto_deploy_eligibility.py" in preflight
    assert "--github-step-summary" in preflight
    assert "::warning title=Pages Auto-Deploy Skipped::" in preflight
