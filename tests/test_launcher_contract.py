"""Contract coverage for the public launcher estate."""

from __future__ import annotations

import os
import shutil
import signal
import subprocess
import time
from datetime import timedelta
from pathlib import Path

import pytest

from agents_extensions.shared.session_streams.db import SessionStreamDatabase
from agents_extensions.shared.session_streams.model import LeaseHolder, utc_now
from agents_extensions.shared.session_streams.store import SessionStreamStore
from scripts.session_supervisor import LaunchRole, SessionSupervisor

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
    "start-kimicc.sh",
    "start-glm.sh",
    "start-glmcc.sh",
)
# Compat wrappers forward into the shared adapters; they are part of PUBLIC.
COMPAT = ("start-kimicc.sh", "start-glmcc.sh")
assert set(COMPAT).issubset(PUBLIC)
RETIRED = tuple(f"start-{name}.sh" for name in ("claudex",)) + tuple(
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


@pytest.mark.parametrize(
    "name",
    (
        "start-claude.sh",
        "start-codex.sh",
        "start-gemini.sh",
        "start-grok.sh",
        "start-kimi.sh",
        "start-kimicc.sh",
        "start-glm.sh",
        "start-glmcc.sh",
    ),
)
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
    assert "would exec claude " in result.stdout
    assert "would exec claude --model" not in result.stdout


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


def _core_driver_exit_fixture(
    tmp_path: Path,
    *,
    provider_body: str,
    failed_close_attempts: int = 0,
) -> tuple[Path, Path, Path, Path]:
    """Build a provider-neutral driver with observable close attempts."""
    root = tmp_path / "repo"
    for relative in (
        "start-claude-driver.sh",
        "scripts/lib/handoff_identity.sh",
        "scripts/lib/launcher_core.sh",
        "scripts/lib/session_supervisor.sh",
        "scripts/lib/deploy_extensions.sh",
    ):
        destination = root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPO / relative, destination)

    close_attempts = tmp_path / "close-attempts"
    close_marker = tmp_path / "lease-closed"
    child_started = tmp_path / "child-started"
    python_stub = root / ".venv" / "bin" / "python"
    python_stub.parent.mkdir(parents=True)
    python_stub.write_text(
        f'''#!/usr/bin/env bash
if [[ "${{1:-}}" == "-m" && "${{2:-}}" == "scripts.session_supervisor" ]]; then
  cat <<'JSON'
{{"identity":{{"lease":{{"session_id":"session-test","lease_id":"lease-test","generation":1,"fencing_token":1,"expires_at":"2026-07-23T00:00:00Z"}}}}}}
JSON
  exit 0
fi
if [[ "${{1:-}}" == "-m" && "${{2:-}}" == "agents_extensions.shared.session_streams" ]]; then
  count=0
  if [[ -f {os.fspath(close_attempts)!r} ]]; then count="$(< {os.fspath(close_attempts)!r})"; fi
  count=$((count + 1))
  printf '%s\n' "$count" > {os.fspath(close_attempts)!r}
  if [[ "$count" -le {failed_close_attempts} ]]; then exit 1; fi
  touch {os.fspath(close_marker)!r}
  exit 0
fi
exec {os.fspath(REPO / ".venv" / "bin" / "python")!r} "$@"
''',
        encoding="utf-8",
    )
    python_stub.chmod(0o755)

    provider = root / "provider.sh"
    provider.write_text(
        f"#!/usr/bin/env bash\ntouch {os.fspath(child_started)!r}\n{provider_body}\n",
        encoding="utf-8",
    )
    provider.chmod(0o755)

    adapter = root / "scripts" / "launchers" / "claude.sh"
    adapter.parent.mkdir(parents=True, exist_ok=True)
    adapter.write_text(
        f"""#!/usr/bin/env bash
launcher_adapter_validate() {{ :; }}
launcher_adapter_preflight() {{ :; }}
launcher_adapter_canary() {{ return 0; }}
launcher_adapter_exec() {{ launcher_exec_command {os.fspath(provider)!r}; }}
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
    return root / "start-claude-driver.sh", close_attempts, close_marker, child_started


def test_driver_normal_exit_closes_with_bounded_idempotent_retry(tmp_path: Path) -> None:
    launcher, close_attempts, close_marker, child_started = _core_driver_exit_fixture(
        tmp_path,
        provider_body="exit 7",
        failed_close_attempts=1,
    )
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

    assert result.returncode == 7
    assert child_started.is_file()
    assert close_marker.is_file()
    assert close_attempts.read_text(encoding="utf-8").strip() == "2"


@pytest.mark.parametrize(
    ("termination_signal", "expected_exit"),
    ((signal.SIGINT, 130), (signal.SIGTERM, 143), (signal.SIGHUP, 129)),
)
def test_driver_termination_forwards_signal_and_closes_exact_lease(
    tmp_path: Path,
    termination_signal: signal.Signals,
    expected_exit: int,
) -> None:
    launcher, close_attempts, close_marker, child_started = _core_driver_exit_fixture(
        tmp_path,
        provider_body="trap 'exit 0' INT TERM HUP\nwhile :; do sleep 0.1; done",
    )
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    process = subprocess.Popen(
        ["bash", os.fspath(launcher), "--epic", "devops"],
        cwd=launcher.parent,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    for _ in range(100):
        if child_started.is_file():
            break
        process.poll()
        if process.returncode is not None:
            break
        time.sleep(0.02)
    assert child_started.is_file()

    process.send_signal(termination_signal)
    stdout, stderr = process.communicate(timeout=10)
    assert process.returncode == expected_exit, stdout + stderr
    assert close_marker.is_file()
    assert close_attempts.read_text(encoding="utf-8").strip() == "1"


def test_all_driver_adapters_use_common_closure_wrapper() -> None:
    for provider in ("claude", "codex", "gemini", "grok"):
        body = (REPO / "scripts" / "launchers" / f"{provider}.sh").read_text(encoding="utf-8")
        assert 'launcher_exec_command "${cmd[@]}"' in body


def test_real_store_driver_close_successor_and_expired_recovery(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    for relative in (
        "start-claude-driver.sh",
        "scripts/lib/handoff_identity.sh",
        "scripts/lib/launcher_core.sh",
        "scripts/lib/session_supervisor.sh",
        "scripts/lib/deploy_extensions.sh",
        "scripts/config/issue_streams.yaml",
    ):
        destination = root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPO / relative, destination)
    python_bin = root / ".venv" / "bin" / "python"
    python_bin.parent.mkdir(parents=True)
    python_bin.write_text(
        f"#!/usr/bin/env bash\nexec {os.fspath(REPO / '.venv' / 'bin' / 'python')!r} \"$@\"\n",
        encoding="utf-8",
    )
    python_bin.chmod(0o755)
    provider = root / "provider.sh"
    provider.write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
    provider.chmod(0o755)
    adapter = root / "scripts" / "launchers" / "claude.sh"
    adapter.parent.mkdir(parents=True, exist_ok=True)
    adapter.write_text(
        f"""#!/usr/bin/env bash
launcher_adapter_validate() {{ :; }}
launcher_adapter_preflight() {{ :; }}
launcher_adapter_canary() {{ return 0; }}
launcher_adapter_exec() {{ launcher_exec_command {os.fspath(provider)!r}; }}
""",
        encoding="utf-8",
    )
    adapter.chmod(0o755)
    subprocess.run(["git", "init", "-q", "-b", "main", os.fspath(root)], check=True, timeout=30)
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    env["PYTHONPATH"] = os.fspath(REPO)

    result = subprocess.run(
        ["bash", os.fspath(root / "start-claude-driver.sh"), "--epic", "devops"],
        cwd=root,
        env=env,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr + result.stdout

    database = SessionStreamDatabase(root / ".agent/session-streams/v1/session-streams.sqlite3")
    store = SessionStreamStore(database)
    history = store.dump_stream("epic:5703")
    assert history["sessions"][0]["state"] == "closed"
    assert history["lease"]["state"] == "released"
    assert [event["event_type"] for event in history["lease_events"]] == ["acquired", "released"]

    supervisor = SessionSupervisor(store, repo_root=root)
    successor = supervisor.open_driver(
        role=LaunchRole.DRIVER,
        stream_id="epic:5703",
        holder=LeaseHolder(
            agent="codex",
            harness="codex-cli",
            instance_id="successor-after-clean-close",
            process_id=os.getpid(),
        ),
        lineage_id="lineage-successor-after-clean-close",
        ttl_seconds=300,
    )
    assert successor.generation == 2
    assert successor.fencing_token == 2
    assert supervisor.close_driver(role=LaunchRole.DRIVER, lease=successor) == "closed"

    expired_stream = "epic:4708"
    store.open_session(
        stream_id=expired_stream,
        holder=LeaseHolder(
            agent="grok",
            harness="grok-tui",
            instance_id="expired-dead-holder",
            process_id=999_999_009,
        ),
        lineage_id="lineage-expired-dead-holder",
        ttl_seconds=30,
        now=utc_now() - timedelta(minutes=5),
    )
    rerouted = supervisor.open_driver(
        role=LaunchRole.DRIVER,
        stream_id=expired_stream,
        holder=LeaseHolder(
            agent="codex",
            harness="codex-cli",
            instance_id="ttl-reroute-successor",
            process_id=os.getpid(),
        ),
        lineage_id="lineage-ttl-reroute-successor",
        ttl_seconds=300,
    )
    assert rerouted.generation == 2
    assert rerouted.fencing_token == 2
    recovered_history = store.dump_stream(expired_stream)
    assert [session["state"] for session in recovered_history["sessions"]] == ["closed", "open"]
    assert "force_closed" in [event["event_type"] for event in recovered_history["lease_events"]]
    assert supervisor.close_driver(role=LaunchRole.DRIVER, lease=rerouted) == "closed"


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


def test_compat_wrappers_forward_to_shared_adapters() -> None:
    kimicc = (REPO / "start-kimicc.sh").read_text(encoding="utf-8")
    glmcc = (REPO / "start-glmcc.sh").read_text(encoding="utf-8")
    assert 'exec "$ROOT/start-kimi.sh" --harness claude-code "$@"' in kimicc
    assert 'exec "$ROOT/start-glm.sh" "$@"' in glmcc
    # Wrappers must not set route credentials themselves — isolation stays in
    # the shared route helpers.
    for body in (kimicc, glmcc):
        assert "ANTHROPIC_AUTH_TOKEN" not in body
        assert "ANTHROPIC_BASE_URL" not in body
        assert "ZAI_API_KEY" not in body
    # Sol P2: kimicc must reject a later --harness override.
    assert "--harness|--harness=*" in kimicc


def test_compat_kimicc_rejects_harness_override() -> None:
    result = run_launcher("start-kimicc.sh", "--harness", "kimi-code")
    assert result.returncode == 2
    assert "always uses Claude Code" in result.stderr


def test_compat_kimicc_and_glmcc_dry_run(tmp_path: Path) -> None:
    home = tmp_path / "home"
    kimi = run_launcher(
        "start-kimicc.sh",
        "--model",
        "k3",
        env={"HOME": str(home), "KIMICC_AUTH_TOKEN": "kimi-compat-secret"},
    )
    assert kimi.returncode == 0, kimi.stderr
    assert "credential_source=KIMICC_AUTH_TOKEN" in kimi.stdout
    assert "kimi-compat-secret" not in kimi.stdout + kimi.stderr

    glm = run_launcher(
        "start-glmcc.sh",
        env={"HOME": str(home), "ZAI_API_KEY": "glm-compat-secret"},
    )
    assert glm.returncode == 0, glm.stderr
    assert "credential_source=ZAI_API_KEY" in glm.stdout
    assert "glm-compat-secret" not in glm.stdout + glm.stderr


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
