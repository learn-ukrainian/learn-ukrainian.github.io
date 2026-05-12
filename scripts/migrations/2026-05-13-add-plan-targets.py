"""Add optional plan.targets blocks from legacy vocabulary_hints.required."""

from __future__ import annotations

import argparse
import difflib
import os
import re
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PLAN_DIR = REPO_ROOT / "curriculum" / "l2-uk-en" / "plans" / "a1"


@dataclass(frozen=True)
class PlanTargets:
    """Optional unified plan.targets schema."""

    new_vocabulary: list[str] = field(default_factory=list)
    new_grammar: list[str] = field(default_factory=list)
    recycle_vocabulary: list[str] = field(default_factory=list)

    @classmethod
    def from_plan(cls, plan: dict[str, Any]) -> PlanTargets:
        targets = plan.get("targets")
        if isinstance(targets, dict):
            return cls(
                new_vocabulary=_string_list(targets.get("new_vocabulary")),
                new_grammar=_string_list(targets.get("new_grammar")),
                recycle_vocabulary=_string_list(targets.get("recycle_vocabulary")),
            )
        hints = plan.get("vocabulary_hints")
        required = hints.get("required") if isinstance(hints, dict) else []
        return cls(new_vocabulary=_dedupe([_extract_lemma(item) for item in _string_list(required)]))

    def as_dict(self) -> dict[str, list[str]]:
        return {
            "new_vocabulary": self.new_vocabulary,
            "new_grammar": self.new_grammar,
            "recycle_vocabulary": self.recycle_vocabulary,
        }


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    result: list[str] = []
    for item in value:
        if isinstance(item, dict):
            word = item.get("lemma") or item.get("word")
            if word:
                result.append(str(word).strip())
        elif item:
            result.append(str(item).strip())
    return [item for item in result if item]


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        result.append(item)
    return result


def _extract_lemma(item: str) -> str:
    lemma = item.split("(", 1)[0]
    lemma = re.split(r"\s+[—-]\s+", lemma, maxsplit=1)[0]
    return lemma.strip().strip("`\"'")


def _quote_yaml_scalar(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def _render_targets_block(targets: PlanTargets) -> str:
    if targets.new_vocabulary:
        lines = ["targets:", "  new_vocabulary:"]
        lines.extend(f"    - {_quote_yaml_scalar(item)}" for item in targets.new_vocabulary)
    else:
        lines = ["targets:", "  new_vocabulary: []"]
    if targets.new_grammar:
        lines.append("  new_grammar:")
        lines.extend(f"    - {_quote_yaml_scalar(item)}" for item in targets.new_grammar)
    else:
        lines.append("  new_grammar: []")
    if targets.recycle_vocabulary:
        lines.append("  recycle_vocabulary:")
        lines.extend(f"    - {_quote_yaml_scalar(item)}" for item in targets.recycle_vocabulary)
    else:
        lines.append("  recycle_vocabulary: []")
    return "\n".join(lines) + "\n"


def _find_top_level_block_end(lines: list[str], start_index: int) -> int:
    for index in range(start_index + 1, len(lines)):
        line = lines[index]
        if line and not line.startswith((" ", "\t")) and re.match(r"^[A-Za-z_][\w-]*:", line):
            return index
    return len(lines)


def add_targets_to_text(text: str) -> str:
    plan = yaml.safe_load(text) or {}
    if not isinstance(plan, dict) or plan.get("targets") is not None:
        return text

    targets = PlanTargets.from_plan(plan)
    if not targets.new_vocabulary:
        return text

    lines = text.splitlines(keepends=True)
    insert_at = len(lines)
    for index, line in enumerate(lines):
        if line.startswith("vocabulary_hints:"):
            insert_at = _find_top_level_block_end([item.rstrip("\n") for item in lines], index)
            break

    prefix = "" if insert_at == 0 or lines[insert_at - 1].endswith("\n") else "\n"
    block = prefix + _render_targets_block(targets)
    return "".join([*lines[:insert_at], block, *lines[insert_at:]])


def process_path(path: Path, *, dry_run: bool) -> bool:
    original = path.read_text(encoding="utf-8")
    updated = add_targets_to_text(original)
    if updated == original:
        return False

    if dry_run:
        diff = difflib.unified_diff(
            original.splitlines(),
            updated.splitlines(),
            fromfile=str(path),
            tofile=str(path),
            lineterm="",
        )
        print("\n".join(diff))
        return True

    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent), text=True)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(updated)
        os.replace(tmp_name, path)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)
    return True


def _default_paths() -> list[Path]:
    return sorted(DEFAULT_PLAN_DIR.glob("*.yaml"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", type=Path, help="Plan YAML paths. Defaults to all A1 plans.")
    parser.add_argument("--dry-run", action="store_true", help="Print proposed unified diffs without writing.")
    args = parser.parse_args(argv)

    changed = 0
    for path in args.paths or _default_paths():
        if process_path(path, dry_run=args.dry_run):
            changed += 1
    print(f"{'Would update' if args.dry_run else 'Updated'} {changed} plan(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
