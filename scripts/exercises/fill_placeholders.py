#!/usr/bin/env python3
"""Fill exercise placeholders with actual exercise DSL.

Reads a .md file with :::exercise-placeholder blocks and generates
:::exercise[type] blocks. Simple types (match, MC, cloze) are
deterministic. Complex types (true-false, read-and-answer) need LLM.

Usage:
    .venv/bin/python scripts/exercises/fill_placeholders.py path/to/module.md
    .venv/bin/python scripts/exercises/fill_placeholders.py path/to/module.md --dry-run

Issue: #996
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# Parse :::exercise-placeholder blocks
_PLACEHOLDER_RE = re.compile(
    r':::exercise-placeholder\n(.*?)\n:::', re.DOTALL
)


def _parse_placeholder(block: str) -> dict:
    """Parse a placeholder block into a dict of fields."""
    fields = {}
    for line in block.strip().split("\n"):
        line = line.strip()
        if ":" in line:
            key, _, value = line.partition(":")
            fields[key.strip()] = value.strip()
    return fields


def _generate_multiple_choice(fields: dict) -> str:
    """Generate a multiple-choice exercise from placeholder fields."""
    vocab = [w.strip() for w in fields.get("vocabulary", "").split(",")]
    correct = {w.strip() for w in fields.get("correct", "").split(",")}
    tests = fields.get("tests", "Choose the correct answer")

    lines = [":::exercise[multiple-choice]"]
    lines.append(f"{tests}")
    for word in vocab:
        marker = "[x]" if word in correct else "[ ]"
        lines.append(f"- {marker} {word}")
    lines.append(":::")
    return "\n".join(lines)


def _generate_cloze(fields: dict) -> str:
    """Generate a cloze exercise from placeholder fields."""
    vocab = [w.strip() for w in fields.get("vocabulary", "").split(",")]

    lines = [":::exercise[cloze]"]
    # Try to create word pairs from vocabulary
    # Expected format: word1, word2, word3, word4 (pairs)
    for i in range(0, len(vocab) - 1, 2):
        word1 = vocab[i]
        word2 = vocab[i + 1] if i + 1 < len(vocab) else ""
        if word1 and word2:
            # Find the differing letter
            diff_pos = -1
            for j in range(min(len(word1), len(word2))):
                if word1[j] != word2[j]:
                    diff_pos = j
                    break
            if diff_pos >= 0:
                blanked = word1[:diff_pos] + "{" + word1[diff_pos] + "}" + word1[diff_pos + 1:]
                lines.append(f"{blanked} — {word1}")
            else:
                lines.append(f"{{{word1[0]}}}{word1[1:]} — {word1}")
    lines.append(":::")
    return "\n".join(lines)


def _generate_match(fields: dict) -> str:
    """Generate a match exercise from placeholder fields."""
    vocab = [w.strip() for w in fields.get("vocabulary", "").split(",")]

    lines = [":::exercise[match]"]
    lines.append("| Left | Right |")
    lines.append("|------|-------|")
    # Try to parse key=value pairs from vocabulary
    for item in vocab:
        if "=" in item:
            left, right = item.split("=", 1)
            lines.append(f"| {left.strip()} | {right.strip()} |")
        elif "—" in item:
            left, right = item.split("—", 1)
            lines.append(f"| {left.strip()} | {right.strip()} |")
    lines.append(":::")
    return "\n".join(lines)


def _generate_true_false(fields: dict) -> str:
    """Generate a true-false stub (needs LLM for actual statements)."""
    lines = [":::exercise[true-false]"]
    lines.append(f"<!-- TODO: Generate true/false statements about: {fields.get('tests', '')} -->")
    lines.append(f"<!-- Vocabulary: {fields.get('vocabulary', '')} -->")
    lines.append("- [true] (placeholder — needs LLM generation)")
    lines.append("- [false] (placeholder — needs LLM generation)")
    lines.append(":::")
    return "\n".join(lines)


def _generate_group_sort(fields: dict) -> str:
    """Generate a group-sort exercise from placeholder fields."""
    vocab = [w.strip() for w in fields.get("vocabulary", "").split(",")]
    correct = fields.get("correct", "")

    lines = [":::exercise[group-sort]"]
    lines.append("groups:")
    # Try to parse groups from correct field
    if ":" in correct:
        for group_def in correct.split(";"):
            if ":" in group_def:
                name, items = group_def.split(":", 1)
                item_list = [i.strip() for i in items.split(",")]
                lines.append(f"  - name: {name.strip()}")
                lines.append(f"    items: [{', '.join(item_list)}]")
    else:
        lines.append("  - name: Group A")
        lines.append(f"    items: [{', '.join(vocab[:len(vocab)//2])}]")
        lines.append("  - name: Group B")
        lines.append(f"    items: [{', '.join(vocab[len(vocab)//2:])}]")
    lines.append(":::")
    return "\n".join(lines)


_GENERATORS = {
    "multiple-choice": _generate_multiple_choice,
    "cloze": _generate_cloze,
    "match": _generate_match,
    "true-false": _generate_true_false,
    "group-sort": _generate_group_sort,
}


def fill_placeholders(text: str) -> tuple[str, int]:
    """Replace all :::exercise-placeholder blocks with actual exercises.

    Returns (modified_text, count_of_replacements).
    """
    count = 0

    def _replace(match):
        nonlocal count
        block = match.group(1)
        fields = _parse_placeholder(block)
        exercise_type = fields.get("type", "multiple-choice")

        generator = _GENERATORS.get(exercise_type)
        if generator:
            count += 1
            return generator(fields)
        else:
            # Unknown type — leave as placeholder with a note
            return f":::exercise-placeholder\n{block}\n<!-- Unknown type: {exercise_type} -->\n:::"

    result = _PLACEHOLDER_RE.sub(_replace, text)
    return result, count


def main():
    parser = argparse.ArgumentParser(description="Fill exercise placeholders with DSL")
    parser.add_argument("file", help="Path to .md file with placeholders")
    parser.add_argument("--dry-run", action="store_true", help="Print result without writing")
    args = parser.parse_args()

    path = Path(args.file)
    if not path.exists():
        print(f"File not found: {path}")
        sys.exit(1)

    text = path.read_text("utf-8")
    filled, count = fill_placeholders(text)

    if count == 0:
        print("No exercise placeholders found.")
        sys.exit(0)

    if args.dry_run:
        print(f"Would fill {count} placeholder(s):")
        print(filled)
    else:
        path.write_text(filled, "utf-8")
        print(f"Filled {count} exercise placeholder(s) in {path.name}")


if __name__ == "__main__":
    main()
