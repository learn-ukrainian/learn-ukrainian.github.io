"""Regression tests for deploy-script idempotency checks."""

from __future__ import annotations

import shlex
import shutil
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PROJECT_PYTHON = REPO_ROOT / ".venv" / "bin" / "python"
DEPLOY_SCRIPT = Path("scripts/deploy_prompts.sh")
CHECK_SCRIPT = Path("scripts/check_rules_deployment.sh")
ORPHAN_PATHS_FILE = Path("scripts/deploy_orphan_paths.sh")
ORPHAN_PATH_VARS = (
    "ORPHAN_PATHS_CLAUDE",
    "ORPHAN_PATHS_AGENT",  # kept for compat (empty; .agent/ preserve-by-default)
    "ORPHAN_PATHS_AGENTS",
    "ORPHAN_PATHS_CODEX",
    "ORPHAN_PATHS_GEMINI",
)
DRIFT_TARGET = Path(".claude/rules/pipeline.md")
CODEX_HOOK_TARGET = Path(".codex/hooks/session-setup.sh")
CODEX_HOOKS_CONFIG = Path(".codex/hooks.json")
PROMPT_CONTRACT_MANIFEST = Path("prompt-contracts/manifests/curriculum-lifecycle.module.v1.yaml")
READINESS_PROFILE_CONFIG = Path("curriculum-lifecycle/config/readiness-profiles.v1.yaml")
COORDINATOR_CONFIG = Path("curriculum-lifecycle/config/coordinator.v1.yaml")
UNSCOPED_RULE_FILES = (
    "operator-expectations.md",
    "critical-rules.md",
    "non-negotiable-rules.md",
    "workflow.md",
    "fleet-comms-coordination.md",
    "delegate-must-use-worktree.md",
    "cli-help-standard.md",
    "model-assignment.md",
)
CLAUDE_RULE_FILES = (
    "_load-via-api.md",
    "activity-yaml.md",
    "mcp-sources-and-dictionaries.md",
    "pipeline.md",
    "ukrainian-linguistics.md",
)


def _copy_repo_subset(target: Path) -> None:
    for directory in ("agents_extensions/shared", "agents_extensions/codex", "gemini_extensions"):
        shutil.copytree(REPO_ROOT / directory, target / directory, symlinks=True)

    for relative_path in (
        DEPLOY_SCRIPT,
        CHECK_SCRIPT,
        ORPHAN_PATHS_FILE,
        Path("scripts/lint_prompts.py"),
        Path("scripts/lint/lint_prompts.py"),
        Path("scripts/lint/lint_agent_skills.py"),
        Path(".gemini/config.yaml"),
    ):
        destination = target / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPO_ROOT / relative_path, destination)

    bin_dir = target / ".venv" / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    python_wrapper = bin_dir / "python"
    python_wrapper.write_text(
        f'#!/usr/bin/env bash\nexec {shlex.quote(str(PROJECT_PYTHON))} "$@"\n',
        encoding="utf-8",
    )
    python_wrapper.chmod(0o755)


def _init_checkout(tmp_path: Path) -> Path:
    assert PROJECT_PYTHON.exists(), f"Expected interpreter missing: {PROJECT_PYTHON}"
    repo = tmp_path / "repo"
    repo.mkdir()
    _copy_repo_subset(repo)
    return repo


def _run(repo: Path, script: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(script)],
        cwd=repo,
        capture_output=True,
        check=False,
        text=True,
    )


def _run_command(repo: Path, command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=repo,
        capture_output=True,
        check=False,
        text=True,
    )


def test_fresh_deploy_produces_synced_output(tmp_path: Path) -> None:
    """A clean checkout should deploy successfully and pass drift checks."""
    repo = _init_checkout(tmp_path)

    deploy_result = _run(repo, DEPLOY_SCRIPT)
    assert deploy_result.returncode == 0, (
        f"deploy failed:\nstdout: {deploy_result.stdout}\nstderr: {deploy_result.stderr}"
    )

    check_result = _run(repo, CHECK_SCRIPT)
    assert check_result.returncode == 0, (
        f"drift check failed after fresh deploy:\nstdout: {check_result.stdout}\nstderr: {check_result.stderr}"
    )
    assert (repo / CODEX_HOOK_TARGET).exists()
    assert (repo / CODEX_HOOKS_CONFIG).exists()
    assert (repo / CODEX_HOOKS_CONFIG).read_text(encoding="utf-8") == (
        repo / "agents_extensions" / "codex" / "hooks.json"
    ).read_text(encoding="utf-8")
    assert (repo / ".codex" / "memory" / "MEMORY.md").exists()
    assert (repo / ".gemini/config.yaml").exists()
    assert (repo / ".gemini/skills/final-review/SKILL.md").exists()
    assert (repo / ".gemini/skills/post-build-review/SKILL.md").exists()
    deployed_claude_rules = sorted(path.name for path in (repo / ".claude" / "rules").glob("*.md"))
    assert deployed_claude_rules == sorted(CLAUDE_RULE_FILES)
    for filename in UNSCOPED_RULE_FILES:
        assert not (repo / ".claude" / "rules" / filename).exists()
        assert (repo / ".agent" / "rules" / filename).exists()
        assert (repo / ".gemini" / "rules" / filename).exists()
        assert (repo / ".codex" / "rules" / filename).exists()
    for shared_file in (PROMPT_CONTRACT_MANIFEST, READINESS_PROFILE_CONFIG, COORDINATOR_CONFIG):
        canonical = repo / "agents_extensions/shared" / shared_file
        for mirror_root in (".claude", ".agent", ".codex"):
            assert (repo / mirror_root / shared_file).read_bytes() == canonical.read_bytes()

    codex_hooks_diff = _run_command(
        repo,
        ["diff", "-rq", "agents_extensions/shared/hooks", ".codex/hooks"],
    )
    assert codex_hooks_diff.returncode == 0, (
        f"Codex hooks drift after fresh deploy:\nstdout: {codex_hooks_diff.stdout}\nstderr: {codex_hooks_diff.stderr}"
    )


def test_claude_rule_exclusion_list_covers_unscoped_files() -> None:
    """The Claude-only exclusion list must cover every always-load rule."""
    shared = (REPO_ROOT / ORPHAN_PATHS_FILE).read_text(encoding="utf-8")
    for filename in UNSCOPED_RULE_FILES:
        assert f'"rules/{filename}"' in shared


def _bash_orphan_sets() -> dict[str, frozenset[str]]:
    """Source deploy_orphan_paths.sh and return word-split path sets."""
    bash = """
set -euo pipefail
source scripts/deploy_orphan_paths.sh
echo "CLAUDE:${ORPHAN_PATHS_CLAUDE} ${CLAUDE_RULE_AUTOLOAD_EXCLUDE_PATHS}"
echo "AGENT:${ORPHAN_PATHS_AGENT}"
echo "AGENTS:${ORPHAN_PATHS_AGENTS}"
echo "CODEX:${ORPHAN_PATHS_CODEX} ${CODEX_OVERLAY_PATHS}"
echo "GEMINI:${ORPHAN_PATHS_GEMINI}"
"""
    result = subprocess.run(
        ["bash", "-c", bash],
        cwd=REPO_ROOT,
        capture_output=True,
        check=True,
        text=True,
    )
    sets: dict[str, frozenset[str]] = {}
    for line in result.stdout.splitlines():
        label, _, paths = line.partition(":")
        tokens = [token for token in paths.split() if token]
        sets[label] = frozenset(tokens)
    return sets


def test_orphan_allowlist_single_sourced_no_inline_literals() -> None:
    """Deploy and checker must source deploy_orphan_paths.sh — no duplicate literals."""
    deploy = (REPO_ROOT / DEPLOY_SCRIPT).read_text(encoding="utf-8")
    check = (REPO_ROOT / CHECK_SCRIPT).read_text(encoding="utf-8")
    shared = (REPO_ROOT / ORPHAN_PATHS_FILE).read_text(encoding="utf-8")

    assert 'source "$PROJECT_ROOT/scripts/deploy_orphan_paths.sh"' in deploy
    assert 'source "$PROJECT_ROOT/scripts/deploy_orphan_paths.sh"' in check

    for var in ORPHAN_PATH_VARS:
        assert f'{var}="' in shared, f"{var} missing from shared orphan allowlist"
        assert f'{var}="' not in deploy, f"{var} duplicated inline in deploy script"
        assert f'{var}="' not in check, f"{var} duplicated inline in checker script"

    assert 'CODEX_OVERLAY_PATHS="' in shared
    assert 'CODEX_OVERLAY_PATHS="' not in deploy
    assert 'CODEX_OVERLAY_PATHS="' not in check

    # Literal orphan tokens must not reappear as checker check_pair args.
    assert '"dispatch-briefs" \\' not in check
    assert '"*-handoff.md" \\' not in check
    assert '"hooks.json" \\' not in check

    sets = _bash_orphan_sets()
    # .agent/ is preserve-by-default (#4741); no runtime orphan tokens.
    assert sets["AGENT"] == frozenset()
    assert sets["CODEX"] >= {"hooks.json", "memory"}
    assert sets["CLAUDE"] >= {"scheduled_tasks.lock", "worktrees", "*-epic"}
    assert sets["CLAUDE"] >= {f"rules/{name}" for name in UNSCOPED_RULE_FILES}


def test_drift_checker_orphan_globs_match_deploy_script() -> None:
    """The post-deploy drift checker must mirror deploy orphan globs."""
    sets = _bash_orphan_sets()
    assert "*-epic" in sets["CLAUDE"]
    # .agent/ runtime state (handoffs, dispatch-briefs, etc.) is preserve-by-default
    # and no longer appears in the AGENT orphan set (#4741).
    assert sets["AGENT"] == frozenset()


def test_second_deploy_is_noop_for_codex_target(tmp_path: Path) -> None:
    """Two consecutive deploys should leave the Codex target unchanged."""
    repo = _init_checkout(tmp_path)

    first_result = _run(repo, DEPLOY_SCRIPT)
    assert first_result.returncode == 0, (
        f"first deploy failed:\nstdout: {first_result.stdout}\nstderr: {first_result.stderr}"
    )

    second_result = _run(repo, DEPLOY_SCRIPT)
    assert second_result.returncode == 0, (
        f"second deploy failed:\nstdout: {second_result.stdout}\nstderr: {second_result.stderr}"
    )
    assert "agents_extensions/shared → .codex: no changes" in second_result.stdout
    assert "agents_extensions/codex → .codex: no changes" in second_result.stdout
    assert "No changes to deploy." in second_result.stdout


def test_codex_hooks_json_is_managed_source_not_orphan() -> None:
    """Codex hooks config must be deployed from agents_extensions/codex."""
    shared = (REPO_ROOT / ORPHAN_PATHS_FILE).read_text(encoding="utf-8")
    check = (REPO_ROOT / CHECK_SCRIPT).read_text(encoding="utf-8")

    assert (REPO_ROOT / "agents_extensions" / "codex" / "hooks.json").exists()
    assert (
        'ORPHAN_PATHS_CODEX="agents/curriculum-orchestrator.toml '
        'agents/curriculum-writer.toml config.toml settings.local.json"'
    ) in shared
    assert 'CODEX_OVERLAY_PATHS="hooks.json memory"' in shared
    assert "$CODEX_OVERLAY_PATHS" in check


def test_missing_codex_hooks_json_is_drift(tmp_path: Path) -> None:
    """The drift checker must fail if runtime .codex/hooks.json disappears."""
    repo = _init_checkout(tmp_path)

    deploy_result = _run(repo, DEPLOY_SCRIPT)
    assert deploy_result.returncode == 0, (
        f"deploy failed:\nstdout: {deploy_result.stdout}\nstderr: {deploy_result.stderr}"
    )

    (repo / CODEX_HOOKS_CONFIG).unlink()

    check_result = _run(repo, CHECK_SCRIPT)
    combined_output = f"{check_result.stdout}\n{check_result.stderr}"
    assert check_result.returncode != 0
    assert "Deploy-script drift between agents_extensions/codex and .codex" in combined_output
    assert "Missing deployed overlay file: .codex/hooks.json" in combined_output


def test_gemini_shared_skill_overlay_is_checked_without_deleting_provider_skills(
    tmp_path: Path,
) -> None:
    """Shared skills overlay into Gemini without replacing Gemini-only skills."""
    repo = _init_checkout(tmp_path)
    deploy_result = _run(repo, DEPLOY_SCRIPT)
    assert deploy_result.returncode == 0, deploy_result.stderr

    shared = repo / ".gemini" / "skills" / "post-build-review" / "SKILL.md"
    provider = repo / ".gemini" / "skills" / "final-review" / "SKILL.md"
    assert shared.exists()
    assert provider.exists()

    unauthorized = repo / ".gemini" / "unauthorized-target-file.txt"
    unauthorized.write_text("not source-owned\n", encoding="utf-8")
    unauthorized_check = _run(repo, CHECK_SCRIPT)
    unauthorized_output = f"{unauthorized_check.stdout}\n{unauthorized_check.stderr}"
    assert unauthorized_check.returncode != 0
    assert "Unowned deployed Gemini file" in unauthorized_output
    assert "unauthorized-target-file.txt" in unauthorized_output
    unauthorized.unlink()

    shared.write_text(shared.read_text(encoding="utf-8") + "\n# drift\n", encoding="utf-8")
    check_result = _run(repo, CHECK_SCRIPT)
    combined_output = f"{check_result.stdout}\n{check_result.stderr}"
    assert check_result.returncode != 0
    assert ("agents_extensions/shared/skills/post-build-review and .gemini/skills/post-build-review") in combined_output

    shutil.copy2(
        repo / "agents_extensions" / "shared" / "skills" / "post-build-review" / "SKILL.md",
        shared,
    )
    provider.write_text(provider.read_text(encoding="utf-8") + "\n# provider drift\n", encoding="utf-8")
    provider_check = _run(repo, CHECK_SCRIPT)
    provider_output = f"{provider_check.stdout}\n{provider_check.stderr}"
    assert provider_check.returncode != 0
    assert ("gemini_extensions/skills/final-review and .gemini/skills/final-review") in provider_output
    assert "SKILL.md" in provider_output

    provider_source = repo / "gemini_extensions" / "skills" / "final-review" / "SKILL.md"
    provider_source.write_text(
        provider_source.read_text(encoding="utf-8") + "\n# provider source update\n",
        encoding="utf-8",
    )
    redeploy = _run(repo, DEPLOY_SCRIPT)
    assert redeploy.returncode == 0, redeploy.stderr
    assert "deleting skills/post-build-review" not in redeploy.stdout
    assert shared.exists()

    stale = shared.parent / "stale-resource.txt"
    stale.write_text("stale shared mirror file\n", encoding="utf-8")
    stale_redeploy = _run(repo, DEPLOY_SCRIPT)
    assert stale_redeploy.returncode == 0, stale_redeploy.stderr
    assert not stale.exists()

    shutil.rmtree(repo / "agents_extensions" / "shared" / "skills" / "post-build-review")
    for mirror in (".claude/skills", ".agent/skills", ".agents/skills", ".codex/skills"):
        shutil.rmtree(repo / mirror / "post-build-review", ignore_errors=True)
    removed_redeploy = _run(repo, DEPLOY_SCRIPT)
    assert removed_redeploy.returncode == 0, removed_redeploy.stderr
    assert not shared.parent.exists()
    assert provider.exists()


def test_gemini_shared_skill_exclusion_does_not_mask_root_drift(tmp_path: Path) -> None:
    """The skills/* overlay exclusion must not become diff's match-all '*'."""
    repo = _init_checkout(tmp_path)
    deploy_result = _run(repo, DEPLOY_SCRIPT)
    assert deploy_result.returncode == 0, deploy_result.stderr

    settings = repo / ".gemini" / "settings.json"
    settings.write_text(
        settings.read_text(encoding="utf-8") + "\n",
        encoding="utf-8",
    )

    check_result = _run(repo, CHECK_SCRIPT)
    combined_output = f"{check_result.stdout}\n{check_result.stderr}"
    assert check_result.returncode != 0
    assert "Deploy-script drift between gemini_extensions and .gemini" in combined_output
    assert "settings.json" in combined_output


def test_gemini_shared_skill_name_collision_fails_closed(tmp_path: Path) -> None:
    """A provider-specific duplicate cannot shadow the canonical shared skill."""
    repo = _init_checkout(tmp_path)
    duplicate = repo / "gemini_extensions" / "skills" / "post-build-review" / "SKILL.md"
    duplicate.parent.mkdir(parents=True)
    duplicate.write_text("provider duplicate\n", encoding="utf-8")

    deploy_result = _run(repo, DEPLOY_SCRIPT)
    combined_output = f"{deploy_result.stdout}\n{deploy_result.stderr}"
    assert deploy_result.returncode != 0
    assert "shared/Gemini skill collision: post-build-review" in combined_output


def test_codex_orphan_is_caught(tmp_path: Path) -> None:
    """Undeclared destination-only Codex paths must abort the deploy."""
    repo = _init_checkout(tmp_path)
    orphan = repo / ".codex" / "stale-only.txt"
    orphan.parent.mkdir(parents=True)
    orphan.write_text("stale\n", encoding="utf-8")

    deploy_result = _run(repo, DEPLOY_SCRIPT)
    combined_output = f"{deploy_result.stdout}\n{deploy_result.stderr}"

    assert deploy_result.returncode != 0
    assert "agents_extensions/shared → .codex" in combined_output
    assert "undeclared orphan 'stale-only.txt'" in combined_output


def test_agent_transient_briefs_are_preserved(tmp_path: Path) -> None:
    """In-flight dispatch briefs in .agent/ must neither abort the deploy nor be wiped.

    Regression for #3456/#4741: .agent/ is preserve-by-default (rsync without
    --delete, no orphan preflight). Runtime briefs are always kept; no
    ORPHAN_PATHS_AGENT declaration needed anymore.
    """
    repo = _init_checkout(tmp_path)
    agent_dir = repo / ".agent"
    agent_dir.mkdir(parents=True)
    brief = agent_dir / "atlas-3150-brief.md"
    brief.write_text("transient dispatch brief\n", encoding="utf-8")
    dispatch = agent_dir / "dispatch-3098-slice3.md"
    dispatch.write_text("transient dispatch prompt\n", encoding="utf-8")
    # Regression (2026-07-05 / #4741): briefs under dispatch-briefs/ are
    # preserved because .agent/ no longer has --delete (no glob needed).
    collected = agent_dir / "dispatch-briefs" / "4497-runner-failover.md"
    collected.parent.mkdir(parents=True)
    collected.write_text("collected dispatch brief\n", encoding="utf-8")

    deploy_result = _run(repo, DEPLOY_SCRIPT)
    assert deploy_result.returncode == 0, (
        "deploy aborted with an in-flight brief present:\n"
        f"stdout: {deploy_result.stdout}\nstderr: {deploy_result.stderr}"
    )
    # No --delete on .agent/ (preserve-by-default); briefs must survive.
    assert brief.exists(), "atlas-3150-brief.md was wiped"
    assert dispatch.exists(), "dispatch-3098-slice3.md was wiped"
    assert collected.exists(), "dispatch-briefs/ brief was wiped"


def test_claude_epic_dirs_are_preserved(tmp_path: Path) -> None:
    """Curriculum-track *-epic/ driver-handoff dirs in .claude/ must survive deploy.

    Regression: the ORPHAN_PATHS_CLAUDE allowlist enumerated only ``folk-epic``
    and ``bio-epic``, so when the atlas track created ``.claude/atlas-epic/`` the
    preflight guard flagged it as an undeclared orphan and aborted EVERY deploy —
    blocking all agent-def / rule / skill propagation until manually unbroken.
    The allowlist is now a ``*-epic`` GLOB, so any current OR FUTURE epic dir is
    preserved. This test uses a brand-new epic name (``hist-epic``) the allowlist
    was never explicitly told about, to prove the glob generalizes.
    """
    repo = _init_checkout(tmp_path)
    for epic in ("atlas-epic", "hist-epic"):
        handoff = repo / ".claude" / epic / "CLAUDE-DRIVER-HANDOFF.md"
        handoff.parent.mkdir(parents=True, exist_ok=True)
        handoff.write_text(f"{epic} driver handoff — runtime state\n", encoding="utf-8")

    deploy_result = _run(repo, DEPLOY_SCRIPT)
    assert deploy_result.returncode == 0, (
        "deploy aborted with a *-epic driver-handoff dir present:\n"
        f"stdout: {deploy_result.stdout}\nstderr: {deploy_result.stderr}"
    )
    for epic in ("atlas-epic", "hist-epic"):
        handoff = repo / ".claude" / epic / "CLAUDE-DRIVER-HANDOFF.md"
        assert handoff.exists(), f".claude/{epic}/ was wiped by rsync --delete"


def test_drift_is_caught(tmp_path: Path) -> None:
    """Post-deploy edits to a target tree must be reported as drift."""
    repo = _init_checkout(tmp_path)

    deploy_result = _run(repo, DEPLOY_SCRIPT)
    assert deploy_result.returncode == 0, (
        f"deploy failed:\nstdout: {deploy_result.stdout}\nstderr: {deploy_result.stderr}"
    )

    drifted_file = repo / DRIFT_TARGET
    assert drifted_file.exists(), f"Expected deployed file missing: {drifted_file}"
    drifted_file.write_text(
        drifted_file.read_text(encoding="utf-8") + "\n# drift injected by test\n",
        encoding="utf-8",
    )

    check_result = _run(repo, CHECK_SCRIPT)
    combined_output = f"{check_result.stdout}\n{check_result.stderr}"
    assert check_result.returncode != 0
    assert "Deploy-script drift between agents_extensions/shared and .claude" in combined_output
    assert "pipeline.md" in combined_output
