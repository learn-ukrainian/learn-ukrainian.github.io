"""CTO wrappers use registered driver identity and preserve every refusal gate."""

from __future__ import annotations

import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from agents_extensions.shared.session_streams.db import SessionStreamDatabase
from agents_extensions.shared.session_streams.model import LeaseHolder
from agents_extensions.shared.session_streams.store import NotFoundError, SessionStreamStore
from tests.epics_monitor_stub import epics_monitor_stub
from tests.rules_core_view import _build_view
from tests.test_claude_cap_guard import launch_with_usage as _usage_fixture
from tests.test_launcher_contract import REPO, _core_canary_failure_fixture, run_launcher
from tests.test_launcher_driver_scope import scope_sandbox

pytestmark = pytest.mark.usefixtures("hermetic_monitor")
WRAPPERS = ("start-claude-cto.sh", "start-codex-cto.sh")
launch_with_usage = _usage_fixture
# The epics stream id comes from the registry, so a re-rooted epic needs no test edit.
_STREAMS = yaml.safe_load((REPO / "scripts/config/issue_streams.yaml").read_text(encoding="utf-8"))["streams"]
EPICS_STREAM = f"epic:{_STREAMS['epics']['epics'][0]}"


@pytest.fixture(autouse=True)
def clean_selection(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in (
        "LAUNCHER_MODEL",
        "LAUNCHER_EFFORT",
        "LU_CLAUDE_CAP_OVERRIDE",
        "SESSION_SUPERVISOR_WAKE_DELIVERY",
        "SESSION_SUPERVISOR_WAKE_STREAM",
        "LC_DRIVER_LEASE_ENABLED",
    ):
        monkeypatch.delenv(key, raising=False)


@pytest.mark.parametrize("name", WRAPPERS)
@pytest.mark.parametrize("case", ("default", "model", "effort", "environment", "precedence"))
def test_cto_selection_and_dry_run(name: str, case: str, launch_with_usage) -> None:
    model = "claude-sonnet-5-5" if name == WRAPPERS[0] else "gpt-6.1-sol"
    alternate = "claude-fable-5-1" if name == WRAPPERS[0] else model
    args: tuple[str, ...] = ()
    env: dict[str, str] = {}
    expected_model, effort = model, "high"
    if case == "model":
        args, expected_model = ("--model", alternate), alternate
    elif case == "effort":
        args, effort = ("--effort=medium",), "medium"
    elif case == "environment":
        env, expected_model, effort = {"LAUNCHER_MODEL": alternate, "LAUNCHER_EFFORT": "medium"}, alternate, "medium"
    elif case == "precedence":
        env = {"LAUNCHER_MODEL": "not-certified", "LAUNCHER_EFFORT": "low"}
        args, effort = ("--model=" + model, "--effort", "xhigh"), "xhigh"
    result = launch_with_usage("0", *args, name=name, env=env)
    assert result.returncode == 0, result.stdout + result.stderr
    command = shlex.split(
        next(line.removeprefix("would exec ") for line in result.stdout.splitlines() if line.startswith("would exec "))
    )
    assert command[command.index("--model") + 1] == expected_model
    if name == WRAPPERS[0]:
        assert command[command.index("--effort") + 1] == effort
    else:
        assert f"model_reasoning_effort={effort}" in command
    provider = "claude" if name == WRAPPERS[0] else "codex"
    assert f"stream={EPICS_STREAM} agent={provider}" in result.stdout
    assert f"slot={provider}-epics" in result.stdout
    assert ".claude/epics-epic/DRIVER-STATE.md" in result.stdout
    assert "drive-epic" in result.stdout
    assert "LAUNCHER_DRY_RUN=1" in result.stdout
    assert not (Path(result.args[0]).parent / ".claude/epics-epic/DRIVER-STATE.md").exists()


@pytest.mark.parametrize("name", (*WRAPPERS, "start-claude-driver.sh", "start-codex-driver.sh"))
def test_epics_selector_is_registered_for_both_driver_seats(name, launch_with_usage) -> None:
    result = launch_with_usage("0", "--epic", "epics", name=name)
    assert result.returncode == 0, result.stderr
    assert f"stream={EPICS_STREAM}" in result.stdout
    assert "session epic=epics" in result.stdout


@pytest.mark.parametrize("name", WRAPPERS)
@pytest.mark.parametrize("args", (("--force",), ("--epic", "infra", "--force"), ("--model", "opus", "--force")))
def test_cto_force_is_refused_before_any_driver_work(name, args, launch_with_usage) -> None:
    result = launch_with_usage("0", *args, name=name)
    assert result.returncode == 2
    assert "CTO launchers reject --force" in result.stderr
    assert result.stdout == ""


@pytest.mark.parametrize("name", WRAPPERS)
@pytest.mark.parametrize(
    "selector, message", (("no-such-stream", "unknown lane selector"), ("docs-knowledge", "not registered"))
)
def test_cto_unregistered_selectors_stay_refused(name, selector, message, launch_with_usage) -> None:
    result = launch_with_usage("0", "--epic", selector, name=name)
    assert result.returncode == 2, result.stderr
    assert message in result.stderr
    assert "would claim lease" not in result.stdout
    assert "would exec" not in result.stdout


def test_epics_stream_key_is_distinct_from_nested_epics_and_duplicate_keys(tmp_path: Path) -> None:
    registry = tmp_path / "issue_streams.yaml"
    valid = 'schema_version: 1\nstreams:\n  epics:\n    title: "Coordination"\n    epics: [10453]\n  infra:\n    epics: [6943]\n'
    script = 'source "$1"; _launcher_stream_anchor_epic epics'
    for suffix, code, expected in (
        ("", 0, "10453"),
        ("  epics:\n    epics: [99999]\n", 1, ""),
        ("  infra:\n    epics: [99999]\n", 1, ""),
    ):
        registry.write_text(valid + suffix)
        result = subprocess.run(
            ["bash", "-c", script, "fixture", str(REPO / "scripts/lib/handoff_identity.sh")],
            env={**os.environ, "HANDOFF_ISSUE_STREAMS_YAML": str(registry)},
            capture_output=True,
            text=True,
            timeout=15,
        )
        assert result.returncode == code, result.stderr
        assert result.stdout == expected


def _runtime_checkout(tmp_path: Path) -> tuple[Path, dict[str, str]]:
    launcher, _, _ = _core_canary_failure_fixture(tmp_path)
    root = launcher.parent
    for name in WRAPPERS:
        shutil.copy2(REPO / name, root / name)
    env = scope_sandbox(root, tmp_path)
    # Only preparation and provider execution are fake. Slot validation, scope
    # re-entry, common supervisor and remote lease refusals execute real code.
    (root / "scripts/lib/deploy_extensions.sh").write_text("deploy_agent_extensions() { :; }\n")
    core = root / "scripts/lib/launcher_core.sh"
    core.write_text(core.read_text() + "\nlauncher_import_rollover_bundle() { :; }\n")
    for provider in ("claude", "codex"):
        (root / f"scripts/launchers/{provider}.sh").write_text("""launcher_adapter_validate() { :; }
launcher_adapter_preflight() { :; }
launcher_adapter_canary() { printf 'CANARY_STARTED\\n'; return 1; }
launcher_adapter_exec() { printf 'PROVIDER_STARTED\\n'; }
""")
    # The fixture interpreter forwards the real remote supervisor against an
    # owned loopback service. No production stream or provider is contacted.
    runner = root / ".venv/bin/python"
    module = f"import sys; sys.path.insert(0, {str(REPO)!r}); from scripts.session_supervisor import main; raise SystemExit(main(sys.argv[1:]))"
    runner.write_text(f"""#!/usr/bin/env bash
if [ "${{1:-}}" = -m ] && [ "${{2:-}}" = scripts.session_supervisor ]; then
  shift 2
  exec {shlex.quote(sys.executable)} -c {shlex.quote(module)} "$@"
fi
exec {shlex.quote(sys.executable)} "$@"
""")
    runner.chmod(0o755)
    return root, env


@pytest.mark.parametrize(
    "name, model_args",
    ((WRAPPERS[0], ()), (WRAPPERS[1], ()), (WRAPPERS[0], ("--model", "opus"))),
)
@pytest.mark.parametrize("refusal", ("occupied", "duplicate", "identity", "slot"))
def test_cto_epics_refusal_gates_execute_without_dry_run(
    tmp_path: Path, name: str, refusal: str, model_args: tuple[str, ...]
) -> None:
    root, env = _runtime_checkout(tmp_path)
    provider = "claude" if name == WRAPPERS[0] else "codex"
    store = SessionStreamStore(SessionStreamDatabase(tmp_path / "streams.sqlite3"))
    if refusal in {"occupied", "duplicate"}:
        store.open_session(
            stream_id=EPICS_STREAM,
            holder=LeaseHolder(
                agent=provider if refusal == "duplicate" else "grok",
                harness="claude-code" if provider == "claude" else "codex-cli",
                instance_id="existing-supervisor",
                process_id=os.getpid(),
                task_id="fixture-holder",
            ),
            lineage_id="fixture-lineage",
            ttl_seconds=900,
        )
        before = store.dump_stream(EPICS_STREAM)
        env["SESSION_INSTANCE_ID"] = "existing-supervisor" if refusal == "duplicate" else "candidate-supervisor"
    elif refusal == "identity":
        env.update(SESSION_SUPERVISOR_WAKE_DELIVERY="fixture-event", SESSION_SUPERVISOR_WAKE_STREAM="epic:6943")
    else:
        # Remove only the candidate's actual roster slot in the copied registry.
        roster = root / "scripts/config/area_assignments.yaml"
        roster.write_text(roster.read_text().replace(f"      - {provider}-epics\n", ""))
    with epics_monitor_stub(store) as monitor_url:
        result = run_launcher(
            name,
            "--epic",
            "epics",
            *model_args,
            root=root,
            dry_run=False,
            env={**env, "LU_MONITOR_LOOPBACK": monitor_url},
        )
    assert result.returncode == (2 if refusal == "slot" else 1), result.stdout + result.stderr
    if refusal in {"occupied", "duplicate"}:
        assert "already has live session" in result.stderr
        assert store.dump_stream(EPICS_STREAM) == before
    elif refusal == "identity":
        assert "supervisory event stream does not match this launcher" in result.stderr
        with pytest.raises(NotFoundError, match=f"stream not found: {EPICS_STREAM}"):
            store.dump_stream(EPICS_STREAM)
    else:
        assert f"'{provider}-epics'" in result.stderr
        assert "not registered" in result.stderr
    assert "CANARY_STARTED" not in result.stdout
    assert "PROVIDER_STARTED" not in result.stdout


@pytest.mark.parametrize(
    "name, model",
    ((WRAPPERS[0], "claude-sonnet-5-5"), (WRAPPERS[0], "claude-opus-5-5[1m]"), (WRAPPERS[1], "gpt-6.1-sol")),
)
def test_scope_reentry_preserves_cto_defaults_and_explicit_opus(tmp_path: Path, name: str, model: str) -> None:
    root, env = _runtime_checkout(tmp_path)
    core = root / "scripts/lib/launcher_core.sh"
    core.write_text(
        core.read_text()
        + """
launcher_load_rules_core() { printf 'REENTRY:%s|%s|%s|%s\\n' "${0##*/}" "$LC_EPIC" "$LC_MODEL" "$LC_EFFORT"; exit 0; }
"""
    )
    args = ("--model", model) if "opus" in model else ()
    result = run_launcher(name, *args, root=root, dry_run=False, env=env)
    assert result.returncode == 0, result.stdout + result.stderr
    assert f"REENTRY:{name}|epics|{model}|high\n" in result.stdout
    assert Path(env["FAKE_STARTS"]).read_text().splitlines() == ["start"]


@pytest.mark.parametrize(
    "name, args, model",
    (
        (WRAPPERS[0], (), "claude-sonnet-5-5"),
        (WRAPPERS[0], ("--model", "opus"), "claude-opus-5-5[1m]"),
        (WRAPPERS[1], (), "gpt-6.1-sol"),
    ),
)
def test_supervisor_successor_reenters_cto_wrapper(
    tmp_path: Path, name: str, args: tuple[str, ...], model: str
) -> None:
    core = (REPO / "scripts/lib/launcher_core.sh").read_text()
    core += """
launcher_load_rules_core() { printf 'SUCCESSOR:%s|%s|%s|%s\\n' "${0##*/}" "$LC_EPIC" "$LC_MODEL" "$LC_EFFORT"; exit 0; }
"""
    root = _build_view(
        tmp_path / "checkout",
        {
            ("scripts", "lib", "launcher_core.sh"): core,
            ("scripts", "lib", "claude_weekly_used.py"): "print('0')\n",
        },
    )
    script = """source "$1"
LC_ROOT="$2"
LC_PROVIDER="$3"
LC_DRIVER_LEASE_CLOSED=1
LC_SUPERVISORY_DELIVERY=fixture-event
SESSION_STREAM_ID=epic:10453
SESSION_STREAM_GENERATION=1
shift 3
LC_DRIVER_ORIGINAL_ARGS=("$@")
session_supervisor_exec_successor
"""
    result = subprocess.run(
        [
            "bash",
            "-c",
            script,
            str(root / name),
            str(REPO / "scripts/lib/session_supervisor.sh"),
            str(root),
            "claude" if name == WRAPPERS[0] else "codex",
            *args,
        ],
        env={**os.environ, "LAUNCHER_DRY_RUN": "1"},
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert f"SUCCESSOR:{name}|epics|{model}|high\n" in result.stdout


@pytest.mark.parametrize("name", WRAPPERS)
def test_cto_help_names_defaults_and_no_takeover(name) -> None:
    result = run_launcher(name, "--help")
    assert result.returncode == 0
    assert f"Usage: ./{name}" in result.stdout
    assert "CTO defaults: --epic epics" in result.stdout
    assert "--force is refused" in result.stdout
    assert "--epic infra --force" not in result.stdout
    assert os.access(REPO / name, os.X_OK)
