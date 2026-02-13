#!/usr/bin/env python3
"""Extract delimited content from raw Gemini output files.

Replaces the manual sed/wc/Read cycle with a single CLI command that:
1. Reads the raw Gemini output file
2. Extracts content for each expected tag (from PHASE_TAGS)
3. Reports what was found/missing/truncated
4. Writes extracted content to output-dir
5. Extracts friction report if present

Usage:
    .venv/bin/python scripts/extract_phase.py /tmp/gemini-output.txt --phase 2 \
        --output-dir curriculum/l2-uk-en/b1/orchestration/slug/

    # Custom tags (override PHASE_TAGS lookup):
    .venv/bin/python scripts/extract_phase.py /tmp/output.txt --tags CONTENT ACTIVITIES

Exit codes:
    0 - All expected tags found
    1 - One or more expected tags missing
"""

import argparse
import sys
from pathlib import Path

# Add project root so we can import gemini_output
sys.path.insert(0, str(Path(__file__).resolve().parent))

from gemini_output import PHASE_TAGS, extract_delimited, validate_output


def extract_friction(text: str) -> str | None:
    """Extract friction report from raw output."""
    return extract_delimited(text, "FRICTION")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Extract delimited content from raw Gemini output."
    )
    parser.add_argument("input_file", type=Path, help="Raw Gemini output file")
    parser.add_argument(
        "--phase",
        type=str,
        help="Phase number (looks up expected tags from PHASE_TAGS). "
        "Use 'fix', 'fix-content', 'fix-activities' for fix phases.",
    )
    parser.add_argument(
        "--tags",
        nargs="+",
        help="Override: explicit list of tags to extract (ignores --phase)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Directory to write extracted files to",
    )
    parser.add_argument(
        "--attempt",
        type=int,
        default=1,
        help="Attempt number for friction report naming (default: 1)",
    )

    args = parser.parse_args()

    # Resolve expected tags
    if args.tags:
        expected_tags = args.tags
    elif args.phase is not None:
        # Try int first, then string key
        try:
            phase_key: int | str = int(args.phase)
        except ValueError:
            phase_key = args.phase
        if phase_key not in PHASE_TAGS:
            print(f"ERROR: Unknown phase '{args.phase}'. Known: {list(PHASE_TAGS.keys())}")
            return 1
        expected_tags = PHASE_TAGS[phase_key]
    else:
        print("ERROR: Provide either --phase or --tags")
        return 1

    # Read input
    if not args.input_file.exists():
        print(f"ERROR: Input file not found: {args.input_file}")
        return 1

    raw_text = args.input_file.read_text(encoding="utf-8")
    print(f"Read {len(raw_text):,} chars from {args.input_file}")

    # Create output dir
    args.output_dir.mkdir(parents=True, exist_ok=True)

    # Validate
    result = validate_output(raw_text, expected_tags)

    # Extract and write each tag
    for tag in expected_tags:
        content = extract_delimited(raw_text, tag)
        if content:
            # Determine output filename based on phase
            if args.phase is not None:
                out_file = args.output_dir / f"phase-{args.phase}-{tag.lower()}.md"
            else:
                out_file = args.output_dir / f"{tag.lower()}.md"
            out_file.write_text(content + "\n", encoding="utf-8")
            lines = content.count("\n") + 1
            print(f"  ✅ {tag}: {lines} lines → {out_file.name}")
        elif tag in result["truncated"]:
            print(f"  ⚠️  {tag}: TRUNCATED (START found, no END)")
        else:
            print(f"  ❌ {tag}: NOT FOUND")

    # Extract friction report (always attempt, regardless of phase)
    friction = extract_friction(raw_text)
    if friction:
        friction_file = args.output_dir / f"friction-attempt-{args.attempt}.md"
        friction_file.write_text(friction + "\n", encoding="utf-8")
        print(f"  📋 FRICTION: → {friction_file.name}")

    # Summary
    if result["valid"]:
        print(f"\n✅ All {len(expected_tags)} tag(s) extracted successfully.")
        return 0
    else:
        missing = result["missing"]
        truncated = result["truncated"]
        print(f"\n❌ Missing tags: {missing}")
        if truncated:
            print(f"   Truncated (START without END): {truncated}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
