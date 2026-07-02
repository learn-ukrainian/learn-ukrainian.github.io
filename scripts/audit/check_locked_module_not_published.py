#!/usr/bin/env python3
"""Block locked/todo/planned landing modules from being served as live MDX."""

from __future__ import annotations

import argparse
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DOCS_DIR = PROJECT_ROOT / "site" / "src" / "content" / "docs"

LANDING_DOC_TRACKS = {
    "a1",
    "a2",
    "b1",
    "b2",
    "b2-pro",
    "c1",
    "c1-pro",
    "c2",
    "bio",
    "folk",
    "hist",
    "istorio",
    "lit",
    "lit-crimea",
    "lit-doc",
    "lit-drama",
    "lit-essay",
    "lit-fantastika",
    "lit-hist-fic",
    "lit-humor",
    "lit-war",
    "lit-youth",
    "oes",
    "ruth",
}
NON_PUBLISHED_STATUSES = {"locked", "planned", "todo"}
MODULE_OBJECT_RE = re.compile(r"\{[^{}]*\}", re.DOTALL)
PROP_RE = re.compile(r"""\b(?P<name>slug|status)\s*:\s*["'](?P<value>[^"']+)["']""")
DRAFT_TRUE_RE = re.compile(r"^draft:\s*true\s*(?:#.*)?$", re.IGNORECASE)


@dataclass(frozen=True, order=True)
class ModuleStatus:
    track: str
    slug: str
    status: str
    index_path: Path
    line_no: int


@dataclass(frozen=True, order=True)
class ModuleTarget:
    track: str
    slug: str


@dataclass(frozen=True, order=True)
class CheckScope:
    tracks: frozenset[str]
    modules: frozenset[ModuleTarget]


@dataclass(frozen=True, order=True)
class Finding:
    module: ModuleStatus
    mdx_path: Path

    def format(self) -> str:
        module = self.module
        return (
            f"{display_path(self.mdx_path)}:1: {module.track}/{module.slug} is "
            f"{module.status!r} in {display_path(module.index_path)}:{module.line_no} "
            "but its MDX page is published; add draft: true or remove the page"
        )


def display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(PROJECT_ROOT.resolve()).as_posix()
    except ValueError:
        return str(path)


def _as_absolute_path(path: Path) -> Path:
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def _repo_relative(path: Path) -> Path | None:
    try:
        return _as_absolute_path(path).resolve().relative_to(PROJECT_ROOT.resolve())
    except ValueError:
        return None


def parse_landing_modules(index_path: Path, track: str) -> dict[str, ModuleStatus]:
    if not index_path.is_file():
        return {}

    text = index_path.read_text(encoding="utf-8")
    modules: dict[str, ModuleStatus] = {}
    for object_match in MODULE_OBJECT_RE.finditer(text):
        props = {match.group("name"): match.group("value") for match in PROP_RE.finditer(object_match.group(0))}
        slug = props.get("slug")
        status = props.get("status")
        if slug is None or status is None:
            continue
        modules[slug] = ModuleStatus(
            track=track,
            slug=slug,
            status=status,
            index_path=index_path,
            line_no=text.count("\n", 0, object_match.start()) + 1,
        )
    return modules


def has_draft_true(path: Path) -> bool:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        return False
    for line in lines[1:]:
        stripped = line.strip()
        if stripped == "---":
            return False
        if DRAFT_TRUE_RE.match(stripped):
            return True
    return False


def _module_path(docs_dir: Path, module: ModuleStatus | ModuleTarget) -> Path:
    return docs_dir / module.track / f"{module.slug}.mdx"


def _check_module(module: ModuleStatus, docs_dir: Path) -> Finding | None:
    if module.status not in NON_PUBLISHED_STATUSES:
        return None
    mdx_path = _module_path(docs_dir, module)
    if not mdx_path.is_file():
        return None
    if has_draft_true(mdx_path):
        return None
    return Finding(module=module, mdx_path=mdx_path)


def check_scope(scope: CheckScope, *, docs_dir: Path = DOCS_DIR) -> list[Finding]:
    findings_by_module: dict[tuple[str, str], Finding] = {}
    tracks = set(scope.tracks)
    tracks.update(module.track for module in scope.modules)

    modules_by_track = {
        track: parse_landing_modules(docs_dir / track / "index.mdx", track)
        for track in tracks
        if track in LANDING_DOC_TRACKS
    }

    for track in scope.tracks:
        for module in modules_by_track.get(track, {}).values():
            finding = _check_module(module, docs_dir)
            if finding is not None:
                findings_by_module[(module.track, module.slug)] = finding

    for target in scope.modules:
        module = modules_by_track.get(target.track, {}).get(target.slug)
        if module is None:
            continue
        finding = _check_module(module, docs_dir)
        if finding is not None:
            findings_by_module[(module.track, module.slug)] = finding

    return sorted(findings_by_module.values())


def affected_scope(paths: list[Path]) -> CheckScope:
    tracks: set[str] = set()
    modules: set[ModuleTarget] = set()

    for raw_path in paths:
        rel_path = _repo_relative(raw_path)
        if rel_path is None or rel_path.suffix.lower() != ".mdx":
            continue

        parts = rel_path.parts
        if len(parts) != 6 or parts[:4] != ("site", "src", "content", "docs"):
            continue

        track = parts[4]
        if track not in LANDING_DOC_TRACKS:
            continue
        if parts[5] == "index.mdx":
            tracks.add(track)
            continue
        modules.add(ModuleTarget(track=track, slug=Path(parts[5]).stem))

    return CheckScope(tracks=frozenset(tracks), modules=frozenset(modules))


def _git_output(args: list[str]) -> str:
    return subprocess.check_output(["git", *args], cwd=PROJECT_ROOT, text=True)


def get_changed_files(base: str) -> list[Path]:
    merge_base = _git_output(["merge-base", base, "HEAD"]).strip()
    output = _git_output(["diff", "--name-only", f"{merge_base}...HEAD"])
    return [PROJECT_ROOT / line for line in output.splitlines() if line]


def get_local_changed_files(*, cached: bool = False) -> list[Path]:
    cmd = ["diff", "--name-only"]
    if cached:
        cmd.append("--cached")
    output = _git_output(cmd)
    return [PROJECT_ROOT / line for line in output.splitlines() if line]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Check locked/todo/planned landing modules are not published.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--changed-vs-base", metavar="BASE", help="Compare against base branch, e.g. origin/main")
    group.add_argument("--files", nargs="+", type=Path, help="Scan explicit files, e.g. from pre-commit")
    group.add_argument("--all", action="store_true", help="Scan every known landing track.")
    return parser


def discover_scope(*, docs_dir: Path = DOCS_DIR) -> CheckScope:
    tracks = frozenset(
        path.parent.name
        for path in docs_dir.glob("*/index.mdx")
        if path.parent.name in LANDING_DOC_TRACKS
    )
    return CheckScope(tracks=tracks, modules=frozenset())


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.all:
        scope = discover_scope()
    elif args.changed_vs_base:
        raw_paths = [
            *get_changed_files(args.changed_vs_base),
            *get_local_changed_files(),
            *get_local_changed_files(cached=True),
        ]
        scope = affected_scope(raw_paths)
    else:
        raw_paths = args.files
        scope = affected_scope(raw_paths)
    if not scope.tracks and not scope.modules:
        print("0 findings: no landing docs require locked-module publish check.")
        return 0

    findings = check_scope(scope)
    if not findings:
        checked_count = len(scope.tracks) + len(scope.modules)
        print(f"0 findings: no locked/todo/planned modules published in {checked_count} changed scope(s).")
        return 0

    for finding in findings:
        print(finding.format())
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
