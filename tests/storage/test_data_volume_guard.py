"""Guarded service starts use mount identity, including the direct launcher path."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
UUID = "12345678-1234-1234-1234-123456789abc"
OTHER_UUID = "87654321-4321-4321-4321-cba987654321"


@pytest.fixture
def guarded_repo(tmp_path: Path) -> tuple[Path, Path, Path, dict[str, str]]:
    repo = tmp_path / "repo"
    storage = repo / "scripts" / "storage"
    storage.mkdir(parents=True)
    (repo / "data").mkdir()
    marker = tmp_path / "config" / "data-volume.uuid"
    marker.parent.mkdir()
    guard = storage / "data_volume_guard.sh"
    guard.write_text(
        (ROOT / "scripts/storage/data_volume_guard.sh")
        .read_text(encoding="utf-8")
        .replace("UUID_FILE=/etc/learn-ukrainian/data-volume.uuid", f"UUID_FILE={marker}"),
        encoding="utf-8",
    )
    services = repo / "services.sh"
    services.write_text((ROOT / "services.sh").read_text(encoding="utf-8"), encoding="utf-8")
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    findmnt = bin_dir / "findmnt"
    findmnt.write_text(
        "#!/usr/bin/env bash\n"
        'printf "%s\\n" "$*" >> "$FAKE_FINDMNT_CALLS"\n'
        '[[ "${FAKE_FINDMNT_EXIT:-0}" == 0 ]] || exit 1\n'
        'if [[ "${*: -1}" == / ]]; then\n'
        '  printf "%s %s\\n" "${FAKE_ROOT_UUID:-}" "${FAKE_ROOT_SOURCE:-/dev/root}"\n'
        '  exit 0\n'
        'fi\n'
        'printf "%s %s\\n" "${FAKE_FINDMNT_UUID:-}" "${FAKE_FINDMNT_SOURCE:-/dev/fake}"\n',
        encoding="utf-8",
    )
    findmnt.chmod(0o755)
    calls = tmp_path / "findmnt-calls"
    env = os.environ.copy()
    env.update(
        PATH=f"{bin_dir}:{env['PATH']}",
        FAKE_FINDMNT_CALLS=str(calls),
        FAKE_FINDMNT_UUID=UUID,
        FAKE_ROOT_UUID=OTHER_UUID,
        LU_SERVICES_ROLE="local",
    )
    return guard, services, marker, env


def run_guard(guard: Path, env: dict[str, str], *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["bash", str(guard), *args], env=env, text=True, capture_output=True)


def test_absent_uuid_file_is_noop(guarded_repo: tuple[Path, Path, Path, dict[str, str]]) -> None:
    guard, _, marker, env = guarded_repo
    result = run_guard(guard, env)
    assert result.returncode == 0
    assert not marker.exists()
    assert not Path(env["FAKE_FINDMNT_CALLS"]).exists()
    assert run_guard(guard, env, "--status").stdout == "data: root disk\n"


def test_unreadable_uuid_parent_refuses_start(
    guarded_repo: tuple[Path, Path, Path, dict[str, str]], tmp_path: Path
) -> None:
    guard, _, marker, env = guarded_repo
    marker.write_text(UUID + "\n", encoding="utf-8")
    marker.parent.chmod(0)
    try:
        result = run_guard(guard, env, "--", "touch", str(tmp_path / "started"))
        assert result.returncode == 78
        assert "cannot check UUID file" in result.stderr
        assert "Permission denied" in result.stderr
        assert not (tmp_path / "started").exists()
        assert not Path(env["FAKE_FINDMNT_CALLS"]).exists()
    finally:
        marker.parent.chmod(0o755)


def test_unreadable_uuid_file_refuses_start(
    guarded_repo: tuple[Path, Path, Path, dict[str, str]], tmp_path: Path
) -> None:
    guard, _, marker, env = guarded_repo
    marker.write_text(UUID + "\n", encoding="utf-8")
    marker.chmod(0)
    try:
        result = run_guard(guard, env, "--", "touch", str(tmp_path / "started"))
        assert result.returncode == 78
        assert "cannot read UUID file" in result.stderr
        assert not (tmp_path / "started").exists()
        assert not Path(env["FAKE_FINDMNT_CALLS"]).exists()
    finally:
        marker.chmod(0o644)


def test_dangling_uuid_symlink_refuses_start(
    guarded_repo: tuple[Path, Path, Path, dict[str, str]]
) -> None:
    guard, _, marker, env = guarded_repo
    marker.symlink_to(marker.parent / "missing")
    result = run_guard(guard, env)
    assert result.returncode == 78
    assert "cannot check UUID file" in result.stderr
    assert not Path(env["FAKE_FINDMNT_CALLS"]).exists()


def test_status_identifies_unexpected_volume(
    guarded_repo: tuple[Path, Path, Path, dict[str, str]]
) -> None:
    guard, _, marker, env = guarded_repo
    marker.write_text(UUID + "\n", encoding="utf-8")
    env.update(
        FAKE_FINDMNT_UUID=OTHER_UUID,
        FAKE_ROOT_UUID="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
    )
    assert run_guard(guard, env, "--status").stdout == (
        f"data: volume {OTHER_UUID} (expected {UUID})\n"
    )


def test_matching_uuid_executes_command(
    guarded_repo: tuple[Path, Path, Path, dict[str, str]], tmp_path: Path
) -> None:
    guard, _, marker, env = guarded_repo
    marker.write_text(UUID + "\n", encoding="utf-8")
    result = run_guard(guard, env, "--", sys.executable, "-c", "print('started')")
    assert result.returncode == 0, result.stderr
    assert result.stdout == "started\n"
    assert Path(env["FAKE_FINDMNT_CALLS"]).read_text().strip() == (
        f"-no UUID,SOURCE -T {guard.parents[2] / 'data'}"
    )
    assert run_guard(guard, env, "--status").stdout == f"data: volume {UUID}\n"


@pytest.mark.parametrize("actual,findmnt_exit", [(OTHER_UUID, "0"), (UUID, "1")])
def test_mismatch_or_unmounted_exits_78(
    guarded_repo: tuple[Path, Path, Path, dict[str, str]],
    actual: str,
    findmnt_exit: str,
) -> None:
    guard, _, marker, env = guarded_repo
    marker.write_text(UUID + "\n", encoding="utf-8")
    env.update(FAKE_FINDMNT_UUID=actual, FAKE_FINDMNT_EXIT=findmnt_exit)
    result = run_guard(guard, env)
    assert result.returncode == 78
    assert "not mounted from configured UUID" in result.stderr
    expected_status = "data: root disk\n" if findmnt_exit == "0" else "data: unknown\n"
    assert run_guard(guard, env, "--status").stdout == expected_status


@pytest.mark.parametrize("action", ["start", "restart", "fix"])
def test_services_refuses_mismatch_before_side_effects(
    guarded_repo: tuple[Path, Path, Path, dict[str, str]], action: str
) -> None:
    _, services, marker, env = guarded_repo
    marker.write_text(UUID + "\n", encoding="utf-8")
    env["FAKE_FINDMNT_UUID"] = OTHER_UUID
    result = subprocess.run(
        ["bash", str(services), action, "api"],
        env=env,
        text=True,
        capture_output=True,
    )
    assert result.returncode == 78
    assert "not mounted from configured UUID" in result.stderr
    assert not (services.parent / ".pids").exists()


def test_help_describes_modes(guarded_repo: tuple[Path, Path, Path, dict[str, str]]) -> None:
    guard, _, _, env = guarded_repo
    result = run_guard(guard, env, "--help")
    assert result.returncode == 0
    assert "Exit codes:" in result.stdout
    assert "--status" in result.stdout
