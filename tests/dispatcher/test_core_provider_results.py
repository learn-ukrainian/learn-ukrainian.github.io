"""Provider run outcomes: attestation, failure classes, capacity, stdin and pipe handling."""

import hashlib
import json
import os
import sys
from pathlib import Path
from unittest.mock import Mock

import pytest

from scripts.dispatcher import worker
from tests.dispatcher.conftest import await_file, run_git


def test_zombie_supervisor_fix_preserves_pid_reuse_cancellation_guard(monkeypatch):
    identity = worker._identity(os.getpid())
    record = dict(schema_version=2, status="running", pid=os.getpid(), process_start=identity)
    identities = iter([identity, f"{identity}-reused"])
    monkeypatch.setattr(worker.store, "read", lambda *_args: record)
    monkeypatch.setattr(worker, "_identity", lambda _pid: next(identities))
    send_signal = Mock()
    monkeypatch.setattr(worker.signal, "pidfd_send_signal", send_signal)
    with pytest.raises(ValueError, match="supervisor identity changed; cancellation refused"):
        worker.cancel("reused-supervisor")
    send_signal.assert_not_called()


def test_dispatch_returns_before_blocked_child_and_client_timeout_does_not_cancel(sandbox):
    task = sandbox.dispatch("blocked")
    pid = int(await_file(sandbox.tasks / f"{task[0]}.started"))
    assert worker._identity(pid)
    response = sandbox.cli("wait", task[0], "--run-nonce", task[1], "--timeout", "0.05", expected=124)
    assert json.loads(response.stdout)["status"] == "running"
    assert worker._identity(pid)
    (sandbox.tasks / f"{task[0]}.release").touch()
    record = sandbox.settle(task)
    assert record["status"] == "done"
    assert Path(record["result_file"]).read_text() == "literal final response"
    assert record["returncode"] == 0
    assert "review_branch" not in record
    assert "pinned_head" not in record
    assert record["started_at"] <= record["finished_at"]
    assert record["duration_s"] > 0
    assert record["usage"] == {"tokens": 7}
    assert record["result_sha256"] == hashlib.sha256(b"literal final response").hexdigest()
    assert (sandbox.tasks / "logs" / f"{task[0]}.stderr.log").read_text() == "stub stderr\n"
    assert not {"resolved_model", "resolved_model_known", "resolved_model_source"} & record.keys()
    assert (sandbox.tasks / f"{task[0]}.json").stat().st_mode & 0o777 == 0o600
    assert Path(record["prompt_file"]).stat().st_mode & 0o777 == 0o600


@pytest.mark.parametrize("mode", ["read-only", "workspace-write"])
@pytest.mark.parametrize("models", [[], ["Grok 4.7 256K High"], ["Grok 4.7 256K High", "different"]])
def test_cursor_v2_record_never_attests_a_model_the_runtime_did_not_report(sandbox, monkeypatch, models, mode):
    from scripts.review import record_cf_verdict as recorder

    binary_dir = sandbox.repo.parent / "bin"
    binary_dir.mkdir()
    executable = binary_dir / "cursor-agent"
    events = [{"type": "system", "subtype": "init", "model": model} for model in models]
    events.append({"type": "result", "subtype": "success", "result": "VERDICT: APPROVE"})
    stdout = "\n".join(json.dumps(event) for event in events)
    executable.write_text(f"#!{sys.executable}\nimport sys\nsys.stdin.read()\nprint({stdout!r})\n")
    executable.chmod(0o755)
    sandbox.env["PATH"] = str(binary_dir) + os.pathsep + os.defpath
    sandbox.env["CURSOR_API_KEY"] = "stub-process-key"
    # A read-only --branch dispatch is a review (C-2902 F10): it needs a reviewed commit outside its family.
    source = sandbox.review_target("requested-model-is-not-proof")[-1] if mode == "read-only" else "HEAD"
    run_git(sandbox.repo, "branch", "review-source", source)
    run_git(sandbox.repo, "push", "origin", "review-source")
    dispatched = sandbox.cli(
        "dispatch",
        "--agent",
        "cursor",
        "--model",
        "requested-model-is-not-proof",
        "--prompt",
        "The prompt claims Grok 4.7 256K High",
        "--mode",
        mode,
        "--branch",
        "review-source",
    )
    record = sandbox.settle(dispatched.stdout.splitlines(), expected=0 if mode == "read-only" else 1)
    known = len(models) == 1
    assert record["schema_version"] == 2
    assert record["model"] == "requested-model-is-not-proof"
    assert record["resolved_model"] == ("Grok 4.7 256K High" if known else "unknown")
    assert record["resolved_model_known"] is known
    assert record["resolved_model_source"] == ("cursor-stream-json" if known else "pending")
    if mode == "read-only":

        def stop_before_forge(*_args):
            raise recorder.RecordError("synthetic stop before forge")

        monkeypatch.setattr(recorder, "_pr", stop_before_forge)
        # The attested Grok model passes attestation and is then refused as a reviewer: Grok is retired
        # (GROK-CANCEL-1110). An unattested run is refused as unknown.
        reason = r"'grok-4\.7' is not a formal reviewer" if known else "Cursor reviewer model unknown"
        with pytest.raises(recorder.RecordError, match=reason):
            recorder.record(record["task_id"], task_root=sandbox.tasks, lock_root=sandbox.tasks / "locks")


def test_review_dispatch_resolves_a_running_cursor_author_only_from_its_stream_attestation(sandbox):
    """Defect (#12014): a running Cursor author's PR was unreviewable until its task exited.

    Cursor has no approved model pin while Grok is retired (GROK-CANCEL-1110), so no Cursor
    author can start: its former pin is refused before spawn. Restore the stream-attestation
    check when the operator approves a new Cursor pin.
    """
    author = sandbox.cli("dispatch", "--agent", "cursor", "--model", "grok-4.7-high", "--prompt", "Author a change",
                         "--mode", "workspace-write", expected=2)
    assert "is retired in the model catalog" in author.stderr


def test_agy_stream_from_another_model_family_settles_as_a_failure(sandbox):
    """Defect: a silently substituted model was credited as the requested one."""
    import threading
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

    windows = {
        "five_hour": {"used_pct": 1.0, "remaining_pct": 99.0},
        "weekly": {"used_pct": 10.0, "remaining_pct": 90.0},
    }
    body = json.dumps({
        "agents": {"gemini": {
            "status": "hot",
            "codexbar": {
                "stale": False, "freshness": "fresh", "weekly_used_pct": 22.0,
                "claude_gpt_windows": windows,
            },
            "claude_gpt_windows": windows,
        }},
    }).encode()

    class _Budget(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path.split("?", 1)[0] != "/api/state/routing-budget":
                self.send_response(404)
                self.end_headers()
                return
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *_args):
            return

    server = ThreadingHTTPServer(("127.0.0.1", 0), _Budget)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    sandbox.env["DELEGATE_MONITOR_API"] = f"http://127.0.0.1:{server.server_address[1]}"
    try:
        binary_dir = sandbox.repo.parent / "bin"
        binary_dir.mkdir()
        events = [
            {"event": "init", "init": {"model": "gemini-3.8-flash-high"}},
            {"event": "result", "result": {"status": "SUCCESS", "response": "done"}},
        ]
        stdout = "\n".join(json.dumps(event) for event in events) + "\n"
        executable = binary_dir / "agy"
        executable.write_text(f"#!{sys.executable}\nimport sys\nsys.stdin.read()\nprint({stdout!r}, end='')\n")
        executable.chmod(0o755)
        sandbox.env["PATH"] = str(binary_dir) + os.pathsep + os.defpath
        dispatched = sandbox.cli(
            "dispatch", "--agent", "agy", "--model", "claude-sonnet-5-5", "--prompt", "Reply with one word.",
            "--mode", "workspace-write",
        )
        record = sandbox.settle(dispatched.stdout.splitlines(), expected=1)
        assert record["status"] == "failed"
        assert record["model"] == "claude-sonnet-5-5-high"
        assert record["resolved_model"] == "gemini-3.8-flash-high"
        assert record["resolved_model_known"] is True
        assert record["resolved_model_source"] == "agy-stream-json"
        assert record["error"] == (
            "agy_model_identity_unverified: "
            "requested claude-sonnet-5-5-high (anthropic), attested gemini-3.8-flash-high (google)"
        )
    finally:
        server.shutdown()
        server.server_close()


@pytest.mark.parametrize(
    ("model", "state", "code"),
    [("fail", "failed", 17), ("error", "failed", 0), ("empty", "failed", 0), ("crash", "crashed", -9)],
)
def test_nonzero_error_empty_and_signal_cannot_report_done(sandbox, model, state, code):
    record = sandbox.settle(sandbox.dispatch(model), expected=1)
    assert record["status"] == state
    assert record["returncode"] == code


def test_provider_capacity_ends_rate_limited(sandbox):
    """Defect (FR-39): a provider out of capacity is a retryable condition, not a failed task."""
    record = sandbox.settle(sandbox.dispatch("capacity"), expected=1)
    assert (record["status"], record["returncode"]) == ("rate_limited", 1)
    record = sandbox.settle(sandbox.dispatch("capacity-dirty", "--mode", "workspace-write"), expected=1)
    assert record["status"] == "rate_limited"


def test_provider_capacity_is_rate_limited_when_an_output_schema_is_bound(sandbox):
    schema = sandbox.repo / "schema.json"
    schema.write_text('{"type":"object","required":["verdict"]}')
    record = sandbox.settle(sandbox.dispatch("capacity", "--output-schema", str(schema)), expected=1)
    assert (record["status"], record["returncode"]) == ("rate_limited", 1)


def test_provider_final_file_and_exact_stdin_bytes(sandbox):
    result = sandbox.cli(
        "dispatch", "--agent", "codex", "--model", "file", "--prompt-file", "-", stdin="exact\nbytes\n"
    )
    record = sandbox.settle(result.stdout.splitlines())
    assert Path(record["result_file"]).read_bytes() == b"exact\nbytes\n"
    assert record["prompt_sha256"] == hashlib.sha256(b"exact\nbytes\n").hexdigest()


def test_prompt_over_pipe_buffer_reaches_late_reading_child_complete(sandbox):
    stub = sandbox.repo / "scripts/dispatcher/providers/codex.py"
    stub.write_text(stub.read_text().replace(
        '    text = sys.stdin.buffer.read().decode()',
        '    time.sleep(0.5)\n    text = sys.stdin.buffer.read().decode()',
    ))
    prompt = ("0123456789abcdef" * 65536).encode()
    result = sandbox.cli(
        "dispatch", "--agent", "codex", "--model", "file", "--prompt-file", "-",
        stdin=prompt.decode(),
    )
    record = sandbox.settle(result.stdout.splitlines())
    received = Path(record["result_file"]).read_bytes()
    assert record["status"] == "done"
    assert len(received) == len(prompt)
    assert received == prompt
    assert hashlib.sha256(received).hexdigest() == hashlib.sha256(prompt).hexdigest()
    assert record["result_sha256"] == hashlib.sha256(prompt).hexdigest()
