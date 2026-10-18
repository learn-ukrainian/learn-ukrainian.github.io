"""Installed versus pinned versus running, written to private local state (#10862).

Session start calls ``write_report`` once. The report lives under
``$XDG_STATE_HOME/learn-ukrainian/stack-drift`` (or
``~/.local/state/learn-ukrainian/stack-drift``). It records versions only.
Command output that is not a version is dropped, and the report is refused
if its resolved path is inside the session checkout or the canonical repository.

There is no timer. The weekly audit publishes pinned-versus-latest; this
check does not.

The report file is replaced from a temp name created with ``O_EXCL``. A
symlink or extra hard link at the destination is refused, and so is a state
directory whose real path sits inside a git checkout or worktree.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import re
import secrets
import shutil
import stat
import subprocess
import sys
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path

from scripts.ci.stack_currency_report import (
    PinFileError,
    load_pin_rows,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
BUDGET_SECONDS = 1.5
PROBE_TIMEOUT_SECONDS = 0.25
_PREDICTABLE_TEMP = "report.json.tmp"
_STABLE_VERSION = re.compile(r"^[0-9]+(?:\.[0-9]+){1,3}$")
_IPV4 = re.compile(r"^(?:\d{1,3}\.){3}\d{1,3}$")
_SENTINELS = frozenset({"absent", "unknown", "not_running", "differs", "missing"})
_MULTI = re.compile(
    r"^(?:restic|rclone) (?:absent|unknown|[0-9]+(?:\.[0-9]+){1,3})"
    r"(?:, (?:restic|rclone) (?:absent|unknown|[0-9]+(?:\.[0-9]+){1,3}))$"
)


# argv, process comm. Command names are PATH lookups, never stored paths.
_PROBES: dict[str, tuple[tuple[str, ...], str]] = {
    "claude-code": (("claude", "--version"), "claude"),
    "codex": (("codex", "--version"), "codex"),
    "grok": (("grok", "--version"), "grok"),
    "cursor-agent": (("cursor-agent", "--version"), "cursor-agent"),
    "agy": (("agy", "--version"), "agy"),
    "entire": (("entire", "--version"), "entire"),
    "gh": (("gh", "--version"), "gh"),
    "uv": (("uv", "--version"), "uv"),
    "node": (("node", "--version"), "node"),
    "sqlite": (("sqlite3", "--version"), "sqlite3"),
    "postgresql": (("psql", "--version"), "postgres"),
    "prometheus": (("prometheus", "--version"), "prometheus"),
    "grafana": (("grafana-server", "-v"), "grafana-server"),
    "alertmanager": (("alertmanager", "--version"), "alertmanager"),
}
_MULTI_PROBES: dict[str, tuple[tuple[str, ...], ...]] = {
    "backup-restore": (("restic", "--version"), ("rclone", "--version")),
}


def probe_spec(name: str) -> tuple[tuple[str, ...], str] | None:
    """``(argv, process comm)`` for one local command, or None."""
    return _PROBES.get(name)


def multi_argv(name: str) -> tuple[tuple[str, ...], ...] | None:
    return _MULTI_PROBES.get(name)


def watched_comms(names: tuple[str, ...] | list[str] = ()) -> frozenset[str]:
    """Process comm names worth a private drift scan. Built from probes, not paths."""
    comms = {comm for _argv, comm in _PROBES.values()}
    comms.add("python")
    for argv_rows in _MULTI_PROBES.values():
        comms.update(argv[0] for argv in argv_rows)
    for name in names:
        spec = probe_spec(name)
        if spec is not None:
            comms.add(spec[1])
    return frozenset(comms)


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


def scan_processes(watched: frozenset[str]) -> dict[str, list[Path]]:
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
        if name not in watched and not name.startswith("python"):
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

    multi = multi_argv(name)
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

    spec = probe_spec(name)
    if spec is None:
        return Reading("unknown", "unknown")
    argv, comm = spec
    binary_text = which(argv[0])
    binary = Path(binary_text) if binary_text else None
    installed = "absent" if binary is None else version_token(_probe_text(argv, run))
    running = running_label(installed, binary, exes_for(comm))
    return Reading(_store_probe(installed), _store_probe(running))


def _default_run(argv: tuple[str, ...], deadline: float) -> str:
    remaining = deadline - time.monotonic()
    if remaining <= 0 or argv[0] != Path(argv[0]).name:
        return ""
    try:
        timeout = min(PROBE_TIMEOUT_SECONDS, remaining)
        match argv:
            case ("claude", "--version"):
                completed = subprocess.run(
                    ["claude", "--version"], capture_output=True, text=True, timeout=timeout, check=False
                )
            case ("codex", "--version"):
                completed = subprocess.run(
                    ["codex", "--version"], capture_output=True, text=True, timeout=timeout, check=False
                )
            case ("grok", "--version"):
                completed = subprocess.run(
                    ["grok", "--version"], capture_output=True, text=True, timeout=timeout, check=False
                )
            case ("cursor-agent", "--version"):
                completed = subprocess.run(
                    ["cursor-agent", "--version"], capture_output=True, text=True, timeout=timeout, check=False
                )
            case ("agy", "--version"):
                completed = subprocess.run(
                    ["agy", "--version"], capture_output=True, text=True, timeout=timeout, check=False
                )
            case ("entire", "--version"):
                completed = subprocess.run(
                    ["entire", "--version"], capture_output=True, text=True, timeout=timeout, check=False
                )
            case ("gh", "--version"):
                completed = subprocess.run(
                    ["gh", "--version"], capture_output=True, text=True, timeout=timeout, check=False
                )
            case ("uv", "--version"):
                completed = subprocess.run(
                    ["uv", "--version"], capture_output=True, text=True, timeout=timeout, check=False
                )
            case ("node", "--version"):
                completed = subprocess.run(
                    ["node", "--version"], capture_output=True, text=True, timeout=timeout, check=False
                )
            case ("sqlite3", "--version"):
                completed = subprocess.run(
                    ["sqlite3", "--version"], capture_output=True, text=True, timeout=timeout, check=False
                )
            case ("psql", "--version"):
                completed = subprocess.run(
                    ["psql", "--version"], capture_output=True, text=True, timeout=timeout, check=False
                )
            case ("prometheus", "--version"):
                completed = subprocess.run(
                    ["prometheus", "--version"], capture_output=True, text=True, timeout=timeout, check=False
                )
            case ("grafana-server", "-v"):
                completed = subprocess.run(
                    ["grafana-server", "-v"], capture_output=True, text=True, timeout=timeout, check=False
                )
            case ("alertmanager", "--version"):
                completed = subprocess.run(
                    ["alertmanager", "--version"], capture_output=True, text=True, timeout=timeout, check=False
                )
            case ("restic", "--version"):
                completed = subprocess.run(
                    ["restic", "--version"], capture_output=True, text=True, timeout=timeout, check=False
                )
            case ("rclone", "--version"):
                completed = subprocess.run(
                    ["rclone", "--version"], capture_output=True, text=True, timeout=timeout, check=False
                )
            case _:
                return ""
    except (OSError, subprocess.TimeoutExpired):
        return ""
    return f"{completed.stdout}\n{completed.stderr}"


def _assert_outside_repo(directory: Path, roots: tuple[Path, ...]) -> Path:
    """Resolved destination. A symlink into any root is the same refusal."""
    resolved = directory.expanduser().resolve()
    for root in roots:
        root_resolved = root.expanduser().resolve()
        if resolved == root_resolved or root_resolved in resolved.parents:
            raise DriftError("stack drift report must stay outside the repository")
    return resolved


def _assert_not_inside_git(directory: Path) -> None:
    """Refuse a real path inside any checkout or linked worktree.

    ``directory`` is already resolved. A ``.git`` directory marks a checkout.
    A ``.git`` file marks a linked worktree. ``lstat`` does not follow either.
    """
    for parent in (directory, *directory.parents):
        marker = parent / ".git"
        try:
            marker.lstat()
        except FileNotFoundError:
            continue
        except OSError as exc:
            raise DriftError("stack drift report must stay outside the repository") from exc
        raise DriftError("stack drift report must stay outside the repository")


def _refuse_linked_file(path: Path) -> None:
    """Refuse a symlink or a file with another hard link. Missing is allowed.

    ``lstat`` does not open the path and does not follow a symlink.
    """
    try:
        info = path.lstat()
    except FileNotFoundError:
        return
    except OSError as exc:
        raise DriftError("stack drift report could not be written") from exc
    if stat.S_ISLNK(info.st_mode) or info.st_nlink > 1:
        raise DriftError("stack drift report must stay a private file")


def _write_new_file(directory: Path, destination: Path, text: str) -> None:
    """Write ``text`` to a new temp file in ``directory``, then replace ``destination``.

    A random name is created with ``O_EXCL``. ``report.json.tmp`` and any
    other pre-existing path are not opened.
    """
    temporary = directory / f".report-{secrets.token_hex(16)}.tmp"
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(text.encode("utf-8"))
            stream.flush()
            os.fsync(stream.fileno())
            os.fchmod(stream.fileno(), 0o600)
        os.replace(temporary, destination)
    except OSError:
        temporary.unlink(missing_ok=True)
        raise
    os.chmod(destination, 0o600)


def build_rows(pins_path: Path, read: Callable[[str], Reading]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for pin in load_pin_rows(pins_path):
        if pin["pinned"] == "missing":
            rows.append({"name": pin["name"], "pinned": "missing", "installed": "unknown", "running": "unknown"})
            continue
        try:
            reading = read(pin["name"])
        except Exception:
            reading = Reading("unknown", "unknown")
        rows.append(
            {
                "name": pin["name"],
                "pinned": pin["pinned"],
                "installed": _store_probe(reading.installed),
                "running": _store_probe(reading.running),
            }
        )
    return rows


def write_report(
    repo_root: Path,
    *,
    canonical_root: Path | None = None,
    read: Callable[[str], Reading] | None = None,
    env: Mapping[str, str] | None = None,
) -> Path:
    """Write ``report.json`` outside the session checkout and the canonical repository."""
    roots = (repo_root, REPO_ROOT)
    if canonical_root is not None:
        roots = (*roots, canonical_root)
    directory = _assert_outside_repo(state_dir(env), roots)
    _assert_not_inside_git(directory)
    directory.mkdir(parents=True, exist_ok=True)
    directory.chmod(0o700)
    destination = directory / "report.json"
    _refuse_linked_file(destination)
    _refuse_linked_file(directory / _PREDICTABLE_TEMP)
    pins_path = repo_root / "scripts" / "config" / "stack_pins.yaml"
    complete = True
    if read is None:
        scan_deadline = time.monotonic() + BUDGET_SECONDS
        try:
            pin_names = [row["name"] for row in load_pin_rows(pins_path)]
        except PinFileError:
            pin_names = []
        grouped = scan_processes(watched_comms(pin_names))

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
    _write_new_file(directory, destination, text)
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
