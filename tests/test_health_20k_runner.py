"""Black-box checks for the fail-closed Atlas 20k runner health probe."""

import os
import subprocess
from pathlib import Path

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
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    fake_ssh = fake_bin / "ssh"
    fake_ssh.write_text("#!/usr/bin/env bash\nexit 1\n", encoding="utf-8")
    fake_ssh.chmod(0o755)

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
