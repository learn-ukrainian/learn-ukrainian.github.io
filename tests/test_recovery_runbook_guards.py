"""Executable guards for the shared-install restore in docs/runbooks/recovery.md.

The shell under test is the runbook's own fenced blocks. npm is never invoked.
The puppeteer recovery slice stops before ``npm ci`` and runs against a synthetic
cache under the test temporary directory.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

RUNBOOK = Path(__file__).resolve().parents[1] / "docs" / "runbooks" / "recovery.md"
_CACHE_LINE = '  cache="${PUPPETEER_CACHE_DIR:-$HOME/.cache/puppeteer}"\n'
_INSTALL_LINE = '  install_dir="<browser folder from the puppeteer error>"\n'
_EXECUTABLE_LINE = '  executable="<executable path from the puppeteer error>"\n'
_NPM_CI_LINE = "\n  npm ci\n"


def _blocks() -> list[str]:
    text = RUNBOOK.read_text(encoding="utf-8")
    blocks: list[str] = []
    lines = text.splitlines()
    index = 0
    while index < len(lines):
        if lines[index].startswith("```bash"):
            index += 1
            body: list[str] = []
            while index < len(lines) and not lines[index].startswith("```"):
                body.append(lines[index])
                index += 1
            blocks.append("\n".join(body) + "\n")
        index += 1
    return blocks


def _puppeteer_block() -> str:
    matches = [block for block in _blocks() if "PUPPETEER_CACHE_DIR" in block and "rmdir" in block]
    assert len(matches) == 1
    return matches[0]


def _recovery_script() -> str:
    """The runbook's cache-recovery commands, with the operator paths bound from the environment."""
    block = _puppeteer_block()
    start = block.find(_CACHE_LINE)
    end = block.find(_NPM_CI_LINE)
    assert start != -1 and end != -1 and start < end
    body = block[start:end]
    assert _INSTALL_LINE in body and _EXECUTABLE_LINE in body
    body = body.replace(_INSTALL_LINE, '  install_dir="$RECOVERY_TEST_INSTALL_DIR"\n', 1)
    body = body.replace(_EXECUTABLE_LINE, '  executable="$RECOVERY_TEST_EXECUTABLE"\n', 1)
    assert "<browser folder" not in body
    assert "npm" not in body
    assert "rm -rf" not in body
    return "set -euo pipefail\n" + body + "\n"


def _run(
    *,
    cache: str,
    install_dir: str,
    executable: str,
    home: Path,
) -> subprocess.CompletedProcess[str]:
    env = {
        "PATH": "/usr/bin:/bin",
        "HOME": str(home),
        "PUPPETEER_CACHE_DIR": cache,
        "RECOVERY_TEST_INSTALL_DIR": install_dir,
        "RECOVERY_TEST_EXECUTABLE": executable,
        "LC_ALL": "C",
    }
    return subprocess.run(
        ["bash", "-c", _recovery_script()],
        check=False,
        capture_output=True,
        text=True,
        env=env,
        timeout=30,
    )


def _home(tmp_path: Path) -> Path:
    home = tmp_path / "home"
    home.mkdir()
    return home


def _sentinel(cache: Path) -> Path:
    path = cache / "keep"
    path.write_text("sentinel", encoding="utf-8")
    return path


def _executable(install: Path) -> str:
    return str(install / "chrome-linux64" / "chrome")


def test_recovery_block_rmdirs_before_quarantine_and_preserves_newlines() -> None:
    """Empty ``rmdir`` is the first branch. The move is a rename, and captures keep a trailing newline."""
    block = _puppeteer_block()
    assert "rm -rf" not in block
    assert "rm -r" not in block
    assert "printf x" in block
    assert "${captured%x}" in block
    assert block.index("rmdir --") < block.index("mv -T --") < block.index(_NPM_CI_LINE)


def test_failed_cd_exits_before_npm_in_every_install_block(tmp_path: Path) -> None:
    blocks = [block for block in _blocks() if "npm ci" in block and "|| exit 1" in block]
    assert len(blocks) == 3
    for path in (
        Path("/absolute/path/to/clean/learn-ukrainian"),
        Path("/absolute/path/to/primary/learn-ukrainian"),
    ):
        assert not path.exists()
    home = _home(tmp_path)
    stamp = tmp_path / "npm-invoked"
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    trip = "#!/bin/sh\nprintf '%s\\n' \"$0 $*\" >> \"$NPM_TRIPWIRE\"\nexit 99\n"
    for name in ("npm", "npx", "node"):
        tool = bin_dir / name
        tool.write_text(trip, encoding="utf-8")
        tool.chmod(0o755)
    env = {
        "PATH": f"{bin_dir}:/usr/bin:/bin",
        "HOME": str(home),
        "NPM_TRIPWIRE": str(stamp),
        "LC_ALL": "C",
    }
    for block in blocks:
        proc = subprocess.run(
            ["bash", "-c", block], check=False, capture_output=True, text=True, env=env, timeout=30
        )
        assert proc.returncode == 1, proc.stderr
        assert not stamp.exists()


def test_every_fenced_bash_block_passes_bash_n() -> None:
    blocks = _blocks()
    assert len(blocks) >= 3
    for index, block in enumerate(blocks):
        proc = subprocess.run(
            ["bash", "-n"], input=block, text=True, capture_output=True, check=False, timeout=30
        )
        assert proc.returncode == 0, f"block {index}: {proc.stderr}"


def test_newline_in_the_cache_path_does_not_remove_an_outside_empty_directory(tmp_path: Path) -> None:
    """A cache directory whose name ends in a newline must not authorize a different tree."""
    root = tmp_path / "root"
    cache = root / "puppeteer\n"
    (cache / "chrome").mkdir(parents=True)
    kept = _sentinel(cache)
    outside = root / "puppeteer" / "linux-empty"
    outside.mkdir(parents=True)
    outside_keep = outside.parent / "keep"
    outside_keep.write_text("outside", encoding="utf-8")
    proc = _run(
        cache=str(cache),
        install_dir=str(outside),
        executable=_executable(outside),
        home=_home(tmp_path),
    )
    assert proc.returncode != 0, proc.stderr
    assert outside.is_dir()
    assert outside_keep.read_text(encoding="utf-8") == "outside"
    assert kept.read_text(encoding="utf-8") == "sentinel"
    assert not list((cache / "chrome").glob("linux-empty.quarantine.*"))


def test_newline_in_the_install_ancestor_does_not_remove_an_outside_empty_directory(tmp_path: Path) -> None:
    """Stripping a newline from the install path must not make it look inside the cache."""
    root = tmp_path / "root"
    root.mkdir()
    cache = root / "puppeteer"
    cache.mkdir()
    kept = _sentinel(cache)
    install = root / "puppeteer\n" / "linux-empty"
    install.mkdir(parents=True)
    proc = _run(
        cache=str(cache),
        install_dir=str(install),
        executable=_executable(install),
        home=_home(tmp_path),
    )
    assert proc.returncode != 0, proc.stderr
    assert install.is_dir()
    assert kept.read_text(encoding="utf-8") == "sentinel"


def test_empty_install_directory_inside_the_cache_is_removed(tmp_path: Path) -> None:
    cache = tmp_path / "cache"
    install = cache / "chrome" / "linux-1"
    install.mkdir(parents=True)
    kept = _sentinel(cache)
    proc = _run(
        cache=str(cache),
        install_dir=str(install),
        executable=_executable(install),
        home=_home(tmp_path),
    )
    assert proc.returncode == 0, proc.stderr
    assert not install.exists()
    assert (cache / "chrome").is_dir()
    assert kept.read_text(encoding="utf-8") == "sentinel"
    assert list((cache / "chrome").glob("linux-1.quarantine.*")) == []


def test_nonempty_partial_install_is_quarantined_and_preserved(tmp_path: Path) -> None:
    cache = tmp_path / "cache"
    install = cache / "chrome" / "linux-1"
    (install / "chrome-linux64").mkdir(parents=True)
    (install / "chrome-linux64" / "leftover").write_text("keep", encoding="utf-8")
    kept = _sentinel(cache)
    proc = _run(
        cache=str(cache),
        install_dir=str(install),
        executable=_executable(install),
        home=_home(tmp_path),
    )
    assert proc.returncode == 0, proc.stderr
    assert not install.exists()
    quarantined = list((cache / "chrome").glob("linux-1.quarantine.*"))
    assert len(quarantined) == 1
    assert quarantined[0].parent == cache / "chrome"
    assert (quarantined[0] / "chrome-linux64" / "leftover").read_text(encoding="utf-8") == "keep"
    assert kept.read_text(encoding="utf-8") == "sentinel"
    assert cache.is_dir()


def test_cache_root_and_outside_directory_are_left_in_place(tmp_path: Path) -> None:
    cache = tmp_path / "cache"
    cache.mkdir()
    kept = _sentinel(cache)
    home = _home(tmp_path)
    root_proc = _run(
        cache=str(cache),
        install_dir=str(cache),
        executable=_executable(cache),
        home=home,
    )
    assert root_proc.returncode != 0, root_proc.stderr
    assert "cache root" in root_proc.stderr
    assert kept.read_text(encoding="utf-8") == "sentinel"

    outside = tmp_path / "outside" / "linux-1"
    outside.mkdir(parents=True)
    outside_proc = _run(
        cache=str(cache),
        install_dir=str(outside),
        executable=_executable(outside),
        home=home,
    )
    assert outside_proc.returncode != 0, outside_proc.stderr
    assert outside.is_dir()
    assert kept.read_text(encoding="utf-8") == "sentinel"


def test_present_executable_blocks_removal(tmp_path: Path) -> None:
    cache = tmp_path / "cache"
    install = cache / "chrome" / "linux-1"
    executable = install / "chrome-linux64" / "chrome"
    executable.parent.mkdir(parents=True)
    executable.write_text("bin", encoding="utf-8")
    kept = _sentinel(cache)
    proc = _run(
        cache=str(cache),
        install_dir=str(install),
        executable=str(executable),
        home=_home(tmp_path),
    )
    assert proc.returncode != 0, proc.stderr
    assert executable.read_text(encoding="utf-8") == "bin"
    assert install.is_dir()
    assert kept.read_text(encoding="utf-8") == "sentinel"
    assert list((cache / "chrome").glob("linux-1.quarantine.*")) == []


def test_unlistable_directory_is_not_moved(tmp_path: Path) -> None:
    if os.geteuid() == 0:
        pytest.skip("mode 000 does not stop root from listing the directory")
    cache = tmp_path / "cache"
    install = cache / "chrome" / "linux-1"
    (install / "child").mkdir(parents=True)
    kept = _sentinel(cache)
    install.chmod(0)
    try:
        proc = _run(
            cache=str(cache),
            install_dir=str(install),
            executable=_executable(install),
            home=_home(tmp_path),
        )
    finally:
        install.chmod(0o755)
    assert proc.returncode != 0, proc.stderr
    assert (install / "child").is_dir()
    assert kept.read_text(encoding="utf-8") == "sentinel"
    assert list((cache / "chrome").glob("linux-1.quarantine.*")) == []


def test_symlink_install_directory_is_not_moved(tmp_path: Path) -> None:
    cache = tmp_path / "cache"
    real = cache / "chrome" / "real"
    real.mkdir(parents=True)
    (real / "child").write_text("keep", encoding="utf-8")
    link = cache / "chrome" / "linux-1"
    link.symlink_to(real, target_is_directory=True)
    kept = _sentinel(cache)
    proc = _run(
        cache=str(cache),
        install_dir=str(link),
        executable=_executable(link),
        home=_home(tmp_path),
    )
    assert proc.returncode != 0, proc.stderr
    assert link.is_symlink()
    assert (real / "child").read_text(encoding="utf-8") == "keep"
    assert kept.read_text(encoding="utf-8") == "sentinel"
    assert list((cache / "chrome").glob("*.quarantine.*")) == []
