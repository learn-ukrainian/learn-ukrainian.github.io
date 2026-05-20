#!/usr/bin/env python3
"""Prune promoted V7 forensics from locked curriculum modules."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.sync.promote_module import CURRICULUM_ROOT, FORENSICS_FILES, _sanitized_git_env


@dataclass(frozen=True)
class ModuleTarget:
    level: str
    slug: str

    @property
    def label(self) -> str:
        return f"{self.level}/{self.slug}"

    @property
    def module_rel(self) -> Path:
        return CURRICULUM_ROOT / self.level / self.slug


def _run_git(repo_root: Path, args: list[str], *, check: bool = True) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ["git", "-C", str(repo_root), *args],
        check=check,
        capture_output=True,
        env=_sanitized_git_env(),
    )


def _decode(data: bytes) -> str:
    return data.decode("utf-8", errors="replace")


def _status_path(target: ModuleTarget) -> Path:
    return target.module_rel / "status" / f"{target.slug}.json"


def _read_status(repo_root: Path, target: ModuleTarget) -> str | None:
    path = repo_root / _status_path(target)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    status = data.get("status")
    return status if isinstance(status, str) else None


def _is_locked(repo_root: Path, target: ModuleTarget) -> bool:
    return _read_status(repo_root, target) == "locked"


def _discover_all_targets(repo_root: Path, *, force: bool) -> list[ModuleTarget]:
    root = repo_root / CURRICULUM_ROOT
    targets: list[ModuleTarget] = []
    if not root.exists():
        return targets
    for level_dir in sorted(path for path in root.iterdir() if path.is_dir() and not path.name.startswith("_")):
        if level_dir.name == "plans":
            continue
        for module_dir in sorted(path for path in level_dir.iterdir() if path.is_dir()):
            target = ModuleTarget(level=level_dir.name, slug=module_dir.name)
            has_status = (repo_root / _status_path(target)).exists()
            has_forensics = any((module_dir / filename).exists() for filename in FORENSICS_FILES)
            if force:
                if has_forensics:
                    targets.append(target)
            elif has_status:
                targets.append(target)
    return targets


def _forensics_paths(target: ModuleTarget) -> list[Path]:
    return [target.module_rel / filename for filename in sorted(FORENSICS_FILES)]


def _commit(repo_root: Path, rels: list[Path], message: str) -> None:
    rel_args = [rel.as_posix() for rel in rels]
    _run_git(repo_root, ["add", "-u", "--", *rel_args])
    staged = _run_git(repo_root, ["diff", "--cached", "--quiet"], check=False)
    if staged.returncode == 0:
        print("OK no staged changes")
        return
    _run_git(repo_root, ["commit", "-m", message])


def _prune_one(repo_root: Path, target: ModuleTarget, *, dry_run: bool) -> list[Path]:
    removed: list[Path] = []
    for rel in _forensics_paths(target):
        path = repo_root / rel
        if not path.exists():
            print(f"{target.label}: already pruned, skip {rel.name}")
            continue
        if dry_run:
            print(f"{target.label}: would remove {rel.as_posix()}")
        else:
            path.unlink()
            print(f"{target.label}: removed {rel.as_posix()}")
        removed.append(rel)
    return removed


def prune(args: argparse.Namespace, *, repo_root: Path = ROOT) -> int:
    repo_root = repo_root.resolve()
    if args.all:
        targets = _discover_all_targets(repo_root, force=args.force)
        if not targets:
            print("OK nothing-to-prune")
            return 0
    else:
        if not args.level or not args.slug:
            print("ERROR specify --level and --slug, or use --all", file=sys.stderr)
            return 2
        targets = [ModuleTarget(level=args.level.lower(), slug=args.slug)]

    removed: list[Path] = []
    refused = False
    for target in targets:
        if not args.force and not _is_locked(repo_root, target):
            status = _read_status(repo_root, target)
            if args.all:
                print(f"{target.label}: skip status={status or 'missing'}")
                continue
            print(
                f"ERROR {target.label} is not locked "
                f"(status={status or 'missing'}); use --force to bypass",
                file=sys.stderr,
            )
            refused = True
            continue
        removed.extend(_prune_one(repo_root, target, dry_run=args.dry_run))

    if refused:
        return 1

    if not removed:
        print("OK nothing-to-prune")
        return 0

    if args.dry_run:
        print(f"OK dry-run would remove {len(removed)} file(s)")
        return 0

    if args.no_commit:
        print("OK pruned without commit (--no-commit)")
        return 0

    if args.all:
        message = "chore(content): prune forensics for locked modules"
    else:
        target = targets[0]
        message = f"chore(content): prune forensics for locked {target.label}"
    try:
        _commit(repo_root, removed, message)
    except subprocess.CalledProcessError as exc:
        print(_decode(exc.stderr), file=sys.stderr, end="")
        return exc.returncode or 1
    print("OK pruned and committed")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--level", help="Level to prune")
    parser.add_argument("--slug", help="Module slug to prune")
    parser.add_argument("--all", action="store_true", help="Prune every locked module")
    parser.add_argument("--dry-run", action="store_true", help="Show planned deletions without deleting")
    parser.add_argument("--no-commit", action="store_true", help="Delete files but skip git commit")
    parser.add_argument("--force", action="store_true", help="Bypass locked-status check")
    return parser


def main(argv: list[str] | None = None, *, repo_root: Path = ROOT) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return prune(args, repo_root=repo_root)


if __name__ == "__main__":
    raise SystemExit(main())
