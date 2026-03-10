#!/usr/bin/env python3
"""Fill phase templates with placeholders from a YAML file.

Reads a template file and a YAML placeholders file, performs string
substitution for each {KEY}: value pair, validates no unresolved
placeholders remain, and writes the filled result.

Usage:
    .venv/bin/python scripts/fill_template.py \
        --template claude_extensions/phases/gemini/phase-2-content.md \
        --placeholders orchestration/{slug}/placeholders.yaml \
        --output orchestration/{slug}/phase-2-prompt.md

    # Override/add per-section values without touching placeholders.yaml:
    .venv/bin/python scripts/fill_template.py \
        --template ... --placeholders ... --output ... \
        --set SECTION_TITLE="Практика: Родина та тварини" \
        --set HARD_MINIMUM_WORD_COUNT=600

Exit codes:
    0 - Success
    1 - Error (missing file, unresolved placeholders, etc.)
"""

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import yaml

# Pattern matching {UPPERCASE_PLACEHOLDER} (at least 2 chars, A-Z/0-9/_)
PLACEHOLDER_RE = re.compile(r"\{[A-Z][A-Z0-9_]+\}")


def fill_template(template_text: str, placeholders: dict[str, str]) -> str:
    """Replace {KEY} patterns in template with values from placeholders dict."""
    result = template_text
    for key, value in placeholders.items():
        token = "{" + key + "}"
        result = result.replace(token, str(value))
    return result


def find_unresolved(text: str) -> list[str]:
    """Return list of unresolved {PLACEHOLDER} tokens still in text."""
    return sorted(set(PLACEHOLDER_RE.findall(text)))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Fill phase templates with YAML placeholders."
    )
    parser.add_argument(
        "--template", type=Path, required=True, help="Template file to fill"
    )
    parser.add_argument(
        "--placeholders", type=Path, required=True, help="YAML file with placeholder values"
    )
    parser.add_argument(
        "--output", type=Path, required=True, help="Output file path"
    )
    parser.add_argument(
        "--strict", action="store_true", default=True,
        help="Fail if unresolved placeholders remain (default: true)"
    )
    parser.add_argument(
        "--no-strict", action="store_false", dest="strict",
        help="Warn but don't fail on unresolved placeholders"
    )
    parser.add_argument(
        "--set", action="append", default=[], metavar="KEY=VALUE",
        help="Override or add a placeholder (repeatable). Applied AFTER YAML file."
    )
    args = parser.parse_args()

    if not args.template.exists():
        print(f"ERROR: Template not found: {args.template}")
        return 1
    if not args.placeholders.exists():
        print(f"ERROR: Placeholders file not found: {args.placeholders}")
        return 1

    template_text = args.template.read_text(encoding="utf-8")
    placeholders = yaml.safe_load(args.placeholders.read_text(encoding="utf-8"))

    # Apply --set overrides on top of YAML placeholders
    for item in args.set:
        if "=" not in item:
            print(f"ERROR: --set requires KEY=VALUE format, got: {item}")
            return 1
        key, value = item.split("=", 1)
        placeholders[key] = value

    if not isinstance(placeholders, dict):
        print(f"ERROR: Placeholders file must be a YAML dict, got {type(placeholders).__name__}")
        return 1

    filled = fill_template(template_text, placeholders)
    unresolved = find_unresolved(filled)

    if unresolved:
        msg = f"Unresolved placeholders ({len(unresolved)}): {', '.join(unresolved)}"
        if args.strict:
            print(f"ERROR: {msg}")
            return 1
        else:
            print(f"WARNING: {msg}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(filled, encoding="utf-8")
    print(f"Filled template → {args.output} ({len(filled):,} chars, {len(placeholders)} placeholders applied)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
