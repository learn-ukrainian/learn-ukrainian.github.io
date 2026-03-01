#!/usr/bin/env python3
"""Assemble section-by-section Phase 2 output into a single content file.

For section-by-section content generation, Phase 2 may be dispatched as
individual section prompts. This script concatenates the extracted sections
and summary into a single content block, then validates the result.

Usage:
    .venv/bin/python scripts/assemble_sections.py \
        --sections-dir curriculum/l2-uk-en/b1/orchestration/slug/ \
        --output curriculum/l2-uk-en/b1/06-slug.md \
        --word-target 4000 \
        --meta-path curriculum/l2-uk-en/b1/meta/slug.yaml

Exit codes:
    0 - Success (all sections found, validation passed)
    1 - Missing sections or summary
    2 - Validation failure (word count < 80% of target, or missing H2 headers)
"""

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import yaml


def find_section_files(sections_dir: Path) -> list[Path]:
    """Find section_N.md files sorted by index."""
    pattern = re.compile(r"^section_(\d+)\.md$")
    files = []
    for f in sorted(sections_dir.iterdir()):
        m = pattern.match(f.name)
        if m:
            files.append((int(m.group(1)), f))
    files.sort(key=lambda x: x[0])
    return [f for _, f in files]


def count_words(text: str) -> int:
    """Count words in text (Ukrainian + English)."""
    return len(text.split())


def extract_h2_headers(text: str) -> list[str]:
    """Extract H2 headers from markdown text."""
    return re.findall(r"^## (.+)$", text, re.MULTILINE)


def load_meta_outline(meta_path: Path) -> list[str]:
    """Load expected H2 section names from meta's content_outline."""
    with open(meta_path) as f:
        meta = yaml.safe_load(f)

    outline = meta.get("content_outline", [])
    names = []
    for section in outline:
        if isinstance(section, dict):
            name = section.get("section") or section.get("name", "")
            if name:
                names.append(name)
        elif isinstance(section, str):
            names.append(section)
    return names


def main():
    parser = argparse.ArgumentParser(
        description="Assemble section files into a single content file."
    )
    parser.add_argument(
        "--sections-dir",
        required=True,
        help="Directory containing section_0.md, section_1.md, ..., summary.md",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Output content file path",
    )
    parser.add_argument(
        "--word-target",
        type=int,
        default=0,
        help="Expected word count target (warns if < 80%%)",
    )
    parser.add_argument(
        "--meta-path",
        default=None,
        help="Path to meta YAML file (for H2 header validation)",
    )
    args = parser.parse_args()

    sections_dir = Path(args.sections_dir)
    output_path = Path(args.output)

    if not sections_dir.is_dir():
        print(f"ERROR: sections-dir not found: {sections_dir}", file=sys.stderr)
        sys.exit(1)

    # Find section files
    section_files = find_section_files(sections_dir)
    summary_file = sections_dir / "summary.md"

    if not section_files:
        print(f"ERROR: No section_N.md files found in {sections_dir}", file=sys.stderr)
        sys.exit(1)

    if not summary_file.exists():
        print(f"WARNING: summary.md not found in {sections_dir}", file=sys.stderr)

    # Read and concatenate
    parts = []
    for sf in section_files:
        content = sf.read_text().strip()
        if content:
            parts.append(content)
            print(f"  Section {sf.name}: {count_words(content)} words")

    if summary_file.exists():
        summary_content = summary_file.read_text().strip()
        if summary_content:
            parts.append(summary_content)
            print(f"  summary.md: {count_words(summary_content)} words")

    assembled = "\n\n".join(parts)
    total_words = count_words(assembled)
    print(f"\n  Total: {total_words} words")

    # Write output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(assembled + "\n")
    print(f"  Written to: {output_path}")

    # Validation
    exit_code = 0

    # Word count check
    if args.word_target > 0:
        ratio = total_words / args.word_target
        threshold = 0.8
        if ratio < threshold:
            print(
                f"\n  WARNING: Word count {total_words} is {ratio:.1%} of target "
                f"{args.word_target} (below {threshold:.0%} threshold)",
                file=sys.stderr,
            )
            exit_code = 2
        else:
            print(f"  Word count: {ratio:.1%} of target ({args.word_target})")

    # H2 header check
    if args.meta_path:
        meta_path = Path(args.meta_path)
        if meta_path.exists():
            expected = load_meta_outline(meta_path)
            found = extract_h2_headers(assembled)

            # Normalize for comparison (strip whitespace)
            expected_norm = {h.strip().lower() for h in expected}
            found_norm = {h.strip().lower() for h in found}

            missing = expected_norm - found_norm
            if missing:
                print(f"\n  WARNING: Missing H2 sections from content_outline:", file=sys.stderr)
                for m in sorted(missing):
                    print(f"    - {m}", file=sys.stderr)
                exit_code = max(exit_code, 2)
            else:
                print(f"  H2 headers: all {len(expected)} sections present")
        else:
            print(f"  WARNING: meta file not found: {meta_path}", file=sys.stderr)

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
