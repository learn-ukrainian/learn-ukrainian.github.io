"""Contract coverage for the ten-script public launcher estate."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
PUBLIC = (
    "start-claude.sh",
    "start-claude-driver.sh",
    "start-codex.sh",
    "start-codex-driver.sh",
    "start-gemini.sh",
    "start-gemini-driver.sh",
    "start-grok.sh",
    "start-grok-driver.sh",
    "start-kimi.sh",
    "start-glm.sh",
)
RETIRED = tuple(f"start-{name}.sh" for name in ("claudex", "kimicc", "glmcc")) + tuple(
    f"start-{provider}-drive.sh" for provider in ("gemini", "grok", "opus", "sonnet")
)


def run_launcher(
    name: str,
    *args: str,
    env: dict[str, str] | None = None,
    dry_run: bool = True,
) -> subprocess.CompletedProcess[str]:
    launch_env = os.environ.copy()
    launch_env["LAUNCHER_DRY_RUN"] = "1" if dry_run else "0"
    launch_env.update(env or {})
    return subprocess.run(
        [str(REPO / name), *args],
        cwd=REPO,
        env=launch_env,
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
    )


def test_root_launcher_allowlist_is_exact() -> None:
    assert {path.name for path in REPO.glob("start-*.sh")} == set(PUBLIC)


@pytest.mark.parametrize("name", PUBLIC)
def test_help_is_machine_usable(name: str) -> None:
    result = run_launcher(name, "--help")
    assert result.returncode == 0, result.stderr
    assert "Usage:" in result.stdout
    assert "EXIT CODES:" in result.stdout
    assert "LAUNCHER_DRY_RUN=1" in result.stdout


@pytest.mark.parametrize("name", PUBLIC)
def test_unknown_launcher_flag_exits_usage_error(name: str) -> None:
    result = run_launcher(name, "--does-not-exist")
    assert result.returncode == 2
    assert "run --help" in result.stderr


@pytest.mark.parametrize("name", ("start-claude.sh", "start-codex.sh", "start-gemini.sh", "start-grok.sh", "start-kimi.sh", "start-glm.sh"))
def test_interactive_launchers_reject_driver_epic(name: str) -> None:
    result = run_launcher(name, "--epic", "devops")
    assert result.returncode == 2
    assert "interactive launchers reject --epic" in result.stderr


def test_driver_requires_certified_model_and_valid_epic() -> None:
    missing = run_launcher("start-claude-driver.sh")
    assert missing.returncode == 2
    untrusted = run_launcher("start-claude-driver.sh", "--epic", "devops", "--model", "not-certified")
    assert untrusted.returncode == 4
    invalid = run_launcher("start-gemini-driver.sh", "--epic", "not-a-lane")
    assert invalid.returncode == 2


def test_dry_run_does_not_require_a_provider_binary(tmp_path: Path) -> None:
    shell = shutil.which("bash")
    assert shell is not None
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    (bin_dir / "bash").symlink_to(shell)
    provider_free_path = f"{bin_dir}{os.pathsep}{os.defpath}"
    provider_binaries = ("agy", "claude", "codex", "grok", "kimi")
    assert all(shutil.which(binary, path=provider_free_path) is None for binary in provider_binaries)

    result = run_launcher("start-claude.sh", env={"PATH": provider_free_path})
    assert result.returncode == 0, result.stderr
    assert "LAUNCHER_DRY_RUN=1: would require binary claude" in result.stdout
    assert "would exec claude --model claude-fable-5" in result.stdout


def test_codex_driver_preserves_transport_probe_and_lease_guard() -> None:
    sustained = run_launcher("start-codex-driver.sh", "--epic", "devops", "--model", "gpt-5.6-sol")
    assert sustained.returncode == 0, sustained.stderr
    assert "would probe" in sustained.stdout
    assert sustained.stdout.index("would claim lease") < sustained.stdout.index("would mint and bootstrap")
    assert sustained.stdout.index("would mint and bootstrap") < sustained.stdout.index("would bind drive-epic")

    governor = run_launcher("start-codex-driver.sh", "--governor", "AUTO", env={"SESSION_EPIC": "foreign"})
    assert governor.returncode == 0, governor.stderr
    assert "--model gpt-5.6-sol" in governor.stdout
    assert "governor SESSION_EPIC=<unset>" in governor.stdout
    assert "would claim lease" not in governor.stdout


def _core_canary_failure_fixture(tmp_path: Path) -> tuple[Path, Path, Path]:
    """Build a provider-neutral driver whose canary failure is observable."""
    root = tmp_path / "repo"
    for relative in (
        "start-claude-driver.sh",
        "scripts/lib/handoff_identity.sh",
        "scripts/lib/launcher_core.sh",
        "scripts/lib/session_supervisor.sh",
        # The core's deploy staleness gate sources this; without package.json
        # in the sandbox it warns and passes (#5958).
        "scripts/lib/deploy_extensions.sh",
    ):
        destination = root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPO / relative, destination)

    claim_marker = tmp_path / "lease-claimed"
    close_marker = tmp_path / "lease-closed"
    python_stub = root / ".venv" / "bin" / "python"
    python_stub.parent.mkdir(parents=True)
    python_stub.write_text(
        f'''#!/usr/bin/env bash
if [[ "${{1:-}}" == "-m" && "${{2:-}}" == "scripts.session_supervisor" ]]; then
  touch {os.fspath(claim_marker)!r}
  cat <<'JSON'
{{"identity":{{"lease":{{"session_id":"session-test","lease_id":"lease-test","generation":1,"fencing_token":1,"expires_at":"2026-07-23T00:00:00Z"}}}}}}
JSON
  exit 0
fi
if [[ "${{1:-}}" == "-m" && "${{2:-}}" == "agents_extensions.shared.session_streams" ]]; then
  touch {os.fspath(close_marker)!r}
  exit 0
fi
exec {os.fspath(REPO / ".venv" / "bin" / "python")!r} "$@"
''',
        encoding="utf-8",
    )
    python_stub.chmod(0o755)

    adapter = root / "scripts" / "launchers" / "claude.sh"
    adapter.parent.mkdir(parents=True, exist_ok=True)
    adapter.write_text(
        """#!/usr/bin/env bash
launcher_adapter_validate() { :; }
launcher_adapter_preflight() { :; }
launcher_adapter_canary() { return 1; }
launcher_adapter_exec() { printf 'PROVIDER_EXEC\\n'; }
""",
        encoding="utf-8",
    )
    adapter.chmod(0o755)
    initialized = subprocess.run(
        ["git", "init", "-q", "-b", "main", os.fspath(root)],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert initialized.returncode == 0, initialized.stderr
    return root / "start-claude-driver.sh", claim_marker, close_marker


def test_canary_failure_closes_lease_and_refuses_driver_launch(tmp_path: Path) -> None:
    launcher, claim_marker, close_marker = _core_canary_failure_fixture(tmp_path)
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    result = subprocess.run(
        ["bash", os.fspath(launcher), "--epic", "devops"],
        cwd=launcher.parent,
        env=env,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )

    assert result.returncode == 1
    assert claim_marker.is_file()
    # Mutation guard: deleting the shared-core close call leaves this marker
    # absent and recreates the six-hour lease leak for every provider driver.
    assert close_marker.is_file()
    assert "PROVIDER_EXEC" not in result.stdout


def test_harness_contracts_and_redacted_kimi_glm_credentials(tmp_path: Path) -> None:
    home = tmp_path / "home"
    kimi_secret = "kimi-secret-must-not-appear"
    kimi = run_launcher(
        "start-kimi.sh",
        "--harness",
        "claude-code",
        "--model",
        "k3",
        env={"HOME": str(home), "KIMICC_AUTH_TOKEN": kimi_secret},
    )
    assert kimi.returncode == 0, kimi.stderr
    assert "credential_source=KIMICC_AUTH_TOKEN" in kimi.stdout
    assert kimi_secret not in kimi.stdout + kimi.stderr

    glm_secret = "glm-secret-must-not-appear"
    glm = run_launcher(
        "start-glm.sh",
        env={"HOME": str(home), "ZAI_API_KEY": glm_secret},
    )
    assert glm.returncode == 0, glm.stderr
    assert "credential_source=ZAI_API_KEY" in glm.stdout
    assert glm_secret not in glm.stdout + glm.stderr

    unsupported = run_launcher("start-glm.sh", "--harness", "native")
    assert unsupported.returncode == 2
    assert "native is unsupported" in unsupported.stderr


def test_kimi_never_uses_ambient_anthropic_token(tmp_path: Path) -> None:
    foreign = "anthropic-secret-must-not-appear"
    result = run_launcher(
        "start-kimi.sh",
        "--harness",
        "claude-code",
        env={"HOME": str(tmp_path / "home"), "ANTHROPIC_AUTH_TOKEN": foreign},
    )
    assert result.returncode == 3
    assert "no Kimi API credential" in result.stderr
    assert foreign not in result.stdout + result.stderr


def test_session_and_durable_helper_roots_are_deliberately_distinct() -> None:
    core = (REPO / "scripts/lib/launcher_core.sh").read_text(encoding="utf-8")
    kimi = (REPO / "scripts/launchers/kimi.sh").read_text(encoding="utf-8")
    route = (REPO / "scripts/lib/kimicc_route.sh").read_text(encoding="utf-8")
    assert "LC_SESSION_ROOT" in core and "LC_DURABLE_HELPER_ROOT" in core
    assert 'kimicc_configure_route "$LC_SESSION_ROOT" "$LC_SESSION_ROOT" "$LC_DURABLE_HELPER_ROOT"' in kimi
    assert "durable_helper_dir" in route


def test_retired_names_are_absent_from_tracked_content() -> None:
    tracked = subprocess.run(
        ["git", "ls-files"], cwd=REPO, text=True, capture_output=True, check=True, timeout=30
    ).stdout.splitlines()
    for retired in RETIRED:
        assert not (REPO / retired).exists()
        for relative in tracked:
            path = REPO / relative
            if path.is_file() and path.suffix not in {".png", ".jpg", ".jpeg", ".gif", ".pdf"}:
                assert retired not in path.read_text(encoding="utf-8", errors="ignore"), relative
