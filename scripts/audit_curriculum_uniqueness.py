#!/usr/bin/env python3
"""
Audit Curriculum Plans for Vocabulary Uniqueness

Scans all CURRICULUM-PLAN.md files and identifies words listed as
'Core Vocabulary' in more than one module.

Output: Detailed JSON report + console summary
"""

import re
import sys
import json
from pathlib import Path
from collections import defaultdict

# Level order for determining earliest appearance
LEVEL_ORDER = ['A1', 'A2', 'B1', 'B2', 'C1', 'C2', 'LIT']


def get_level_order(level: str) -> int:
    """Get numeric order for level sorting."""
    try:
        return LEVEL_ORDER.index(level.upper())
    except ValueError:
        return 999  # Unknown levels sort last


def audit_uniqueness():
    project_root = Path(__file__).parent.parent
    plan_dir = project_root / "docs" / "l2-uk-en"

    # Find standard curriculum plans (A1-C2)
    plan_files = sorted(plan_dir.glob("*-CURRICULUM-PLAN.md"))
    plan_files = [f for f in plan_files if 'BACKUP' not in f.name]

    # Filter to standard levels only
    standard_levels = ['A1', 'A2', 'B1', 'B2', 'C1', 'C2']
    plan_files = [f for f in plan_files
                  if any(f.name.startswith(lvl) for lvl in standard_levels)]

    if not plan_files:
        print("❌ No curriculum plans found.")
        return

    print("=" * 80)
    print("CURRICULUM VOCABULARY UNIQUENESS AUDIT")
    print("=" * 80)
    print()
    print(f"📄 Found {len(plan_files)} curriculum plans:")
    for pf in plan_files:
        print(f"   - {pf.name}")
    print()

    # Map: word -> list of {level, module, title}
    global_vocab = defaultdict(list)
    level_stats = {}

    # Regex patterns
    module_pattern = re.compile(r'#### Module\s+(\d+):\s*(.+)')
    vocab_pattern = re.compile(r'\*\*Vocabulary\s+\(\d+\s+words?\):\*\*\s*\n(.*?)(?=\n\n|\n#|\Z)', re.DOTALL)

    # Parse each plan
    for plan_file in plan_files:
        level = plan_file.name.split("-")[0].upper()
        content = plan_file.read_text(encoding='utf-8')

        print(f"📖 Parsing {plan_file.name}...")

        # Split by module sections
        parts = re.split(r'(?=#### Module)', content)
        module_count = 0
        word_count = 0

        for part in parts:
            module_match = module_pattern.search(part)
            if not module_match:
                continue

            module_num = int(module_match.group(1))
            module_title = module_match.group(2).strip()

            vocab_match = vocab_pattern.search(part)
            if not vocab_match:
                continue

            # Extract and clean vocabulary
            raw_vocab = vocab_match.group(1).strip()
            # Remove parenthetical notes
            clean_vocab = re.sub(r'\([^)]*\)', '', raw_vocab)
            # Remove ellipsis
            clean_vocab = clean_vocab.replace('...', '')
            # Split and clean
            words = [w.strip().lower() for w in clean_vocab.split(',')
                    if w.strip() and not w.strip().startswith('[')]

            # Skip "Review selection" entries
            words = [w for w in words if 'review' not in w.lower()]

            module_count += 1
            word_count += len(words)

            for word in words:
                global_vocab[word].append({
                    'level': level,
                    'module': module_num,
                    'title': module_title
                })

        level_stats[level] = {
            'modules': module_count,
            'words': word_count
        }
        print(f"   ✓ {module_count} modules, {word_count} vocabulary words")

    print()
    print(f"📊 Total: {sum(s['modules'] for s in level_stats.values())} modules, "
          f"{sum(s['words'] for s in level_stats.values())} vocabulary words")
    print()

    # Identify duplicates
    print("🔍 Analyzing duplicates...")
    duplicates = {}

    for word, locs in global_vocab.items():
        if len(locs) > 1:
            # Sort by level order, then module number
            sorted_locs = sorted(locs, key=lambda x: (get_level_order(x['level']), x['module']))

            earliest = sorted_locs[0]
            later = sorted_locs[1:]

            duplicates[word] = {
                'total_appearances': len(locs),
                'earliest': earliest,
                'later_appearances': later,
                'recommendation': f"Keep {earliest['level']}-M{earliest['module']:02d} (first). "
                                 f"Review/remove {len(later)} later appearance(s)."
            }

    # Calculate statistics
    total_unique = len(global_vocab)
    duplicate_count = len(duplicates)
    duplicate_instances = sum(len(d['later_appearances']) for d in duplicates.values())

    # Level breakdown
    level_breakdown = defaultdict(int)
    for dup_info in duplicates.values():
        for app in dup_info['later_appearances']:
            level_breakdown[app['level']] += 1

    # Build report
    report = {
        'summary': {
            'total_unique_words': total_unique,
            'words_with_duplicates': duplicate_count,
            'total_duplicate_instances': duplicate_instances,
            'duplication_rate': f"{(duplicate_count / total_unique * 100):.1f}%"
        },
        'level_statistics': level_stats,
        'level_breakdown': dict(level_breakdown),
        'duplicates': duplicates
    }

    # Save JSON report
    output_path = project_root / 'curriculum_duplicates_report.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    # Display summary
    print()
    print("=" * 80)
    print("RESULTS SUMMARY")
    print("=" * 80)
    print()
    print(f"📚 Total unique words:              {total_unique:,}")
    print(f"🔁 Words with duplicates:           {duplicate_count:,}")
    print(f"📈 Total duplicate instances:       {duplicate_instances:,}")
    print(f"📊 Duplication rate:                {report['summary']['duplication_rate']}")
    print()

    if level_breakdown:
        print("Level-wise duplicate instances:")
        for level in LEVEL_ORDER:
            if level in level_breakdown:
                print(f"   {level}: {level_breakdown[level]} duplicate instances")
        print()

    # Show top 20 duplicates
    if duplicates:
        sorted_dups = sorted(
            duplicates.items(),
            key=lambda x: x[1]['total_appearances'],
            reverse=True
        )

        print("=" * 80)
        print("TOP 20 MOST DUPLICATED WORDS")
        print("=" * 80)
        print()

        for i, (word, info) in enumerate(sorted_dups[:20], 1):
            earliest = info['earliest']
            print(f"{i:2d}. '{word}' appears in {info['total_appearances']} modules:")
            print(f"    First:  {earliest['level']}-M{earliest['module']:02d} - {earliest['title']}")

            for app in info['later_appearances'][:3]:
                print(f"    Later:  {app['level']}-M{app['module']:02d} - {app['title']}")

            if len(info['later_appearances']) > 3:
                print(f"    ... and {len(info['later_appearances']) - 3} more")
            print()

    print("=" * 80)
    print(f"💾 Full report saved to: {output_path}")
    print("=" * 80)
    print()

    if duplicates:
        print("⚠️  DUPLICATES FOUND")
        print()
        print("Next steps:")
        print("1. Review curriculum_duplicates_report.json")
        print("2. Decide resolution strategy for each duplicate")
        print("3. Proceed to Phase 2: Blueprint Refactoring")
        print()
        sys.exit(1)
    else:
        print("✅ SUCCESS: No duplicate vocabulary found!")
        sys.exit(0)


if __name__ == "__main__":
    audit_uniqueness()
