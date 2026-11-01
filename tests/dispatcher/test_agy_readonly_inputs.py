"""Explicit read-only AGY inputs are mounted at a fixed path or refused before spawn."""

import hashlib
import json
import os
import shlex
import subprocess
import sys
import time
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from scripts.dispatcher import agy_sandbox, cli, git, store, worker
from scripts.dispatcher.providers import agy as agy_provider


def _git(cwd: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(cwd), *args],
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    ).stdout.strip()


def _linked_worktree(tmp_path: Path) -> tuple[Path, Path]:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    (repo / "README.md").write_text("reviewed\n")
    _git(repo, "add", "README.md")
    _git(repo, "-c", "user.email=s@example.invalid", "-c", "user.name=S", "commit", "-q", "-m", "base")
    worktree = tmp_path / "worktree"
    _git(repo, "worktree", "add", "-q", "--detach", str(worktree), "main")
    return repo, worktree


def _bwrap_usable() -> bool:
    if agy_sandbox.unavailable():
        return False
    probe = subprocess.run(
        ["bwrap", "--ro-bind", "/", "/", "--unshare-net", "--unshare-pid", "--dev", "/dev", "--proc", "/proc", "true"],
        capture_output=True,
        check=False,
        timeout=30,
    )
    return probe.returncode == 0


def _launch(
    tmp_path: Path, worktree: Path, task_id: str, command: list[str], inputs: list[dict]
) -> tuple[list[str], dict]:
    final = tmp_path / f"{task_id}.result"
    argv = [
        sys.executable,
        "-I",
        "-c",
        agy_sandbox._BOOTSTRAP,
        str(agy_sandbox.ROOT),
        "--task-id",
        task_id,
        "--worktree",
        str(worktree),
        "--scratch",
        str(tmp_path / f"scratch-{task_id}"),
        "--receipt",
        str(agy_sandbox.receipt_file(final)),
    ]
    for item in inputs:
        argv += ["--input", item["path"], "--input-sha256", item["sha256"]]
    argv += ["--", *command]
    app = tmp_path / "agy-home"
    app.mkdir(exist_ok=True)
    (app / "antigravity-oauth-token").write_text("token")
    return argv, {**os.environ, "AGY_APP_DATA_DIR": str(app)}


def test_refuses_unusable_input_before_spawn(tmp_path, monkeypatch, capsys):
    """Defect class: denied aliases or failed identity checks still start the task."""
    tasks = tmp_path / "tasks"
    monkeypatch.setenv("LU_TASKS_DIR", str(tasks))
    checkout = tmp_path / "checkout"
    checkout.mkdir()
    monkeypatch.setattr(
        git, "resolve_repo", lambda _key=None: (checkout, {"key": "public", "github": "example/public"})
    )
    monkeypatch.setattr(git, "worktree_plan", lambda *args, **kwargs: (tmp_path / "wt", "agy/input", "a" * 40))
    monkeypatch.setattr(git, "create_worktree", Mock())
    monkeypatch.setattr(worker, "settle_left_worktrees", lambda: None)
    start = Mock()
    monkeypatch.setattr(worker, "start", start)
    packet = tmp_path / "packet.bin"
    packet.write_bytes(b"kept\n")
    inside = checkout / "tracked.txt"
    inside.write_text("inside\n")

    def refuse(extra: list[str], message: str, task_id: str) -> None:
        assert (
            cli.main(
                [
                    "dispatch",
                    "--agent",
                    "agy",
                    "--model",
                    "gemini-3.8-flash-high",
                    "--task-id",
                    task_id,
                    "--prompt",
                    "Read the input.",
                    "--mode",
                    "read-only",
                    *extra,
                ]
            )
            == 2
        )
        assert message in capsys.readouterr().err
        start.assert_not_called()
        git.create_worktree.assert_not_called()

    missing = tmp_path / "missing.bin"
    refuse(["--input", str(missing)], "agy_input_refused: not a readable regular file", "missing")
    directory = tmp_path / "dir"
    directory.mkdir()
    refuse(["--input", str(directory)], "agy_input_refused: not a regular file", "directory")
    link = tmp_path / "link.bin"
    link.symlink_to(packet)
    refuse(["--input", str(link)], "agy_input_refused: symlink", "symlink")
    huge = tmp_path / "huge.bin"
    huge.touch()
    os.truncate(huge, agy_sandbox.MAX_INPUT_BYTES + 1)
    refuse(["--input", str(huge)], f"agy_input_refused: larger than {agy_sandbox.MAX_INPUT_BYTES} bytes", "oversize")
    assert (
        cli.main(
            [
                "dispatch",
                "--agent",
                "sol",
                "--model",
                "gpt-6.1-sol",
                "--task-id",
                "other-agent",
                "--prompt",
                "Read the input.",
                "--mode",
                "read-only",
                "--input",
                str(packet),
            ]
        )
        == 2
    )
    assert "agy_input_refused: --input requires --agent agy and --mode read-only" in capsys.readouterr().err
    assert (
        cli.main(
            [
                "dispatch",
                "--agent",
                "agy",
                "--model",
                "gemini-3.8-flash-high",
                "--task-id",
                "write-mode",
                "--prompt",
                "Read the input.",
                "--mode",
                "workspace-write",
                "--input",
                str(packet),
            ]
        )
        == 2
    )
    assert "agy_input_refused: --input requires --agent agy and --mode read-only" in capsys.readouterr().err
    refuse(
        ["--input", str(packet), "--input", str(missing)],
        "agy_input_refused: not a readable regular file",
        "partial",
    )
    refuse(["--input", str(inside)], "agy_input_refused: path is inside the primary checkout", "inside")
    too_many = [flag for index in range(9) for flag in ("--input", str(tmp_path / f"{index}.bin"))]
    refuse(too_many, f"agy_input_refused: more than {agy_sandbox.MAX_INPUTS} inputs", "too-many")
    home = tmp_path / "home"
    secret = home / ".ssh" / "token"
    secret.parent.mkdir(parents=True)
    secret.write_text("x")
    monkeypatch.setattr(agy_sandbox.Path, "home", staticmethod(lambda: home))
    refuse(["--input", str(secret)], "agy_input_refused: path is under a credential directory", "credential")
    # Hard links must not let denied bytes enter through an allowed name.
    alias = tmp_path / "credential-alias.bin"
    alias.hardlink_to(secret)
    refuse(["--input", str(alias)], "agy_input_refused: hard link", "credential-hardlink")
    checkout_alias = tmp_path / "checkout-alias.bin"
    checkout_alias.hardlink_to(inside)
    refuse(["--input", str(checkout_alias)], "agy_input_refused: hard link", "checkout-hardlink")
    ordinary = tmp_path / "ordinary.bin"
    ordinary.write_bytes(b"ordinary\n")
    recorded = agy_sandbox.bind_inputs([str(ordinary)], repo_root=checkout)
    ordinary_alias = tmp_path / "ordinary-alias.bin"
    ordinary_alias.hardlink_to(ordinary)
    refuse(["--input", str(ordinary_alias)], "agy_input_refused: hard link", "ordinary-hardlink")
    with pytest.raises(agy_sandbox.Refused, match="agy_input_refused: hard link"):
        agy_sandbox.confirm_inputs(recorded, repo_root=checkout)

    late_packet = tmp_path / "late.bin"
    late_packet.write_bytes(b"late\n")
    original_read_exact = agy_sandbox._read_exact

    def linked_during_read(descriptor, size):
        data = original_read_exact(descriptor, size)
        (tmp_path / "late-alias.bin").hardlink_to(late_packet)
        return data

    with monkeypatch.context() as branch:
        branch.setattr(agy_sandbox, "_read_exact", linked_during_read)
        with pytest.raises(ValueError, match="agy_input_refused: hard link"):
            agy_sandbox.bind_inputs([str(late_packet)], repo_root=checkout)

    # F6: each identity lookup failure refuses before payload reads or spawn.
    original_read = os.read
    with monkeypatch.context() as branch:
        read = Mock(wraps=original_read)
        branch.setattr(os, "read", read)
        for target, message in (
            ("relative.bin", "path changed before read"),
            (str(packet) + " (deleted)", "path changed before read"),
            (str(secret), "path is under a credential directory"),
            (str(inside), "path is inside the primary checkout"),
        ):
            branch.setattr(os, "readlink", lambda _descriptor, target=target: target)
            with pytest.raises(ValueError, match="agy_input_refused: " + message):
                agy_sandbox.bind_inputs([str(packet)], repo_root=checkout)
        branch.setattr(os, "readlink", Mock(side_effect=OSError("unavailable")))
        with pytest.raises(ValueError, match="agy_input_refused: not a readable regular file"):
            agy_sandbox.bind_inputs([str(packet)], repo_root=checkout)
        read.assert_not_called()

    original_stat = os.stat
    stat_calls = 0

    def failed_identity_stat(path, *args, **kwargs):
        nonlocal stat_calls
        if path == packet:
            stat_calls += 1
            # Path.resolve(strict=True) performs the first stat; the bind performs the second.
            if stat_calls == 2:
                raise OSError("unavailable")
        return original_stat(path, *args, **kwargs)

    with monkeypatch.context() as branch:
        read = Mock(wraps=original_read)
        branch.setattr(os, "read", read)
        branch.setattr(os, "stat", failed_identity_stat)
        with pytest.raises(ValueError, match="agy_input_refused: not a readable regular file"):
            agy_sandbox.bind_inputs([str(packet)], repo_root=checkout)
        assert stat_calls == 2
        read.assert_not_called()

    original_readlink = os.readlink
    monkeypatch.setattr(os, "readlink", lambda _descriptor: "/different/path")
    with pytest.raises(ValueError, match="agy_input_refused: path changed before read"):
        agy_sandbox.bind_inputs([str(packet)], repo_root=checkout)
    monkeypatch.setattr(os, "readlink", original_readlink)
    original = os.fstat

    def mismatched(fd):
        info = original(fd)

        class _Stat:
            st_mode = info.st_mode
            st_ino = info.st_ino + 1
            st_dev = info.st_dev
            st_size = info.st_size
            st_nlink = info.st_nlink

        return _Stat()

    monkeypatch.setattr(os, "fstat", mismatched)
    with pytest.raises(ValueError, match="agy_input_refused: path changed before read"):
        agy_sandbox.bind_inputs([str(packet)], repo_root=checkout)
    start.assert_not_called()
    assert not tasks.exists() or not list(tasks.glob("*.json"))


def test_ro_bind_records_digest(tmp_path, monkeypatch, capsys):
    """Defect class: the host directory is mounted, the mount is writable, or the digest is not the file bytes."""
    if not _bwrap_usable():
        pytest.skip("needs a usable unprivileged bubblewrap")
    data = b"packet-digest-proof\n"
    packet = tmp_path / "packet.bin"
    packet.write_bytes(data)
    digest = hashlib.sha256(data).hexdigest()
    tasks = tmp_path / "tasks"
    monkeypatch.setenv("LU_TASKS_DIR", str(tasks))
    checkout = tmp_path / "checkout"
    checkout.mkdir()
    monkeypatch.setattr(
        git, "resolve_repo", lambda _key=None: (checkout, {"key": "public", "github": "example/public"})
    )
    monkeypatch.setattr(git, "worktree_plan", lambda *args, **kwargs: (tmp_path / "planned", "agy/input", "a" * 40))
    monkeypatch.setattr(git, "create_worktree", Mock())
    monkeypatch.setattr(worker, "settle_left_worktrees", lambda: None)
    monkeypatch.setattr(agy_sandbox, "unavailable", lambda: None)
    start = Mock(side_effect=lambda spec, record, prompt, timeout: store.create(record, prompt))
    monkeypatch.setattr(worker, "start", start)
    assert (
        cli.main(
            [
                "dispatch",
                "--agent",
                "gemini",
                "--model",
                "gemini-3.8-flash-high",
                "--task-id",
                "agy-input",
                "--prompt",
                "Read /agy-inputs/0 and report its sha256.",
                "--mode",
                "read-only",
                "--research-task-family",
                "dispatcher",
                "--input",
                str(packet),
            ]
        )
        == 0
    ), capsys.readouterr().err
    spec = start.call_args.args[0]
    record = store.read("agy-input")
    saved = json.loads(record["options"]["inputs"])
    assert saved == [
        {
            "bytes": len(data),
            "index": 0,
            "mount": f"{agy_sandbox.INPUT_MOUNT}/0",
            "path": str(packet.resolve()),
            "sha256": digest,
        }
    ]
    assert "input" not in record["options"]
    invocation = agy_provider.build(spec, {})
    assert invocation.argv[invocation.argv.index("--input-sha256") + 1] == digest
    assert invocation.argv[invocation.argv.index("--input") + 1] == str(packet.resolve())
    added = [invocation.argv[index + 1] for index, arg in enumerate(invocation.argv) if arg == "--add-dir"]
    assert agy_sandbox.INPUT_MOUNT in added

    # The dispatch half replaced the bubblewrap check. Restore it before the real mount.
    monkeypatch.undo()
    repo, worktree = _linked_worktree(tmp_path)
    bound = agy_sandbox.bind_inputs([str(packet)], repo_root=repo)
    mount = f"{agy_sandbox.INPUT_MOUNT}/0"
    script = (
        f"sleep 0.4; "
        f"test ! -e {shlex.quote(str(packet.resolve()))} || exit 3; "
        f"test ! -e {agy_sandbox.INPUT_MOUNT}/not-provided || exit 4; "
        f'test "$(ls -A {agy_sandbox.INPUT_MOUNT})" = 0 || exit 7; '
        f"cat {mount} || exit 5; "
        f"echo x >> {mount} && exit 6; "
        "exit 0"
    )
    task_id = "agy-ro-input"
    argv, env = _launch(tmp_path, worktree, task_id, ["/bin/sh", "-c", script], bound)
    run = subprocess.Popen(argv, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=worktree)
    copy = tmp_path / f"scratch-{task_id}" / "inputs" / "0"
    deadline = time.time() + 30
    while time.time() < deadline and not copy.is_file() and run.poll() is None:
        time.sleep(0.05)
    assert copy.is_file()
    assert copy.read_bytes() == data
    assert copy.stat().st_ino != packet.stat().st_ino
    packet.write_bytes(b"mutated-after-copy\n")
    stdout, stderr = run.communicate(timeout=90)
    receipt_path = agy_sandbox.receipt_file(tmp_path / f"{task_id}.result")
    receipt = json.loads(receipt_path.read_text())
    assert (run.returncode, receipt["status"]) == (0, "ran"), (receipt.get("reason"), stderr.decode()[-800:])
    assert stdout == data
    assert packet.read_bytes() == b"mutated-after-copy\n"
    assert receipt["canary"]["passed"] is True
    assert receipt["inputs"] == [{"bytes": len(data), "mount": mount, "sha256": digest}]
    head = receipt["input"]["start"]["head"]
    proof_record = {
        "worktree_base_sha": head,
        "options": {"inputs": json.dumps(bound, separators=(",", ":"), sort_keys=True)},
    }
    _summary, count, error = agy_sandbox.verify(tmp_path / f"{task_id}.result", task_id, proof_record)
    assert error is None and isinstance(count, int)
    proof_record["options"]["inputs"] = json.dumps([{**bound[0], "sha256": "0" * 64}])
    _summary, count, error = agy_sandbox.verify(tmp_path / f"{task_id}.result", task_id, proof_record)
    assert count is None and error == "agy_read_only_boundary: input digest mismatch"


def test_refuses_when_digest_changes_before_start(tmp_path, monkeypatch):
    """Defect class: a swapped file is still mounted."""
    repo, worktree = _linked_worktree(tmp_path)
    packet = tmp_path / "packet.bin"
    packet.write_bytes(b"before\n")
    bound = agy_sandbox.bind_inputs([str(packet)], repo_root=repo)
    packet.write_bytes(b"after\n")
    app = tmp_path / "agy-home"
    app.mkdir()
    (app / "antigravity-oauth-token").write_text("token")
    monkeypatch.setenv("AGY_APP_DATA_DIR", str(app))
    marker = tmp_path / "ran"
    task_id = "digest-change"
    argv, _env = _launch(tmp_path, worktree, task_id, ["/bin/sh", "-c", f"touch {marker}"], bound)
    assert agy_sandbox.main(argv[argv.index("--task-id") :]) == agy_sandbox.REFUSED
    receipt = json.loads(agy_sandbox.receipt_file(tmp_path / f"{task_id}.result").read_text())
    assert receipt["status"] == "refused"
    assert receipt["reason"] == "agy_input_refused: digest changed before start"
    assert not marker.exists()
    assert not (tmp_path / f"scratch-{task_id}").exists()


def test_tool_results_survive_scratch_delete(tmp_path: Path) -> None:
    """The export is written before scratch removal, and a missing file is marked file_removed."""
    conversation = "7cd3ba85-817f-4a03-8223-1ff39ca42419"
    scratch = tmp_path / "scratch"
    app = scratch / "runtime" / "home" / ".gemini" / "antigravity-cli"
    kept = app / "brain" / conversation / ".system_generated" / "steps" / "34" / "output.txt"
    kept.parent.mkdir(parents=True)
    kept.write_text("kept body", encoding="utf-8")
    (app / "brain" / conversation / ".system_generated" / "steps" / "44").mkdir()
    final = tmp_path / "task.result"
    boundary = agy_sandbox._Boundary.__new__(agy_sandbox._Boundary)
    boundary.args = SimpleNamespace(receipt=str(agy_sandbox.receipt_file(final)), scratch=str(scratch))
    boundary.receipt = {}
    boundary.base = scratch
    boundary.created = True
    boundary.process = boundary.relay = boundary.egress = boundary.fixture = None
    boundary.cleanup()

    assert not scratch.exists()
    export = agy_sandbox.tool_results_file(final)
    payload = json.loads(export.read_text(encoding="utf-8"))
    by_step = {item["step_index"]: item for item in payload["calls"]}
    assert payload["schema"] == "agy-tool-results.v1"
    assert by_step[34]["output"] == "kept body"
    assert by_step[44]["output_missing"] == "file_removed"

    def event(step: int) -> dict:
        return {
            "event": "step_update",
            "step_update": {
                "conversation_id": conversation,
                "state": "DONE",
                "step_index": step,
                "tool_name": "call_mcp_tool",
                "tool_info": {
                    "parameters": {"ServerName": "sources", "ToolName": "search_text", "Arguments": "{}"},
                },
            },
        }

    stdout = tmp_path / "stdout.log"
    stdout.write_text(json.dumps(event(34)) + "\n" + json.dumps(event(44)) + "\n", encoding="utf-8")
    retained, missing = agy_sandbox.apply_tool_results(stdout, final, "i12339-tool-results")
    lines = [json.loads(line) for line in stdout.read_text(encoding="utf-8").splitlines()]
    assert (retained, missing) == (1, 1)
    assert lines[0]["step_update"]["tool_info"]["output"] == "kept body"
    assert lines[1]["step_update"]["tool_info"]["output_missing"] == "file_removed"
    assert not export.exists()
