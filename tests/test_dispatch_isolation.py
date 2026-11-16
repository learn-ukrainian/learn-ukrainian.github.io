"""Shared fixtures retained for product tests; machinery test cases run in machinery."""
from __future__ import annotations

import os
import sys
import textwrap
from pathlib import Path

_PY = sys.executable


_MEMORY_MAX = str(4 * 1024**3)


_MEMORY_SWAP = str(512 * 1024**2)


def _write_exe(path: Path, body: str) -> None:
    path.write_text(f"#!{_PY}\n" + textwrap.dedent(body).lstrip("\n"), encoding="utf-8")
    path.chmod(0o755)


def _install_fakes(tmp_path: Path) -> Path:
    bindir = tmp_path / "bin"
    bindir.mkdir()
    _write_exe(
        bindir / "systemctl",
        """
        import os, sys, time
        mode = os.environ.get("FAKE_SYSTEMCTL", "ok")
        if os.environ.get("FAKE_REQUIRE_BUS") and not (
            os.environ.get("XDG_RUNTIME_DIR") or os.environ.get("DBUS_SESSION_BUS_ADDRESS")
        ):
            sys.stderr.write("Failed to connect to user scope bus via local transport: "
                             "$DBUS_SESSION_BUS_ADDRESS and $XDG_RUNTIME_DIR not defined\\n")
            sys.exit(1)
        if mode == "timeout":
            time.sleep(30)
        if mode == "down":
            sys.stderr.write("Failed to connect to bus: No such file or directory\\n")
            sys.exit(1)
        if mode == "not-loaded":
            sys.stdout.write("LoadState=not-found\\nMemoryMax=infinity\\nMemorySwapMax=infinity\\n")
            raise SystemExit(0)
        if mode == "bad-memory":
            sys.stdout.write("LoadState=loaded\\nMemoryMax=infinity\\nMemorySwapMax=infinity\\n")
            raise SystemExit(0)
        if mode == "bad-swap":
            sys.stdout.write(f"LoadState=loaded\\nMemoryMax={os.environ['FAKE_MEMORY_MAX']}\\nMemorySwapMax=infinity\\n")
            raise SystemExit(0)
        sys.stdout.write(
            "LoadState=loaded\\n"
            f"MemoryMax={os.environ['FAKE_MEMORY_MAX']}\\n"
            f"MemorySwapMax={os.environ['FAKE_MEMORY_SWAP']}\\n"
        )
        """,
    )
    _write_exe(
        bindir / "loginctl",
        """
        import os, sys, time
        mode = os.environ.get("FAKE_LOGINCTL", "yes")
        if mode == "timeout":
            time.sleep(30)
        if mode == "down":
            sys.stderr.write("Failed to get user: not found\\n")
            sys.exit(1)
        value = "yes" if mode == "yes" else mode
        sys.stdout.write(f"Linger={value}\\n")
        """,
    )
    _write_exe(
        bindir / "stat",
        """
        import os, sys, time
        mode = os.environ.get("FAKE_STAT", "cgroup2fs")
        if mode == "timeout":
            time.sleep(30)
        if mode == "down":
            sys.stderr.write("stat: cannot read filesystem\\n")
            sys.exit(1)
        sys.stdout.write(mode + "\\n")
        """,
    )
    _write_exe(
        bindir / "systemd-run",
        """
        import os, sys, time
        log = os.environ.get("FAKE_ARGV_LOG")
        if log:
            open(log, "w", encoding="utf-8").write("\\n".join(sys.argv))
        mode = os.environ.get("FAKE_SYSTEMD_RUN", "exec")
        env_log = os.environ.get("FAKE_ENV_LOG")
        if env_log:
            names = ("XDG_RUNTIME_DIR", "DBUS_SESSION_BUS_ADDRESS")
            open(env_log, "w", encoding="utf-8").write(repr({name: os.environ.get(name) for name in names}))
        if os.environ.get("FAKE_REQUIRE_BUS") and not (
            os.environ.get("XDG_RUNTIME_DIR") or os.environ.get("DBUS_SESSION_BUS_ADDRESS")
        ):
            sys.stderr.write("Failed to connect to user scope bus via local transport: "
                             "$DBUS_SESSION_BUS_ADDRESS and $XDG_RUNTIME_DIR not defined\\n")
            sys.exit(1)
        if mode == "fail":
            sys.stderr.write("Failed to start transient scope unit: Unit name already exists\\n")
            sys.exit(1)
        if mode == "timeout":
            time.sleep(30)
        if "--" not in sys.argv:
            sys.stderr.write("missing --\\n")
            sys.exit(2)
        command = sys.argv[sys.argv.index("--") + 1 :]
        os.execv(command[0], command)
        """,
    )
    return bindir


def _env(bindir: Path, **overrides: str) -> dict[str, str]:
    env = os.environ.copy()
    env["PATH"] = f"{bindir}{os.pathsep}{env.get('PATH', '')}"
    env["FAKE_MEMORY_MAX"] = _MEMORY_MAX
    env["FAKE_MEMORY_SWAP"] = _MEMORY_SWAP
    env.update(overrides)
    return env


def _subtree(tmp_path: Path, text: str = "cpu memory pids\n") -> Path:
    path = tmp_path / "cgroup.subtree_control"
    path.write_text(text, encoding="ascii")
    return path
