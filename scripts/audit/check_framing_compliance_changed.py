#!/usr/bin/env python3
"""Check changed built FOLK modules against the framing-compliance gate."""

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


def _load_framing_gate_verify() -> Any:
    module_name = "scripts.audit.framing_compliance_gate"
    if "scripts.audit" not in sys.modules:
        audit_package = types.ModuleType("scripts.audit")
        audit_package.__path__ = [str(PROJECT_ROOT / "scripts" / "audit")]
        sys.modules["scripts.audit"] = audit_package
    spec = importlib.util.spec_from_file_location(
        module_name,
        PROJECT_ROOT / "scripts" / "audit" / "framing_compliance_gate.py",
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load framing compliance gate")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module.verify


verify = _load_framing_gate_verify()


@dataclass(frozen=True, order=True)
class ModuleTarget:
    level: str
    slug: str


def _repo_relative_path(raw_path: str, repo_root: Path) -> PurePosixPath | None:
    path = Path(raw_path)
    if path.is_absolute():
        try:
            path = path.resolve().relative_to(repo_root.resolve())
        except ValueError:
            return None
    return PurePosixPath(path.as_posix())


def _built_module_exists(repo_root: Path, slug: str) -> bool:
    return (repo_root / "curriculum" / "l2-uk-en" / "folk" / slug / "module.md").exists()


def target_from_changed_path(raw_path: str, repo_root: Path) -> ModuleTarget | None:
    rel = _repo_relative_path(raw_path, repo_root)
    if rel is None:
        return None
    parts = rel.parts
    if len(parts) == 5 and parts[:3] == ("curriculum", "l2-uk-en", "folk") and parts[4] == "module.md":
        return ModuleTarget("folk", parts[3])
    if (
        len(parts) == 5
        and parts[:4] == ("curriculum", "l2-uk-en", "plans", "folk")
        and parts[4].endswith((".yaml", ".yml"))
    ):
        slug = PurePosixPath(parts[4]).stem
        if _built_module_exists(repo_root, slug):
            return ModuleTarget("folk", slug)
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


def _annotation_escape(value: Any) -> str:
    return str(value).replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")


def _emit_annotation(item: dict[str, Any]) -> None:
    kind = "error" if item["severity"] == "violation" else "warning"
    message = f"{item['rule_id']}: {item['title']} - {item['snippet']}"
    print(
        f"::{kind} file={_annotation_escape(item['source_path'])},"
        f"line={_annotation_escape(item['line'])}::{_annotation_escape(message)}"
    )


def _print_report(target: ModuleTarget, report: dict[str, Any]) -> None:
    status = "PASS" if report["passed"] else "FAIL"
    print(
        f"{status}: {target.level}/{target.slug}: "
        f"violations={len(report.get('violations', []))} "
        f"warnings={len(report.get('warnings', []))} "
        f"infos={len(report.get('infos', []))}"
    )
    for item in [*report.get("violations", []), *report.get("warnings", [])]:
        _emit_annotation(item)
        print(
            f" - {item['severity']} {item['rule_id']} "
            f"{item['source_path']}:{item['line']}: {item['snippet']}"
        )


def run(changed_paths: list[str], *, repo_root: Path, emit_json: bool) -> int:
    targets = collect_targets(changed_paths, repo_root)
    results: list[dict[str, Any]] = []
    hard_failures: list[ModuleTarget] = []
    warning_count = 0

    for target in targets:
        report = verify(target.level, target.slug, repo_root=repo_root)
        if report["violations"]:
            hard_failures.append(target)
        warning_count += len(report.get("warnings", []))
        if not emit_json:
            _print_report(target, report)
        results.append(
            {
                "level": target.level,
                "slug": target.slug,
                "passed": report["passed"],
                "violations": report.get("violations", []),
                "warnings": report.get("warnings", []),
                "infos": report.get("infos", []),
            }
        )

    summary = {
        "checked": len(targets),
        "hard_failures": len(hard_failures),
        "warnings": warning_count,
        "passed": not hard_failures,
        "results": results,
    }
    if emit_json:
        print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(
            "SUMMARY: framing-compliance checked "
            f"{len(targets)} built folk module(s); "
            f"hard_failures={len(hard_failures)} warnings={warning_count}"
        )
    return 1 if hard_failures else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", default="origin/main", help="Base ref changed-file detection")
    parser.add_argument("--changed", action="store_true", help="Check files changed against --base...HEAD")
    parser.add_argument("--changed-file", action="append", default=[], help="Changed path check; repeatable in tests")
    parser.add_argument("--repo-root", type=Path, default=PROJECT_ROOT, help="Repository root")
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
