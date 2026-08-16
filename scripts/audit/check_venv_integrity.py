#!/usr/bin/env python3
"""Primary-venv integrity probe: DETECT an empty/broken venv (#6830).

Follow-up to #6830 (#6818 comment). Two live incidents motivate this:

1. **Empty venv.** A mid-session `uv` venv rebuild (2026-08-15 18:47) left the
   primary `.venv` with no site-packages; every consumer (`ModuleNotFoundError:
   No module named 'yaml'`) failed until an operator ran
   ``uv pip install -r requirements.txt`` by hand. The restore itself then
   surfaced manifest debt: ``requirements.txt`` was missing ``psutil``,
   ``filelock``, and ``rapidfuzz`` (pulled in only transitively before), so a
   from-scratch reinstall from that file alone still left three modules
   missing (three ``TestVerifyQuoteHandler`` tests silently red).
2. **Broken console-script shebangs.** ``.venv/bin/pytest`` (and ``py.test``,
   ``cbor2``) use pip's long-path launcher trick — ``#!/bin/sh`` followed by
   a ``'''exec' '<python path>' "$0" "$@"`` line — and that embedded
   interpreter path pointed at a DELETED dispatch worktree's own venv
   (``.../.worktrees/dispatch/codex/465-.../.venv/bin/python3``). Verbatim
   ``pytest`` on the primary hard-fails while ``python -m pytest`` still
   works, because module invocation never execs the broken launcher script.
   Pollution class: some install/reinstall ran with ``sys.executable``
   resolving into a worktree venv instead of the primary one.

This module is DETECTION ONLY, mirroring ``check_primary_integrity.py`` /
``check_node_modules_integrity.py``'s posture:

- DETECT (a): a curated set of lightweight, always-required modules
  (``requirements.txt``'s non-ML core — deliberately excludes torch/
  sentence-transformers/qdrant-client, which are legitimately expensive to
  import and would make this unsuitable for a session-start hook) fail to
  import under the primary venv's own interpreter. One subprocess, not one
  per module — cheap (<1s warm) and catches "the venv is empty" as reliably
  as importing everything, without the heavy-ML import tax.
- DETECT (b): every non-symlink entry in ``.venv/bin/`` that is a pip
  console-script launcher (``#!`` first line) whose embedded interpreter path
  does not realpath-resolve to the SAME interpreter as the venv's own
  ``bin/python`` (a healthy venv's own ``bin/python`` is itself normally a
  symlink out to the base interpreter, so "inside the venv directory" is the
  wrong test — see ``find_broken_console_scripts``'s docstring).
- RECORD: every detection appends a JSONL event (mirrors the sibling
  watchdogs' RECORD contract) with the missing modules / broken scripts and
  the dispatches running at the time.
- ALERT ONLY, never repairs. Reinstalling packages or console scripts is a
  package-mutation, not a read, and the primary venv is off-limits to
  dispatch-worktree writes by convention — repair is an explicit operator
  action; this probe prints the command to run, it never runs it.

Usage::

    python scripts/audit/check_venv_integrity.py

Wire-up (matches ``check_node_modules_integrity``'s three call sites): the
``cmd_dispatch`` pre-dispatch gate, the post-worker sweep (both in
``scripts/delegate.py``), and the Monitor API health-orient canary
(``scripts/api/main.py``). Callers fail open on any probe exception —
consistent with the existing watchdogs, a probe bug must never itself block
or crash a dispatch.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


def _load_sibling(module_name: str, filename: str):
    """Load a sibling module by FILE PATH — see the identical helper (and its
    docstring explaining why) in ``check_node_modules_integrity.py``."""
    if module_name in sys.modules:
        return sys.modules[module_name]
    spec = importlib.util.spec_from_file_location(module_name, Path(__file__).resolve().parent / filename)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


_check_primary_integrity = _load_sibling("_venv_integrity_check_primary_integrity", "check_primary_integrity.py")
_append_event = _check_primary_integrity._append_event
_resolve_main_root = _check_primary_integrity._resolve_main_root
_running_dispatches = _check_primary_integrity._running_dispatches

# Lightweight, always-required modules from requirements.txt/requirements-dev.txt
# (import-name -> the distribution that declares it). Deliberately excludes
# torch, sentence-transformers, transformers, qdrant-client and other
# ML/network-heavy deps: importing those costs real seconds and would make
# this probe unfit for a session-start hook. This set exists to answer one
# question cheaply — "is site-packages populated at all" — which the
# 2026-08-15 incident (every import failing, starting with `yaml`) shows a
# handful of cheap sentinels answers just as reliably as importing everything.
CORE_SENTINEL_MODULES: dict[str, str] = {
    "yaml": "pyyaml",
    "jsonschema": "jsonschema",
    "fastapi": "fastapi",
    "uvicorn": "uvicorn",
    "httpx": "httpx",
    "ahocorasick": "pyahocorasick",
    "pymorphy3": "pymorphy3",
    "jinja2": "jinja2",
    "aiosqlite": "aiosqlite",
    "mcp": "mcp",
    "bs4": "beautifulsoup4",
    "requests": "requests",
    "pytest": "pytest",
    "ruff": "ruff",
    "psutil": "psutil",
    "filelock": "filelock",
    "rapidfuzz": "rapidfuzz",
    "ukrainian_word_stress": "ukrainian-word-stress",
    "zeroconf": "zeroconf",
}

# Console-script launcher name -> owning distribution, for the (rare) cases
# where they differ. Any script not listed here is assumed to share its
# distribution's name (true for the overwhelming majority of pip packages,
# e.g. `cbor2` -> `cbor2`).
_SCRIPT_PACKAGE_ALIASES: dict[str, str] = {"py.test": "pytest"}

# pip's long-path console-script launcher: `#!/bin/sh` followed by a
# tri-quoted `exec` line naming the real interpreter, so shells this long
# path length limit still find a working shebang. See PYTHONPATH/venv
# launcher docs; every modern pip build emits this form when the venv path
# is long enough that a direct `#!/abs/path/python` would overflow the
# kernel's shebang line limit (macOS default: 512 bytes).
_SHEBANG_EXEC_RE = re.compile(r"^'''exec' '(?P<path>[^']+)' \"\$0\" \"\$@\"$")


def _iter_console_scripts(bin_dir: Path):
    """Regular (non-symlink) files directly under a venv's ``bin/``.

    Skips the interpreter symlinks (``python``, ``python3``, ``python3.12``,
    …) — those are not pip console-script launchers, they're the venv's own
    interpreter identity and are checked separately by the primary-integrity
    watchdog's Python-version drift detection, not here.
    """
    if not bin_dir.is_dir():
        return
    for entry in sorted(bin_dir.iterdir()):
        if entry.is_symlink() or not entry.is_file():
            continue
        yield entry


def _extract_interpreter_path(script: Path) -> str | None:
    """The interpreter path a pip console-script launcher execs, or ``None``
    if ``script`` isn't a text launcher (binary tool, activation script,
    data file, …)."""
    try:
        with script.open(encoding="utf-8", errors="strict") as fh:
            first_line = fh.readline().rstrip("\n")
            if not first_line.startswith("#!"):
                return None
            shebang_target = first_line[2:].strip()
            if shebang_target != "/bin/sh":
                # Direct shebang: the interpreter path was short enough to
                # embed as-is (the common case for a short venv path).
                parts = shebang_target.split()
                return parts[0] if parts else None
            second_line = fh.readline().rstrip("\n")
    except (OSError, UnicodeDecodeError):
        return None
    match = _SHEBANG_EXEC_RE.match(second_line)
    return match.group("path") if match else None


def find_broken_console_scripts(venv_dir: Path) -> list[dict[str, Any]]:
    """Console-script launchers under ``venv_dir/bin`` whose embedded
    interpreter is not THIS venv's own interpreter.

    A healthy venv's ``bin/python`` is itself normally a symlink OUT to the
    base interpreter (pyenv, system, …) — so "resolves inside ``venv_dir``"
    is the wrong test; it would flag every launcher in a normal venv, since
    following any of them ends outside ``venv_dir`` too. The right invariant
    is identity with the venv's own interpreter: a launcher is healthy iff
    its embedded path's realpath equals ``venv_dir/bin/python``'s realpath —
    i.e. both ultimately name the same base interpreter. ``realpath`` works
    on a nonexistent path too (pure normalization, no symlink to follow), so
    a launcher pointing at a deleted venv still compares cleanly unequal.

    Returns a list of ``{"script", "interpreter", "exists"}`` dicts, one per
    offending launcher. Empty when every launcher agrees with the venv's own
    interpreter (the healthy case).
    """
    venv_python = Path(os.path.realpath(venv_dir / "bin" / "python"))
    broken: list[dict[str, Any]] = []
    for script in _iter_console_scripts(venv_dir / "bin"):
        interpreter = _extract_interpreter_path(script)
        if interpreter is None:
            continue
        interpreter_path = Path(interpreter)
        exists = interpreter_path.exists()
        resolved = Path(os.path.realpath(interpreter_path))
        if resolved != venv_python:
            broken.append({"script": script.name, "interpreter": interpreter, "exists": exists})
    return broken


def check_sentinel_imports(python_exe: Path, *, timeout: float = 30.0) -> tuple[list[str], str | None]:
    """Try importing every ``CORE_SENTINEL_MODULES`` key under ``python_exe``.

    One subprocess for the whole set (not one per module) — a cold Python
    start dominates the cost of importing any single lightweight module, so
    batching keeps this cheap. Returns ``(missing_modules, error)``; ``error``
    is set only when the probe itself couldn't run (interpreter missing,
    timed out, crashed) — that is also a venv-health signal, surfaced
    separately from "these specific modules are missing".
    """
    if not python_exe.exists():
        return [], f"interpreter does not exist: {python_exe}"
    probe = (
        "import importlib, json, sys\n"
        f"mods = {sorted(CORE_SENTINEL_MODULES)!r}\n"
        "missing = []\n"
        "for m in mods:\n"
        "    try:\n"
        "        importlib.import_module(m)\n"
        "    except Exception as exc:\n"
        "        missing.append(f'{m}: {type(exc).__name__}: {exc}')\n"
        "print(json.dumps(missing))\n"
    )
    try:
        proc = subprocess.run(
            [str(python_exe), "-c", probe],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return [], f"{type(exc).__name__}: {exc}"
    if proc.returncode != 0:
        return [], f"probe subprocess exited {proc.returncode}: {proc.stderr.strip()[-500:]}"
    try:
        return json.loads(proc.stdout.strip() or "[]"), None
    except json.JSONDecodeError as exc:
        return [], f"probe produced unparseable output: {exc}"


def check_venv_integrity(
    repo: Path,
    *,
    tasks_dir: Path | None = None,
    state_dir: Path | None = None,
    python_exe: Path | None = None,
) -> tuple[bool, str]:
    """Detect (never repair) an empty or shebang-broken primary venv.

    Returns ``(ok, message)``. ``ok`` is False when a sentinel module fails
    to import or a console-script launcher is broken; this is an ALERT
    signal only — callers must never block or auto-repair on it (repairing a
    venv is a package mutation, gated to an explicit operator command).
    """
    main_root = _resolve_main_root(Path(repo))
    venv_dir = main_root / ".venv"
    exe = python_exe or (venv_dir / "bin" / "python")
    sdir = state_dir or (main_root / "data" / "telemetry" / "venv-integrity")

    missing, probe_error = check_sentinel_imports(exe)
    broken_scripts = find_broken_console_scripts(venv_dir)

    if not missing and not probe_error and not broken_scripts:
        return True, f"venv integrity ok ({venv_dir})"

    evidence: dict[str, Any] = {
        "missing_modules": missing,
        "probe_error": probe_error,
        "broken_console_scripts": broken_scripts,
        "running_dispatches": _running_dispatches(tasks_dir),
        "venv_dir": str(venv_dir),
    }
    _append_event(sdir, "venv_integrity_alert", **evidence)

    reasons = []
    if probe_error:
        reasons.append(f"sentinel-import probe failed: {probe_error}")
    if missing:
        reasons.append(f"{len(missing)} sentinel module(s) fail to import: {'; '.join(missing)}")
    if broken_scripts:
        detail = ", ".join(f"{b['script']} -> {b['interpreter']}" for b in broken_scripts)
        packages = sorted({_SCRIPT_PACKAGE_ALIASES.get(b["script"], b["script"]) for b in broken_scripts})
        reasons.append(
            f"{len(broken_scripts)} console-script launcher(s) don't match the venv's own interpreter: "
            f"{detail}. Repair (operator-run, never automated against the primary): "
            f"{exe} -m pip install --force-reinstall {' '.join(packages)}"
        )
    return False, (
        f"ALERT: venv integrity issue(s) — {'; '.join(reasons)}. "
        f"NOT repaired (detection only); evidence preserved under {sdir}/events.jsonl."
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Detect an empty or shebang-broken primary venv (#6830).",
    )
    parser.add_argument("-q", "--quiet", action="store_true", help="suppress the OK message (alerts still print)")
    parser.add_argument(
        "--repo", type=Path, default=Path(__file__).resolve().parents[2], help="repo path to check (default: this project root)"
    )
    parser.add_argument(
        "--python-exe",
        type=Path,
        default=None,
        help="interpreter to run the sentinel-import probe under (default: <main_root>/.venv/bin/python)",
    )
    parser.add_argument(
        "--tasks-dir", type=Path, default=None, help="dispatch tasks dir for attribution (default: <root>/batch_state/tasks)"
    )
    parser.add_argument(
        "--state-dir",
        type=Path,
        default=None,
        help="watchdog state/log dir (default: <main_root>/data/telemetry/venv-integrity)",
    )
    args = parser.parse_args(argv)

    tasks_dir = args.tasks_dir
    if tasks_dir is None:
        try:
            tasks_dir = _resolve_main_root(args.repo) / "batch_state" / "tasks"
        except Exception:
            tasks_dir = None

    ok, message = check_venv_integrity(
        args.repo,
        tasks_dir=tasks_dir,
        state_dir=args.state_dir,
        python_exe=args.python_exe,
    )
    if not ok:
        print(f"❌ {message}", file=sys.stderr)
        return 1
    if not args.quiet:
        print(f"✅ {message}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
