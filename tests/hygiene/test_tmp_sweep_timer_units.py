"""Daily temp-sweep user units and installer contract (#9737)."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.orchestration import install_tmp_sweep_timer as installer


def test_service_and_timer_contract() -> None:
    service = (installer.TEMPLATE_DIR / installer.UNITS[0]).read_text()
    timer = (installer.TEMPLATE_DIR / installer.UNITS[1]).read_text()
    assert "Type=oneshot" in service
    assert "WorkingDirectory=@REPO_ROOT@" in service
    starts = [line for line in service.splitlines() if line.startswith("ExecStart=")]
    assert starts == [
        "ExecStart=@REPO_ROOT@/.venv/bin/python -m scripts.hygiene.batch_state_retention",
        "ExecStart=@REPO_ROOT@/.venv/bin/python -m scripts.hygiene.tmp_sweep --unattributed-scratch --apply --summary",
    ]
    assert "PrivateTmp" not in service  # the sweep must see the real system temp area
    # Enforced in user managers (seccomp); PrivateNetwork= is accepted there but isolates nothing.
    assert "RestrictAddressFamilies=AF_UNIX" in service.splitlines()
    assert "IPAddressDeny=any" in service.splitlines()
    assert "OnCalendar=*-*-* 05:30:00 UTC" in timer
    assert "Persistent=true" in timer
    assert "Unit=learn-ukrainian-tmp-sweep.service" in timer
    assert "WantedBy=timers.target" in timer


def test_installer_check_apply_and_enable(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    primary = tmp_path / "primary"
    (primary / ".git").mkdir(parents=True)
    linked = tmp_path / "linked"
    linked.mkdir()
    (linked / ".git").write_text("gitdir: linked")
    unit_dir = tmp_path / "units"
    calls = []
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setattr(installer, "verify_units", lambda _rendered: None)
    monkeypatch.setattr(installer, "systemctl_user", lambda *args: calls.append(args))
    flags = ["--repo-root", str(primary), "--unit-dir", str(unit_dir)]
    assert installer.main([*flags, "--check"]) == 1
    assert installer.main([*flags, "--apply"]) == 0
    assert installer.main([*flags, "--check"]) == 0
    assert installer.main([*flags, "--apply", "--enable"]) == 0
    assert calls == [("daemon-reload",), ("daemon-reload",), ("enable", "--now", "learn-ukrainian-tmp-sweep.timer")]
    assert all((unit_dir / name).stat().st_mode & 0o777 == 0o600 for name in installer.UNITS)
    assert f"WorkingDirectory={primary.resolve()}" in (unit_dir / installer.UNITS[0]).read_text()
    for argv in (["--repo-root", str(linked), "--check"], [*flags, "--enable"], [*flags, "--check", "--apply"]):
        with pytest.raises(SystemExit) as exc:
            installer.main(argv)
        assert exc.value.code == 2, argv


def _installer_fixture(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> list[str]:
    primary = tmp_path / "primary"
    (primary / ".git").mkdir(parents=True)
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setattr(installer, "verify_units", lambda _rendered: None)
    monkeypatch.setattr(installer, "systemctl_user", lambda *args: None)
    return ["--repo-root", str(primary)]


@pytest.mark.parametrize("mode", ["--check", "--apply"])
@pytest.mark.parametrize("existing", [True, False])
def test_installer_refuses_unit_dir_beneath_a_symlinked_ancestor(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mode: str, existing: bool
) -> None:
    """``~/.config`` links elsewhere: the real unit directory behind it is never written or created."""
    flags = _installer_fixture(tmp_path, monkeypatch)
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    outside = tmp_path / "outside-config"
    outside.mkdir()
    if existing:
        (outside / "systemd" / "user").mkdir(parents=True)
    (home / ".config").symlink_to(outside, target_is_directory=True)
    unit_dir = home / ".config" / "systemd" / "user"
    before = sorted(str(path.relative_to(outside)) for path in outside.rglob("*"))
    with pytest.raises(installer.InstallError, match=r"symlinked path component .*\.config"):
        installer.main([*flags, "--unit-dir", str(unit_dir), mode])
    assert sorted(str(path.relative_to(outside)) for path in outside.rglob("*")) == before
    assert (home / ".config").is_symlink()


def test_installer_creates_missing_unit_dirs_without_links(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    flags = _installer_fixture(tmp_path, monkeypatch)
    unit_dir = tmp_path / ".config" / "systemd" / "user"
    assert installer.main([*flags, "--unit-dir", str(unit_dir), "--check"]) == 1
    assert not (tmp_path / ".config").exists()
    assert installer.main([*flags, "--unit-dir", str(unit_dir), "--apply"]) == 0
    assert sorted(path.name for path in unit_dir.iterdir()) == sorted(installer.UNITS)


@pytest.mark.parametrize("mode", ["--check", "--apply"])
def test_installer_refuses_symlinked_unit_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mode: str) -> None:
    flags = _installer_fixture(tmp_path, monkeypatch)
    unit_dir = tmp_path / "units"
    unit_dir.mkdir()
    outside = tmp_path / "outside.service"
    outside.write_text("outside content")
    os.chmod(outside, 0o400)
    (unit_dir / installer.UNITS[0]).symlink_to(outside)
    with pytest.raises(installer.InstallError, match="symlinked unit file"):
        installer.main([*flags, "--unit-dir", str(unit_dir), mode])
    assert outside.read_text() == "outside content" and outside.stat().st_mode & 0o777 == 0o400
    assert (unit_dir / installer.UNITS[0]).is_symlink()
    assert sorted(path.name for path in unit_dir.iterdir()) == [installer.UNITS[0]]


@pytest.mark.parametrize("mode", ["--check", "--apply"])
def test_installer_refuses_symlinked_unit_directory(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mode: str) -> None:
    flags = _installer_fixture(tmp_path, monkeypatch)
    outside = tmp_path / "outside-dir"
    outside.mkdir()
    unit_dir = tmp_path / "units"
    unit_dir.symlink_to(outside, target_is_directory=True)
    with pytest.raises(installer.InstallError, match="real directory"):
        installer.main([*flags, "--unit-dir", str(unit_dir), mode])
    assert list(outside.iterdir()) == []


def test_installer_replaces_unit_without_following_a_raced_link(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A link planted at the unit name after the check is replaced, never written through."""
    flags = _installer_fixture(tmp_path, monkeypatch)
    unit_dir = tmp_path / "units"
    unit_dir.mkdir()
    outside = tmp_path / "outside.service"
    outside.write_text("outside content")
    real_read = installer.read_unit

    def racing_read(dir_fd: int, name: str):
        result = real_read(dir_fd, name)
        os.symlink(outside, name, dir_fd=dir_fd)
        return result

    monkeypatch.setattr(installer, "read_unit", racing_read)
    assert installer.main([*flags, "--unit-dir", str(unit_dir), "--apply"]) == 0
    assert outside.read_text() == "outside content"
    for name in installer.UNITS:
        assert not (unit_dir / name).is_symlink() and (unit_dir / name).stat().st_mode & 0o777 == 0o600
    assert sorted(path.name for path in unit_dir.iterdir()) == sorted(installer.UNITS)


def test_help_names_project_interpreter_and_exit_codes(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        installer.main(["--help"])
    out = capsys.readouterr().out
    assert exc.value.code == 0 and "<project-python>" not in out
    assert ".venv/bin/python -m scripts.orchestration.install_tmp_sweep_timer --check" in out
    assert "2 = invalid usage" in out


def _systemd_analyze_usable(tmp_path: Path) -> str | None:
    """Return why ``systemd-analyze verify`` cannot run here, or None when it can."""
    if not shutil.which("systemd-analyze"):
        return "systemd-analyze is not installed"
    probe = tmp_path / "capability-probe.service"
    probe.write_text("[Service]\nType=oneshot\nExecStart=/bin/true\n")
    result = subprocess.run(
        ["systemd-analyze", "verify", str(probe)], capture_output=True, text=True, check=False, timeout=60
    )
    if result.returncode:
        return f"systemd-analyze cannot verify even a minimal unit here: {(result.stderr or result.stdout).strip()}"
    return None


def test_rendered_units_pass_systemd_analyze(tmp_path: Path) -> None:
    rendered = installer.render_units(Path(sys.executable).parents[2])
    reason = _systemd_analyze_usable(tmp_path)
    if reason:
        pytest.skip(reason)
    paths = []
    for name, text in rendered.items():
        file = tmp_path / name
        file.write_text(text)
        paths.append(str(file))
    result = subprocess.run(
        ["systemd-analyze", "verify", *paths], capture_output=True, text=True, check=False, timeout=60
    )
    assert result.returncode == 0, result.stderr


@pytest.mark.skipif(
    os.environ.get("LU_SYSTEMD_USER_PROBES") != "1",
    reason="creates a transient unit in the real user service manager; opt in with LU_SYSTEMD_USER_PROBES=1",
)
def test_service_sandbox_refuses_network_sockets() -> None:
    """Run the service's own network directives in a transient user unit and try to open sockets.

    This talks to the host's real systemd user manager, so it runs only on explicit opt-in.
    """
    service = (installer.TEMPLATE_DIR / installer.UNITS[0]).read_text()
    properties = [
        line
        for line in service.splitlines()
        if line.startswith(("RestrictAddressFamilies=", "IPAddressDeny=", "PrivateNetwork="))
    ]
    environment = dict(os.environ)
    environment.setdefault("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}")
    if not shutil.which("systemd-run"):
        pytest.skip("systemd-run is not installed")
    manager = subprocess.run(
        ["systemctl", "--user", "show-environment"], capture_output=True, env=environment, check=False, timeout=30
    )
    if manager.returncode:
        pytest.skip("no reachable systemd user manager on this runner")
    probe = (
        "import socket\n"
        "for family in (socket.AF_INET, socket.AF_INET6):\n"
        "    try:\n"
        "        socket.socket(family, socket.SOCK_STREAM).close()\n"
        "        print('open', family.name)\n"
        "    except OSError:\n"
        "        print('refused', family.name)\n"
        "socket.socket(socket.AF_UNIX, socket.SOCK_STREAM).close()\n"
        "print('open AF_UNIX')\n"
    )
    command = ["systemd-run", "--user", "--wait", "--pipe", "--quiet"]
    for line in properties:
        command += ["-p", line]
    result = subprocess.run(
        [*command, sys.executable, "-I", "-c", probe],
        capture_output=True,
        text=True,
        env=environment,
        check=False,
        timeout=120,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.split("\n")[:3] == ["refused AF_INET", "refused AF_INET6", "open AF_UNIX"]
