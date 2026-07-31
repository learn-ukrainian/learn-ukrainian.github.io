"""Black-box checks for the fail-closed Atlas 20k runner health probe."""

import os
import subprocess
from pathlib import Path

from scripts.lexicon.runner.durable_mirror import snapshot, write_restic_gate_receipt

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts/lexicon/runner/health_20k_runner.sh"


def _run_probe(*, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(SCRIPT)],
        cwd=REPO,
        env={**os.environ, **env},
        capture_output=True,
        text=True,
        check=False,
    )


def _stub_ssh(tmp_path: Path, *, exit_code: int = 0) -> Path:
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    fake_ssh = fake_bin / "ssh"
    fake_ssh.write_text(
        "#!/usr/bin/env bash\n"
        'if [[ -n "${SSH_ARGS_FILE:-}" ]]; then\n'
        '  printf "%s\\n" "$@" > "$SSH_ARGS_FILE"\n'
        "fi\n"
        f"exit {exit_code}\n",
        encoding="utf-8",
    )
    fake_ssh.chmod(0o755)
    return fake_bin


def _make_durable_mirror(tmp_path: Path) -> Path:
    source = tmp_path / "runner-work"
    source.mkdir()
    (source / "ledger.sqlite").write_bytes(b"ledger")
    mirror = tmp_path / "runner-mirror" / "run-20k"
    snapshot(str(source), mirror, allow_live=True)
    write_restic_gate_receipt(
        mirror.parent,
        restic_snapshot_id="a" * 64,
        host="test-host",
        git_sha="b" * 40,
    )
    return mirror


def test_health_probe_requires_runner_host() -> None:
    result = _run_probe(env={"ATLAS_RUNNER_HOST": ""})

    assert result.returncode == 2
    assert "ATLAS_RUNNER_HOST is required; see #6077 AC-HOST." in result.stderr
    assert result.stdout.splitlines() == [
        "host_set=false",
        "mirror_present=false",
        "mirror_require_ok=false",
        "mirror_age_hint=max_age_hours=24",
    ]


def test_health_probe_fails_closed_when_ssh_check_fails(tmp_path: Path) -> None:
    fake_bin = _stub_ssh(tmp_path, exit_code=1)

    result = _run_probe(
        env={
            "ATLAS_RUNNER_HOST": "ops@runner.example",
            "PATH": f"{fake_bin}:{os.environ['PATH']}",
        }
    )

    assert result.returncode == 2
    assert "runner SSH work-dir check failed" in result.stderr
    assert result.stdout.splitlines() == [
        "host_set=true",
        "mirror_present=false",
        "mirror_require_ok=false",
        "mirror_age_hint=max_age_hours=24",
    ]


def test_health_probe_fails_closed_without_local_mirror(tmp_path: Path) -> None:
    fake_bin = _stub_ssh(tmp_path)
    missing_mirror = tmp_path / "missing-mirror"

    result = _run_probe(
        env={
            "ATLAS_RUNNER_HOST": "ops@runner.example",
            "ATLAS_MIRROR_DIR": str(missing_mirror),
            "PATH": f"{fake_bin}:{os.environ['PATH']}",
        }
    )

    assert result.returncode == 2
    assert f"no local mirror at {missing_mirror}" in result.stderr
    assert result.stdout.splitlines() == [
        "host_set=true",
        "mirror_present=false",
        "mirror_require_ok=false",
        "mirror_age_hint=max_age_hours=24",
    ]


def test_health_probe_fails_closed_when_mirror_is_not_durable(tmp_path: Path) -> None:
    fake_bin = _stub_ssh(tmp_path)
    mirror = tmp_path / "invalid-mirror"
    mirror.mkdir()

    result = _run_probe(
        env={
            "ATLAS_RUNNER_HOST": "ops@runner.example",
            "ATLAS_MIRROR_DIR": str(mirror),
            "PATH": f"{fake_bin}:{os.environ['PATH']}",
        }
    )

    assert result.returncode == 2
    assert "runner durable-mirror check failed" in result.stderr
    assert result.stdout.splitlines() == [
        "host_set=true",
        "mirror_present=true",
        "mirror_require_ok=false",
        "mirror_age_hint=max_age_hours=24",
    ]


def test_health_probe_succeeds_with_reachable_runner_and_durable_mirror(tmp_path: Path) -> None:
    fake_bin = _stub_ssh(tmp_path)
    mirror = _make_durable_mirror(tmp_path)
    ssh_args = tmp_path / "ssh-args"

    result = _run_probe(
        env={
            "ATLAS_RUNNER_HOST": "ops@runner.example",
            "ATLAS_MIRROR_DIR": str(mirror),
            "PATH": f"{fake_bin}:{os.environ['PATH']}",
            "SSH_ARGS_FILE": str(ssh_args),
        }
    )

    assert result.returncode == 0, result.stderr
    assert ssh_args.read_text(encoding="utf-8").splitlines()[:5] == [
        "-o",
        "BatchMode=yes",
        "-o",
        "ConnectTimeout=10",
        "--",
    ]
    assert result.stdout.splitlines()[0].startswith(f"durable: {mirror} (1 files, generated_at=")
    assert result.stdout.splitlines()[1:] == [
        "host_set=true",
        "mirror_present=true",
        "mirror_require_ok=true",
        "mirror_age_hint=max_age_hours=24",
    ]
