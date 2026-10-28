"""Linux-native systemd templates must supervise listeners, not oneshot services.sh."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from scripts.storage import install_data_volume_dropins as installer
from tests._host_path_guard import assert_no_host_facts

PACKAGING = Path(__file__).resolve().parents[2] / "packaging" / "systemd"
UNITS = (
    "learn-ukrainian-api.service",
    "learn-ukrainian-sources.service",
    "learn-ukrainian-work.service",
    "learn-ukrainian-astro.service",
)
DROPINS = PACKAGING / "dropins"


def test_systemd_templates_have_no_host_facts() -> None:
    for path in PACKAGING.iterdir():
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        assert_no_host_facts(text, path.name)
    for path in (
        PACKAGING / "learn-ukrainian-worktree-gc.service",
        DROPINS / "learn-ukrainian-worktree-gc.service.d/data-volume.conf",
    ):
        command = next(line for line in path.read_text().splitlines() if line.startswith("ExecStart=") and line != "ExecStart=")
        assert command.endswith("--repo-root @REPO_ROOT@ --repo-root @PRIVATE_ROOT@ --apply")


@pytest.mark.repo_wide
def test_data_volume_dropins_cover_all_services_and_preserve_commands() -> None:
    timers = {path.stem + ".service" for path in PACKAGING.glob("*.timer")}
    expected = set(UNITS) | timers
    actual = {path.parent.name.removesuffix(".d") for path in DROPINS.glob("*.service.d/data-volume.conf")}
    assert actual == expected
    for unit in expected:
        original = (PACKAGING / unit).read_text(encoding="utf-8")
        commands = [line.removeprefix("ExecStart=") for line in original.splitlines() if line.startswith("ExecStart=")]
        dropin = (DROPINS / f"{unit}.d/data-volume.conf").read_text(encoding="utf-8")
        assert "ExecStart=\n" in dropin
        if unit == "learn-ukrainian-project-state-reporter.service":
            commands = [command.replace("%h/projects/learn-ukrainian", "@REPO_ROOT@") for command in commands]
            assert "WorkingDirectory=@REPO_ROOT@" in dropin
        # A oneshot may run several commands; the guard must wrap each, in order.
        guarded = [line for line in dropin.splitlines() if line.startswith("ExecStart=") and line != "ExecStart="]
        assert len(guarded) == len(commands)
        for line, command in zip(guarded, commands, strict=True):
            assert line.endswith(f"/data_volume_guard.sh -- {command}")
        assert "RestartPreventExitStatus=78" in dropin


def test_data_volume_dropin_installer_refuses_dispatch_worktree_apply(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    destination = tmp_path / "user"
    worktree_root = Path(".worktrees") / "dispatch" / "codex" / "task" / "repo"
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(installer, "REPO_ROOT", worktree_root)
    monkeypatch.setattr(
        sys,
        "argv",
        ["install_data_volume_dropins.py", "--destination", str(destination), "--apply"],
    )

    with pytest.raises(SystemExit) as exc_info:
        installer.main()

    assert exc_info.value.code == 2
    assert "--apply must run from the primary checkout" in capsys.readouterr().err
    assert not destination.exists()


def test_data_volume_dropin_installer_applies_from_primary_checkout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    destination = tmp_path / "user"
    monkeypatch.chdir(tmp_path)
    primary_root = Path("primary")
    (primary_root / ".git").mkdir(parents=True)
    monkeypatch.setattr(installer, "REPO_ROOT", primary_root)
    monkeypatch.setattr(
        sys,
        "argv",
        ["install_data_volume_dropins.py", "--destination", str(destination), "--apply"],
    )
    assert installer.main() == 0
    files = list(destination.glob("*.service.d/data-volume.conf"))
    assert len(files) == 19
    assert all("@REPO_ROOT@" not in file.read_text(encoding="utf-8") for file in files)
    assert all("@PYTHON@" not in file.read_text(encoding="utf-8") for file in files)
    assert all("@PRIVATE_ROOT@" not in file.read_text(encoding="utf-8") for file in files)
    assert (
        f"--repo-root {primary_root} "
        f"--repo-root {primary_root.parent / 'learn-ukrainian-infra-private'} --apply"
        in (destination / "learn-ukrainian-worktree-gc.service.d/data-volume.conf").read_text(encoding="utf-8")
    )


def test_git_maintenance_limits_and_schedule() -> None:
    from scripts.orchestration.scheduled_worktree_cleanup import GC_DEADLINE_SECONDS, GC_MEMORY_MAX

    service = (PACKAGING / "learn-ukrainian-git-maintenance.service").read_text()
    assert GC_MEMORY_MAX == 2 * 1024**3
    assert {"MemoryMax=2G", "MemorySwapMax=0", "CPUQuota=100%", "TasksMax=32", "KillMode=control-group"} <= set(service.splitlines())
    timeout = int(next(line.split("=", 1)[1] for line in service.splitlines() if line.startswith("TimeoutStartSec=")))
    # Both repositories run sequentially; each may consume its full deadline.
    assert timeout > 2 * GC_DEADLINE_SECONDS + 20
    timer = (PACKAGING / "learn-ukrainian-git-maintenance.timer").read_text()
    assert {"OnCalendar=*-*-* 03:30:00 UTC", "Persistent=false"} <= set(timer.splitlines())
