"""VPS worker exec + dual-host occupancy placement."""

from __future__ import annotations

import io
import os
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.fleet_comms.paths import RETIRED_LOCAL_MARKER
from scripts.orchestration import job_host_exec as jh


@pytest.fixture(autouse=True)
def _clear_occupancy_pin(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(jh.ENV_OCCUPANCY_HOST, raising=False)
    monkeypatch.delenv(jh.ENV_RUNTIME_INITIATOR, raising=False)
    monkeypatch.delenv(jh.ENV_RUNTIME_INITIATOR_SOURCE, raising=False)


def test_cli_help_runs_without_pythonpath(tmp_path: Path) -> None:
    script = Path(jh.__file__).resolve()
    env = os.environ.copy()
    env["PYTHONPATH"] = ""
    proc = subprocess.run(
        [sys.executable, str(script), "--help"],
        cwd=tmp_path,
        env=env,
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert proc.returncode == 0, proc.stderr
    assert "Examples:" in proc.stdout
    assert "Exit codes:" in proc.stdout


def _marker_root(tmp_path: Path) -> Path:
    plane = tmp_path / "batch_state" / "fleet-comms" / "v1"
    plane.mkdir(parents=True)
    (plane / RETIRED_LOCAL_MARKER).write_text("retired\n", encoding="utf-8")
    return tmp_path


def _entry(*, status: str = "fresh", mem: float = 20.0, disk: float = 40.0, cpu: int = 4, load1: float = 0.2) -> dict:
    return {
        "status": status,
        "cpu_count": cpu,
        "loadavg": [load1, 0.1, 0.1],
        "mem": {"pct": mem},
        "disk": {"pct": disk},
        "occupants": [],
    }


def _payload(**hosts: dict) -> dict:
    shaped = {}
    for host_id, entry in hosts.items():
        row = dict(entry)
        row["host_id"] = host_id
        shaped[host_id] = row
    return {"schema": "monitor-occupancy.v1", "hosts": shaped}


def test_build_remote_command_prefixes_path_and_cds() -> None:
    remote = jh.build_remote_command(
        [".venv/bin/python", "scripts/delegate.py", "dispatch", "--agent", "kimi"],
        remote_repo="/remote/repo",
    )
    assert 'export PATH="$HOME/.local/bin:$HOME/.opencode/bin:$PATH"' in remote
    assert "cd /remote/repo &&" in remote


def test_build_ssh_argv_is_batchmode() -> None:
    argv = jh.build_ssh_argv("job-alias", "true")
    assert argv[:5] == ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=12"]
    assert argv[5] == "job-alias"


def test_source_has_no_baked_ops_home_defaults() -> None:
    text = Path(jh.__file__).read_text(encoding="utf-8")
    assert "/home/ops" not in text


def test_fails_closed_when_env_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(jh.ENV_HOST, raising=False)
    monkeypatch.delenv(jh.ENV_HOST_FALLBACK, raising=False)
    monkeypatch.delenv(jh.ENV_REPO, raising=False)
    monkeypatch.delenv(jh.ENV_TEACHER_HOST, raising=False)
    monkeypatch.delenv(jh.ENV_TEACHER_REPO, raising=False)
    monkeypatch.delenv(jh.ENV_DISPATCH_SSH, raising=False)
    with pytest.raises(ValueError, match="is required"):
        jh.job_dispatch_host()
    with pytest.raises(ValueError, match="is required"):
        jh.job_dispatch_repo()
    with pytest.raises(ValueError, match="is required"):
        jh.ssh_alias_for_host_id("host-job")
    with pytest.raises(ValueError, match="is required"):
        jh.ssh_alias_for_host_id("host-teacher")
    with pytest.raises(ValueError, match="is required"):
        jh.repo_for_host_id("host-teacher")


def test_no_marker_stays_notebook(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(jh.ENV_ALLOW_NOTEBOOK, raising=False)
    occupancy = _payload(**{"host-job": _entry(), "host-teacher": _entry(disk=20.0)})
    placement, reason, host_id = jh.decide_dispatch_placement(repo_root=tmp_path, occupancy=occupancy)
    assert (placement, reason, host_id) == ("notebook", "no_retire_marker", None)


def test_picks_teacher_when_it_has_more_headroom(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(jh.ENV_ALLOW_NOTEBOOK, raising=False)
    root = _marker_root(tmp_path)
    occupancy = _payload(
        **{
            "host-job": _entry(mem=20.0, disk=49.0, load1=0.2),
            "host-teacher": _entry(mem=20.0, disk=24.0, load1=0.1),
        }
    )
    placement, reason, host_id = jh.decide_dispatch_placement(repo_root=root, occupancy=occupancy)
    assert (placement, reason, host_id) == ("vps", "available", "host-teacher")


def test_job_full_uses_teacher(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(jh.ENV_ALLOW_NOTEBOOK, raising=False)
    root = _marker_root(tmp_path)
    occupancy = _payload(
        **{
            "host-job": _entry(mem=90.0, disk=40.0),
            "host-teacher": _entry(mem=20.0, disk=24.0),
        }
    )
    assert jh.decide_dispatch_placement(repo_root=root, occupancy=occupancy) == (
        "vps",
        "available",
        "host-teacher",
    )


def test_teacher_full_uses_job(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(jh.ENV_ALLOW_NOTEBOOK, raising=False)
    root = _marker_root(tmp_path)
    occupancy = _payload(
        **{
            "host-job": _entry(mem=20.0, disk=40.0),
            "host-teacher": _entry(mem=99.0, disk=99.0),
        }
    )
    assert jh.decide_dispatch_placement(repo_root=root, occupancy=occupancy) == (
        "vps",
        "available",
        "host-job",
    )


def test_both_full_or_down_falls_back_to_notebook(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(jh.ENV_ALLOW_NOTEBOOK, raising=False)
    root = _marker_root(tmp_path)
    both_full = _payload(**{"host-job": _entry(mem=90.0), "host-teacher": _entry(disk=90.0)})
    assert jh.decide_dispatch_placement(repo_root=root, occupancy=both_full) == ("notebook", "full", None)
    both_down = _payload(
        **{
            "host-job": _entry(status="unavailable"),
            "host-teacher": _entry(status="unavailable"),
        }
    )
    assert jh.decide_dispatch_placement(repo_root=root, occupancy=both_down) == (
        "notebook",
        "unavailable",
        None,
    )
    assert jh.decide_dispatch_placement(repo_root=root, occupancy=None) == ("notebook", "unavailable", None)


def test_allow_env_bypasses_block(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(jh.ENV_ALLOW_NOTEBOOK, "1")
    root = _marker_root(tmp_path)
    occupancy = _payload(**{"host-job": _entry(), "host-teacher": _entry(disk=10.0)})
    assert jh.decide_dispatch_placement(repo_root=root, occupancy=occupancy) == (
        "notebook",
        "allow_env",
        None,
    )


def test_ssh_alias_for_teacher_and_job(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(jh.ENV_DISPATCH_SSH, "host-job=job-alias,host-teacher=teacher-alias")
    assert jh.ssh_alias_for_host_id("host-teacher") == "teacher-alias"
    assert jh.ssh_alias_for_host_id("host-job") == "job-alias"
    monkeypatch.delenv(jh.ENV_DISPATCH_SSH, raising=False)
    monkeypatch.setenv(jh.ENV_TEACHER_HOST, "teacher-from-env")
    monkeypatch.setenv(jh.ENV_HOST, "job-from-env")
    assert jh.ssh_alias_for_host_id("host-teacher") == "teacher-from-env"
    assert jh.ssh_alias_for_host_id("host-job") == "job-from-env"


def test_main_uses_ssh_stub(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    args_file = tmp_path / "ssh.args"
    fake_ssh = fake_bin / "ssh"
    fake_ssh.write_text(
        "#!/usr/bin/env bash\n"
        f'printf "%s\\n" "$@" > {args_file}\n'
        f'cat > {args_file}.stdin\n'
        "exit 0\n",
        encoding="utf-8",
    )
    fake_ssh.chmod(0o755)
    monkeypatch.setenv("PATH", f"{fake_bin}:/usr/bin:/bin")
    monkeypatch.setenv(jh.ENV_TEACHER_HOST, "teacher-alias")
    monkeypatch.setenv(jh.ENV_TEACHER_REPO, "/remote/repo")
    rc = jh.main(
        ["--host-id", "host-teacher", "--", ".venv/bin/python", "scripts/delegate.py", "dispatch"]
    )
    assert rc == 0
    recorded = args_file.read_text(encoding="utf-8")
    script = (tmp_path / "ssh.args.stdin").read_text(encoding="utf-8")
    assert "BatchMode=yes" in recorded
    assert "teacher-alias" in recorded
    assert "bash -s" in recorded
    assert "cd /remote/repo" in script
    assert "scripts/delegate.py" in script
    assert f"export {jh.ENV_ALLOW_NOTEBOOK}=1" in script


def test_main_dispatch_preserves_session_initiator(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    args_file = tmp_path / "ssh.args"
    fake_ssh = fake_bin / "ssh"
    fake_ssh.write_text(
        "#!/usr/bin/env bash\n"
        f'printf "%s\\n" "$@" > {args_file}\n'
        f"cat > {args_file}.stdin\n"
        "exit 0\n",
        encoding="utf-8",
    )
    fake_ssh.chmod(0o755)
    monkeypatch.setenv("PATH", f"{fake_bin}:/usr/bin:/bin")
    monkeypatch.setenv(jh.ENV_HOST, "job-alias")
    monkeypatch.setenv(jh.ENV_REPO, "/remote/repo")
    monkeypatch.setenv("SESSION_HANDOFF_AGENT", "cursor")
    rc = jh.main(
        [
            "--host-id",
            "host-job",
            "--",
            ".venv/bin/python",
            "scripts/delegate.py",
            "dispatch",
            "--agent",
            "codex",
            "--task-id",
            "cf",
        ]
    )
    assert rc == 0
    script = (tmp_path / "ssh.args.stdin").read_text(encoding="utf-8")
    assert "--initiator" in script
    assert "cursor" in script
    assert f"export {jh.ENV_RUNTIME_INITIATOR}=" in script
    assert f"export {jh.ENV_RUNTIME_INITIATOR_SOURCE}=" in script


def test_main_dispatch_copies_local_prompt_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    args_file = tmp_path / "ssh.args"
    fake_ssh = fake_bin / "ssh"
    fake_ssh.write_text(
        "#!/usr/bin/env bash\n"
        f'printf "%s\\n" "$@" > {args_file}\n'
        f'cat > {args_file}.stdin\n'
        "exit 0\n",
        encoding="utf-8",
    )
    fake_ssh.chmod(0o755)
    prompt = tmp_path / "brief.md"
    prompt.write_text("keep curriculum/l2-uk-en in the worktree\n", encoding="utf-8")
    monkeypatch.setenv("PATH", f"{fake_bin}:/usr/bin:/bin")
    monkeypatch.setenv(jh.ENV_HOST, "job-alias")
    monkeypatch.setenv(jh.ENV_REPO, "/remote/repo")
    rc = jh.main(
        [
            "--host-id",
            "host-job",
            "--",
            ".venv/bin/python",
            "scripts/delegate.py",
            "dispatch",
            "--agent",
            "codex",
            "--task-id",
            "cf",
            "--prompt-file",
            str(prompt),
        ]
    )
    assert rc == 0
    recorded = args_file.read_text(encoding="utf-8")
    script = (tmp_path / "ssh.args.stdin").read_text(encoding="utf-8")
    assert str(prompt) not in recorded
    assert "keep curriculum/l2-uk-en in the worktree" not in recorded
    assert "--prompt-file" in script
    assert "/tmp/lu-dispatch-prompt.XXXXXX" in script
    assert "$LU_DISPATCH_PROMPT_0" in script
    assert f"export {jh.ENV_ALLOW_NOTEBOOK}=1" in script


def test_main_help_contract() -> None:
    help_text = jh.build_parser().format_help()
    assert "Execute a command on a VPS worker checkout over BatchMode SSH." in help_text
    assert "do not use it to start a second Monitor" in help_text
    assert "Examples:" in help_text
    assert "Outputs:" in help_text
    assert "Exit codes:" in help_text
    assert "Related:" in help_text
    assert "--prompt-file" in help_text
    assert "Issue: #7062" in help_text


def test_forward_dispatch_sets_allow_notebook(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    args_file = tmp_path / "ssh.args"
    fake_ssh = fake_bin / "ssh"
    fake_ssh.write_text(
        "#!/usr/bin/env bash\n"
        f'printf "%s\\n" "$@" > {args_file}\n'
        f'cat > {args_file}.stdin\n'
        "exit 0\n",
        encoding="utf-8",
    )
    fake_ssh.chmod(0o755)
    monkeypatch.setenv("PATH", f"{fake_bin}:/usr/bin:/bin")
    monkeypatch.setenv(jh.ENV_HOST, "job-alias")
    monkeypatch.setenv(jh.ENV_REPO, "/remote/repo")
    rc = jh.forward_dispatch(
        host_id="host-job",
        argv=["scripts/delegate.py", "dispatch", "--agent", "agy", "--task-id", "smoke"],
    )
    assert rc == 0
    recorded = args_file.read_text(encoding="utf-8")
    script = (tmp_path / "ssh.args.stdin").read_text(encoding="utf-8")
    assert "BatchMode=yes" in recorded
    assert "job-alias" in recorded
    assert "bash -s" in recorded
    assert f"export {jh.ENV_ALLOW_NOTEBOOK}=1" in script
    assert "dispatch" in script
    assert "--agent" in script


def test_forward_dispatch_preserves_initiator(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    args_file = tmp_path / "ssh.args"
    fake_ssh = fake_bin / "ssh"
    fake_ssh.write_text(
        "#!/usr/bin/env bash\n"
        f'printf "%s\\n" "$@" > {args_file}\n'
        f'cat > {args_file}.stdin\n'
        "exit 0\n",
        encoding="utf-8",
    )
    fake_ssh.chmod(0o755)
    monkeypatch.setenv("PATH", f"{fake_bin}:/usr/bin:/bin")
    monkeypatch.setenv(jh.ENV_HOST, "job-alias")
    monkeypatch.setenv(jh.ENV_REPO, "/remote/repo")
    rc = jh.forward_dispatch(
        host_id="host-job",
        argv=["scripts/delegate.py", "dispatch", "--agent", "codex", "--task-id", "cf"],
        initiator="cursor/job-host-dispatch",
        initiator_source="session_env",
    )
    assert rc == 0
    recorded = args_file.read_text(encoding="utf-8")
    script = (tmp_path / "ssh.args.stdin").read_text(encoding="utf-8")
    assert "--initiator" in script
    assert "cursor/job-host-dispatch" in script
    assert f"export {jh.ENV_RUNTIME_INITIATOR}=" in script
    assert f"export {jh.ENV_RUNTIME_INITIATOR_SOURCE}=" in script
    assert "cursor/job-host-dispatch" not in recorded


def test_forward_dispatch_inlines_prompt_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    args_file = tmp_path / "ssh.args"
    fake_ssh = fake_bin / "ssh"
    fake_ssh.write_text(
        "#!/usr/bin/env bash\n"
        f'printf "%s\\n" "$@" > {args_file}\n'
        f'cat > {args_file}.stdin\n'
        "exit 0\n",
        encoding="utf-8",
    )
    fake_ssh.chmod(0o755)
    prompt = tmp_path / "brief.md"
    prompt.write_text("keep curriculum/l2-uk-en in the worktree\n", encoding="utf-8")
    monkeypatch.setenv("PATH", f"{fake_bin}:/usr/bin:/bin")
    monkeypatch.setenv(jh.ENV_HOST, "job-alias")
    monkeypatch.setenv(jh.ENV_REPO, "/remote/repo")
    rc = jh.forward_dispatch(
        host_id="host-job",
        argv=[
            "scripts/delegate.py",
            "dispatch",
            "--agent",
            "codex",
            "--task-id",
            "cf",
            "--prompt-file",
            str(prompt),
        ],
    )
    assert rc == 0
    recorded = args_file.read_text(encoding="utf-8")
    script = (tmp_path / "ssh.args.stdin").read_text(encoding="utf-8")
    assert str(prompt) not in recorded
    assert "keep curriculum/l2-uk-en in the worktree" not in recorded
    assert "--prompt-file" in script
    assert "/tmp/lu-dispatch-prompt.XXXXXX" in script
    assert "$LU_DISPATCH_PROMPT_0" in script
    assert "\n--prompt\n-\n" not in script
    assert "keep curriculum/l2-uk-en in the worktree" not in script


def test_forward_dispatch_rewrites_prompt_dash(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    args_file = tmp_path / "ssh.args"
    fake_ssh = fake_bin / "ssh"
    fake_ssh.write_text(
        "#!/usr/bin/env bash\n"
        f'printf "%s\\n" "$@" > {args_file}\n'
        f'cat > {args_file}.stdin\n'
        "exit 0\n",
        encoding="utf-8",
    )
    fake_ssh.chmod(0o755)
    monkeypatch.setenv("PATH", f"{fake_bin}:/usr/bin:/bin")
    monkeypatch.setenv(jh.ENV_HOST, "job-alias")
    monkeypatch.setenv(jh.ENV_REPO, "/remote/repo")
    class _Stdin:
        buffer = io.BytesIO(b"touch wiki/pages.md\n")

    monkeypatch.setattr(jh.sys, "stdin", _Stdin())
    rc = jh.forward_dispatch(
        host_id="host-job",
        argv=[
            "scripts/delegate.py",
            "dispatch",
            "--agent",
            "codex",
            "--task-id",
            "cf",
            "--prompt",
            "-",
        ],
    )
    assert rc == 0
    recorded = args_file.read_text(encoding="utf-8")
    script = (tmp_path / "ssh.args.stdin").read_text(encoding="utf-8")
    assert "--prompt-file" in script
    assert "/tmp/lu-dispatch-prompt.XXXXXX" in script
    assert "$LU_DISPATCH_PROMPT_0" in script
    assert "\n--prompt\n-\n" not in script
    assert "touch wiki/pages.md" not in recorded


def test_forward_dispatch_copies_lifecycle_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    args_file = tmp_path / "ssh.args"
    fake_ssh = fake_bin / "ssh"
    fake_ssh.write_text(
        "#!/usr/bin/env bash\n"
        f'printf "%s\\n" "$@" > {args_file}\n'
        f'cat > {args_file}.stdin\n'
        "exit 0\n",
        encoding="utf-8",
    )
    fake_ssh.chmod(0o755)
    ledger = tmp_path / "task-lifecycle.json"
    ledger.write_text('{"schema":"task-lifecycle.v1","task_id":"cf"}\n', encoding="utf-8")
    monkeypatch.setenv("PATH", f"{fake_bin}:/usr/bin:/bin")
    monkeypatch.setenv(jh.ENV_HOST, "job-alias")
    monkeypatch.setenv(jh.ENV_REPO, "/remote/repo")
    rc = jh.forward_dispatch(
        host_id="host-job",
        argv=[
            "scripts/delegate.py",
            "dispatch",
            "--agent",
            "codex",
            "--task-id",
            "cf",
            "--lifecycle-file",
            str(ledger),
        ],
    )
    assert rc == 0
    recorded = args_file.read_text(encoding="utf-8")
    script = (tmp_path / "ssh.args.stdin").read_text(encoding="utf-8")
    assert str(ledger) not in recorded
    assert "--lifecycle-file" in script
    assert "/tmp/lu-dispatch-lifecycle.XXXXXX" in script
    assert "$LU_DISPATCH_LIFECYCLE_0" in script
    assert "base64 -d >" in script


def test_forward_dispatch_copies_output_schema(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    args_file = tmp_path / "ssh.args"
    fake_ssh = fake_bin / "ssh"
    fake_ssh.write_text(
        "#!/usr/bin/env bash\n"
        f'printf "%s\\n" "$@" > {args_file}\n'
        f'cat > {args_file}.stdin\n'
        "exit 0\n",
        encoding="utf-8",
    )
    fake_ssh.chmod(0o755)
    schema = tmp_path / "review.schema.json"
    schema.write_text('{"type":"object"}\n', encoding="utf-8")
    monkeypatch.setenv("PATH", f"{fake_bin}:/usr/bin:/bin")
    monkeypatch.setenv(jh.ENV_HOST, "job-alias")
    monkeypatch.setenv(jh.ENV_REPO, "/remote/repo")
    rc = jh.forward_dispatch(
        host_id="host-job",
        argv=[
            "scripts/delegate.py",
            "dispatch",
            "--agent",
            "codex",
            "--task-id",
            "cf",
            "--output-schema",
            str(schema),
        ],
    )
    assert rc == 0
    recorded = args_file.read_text(encoding="utf-8")
    script = (tmp_path / "ssh.args.stdin").read_text(encoding="utf-8")
    assert str(schema) not in recorded
    assert "--output-schema" in script
    assert "/tmp/lu-dispatch-output-schema.XXXXXX" in script
    assert "$LU_DISPATCH_OUTPUT_SCHEMA_0" in script
    assert "base64 -d >" in script


def test_forward_dispatch_rejects_notebook_cwd(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(jh.ENV_HOST, "job-alias")
    monkeypatch.setenv(jh.ENV_REPO, "/remote/repo")
    with pytest.raises(ValueError, match="--cwd"):
        jh.forward_dispatch(
            host_id="host-job",
            argv=[
                "scripts/delegate.py",
                "dispatch",
                "--agent",
                "codex",
                "--task-id",
                "cf",
                "--cwd",
                str(tmp_path),
            ],
        )


def test_forward_dispatch_strips_notebook_worktree_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    args_file = tmp_path / "ssh.args"
    fake_ssh = fake_bin / "ssh"
    fake_ssh.write_text(
        "#!/usr/bin/env bash\n"
        f'printf "%s\\n" "$@" > {args_file}\n'
        f'cat > {args_file}.stdin\n'
        "exit 0\n",
        encoding="utf-8",
    )
    fake_ssh.chmod(0o755)
    monkeypatch.setenv("PATH", f"{fake_bin}:/usr/bin:/bin")
    monkeypatch.setenv(jh.ENV_HOST, "job-alias")
    monkeypatch.setenv(jh.ENV_REPO, "/remote/repo")
    local_wt = tmp_path / "wt"
    local_wt.mkdir()
    rc = jh.forward_dispatch(
        host_id="host-job",
        argv=[
            "scripts/delegate.py",
            "dispatch",
            "--agent",
            "codex",
            "--task-id",
            "cf",
            "--worktree",
            str(local_wt),
        ],
    )
    assert rc == 0
    recorded = args_file.read_text(encoding="utf-8")
    script = (tmp_path / "ssh.args.stdin").read_text(encoding="utf-8")
    assert str(local_wt) not in recorded
    assert "--worktree" in script


def test_forward_dispatch_missing_ssh_is_transport_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    empty = tmp_path / "empty"
    empty.mkdir()
    monkeypatch.setenv("PATH", str(empty))
    monkeypatch.setenv(jh.ENV_HOST, "job-alias")
    monkeypatch.setenv(jh.ENV_REPO, "/remote/repo")
    with pytest.raises(jh.SshTransportError):
        jh.forward_dispatch(
            host_id="host-job",
            argv=["scripts/delegate.py", "dispatch", "--agent", "codex", "--task-id", "cf"],
        )


def test_forward_dispatch_unexecutable_ssh_is_transport_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    fake_ssh = fake_bin / "ssh"
    fake_ssh.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    fake_ssh.chmod(0o644)
    monkeypatch.setenv("PATH", str(fake_bin))
    monkeypatch.setenv(jh.ENV_HOST, "job-alias")
    monkeypatch.setenv(jh.ENV_REPO, "/remote/repo")
    with pytest.raises(jh.SshTransportError):
        jh.forward_dispatch(
            host_id="host-job",
            argv=["scripts/delegate.py", "dispatch", "--agent", "codex", "--task-id", "cf"],
        )


def test_notebook_fallback_only_on_transport_failure() -> None:
    assert jh.notebook_fallback_after_forward(None, error=ValueError("missing host")) is False
    assert jh.notebook_fallback_after_forward(None, error=FileNotFoundError("/tmp/local.json")) is False
    assert jh.notebook_fallback_after_forward(None, error=FileNotFoundError("/tmp/ssh")) is False
    assert jh.notebook_fallback_after_forward(None, error=FileNotFoundError("ssh")) is False
    assert jh.notebook_fallback_after_forward(None, error=jh.SshTransportError("ssh missing")) is True
    assert jh.notebook_fallback_after_forward(None, error=jh.SshTransportError("Permission denied")) is True
    assert jh.notebook_fallback_after_forward(255) is True
    assert jh.notebook_fallback_after_forward(0) is False
    assert jh.notebook_fallback_after_forward(2) is False


@pytest.mark.parametrize(
    ("mode", "expected_rc"),
    [("success", 0), ("failure", 7), ("signal", 143)],
)
def test_remote_payload_script_cleans_private_files_on_exit_failure_and_signal(
    tmp_path: Path, mode: str, expected_rc: int
) -> None:
    """The remote trap must remove each 0600 payload file in every exit path."""
    remote_python = tmp_path / ".venv" / "bin" / "python"
    remote_python.parent.mkdir(parents=True)
    remote_python.symlink_to(sys.executable)
    remote_delegate = tmp_path / "scripts" / "delegate.py"
    remote_delegate.parent.mkdir()
    observed_path = tmp_path / "payload-path"
    remote_delegate.write_text(
        "import os\n"
        "import signal\n"
        "import stat\n"
        "import sys\n"
        "from pathlib import Path\n"
        "payload = Path(sys.argv[sys.argv.index('--prompt-file') + 1])\n"
        "mode = stat.S_IMODE(payload.stat().st_mode)\n"
        "Path(os.environ['LU_TEST_PAYLOAD_PATH']).write_text(f'{payload}\\n{mode:o}', encoding='utf-8')\n"
        "if os.environ['LU_TEST_PAYLOAD_MODE'] == 'signal':\n"
        "    os.kill(os.getppid(), signal.SIGTERM)\n"
        "sys.exit(7 if os.environ['LU_TEST_PAYLOAD_MODE'] == 'failure' else 0)\n",
        encoding="utf-8",
    )
    prompt = tmp_path / "brief.md"
    prompt.write_text("private body\n", encoding="utf-8")
    rest, payloads = jh.materialize_local_dispatch_argv(
        ["dispatch", "--prompt-file", str(prompt)]
    )
    script = jh._build_remote_dispatch_script(
        argv=rest,
        remote_repo=str(tmp_path),
        payloads=payloads,
        extra_exports=[
            f"export LU_TEST_PAYLOAD_PATH={observed_path}",
            f"export LU_TEST_PAYLOAD_MODE={mode}",
        ],
    )
    rendered = script.decode("utf-8")
    assert "umask 077" in rendered
    assert "mktemp /tmp/lu-dispatch-prompt.XXXXXX" in rendered
    assert "trap _on_exit EXIT" in rendered
    assert "trap '_on_signal 15' TERM" in rendered
    assert "private body" not in rendered
    completed = subprocess.run(
        ["bash", "-s"],
        input=script,
        check=False,
        capture_output=True,
        timeout=30,
    )
    assert completed.returncode == expected_rc, completed.stderr.decode("utf-8")
    payload_name, payload_mode = observed_path.read_text(encoding="utf-8").splitlines()
    payload_path = Path(payload_name)
    assert int(payload_mode, 8) & 0o077 == 0
    assert not payload_path.exists()


def test_main_missing_ssh_dispatch_returns_255(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    empty = tmp_path / "empty"
    empty.mkdir()
    monkeypatch.setenv("PATH", str(empty))
    monkeypatch.setenv(jh.ENV_HOST, "job-alias")
    monkeypatch.setenv(jh.ENV_REPO, "/remote/repo")
    rc = jh.main(
        [
            "--host-id",
            "host-job",
            "--",
            ".venv/bin/python",
            "scripts/delegate.py",
            "dispatch",
            "--agent",
            "codex",
            "--task-id",
            "cf",
        ]
    )
    assert rc == 255


def test_main_missing_ssh_plain_command_returns_255(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    empty = tmp_path / "empty"
    empty.mkdir()
    monkeypatch.setenv("PATH", str(empty))
    monkeypatch.setenv(jh.ENV_HOST, "job-alias")
    monkeypatch.setenv(jh.ENV_REPO, "/remote/repo")
    rc = jh.main(["--host-id", "host-job", "--", "true"])
    assert rc == 255
