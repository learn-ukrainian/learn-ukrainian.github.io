#!/usr/bin/env python3
"""Scan public pull-request text for infrastructure leaks.

The file scanner does not see a pull request title, body, branch name, or
commit message. This command scans those four surfaces with the same home-path
needles and the same IP and credential rules as the repository OPSEC lint.
It prints the field, the rule, and the line number. It does not print the
matched text.

Examples:
  PR_TITLE=... PR_BODY=... PR_BRANCH=... \\
    .venv/bin/python scripts/audit/lint_public_surfaces.py --base <sha> --head <sha>

Outputs: one "field rule line" row per finding on stdout. Writes nothing.
Exit codes: 0 when every supplied surface is clean, 1 when a surface is
flagged or git cannot be read.
Related: scripts/audit/lint_opsec_leaks.py, scripts/opsec/needles.py.
"""

from __future__ import annotations

import argparse
import importlib.util
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

_HERE = Path(__file__).resolve().parent


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path.name}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


_leaks = _load("_lu_opsec_leaks", _HERE / "lint_opsec_leaks.py")
_needles = _load("_lu_opsec_needles", _HERE.parent / "opsec" / "needles.py")
surface_infrastructure_rules = _leaks.surface_infrastructure_rules
Needles = _needles.Needles
home_dir_pattern = _needles.home_dir_pattern
load_needles = _needles.load_needles

_FILE_URI = re.compile(r"file://", re.IGNORECASE)
_PRIVATE_HOST = re.compile(
    r"\b(?:[a-z0-9-]+\.)+(?:local|internal|lan|localdomain|home\.arpa)\b",
    re.IGNORECASE,
)
_GIT_TIMEOUT_SECONDS = 30.0


@dataclass(frozen=True)
class SurfaceFinding:
    field: str
    rule: str
    line: int


def scan_text(text: str, *, field: str, needles: Needles | None = None) -> list[SurfaceFinding]:
    """Return findings for one surface. ``needles`` defaults to the configured file."""
    if not text:
        return []
    loaded = load_needles() if needles is None else needles
    home = re.compile(home_dir_pattern(loaded))
    findings: list[SurfaceFinding] = []
    lines = text.splitlines() or [text]
    for number, line in enumerate(lines, 1):
        if home.search(line):
            findings.append(SurfaceFinding(field, "host-path", number))
        if _FILE_URI.search(line):
            findings.append(SurfaceFinding(field, "file-uri", number))
        if _PRIVATE_HOST.search(line):
            findings.append(SurfaceFinding(field, "private-host", number))
    findings.extend(
        SurfaceFinding(field, rule, line) for line, rule in surface_infrastructure_rules(text)
    )
    return findings


def commit_message_text(base: str, head: str) -> str:
    """Return commit messages reachable from ``head`` and not from ``base``."""
    result = subprocess.run(
        ["git", "log", "--format=%B%x1e", f"{base}..{head}"],
        check=True,
        capture_output=True,
        text=True,
        timeout=_GIT_TIMEOUT_SECONDS,
    )
    return result.stdout


def render(findings: list[SurfaceFinding]) -> str:
    return "\n".join(f"{item.field} {item.rule} line={item.line}" for item in findings)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--title-env", default="PR_TITLE", help="Environment variable holding the title.")
    parser.add_argument("--body-env", default="PR_BODY", help="Environment variable holding the body.")
    parser.add_argument("--branch-env", default="PR_BRANCH", help="Environment variable holding the branch name.")
    parser.add_argument("--base", default="", help="Base commit for the commit-message range. Omit to skip commits.")
    parser.add_argument("--head", default="", help="Head commit for the commit-message range.")
    args = parser.parse_args(argv)

    surfaces: list[tuple[str, str]] = [
        ("title", os.environ.get(args.title_env, "")),
        ("body", os.environ.get(args.body_env, "")),
        ("branch", os.environ.get(args.branch_env, "")),
    ]
    if bool(args.base) != bool(args.head):
        print("OPSEC publication surfaces: pass both --base and --head, or neither.", file=sys.stderr)
        return 1
    if args.base and args.head:
        try:
            surfaces.append(("commit", commit_message_text(args.base, args.head)))
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
            print(f"OPSEC publication surfaces: git log failed ({type(exc).__name__}).", file=sys.stderr)
            return 1

    findings: list[SurfaceFinding] = []
    for field, text in surfaces:
        findings.extend(scan_text(text, field=field))
    if findings:
        print(render(findings))
        print(f"OPSEC publication surfaces blocked: {len(findings)} finding(s).", file=sys.stderr)
        return 1
    print("OPSEC publication surfaces clean.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
