"""Explicit read-only AGY inputs are mounted at a fixed path or refused before spawn."""

import hashlib
import json
import os
import shlex
import subprocess
import sys
import time
from pathlib import Path
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
    """Defect class: a bad input is dropped or the task still starts."""
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
