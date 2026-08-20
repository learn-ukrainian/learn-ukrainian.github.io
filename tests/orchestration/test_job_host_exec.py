"""VPS worker exec + dual-host occupancy placement."""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.fleet_comms.paths import RETIRED_LOCAL_MARKER
from scripts.orchestration import job_host_exec as jh


@pytest.fixture(autouse=True)
def _clear_occupancy_pin(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(jh.ENV_OCCUPANCY_HOST, raising=False)


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


def test_defaults_when_env_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(jh.ENV_HOST, raising=False)
    monkeypatch.delenv(jh.ENV_HOST_FALLBACK, raising=False)
    monkeypatch.delenv(jh.ENV_REPO, raising=False)
    monkeypatch.delenv(jh.ENV_TEACHER_HOST, raising=False)
    monkeypatch.delenv(jh.ENV_TEACHER_REPO, raising=False)
    monkeypatch.delenv(jh.ENV_DISPATCH_SSH, raising=False)
    assert jh.job_dispatch_host() == jh.DEFAULT_JOB_SSH
    assert jh.job_dispatch_repo() == jh.DEFAULT_JOB_REPO
    assert jh.ssh_alias_for_host_id("host-job") == jh.DEFAULT_JOB_SSH
    assert jh.ssh_alias_for_host_id("host-teacher") == jh.DEFAULT_TEACHER_SSH
    assert jh.repo_for_host_id("host-teacher") == jh.DEFAULT_TEACHER_REPO


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
    blocked = jh.notebook_dispatch_blocked(repo_root=root, occupancy=occupancy)
    assert blocked is not None
    assert "host-teacher" in blocked
    assert "every VPS worker host" in blocked


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
    assert jh.notebook_dispatch_blocked(repo_root=root, occupancy=None) is None


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
    assert "BatchMode=yes" in recorded
    assert "teacher-alias" in recorded
    assert "cd /remote/repo" in recorded
    assert "scripts/delegate.py" in recorded


def test_forward_dispatch_sets_allow_notebook(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    args_file = tmp_path / "ssh.args"
    fake_ssh = fake_bin / "ssh"
    fake_ssh.write_text(
        "#!/usr/bin/env bash\n"
        f'printf "%s\\n" "$@" > {args_file}\n'
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
    assert "BatchMode=yes" in recorded
    assert "job-alias" in recorded
    assert f"export {jh.ENV_ALLOW_NOTEBOOK}=1" in recorded
    assert "dispatch" in recorded
    assert "--agent" in recorded


def test_forward_dispatch_inlines_prompt_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    args_file = tmp_path / "ssh.args"
    stdin_file = tmp_path / "ssh.stdin"
    fake_ssh = fake_bin / "ssh"
    fake_ssh.write_text(
        "#!/usr/bin/env bash\n"
        f'printf "%s\\n" "$@" > {args_file}\n'
        f"cat > {stdin_file}\n"
        "exit 0\n",
        encoding="utf-8",
    )
    fake_ssh.chmod(0o755)
    prompt = tmp_path / "brief.md"
    prompt.write_text("review PR 7070 exact head\n", encoding="utf-8")
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
    assert "--prompt-file" not in recorded
    assert "--prompt" in recorded
    assert stdin_file.read_text(encoding="utf-8") == "review PR 7070 exact head\n"


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
    assert str(ledger) not in recorded
    assert "--lifecycle-file" in recorded
    assert "/tmp/lu-dispatch-lifecycle-" in recorded
    assert "base64 -d >" in recorded


def test_notebook_fallback_only_on_transport_failure() -> None:
    assert jh.notebook_fallback_after_forward(None, error=ValueError("missing host")) is False
    assert jh.notebook_fallback_after_forward(None, error=FileNotFoundError("/tmp/local.json")) is False
    assert jh.notebook_fallback_after_forward(None, error=FileNotFoundError("ssh")) is True
    assert jh.notebook_fallback_after_forward(255) is True
    assert jh.notebook_fallback_after_forward(0) is False
    assert jh.notebook_fallback_after_forward(2) is False
