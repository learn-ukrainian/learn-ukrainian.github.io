"""CTO wrappers use registered driver identity and preserve every refusal gate."""

from __future__ import annotations

import hashlib
import json
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
launcher_load_rules_core() {
  [ "$SESSION_SUPERVISOR_WAKE_STREAM" = epic:10453 ] || exit 94
  [ "$SESSION_SUPERVISOR_WAKE_DELIVERY" = fixture-event ] || exit 95
  [ "$LC_SUPERVISORY_PREDECESSOR_GENERATION" = 1 ] || exit 96
  [ -z "${SESSION_STREAM_LEASE_ID:-}" ] || exit 97
  [ -z "${SESSION_STREAM_SESSION_ID:-}" ] || exit 98
  printf 'SUCCESSOR:%s|%s|%s|%s\\n' "${0##*/}" "$LC_EPIC" "$LC_MODEL" "$LC_EFFORT"
  printf 'CAPTURED:'
  printf '%s\\0' "${LC_DRIVER_ORIGINAL_ARGS[@]}"
  exit 0
}
"""
    root = _build_view(
        tmp_path / "checkout",
        {
            ("scripts", "lib", "launcher_core.sh"): core,
            ("scripts", "lib", "claude_weekly_used.py"): "print('0')\n",
            ("scripts", "lib", "session_supervisor.sh"): (REPO / "scripts/lib/session_supervisor.sh").read_text(),
            ("scripts", "ai_agent_bridge", "inbox_watch.sh"): "",
        },
    )
    home = tmp_path / "home"
    bindir = home / ".local/bin"
    bindir.mkdir(parents=True)
    config = tmp_path / "source policy"
    config.mkdir()
    role = "fixture role with spaces\nsecond line\n" + "ї" * 30000
    assert len(role.encode()) < 131072 < len(json.dumps(role).encode())
    (config / "CTO-ROLE-PROMPT.txt").write_text(role + "\n\n")
    # This source-only template mirrors the admitted wrapper, with test-owned
    # policy inputs. Authentication and launch executables below are fakes.
    wrapper = bindir / "lu-start-cto"
    wrapper_source = r"""#!/usr/bin/env bash
set -euo pipefail
REPO=@REPO@
CFG=@CFG@
ROLE=$CFG/CTO-ROLE-PROMPT.txt
ACCT_FILE=$CFG/claude-account
MODEL=@MODEL@
EFFORT=@EFFORT@
KICK=@KICK@

HERE=0
ACCT=""
for arg in "$@"; do
  case "$arg" in
    --here) HERE=1 ;;
    a|b) ACCT=$arg ;;
    -h|--help) sed -n '2,13p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "unknown argument: $arg (usage: lu-start-cto [a|b] [--here])" >&2; exit 2 ;;
  esac
done
[ -r "$ROLE" ] || { echo "missing $ROLE" >&2; exit 4; }
pgrep -f "operator-appointed CTO AND cross-epic" >/dev/null && { echo "refused: a CTO process is still running" >&2; exit 3; }
if [ -z "$ACCT" ]; then
  ACCT=$(tr -d '[:space:]' < "$ACCT_FILE" 2>/dev/null || true)
  [ "$ACCT" = b ] || ACCT=a
fi
if [ "$ACCT" = b ]; then DIR=@ACCOUNT@; else DIR=@ACCOUNT@; fi
[ -s "$DIR/.credentials.json" ] || { echo "refused: account $ACCT ($DIR) is not logged in" >&2; exit 4; }
CLAUDE_CONFIG_DIR=$DIR claude auth status 2>/dev/null | grep -q '"loggedIn": true' \
  || { echo "refused: account $ACCT is not logged in; run: CLAUDE_CONFIG_DIR=$DIR claude, then /login" >&2; exit 4; }
printf '%s\n' "$ACCT" > "$ACCT_FILE"
export CLAUDE_CONFIG_DIR=$DIR
echo "CTO seat: Claude account $ACCT ($DIR)"

LAUNCH=(./start-claude-cto.sh --epic epics --model "$MODEL" --effort "$EFFORT" "$KICK" -- --dangerously-skip-permissions --append-system-prompt "$(cat "$ROLE")")
if [ "$HERE" = 1 ]; then
  cd "$REPO" && exec "${LAUNCH[@]}"
fi
tmux has-session -t =cto 2>/dev/null && { echo "refused: tmux session cto exists (use --here inside it)" >&2; exit 3; }
tmux new-session -d -s cto -c "$REPO" -e "CLAUDE_CONFIG_DIR=$DIR" "./start-claude-cto.sh --epic epics --model $MODEL --effort $EFFORT \"$KICK\" -- --dangerously-skip-permissions --append-system-prompt \"\$(cat '$ROLE')\"; exec bash"
echo "started; attach with: tmux attach -t cto"
"""
    for key, value in {
        "REPO": str(root),
        "CFG": str(config),
        "MODEL": "claude-opus-5-5",
        "EFFORT": "high",
        "KICK": "fixture kick with spaces",
        "ACCOUNT": str(tmp_path / "fake-account"),
    }.items():
        wrapper_source = wrapper_source.replace("@" + key + "@", shlex.quote(value))
    wrapper.write_text(wrapper_source)
    wrapper.chmod(0o755)
    account = tmp_path / "fake-account"
    account.mkdir()
    (account / ".credentials.json").write_text("fixture-only")
    (config / "claude-account").write_text("b\n")
    cli = bindir / "claude"
    cli.write_text("#!/bin/sh\nprintf '%s\\n' '{\"loggedIn\": true}'\n")
    cli.chmod(0o755)
    pgrep = bindir / "pgrep"
    pgrep.write_text("#!/bin/sh\nexit 1\n")
    pgrep.chmod(0o755)
    generated = (
        "--epic",
        "epics",
        "--model",
        "claude-opus-5-5",
        "--effort",
        "high",
        "fixture kick with spaces",
        "--",
        "--dangerously-skip-permissions",
        "--append-system-prompt",
        role,
    )
    supported = name == WRAPPERS[0] and bool(args)
    captured = generated if supported else args
    if name == WRAPPERS[0]:
        from scripts.session_supervisor import SupervisorError, cto_wrapper_signature

        with pytest.MonkeyPatch.context() as patch:
            patch.chdir(root)
            if supported:
                assert len(cto_wrapper_signature(wrapper, root, root / name, list(captured))) == 64
            else:
                with pytest.raises(SupervisorError, match="cto-wrapper-unsupported"):
                    cto_wrapper_signature(wrapper, root, root / name, list(captured))
    # Exercise the actual watcher preflight with the metadata transported by
    # start_inbox_watch, rather than copying the launcher's locals into a probe.
    probe = tmp_path / "watcher_probe.py"
    probe.write_text(f"""import fcntl, hashlib, os, stat, sys
from tempfile import TemporaryFile
from types import SimpleNamespace
from unittest.mock import Mock, patch
sys.path[:0] = [{str(REPO)!r}, {str(REPO / "scripts")!r}]
from scripts.ai_agent_bridge import _inbox_watch as watch
assert os.getppid() == int(os.environ['FIXTURE_WATCHER_PARENT'])
assert os.getpid() == int(os.environ['FIXTURE_WATCHER_PID'])
with open(f'/proc/self/task/{{os.getpid()}}/children') as children:
    assert not children.read().strip()
available = watch.preflight_supervisory_successor()
if not available:
    service = Mock()
    supervisor = Mock()
    lease = SimpleNamespace(session_id='fixture-predecessor', stream_id='epic:10453', generation=1)
    request = watch.SupervisoryRequest('fixture-event', lease.stream_id, 'restart', 1)
    delivery = SimpleNamespace(delivery_id='fixture-event', state='queued')
    with patch.object(watch, 'pending_supervisory_delivery', return_value=delivery), \\
         patch.object(watch, 'read_supervisory_request', return_value=request):
        assert watch.consume_supervisory_event(
            service, supervisor, lease, restart_preflight=watch.preflight_supervisory_successor,
        ) is None
    service.claim_next_delivery.assert_not_called()
    service.record_supervisory_consumption.assert_not_called()
    supervisor.handoff_driver.assert_not_called()
    print('WATCHER_REFUSED_NO_CLAIM_CONSUME_PREPARE', flush=True)
else:
    print('WATCHER_SUPPORTED', flush=True)
# Unknown or malformed CTO capture must never fall back to generic CLI success.
if os.path.basename(os.environ['LC_SUPERVISORY_ENTRYPOINT']) == 'start-claude-cto.sh':
    # Repeated preflight must reopen at offset zero, preserving F1 parity.
    assert watch.preflight_supervisory_successor() == available
    os.environ.pop('LC_SUPERVISORY_ORIGINAL_ARGS_FD', None)
    assert not watch.preflight_supervisory_successor()
    os.environ['LC_SUPERVISORY_ORIGINAL_ARGS_FD'] = '215'
    assert stat.S_ISREG(os.fstat(215).st_mode)
    assert os.fstat(215).st_nlink == 0
    assert fcntl.fcntl(215, fcntl.F_GETFL) & os.O_ACCMODE == os.O_RDONLY
    raw = os.pread(215, os.fstat(215).st_size, 0)
    assert hashlib.sha256(raw).hexdigest() == os.environ['FIXTURE_ARGV_SHA256']
    assert raw.count(b'\\0') == int(os.environ['FIXTURE_ARGV_COUNT'])
    saved = os.dup(215)
    with TemporaryFile() as malformed:
        malformed.write(b'\\xff\\0')
        malformed.flush()
        os.dup2(malformed.fileno(), 215)
        # Invalid bytes refuse inside preflight, keeping the watcher alive and
        # leaving the queued delivery untouched even for a supported launcher.
        assert not watch.preflight_supervisory_successor()
        service = Mock()
        supervisor = Mock()
        lease = SimpleNamespace(session_id='fixture-predecessor', stream_id='epic:10453', generation=1)
        request = watch.SupervisoryRequest('fixture-event', lease.stream_id, 'restart', 1)
        delivery = SimpleNamespace(delivery_id='fixture-event', state='queued')
        with patch.object(watch, 'pending_supervisory_delivery', return_value=delivery), \\
             patch.object(watch, 'read_supervisory_request', return_value=request):
            assert watch.consume_supervisory_event(
                service, supervisor, lease, restart_preflight=watch.preflight_supervisory_successor,
            ) is None
        service.claim_next_delivery.assert_not_called()
        service.record_supervisory_consumption.assert_not_called()
        supervisor.handoff_driver.assert_not_called()
        malformed.seek(0)
        malformed.truncate()
        malformed.write(b'unterminated')
        malformed.flush()
        assert not watch.preflight_supervisory_successor()
    os.close(215)
    assert not watch.preflight_supervisory_successor()
    os.dup2(saved, 215)
    os.close(saved)
    assert watch.preflight_supervisory_successor() == available
raise SystemExit(0 if available else 3)
""")
    watcher = root / "scripts/ai_agent_bridge/inbox_watch.sh"
    watcher.parent.mkdir(parents=True, exist_ok=True)
    watcher.write_text(f"#!/usr/bin/env bash\nexec {shlex.quote(sys.executable)} {shlex.quote(str(probe))}\n")
    watcher.chmod(0o755)
    script = r"""set -euo pipefail
source "$1"
LC_ROOT="$2"
LC_PROVIDER="$3"
LC_MODE=driver
LC_DURABLE_HELPER_ROOT="$2"
source "$2/scripts/lib/launcher_core.sh"
LC_DRIVER_PROVIDER_COMMAND=claude
LC_DRIVER_PROVIDER_EXECUTABLE="$HOME/.local/bin/claude"
LC_DRIVER_LEASE_CLOSED=0
LC_SUPERVISORY_DELIVERY=fixture-event
export SESSION_STREAM_ID=epic:10453 SESSION_STREAM_GENERATION=1
export SESSION_STREAM_LEASE_ID=fixture-lease SESSION_STREAM_SESSION_ID=fixture-predecessor
shift 3
LC_DRIVER_ORIGINAL_ARGS=("$@")
# A live fake predecessor must survive a refused preflight. Only a successful
# preflight permits the exact predecessor stop and existing release/exec edge.
sleep 30 & predecessor=$!
trap 'kill "$predecessor" 2>/dev/null || true; wait "$predecessor" 2>/dev/null || true' EXIT
export FIXTURE_WATCHER_PARENT=$BASHPID
# Reap the small producer before exec, reproducing Bash's pre-exec race
# deterministically. The large payload partition must drain in Python first.
set -T
trap 'if [[ $BASH_COMMAND == exec\ \"\$capture_python\"* || $BASH_COMMAND == exec\ \"\$watcher\"* ]]; then
  export FIXTURE_WATCHER_PID=$BASHPID
  if [[ $BASH_COMMAND == exec\ \"\$capture_python\"* && $FIXTURE_REAP_CAPTURE = 1 ]]; then
    wait "$!"
    printf "CAPTURE_PRODUCER_REAPED\\n" >&2
  fi
fi' DEBUG
session_supervisor_start_inbox_watch
trap - DEBUG
watcher_rc=0
wait "$LC_SUPERVISORY_WATCH_PID" || watcher_rc=$?
cat <&216
LC_SUPERVISORY_WATCH_PID=""
session_supervisor_stop_inbox_watch
LC_SUPERVISORY_DELIVERY=fixture-event
if ! session_supervisor_preflight_successor; then
  [ "$watcher_rc" = 3 ] || exit 90
  kill -0 "$predecessor" || exit 91
  [ "$LC_DRIVER_LEASE_CLOSED" = 0 ] || exit 92
  printf 'PREDECESSOR_RETAINED\n'
  exit 3
fi
[ "$watcher_rc" = 0 ] || exit 89
kill -0 "$predecessor" || exit 91
[ "$LC_DRIVER_LEASE_CLOSED" = 0 ] || exit 92
kill "$predecessor"
wait "$predecessor" 2>/dev/null || true
trap - EXIT
if session_supervisor_exec_successor; then exit 93; fi
LC_DRIVER_LEASE_CLOSED=1
session_supervisor_exec_successor
"""
    scratch_root = tmp_path / "runtime scratch"
    for capture_tmpdir in (None, tmp_path / "ambient temp"):
        launcher_env = dict(os.environ)
        launcher_env["LU_SCRATCH_ROOT"] = str(scratch_root)
        if capture_tmpdir is None:
            launcher_env.pop("TMPDIR", None)
        else:
            capture_tmpdir.mkdir()
            launcher_env["TMPDIR"] = str(capture_tmpdir)
        if supported:
            # Keep the huge UTF-8 input with TMPDIR set; use a small supported
            # vector for the deterministic pre-exec reap with TMPDIR unset.
            partition_role = role if capture_tmpdir is not None else ""
            (config / "CTO-ROLE-PROMPT.txt").write_text(partition_role + "\n\n")
            captured = (*generated[:-1], partition_role)
        raw = b"".join(arg.encode() + b"\0" for arg in captured)
        launcher_env["FIXTURE_ARGV_SHA256"] = hashlib.sha256(raw).hexdigest()
        launcher_env["FIXTURE_ARGV_COUNT"] = str(len(captured))
        launcher_env["FIXTURE_REAP_CAPTURE"] = "1" if capture_tmpdir is None else "0"
        result = subprocess.run(
            [
                "bash",
                "-c",
                script,
                str(root / name),
                str(root / "scripts/lib/session_supervisor.sh"),
                str(root),
                "claude" if name == WRAPPERS[0] else "codex",
                *captured,
            ],
            cwd=root,
            env={
                **launcher_env,
                "LAUNCHER_DRY_RUN": "1",
                "HOME": str(home),
                "PATH": f"{bindir}{os.pathsep}{os.defpath}",
            },
            capture_output=True,
            text=True,
            timeout=30,
        )
        if name == WRAPPERS[0] and capture_tmpdir is None:
            assert "CAPTURE_PRODUCER_REAPED\n" in result.stderr
        if name == WRAPPERS[0] and not supported:
            assert result.returncode == 3, result.stdout + result.stderr
            assert "cto-wrapper-unsupported" in result.stderr
            assert result.stdout == "WATCHER_REFUSED_NO_CLAIM_CONSUME_PREPARE\nPREDECESSOR_RETAINED\n"
            assert "SUCCESSOR:" not in result.stdout
        else:
            assert result.returncode == 0, result.stdout + result.stderr
            selected_model = "claude-opus-5-5" if supported else model
            assert result.stdout.startswith("WATCHER_SUPPORTED\n")
            assert f"SUCCESSOR:{name}|epics|{selected_model}|high\n" in result.stdout
            assert result.stdout.endswith("CAPTURED:" + "\0".join(captured) + "\0")
            assert (config / "claude-account").read_text() == "b\n"
        assert not list((scratch_root / "task-scratch").glob("cto-argument-capture.*"))
