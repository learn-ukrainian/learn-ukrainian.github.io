#!/usr/bin/env python3
"""Check that generated MDX is current for changed curriculum sources."""

from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CURRICULUM_ROOT = PROJECT_ROOT / "curriculum" / "l2-uk-en"
MDX_ROOT = PROJECT_ROOT / "site" / "src" / "content" / "docs"
VENV_PYTHON = PROJECT_ROOT / ".venv" / "bin" / "python"

sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
from manifest_utils import get_modules_for_level

from scripts.build import linear_pipeline

SEMINAR_LEVELS = linear_pipeline.SEMINAR_LEVELS


@dataclass(frozen=True, order=True)
class ModuleTarget:
    level: str
    slug: str
    local_num: int

    @property
    def mdx_path(self) -> Path:
        return MDX_ROOT / self.level / f"{self.slug}.mdx"


def _git_changed_files(base: str) -> list[Path]:
    try:
        merge_base = subprocess.check_output(
            ["git", "merge-base", base, "HEAD"],
            cwd=PROJECT_ROOT,
            text=True,
        ).strip()
        rev_range = f"{merge_base}...HEAD"
    except subprocess.CalledProcessError:
        rev_range = f"{base}...HEAD"

    output = subprocess.check_output(
        ["git", "diff", "--name-only", "--diff-filter=AMR", rev_range],
        cwd=PROJECT_ROOT,
        text=True,
    )
    return [PROJECT_ROOT / line for line in output.splitlines() if line]


def _module_key_for_source(path: Path) -> tuple[str, str] | None:
    try:
        rel = path.resolve().relative_to(CURRICULUM_ROOT)
    except ValueError:
        return None

    parts = rel.parts
    if len(parts) < 2:
        return None

    # curriculum/l2-uk-en/plans/{level}/{slug}.yaml
    if parts[0] == "plans" and len(parts) == 3 and rel.suffix in {".yaml", ".yml"}:
        return parts[1], Path(parts[2]).stem

    level = parts[0]

    # curriculum/l2-uk-en/{level}/{slug}.md
    if len(parts) == 2 and rel.suffix == ".md":
        return level, rel.stem

    # curriculum/l2-uk-en/{level}/{slug}/module.md
    # curriculum/l2-uk-en/{level}/{slug}/{activities,vocabulary,resources}.yaml
    if len(parts) == 3 and parts[2] in {
        "module.md",
        "activities.yaml",
        "activities.yml",
        "vocabulary.yaml",
        "vocabulary.yml",
        "resources.yaml",
        "resources.yml",
    }:
        return level, parts[1]

    # Legacy sibling layouts still feed the generator.
    # curriculum/l2-uk-en/{level}/activities/{slug}.yaml
    # curriculum/l2-uk-en/{level}/vocabulary/{slug}.yaml
    # curriculum/l2-uk-en/{level}/meta/{slug}.yaml
    # curriculum/l2-uk-en/{level}/discovery/{slug}.yaml
    if (
        len(parts) == 3
        and parts[1] in {"activities", "vocabulary", "meta", "discovery"}
        and rel.suffix in {".yaml", ".yml"}
    ):
        return level, rel.stem

    return None


def affected_module_keys(paths: list[Path]) -> set[tuple[str, str]]:
    """Return ``(level, slug)`` pairs whose generated MDX may have changed."""
    return {key for path in paths if (key := _module_key_for_source(path))}


def _resolve_targets(keys: set[tuple[str, str]]) -> list[ModuleTarget]:
    targets: list[ModuleTarget] = []
    by_level: dict[str, dict[str, int]] = {}

    for level, slug in sorted(keys):
        if level not in by_level:
            by_level[level] = {
                module.slug: module.local_num
                for module in get_modules_for_level(level)
            }
        local_num = by_level[level].get(slug)
        if local_num is None:
            print(
                f"::warning::Could not resolve curriculum module {level}/{slug}; "
                "skipping MDX generation drift check for it."
            )
            continue
        targets.append(ModuleTarget(level=level, slug=slug, local_num=local_num))

    return targets


def _read_optional(path: Path) -> bytes | None:
    if not path.exists():
        return None
    return path.read_bytes()


def _is_seminar_plan_without_module(target: ModuleTarget) -> bool:
    if target.level not in SEMINAR_LEVELS:
        return False

    module_dir = CURRICULUM_ROOT / target.level / target.slug
    return not module_dir.exists()


def _filter_generatable_targets(targets: list[ModuleTarget]) -> list[ModuleTarget]:
    generatable: list[ModuleTarget] = []
    for target in targets:
        if _is_seminar_plan_without_module(target):
            print(
                f"Skipping {target.level}/{target.slug}: seminar plan "
                "has no module directory yet."
            )
            continue
        generatable.append(target)
    return generatable


def _run_generator(target: ModuleTarget) -> None:
    if target.level in SEMINAR_LEVELS:
        module_dir = CURRICULUM_ROOT / target.level / target.slug
        plan_path = CURRICULUM_ROOT / "plans" / target.level / f"{target.slug}.yaml"
        content = linear_pipeline.assemble_mdx(module_dir, target.mdx_path, plan_path)
        target.mdx_path.write_text(content, encoding="utf-8")
        return

    if not VENV_PYTHON.exists():
        raise FileNotFoundError(
            f"Expected project venv at {VENV_PYTHON}. "
            "Create it before running the MDX generation drift check."
        )

    subprocess.run(
        [
            str(VENV_PYTHON),
            "scripts/generate_mdx.py",
            "l2-uk-en",
            target.level,
            str(target.local_num),
            "--validate",
        ],
        cwd=PROJECT_ROOT,
        check=True,
    )


def check_targets(targets: list[ModuleTarget]) -> int:
    targets = _filter_generatable_targets(targets)
    if not targets:
        print("No changed curriculum sources require MDX generation.")
        return 0

    before = {target.mdx_path: _read_optional(target.mdx_path) for target in targets}

    for target in targets:
        print(f"Regenerating {target.level}/{target.slug} -> {target.mdx_path.relative_to(PROJECT_ROOT)}")
        _run_generator(target)

    drifted = [
        path
        for path, old_content in before.items()
        if _read_optional(path) != old_content
    ]

    if not drifted:
        print("Generated MDX is current for changed curriculum sources.")
        return 0

    print("\nGenerated MDX drift detected. Commit regenerated MDX for:")
    for path in drifted:
        print(f"  - {path.relative_to(PROJECT_ROOT)}")
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Regenerate changed curriculum modules and fail if MDX output drifts."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--changed-vs-base", metavar="BASE")
    group.add_argument("--files", nargs="+", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    paths = _git_changed_files(args.changed_vs_base) if args.changed_vs_base else args.files
    keys = affected_module_keys(paths)
    targets = _resolve_targets(keys)
    return check_targets(targets)


if __name__ == "__main__":
    raise SystemExit(main())
