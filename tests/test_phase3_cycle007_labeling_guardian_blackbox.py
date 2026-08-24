from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
GUARDIAN = ROOT / "scripts/projects/open_model_data/phase3_cycle007_labeling_guardian.py"
EXPECTED_TERMINAL = (
    ROOT / "tests/fixtures/phase3_cycle007_labeling_guardian/terminal-receipt.json"
)
STAGES = ("gemini", "grok", "compare", "audit", "adjudicate", "resolve", "certify")


def _wait_for(path: Path, timeout: float = 10.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if path.exists():
            return
        time.sleep(0.02)
    raise AssertionError(f"timed out waiting for {path.name}")


def _fixture_tree(tmp_path: Path) -> dict[str, Path]:
    package = tmp_path / "package"
    backing = tmp_path / "backing"
    locks = tmp_path / "locks"
    package.mkdir(mode=0o700)
    backing.mkdir(mode=0o700)
    locks.mkdir(mode=0o700)
    (package / "control").mkdir(mode=0o700)
    for name in (
        "label-output-gemini-cycle007-v1",
        "label-output-grok-cycle007-v1",
        "dual-label-output-cycle007-v1",
        "consensus-audit-cycle007-v1",
        "dual-label-adjudication-cycle007-v1",
        "dual-label-final-cycle007-v1",
    ):
        (backing / name).mkdir(mode=0o700)
    runner = tmp_path / "runner.py"
    runner.write_text("# held-out fake provider\n", encoding="utf-8")
    return {
        "package": package,
        "backing": backing,
        "locks": locks,
        "runner": runner,
        "state": package / "control/fake-controller-state.json",
    }


def _write_harness(
    tmp_path: Path,
    fixture: dict[str, Path],
    controller: Path,
    *,
    stage_timeout_seconds: float | None = None,
) -> Path:
    harness = tmp_path / "guardian-harness.py"
    code_paths = {
        "grok_runner": fixture["runner"],
        "compare_runner": fixture["runner"],
        "audit_runner": fixture["runner"],
        "adjudicate_runner": fixture["runner"],
        "resolve_runner": fixture["runner"],
        "certify_runner": fixture["runner"],
    }
    harness.write_text(
        f"""
import importlib.util, json, sys
from pathlib import Path

spec = importlib.util.spec_from_file_location("held_out_guardian", {str(GUARDIAN)!r})
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)
{f"module.STAGE_TIMEOUT_SECONDS = {stage_timeout_seconds!r}" if stage_timeout_seconds is not None else ""}
config = module.Config(
    action="resume",
    package=Path({str(fixture['package'])!r}),
    backing_root=Path({str(fixture['backing'])!r}),
    guardian_lock=Path({str(fixture['locks'] / 'guardian.lock')!r}),
    controller_lock=Path({str(fixture['locks'] / 'controller.lock')!r}),
    execution_lock=Path({str(fixture['locks'] / 'execution.lock')!r}),
    controller=Path({str(controller)!r}),
    preflight_receipt=Path({str(tmp_path / 'preflight.json')!r}),
    gemini_canary_receipt=Path({str(tmp_path / 'gemini.json')!r}),
    grok_canary_receipt=Path({str(tmp_path / 'grok.json')!r}),
    code_paths={{{', '.join(f'{label!r}: Path({str(path)!r})' for label, path in code_paths.items())}}},
    owner_uid=0,
    owner_gid=0,
    min_free_bytes=1,
    through=sys.argv[1],
    receipt=None,
    mountinfo=Path("/proc/self/mountinfo"),
    mount_command="mount",
    operator_inspected_count=None,
    resolution_authorization=None,
    resolution_authority_attestation=None,
    resolution_authority_root=None,
    resolution_nonce_ledger=None,
    resolution_advisor_response=None,
)
module._recover_guardian_temporaries = lambda _config: 0
module._require_free_space = lambda _config: 100
try:
    result = module._resume(config, [])
except module.GuardianError as exc:
    result = {{"ok": False, "failure_code": str(exc), "text_free": True}}
print(json.dumps(result, sort_keys=True, separators=(",", ":")))
""",
        encoding="utf-8",
    )
    return harness


def _run_harness(harness: Path, through: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(harness), through],
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
    )


def test_held_out_stage_sequence_reaches_terminal_and_second_run_is_noop(tmp_path: Path) -> None:
    fixture = _fixture_tree(tmp_path)
    controller = tmp_path / "fake-controller.py"
    controller.write_text(
        f"""
import argparse, json, os
from pathlib import Path

stages = {STAGES!r}
parser = argparse.ArgumentParser(add_help=False)
parser.add_argument("action")
parser.add_argument("--stage")
args, _unknown = parser.parse_known_args()
state_path = Path({str(fixture['state'])!r})
state = json.loads(state_path.read_text()) if state_path.exists() else {{"completed": [], "calls": []}}
if args.action == "run":
    os.fstat(int(os.environ["PHASE3_CYCLE007_EXECUTION_LOCK_FD"]))
    expected = stages[len(state["completed"])]
    if args.stage != expected:
        raise SystemExit(9)
    state["calls"].append(args.stage)
    state["completed"].append(args.stage)
    state_path.write_text(json.dumps(state, sort_keys=True))
    seal = state_path.parent / f"stage-{{args.stage}}.complete.json"
    seal.write_text("{{}}")
result = {{
    "ok": True,
    "completed_stages": state["completed"],
    "ready": state["completed"] == list(stages),
    "text_free": True,
}}
print(json.dumps(result, sort_keys=True, separators=(",", ":")))
""",
        encoding="utf-8",
    )
    harness = _write_harness(tmp_path, fixture, controller)
    first = _run_harness(harness, "certify")
    assert first.returncode == 0, first.stderr
    first_result = json.loads(first.stdout)
    state = json.loads(fixture["state"].read_text(encoding="utf-8"))
    assert first_result["completed_stages"] == list(STAGES)
    assert len(state["calls"]) == len(STAGES)

    second = _run_harness(harness, "certify")
    assert second.returncode == 0, second.stderr
    second_state = json.loads(fixture["state"].read_text(encoding="utf-8"))
    observed = {
        "completed_stages": json.loads(second.stdout)["completed_stages"],
        "provider_call_count": len(state["calls"]),
        "second_run_provider_call_count": len(second_state["calls"]),
        "text_free": True,
    }
    assert observed == json.loads(EXPECTED_TERMINAL.read_text(encoding="utf-8"))


def test_process_death_after_packet_boundary_resumes_at_next_packet(tmp_path: Path) -> None:
    fixture = _fixture_tree(tmp_path)
    controller = tmp_path / "packet-controller.py"
    paused = tmp_path / "paused"
    controller_pid = tmp_path / "controller.pid"
    packet_calls = tmp_path / "packet-calls.json"
    controller.write_text(
        f"""
import argparse, json, os, time
from pathlib import Path

parser = argparse.ArgumentParser(add_help=False)
parser.add_argument("action")
parser.add_argument("--stage")
args, _unknown = parser.parse_known_args()
state_path = Path({str(fixture['state'])!r})
calls_path = Path({str(packet_calls)!r})
state = json.loads(state_path.read_text()) if state_path.exists() else {{"completed": []}}
if args.action == "run":
    Path({str(controller_pid)!r}).write_text(str(os.getpid()))
    calls = json.loads(calls_path.read_text()) if calls_path.exists() else []
    next_packet = (calls[-1] + 1) if calls else 1
    while next_packet <= 3:
        calls.append(next_packet)
        temporary = calls_path.with_suffix(".tmp")
        temporary.write_text(json.dumps(calls))
        os.replace(temporary, calls_path)
        if next_packet == 1 and not Path({str(paused)!r}).exists():
            Path({str(paused)!r}).write_text("ready")
            time.sleep(60)
        next_packet += 1
    state["completed"] = ["gemini"]
    state_path.write_text(json.dumps(state))
print(json.dumps({{"ok": True, "completed_stages": state["completed"], "ready": False, "text_free": True}}))
""",
        encoding="utf-8",
    )
    harness = _write_harness(tmp_path, fixture, controller)
    first = subprocess.Popen(
        [sys.executable, str(harness), "gemini"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    _wait_for(paused)
    first.kill()
    os.kill(int(controller_pid.read_text(encoding="utf-8")), signal.SIGKILL)
    first.wait(timeout=5)

    second = _run_harness(harness, "gemini")
    assert second.returncode == 0, second.stderr
    assert json.loads(second.stdout)["completed_stages"] == ["gemini"]
    assert json.loads(packet_calls.read_text(encoding="utf-8")) == [1, 2, 3]


def test_surviving_runner_lock_blocks_replacement_guardian(tmp_path: Path) -> None:
    fixture = _fixture_tree(tmp_path)
    controller = tmp_path / "orphan-controller.py"
    controller_pid = tmp_path / "controller.pid"
    child_pid = tmp_path / "child.pid"
    child = tmp_path / "runner-child.py"
    child.write_text("import os,time; os.fstat(int(os.environ['LOCK_FD'])); time.sleep(60)\n", encoding="utf-8")
    controller.write_text(
        f"""
import argparse, json, os, subprocess, sys, time
from pathlib import Path

parser = argparse.ArgumentParser(add_help=False)
parser.add_argument("action")
parser.add_argument("--stage")
args, _unknown = parser.parse_known_args()
if args.action == "status":
    print(json.dumps({{"ok": True, "completed_stages": [], "ready": False, "text_free": True}}))
else:
    Path({str(controller_pid)!r}).write_text(str(os.getpid()))
    descriptor = int(os.environ["PHASE3_CYCLE007_EXECUTION_LOCK_FD"])
    process = subprocess.Popen(
        [sys.executable, {str(child)!r}],
        env={{**os.environ, "LOCK_FD": str(descriptor)}},
        pass_fds=(descriptor,),
    )
    Path({str(child_pid)!r}).write_text(str(process.pid))
    time.sleep(60)
""",
        encoding="utf-8",
    )
    harness = _write_harness(tmp_path, fixture, controller)
    first = subprocess.Popen(
        [sys.executable, str(harness), "gemini"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    _wait_for(child_pid)
    first.kill()
    os.kill(int(controller_pid.read_text(encoding="utf-8")), signal.SIGKILL)
    first.wait(timeout=5)
    try:
        replacement = _run_harness(harness, "gemini")
        assert replacement.returncode == 0
        assert json.loads(replacement.stdout)["failure_code"] == "active_worker"
    finally:
        os.kill(int(child_pid.read_text(encoding="utf-8")), signal.SIGKILL)


def test_real_controller_timeout_leaves_runner_lock_blocking_replacement(tmp_path: Path) -> None:
    fixture = _fixture_tree(tmp_path)
    controller = tmp_path / "timeout-controller.py"
    controller_pid = tmp_path / "controller.pid"
    child_pid = tmp_path / "child.pid"
    child = tmp_path / "timeout-runner-child.py"
    child.write_text(
        "import os,time; os.fstat(int(os.environ['LOCK_FD'])); time.sleep(60)\n",
        encoding="utf-8",
    )
    controller.write_text(
        f"""
import argparse, json, os, subprocess, sys, time
from pathlib import Path

parser = argparse.ArgumentParser(add_help=False)
parser.add_argument("action")
parser.add_argument("--stage")
args, _unknown = parser.parse_known_args()
if args.action == "status":
    print(json.dumps({{"ok": True, "completed_stages": [], "ready": False, "text_free": True}}))
else:
    Path({str(controller_pid)!r}).write_text(str(os.getpid()))
    descriptor = int(os.environ["PHASE3_CYCLE007_EXECUTION_LOCK_FD"])
    process = subprocess.Popen(
        [sys.executable, {str(child)!r}],
        env={{**os.environ, "LOCK_FD": str(descriptor)}},
        pass_fds=(descriptor,),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    Path({str(child_pid)!r}).write_text(str(process.pid))
    time.sleep(60)
""",
        encoding="utf-8",
    )
    timed_harness = _write_harness(
        tmp_path,
        fixture,
        controller,
        stage_timeout_seconds=0.5,
    )
    timed = _run_harness(timed_harness, "gemini")
    assert timed.returncode == 0, timed.stderr
    assert json.loads(timed.stdout)["failure_code"] == "controller_timeout"
    _wait_for(child_pid)
    with pytest.raises(ProcessLookupError):
        os.kill(int(controller_pid.read_text(encoding="utf-8")), 0)
    try:
        replacement = _run_harness(timed_harness, "gemini")
        assert replacement.returncode == 0, replacement.stderr
        assert json.loads(replacement.stdout)["failure_code"] == "active_worker"
    finally:
        os.kill(int(child_pid.read_text(encoding="utf-8")), signal.SIGKILL)


def test_adjudicator_return_before_stage_seal_blocks_duplicate_call(tmp_path: Path) -> None:
    fixture = _fixture_tree(tmp_path)
    controller = tmp_path / "adjudicate-controller.py"
    controller_pid = tmp_path / "controller.pid"
    provider_returned = tmp_path / "provider-returned"
    call_count = tmp_path / "call-count"
    completed = ["gemini", "grok", "compare", "audit"]
    controller.write_text(
        f"""
import argparse, json, os, time
from pathlib import Path

parser = argparse.ArgumentParser(add_help=False)
parser.add_argument("action")
parser.add_argument("--stage")
args, _unknown = parser.parse_known_args()
completed = {completed!r}
if args.action == "run":
    Path({str(controller_pid)!r}).write_text(str(os.getpid()))
    count_path = Path({str(call_count)!r})
    count = int(count_path.read_text()) if count_path.exists() else 0
    count_path.write_text(str(count + 1))
    Path({str(provider_returned)!r}).write_text("returned")
    time.sleep(60)
print(json.dumps({{"ok": True, "completed_stages": completed, "ready": False, "text_free": True}}))
""",
        encoding="utf-8",
    )
    harness = _write_harness(tmp_path, fixture, controller)
    first = subprocess.Popen(
        [sys.executable, str(harness), "adjudicate"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    _wait_for(provider_returned)
    first.kill()
    os.kill(int(controller_pid.read_text(encoding="utf-8")), signal.SIGKILL)
    first.wait(timeout=5)

    replacement = _run_harness(harness, "adjudicate")
    assert replacement.returncode == 0
    assert json.loads(replacement.stdout)["failure_code"] == "ambiguous_provider_attempt"
    assert call_count.read_text(encoding="utf-8") == "1"
