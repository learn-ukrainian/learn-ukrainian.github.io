"""Installed versus pinned versus running, written to private local state (#10862).

Session start calls ``write_report`` once. The report lives under
``$XDG_STATE_HOME/learn-ukrainian/stack-drift`` (or
``~/.local/state/learn-ukrainian/stack-drift``). It records versions only.
Command output that is not a version is dropped, and the report is refused
if the state directory is inside the repository.

There is no timer. The weekly audit publishes pinned-versus-latest; this
check does not.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path

from scripts.ci.stack_currency_report import EXPECTED_COMPONENTS, PinFileError, load_pin_rows

REPO_ROOT = Path(__file__).resolve().parents[2]
BUDGET_SECONDS = 1.5
PROBE_TIMEOUT_SECONDS = 0.25
_STABLE_VERSION = re.compile(r"^[0-9]+(?:\.[0-9]+){1,3}$")
_IPV4 = re.compile(r"^(?:\d{1,3}\.){3}\d{1,3}$")
_SENTINELS = frozenset({"absent", "unknown", "not_running", "differs", "missing"})
_MULTI = re.compile(
    r"^(?:restic|rclone) (?:absent|unknown|[0-9]+(?:\.[0-9]+){1,3})"
    r"(?:, (?:restic|rclone) (?:absent|unknown|[0-9]+(?:\.[0-9]+){1,3}))$"
)

# argv0 is a command name looked up on PATH, never a stored path.
COMMANDS: dict[str, tuple[str, ...]] = {
    "claude-code": ("claude", "--version"),
    "codex": ("codex", "--version"),
    "grok": ("grok", "--version"),
    "cursor-agent": ("cursor-agent", "--version"),
    "agy": ("agy", "--version"),
    "entire": ("entire", "--version"),
    "gh": ("gh", "--version"),
    "uv": ("uv", "--version"),
    "node": ("node", "--version"),
    "sqlite": ("sqlite3", "--version"),
    "postgresql": ("psql", "--version"),
    "prometheus": ("prometheus", "--version"),
    "grafana": ("grafana-server", "-v"),
    "alertmanager": ("alertmanager", "--version"),
}
PROCESS_COMM: dict[str, str] = {
    "claude-code": "claude",
    "codex": "codex",
    "grok": "grok",
    "cursor-agent": "cursor-agent",
    "agy": "agy",
    "entire": "entire",
    "gh": "gh",
    "uv": "uv",
    "python": "python",
    "node": "node",
    "sqlite": "sqlite3",
    "postgresql": "postgres",
    "prometheus": "prometheus",
    "grafana": "grafana-server",
    "alertmanager": "alertmanager",
}
MULTI_COMMANDS: dict[str, tuple[tuple[str, ...], ...]] = {
    "backup-restore": (("restic", "--version"), ("rclone", "--version")),
}


class DriftError(ValueError):
    """The private report could not be written. The message stays free of paths."""


@dataclass(frozen=True)
class Reading:
    installed: str
    running: str


def state_dir(env: Mapping[str, str] | None = None) -> Path:
    """``learn-ukrainian/stack-drift`` under the XDG state home."""
    source = os.environ if env is None else env
    configured = source.get("XDG_STATE_HOME", "")
    if configured and Path(configured).is_absolute():
        base = Path(configured)
    else:
        home = source.get("HOME", "")
        base = (Path(home).expanduser() if home else Path.home()) / ".local" / "state"
    return base / "learn-ukrainian" / "stack-drift"


def version_token(text: str) -> str:
    """First stable version token. Paths, URLs, and addresses are not versions."""
    for token in text.split():
        if any(mark in token for mark in ("/", ":", "@", "\\")):
            continue
        candidate = token[1:] if token.startswith("v") and len(token) > 1 and token[1].isdigit() else token
        candidate = candidate.rstrip(".,);")
        if _IPV4.fullmatch(candidate) or not _STABLE_VERSION.fullmatch(candidate):
            continue
        return candidate
    return "unknown"


def _store_probe(value: str) -> str:
    if value in _SENTINELS or _STABLE_VERSION.fullmatch(value) or _MULTI.fullmatch(value):
        return value
    return "unknown"


def _same_inode(left: Path, right: Path) -> bool | None:
    try:
        left_stat = left.stat()
        right_stat = right.stat()
    except OSError:
        return None
    return left_stat.st_ino == right_stat.st_ino and left_stat.st_dev == right_stat.st_dev


def running_label(installed: str, binary: Path | None, exes: list[Path]) -> str:
    """``installed`` when the running executable is that binary, else a sentinel."""
    if not exes:
        return "not_running"
    if binary is None:
        return "differs"
    saw_match = False
    for exe in exes:
        same = _same_inode(exe, binary)
        if same is False:
            return "differs"
        if same is True:
            saw_match = True
    if saw_match:
        return installed
    return "unknown"


_WATCHED_COMMS = frozenset({*PROCESS_COMM.values(), "restic", "rclone"})


def scan_processes() -> dict[str, list[Path]]:
    """One pass over process comm names. Paths stay in this process."""
    proc = Path("/proc")
    grouped: dict[str, list[Path]] = {}
    if not proc.is_dir():
        return grouped
    try:
        entries = list(proc.iterdir())
    except OSError:
        return grouped
    for entry in entries:
        if not entry.name.isdigit():
            continue
        try:
            name = (entry / "comm").read_text(encoding="utf-8", errors="replace").strip()
        except OSError:
            continue
        if name not in _WATCHED_COMMS and not name.startswith("python"):
            continue
        exe = entry / "exe"
        try:
            linked = exe.is_symlink()
        except OSError:
            continue
        if linked:
            grouped.setdefault(name, []).append(exe)
    return grouped


def exes_for_comm(grouped: dict[str, list[Path]], comm: str) -> list[Path]:
    if comm == "python":
        return [
            exe for name, paths in grouped.items() if name == "python" or name.startswith("python") for exe in paths
        ]
    return list(grouped.get(comm, ()))


def _probe_text(argv: tuple[str, ...], run: Callable[[tuple[str, ...]], str]) -> str:
    try:
        return run(argv)
    except Exception:
        return ""


def probe_component(
    name: str,
    *,
    which: Callable[[str], str | None],
    run: Callable[[tuple[str, ...]], str],
    exes_for: Callable[[str], list[Path]],
    python_version: str,
    python_executable: Path | None,
) -> Reading:
    """Installed and running versions for one component. No paths in the result."""
    if name == "python":
        installed = version_token(python_version)
        binary = python_executable
        running = running_label(installed, binary, exes_for("python"))
        if running == "not_running":
            running = installed
        return Reading(_store_probe(installed), _store_probe(running))

    multi = MULTI_COMMANDS.get(name)
    if multi is not None:
        parts: list[str] = []
        labels: list[str] = []
        for argv in multi:
            binary_text = which(argv[0])
            binary = Path(binary_text) if binary_text else None
            if binary is None:
                parts.append(f"{argv[0]} absent")
                labels.append(running_label("absent", None, exes_for(argv[0])))
                continue
            installed = version_token(_probe_text(argv, run))
            parts.append(f"{argv[0]} {installed}")
            labels.append(running_label(installed, binary, exes_for(argv[0])))
        installed_text = _store_probe(", ".join(parts))
        if "differs" in labels:
            running = "differs"
        elif "unknown" in labels:
            running = "unknown"
        elif all(label == "not_running" for label in labels):
            running = "not_running"
        else:
            running = installed_text
        return Reading(installed_text, _store_probe(running))

    argv = COMMANDS.get(name)
    if argv is None:
        return Reading("unknown", "unknown")
    binary_text = which(argv[0])
    binary = Path(binary_text) if binary_text else None
    installed = "absent" if binary is None else version_token(_probe_text(argv, run))
    running = running_label(installed, binary, exes_for(PROCESS_COMM.get(name, argv[0])))
    return Reading(_store_probe(installed), _store_probe(running))


def _default_run(argv: tuple[str, ...], deadline: float) -> str:
    remaining = deadline - time.monotonic()
    if remaining <= 0 or argv[0] != Path(argv[0]).name:
        return ""
    try:
        completed = subprocess.run(
            list(argv),
            capture_output=True,
            text=True,
            timeout=min(PROBE_TIMEOUT_SECONDS, remaining),
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return ""
    return f"{completed.stdout}\n{completed.stderr}"


def _assert_outside_repo(directory: Path, roots: tuple[Path, ...]) -> Path:
    resolved = directory.expanduser().resolve()
    for root in roots:
        root_resolved = root.resolve()
        if resolved == root_resolved or root_resolved in resolved.parents:
            raise DriftError("stack drift report must stay outside the repository")
    return resolved


def build_rows(pins_path: Path, read: Callable[[str], Reading]) -> list[dict[str, str]]:
    loaded = {row["name"]: row for row in load_pin_rows(pins_path)}
    rows: list[dict[str, str]] = []
    seen: set[str] = set()
    names = [*EXPECTED_COMPONENTS, *(name for name in loaded if name not in EXPECTED_COMPONENTS)]
    for name in names:
        if name in seen:
            continue
        seen.add(name)
        pin = loaded.get(name)
        pinned = "missing" if pin is None or pin["pinned"] == "missing" else pin["pinned"]
        try:
            reading = read(name)
        except Exception:
            reading = Reading("unknown", "unknown")
        rows.append(
            {
                "name": name,
                "pinned": pinned,
                "installed": _store_probe(reading.installed),
                "running": _store_probe(reading.running),
            }
        )
    return rows


def write_report(
    repo_root: Path,
    *,
    read: Callable[[str], Reading] | None = None,
    env: Mapping[str, str] | None = None,
) -> Path:
    """Write ``report.json`` under the private stack-drift directory."""
    directory = _assert_outside_repo(state_dir(env), (repo_root, REPO_ROOT))
    directory.mkdir(parents=True, exist_ok=True)
    directory.chmod(0o700)
    destination = directory / "report.json"
    pins_path = repo_root / "scripts" / "config" / "stack_pins.yaml"
    complete = True
    if read is None:
        scan_deadline = time.monotonic() + BUDGET_SECONDS
        grouped = scan_processes()

        def run(argv: tuple[str, ...]) -> str:
            return _default_run(argv, scan_deadline)

        def read(name: str) -> Reading:
            nonlocal complete
            if time.monotonic() >= scan_deadline:
                complete = False
                return Reading("unknown", "unknown")
            return probe_component(
                name,
                which=shutil.which,
                run=run,
                exes_for=lambda comm: exes_for_comm(grouped, comm),
                python_version=platform.python_version(),
                python_executable=Path(sys.executable),
            )

    try:
        rows = build_rows(pins_path, read)
        payload: dict[str, object] = {"schema": "stack-drift.v1", "complete": complete, "rows": rows}
    except PinFileError:
        payload = {"schema": "stack-drift.v1", "complete": complete, "rows": [], "error": "pins_unreadable"}
    text = json.dumps(payload, indent=2) + "\n"
    temporary = destination.with_suffix(".json.tmp")
    temporary.write_text(text, encoding="utf-8")
    os.chmod(temporary, 0o600)
    os.replace(temporary, destination)
    os.chmod(destination, 0o600)
    return destination


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Write installed, pinned, and running versions to the private stack-drift directory.\n"
            "Session start already runs this once. Do not schedule it, and do not publish the report."
        ),
        epilog=(
            "Examples:\n"
            "  .venv/bin/python -m scripts.ops.host_stack_drift\n"
            "  .venv/bin/python -m scripts.ops.host_stack_drift --repo-root .\n"
            "\n"
            "Outputs:\n"
            "  report.json under $XDG_STATE_HOME/learn-ukrainian/stack-drift "
            "(mode 0600). Versions only.\n"
            "  Stdout is one fixed line and does not include versions or paths.\n"
            "\n"
            "Exit codes:\n"
            "  0 when the private report is written, including when a probe is unknown.\n"
            "  1 when the report would land inside the repository or cannot be written.\n"
            "\n"
            "Related:\n"
            "  Pin file: scripts/config/stack_pins.yaml.\n"
            "  Policy: docs/best-practices/stack-currency.md section 2.\n"
            "  Caller: scripts/hooks/session_start_gate.py (#10862)."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=REPO_ROOT,
        help="checkout whose scripts/config/stack_pins.yaml is the pin source (default: this repo)",
    )
    args = parser.parse_args(argv)
    try:
        write_report(args.repo_root.resolve())
    except (DriftError, OSError):
        print("stack-drift report was not written")
        return 1
    print("stack-drift report written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
