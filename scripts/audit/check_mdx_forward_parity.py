#!/usr/bin/env python3
"""Check changed folk/seminar sources have current committed site MDX."""

from __future__ import annotations

import argparse
import importlib.util
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.build import linear_pipeline


def _load_reverse_parity() -> ModuleType:
    helper_path = PROJECT_ROOT / "scripts" / "audit" / "check_mdx_source_parity.py"
    spec = importlib.util.spec_from_file_location("check_mdx_source_parity_for_forward", helper_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load reverse parity helper: {helper_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


reverse_parity = _load_reverse_parity()
SEMINAR_LEVELS = linear_pipeline.SEMINAR_LEVELS
MDX_DIR = reverse_parity.MDX_DIR
SOURCE_DIR = reverse_parity.SOURCE_DIR

SOURCE_FILENAMES = {
    "activities.yaml",
    "activities.yml",
    "module.md",
    "resources.yaml",
    "resources.yml",
    "vocabulary.yaml",
    "vocabulary.yml",
}
NAV_FRONTMATTER_RE = re.compile(r"^(prev|next):(?:\s|$)")


@dataclass(frozen=True, order=True)
class ModuleTarget:
    level: str
    slug: str

    @property
    def module_dir(self) -> Path:
        return SOURCE_DIR / self.level / self.slug

    @property
    def mdx_path(self) -> Path:
        return MDX_DIR / self.level / f"{self.slug}.mdx"


def plan_path_for(level: str, slug: str) -> Path:
    """Mirror the v7 build caller's plan path derivation."""
    return linear_pipeline.plan_path_for(level, slug)


def _as_repo_path(path: Path) -> Path:
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def _target_for_source(path: Path) -> ModuleTarget | None:
    path = _as_repo_path(path)
    try:
        rel_path = path.resolve().relative_to(SOURCE_DIR)
    except ValueError:
        return None

    parts = rel_path.parts
    if len(parts) < 2:
        return None

    if parts[0] == "plans":
        if len(parts) == 3 and rel_path.suffix in {".yaml", ".yml"}:
            level = parts[1].lower()
            if level in SEMINAR_LEVELS:
                return ModuleTarget(level, Path(parts[2]).stem)
        return None

    level = parts[0].lower()
    if level not in SEMINAR_LEVELS:
        return None

    if len(parts) == 3 and parts[2] in SOURCE_FILENAMES:
        return ModuleTarget(level, parts[1])

    return None


def affected_source_targets(paths: list[Path]) -> set[ModuleTarget]:
    """Return folk/seminar modules whose assembled MDX may have changed."""
    targets: set[ModuleTarget] = set()
    for path in paths:
        target = _target_for_source(path)
        if target is not None:
            targets.add(target)
    return targets


def _get_local_changed_files(*, cached: bool = False) -> list[Path]:
    cmd = ["git", "diff", "--name-only"]
    if cached:
        cmd.append("--cached")
    try:
        output = subprocess.check_output(cmd, cwd=PROJECT_ROOT, text=True)
    except subprocess.CalledProcessError:
        return []
    return [PROJECT_ROOT / line for line in output.splitlines() if line]


def normalize_mdx_for_parity(text: str) -> str:
    """Remove generated nav frontmatter and trailing whitespace before compare."""
    lines = [line.rstrip() for line in text.splitlines()]

    if lines and lines[0].strip() == "---":
        for closing_index in range(1, len(lines)):
            if lines[closing_index].strip() != "---":
                continue
            frontmatter = [
                line for line in lines[1:closing_index] if not NAV_FRONTMATTER_RE.match(line)
            ]
            lines = ["---", *frontmatter, *lines[closing_index:]]
            break

    normalized = "\n".join(lines).rstrip()
    return f"{normalized}\n" if normalized else ""


def _assemble_target(target: ModuleTarget, output_path: Path) -> str:
    linear_pipeline.assemble_mdx(
        target.module_dir,
        output_path,
        plan_path_for(target.level, target.slug),
    )
    return output_path.read_text(encoding="utf-8")


def check_targets(targets: set[ModuleTarget]) -> list[str]:
    violations: list[str] = []

    with tempfile.TemporaryDirectory(prefix="mdx-forward-parity-") as tmp_dir_raw:
        tmp_dir = Path(tmp_dir_raw)
        for target in sorted(targets):
            mdx_rel = Path("site/src/content/docs") / target.level / f"{target.slug}.mdx"
            stale_message = (
                f"source changed but site MDX stale for {target.level}/{target.slug} — "
                f"regenerate (assemble_mdx / `make` path) and commit {mdx_rel}"
            )

            if not target.module_dir.exists() and not target.mdx_path.exists():
                continue

            if not target.mdx_path.exists():
                violations.append(stale_message)
                continue

            try:
                generated = _assemble_target(target, tmp_dir / f"{target.level}-{target.slug}.mdx")
            except Exception as exc:
                violations.append(f"failed to assemble MDX for {target.level}/{target.slug}: {exc}")
                continue

            committed = target.mdx_path.read_text(encoding="utf-8")
            if normalize_mdx_for_parity(generated) != normalize_mdx_for_parity(committed):
                violations.append(stale_message)

    return violations


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Check changed folk/seminar sources have current committed site MDX."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--changed-vs-base", metavar="BASE", help="Compare base branch, e.g. origin/main")
    group.add_argument("--files", nargs="+", type=Path, help="Scan explicit files (for pre-commit)")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.changed_vs_base:
        changed_files = [
            *reverse_parity.get_changed_files(base=args.changed_vs_base),
            *_get_local_changed_files(),
            *_get_local_changed_files(cached=True),
        ]
    else:
        changed_files = reverse_parity.get_changed_files(cached=True)
        explicit_files = [_as_repo_path(path) for path in args.files]
        changed_files = [*changed_files, *explicit_files]

    targets = affected_source_targets(changed_files)
    if not targets:
        print("0 findings: no changed folk/seminar sources require site MDX parity check.")
        return 0

    violations = check_targets(targets)
    if not violations:
        print(f"0 findings: forward MDX parity OK for {len(targets)} changed folk/seminar module(s).")
        return 0

    for violation in violations:
        print(violation)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
