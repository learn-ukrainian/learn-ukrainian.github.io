"""Executable guards for the shared-install restore in docs/runbooks/recovery.md.

The shell under test is the runbook's own fenced blocks. npm is never invoked.
The puppeteer recovery slice stops before ``npm ci`` and runs against a synthetic
cache under the test temporary directory.
"""

from __future__ import annotations

import os
import subprocess
import time
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
    path_prefix: str | None = None,
    path: str | None = None,
    extra_env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    if path is None:
        path = "/usr/bin:/bin"
        # Optional directory of an mv that rejects --update=none-fail.
        # path_prefix stays in front so a test's own stubs win.
        shim = os.environ.get("RECOVERY_TEST_MV_SHIM")
        if shim:
            path = f"{shim}:{path}"
        if path_prefix:
            path = f"{path_prefix}:{path}"
    env = {
        "PATH": path,
        "HOME": str(home),
        "PUPPETEER_CACHE_DIR": cache,
        "RECOVERY_TEST_INSTALL_DIR": install_dir,
        "RECOVERY_TEST_EXECUTABLE": executable,
        "LC_ALL": "C",
    }
    if extra_env:
        env.update(extra_env)
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
    """Empty ``rmdir`` is the first branch. The move is a noreplace rename, and captures keep a trailing newline."""
    block = _puppeteer_block()
    assert "rm -rf" not in block
    assert "rm -r" not in block
    assert "printf x" in block
    assert "${captured%x}" in block
    move = 'mv -n -T -- "$install_real" "$quarantine"'
    probe = 'timeout 120 lsof -nP -F p +D "$1"'
    assert "--update=none-fail" not in block
    assert "9.5 or newer" not in RUNBOOK.read_text(encoding="utf-8")
    assert block.index("rmdir --") < block.index(probe) < block.index(move)
    assert block.index(probe) < block.index('_probe_cache_holders "$cache_real"') < block.index(move)
    assert 'lsof -nP +D "$cache_real" 2>/dev/null || true' not in block
    assert block.index(move) < block.index(_NPM_CI_LINE)
    assert "Refusing to quarantine the browser cache while a process holds it." in block
    assert "Refusing to quarantine over an existing path." in block


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
    trip = '#!/bin/sh\nprintf \'%s\\n\' "$0 $*" >> "$NPM_TRIPWIRE"\nexit 99\n'
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
        proc = subprocess.run(["bash", "-c", block], check=False, capture_output=True, text=True, env=env, timeout=30)
        assert proc.returncode == 1, proc.stderr
        assert not stamp.exists()


def test_every_fenced_bash_block_passes_bash_n() -> None:
    blocks = _blocks()
    assert len(blocks) >= 3
    for index, block in enumerate(blocks):
        proc = subprocess.run(["bash", "-n"], input=block, text=True, capture_output=True, check=False, timeout=30)
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


def _executable_stub(directory: Path, name: str, body: str) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / name
    path.write_text(body, encoding="utf-8")
    path.chmod(0o755)
    return path


def _partial_install(tmp_path: Path) -> tuple[Path, Path, Path]:
    cache = tmp_path / "cache"
    install = cache / "chrome" / "linux-1"
    (install / "chrome-linux64").mkdir(parents=True)
    (install / "chrome-linux64" / "leftover").write_text("keep", encoding="utf-8")
    kept = _sentinel(cache)
    return cache, install, kept


def _assert_install_stays(install: Path, kept: Path) -> None:
    assert install.is_dir()
    assert (install / "chrome-linux64" / "leftover").read_text(encoding="utf-8") == "keep"
    assert list(install.parent.glob("linux-1.quarantine.*")) == []
    assert kept.read_text(encoding="utf-8") == "sentinel"


def _assert_probe_refused(
    proc: subprocess.CompletedProcess[str],
    install: Path,
    kept: Path,
    probe_text: str,
) -> None:
    assert proc.returncode != 0, f"expected refusal, exited {proc.returncode}: {proc.stderr}"
    assert probe_text in proc.stderr
    _assert_install_stays(install, kept)


def _command_path_without_lsof(directory: Path) -> str:
    """Tools the block needs before the probe, with lsof absent."""
    directory.mkdir(parents=True, exist_ok=True)
    for name in ("bash", "readlink", "stat", "find", "date", "timeout", "mv"):
        target = Path("/usr/bin") / name
        if not target.exists():
            target = Path("/bin") / name
        link = directory / name
        if not link.exists():
            link.symlink_to(target)
    assert not (directory / "lsof").exists()
    return str(directory)


def test_destination_created_after_the_existence_check_is_left_intact(tmp_path: Path) -> None:
    """An empty destination created after the absence check must not be replaced."""
    cache = tmp_path / "cache"
    install = cache / "chrome" / "linux-1"
    (install / "chrome-linux64").mkdir(parents=True)
    (install / "chrome-linux64" / "leftover").write_text("keep", encoding="utf-8")
    kept = _sentinel(cache)
    # The stub runs as mv, after the block's existence check, and creates the destination.
    _executable_stub(
        tmp_path / "bin",
        "mv",
        '#!/bin/bash\nset -euo pipefail\ndest="${@: -1}"\nmkdir -p -- "$dest"\nexec /usr/bin/mv "$@"\n',
    )
    proc = _run(
        cache=str(cache),
        install_dir=str(install),
        executable=_executable(install),
        home=_home(tmp_path),
        path_prefix=str(tmp_path / "bin"),
    )
    assert install.is_dir(), proc.stderr
    assert (install / "chrome-linux64" / "leftover").read_text(encoding="utf-8") == "keep"
    created = list((cache / "chrome").glob("linux-1.quarantine.*"))
    assert len(created) == 1
    assert created[0].is_dir()
    assert list(created[0].iterdir()) == []
    assert proc.returncode != 0, proc.stderr
    assert "Refusing to quarantine over an existing path." in proc.stderr
    assert kept.read_text(encoding="utf-8") == "sentinel"


def test_ancestor_swap_before_the_move_does_not_leave_the_cache(tmp_path: Path) -> None:
    """A parent swapped for an outside symlink after validation must not be quarantined there."""
    cache = tmp_path / "cache"
    install = cache / "chrome" / "linux-1"
    (install / "chrome-linux64").mkdir(parents=True)
    marker = install / "chrome-linux64" / "leftover"
    marker.write_text("inside", encoding="utf-8")
    kept = _sentinel(cache)
    outside = tmp_path / "outside"
    victim = outside / "linux-1" / "chrome-linux64"
    victim.mkdir(parents=True)
    (victim / "marker").write_text("victim", encoding="utf-8")
    # date runs after validation and before mv. The stub swaps the ancestor, then the real date runs.
    _executable_stub(
        tmp_path / "bin",
        "date",
        "#!/bin/bash\n"
        "set -euo pipefail\n"
        'mv -T -- "$RECOVERY_ANCESTOR_DIR" "$RECOVERY_ANCESTOR_DIR.real"\n'
        'ln -s "$RECOVERY_ANCESTOR_TARGET" "$RECOVERY_ANCESTOR_DIR"\n'
        'exec /usr/bin/date "$@"\n',
    )
    holder = subprocess.Popen(
        ["bash", "-c", 'exec 3<"$1"; exec sleep 60', "_", str(marker)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        seen = ""
        for _ in range(50):
            probe = subprocess.run(
                ["lsof", "-nP", "+D", str(cache)],
                check=False,
                capture_output=True,
                text=True,
                timeout=10,
            )
            seen = probe.stdout
            if str(holder.pid) in seen:
                break
            time.sleep(0.05)
        else:
            pytest.fail(f"holder was not visible to lsof\n{seen}")
        proc = _run(
            cache=str(cache),
            install_dir=str(install),
            executable=_executable(install),
            home=_home(tmp_path),
            path_prefix=str(tmp_path / "bin"),
            extra_env={
                "RECOVERY_ANCESTOR_DIR": str(cache / "chrome"),
                "RECOVERY_ANCESTOR_TARGET": str(outside),
            },
        )
    finally:
        holder.kill()
        holder.wait(timeout=5)
    assert (victim / "marker").is_file()
    assert (victim / "marker").read_text(encoding="utf-8") == "victim"
    assert list(outside.glob("linux-1.quarantine.*")) == []
    assert (cache / "chrome.real" / "linux-1" / "chrome-linux64" / "leftover").read_text(encoding="utf-8") == "inside"
    assert proc.returncode != 0, proc.stderr
    assert "Refusing to quarantine the browser cache while a process holds it." in proc.stderr
    assert kept.read_text(encoding="utf-8") == "sentinel"


def test_lsof_error_exit_does_not_rename(tmp_path: Path) -> None:
    """A probe that prints an error and exits 2 is not an idle cache."""
    cache, install, kept = _partial_install(tmp_path)
    _executable_stub(
        tmp_path / "bin",
        "lsof",
        "#!/bin/sh\nprintf '%s\\n' 'stub-error: probe failed' >&2\nexit 2\n",
    )
    proc = _run(
        cache=str(cache),
        install_dir=str(install),
        executable=_executable(install),
        home=_home(tmp_path),
        path_prefix=str(tmp_path / "bin"),
    )
    assert proc.returncode != 0, proc.stderr
    assert "stub-error: probe failed" in proc.stderr
    _assert_install_stays(install, kept)


def test_lsof_idle_exit_1_with_no_output_quarantines(tmp_path: Path) -> None:
    """Exit 1 and no output is the idle result measured for lsof with warnings suppressed."""
    cache, install, kept = _partial_install(tmp_path)
    _executable_stub(tmp_path / "bin", "lsof", "#!/bin/sh\nexit 1\n")
    proc = _run(
        cache=str(cache),
        install_dir=str(install),
        executable=_executable(install),
        home=_home(tmp_path),
        path_prefix=str(tmp_path / "bin"),
    )
    assert proc.returncode == 0, proc.stderr
    assert not install.exists()
    quarantined = list((cache / "chrome").glob("linux-1.quarantine.*"))
    assert len(quarantined) == 1
    assert (quarantined[0] / "chrome-linux64" / "leftover").read_text(encoding="utf-8") == "keep"
    assert kept.read_text(encoding="utf-8") == "sentinel"


def test_lsof_holder_field_refuses(tmp_path: Path) -> None:
    """A p<pid> field is a holder even when lsof exits 0."""
    cache, install, kept = _partial_install(tmp_path)
    _executable_stub(tmp_path / "bin", "lsof", "#!/bin/sh\nprintf '%s\\n' 'p12345'\nexit 0\n")
    proc = _run(
        cache=str(cache),
        install_dir=str(install),
        executable=_executable(install),
        home=_home(tmp_path),
        path_prefix=str(tmp_path / "bin"),
    )
    assert proc.returncode != 0, proc.stderr
    assert "p12345" in proc.stderr
    assert "Refusing to quarantine the browser cache while a process holds it." in proc.stderr
    _assert_install_stays(install, kept)


def test_lsof_timeout_is_not_idle(tmp_path: Path) -> None:
    """coreutils timeout exit 124 refuses. An idle lsof behind it must not run the rename."""
    cache, install, kept = _partial_install(tmp_path)
    _executable_stub(
        tmp_path / "bin",
        "timeout",
        "#!/bin/sh\nprintf '%s\\n' 'timeout: command timed out' >&2\nexit 124\n",
    )
    _executable_stub(tmp_path / "bin", "lsof", "#!/bin/sh\nexit 1\n")
    proc = _run(
        cache=str(cache),
        install_dir=str(install),
        executable=_executable(install),
        home=_home(tmp_path),
        path_prefix=str(tmp_path / "bin"),
    )
    assert proc.returncode != 0, proc.stderr
    assert "timeout: command timed out" in proc.stderr
    assert "status 124" in proc.stderr
    _assert_install_stays(install, kept)


def test_lsof_permission_diagnostic_is_not_idle(tmp_path: Path) -> None:
    """Exit 1 with an opendir diagnostic is a failed probe, including beside the tracefs warning."""
    cache, install, kept = _partial_install(tmp_path)
    _executable_stub(
        tmp_path / "bin",
        "lsof",
        """#!/bin/sh
printf '%s\\n' \\
  "lsof: WARNING: can't stat() tracefs file system /sys/kernel/debug/tracing" \\
  "      Output information may be incomplete." \\
  "lsof: WARNING: can't opendir(/cache): Permission denied" >&2
exit 1
""",
    )
    proc = _run(
        cache=str(cache),
        install_dir=str(install),
        executable=_executable(install),
        home=_home(tmp_path),
        path_prefix=str(tmp_path / "bin"),
    )
    assert proc.returncode != 0, proc.stderr
    assert "Permission denied" in proc.stderr
    _assert_install_stays(install, kept)


def test_lsof_filesystem_stat_warning_stays_idle(tmp_path: Path) -> None:
    """The tracefs stat warning measured on lsof 4.99.4 does not hide an empty selection."""
    cache, install, kept = _partial_install(tmp_path)
    _executable_stub(
        tmp_path / "bin",
        "lsof",
        """#!/bin/sh
printf '%s\\n' \\
  "lsof: WARNING: can't stat() tracefs file system /sys/kernel/debug/tracing" \\
  "      Output information may be incomplete." >&2
exit 1
""",
    )
    proc = _run(
        cache=str(cache),
        install_dir=str(install),
        executable=_executable(install),
        home=_home(tmp_path),
        path_prefix=str(tmp_path / "bin"),
    )
    assert proc.returncode == 0, proc.stderr
    assert "can't stat()" in proc.stderr
    assert not install.exists()
    quarantined = list((cache / "chrome").glob("linux-1.quarantine.*"))
    assert len(quarantined) == 1
    assert kept.read_text(encoding="utf-8") == "sentinel"


def test_lsof_exit_3_empty_output_refuses(tmp_path: Path) -> None:
    """A status other than idle or a holder, with no output, is not an idle cache."""
    cache, install, kept = _partial_install(tmp_path)
    _executable_stub(tmp_path / "bin", "lsof", "#!/bin/sh\nexit 3\n")
    proc = _run(
        cache=str(cache),
        install_dir=str(install),
        executable=_executable(install),
        home=_home(tmp_path),
        path_prefix=str(tmp_path / "bin"),
    )
    _assert_probe_refused(
        proc,
        install,
        kept,
        "Refusing to quarantine because the cache holder check did not show an idle cache (status 3).",
    )


def test_lsof_exit_0_empty_output_refuses(tmp_path: Path) -> None:
    """Exit 0 and no output is not idle.

    lsof 4.99.4 on an empty directory exits 1, with no file lines. A probe that
    claims success without that shape must not be read as idle.
    """
    cache, install, kept = _partial_install(tmp_path)
    _executable_stub(tmp_path / "bin", "lsof", "#!/bin/sh\nexit 0\n")
    proc = _run(
        cache=str(cache),
        install_dir=str(install),
        executable=_executable(install),
        home=_home(tmp_path),
        path_prefix=str(tmp_path / "bin"),
    )
    _assert_probe_refused(
        proc,
        install,
        kept,
        "Refusing to quarantine because the cache holder check did not show an idle cache (status 0).",
    )


def test_lsof_unrecognised_warning_refuses(tmp_path: Path) -> None:
    """Exit 1 with empty stdout and a warning outside the filesystem-stat pair refuses.

    The recognised pair proceeds in test_lsof_filesystem_stat_warning_stays_idle.
    """
    cache, install, kept = _partial_install(tmp_path)
    _executable_stub(
        tmp_path / "bin",
        "lsof",
        "#!/bin/sh\nprintf '%s\\n' 'lsof: WARNING: unknown filesystem probe' >&2\nexit 1\n",
    )
    proc = _run(
        cache=str(cache),
        install_dir=str(install),
        executable=_executable(install),
        home=_home(tmp_path),
        path_prefix=str(tmp_path / "bin"),
    )
    _assert_probe_refused(proc, install, kept, "lsof: WARNING: unknown filesystem probe")


def test_lsof_missing_from_path_refuses(tmp_path: Path) -> None:
    """A PATH with no lsof executable takes the block's existing refusal and does not rename."""
    cache, install, kept = _partial_install(tmp_path)
    proc = _run(
        cache=str(cache),
        install_dir=str(install),
        executable=_executable(install),
        home=_home(tmp_path),
        path=_command_path_without_lsof(tmp_path / "bin"),
    )
    _assert_probe_refused(proc, install, kept, "Refusing to quarantine without a cache holder check.")


def test_lsof_bad_option_usage_refuses(tmp_path: Path) -> None:
    """A usage diagnostic with exit 1 and no p<pid> line is a failed probe, not an idle cache."""
    cache, install, kept = _partial_install(tmp_path)
    _executable_stub(
        tmp_path / "bin",
        "lsof",
        "#!/bin/sh\n"
        "printf '%s\\n' 'lsof: illegal option character: -' ' usage: [-?abhHKlnNoOPRtUvVX] [-p s]' >&2\n"
        "exit 1\n",
    )
    proc = _run(
        cache=str(cache),
        install_dir=str(install),
        executable=_executable(install),
        home=_home(tmp_path),
        path_prefix=str(tmp_path / "bin"),
    )
    _assert_probe_refused(proc, install, kept, "lsof: illegal option character: -")
    assert "usage:" in proc.stderr


def test_lsof_error_after_ancestor_swap_does_not_rename_outside(tmp_path: Path) -> None:
    """A failing probe must not quarantine through a parent swapped for an outside symlink."""
    cache, install, kept = _partial_install(tmp_path)
    outside = tmp_path / "outside"
    victim = outside / "linux-1" / "chrome-linux64"
    victim.mkdir(parents=True)
    (victim / "marker").write_text("victim", encoding="utf-8")
    bin_dir = tmp_path / "bin"
    _executable_stub(
        bin_dir,
        "date",
        "#!/bin/bash\n"
        "set -euo pipefail\n"
        'mv -T -- "$RECOVERY_ANCESTOR_DIR" "$RECOVERY_ANCESTOR_DIR.real"\n'
        'ln -s "$RECOVERY_ANCESTOR_TARGET" "$RECOVERY_ANCESTOR_DIR"\n'
        'exec /usr/bin/date "$@"\n',
    )
    _executable_stub(
        bin_dir,
        "lsof",
        "#!/bin/sh\nprintf '%s\\n' 'stub-error: probe failed' >&2\nexit 2\n",
    )
    proc = _run(
        cache=str(cache),
        install_dir=str(install),
        executable=_executable(install),
        home=_home(tmp_path),
        path_prefix=str(bin_dir),
        extra_env={
            "RECOVERY_ANCESTOR_DIR": str(cache / "chrome"),
            "RECOVERY_ANCESTOR_TARGET": str(outside),
        },
    )
    assert proc.returncode != 0, proc.stderr
    assert "stub-error: probe failed" in proc.stderr
    assert (victim / "marker").read_text(encoding="utf-8") == "victim"
    assert list(outside.glob("linux-1.quarantine.*")) == []
    assert (cache / "chrome.real" / "linux-1" / "chrome-linux64" / "leftover").read_text(encoding="utf-8") == "keep"
    assert kept.read_text(encoding="utf-8") == "sentinel"


def test_mv_that_rejects_the_update_option_leaves_the_folder(tmp_path: Path) -> None:
    """An mv that rejects --update=none-fail fails closed through the existing error branch."""
    cache, install, kept = _partial_install(tmp_path)
    _executable_stub(
        tmp_path / "bin",
        "mv",
        "#!/bin/sh\nprintf '%s\\n' \"mv: unrecognized option '--update=none-fail'\" >&2\nexit 1\n",
    )
    proc = _run(
        cache=str(cache),
        install_dir=str(install),
        executable=_executable(install),
        home=_home(tmp_path),
        path_prefix=str(tmp_path / "bin"),
    )
    assert proc.returncode != 0, proc.stderr
    assert "unrecognized option" in proc.stderr
    assert "Refusing to quarantine; the browser folder was not renamed." in proc.stderr
    _assert_install_stays(install, kept)


_NONE_FAIL_REJECTION = "mv: invalid argument 'none-fail' for '--update'"


def _older_mv_shim(directory: Path, *, create_dest: bool = False) -> Path:
    """mv that rejects the 9.5-only option and otherwise execs /usr/bin/mv.

    create_dest makes the named destination exist before the real rename, which
    is the collision the noreplace flag must not replace.
    """
    rejection = (
        '  if [ "$arg" = "--update=none-fail" ]; then\n'
        f"    printf '%s\\n' \"{_NONE_FAIL_REJECTION}\" >&2\n"
        "    exit 1\n"
        "  fi\n"
    )
    if create_dest:
        body = (
            "#!/bin/sh\n"
            "dest=\n"
            'for arg in "$@"; do\n'
            f"{rejection}"
            "  dest=$arg\n"
            "done\n"
            'mkdir -p -- "$dest"\n'
            'exec /usr/bin/mv "$@"\n'
        )
    else:
        body = f'#!/bin/sh\nfor arg in "$@"; do\n{rejection}done\nexec /usr/bin/mv "$@"\n'
    return _executable_stub(directory, "mv", body)


def test_older_mv_shim_quarantines_a_partial_install(tmp_path: Path) -> None:
    """A partial install is quarantined when mv rejects --update=none-fail."""
    cache, install, kept = _partial_install(tmp_path)
    _older_mv_shim(tmp_path / "bin")
    proc = _run(
        cache=str(cache),
        install_dir=str(install),
        executable=_executable(install),
        home=_home(tmp_path),
        path_prefix=str(tmp_path / "bin"),
    )
    assert proc.returncode == 0, proc.stderr
    assert _NONE_FAIL_REJECTION not in proc.stderr
    assert not install.exists()
    quarantined = list((cache / "chrome").glob("linux-1.quarantine.*"))
    assert len(quarantined) == 1
    assert (quarantined[0] / "chrome-linux64" / "leftover").read_text(encoding="utf-8") == "keep"
    assert kept.read_text(encoding="utf-8") == "sentinel"


def test_older_mv_shim_does_not_replace_an_existing_destination(tmp_path: Path) -> None:
    """The same shim leaves a destination that appears as mv starts."""
    cache, install, kept = _partial_install(tmp_path)
    _older_mv_shim(tmp_path / "bin", create_dest=True)
    proc = _run(
        cache=str(cache),
        install_dir=str(install),
        executable=_executable(install),
        home=_home(tmp_path),
        path_prefix=str(tmp_path / "bin"),
    )
    assert proc.returncode != 0, proc.stderr
    assert _NONE_FAIL_REJECTION not in proc.stderr
    assert "Refusing to quarantine over an existing path." in proc.stderr
    assert install.is_dir()
    assert (install / "chrome-linux64" / "leftover").read_text(encoding="utf-8") == "keep"
    created = list((cache / "chrome").glob("linux-1.quarantine.*"))
    assert len(created) == 1
    assert created[0].is_dir()
    assert list(created[0].iterdir()) == []
    assert kept.read_text(encoding="utf-8") == "sentinel"


def test_mv_that_rejects_no_clobber_leaves_the_folder(tmp_path: Path) -> None:
    """An mv that does not implement -n fails closed and does not rename."""
    cache, install, kept = _partial_install(tmp_path)
    _executable_stub(
        tmp_path / "bin",
        "mv",
        "#!/bin/sh\n"
        'for arg in "$@"; do\n'
        '  if [ "$arg" = "-n" ] || [ "$arg" = "--no-clobber" ]; then\n'
        "    printf '%s\\n' \"mv: invalid option -- 'n'\" >&2\n"
        "    exit 1\n"
        "  fi\n"
        "done\n"
        'exec /usr/bin/mv "$@"\n',
    )
    proc = _run(
        cache=str(cache),
        install_dir=str(install),
        executable=_executable(install),
        home=_home(tmp_path),
        path_prefix=str(tmp_path / "bin"),
    )
    assert proc.returncode != 0, proc.stderr
    assert "invalid option" in proc.stderr
    assert "Refusing to quarantine; the browser folder was not renamed." in proc.stderr
    _assert_install_stays(install, kept)
