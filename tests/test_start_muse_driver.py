"""Muse admission and shared lease lifecycle, with no provider/model calls."""

from __future__ import annotations

import os
import shutil
import signal
import subprocess
import sys
from pathlib import Path

import pytest

from agents_extensions.shared.session_streams.inventory import stream_anchor_id
from tests.test_launcher_contract import (
    _blocking_signal_provider,
    _core_driver_exit_fixture,
    _wait_for_launcher_readiness,
)

REPO = Path(__file__).resolve().parents[1]
CORE = REPO / "scripts/lib/launcher_core.sh"
ADAPTER = REPO / "scripts/launchers/muse.sh"
pytestmark = pytest.mark.usefixtures("hermetic_monitor")


@pytest.fixture
def muse_env(tmp_path: Path) -> dict[str, str]:
    bindir = tmp_path / "bin"
    bindir.mkdir()
    for name, body in {
        "muse": 'printf "muse-started\\n" >> "$MUSE_TEST_CALLS"; exit 99',
        "gh": (
            '[ "${MUSE_TEST_GH_RC:-0}" = 0 ] || exit "$MUSE_TEST_GH_RC"\n'
            '[ -z "${GH_REPO:-}${GITHUB_REPOSITORY:-}" ] || exit 98\n'
            "printf 'HTTP/2 200 OK\\r\\nContent-Type: application/json\\r\\n\\r\\n"
            '{"visibility":"%s"}\\n\' "${MUSE_TEST_VISIBILITY:-PUBLIC}"'
        ),
    }.items():
        binary = bindir / name
        binary.write_text(f"#!/bin/bash\n{body}\n")
        binary.chmod(0o755)
    env = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith(("LAUNCHER_", "GIT_", "SESSION_", "LC_")) and key != "LU_RULES_SEAT"
    }
    env.update(
        PATH=f"{bindir}:{os.environ['PATH']}",
        AGENT_ORIGINAL_PATH=f"{bindir}:{os.environ['PATH']}",
        AGENT_REAL_GH=str(bindir / "gh"),
        MUSE_TEST_CALLS=str(tmp_path / "muse-calls"),
    )
    return env


def launch(env: dict[str, str], *args: str, dry: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        [str(REPO / "start-muse-driver.sh"), *args],
        cwd=REPO,
        env={**env, "LAUNCHER_DRY_RUN": "1" if dry else "0"},
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert not Path(env["MUSE_TEST_CALLS"]).exists(), "admission/dry-run started the Muse binary"
    return result


def test_help_needs_no_provider_or_visibility_probe(muse_env: dict[str, str]) -> None:
    result = launch({**muse_env, "MUSE_TEST_GH_RC": "1"}, "--help", dry=False)
    assert result.returncode == 0, result.stderr
    for expected in ("Usage: ./start-muse-driver.sh", "muse-spark-1.3", "--effort", "--dry-run", "EXIT CODES:"):
        assert expected in result.stdout
    assert "--force" not in result.stdout
    assert "Unproven guards: shell, credential, publish, destructive-command, filesystem." in result.stdout


@pytest.mark.parametrize("selector", ["devops", "infra.devops"])
@pytest.mark.parametrize("effort", ["none", "minimal", "low", "medium", "high", "xhigh", "max", "ultra"])
def test_dry_run_argv_and_capsule_binding(
    muse_env: dict[str, str],
    tmp_path: Path,
    selector: str,
    effort: str,
) -> None:
    argv_path = tmp_path / "argv"
    result = launch(
        {**muse_env, "LAUNCHER_DRY_RUN_ARGV_FILE": str(argv_path)},
        "--epic",
        selector,
        "--effort",
        effort,
        "--dry-run",
        "--",
        "A bounded task",
    )
    assert result.returncode == 0, result.stderr
    argv = argv_path.read_bytes().decode().rstrip("\0").split("\0")
    assert argv[:-1] == [
        "muse",
        "--provider",
        "meta",
        "--model",
        "muse-spark-1.3",
        "--reasoning-effort",
        effort,
        "--workspace",
        str(REPO),
        "--worktree",
        "off",
        "--disable-shell",
        "--disable-write",
    ]
    assert argv[-1].startswith('<rules-core seat="core"')
    assert "A bounded task" in argv[-1]
    assert "launcher already claimed the devops lease" in argv[-1]
    stream = stream_anchor_id("devops", REPO)
    assert f"would claim lease stream={stream} agent=muse harness=muse-cli" in result.stdout
    assert "slot=muse-devops" in result.stdout
    assert "provider canary: not run; rollover uses scripts.session_canary.muse_lane mint and score" in result.stdout
    assert "MUSE_GUARD_PARITY_UNPROVEN" in result.stdout


@pytest.mark.parametrize("dry", [True, False])
@pytest.mark.parametrize(
    ("args", "override", "code", "reason"),
    [
        (["--model", "unknown"], {}, 4, "MUSE_MODEL_UNCERTIFIED"),
        (["--model", "claude-fable-5"], {}, 4, "MUSE_MODEL_UNCERTIFIED"),
        (["--model="], {}, 4, "MUSE_MODEL_UNCERTIFIED"),
        ([], {"LAUNCHER_MODEL": "unknown"}, 4, "MUSE_MODEL_UNCERTIFIED"),
        (["--epic", "folk"], {}, 4, "MUSE_UKRAINIAN_CONTENT_FORBIDDEN"),
        (["--epic", "bio"], {}, 4, "MUSE_UKRAINIAN_CONTENT_FORBIDDEN"),
        (["--epic", "hramatka"], {}, 4, "MUSE_UKRAINIAN_CONTENT_FORBIDDEN"),
        (["--epic", "open-model-data"], {}, 4, "MUSE_UKRAINIAN_CONTENT_FORBIDDEN"),
        (["--epic", "curriculum-upgrade"], {}, 4, "MUSE_CURRICULUM_CONTENT_FORBIDDEN"),
        (["--epic", "curriculum-upgrade"], {"LU_RULES_SEAT": "core"}, 4, "MUSE_CURRICULUM_CONTENT_FORBIDDEN"),
        ([], {"LU_RULES_SEAT": "content"}, 4, "MUSE_CURRICULUM_CONTENT_FORBIDDEN"),
        (["--epic", "infra"], {}, 4, "MUSE_STREAM_NOT_ADMITTED"),
        (["--epic", "atlas"], {}, 4, "MUSE_STREAM_NOT_ADMITTED"),
        (["--epic", "unknown"], {}, 4, "MUSE_STREAM_NOT_ADMITTED"),
        ([], {"MUSE_TEST_VISIBILITY": "PRIVATE"}, 4, "MUSE_PRIVATE_REPOSITORY_FORBIDDEN"),
        ([], {"MUSE_TEST_VISIBILITY": "INTERNAL"}, 4, "MUSE_PRIVATE_REPOSITORY_FORBIDDEN"),
        ([], {"MUSE_TEST_VISIBILITY": "UNKNOWN"}, 4, "MUSE_REPOSITORY_VISIBILITY_UNKNOWN"),
        ([], {"MUSE_TEST_GH_RC": "1"}, 4, "MUSE_REPOSITORY_VISIBILITY_UNKNOWN"),
        (["--effort", "bogus"], {}, 2, "MUSE_EFFORT_UNSUPPORTED"),
        (["--harness", "codex"], {}, 2, "MUSE_HARNESS_UNSUPPORTED"),
        (["--force"], {}, 4, "MUSE_FORCE_FORBIDDEN"),
        ([], {"LC_DRIVER_LEASE_ENABLED": "0"}, 4, "MUSE_LEASE_REQUIRED"),
        (["--", "--model", "muse-spark-1.3"], {}, 2, "MUSE_PROVIDER_FLAGS_FORBIDDEN"),
        (["--", "--config=hooks=[]"], {}, 2, "MUSE_PROVIDER_FLAGS_FORBIDDEN"),
        (["--", "--yolo"], {}, 2, "MUSE_PROVIDER_FLAGS_FORBIDDEN"),
        (["--", "resume", "--last"], {}, 2, "MUSE_PROVIDER_FLAGS_FORBIDDEN"),
    ],
)
def test_typed_refusals_before_provider(
    muse_env: dict[str, str],
    args: list[str],
    override: dict[str, str],
    code: int,
    reason: str,
    dry: bool,
) -> None:
    result = launch({**muse_env, **override}, "--epic", "devops", *args, dry=dry)
    assert result.returncode == code, result.stdout + result.stderr
    assert reason in result.stderr
    assert "would exec" not in result.stdout
    assert "would claim" not in result.stdout


def test_real_guard_gate_cannot_be_overridden(muse_env: dict[str, str]) -> None:
    result = launch({**muse_env, "MUSE_GUARD_PARITY_PROVEN": "1"}, "--epic", "devops", dry=False)
    assert result.returncode == 4
    assert "MUSE_GUARD_PARITY_UNPROVEN: shell,credential,publish,destructive-command,filesystem" in result.stderr
    assert result.stdout == ""


def test_repository_override_cannot_hide_private_checkout(muse_env: dict[str, str]) -> None:
    result = launch(
        {
            **muse_env,
            "GH_REPO": "example/public",
            "GITHUB_REPOSITORY": "example/public",
            "MUSE_TEST_VISIBILITY": "PRIVATE",
        },
        "--epic",
        "devops",
        dry=False,
    )
    assert result.returncode == 4
    assert "MUSE_PRIVATE_REPOSITORY_FORBIDDEN" in result.stderr


def test_direct_exec_seam_still_refuses(muse_env: dict[str, str]) -> None:
    result = subprocess.run(
        [
            "bash",
            "-c",
            'source "$1"; source "$2"; LC_DRY_RUN=0; launcher_adapter_exec',
            "bash",
            str(CORE),
            str(ADAPTER),
        ],
        cwd=REPO,
        env=muse_env,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 4
    assert "MUSE_GUARD_PARITY_UNPROVEN" in result.stderr
    assert not Path(muse_env["MUSE_TEST_CALLS"]).exists()


@pytest.mark.parametrize("provider", ["claude", "codex", "gemini", "grok", "cursor", "kimi", "glm"])
@pytest.mark.parametrize("mode", ["interactive", "driver"])
@pytest.mark.parametrize("variant", ["help", "default"])
def test_other_launcher_help_and_defaults_are_unchanged(provider: str, mode: str, variant: str) -> None:
    from tests.review.test_model_catalog import APPROVED_BASELINE, APPROVED_INPUTS

    index = APPROVED_INPUTS["launchers"].index({"provider": provider, "mode": mode, "variant": variant})
    command = """source "$1"
LC_PROVIDER="$2" LC_MODE="$3" LC_CURSOR_SEAT_PIN=grok-4.7-high
LC_ROOT="$5" LC_DURABLE_HELPER_ROOT="$6"
launcher_defaults
if [ "$4" = help ]; then launcher_parse --help; fi
launcher_normalize_model
launcher_normalize_effort
launcher_validate_driver_certification
printf '%s\\n' "$LC_MODEL" "$LC_EFFORT" "$LC_HARNESS" "$LC_ENDPOINT" "$LC_ISOLATE_CONFIG"
"""
    env = {k: v for k, v in os.environ.items() if not k.startswith("LAUNCHER_")}
    result = subprocess.run(
        ["bash", "-c", command, "capture", str(CORE), provider, mode, variant, str(REPO), str(Path(sys.prefix).parent)],
        cwd=REPO,
        env=env,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert {"exit_status": result.returncode, "stdout": result.stdout, "stderr": result.stderr} == (
        APPROVED_BASELINE["launchers"][index]
    )


def lifecycle_fixture(tmp_path: Path, body: str, ready: Path | None = None) -> tuple[Path, Path, Path]:
    """Isolate only Muse admission; exercise the unmodified shared lease machinery."""
    old_launcher, attempts, closed, _ = _core_driver_exit_fixture(
        tmp_path,
        provider_body=body,
        forward_ready=ready,
    )
    root = old_launcher.parent
    launcher = root / "start-muse-driver.sh"
    shutil.copy2(REPO / launcher.name, launcher)
    # Reuse the fixture's scope exports for this new entrypoint as well.
    original_body = old_launcher.read_text()
    scope_exports = original_body.split("set -euo pipefail", 1)[0].split("\n", 1)[1]
    body_text = launcher.read_text()
    launcher.write_text(body_text.replace("set -euo pipefail", scope_exports + "set -euo pipefail", 1))
    adapter = root / "scripts/launchers/muse.sh"
    adapter.write_text(
        "launcher_adapter_validate() { :; }\n"
        "launcher_adapter_preflight() { :; }\n"
        'launcher_adapter_canary() { printf "canary\\n" >> "$MUSE_TEST_EVENTS"; }\n'
        "launcher_adapter_exec() { launcher_exec_command muse; }\n"
    )
    python_stub = root / ".venv/bin/python"
    text = python_stub.read_text()
    text = text.replace("  cat <<'JSON'", '  printf "claim\\n" >> "$MUSE_TEST_EVENTS"\n  cat <<\'JSON\'', 1)
    text = text.replace("  touch ", '  printf "close\\n" >> "$MUSE_TEST_EVENTS"\n  touch ', 1)
    python_stub.write_text(text)
    bindir = tmp_path / "bin"
    bindir.mkdir()
    muse = bindir / "muse"
    muse.write_text('#!/bin/bash\nprintf "exec\\n" >> "$MUSE_TEST_EVENTS"\n' + body + "\n")
    muse.chmod(0o755)
    return launcher, attempts, closed


@pytest.mark.parametrize("exit_code", [0, 7])
def test_shared_lease_claim_exec_close_order(muse_env: dict[str, str], tmp_path: Path, exit_code: int) -> None:
    fixture_dir = tmp_path / "lifecycle"
    fixture_dir.mkdir()
    launcher, attempts, closed = lifecycle_fixture(fixture_dir, f"exit {exit_code}")
    events = tmp_path / "events"
    result = subprocess.run(
        ["bash", str(launcher), "--epic", "devops"],
        cwd=launcher.parent,
        env={**muse_env, "PATH": f"{fixture_dir / 'bin'}:{muse_env['PATH']}", "MUSE_TEST_EVENTS": str(events)},
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    assert result.returncode == exit_code, result.stdout + result.stderr
    assert events.read_text().splitlines() == ["claim", "canary", "exec", "close"]
    assert attempts.read_text().strip() == "1"
    assert closed.is_file()


@pytest.mark.parametrize(("sig", "exit_code"), [(signal.SIGINT, 130), (signal.SIGTERM, 143), (signal.SIGHUP, 129)])
def test_shared_signal_closes_muse_lease(
    muse_env: dict[str, str],
    tmp_path: Path,
    sig: signal.Signals,
    exit_code: int,
) -> None:
    fixture_dir = tmp_path / "lifecycle"
    fixture_dir.mkdir()
    ready, child_ready, received = (tmp_path / name for name in ("parent-ready", "child-ready", "received"))
    launcher, attempts, closed = lifecycle_fixture(
        fixture_dir,
        _blocking_signal_provider(received, child_ready),
        ready,
    )
    events = tmp_path / "events"
    process = subprocess.Popen(
        ["bash", str(launcher), "--epic", "devops"],
        cwd=launcher.parent,
        env={**muse_env, "PATH": f"{fixture_dir / 'bin'}:{muse_env['PATH']}", "MUSE_TEST_EVENTS": str(events)},
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        _wait_for_launcher_readiness(process, [ready, child_ready])
        process.send_signal(sig)
        stdout, stderr = process.communicate(timeout=60)
        assert process.returncode == exit_code, stdout + stderr
        assert received.is_file() and closed.is_file()
        assert attempts.read_text().strip() == "1"
        assert events.read_text().splitlines() == ["claim", "canary", "exec", "close"]
    finally:
        if process.poll() is None:
            process.kill()
        process.communicate(timeout=10)


def test_occupied_lease_refuses_before_canary_and_exec(muse_env: dict[str, str], tmp_path: Path) -> None:
    fixture_dir = tmp_path / "lifecycle"
    fixture_dir.mkdir()
    launcher, attempts, closed = lifecycle_fixture(fixture_dir, "exit 99")
    python_stub = launcher.parent / ".venv/bin/python"
    body = python_stub.read_text().replace(
        '  printf "claim\\n" >> "$MUSE_TEST_EVENTS"',
        '  printf "occupied\\n" >> "$MUSE_TEST_EVENTS"\n  echo "already has live session" >&2\n  exit 1',
        1,
    )
    python_stub.write_text(body)
    events = tmp_path / "events"
    result = subprocess.run(
        ["bash", str(launcher), "--epic", "devops"],
        cwd=launcher.parent,
        env={**muse_env, "PATH": f"{fixture_dir / 'bin'}:{muse_env['PATH']}", "MUSE_TEST_EVENTS": str(events)},
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert result.returncode == 1
    assert "already has live session" in result.stderr
    assert events.read_text().splitlines() == ["occupied"]
    assert not attempts.exists() and not closed.exists()


def test_canary_failure_closes_claim_without_provider(muse_env: dict[str, str], tmp_path: Path) -> None:
    fixture_dir = tmp_path / "lifecycle"
    fixture_dir.mkdir()
    launcher, attempts, closed = lifecycle_fixture(fixture_dir, "exit 99")
    adapter = launcher.parent / "scripts/launchers/muse.sh"
    adapter.write_text(
        adapter.read_text().replace(
            'printf "canary\\n" >> "$MUSE_TEST_EVENTS"; }',
            'printf "canary\\n" >> "$MUSE_TEST_EVENTS"; return 2; }',
        )
    )
    events = tmp_path / "events"
    result = subprocess.run(
        ["bash", str(launcher), "--epic", "devops"],
        cwd=launcher.parent,
        env={**muse_env, "PATH": f"{fixture_dir / 'bin'}:{muse_env['PATH']}", "MUSE_TEST_EVENTS": str(events)},
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert result.returncode == 2, result.stdout + result.stderr
    assert events.read_text().splitlines() == ["claim", "canary", "close"]
    assert closed.is_file() and attempts.read_text().strip() == "1"


@pytest.mark.parametrize("lost", [False, True])
def test_shared_renewal_precedes_close_and_stops_on_lease_loss(
    muse_env: dict[str, str],
    tmp_path: Path,
    lost: bool,
) -> None:
    fixture_dir = tmp_path / "lifecycle"
    fixture_dir.mkdir()
    launcher, attempts, closed = lifecycle_fixture(
        fixture_dir,
        'trap "exit 0" TERM\nwhile ! grep -q "^renew$" "$MUSE_TEST_EVENTS"; do sleep 0.05; done\n'
        + ("sleep 0.5\n" if lost else "")
        + "exit 0",
    )
    python_stub = launcher.parent / ".venv/bin/python"
    body = python_stub.read_text()
    first, rest = body.split("\n", 1)
    heartbeat = (
        'if [[ "${1:-}" == "-m" && "${2:-}" == "scripts.session_supervisor" && "${3:-}" == heartbeat ]]; then\n'
        '  printf "renew\\n" >> "$MUSE_TEST_EVENTS"\n'
        + ('  echo "LEASE LOST" >&2; exit 4\n' if lost else "  exit 0\n")
        + "fi\n"
    )
    python_stub.write_text(first + "\n" + heartbeat + rest)
    events = tmp_path / "events"
    result = subprocess.run(
        ["bash", str(launcher), "--epic", "devops"],
        cwd=launcher.parent,
        env={
            **muse_env,
            "PATH": f"{fixture_dir / 'bin'}:{muse_env['PATH']}",
            "MUSE_TEST_EVENTS": str(events),
            "SESSION_STREAM_RENEW_INTERVAL_SECONDS": "1",
            "SESSION_STREAM_RENEW_JITTER_SECONDS": "0",
        },
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert events.read_text().splitlines() == ["claim", "canary", "exec", "renew", "close"]
    assert closed.is_file() and attempts.read_text().strip() == "1"
    if lost:
        assert "LEASE LOST" in result.stderr
    capsules = list((launcher.parent / ".agent/session-capsules/epic-5703").glob("*.json"))
    assert len(capsules) == 1
    import json

    capsule = json.loads(capsules[0].read_text())
    assert capsule["agent"] == "muse" and capsule["harness"] == "muse-cli"
