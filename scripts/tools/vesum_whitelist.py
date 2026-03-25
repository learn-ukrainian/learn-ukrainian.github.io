#!/usr/bin/env python3
"""VESUM false-positive whitelist manager.

Loads global and per-module whitelists of words that VESUM marks as
"not found" but are valid in context. Provides a CLI to add entries.

Global whitelist: docs/rules/vesum-whitelist.yaml
Per-module whitelist: orchestration/{slug}/vesum-whitelist.yaml

Issue: #1017
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
GLOBAL_WHITELIST = PROJECT_ROOT / "docs" / "rules" / "vesum-whitelist.yaml"
CURRICULUM_ROOT = PROJECT_ROOT / "curriculum" / "l2-uk-en"


def load_whitelist(path: Path) -> dict[str, dict]:
    """Load a whitelist YAML file. Returns {word: {reason, approved_by}}."""
    if not path.exists():
        return {}
    try:
        data = yaml.safe_load(path.read_text("utf-8")) or {}
    except yaml.YAMLError:
        return {}
    if not isinstance(data, dict):
        return {}
    result = {}
    for entry in data.get("words", []):
        if not isinstance(entry, dict):
            continue
        word = entry.get("word", "").strip().lower()
        if word:
            result[word] = {
                "reason": entry.get("reason", ""),
                "approved_by": entry.get("approved_by", ""),
            }
    return result


def load_global_whitelist() -> dict[str, dict]:
    """Load the global whitelist."""
    return load_whitelist(GLOBAL_WHITELIST)


def load_module_whitelist(level: str, slug: str) -> dict[str, dict]:
    """Load the per-module whitelist for a given level/slug."""
    path = CURRICULUM_ROOT / level / "orchestration" / slug / "vesum-whitelist.yaml"
    return load_whitelist(path)


def load_combined_whitelist(level: str, slug: str) -> set[str]:
    """Load global + per-module whitelists, return set of whitelisted words."""
    combined = set(load_global_whitelist().keys())
    combined.update(load_module_whitelist(level, slug).keys())
    return combined


def add_word(
    word: str,
    reason: str,
    approved_by: str = "auto",
    *,
    scope: str = "global",
    level: str = "",
    slug: str = "",
) -> Path:
    """Add a word to the specified whitelist. Returns the path written to."""
    if scope == "module":
        if not level or not slug:
            raise ValueError("level and slug required for module-scope whitelist")
        path = CURRICULUM_ROOT / level / "orchestration" / slug / "vesum-whitelist.yaml"
    else:
        path = GLOBAL_WHITELIST

    # Load existing
    if path.exists():
        try:
            data = yaml.safe_load(path.read_text("utf-8")) or {}
        except yaml.YAMLError:
            data = {}
        if not isinstance(data, dict):
            data = {}
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        data = {}

    words_list = data.get("words", [])

    # Check for duplicates
    existing = {e.get("word", "").strip().lower() for e in words_list}
    if word.strip().lower() in existing:
        print(f"Word '{word}' already in whitelist at {path}")
        return path

    words_list.append({
        "word": word.strip().lower(),
        "reason": reason,
        "approved_by": approved_by,
    })
    data["words"] = words_list

    path.write_text(
        yaml.dump(data, allow_unicode=True, default_flow_style=False, sort_keys=False),
        encoding="utf-8",
    )
    print(f"Added '{word}' to {path}")
    return path


def main():
    parser = argparse.ArgumentParser(
        description="Manage VESUM false-positive whitelist",
    )
    sub = parser.add_subparsers(dest="command")

    # add
    add_parser = sub.add_parser("add", help="Add a word to the whitelist")
    add_parser.add_argument("--word", required=True, help="Word to whitelist")
    add_parser.add_argument("--reason", required=True, help="Why this word is valid")
    add_parser.add_argument("--approved-by", default="auto", help="Who approved")
    add_parser.add_argument(
        "--scope", choices=["global", "module"], default="global",
        help="global or module-level whitelist",
    )
    add_parser.add_argument("--level", default="", help="Level (for module scope)")
    add_parser.add_argument("--slug", default="", help="Slug (for module scope)")

    # list
    list_parser = sub.add_parser("list", help="List whitelisted words")
    list_parser.add_argument("--level", default="", help="Level (to include module whitelist)")
    list_parser.add_argument("--slug", default="", help="Slug (to include module whitelist)")

    args = parser.parse_args()

    if args.command == "add":
        add_word(
            args.word, args.reason, args.approved_by,
            scope=args.scope, level=args.level, slug=args.slug,
        )
    elif args.command == "list":
        global_wl = load_global_whitelist()
        print(f"Global whitelist ({len(global_wl)} words):")
        for word, info in global_wl.items():
            print(f"  {word} — {info['reason']} [{info['approved_by']}]")
        if args.level and args.slug:
            module_wl = load_module_whitelist(args.level, args.slug)
            print(f"\nModule whitelist {args.level}/{args.slug} ({len(module_wl)} words):")
            for word, info in module_wl.items():
                print(f"  {word} — {info['reason']} [{info['approved_by']}]")
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
