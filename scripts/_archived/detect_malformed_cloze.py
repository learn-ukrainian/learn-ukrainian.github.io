#!/usr/bin/env python3
"""
Detect malformed cloze activities where options are full sentences instead of single words.

A cloze blank should contain word/phrase options, not full sentences.
We detect this by checking if options are unusually long (>30 chars) or contain
sentence-ending punctuation like ? ! .
"""

import re
import sys
from pathlib import Path
import yaml

# Regex to find cloze blanks: {option1|option2|...}
CLOZE_BLANK_PATTERN = re.compile(r'\{([^}]+)\}')

# Thresholds for detecting sentence-like options
MAX_OPTION_LENGTH = 35  # Words/phrases are typically under 35 chars
SENTENCE_ENDINGS = ['?', '!']  # Question marks and exclamations are strong signals
WEAK_ENDINGS = ['.']  # Periods only count with other signals

def check_cloze_activity(activity: dict, file_path: Path, activity_index: int) -> list:
    """Check a single cloze activity for malformed options."""
    issues = []

    if activity.get('type') != 'cloze':
        return issues

    passage = activity.get('passage', '')
    title = activity.get('title', f'Activity #{activity_index}')

    # Find all cloze blanks
    blanks = CLOZE_BLANK_PATTERN.findall(passage)

    for blank_idx, blank_content in enumerate(blanks):
        options = [opt.strip() for opt in blank_content.split('|')]

        for opt_idx, option in enumerate(options):
            # Skip placeholder options like "--" or empty
            if option in ['--', '-', ''] or len(option) < 3:
                continue

            # Strong signals: question marks, exclamation marks (these should never be in cloze options)
            has_strong_sentence_ending = any(option.rstrip().endswith(p) for p in SENTENCE_ENDINGS)

            # Moderate signals
            is_too_long = len(option) > MAX_OPTION_LENGTH
            has_weak_ending = any(option.rstrip().endswith(p) for p in WEAK_ENDINGS)
            has_many_words = len(option.split()) > 4

            # Issue if: strong ending OR (too long) OR (weak ending + many words)
            is_malformed = (
                has_strong_sentence_ending or
                is_too_long or
                (has_weak_ending and has_many_words)
            )

            if is_malformed:
                reason = 'sentence_ending' if has_strong_sentence_ending else ('too_long' if is_too_long else 'sentence_like')
                issues.append({
                    'file': str(file_path),
                    'title': title,
                    'blank_num': blank_idx + 1,
                    'option': option,
                    'reason': reason,
                    'length': len(option)
                })

    return issues

def scan_file(file_path: Path) -> list:
    """Scan a single YAML file for malformed cloze activities."""
    issues = []

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            activities = yaml.safe_load(f)

        if not isinstance(activities, list):
            return issues

        for idx, activity in enumerate(activities):
            if isinstance(activity, dict):
                issues.extend(check_cloze_activity(activity, file_path, idx))

    except Exception as e:
        print(f"Error processing {file_path}: {e}", file=sys.stderr)

    return issues

def main():
    """Scan all activity YAML files for malformed cloze activities."""
    base_path = Path('curriculum/l2-uk-en')

    all_issues = []
    files_scanned = 0

    for level in ['a1', 'a2', 'b1', 'b2', 'c1', 'c2']:
        activities_dir = base_path / level / 'activities'
        if not activities_dir.exists():
            continue

        for yaml_file in sorted(activities_dir.glob('*.yaml')):
            files_scanned += 1
            issues = scan_file(yaml_file)
            all_issues.extend(issues)

    # Report results
    print(f"\n{'='*70}")
    print(f"MALFORMED CLOZE DETECTION REPORT")
    print(f"{'='*70}")
    print(f"Files scanned: {files_scanned}")
    print(f"Total issues found: {len(all_issues)}")

    if all_issues:
        # Group by file
        by_file = {}
        for issue in all_issues:
            f = issue['file']
            if f not in by_file:
                by_file[f] = []
            by_file[f].append(issue)

        print(f"\n{'='*70}")
        print("ISSUES BY FILE:")
        print(f"{'='*70}\n")

        for file_path, issues in sorted(by_file.items()):
            print(f"\n📄 {file_path}")
            for issue in issues:
                print(f"   └─ [{issue['title']}] Blank #{issue['blank_num']}: \"{issue['option'][:50]}...\" ({issue['length']} chars)")

        # Summary by level
        print(f"\n{'='*70}")
        print("SUMMARY BY LEVEL:")
        print(f"{'='*70}")

        by_level = {}
        for issue in all_issues:
            level = issue['file'].split('/')[2]  # Extract level from path
            by_level[level] = by_level.get(level, 0) + 1

        for level, count in sorted(by_level.items()):
            print(f"  {level.upper()}: {count} issues")
    else:
        print("\n✅ No malformed cloze activities found!")

    return len(all_issues)

if __name__ == '__main__':
    sys.exit(0 if main() == 0 else 1)
