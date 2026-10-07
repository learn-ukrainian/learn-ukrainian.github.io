"""Real PostCompact hydration with a fake launcher lease and Monitor snapshot."""

from __future__ import annotations

import json
import os
import shlex
import shutil
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
HOOK = Path("agents_extensions/shared/hooks/post-compact.sh")


def _run_hook(tmp_path: Path, *, baseline: bool = False, selector: str = "open-model-data",
              stream: str = "epic:6321", export_stream: bool = True) -> tuple[str, list[str], list[str]]:
    """Run real hydration; baseline reconstructs only the unfixed stream inputs."""
    repo = tmp_path / "repo"
    canary = repo / "scripts/session_canary"
    canary.mkdir(parents=True)
    # Use the current tree's canary sources, with untouched dependencies from
    # the worktree. No virtualenv or secondary git checkout is needed.
    (repo / "scripts/__init__.py").write_text(f"__path__.append({str(ROOT / 'scripts')!r})\n")
    # Replay only these explicit capsule dependencies, never scan a repo tree.
    for name in (
        "__init__.py", "codex_lane.py", "gemini_lane.py", "glm_lane.py",
        "grok_lane.py", "handoff_select.py", "shared_hydration.py", "diary.py",
    ):
        source = ROOT / "scripts/session_canary" / name
        target = canary / name
        shutil.copy2(source, target)
    if baseline:
        # #9956's unfixed condition: selector missing from the old table,
        # no explicit stream and no launcher stream in the environment.
        # Keep the real CLI and capsule; only restore the invalid fallback.
        assert not export_stream
        lane = canary / "codex_lane.py"
        source = lane.read_text()
        resolver = "    return _gl._stream_id(args)"
        assert source.count(resolver) == 1
        lane.write_text(source.replace(resolver, (
            "    _gl.EPIC_STREAM_DEFAULTS.pop(args.epic, None)\n"
            "    return (getattr(args, 'stream', None) or os.environ.get('SESSION_STREAM_ID')\n"
            "            or _gl.EPIC_STREAM_DEFAULTS.get(args.epic, f'epic:{args.epic}'))"
        )))
    for directory in ("lib", "config"):
        (repo / "scripts" / directory).symlink_to(ROOT / "scripts" / directory, target_is_directory=True)
    hook = repo / HOOK
    hook.parent.mkdir(parents=True)
    (repo / "agents_extensions/shared/session_streams").symlink_to(
        ROOT / "agents_extensions/shared/session_streams", target_is_directory=True,
    )
    shutil.copy2(ROOT / HOOK, hook)
    if baseline:
        source = hook.read_text()
        stream_argument = ' --stream "$HYDRATION_STREAM"'
        assert source.count(stream_argument) == 1
        hook.write_text(source.replace(stream_argument, ""))
    diary = repo / f".claude/{selector}-epic/CODEX-DRIVER-HANDOFF.md"
    diary.parent.mkdir(parents=True)
    diary.write_text("# Driver handoff\n## Next Drive\n- Reconcile queue.\n")

    args_log = tmp_path / "hydrate-args"
    wrapper = tmp_path / "interpreter-recorder"
    wrapper.write_text(
        "#!/bin/bash\n"
        "if [ \"${1:-}\" = '-m' ]; then\n"
        f"  printf '%s\\n' \"$*\" >> {shlex.quote(str(args_log))}\n"
        "fi\n"
        f"exec {shlex.quote(sys.executable)} \"$@\"\n"
    )
    wrapper.chmod(0o755)
    environment = {
        key: value for key, value in os.environ.items()
        if not key.startswith(("SESSION_", "CODEX_", "GROK_", "GEMINI_", "LU_MONITOR_"))
        and key not in {"CLAUDE_NON_INTERACTIVE", "LEARN_UKRAINIAN_PIPELINE", "HANDOFF_ISSUE_STREAMS_YAML"}
    }
    environment.update({
        "CLAUDE_PROJECT_DIR": str(repo), "CODEX_CANONICAL_REPO_ROOT": str(repo),
        "SESSION_HANDOFF_AGENT": "codex-open-model-data", "SESSION_EPIC": selector,
        "THREAD_ROLLOVER_PYTHON": str(wrapper),
        "SESSION_BOUNDED_RUNNER": str(ROOT / "scripts/agent_runtime/bounded_command.py"),
        "CODEX_COMPACT_SESSION_START": "1", "PYTHONPATH": f"{repo}{os.pathsep}{ROOT}",
        "SESSION_STREAM_SESSION_ID": "session-fixture", "SESSION_STREAM_LEASE_ID": "lease-fixture",
        "SESSION_STREAM_GENERATION": "2", "SESSION_STREAM_FENCING_TOKEN": "7",
        "SESSION_STREAM_AGENT": "codex", "SESSION_STREAM_HARNESS": "codex-cli",
        "SESSION_STREAM_INSTANCE_ID": "codex-fixture", "SESSION_STREAM_PROCESS_ID": "1234",
        "SESSION_STREAM_TASK_ID": "launcher-fixture",
    })
    if export_stream:
        environment["SESSION_STREAM_ID"] = stream
    # The receipt is only fixture data; no lease is opened, renewed, or closed.
    (diary.parent / "session-lease.env").write_text("\n".join(
        f"export {key}={shlex.quote(value)}" for key, value in environment.items() if key.startswith("SESSION_STREAM_")
    ) + "\n")
    snapshot = {
        "stream_id": stream,
        "lease": {
            "stream_id": stream, "session_id": "session-fixture", "lease_id": "lease-fixture",
            "generation": 2, "fencing_token": 7,
            "holder": {
                "agent": "codex", "harness": "codex-cli", "instance_id": "codex-fixture",
                "task_id": "launcher-fixture", "process_id": 1234, "holder_kind": "process", "host_id": None,
            },
            "state": "active", "session_state": "open", "expires_at": "2099-01-01T00:00:00Z",
        },
        "digest": {"stream_id": stream, "limit": 1, "pinned": [], "recent": [], "high_water_entry_id": 0},
    }
    requests: list[str] = []

    class Monitor(BaseHTTPRequestHandler):
        def do_GET(self):
            requests.append(self.path)
            body = json.dumps(snapshot).encode()
            self.send_response(200)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass

    server = HTTPServer(("localhost", 0), Monitor)
    thread = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True)
    thread.start()
    environment["LU_MONITOR_LOOPBACK"] = f"http://localhost:{server.server_port}"
    try:
        result = subprocess.run(["bash", str(hook)], cwd=repo, env=environment,
                                capture_output=True, text=True, timeout=10)
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=1)
    assert result.returncode == 0, result.stderr
    context = json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"]
    return context, args_log.read_text().splitlines() if args_log.exists() else [], requests


def test_open_model_data_hook_main_blocks_and_head_is_ready(tmp_path: Path) -> None:
    main_context, main_args, main_requests = _run_hook(tmp_path / "main", baseline=True, export_stream=False)
    assert "HYDRATION BLOCKED" in main_context
    assert "invalid-stream-id" in main_context
    assert "--stream" not in main_args[0]
    assert main_requests == []
    head_context, head_args, head_requests = _run_hook(tmp_path / "head")
    assert "HYDRATION BLOCKED" not in head_context
    assert '"execution_allowed": true' in head_context
    assert '"state": "ready"' in head_context
    assert "--stream epic:6321" in head_args[0]  # allow-hardcoded-epic: #9956 pre-fix launcher lease fixture
    assert head_requests == ["/api/epics/v1/epic:6321?limit=1"]  # allow-hardcoded-epic: #9956 pre-fix lease fixture
    print("unfixed condition: invalid-stream-id BLOCKED; head: --stream epic:6321 READY")


@pytest.mark.parametrize("selector,stream", [
    ("infra", "epic:6943"), ("infra.devops", "epic:5703"),
    ("curriculum-upgrade", "epic:7994"), ("open-model-data", "epic:6321"),
])
def test_hook_valid_launcher_lane_classes_are_ready(tmp_path, selector, stream) -> None:
    context, args, requests = _run_hook(tmp_path, selector=selector, stream=stream)
    assert "HYDRATION BLOCKED" not in context
    assert '"execution_allowed": true' in context
    assert f"--stream {stream}" in args[0]
    assert requests == [f"/api/epics/v1/{stream}?limit=1"]


def test_hook_prefers_exact_launcher_stream_over_selector(tmp_path) -> None:
    context, args, requests = _run_hook(tmp_path, stream="epic:7994")
    assert "HYDRATION BLOCKED" not in context
    assert "--stream epic:7994" in args[0]  # allow-hardcoded-epic: explicit launcher stream override fixture
    assert requests == ["/api/epics/v1/epic:7994?limit=1"]  # allow-hardcoded-epic: explicit stream override fixture


def test_hook_without_launcher_stream_passes_shell_resolution(tmp_path) -> None:
    context, args, requests = _run_hook(tmp_path, export_stream=False)
    assert "--stream epic:6321" in args[0]  # allow-hardcoded-epic: #9956 pre-fix launcher stream fixture
    # Resolving the stream never substitutes for missing lease evidence.
    assert "HYDRATION BLOCKED" in context
    assert requests == []


def test_hook_unknown_selector_skips_hydration(tmp_path) -> None:
    context, args, requests = _run_hook(tmp_path, selector="unknown-lane", export_stream=False)
    assert "HYDRATION BLOCKED" in context
    assert "unresolved-stream-selector: unknown-lane" in context
    assert args == requests == []
