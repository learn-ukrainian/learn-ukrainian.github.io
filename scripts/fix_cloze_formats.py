#!/usr/bin/env python3
"""
Fix Cloze Format Issues in B1 Modules

Detects and converts wrong cloze formats to the documented standard:
- [___:N] with numbered option lists

Handles:
- [___:answer] format (M17 style)
- [N:answer] format (M18/M21 style)

Usage:
    python scripts/fix_cloze_formats.py --scan       # Scan and report issues
    python scripts/fix_cloze_formats.py --fix M18    # Fix specific module
    python scripts/fix_cloze_formats.py --fix-all    # Fix all issues
"""

import re
import sys
from pathlib import Path
from typing import List, Dict, Tuple

def detect_cloze_format(content: str) -> str:
    """
    Detect which cloze format is used in the content.

    Returns:
        'correct' - [___:N] with option lists
        'named_blanks' - [___:answer] without numbers
        'numbered_inline' - [N:answer] without ___
        'none' - No cloze activity found
    """
    # Check for correct format: [___:1] [___:2] etc
    if re.search(r'\[___:\d+\]', content):
        return 'correct'

    # Check for named blanks: [___:answer]
    if re.search(r'\[___:[а-яіїєґА-ЯІЇЄҐ]', content):
        return 'named_blanks'

    # Check for numbered inline: [1:answer] [2:answer]
    if re.search(r'\[\d+:[а-яіїєґА-ЯІЇЄҐ]', content):
        return 'numbered_inline'

    return 'none'


def extract_cloze_activity(module_path: Path) -> Tuple[str, int, int] | None:
    """
    Extract cloze activity section from module.

    Returns:
        (activity_text, start_line, end_line) or None if not found
    """
    content = module_path.read_text(encoding='utf-8')
    lines = content.split('\n')

    # Find cloze activity
    start_line = None
    for i, line in enumerate(lines):
        if line.startswith('## cloze:'):
            start_line = i
            break

    if start_line is None:
        return None

    # Find end of activity (next ## or # header)
    end_line = len(lines)
    for i in range(start_line + 1, len(lines)):
        if lines[i].startswith('## ') or lines[i].startswith('# '):
            end_line = i
            break

    activity_text = '\n'.join(lines[start_line:end_line])
    return (activity_text, start_line, end_line)


def scan_all_modules(b1_dir: Path) -> Dict[str, str]:
    """
    Scan all B1 modules and report cloze format issues.

    Returns:
        Dict mapping module name to format type
    """
    results = {}

    for md_file in sorted(b1_dir.glob('*.md')):
        content = md_file.read_text(encoding='utf-8')

        # Only check if module has cloze activity
        if '## cloze:' not in content:
            continue

        format_type = detect_cloze_format(content)
        results[md_file.name] = format_type

    return results


def generate_report(results: Dict[str, str]) -> str:
    """Generate a report of cloze format issues."""
    report = []
    report.append("# B1 Cloze Format Scan Report\n")

    correct = [m for m, f in results.items() if f == 'correct']
    named = [m for m, f in results.items() if f == 'named_blanks']
    numbered = [m for m, f in results.items() if f == 'numbered_inline']

    report.append(f"## Summary\n")
    report.append(f"- ✅ Correct format `[___:N]`: {len(correct)} modules")
    report.append(f"- ⚠️  Named blanks `[___:answer]`: {len(named)} modules")
    report.append(f"- ⚠️  Numbered inline `[N:answer]`: {len(numbered)} modules\n")

    if named:
        report.append(f"## Named Blanks Format (needs fixing)\n")
        for module in named:
            report.append(f"- {module}")
        report.append("")

    if numbered:
        report.append(f"## Numbered Inline Format (needs fixing)\n")
        for module in numbered:
            report.append(f"- {module}")
        report.append("")

    report.append(f"## Modules with Correct Format\n")
    for module in correct[:5]:
        report.append(f"- {module}")
    if len(correct) > 5:
        report.append(f"- ...and {len(correct) - 5} more")

    return '\n'.join(report)


def main():
    """Main entry point."""
    b1_dir = Path('curriculum/l2-uk-en/b1')

    if not b1_dir.exists():
        print(f"Error: {b1_dir} not found")
        sys.exit(1)

    # Default: scan and report
    if len(sys.argv) == 1 or '--scan' in sys.argv:
        print("Scanning B1 modules for cloze format issues...\n")
        results = scan_all_modules(b1_dir)
        report = generate_report(results)
        print(report)

        # Save report
        report_path = Path('curriculum/l2-uk-en/b1/cloze-format-report.md')
        report_path.write_text(report, encoding='utf-8')
        print(f"\nReport saved to: {report_path}")

    elif '--fix' in sys.argv:
        print("Manual conversion recommended for now.")
        print("Auto-conversion requires generating appropriate distractors.")
        print("\nFor M18 and M21: Convert [N:answer] to [___:N] with option lists manually.")

    elif '--fix-all' in sys.argv:
        print("Manual conversion recommended for now.")
        print("Auto-conversion requires generating appropriate distractors.")

    else:
        print(__doc__)


if __name__ == '__main__':
    main()
