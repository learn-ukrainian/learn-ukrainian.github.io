#!/usr/bin/env python3
"""Merge expanded sections into the original content file.

Reads the original and expansion files, replaces each H2 section found
in the expansion with the expanded version, writes the merged result back
to the original path, and prints per-section word counts.
"""

import re
import sys
from pathlib import Path


def split_h2_sections(text: str) -> list[tuple[str, str]]:
    """Split markdown text into (header, body) pairs by H2 headings.

    Returns a list of tuples: (h2_line, content_until_next_h2_or_eof).
    The first element may have header="" if there is content before the
    first H2 (front-matter / preamble).
    """
    sections: list[tuple[str, str]] = []
    lines = text.split('\n')
    current_header = ""
    current_lines: list[str] = []

    for line in lines:
        if line.startswith('## '):
            # Save previous section
            sections.append((current_header, '\n'.join(current_lines)))
            current_header = line
            current_lines = []
        else:
            current_lines.append(line)

    # Save last section
    sections.append((current_header, '\n'.join(current_lines)))
    return sections


def section_name(header: str) -> str:
    """Normalize an H2 header line to a comparable key."""
    return header.strip().lstrip('#').strip()


def word_count(text: str) -> int:
    """Count words in a text block (Ukrainian-aware)."""
    # Strip markdown formatting but keep words
    clean = re.sub(r'[#*_`>\[\]|!]', ' ', text)
    clean = re.sub(r'\(.*?\)', ' ', clean)  # remove parenthetical refs
    clean = re.sub(r'https?://\S+', '', clean)
    words = clean.split()
    return len(words)


def main():
    original_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(
        '/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b1/04-sentence-structure.md'
    )
    expansion_path = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(
        '/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b1/orchestration/sentence-structure/phase-2b-expansion.md'
    )

    original_text = original_path.read_text(encoding='utf-8')
    expansion_text = expansion_path.read_text(encoding='utf-8')

    # Parse both files into sections
    orig_sections = split_h2_sections(original_text)
    exp_sections = split_h2_sections(expansion_text)

    # Build a lookup from expansion: normalized name -> (header, body)
    exp_lookup: dict[str, tuple[str, str]] = {}
    for header, body in exp_sections:
        if header:  # skip preamble
            name = section_name(header)
            exp_lookup[name] = (header, body)

    # Rebuild the original, replacing matched sections
    merged_parts: list[str] = []
    replaced = set()

    for header, body in orig_sections:
        name = section_name(header)
        if name and name in exp_lookup:
            exp_header, exp_body = exp_lookup[name]
            merged_parts.append(exp_header)
            merged_parts.append(exp_body)
            replaced.add(name)
        else:
            if header:
                merged_parts.append(header)
            merged_parts.append(body)

    merged_text = '\n'.join(merged_parts)

    # Ensure file ends with exactly one newline
    merged_text = merged_text.rstrip('\n') + '\n'

    # Write the result
    original_path.write_text(merged_text, encoding='utf-8')

    # Report
    print(f"Merged {len(replaced)} sections into {original_path}")
    print(f"Replaced sections: {', '.join(sorted(replaced))}")
    print()

    # Per-section word counts
    final_sections = split_h2_sections(merged_text)
    total = 0
    print(f"{'Section':<55} {'Words':>6}")
    print('-' * 63)
    for header, body in final_sections:
        name = section_name(header) if header else "(preamble)"
        full = (header + '\n' + body) if header else body
        wc = word_count(full)
        total += wc
        marker = " [expanded]" if name in replaced else ""
        print(f"{name:<55} {wc:>6}{marker}")
    print('-' * 63)
    print(f"{'TOTAL':<55} {total:>6}")

    # Check for unmatched expansions
    unmatched = set(exp_lookup.keys()) - replaced
    if unmatched:
        print(f"\nWARNING: {len(unmatched)} expansion sections had no match in original:")
        for name in sorted(unmatched):
            print(f"  - {name}")


if __name__ == '__main__':
    main()
