#!/usr/bin/env python3
"""Check changed seminar modules against the pre-promote quality gate."""

from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
import types
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.common.thresholds import seminar_promote_floors_for
from scripts.pipeline.module_archetypes import SEMINAR_TRACKS


def _load_wiki_completeness_gate() -> None:
    module_name = "scripts.audit.wiki_completeness_gate"
    if module_name in sys.modules:
        return
    if "scripts.audit" not in sys.modules:
        audit_package = types.ModuleType("scripts.audit")
        audit_package.__path__ = [str(PROJECT_ROOT / "scripts" / "audit")]
        sys.modules["scripts.audit"] = audit_package
    spec = importlib.util.spec_from_file_location(
        module_name,
        PROJECT_ROOT / "scripts" / "audit" / "wiki_completeness_gate.py",
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load wiki completeness gate")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)


_load_wiki_completeness_gate()
from scripts.build.promote_quality_gate import verify

LESSON_SOURCE_FILES = frozenset(
    {
        "module.md",
        "activities.yaml",
        "vocabulary.yaml",
        "resources.yaml",
    }
)
PROMOTE_QUALITY_FILE = "promote_quality.json"


@dataclass(frozen=True, order=True)
class ModuleTarget:
    track: str
    slug: str


def _is_seminar_track(track: str) -> bool:
    return track in SEMINAR_TRACKS or seminar_promote_floors_for(track) is not None


def _is_deployed_lesson(repo_root: Path, track: str, slug: str) -> bool:
    return (
        repo_root
        / "site"
        / "src"
        / "content"
        / "docs"
        / track
        / f"{slug}.mdx"
    ).exists()


def _repo_relative_path(raw_path: str, repo_root: Path) -> PurePosixPath | None:
    path = Path(raw_path)
    if path.is_absolute():
        try:
            path = path.resolve().relative_to(repo_root.resolve())
        except ValueError:
            return None
    return PurePosixPath(path.as_posix())


def target_from_changed_path(raw_path: str, repo_root: Path) -> ModuleTarget | None:
    rel = _repo_relative_path(raw_path, repo_root)
    if rel is None:
        return None

    parts = rel.parts
    if (
        len(parts) == 6
        and parts[:4] == ("site", "src", "content", "docs")
        and parts[5].endswith(".mdx")
    ):
        track = parts[4].casefold()
        slug = PurePosixPath(parts[5]).stem
        if slug != "index" and _is_seminar_track(track):
            return ModuleTarget(track, slug)
        return None

    if len(parts) == 5 and parts[:2] == ("curriculum", "l2-uk-en"):
        track = parts[2].casefold()
        slug = parts[3]
        filename = parts[4]
        if (
            _is_seminar_track(track)
            and filename in (LESSON_SOURCE_FILES | {PROMOTE_QUALITY_FILE})
            and _is_deployed_lesson(repo_root, track, slug)
        ):
            return ModuleTarget(track, slug)

    return None


def changed_paths_from_git(repo_root: Path, base: str) -> list[str]:
    proc = subprocess.run(
        [
            "git",
            "diff",
            "--diff-filter=AMR",
            "--name-only",
            f"{base}...HEAD",
        ],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        if proc.stderr:
            print(proc.stderr.strip(), file=sys.stderr)
        raise SystemExit(proc.returncode)
    return [line for line in proc.stdout.splitlines() if line]


def collect_targets(changed_paths: list[str], repo_root: Path) -> list[ModuleTarget]:
    targets = {
        target
        for path in changed_paths
        if (target := target_from_changed_path(path, repo_root)) is not None
    }
    return sorted(targets)


def _format_score(value: Any) -> str:
    if value is None:
        return "missing"
    try:
        return f"{float(value):g}"
    except (TypeError, ValueError):
        return str(value)


def _print_report(target: ModuleTarget, report: dict[str, Any]) -> None:
    if not report["applicable"]:
        print(f"NOTICE: {target.track}/{target.slug} not enrolled -- advisory only")
        return

    status = "PASS" if report["passed"] else "FAIL"
    print(f"{status}: {target.track}/{target.slug}: {report['reason']}")
    for row in report.get("per_dim", []):
        outcome = "ok" if row.get("ok") else "fail"
        print(
            f"  - {row['dim']}: {_format_score(row.get('score'))} >= "
            f"{float(row['floor']):g} ({outcome})"
        )
    if not report["passed"]:
        for failure in report.get("failures", []):
            print(f"  - {failure}")


def run(changed_paths: list[str], *, repo_root: Path, emit_json: bool) -> int:
    targets = collect_targets(changed_paths, repo_root)
    results: list[dict[str, Any]] = []
    enrolled_failures: list[ModuleTarget] = []

    for target in targets:
        floors = seminar_promote_floors_for(target.track)
        report = verify(target.track, target.slug, repo_root=repo_root)
        if floors is None and report["applicable"]:
            report = {
                **report,
                "applicable": False,
                "passed": True,
                "reason": "track not enrolled in pre-promote gate",
                "failures": [],
            }
        if report["applicable"] and not report["passed"]:
            enrolled_failures.append(target)
        if not emit_json:
            _print_report(target, report)
        results.append(
            {
                "track": target.track,
                "slug": target.slug,
                "applicable": report["applicable"],
                "passed": report["passed"],
                "reason": report["reason"],
                "failures": report.get("failures", []),
                "per_dim": report.get("per_dim", []),
            }
        )

    summary = {
        "checked": len(targets),
        "enrolled_failures": len(enrolled_failures),
        "passed": not enrolled_failures,
        "results": results,
    }
    if emit_json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(
            "SUMMARY: promote-quality checked "
            f"{len(targets)} gated seminar module(s); "
            f"enrolled_failures={len(enrolled_failures)}"
        )
    return 1 if enrolled_failures else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--base",
        default="origin/main",
        help="Base ref for changed-file detection",
    )
    parser.add_argument(
        "--changed",
        action="store_true",
        help="Check files changed against --base...HEAD",
    )
    parser.add_argument(
        "--changed-file",
        action="append",
        default=[],
        help="Changed path to check; repeatable for tests",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=PROJECT_ROOT,
        help="Repository root",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON report")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    repo_root = args.repo_root.resolve()
    changed_paths = list(args.changed_file)
    if args.changed or not changed_paths:
        changed_paths.extend(changed_paths_from_git(repo_root, args.base))
    return run(changed_paths, repo_root=repo_root, emit_json=args.json)


if __name__ == "__main__":
    raise SystemExit(main())
