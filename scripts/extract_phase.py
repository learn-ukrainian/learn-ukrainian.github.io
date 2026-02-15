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

import yaml

from gemini_output import PHASE_TAGS, extract_delimited, validate_output

# Tags whose content should be valid YAML (bare list at root)
YAML_TAGS = {"ACTIVITIES", "VOCABULARY"}


def _strip_code_fences(text: str) -> str:
    """Remove ```yaml ... ``` wrappers that Gemini sometimes adds."""
    import re
    # Remove opening ```yaml or ``` at start of content
    text = re.sub(r'^```(?:ya?ml)?\s*\n', '', text)
    # Remove closing ``` at end
    text = re.sub(r'\n```\s*$', '', text)
    return text


def _strip_dict_wrapper(text: str, tag: str) -> tuple[str, str | None]:
    """Auto-strip single-key dict wrapper if YAML tag expects a bare list.

    Gemini frequently wraps vocabulary/activities in a key like:
        items:
          - lemma: ...
    or:
        activities:
          - type: quiz

    This function detects and strips the wrapper, returning the bare list YAML.

    Returns:
        (cleaned_text, wrapper_key_or_None)
    """
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError:
        return text, None

    if isinstance(data, dict) and len(data) == 1:
        key = list(data.keys())[0]
        value = data[key]
        if isinstance(value, list):
            # Re-serialize as bare list
            cleaned = yaml.dump(value, allow_unicode=True, default_flow_style=False)
            return cleaned, key

    return text, None


def _validate_yaml(text: str, tag: str) -> str | None:
    """Try to parse YAML text, return error string or None if valid."""
    try:
        yaml.safe_load(text)
        return None
    except yaml.YAMLError as e:
        if hasattr(e, 'problem_mark'):
            mark = e.problem_mark
            return f"line {mark.line + 1}, col {mark.column + 1}: {e.problem}"
        return str(e)


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
    yaml_errors: list[str] = []
    for tag in expected_tags:
        content = extract_delimited(raw_text, tag)
        if content:
            # Strip code fences that Gemini sometimes wraps around YAML
            cleaned = content
            if tag in YAML_TAGS:
                cleaned = _strip_code_fences(content)
                # Auto-strip single-key dict wrappers (e.g., `items:`, `activities:`)
                cleaned, wrapper_key = _strip_dict_wrapper(cleaned, tag)
                if wrapper_key:
                    print(f"  🔧 {tag}: Auto-stripped '{wrapper_key}:' wrapper → bare list")

            # Determine output filename based on phase
            ext = ".yaml" if tag in YAML_TAGS else ".md"
            if args.phase is not None:
                out_file = args.output_dir / f"phase-{args.phase}-{tag.lower()}{ext}"
            else:
                out_file = args.output_dir / f"{tag.lower()}{ext}"
            out_file.write_text(cleaned + "\n", encoding="utf-8")
            lines = cleaned.count("\n") + 1
            print(f"  ✅ {tag}: {lines} lines → {out_file.name}")

            # YAML validation for activity/vocabulary tags
            if tag in YAML_TAGS:
                err = _validate_yaml(cleaned, tag)
                if err:
                    yaml_errors.append(err)
                    print(f"  ⚠️  {tag}: YAML PARSE ERROR — {err}")
                else:
                    data = yaml.safe_load(cleaned)
                    if isinstance(data, list):
                        print(f"     ✅ Valid YAML: {len(data)} items")
                    else:
                        print(f"     ℹ️  YAML type: {type(data).__name__}")
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
    if result["valid"] and not yaml_errors:
        print(f"\n✅ All {len(expected_tags)} tag(s) extracted successfully.")
        return 0
    else:
        if not result["valid"]:
            missing = result["missing"]
            truncated = result["truncated"]
            print(f"\n❌ Missing tags: {missing}")
            if truncated:
                print(f"   Truncated (START without END): {truncated}")
        if yaml_errors:
            print(f"\n⚠️  YAML validation errors ({len(yaml_errors)}):")
            for err in yaml_errors:
                print(f"   • {err}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
