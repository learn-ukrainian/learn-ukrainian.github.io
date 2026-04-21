#!/usr/bin/env python3
"""Deterministically replace Latin M## module refs in plan prose.

Scope:
- Fixes Ukrainian prose strings across plan YAML files.
- Preserves YAML formatting/quotes via ruamel round-trip editing.
- Skips module identifiers and title fields that legitimately retain M## refs.

Usage:
    ../.venv/bin/python scripts/tools/fix_plan_latin_refs.py
    ../.venv/bin/python scripts/tools/fix_plan_latin_refs.py --write
    ../.venv/bin/python scripts/tools/fix_plan_latin_refs.py --write path/to/file.yaml
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

from ruamel.yaml import YAML

MODULE_REF_RE = re.compile(
    r"(?<![0-9A-Za-zА-Яа-яІіЇїЄєҐґ_])M(?P<start>\d+)(?:-(?:M)?(?P<end>\d+))?\b"
)

PREPOSITION_RULES = {
    "з": ("модуля", "модулів"),
    "із": ("модуля", "модулів"),
    "зі": ("модуля", "модулів"),
    "в": ("модулі", "модулях"),
    "у": ("модулі", "модулях"),
    "до": ("модуля", "модулів"),
    "від": ("модуля", "модулів"),
    "для": ("модуля", "модулів"),
    "після": ("модуля", "модулів"),
    "про": ("модуль", "модулі"),
}

PREPOSITION_RE = re.compile(
    r"(?P<prep>\b(?:з|із|зі|в|у|до|від|для|після|про))\s+"
    r"(?P<ref>M\d+(?:-(?:M)?\d+)?)\b",
    flags=re.IGNORECASE,
)

DASH_REF_RE = re.compile(
    r"(?<![0-9A-Za-zА-Яа-яІіЇїЄєҐґ_])(?P<dash>[—-])\s*(?P<ref>M\d+(?:-(?:M)?\d+)?)\b"
)

DEFAULT_PLAN_ROOTS = (
    Path("curriculum/l2-uk-en/plans/a1"),
    Path("curriculum/l2-uk-en/plans/a2"),
    Path("curriculum/l2-uk-en/plans/b1"),
)


def _styled_scalar(original: Any, text: str) -> Any:
    """Rebuild a ruamel scalar while preserving quote style when possible."""
    if not isinstance(original, str):
        return text
    scalar_type = type(original)
    if scalar_type is str:
        return text
    try:
        return scalar_type(text)
    except Exception:
        return text


def _parse_ref(ref: str) -> tuple[int, int | None]:
    match = MODULE_REF_RE.fullmatch(ref)
    if not match:
        raise ValueError(f"Invalid module ref: {ref}")
    start = int(match.group("start"))
    end = match.group("end")
    return start, int(end) if end is not None else None


def _format_number_range(start: int, end: int | None) -> str:
    if end is None:
        return str(start)
    return f"{start}–{end}"


def _format_ref_with_number_sign(ref: str) -> str:
    start, end = _parse_ref(ref)
    return f"№{_format_number_range(start, end)}"


def _format_module_phrase(noun_singular: str, noun_plural: str, ref: str) -> str:
    start, end = _parse_ref(ref)
    noun = noun_singular if end is None else noun_plural
    return f"{noun} {_format_number_range(start, end)}"


def _maybe_capitalize(template: str, original: str) -> str:
    if original[:1].isupper():
        return template[:1].upper() + template[1:]
    return template


def replace_latin_module_refs(text: str) -> str:
    """Replace Latin M## refs in a single prose string."""

    def replace_preposition(match: re.Match[str]) -> str:
        prep = match.group("prep")
        ref = match.group("ref")
        singular, plural = PREPOSITION_RULES[prep.lower()]
        phrase = _format_module_phrase(singular, plural, ref)
        if prep.lower() in {"в", "у"}:
            normalized = _maybe_capitalize("у", prep)
            return f"{normalized} {phrase}"
        normalized = _maybe_capitalize(prep.lower(), prep)
        return f"{normalized} {phrase}"

    def replace_dash(match: re.Match[str]) -> str:
        dash = match.group("dash")
        ref = match.group("ref")
        start, end = _parse_ref(ref)
        noun = "модуль" if end is None else "модулі"
        return f"{dash} {noun} №{_format_number_range(start, end)}"

    updated = PREPOSITION_RE.sub(replace_preposition, text)
    updated = DASH_REF_RE.sub(replace_dash, updated)
    updated = MODULE_REF_RE.sub(lambda m: _format_ref_with_number_sign(m.group(0)), updated)
    return updated


def _bump_version(version: str) -> str:
    parts = str(version).split(".")
    if not parts:
        return "1.0.1"
    try:
        parts[-1] = str(int(parts[-1]) + 1)
    except ValueError:
        parts.append("1")
    return ".".join(parts)


def _should_skip_path(path: tuple[str, ...]) -> bool:
    if not path:
        return False
    if path == ("module",):
        return True
    if path[-1] == "url":
        return True
    if path[-1] != "title":
        return False
    if "external_resources" in path:
        return True
    return len(path) >= 3 and path[-3:] == ("references", "[]", "title")


def _walk_and_fix(node: Any, path: tuple[str, ...] = ()) -> int:
    changes = 0
    if isinstance(node, list):
        for index, value in enumerate(node):
            child_path = (*path, "[]")
            if isinstance(value, str) and not _should_skip_path(child_path):
                updated = replace_latin_module_refs(value)
                if updated != value:
                    node[index] = _styled_scalar(value, updated)
                    changes += 1
            else:
                changes += _walk_and_fix(value, child_path)
        return changes

    if isinstance(node, dict):
        for key, value in node.items():
            child_path = (*path, str(key))
            if isinstance(value, str) and not _should_skip_path(child_path):
                updated = replace_latin_module_refs(value)
                if updated != value:
                    node[key] = _styled_scalar(value, updated)
                    changes += 1
            else:
                changes += _walk_and_fix(value, child_path)
        return changes

    return 0


def fix_plan_file(plan_path: Path, *, write: bool = False) -> tuple[int, str | None, str | None]:
    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.width = 4096

    document = yaml.load(plan_path.read_text("utf-8"))
    if not isinstance(document, dict):
        return 0, None, None

    changes = _walk_and_fix(document)
    if changes == 0:
        return 0, None, None

    old_version = str(document.get("version", "1.0.0"))
    new_version = _bump_version(old_version)
    document["version"] = _styled_scalar(document.get("version"), new_version)

    if write:
        with plan_path.open("w", encoding="utf-8") as handle:
            yaml.dump(document, handle)

    return changes, old_version, new_version


def _iter_plan_paths(inputs: list[str]) -> list[Path]:
    paths = DEFAULT_PLAN_ROOTS if not inputs else [Path(item) for item in inputs]

    discovered: list[Path] = []
    for path in paths:
        if path.is_dir():
            discovered.extend(sorted(path.glob("*.yaml")))
        elif path.is_file():
            discovered.append(path)
        else:
            raise FileNotFoundError(f"No such file or directory: {path}")
    return discovered


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", help="Plan file(s) or directories to scan")
    parser.add_argument("--write", action="store_true", help="Write changes to disk")
    args = parser.parse_args(argv)

    try:
        plan_paths = _iter_plan_paths(args.paths)
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    changed_files = 0
    total_changes = 0
    mode = "updated" if args.write else "would update"

    for plan_path in plan_paths:
        changes, old_version, new_version = fix_plan_file(plan_path, write=args.write)
        if changes == 0:
            continue
        changed_files += 1
        total_changes += changes
        print(
            f"{plan_path}: {mode} {changes} string(s), version {old_version} -> {new_version}"
        )

    print(
        f"Scanned {len(plan_paths)} plan(s); {mode} {changed_files} file(s), {total_changes} string(s)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
