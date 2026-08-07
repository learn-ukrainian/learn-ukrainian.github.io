"""Regression tests for deploy-script idempotency checks."""

from __future__ import annotations

import os
import shlex
import shutil
import subprocess
import time
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


def _resolve_project_python() -> Path:
    local = REPO_ROOT / ".venv" / "bin" / "python"
    if local.exists():
        return local

    common_dir = subprocess.check_output(
        [
            "git",
            "-C",
            str(REPO_ROOT),
            "rev-parse",
            "--path-format=absolute",
            "--git-common-dir",
        ],
        text=True,
        timeout=30,
    ).strip()
    canonical = Path(common_dir).parent / ".venv" / "bin" / "python"
    if canonical.exists():
        return canonical

    raise RuntimeError(
        f"Project interpreter missing from this checkout and its canonical Git checkout: {local}, {canonical}"
    )


PROJECT_PYTHON = _resolve_project_python()
DEPLOY_SCRIPT = Path("scripts/deploy_prompts.sh")
CHECK_SCRIPT = Path("scripts/check_rules_deployment.sh")
DEPLOY_WORKFLOW = Path(".github/workflows/rules-deployment-check.yml")
ORPHAN_PATHS_FILE = Path("scripts/deploy_orphan_paths.sh")
AGENT_DEPLOY_MANIFEST = Path(".deploy-state/shared-to-agent.manifest")
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
SHARED_CURRICULUM_SKILLS = ("curriculum-lifecycle", "curriculum-preparation")
UNSCOPED_RULE_FILES = (
    "operator-expectations.md",
    "critical-rules.md",
    "non-negotiable-rules.md",
    "workflow.md",
    "fleet-comms-coordination.md",
    "delegate-must-use-worktree.md",
    "cli-help-standard.md",
    "model-assignment.md",
    "fleet-driver-routing.md",
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
        # deploy_prompts.sh delegates the .agent reap to this helper (fd-bound
        # deletion, see scripts/deploy/reap_agent_mirrors.py). The fixture must
        # mirror every file the script actually invokes, or deploy exits non-zero
        # here for a reason that has nothing to do with the behaviour under test.
        Path("scripts/deploy/agent_directory.py"),
        Path("scripts/deploy/reap_agent_mirrors.py"),
        Path("scripts/deploy/sync_agent_mirror.py"),
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
        timeout=120,
    )


def _run_tracked_mirror_check(repo: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(CHECK_SCRIPT), "--tracked-mirrors-only"],
        cwd=repo,
        capture_output=True,
        check=False,
        text=True,
        timeout=30,
    )


def _run_command(repo: Path, command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=repo,
        capture_output=True,
        check=False,
        text=True,
        timeout=30,
    )


def _init_git_history(repo: Path) -> None:
    """Create the source history used to verify legacy deploy artifacts."""
    for command in (
        ["git", "init", "-q"],
        ["git", "config", "user.email", "deploy-test@example.invalid"],
        ["git", "config", "user.name", "Deploy test"],
        ["git", "add", "-A"],
        ["git", "commit", "-qm", "seed deploy source"],
    ):
        result = _run_command(repo, command)
        assert result.returncode == 0, result.stderr


def _delete_source_file(repo: Path, relative: Path) -> bytes:
    """Delete a tracked source file and commit the deletion for a deploy test."""
    source = repo / "agents_extensions" / "shared" / relative
    original = source.read_bytes()
    source.unlink()
    for command in (
        ["git", "add", "-A"],
        ["git", "commit", "-qm", f"retire {relative.name}"],
    ):
        result = _run_command(repo, command)
        assert result.returncode == 0, result.stderr
    return original


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
    for skill_name in SHARED_CURRICULUM_SKILLS:
        canonical_skill = repo / "agents_extensions" / "shared" / "skills" / skill_name
        for mirror_root in (".claude", ".agent", ".agents", ".codex", ".gemini"):
            deployed_skill = repo / mirror_root / "skills" / skill_name
            assert (deployed_skill / "SKILL.md").read_bytes() == (canonical_skill / "SKILL.md").read_bytes()
            assert (deployed_skill / "agents" / "openai.yaml").read_bytes() == (
                canonical_skill / "agents" / "openai.yaml"
            ).read_bytes()

    codex_hooks_diff = _run_command(
        repo,
        ["diff", "-rq", "agents_extensions/shared/hooks", ".codex/hooks"],
    )
    assert codex_hooks_diff.returncode == 0, (
        f"Codex hooks drift after fresh deploy:\nstdout: {codex_hooks_diff.stdout}\nstderr: {codex_hooks_diff.stderr}"
    )


def test_tracked_mirror_drift_is_detected_before_deploy(tmp_path: Path) -> None:
    """A committed mirror mismatch must fail before deploy can overwrite it."""
    repo = _init_checkout(tmp_path)
    source = repo / "gemini_extensions/hooks/check-claude-inbox.sh"
    mirror = repo / ".gemini/hooks/check-claude-inbox.sh"
    mirror.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, mirror)
    _init_git_history(repo)

    clean = _run_tracked_mirror_check(repo)
    assert clean.returncode == 0, clean.stderr + clean.stdout

    mirror.write_text(mirror.read_text(encoding="utf-8") + "\n# committed drift\n", encoding="utf-8")
    commit = _run_command(repo, ["git", "add", str(mirror)])
    assert commit.returncode == 0, commit.stderr
    commit = _run_command(repo, ["git", "commit", "-qm", "introduce mirror drift"])
    assert commit.returncode == 0, commit.stderr

    drift = _run_tracked_mirror_check(repo)
    output = drift.stdout + drift.stderr
    assert drift.returncode != 0
    assert "Committed deploy-mirror drift" in output
    assert "gemini_extensions/hooks/check-claude-inbox.sh -> .gemini/hooks/check-claude-inbox.sh" in output

    deploy = _run(repo, DEPLOY_SCRIPT)
    assert deploy.returncode == 0, deploy.stderr + deploy.stdout
    assert _run_tracked_mirror_check(repo).returncode == 0


@pytest.mark.parametrize(
    ("mirror_relative", "source_relative"),
    (
        (".claude/hooks/auto-audit.sh", "agents_extensions/shared/hooks/auto-audit.sh"),
        (".agent/hooks/auto-audit.sh", "agents_extensions/shared/hooks/auto-audit.sh"),
        (
            ".agents/skills/post-build-review/SKILL.md",
            "agents_extensions/shared/skills/post-build-review/SKILL.md",
        ),
        (".codex/hooks/session-setup.sh", "agents_extensions/shared/hooks/session-setup.sh"),
        (".codex/hooks.json", "agents_extensions/codex/hooks.json"),
        (
            ".gemini/rules/fleet-comms-coordination.md",
            "agents_extensions/shared/rules/fleet-comms-coordination.md",
        ),
        (
            ".gemini/skills/post-build-review/SKILL.md",
            "agents_extensions/shared/skills/post-build-review/SKILL.md",
        ),
        (
            ".gemini/skills/full-rebuild-bio/SKILL.md",
            "gemini_extensions/skills/full-rebuild-bio/SKILL.md",
        ),
    ),
)
def test_tracked_mirror_resolves_each_deploy_source(
    tmp_path: Path,
    mirror_relative: str,
    source_relative: str,
) -> None:
    """Shared and overlay mirrors must resolve to their actual canonical source."""
    repo = _init_checkout(tmp_path)
    source = repo / source_relative
    mirror = repo / mirror_relative
    mirror.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, mirror)
    _init_git_history(repo)

    clean = _run_tracked_mirror_check(repo)
    assert clean.returncode == 0, clean.stderr + clean.stdout

    mirror.write_text(mirror.read_text(encoding="utf-8") + "\n# drift\n", encoding="utf-8")
    drift = _run_tracked_mirror_check(repo)
    output = drift.stdout + drift.stderr
    assert drift.returncode != 0
    assert f"{source_relative} -> {mirror_relative}" in output


def test_tracked_agents_skill_declared_orphan_is_skipped(tmp_path: Path) -> None:
    """Destination-only .agents skills remain governed by their explicit allowlist."""
    repo = _init_checkout(tmp_path)
    orphan_config = repo / ORPHAN_PATHS_FILE
    orphan_config.write_text(
        orphan_config.read_text(encoding="utf-8").replace(
            'ORPHAN_PATHS_AGENTS=""',
            'ORPHAN_PATHS_AGENTS="local-skill"',
        ),
        encoding="utf-8",
    )
    mirror = repo / ".agents/skills/local-skill/SKILL.md"
    mirror.parent.mkdir(parents=True, exist_ok=True)
    mirror.write_text("destination-only skill\n", encoding="utf-8")
    _init_git_history(repo)

    result = _run_tracked_mirror_check(repo)
    assert result.returncode == 0, result.stderr + result.stdout


def test_tracked_claude_glob_orphan_is_skipped(tmp_path: Path) -> None:
    """Glob allowlist entries retain the same semantics as deploy's diff excludes."""
    repo = _init_checkout(tmp_path)
    mirror = repo / ".claude/atlas-epic/CLAUDE-DRIVER-HANDOFF.md"
    mirror.parent.mkdir(parents=True, exist_ok=True)
    mirror.write_text("runtime-only handoff\n", encoding="utf-8")
    _init_git_history(repo)

    result = _run_tracked_mirror_check(repo)
    assert result.returncode == 0, result.stderr + result.stdout


def test_rules_workflow_checks_mirrors_before_deploy() -> None:
    """CI must inspect committed mirrors before its mutating deploy step."""
    workflow = (REPO_ROOT / DEPLOY_WORKFLOW).read_text(encoding="utf-8")
    preflight = "bash scripts/check_rules_deployment.sh --tracked-mirrors-only"
    deploy = "bash scripts/deploy_prompts.sh"

    for path_filter in (
        "agents_extensions/codex/**",
        ".claude/**",
        ".agent/**",
        ".agents/**",
        ".codex/**",
        ".gemini/**",
    ):
        assert workflow.count(f"- '{path_filter}'") == 2
    assert workflow.index(preflight) < workflow.index(deploy)


def test_agent_manifest_reaps_retired_hook_without_touching_agent_state(tmp_path: Path) -> None:
    """A recorded hook is reaped; unrecorded .agent runtime paths survive."""
    repo = _init_checkout(tmp_path)
    _init_git_history(repo)
    retired = Path("hooks/auto-audit.sh")

    first = _run(repo, DEPLOY_SCRIPT)
    assert first.returncode == 0, first.stderr
    assert (repo / AGENT_DEPLOY_MANIFEST).is_file()

    agent_prompt = repo / ".agent/prompts/agent-written.md"
    rollover = repo / ".agent/thread-rollovers/x/handoff.md"
    runtime_tmp = repo / ".agent/tmp/y"
    for path, contents in (
        (agent_prompt, "agent-owned prompt\n"),
        (rollover, "agent-owned handoff\n"),
        (runtime_tmp, "agent-owned scratch\n"),
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(contents, encoding="utf-8")

    _delete_source_file(repo, retired)
    deploy = _run(repo, DEPLOY_SCRIPT)

    assert deploy.returncode == 0, deploy.stderr
    assert "removed retired deploy artifact 'hooks/auto-audit.sh'" in deploy.stdout
    assert not (repo / ".agent" / retired).exists()
    assert not (repo / ".claude" / retired).exists()
    assert not (repo / ".codex" / retired).exists()
    assert agent_prompt.read_text(encoding="utf-8") == "agent-owned prompt\n"
    assert rollover.read_text(encoding="utf-8") == "agent-owned handoff\n"
    assert runtime_tmp.read_text(encoding="utf-8") == "agent-owned scratch\n"


def test_agent_manifest_rejects_symlinked_intermediate_component(tmp_path: Path) -> None:
    """A manifest path must not follow a symlinked .agent/ subdirectory."""
    repo = _init_checkout(tmp_path)
    first = _run(repo, DEPLOY_SCRIPT)
    assert first.returncode == 0, first.stderr

    external_dir = tmp_path / "external"
    external_dir.mkdir()
    victim = external_dir / "victim.txt"
    victim.write_text("must survive\n", encoding="utf-8")
    (repo / ".agent" / "escape").symlink_to(external_dir, target_is_directory=True)
    with (repo / AGENT_DEPLOY_MANIFEST).open("a", encoding="utf-8") as manifest:
        manifest.write("f\tescape/victim.txt\n")

    deploy = _run(repo, DEPLOY_SCRIPT)
    output = f"{deploy.stdout}\n{deploy.stderr}"
    assert deploy.returncode == 0, output
    assert victim.read_text(encoding="utf-8") == "must survive\n"
    assert (repo / ".agent" / "escape").is_symlink()
    assert "symlinked component 'escape'" in output
    assert "ignoring unsafe manifest entry 'f escape/victim.txt'" in output


def test_agent_overlay_write_stays_in_held_directory_after_root_swap(tmp_path: Path) -> None:
    """A post-validation `.agent` symlink swap must not redirect rsync writes.

    The rsync shim waits only when the agent overlay begins.  At that point the
    production helper has already opened and fchdir'ed into `.agent`; the test
    swaps the pathname to an external directory before allowing the real rsync
    binary to run.  A regression to ``rsync ... .agent/`` writes settings.json
    outside the fixture and fails this test.
    """
    repo = _init_checkout(tmp_path)
    # Exercise the post-validation race from the review: the root is a real
    # directory before deploy starts, then becomes a symlink immediately before
    # rsync writes.  (A clean first deploy is covered separately.)
    (repo / ".agent").mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    ready = tmp_path / "rsync-ready"
    release = tmp_path / "rsync-release"
    fake_bin = tmp_path / "fake-bin"
    fake_bin.mkdir()
    real_rsync = shutil.which("rsync")
    assert real_rsync, "rsync is required for the deploy integration test"
    (fake_bin / "rsync").write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        'last="${!#}"\n'
        'if [[ "$last" == "." || "$last" == ".agent" || "$last" == ".agent/" ]]; then\n'
        '    : > "$SYNC_AGENT_RACE_READY"\n'
        '    while [[ ! -e "$SYNC_AGENT_RACE_RELEASE" ]]; do sleep 0.01; done\n'
        "fi\n"
        f"exec {shlex.quote(real_rsync)} \"$@\"\n",
        encoding="utf-8",
    )
    (fake_bin / "rsync").chmod(0o755)
    environment = os.environ | {
        "PATH": f"{fake_bin}{os.pathsep}{os.environ['PATH']}",
        "SYNC_AGENT_RACE_READY": str(ready),
        "SYNC_AGENT_RACE_RELEASE": str(release),
    }
    process = subprocess.Popen(
        ["bash", str(DEPLOY_SCRIPT)],
        cwd=repo,
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        deadline = time.monotonic() + 10
        while not ready.exists() and process.poll() is None and time.monotonic() < deadline:
            time.sleep(0.02)
        assert ready.exists(), "the descriptor-bound .agent rsync never started"

        held_agent = repo / ".agent-held"
        (repo / ".agent").rename(held_agent)
        (repo / ".agent").symlink_to(outside, target_is_directory=True)
    finally:
        release.touch()
        stdout, stderr = process.communicate(timeout=120)

    output = f"{stdout}\n{stderr}"
    assert process.returncode == 0, output
    assert not (outside / "settings.json").exists(), (
        "shared content was written through the swapped .agent symlink"
    )
    assert (repo / ".agent-held" / "settings.json").is_file(), (
        "rsync did not write into the directory held before the pathname swap"
    )


def test_agent_manifest_unlinks_symlink_leaf_without_following_target(tmp_path: Path) -> None:
    """A recorded symlink leaf is unlinked, never followed to its target."""
    repo = _init_checkout(tmp_path)
    first = _run(repo, DEPLOY_SCRIPT)
    assert first.returncode == 0, first.stderr

    external_target = tmp_path / "external-target.txt"
    external_target.write_text("must survive\n", encoding="utf-8")
    link = repo / ".agent" / "link"
    link.symlink_to(external_target)
    with (repo / AGENT_DEPLOY_MANIFEST).open("a", encoding="utf-8") as manifest:
        manifest.write("l\tlink\n")

    deploy = _run(repo, DEPLOY_SCRIPT)
    assert deploy.returncode == 0, deploy.stderr
    assert "removed retired deploy artifact 'link'" in deploy.stdout
    assert external_target.read_text(encoding="utf-8") == "must survive\n"
    assert not link.is_symlink()


def test_agent_manifest_keeps_lexically_unsafe_entries_rejected(tmp_path: Path) -> None:
    """Existing absolute and parent-directory manifest rejections remain in force."""
    repo = _init_checkout(tmp_path)
    first = _run(repo, DEPLOY_SCRIPT)
    assert first.returncode == 0, first.stderr

    parent_victim = tmp_path / "outside"
    absolute_victim = tmp_path / "absolute-outside"
    parent_victim.write_text("must survive\n", encoding="utf-8")
    absolute_victim.write_text("must survive\n", encoding="utf-8")
    # The deploy script exits early on a true no-op, so add a legitimate source
    # change to exercise manifest reaping during this regression.
    source_change = repo / "agents_extensions" / "shared" / "hooks" / "force-redeploy.sh"
    source_change.write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
    source_change.chmod(0o755)
    with (repo / AGENT_DEPLOY_MANIFEST).open("a", encoding="utf-8") as manifest:
        manifest.write("f\t../outside\n")
        manifest.write(f"f\t{absolute_victim}\n")

    deploy = _run(repo, DEPLOY_SCRIPT)
    output = f"{deploy.stdout}\n{deploy.stderr}"
    assert deploy.returncode == 0, output
    assert "ignoring unsafe manifest entry 'f ../outside'" in output
    assert f"ignoring unsafe manifest entry 'f {absolute_victim}'" in output
    assert parent_victim.read_text(encoding="utf-8") == "must survive\n"
    assert absolute_victim.read_text(encoding="utf-8") == "must survive\n"


def test_agent_manifest_reaps_legitimate_nested_file(tmp_path: Path) -> None:
    """Physical-path validation still permits a retired nested .agent/ artifact."""
    repo = _init_checkout(tmp_path)
    retired = Path("hooks/nested/retired.sh")
    source = repo / "agents_extensions" / "shared" / retired
    source.parent.mkdir(parents=True)
    source.write_text("#!/usr/bin/env bash\necho retired\n", encoding="utf-8")
    source.chmod(0o755)
    _init_git_history(repo)

    first = _run(repo, DEPLOY_SCRIPT)
    assert first.returncode == 0, first.stderr
    deployed = repo / ".agent" / retired
    assert deployed.exists()

    _delete_source_file(repo, retired)
    deploy = _run(repo, DEPLOY_SCRIPT)
    assert deploy.returncode == 0, deploy.stderr
    assert "removed retired deploy artifact 'hooks/nested/retired.sh'" in deploy.stdout
    assert not deployed.exists()


def test_agent_manifest_migration_defers_reaping_verified_legacy_artifact(tmp_path: Path) -> None:
    """The first manifest deploy preserves legacy output; the next one reaps it."""
    repo = _init_checkout(tmp_path)
    _init_git_history(repo)
    retired = Path("hooks/auto-audit.sh")
    original = _delete_source_file(repo, retired)

    stale_target = repo / ".agent" / retired
    agent_owned = repo / ".agent/hooks/custom-agent-hook.sh"
    stale_target.parent.mkdir(parents=True)
    stale_target.write_bytes(original)
    agent_owned.write_text("agent-owned hook\n", encoding="utf-8")
    assert not (repo / AGENT_DEPLOY_MANIFEST).exists()

    first = _run(repo, DEPLOY_SCRIPT)
    assert first.returncode == 0, first.stderr
    assert "no deploy manifest yet; preserving all existing paths during migration" in first.stdout
    assert stale_target.read_bytes() == original
    manifest = (repo / AGENT_DEPLOY_MANIFEST).read_text(encoding="utf-8")
    assert "f\thooks/auto-audit.sh" in manifest
    assert "custom-agent-hook.sh" not in manifest
    assert agent_owned.read_text(encoding="utf-8") == "agent-owned hook\n"

    second = _run(repo, DEPLOY_SCRIPT)
    assert second.returncode == 0, second.stderr
    assert "removed retired deploy artifact 'hooks/auto-audit.sh'" in second.stdout
    assert not stale_target.exists()
    assert agent_owned.read_text(encoding="utf-8") == "agent-owned hook\n"


def test_curriculum_preparation_documents_canonical_helper_paths() -> None:
    """Preparation must identify its import-only helpers from the repository root."""
    skill_path = REPO_ROOT / "agents_extensions/shared/skills/curriculum-preparation/SKILL.md"
    skill = skill_path.read_text(encoding="utf-8")
    helper_paths = (
        Path("agents_extensions/shared/skills/curriculum-preparation/scripts/bounded_packet.py"),
        Path("agents_extensions/shared/skills/track-completion/scripts/bounded_completion.py"),
    )

    for helper_path in helper_paths:
        assert (REPO_ROOT / helper_path).is_file()
        assert str(helper_path) in skill
    assert "`scripts/bounded_packet.py`" not in skill
    assert "`../track-completion/scripts/bounded_completion.py`" not in skill


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
        timeout=30,
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


def test_codex_config_and_hooks_are_managed_sources_not_orphans() -> None:
    """Codex App/CLI config and hooks deploy from agents_extensions/codex."""
    shared = (REPO_ROOT / ORPHAN_PATHS_FILE).read_text(encoding="utf-8")
    check = (REPO_ROOT / CHECK_SCRIPT).read_text(encoding="utf-8")

    assert (REPO_ROOT / "agents_extensions" / "codex" / "hooks.json").exists()
    assert (REPO_ROOT / "agents_extensions" / "codex" / "config.toml").exists()
    assert (
        'ORPHAN_PATHS_CODEX="agents/curriculum-orchestrator.toml '
        'agents/curriculum-writer.toml settings.local.json"'
    ) in shared
    assert 'CODEX_OVERLAY_PATHS="config.toml hooks.json memory"' in shared
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


def test_agent_source_managed_subtrees_propagate_deletions_without_wiping_runtime(
    tmp_path: Path,
) -> None:
    """A retired shared hook is removed, while .agent runtime scratch survives.

    The source-managed set is derived from ``agents_extensions/shared``. This
    exercises the exact production boundary: ``hooks/`` is mirrored with
    deletion propagation, but ``thread-rollovers/`` and ``tmp/`` are runtime
    state outside that source tree and remain preserve-by-default.
    """
    repo = _init_checkout(tmp_path)
    source_hook = repo / "agents_extensions" / "shared" / "hooks" / "auto-audit.sh"
    source_hook.write_text("#!/usr/bin/env bash\necho auto-audit\n", encoding="utf-8")
    source_hook.chmod(0o755)
    for command in (
        ["git", "init", "--quiet"],
        ["git", "config", "user.email", "test@example.invalid"],
        ["git", "config", "user.name", "Deploy test"],
        ["git", "add", "agents_extensions"],
        ["git", "commit", "--quiet", "-m", "add source hook"],
    ):
        result = _run_command(repo, command)
        assert result.returncode == 0, result.stderr

    first_deploy = _run(repo, DEPLOY_SCRIPT)
    assert first_deploy.returncode == 0, first_deploy.stderr + first_deploy.stdout
    deployed_hook = repo / ".agent" / "hooks" / "auto-audit.sh"
    assert deployed_hook.exists(), "test fixture hook was not deployed"

    handoff = repo / ".agent" / "thread-rollovers" / "x" / "handoff.md"
    handoff.parent.mkdir(parents=True)
    handoff.write_text("live handoff\n", encoding="utf-8")
    runtime_tmp = repo / ".agent" / "tmp" / "y"
    runtime_tmp.parent.mkdir(parents=True)
    runtime_tmp.write_text("live scratch\n", encoding="utf-8")

    deletion = _run_command(repo, ["git", "rm", "agents_extensions/shared/hooks/auto-audit.sh"])
    assert deletion.returncode == 0, deletion.stderr
    deletion_commit = _run_command(repo, ["git", "commit", "--quiet", "-m", "retire source hook"])
    assert deletion_commit.returncode == 0, deletion_commit.stderr
    second_deploy = _run(repo, DEPLOY_SCRIPT)
    assert second_deploy.returncode == 0, second_deploy.stderr + second_deploy.stdout
    assert not deployed_hook.exists(), "deleted source hook still executes from .agent"
    assert handoff.read_text(encoding="utf-8") == "live handoff\n"
    assert runtime_tmp.read_text(encoding="utf-8") == "live scratch\n"


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
