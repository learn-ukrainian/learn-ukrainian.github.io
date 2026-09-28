#!/usr/bin/env python3
"""Keep the host's jevgrep CLI at npm ``latest`` and sync its user-level skill (#9134).

Run by ``learn-ukrainian-jevgrep-update.timer`` from the primary checkout. It
resolves ``latest`` (or ``JEVGREP_HOLD_VERSION``) to an exact version, installs
it only when the release passes the supply-chain guards, verifies it, rolls
back on failure, then rebuilds the two user-level skill copies as the tracked
project overlay followed by the installed package's own upstream skill text.
Stdlib only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.request
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

PACKAGE = "@dzhng/jevgrep"
REGISTRY_URL = "https://registry.npmjs.org/@dzhng%2fjevgrep"
HOLD_ENV = "JEVGREP_HOLD_VERSION"
REPO_ROOT = Path(__file__).resolve().parents[2]
OVERLAY_REL = Path("agents_extensions/shared/skills/jevgrep/SKILL.md")
SKILL_TARGETS_REL = (
    Path(".claude/skills/jevgrep/SKILL.md"),
    Path(".agents/skills/jevgrep/SKILL.md"),
)
STATE_LOG_REL = Path(".local/state/learn-ukrainian/jevgrep-update.jsonl")
UPSTREAM_SKILL_REL = Path("dist/skills/jevgrep/SKILL.md")
FORBIDDEN_SCRIPTS = ("preinstall", "install", "postinstall")
VERSION_RE = re.compile(r"\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?")
INSTALL_TIMEOUT_S = 900
DOCTOR_TIMEOUT_S = 180
VERSION_TIMEOUT_S = 30

Runner = Callable[[list[str], int], subprocess.CompletedProcess[str]]


def _run(cmd: list[str], timeout: int) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=timeout)


def _fetch_packument() -> dict[str, Any]:
    request = urllib.request.Request(
        REGISTRY_URL, headers={"Accept": "application/json", "User-Agent": "learn-ukrainian-jevgrep-update"}
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def _package_dir() -> Path | None:
    """Return the installed package directory by following the ``jg`` bin link."""
    binary = shutil.which("jg")
    if binary is None:
        return None
    for parent in Path(binary).resolve().parents:
        manifest = parent / "package.json"
        if manifest.is_file():
            try:
                if json.loads(manifest.read_text(encoding="utf-8")).get("name") == PACKAGE:
                    return parent
            except (OSError, ValueError):
                return None
    return None


def _utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


@dataclass
class Deps:
    home: Path = field(default_factory=Path.home)
    run: Runner = _run
    fetch_packument: Callable[[], dict[str, Any]] = _fetch_packument
    package_dir: Callable[[], Path | None] = _package_dir
    repo_root: Path = REPO_ROOT
    environ: Mapping[str, str] = field(default_factory=lambda: os.environ)
    now: Callable[[], str] = _utc_now


def _call(deps: Deps, cmd: list[str], timeout: int) -> tuple[int, str]:
    try:
        result = deps.run(cmd, timeout)
    except OSError as exc:
        return 127, str(exc)
    except subprocess.TimeoutExpired:
        return 124, f"timed out after {timeout}s"
    return result.returncode, (result.stdout or "") + (result.stderr or "")


def _tail(text: str, limit: int = 300) -> str:
    return " ".join(text.split())[-limit:]


def installed_version(deps: Deps) -> str | None:
    code, output = _call(deps, ["jg", "--version"], VERSION_TIMEOUT_S)
    match = VERSION_RE.search(output) if code == 0 else None
    return match.group(0) if match else None


def resolve_target(packument: Mapping[str, Any], environ: Mapping[str, str]) -> str:
    target = environ.get(HOLD_ENV, "").strip() or packument["dist-tags"]["latest"]
    if not isinstance(target, str) or not VERSION_RE.fullmatch(target):
        raise ValueError(f"target is not an exact version: {target!r}")
    return target


def guard_failures(packument: Mapping[str, Any], version: str) -> list[str]:
    meta = packument.get("versions", {}).get(version)
    if not isinstance(meta, dict):
        return [f"{version} is not in the registry"]
    failures = []
    if not meta.get("dist", {}).get("attestations"):
        failures.append("no npm provenance attestations")
    scripts = meta.get("scripts") or {}
    failures.extend(f"install script {name!r} present" for name in FORBIDDEN_SCRIPTS if name in scripts)
    if meta.get("hasInstallScript"):
        failures.append("registry marks hasInstallScript")
    bins = meta.get("bin")
    if not isinstance(bins, dict) or not bins.get("jg"):
        failures.append("bin.jg missing")
    return failures


def _npm_install(deps: Deps, version: str) -> str | None:
    cmd = ["npm", "install", "-g", "--ignore-scripts", "--no-audit", "--no-fund", f"{PACKAGE}@{version}"]
    code, output = _call(deps, cmd, INSTALL_TIMEOUT_S)
    return None if code == 0 else f"npm install {version} exit {code}: {_tail(output)}"


def install_and_verify(deps: Deps, version: str) -> str | None:
    """Install one exact version; return an error message, or None when verified."""
    error = _npm_install(deps, version)
    if error:
        return error
    found = installed_version(deps)
    if found != version:
        return f"jg --version reports {found!r}, expected {version!r}"
    code, output = _call(deps, ["jg", "doctor"], DOCTOR_TIMEOUT_S)
    return None if code == 0 else f"jg doctor exit {code}: {_tail(output)}"


def _strip_frontmatter(text: str) -> str:
    if text.startswith("---\n"):
        end = text.find("\n---\n", 4)
        if end != -1:
            return text[end + len("\n---\n") :]
    return text


def compose_skill(overlay: str, upstream: str, version: str) -> str:
    if not overlay.endswith("\n"):
        overlay += "\n"
    marker = f"\n## Upstream skill (auto-synced from {PACKAGE} {version}, overlay above wins)\n"
    return overlay + marker + _strip_frontmatter(upstream)


def _atomic_write(target: Path, content: str) -> None:
    if target.parent.is_symlink():
        raise OSError(f"refusing symlinked skill directory: {target.parent}")
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=target.parent, prefix=".SKILL.md.")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(content)
        os.chmod(tmp_name, 0o644)
        os.replace(tmp_name, target)
    except BaseException:
        Path(tmp_name).unlink(missing_ok=True)
        raise


def sync_skills(deps: Deps, version: str) -> str:
    """Write overlay + upstream body to the two user-level skill paths; return the upstream sha256."""
    package = deps.package_dir()
    if package is None:
        raise OSError("installed jevgrep package not found")
    package_version = json.loads((package / "package.json").read_text(encoding="utf-8")).get("version")
    if package_version != version:
        raise OSError(f"package.json version {package_version!r} does not match jg --version {version!r}")
    upstream = (package / UPSTREAM_SKILL_REL).read_text(encoding="utf-8")
    overlay = (deps.repo_root / OVERLAY_REL).read_text(encoding="utf-8")
    content = compose_skill(overlay, upstream, version)
    for rel in SKILL_TARGETS_REL:
        target = deps.home / rel
        if not (target.is_file() and target.read_text(encoding="utf-8") == content):
            _atomic_write(target, content)
    return hashlib.sha256(upstream.encode("utf-8")).hexdigest()


def update(deps: Deps, *, dry_run: bool = False) -> tuple[int, dict[str, Any]]:
    current = installed_version(deps)
    record: dict[str, Any] = {
        "time": deps.now(),
        "current": current,
        "target": None,
        "action": None,
        "result": None,
        "upstream_skill_sha256": None,
        "detail": None,
    }
    if dry_run:
        record["dry_run"] = True
    exit_code = 0
    try:
        packument = deps.fetch_packument()
        target = resolve_target(packument, deps.environ)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        record.update(action="resolve", result="failed", detail=f"cannot resolve target: {exc}")
        exit_code = 1
    else:
        record["target"] = target
        if target == current:
            record.update(action="none", result="ok")
        elif failures := guard_failures(packument, target):
            record.update(action="blocked", result="failed", detail="; ".join(failures))
            exit_code = 1
        elif dry_run:
            record.update(action="install", result="dry_run")
        else:
            record["action"] = "install"
            error = install_and_verify(deps, target)
            if error is None:
                record["result"] = "ok"
            else:
                exit_code = 1
                record["detail"] = error
                record["result"] = "failed"
                if current is not None:
                    rollback_error = _npm_install(deps, current)
                    restored = installed_version(deps) == current
                    record["result"] = "rolled_back" if rollback_error is None and restored else "rollback_failed"
                    if record["result"] == "rollback_failed":
                        record["detail"] += f"; rollback to {current} failed: {rollback_error or 'version mismatch'}"
    if dry_run:
        return exit_code, record

    installed = installed_version(deps)
    if installed is None:
        record["detail"] = "; ".join(filter(None, [record["detail"], "jg not installed; skill not synced"]))
    else:
        try:
            record["upstream_skill_sha256"] = sync_skills(deps, installed)
        except (OSError, ValueError) as exc:
            record["detail"] = "; ".join(filter(None, [record["detail"], f"skill sync failed: {exc}"]))
            exit_code = 1
    log_path = deps.home / STATE_LOG_REL
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")
    return exit_code, record


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Keep the host's jevgrep CLI (@dzhng/jevgrep, bin jg) at npm latest and sync the user-level skill.\n"
            "Run by the learn-ukrainian-jevgrep-update timer; operators may run it by hand. Agents never run it."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  .venv/bin/python scripts/tools/jevgrep_update.py --dry-run --json\n"
            "  .venv/bin/python scripts/tools/jevgrep_update.py\n"
            f"  {HOLD_ENV}=0.4.4 .venv/bin/python scripts/tools/jevgrep_update.py   # pin temporarily\n"
            "\n"
            "Guards: the target release must carry npm provenance attestations, have no\n"
            "preinstall/install/postinstall script, and declare bin.jg. It is installed as an exact\n"
            "version with --ignore-scripts, then `jg --version` and `jg doctor` must pass, else the\n"
            "previous version is reinstalled.\n"
            "\n"
            "Outputs: global npm install of the exact version; ~/.claude/skills/jevgrep/SKILL.md and\n"
            "~/.agents/skills/jevgrep/SKILL.md (tracked overlay + installed upstream skill body);\n"
            f"one JSON line appended to ~/{STATE_LOG_REL}. --dry-run writes nothing.\n"
            "Exit codes: 0 up to date or updated and synced; 1 guard, install, verify, registry or\n"
            "sync failure (the previous version is kept); 2 invalid arguments.\n"
            "Related: agents_extensions/shared/skills/jevgrep/UPSTREAM.md, "
            "packaging/systemd/learn-ukrainian-jevgrep-update.{service,timer}, issue #9134."
        ),
    )
    parser.add_argument(
        "--json", action="store_true", help="Print the run record as JSON (default: one human-readable line)."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Resolve the target and check the guards only; no install, no skill writes, no state-log line.",
    )
    return parser


def main(argv: list[str] | None = None, deps: Deps | None = None) -> int:
    args = build_parser().parse_args(argv)
    exit_code, record = update(deps or Deps(), dry_run=args.dry_run)
    if args.json:
        print(json.dumps(record, sort_keys=True))
    else:
        line = f"jevgrep: current={record['current']} target={record['target']} action={record['action']} "
        line += f"result={record['result']}"
        if record["detail"]:
            line += f" detail={record['detail']}"
        print(line)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
