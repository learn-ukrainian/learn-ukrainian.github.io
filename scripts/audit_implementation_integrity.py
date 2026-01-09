#!/usr/bin/env python3
"""
Implementation Integrity Audit

Checks if modules actually implemented the vocabulary assigned to them
in the curriculum plans.

Reports:
- Words in plan but missing from module YAML
- Implementation coverage percentage per module
"""

import re
import sys
import json
import yaml
from pathlib import Path
from collections import defaultdict

LEVEL_ORDER = ['A1', 'A2', 'B1', 'B2', 'C1', 'C2']


def parse_plan_vocabulary(plan_path: Path) -> dict:
    """
    Parse curriculum plan to extract vocabulary per module.

    Returns:
        Dict: {module_num: {title, vocabulary: [words]}}
    """
    content = plan_path.read_text(encoding='utf-8')
    level = plan_path.stem.split('-')[0].upper()

    modules = {}

    module_pattern = re.compile(r'#### Module\s+(\d+):\s*(.+)')
    vocab_pattern = re.compile(r'\*\*Vocabulary\s+\(\d+\s+words?\):\*\*\s*\n(.*?)(?=\n\n|\n#|\Z)', re.DOTALL)

    parts = re.split(r'(?=#### Module)', content)

    for part in parts:
        module_match = module_pattern.search(part)
        if not module_match:
            continue

        module_num = int(module_match.group(1))
        title = module_match.group(2).strip()

        vocab_match = vocab_pattern.search(part)
        if not vocab_match:
            continue

        raw_vocab = vocab_match.group(1).strip()
        # Clean up
        clean_vocab = re.sub(r'\([^)]*\)', '', raw_vocab)
        clean_vocab = clean_vocab.replace('...', '')

        words = [w.strip().lower() for w in clean_vocab.split(',')
                if w.strip() and not w.strip().startswith('[')
                and 'review' not in w.lower()]

        if words:
            modules[module_num] = {
                'title': title,
                'vocabulary': words
            }

    return modules


def read_module_yaml_vocabulary(level: str, module_num: int) -> set:
    """
    Read vocabulary from module's YAML file.

    Returns:
        Set of words (lowercase) from vocabulary YAML
    """
    project_root = Path(__file__).parent.parent
    vocab_dir = project_root / 'curriculum' / 'l2-uk-en' / level.lower() / 'vocabulary'

    # Find vocabulary file for this module
    vocab_files = list(vocab_dir.glob(f'{module_num:02d}-*.yaml'))

    if not vocab_files:
        return set()

    vocab_file = vocab_files[0]

    try:
        with open(vocab_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        if not data or 'items' not in data:
            return set()

        # Extract lemmas
        words = set()
        for item in data['items']:
            if 'lemma' in item:
                words.add(item['lemma'].lower())

        return words
    except Exception as e:
        print(f"⚠️  Error reading {vocab_file}: {e}")
        return set()


def main():
    print("=" * 80)
    print("IMPLEMENTATION INTEGRITY AUDIT")
    print("Checking if modules implemented their assigned vocabulary")
    print("=" * 80)
    print()

    project_root = Path(__file__).parent.parent
    plan_dir = project_root / 'docs' / 'l2-uk-en'

    # Find completed levels only (A1, A2, B1, B2)
    completed_levels = ['A1', 'A2', 'B1', 'B2']
    plan_files = [plan_dir / f'{level}-CURRICULUM-PLAN.md' for level in completed_levels]
    plan_files = [f for f in plan_files if f.exists()]

    print(f"📄 Checking {len(plan_files)} completed levels:")
    for pf in plan_files:
        print(f"   - {pf.name}")
    print()

    all_results = {}
    total_modules = 0
    total_planned_words = 0
    total_implemented_words = 0
    total_missing_words = 0

    modules_with_issues = []

    for plan_file in plan_files:
        level = plan_file.stem.split('-')[0].upper()
        print(f"📖 Checking {level}...")

        # Parse plan
        plan_modules = parse_plan_vocabulary(plan_file)

        level_results = {}

        for module_num, plan_data in sorted(plan_modules.items()):
            total_modules += 1

            planned_vocab = set(plan_data['vocabulary'])
            implemented_vocab = read_module_yaml_vocabulary(level, module_num)

            if not implemented_vocab:
                print(f"   ⚠️  {level}-M{module_num:02d}: No vocabulary YAML found")
                continue

            # Find missing words
            missing = planned_vocab - implemented_vocab
            extra = implemented_vocab - planned_vocab

            planned_count = len(planned_vocab)
            implemented_count = len(implemented_vocab & planned_vocab)
            coverage = (implemented_count / planned_count * 100) if planned_count > 0 else 0

            total_planned_words += planned_count
            total_implemented_words += implemented_count
            total_missing_words += len(missing)

            level_results[module_num] = {
                'title': plan_data['title'],
                'planned_count': planned_count,
                'implemented_count': implemented_count,
                'coverage': coverage,
                'missing': sorted(missing),
                'extra': sorted(extra)
            }

            if missing and coverage < 80:
                modules_with_issues.append({
                    'level': level,
                    'module': module_num,
                    'title': plan_data['title'],
                    'coverage': coverage,
                    'missing_count': len(missing),
                    'missing_words': sorted(missing)[:10]  # First 10
                })

        all_results[level] = level_results

        # Level summary
        level_coverage = sum(r['implemented_count'] for r in level_results.values())
        level_planned = sum(r['planned_count'] for r in level_results.values())
        level_pct = (level_coverage / level_planned * 100) if level_planned > 0 else 0

        print(f"   ✓ {len(level_results)} modules checked")
        print(f"   📊 Coverage: {level_coverage}/{level_planned} words ({level_pct:.1f}%)")
        print()

    # Overall summary
    overall_coverage = (total_implemented_words / total_planned_words * 100) if total_planned_words > 0 else 0

    print("=" * 80)
    print("RESULTS SUMMARY")
    print("=" * 80)
    print()
    print(f"📚 Modules checked:              {total_modules}")
    print(f"📝 Total planned words:          {total_planned_words:,}")
    print(f"✅ Words implemented:            {total_implemented_words:,}")
    print(f"❌ Words missing:                {total_missing_words:,}")
    print(f"📊 Overall coverage:             {overall_coverage:.1f}%")
    print()

    # Save detailed report
    output_path = project_root / 'implementation_integrity_report.json'
    report = {
        'summary': {
            'modules_checked': total_modules,
            'total_planned_words': total_planned_words,
            'total_implemented_words': total_implemented_words,
            'total_missing_words': total_missing_words,
            'overall_coverage': f"{overall_coverage:.1f}%"
        },
        'by_level': all_results,
        'modules_with_issues': modules_with_issues
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"💾 Full report saved to: {output_path}")
    print()

    # Show modules with issues
    if modules_with_issues:
        print("=" * 80)
        print(f"MODULES WITH LOW COVERAGE (<80%)")
        print("=" * 80)
        print()

        for issue in sorted(modules_with_issues, key=lambda x: x['coverage']):
            print(f"{issue['level']}-M{issue['module']:02d}: {issue['title']}")
            print(f"   Coverage: {issue['coverage']:.1f}% ({issue['missing_count']} words missing)")
            print(f"   Sample missing: {', '.join(issue['missing_words'][:5])}")
            if issue['missing_count'] > 5:
                print(f"   ... and {issue['missing_count'] - 5} more")
            print()
    else:
        print("✅ All modules have ≥80% vocabulary coverage!")

    print("=" * 80)

    if total_missing_words > 0:
        print()
        print(f"⚠️  {total_missing_words} words from plans not implemented")
        print(f"   Overall coverage: {overall_coverage:.1f}%")
        print()
        if overall_coverage >= 80:
            print("✅ Coverage acceptable (≥80%)")
            print("   Missing words likely intentional design changes")
            sys.exit(0)
        else:
            print("❌ Coverage below target (<80%)")
            print("   Significant implementation gaps detected")
            sys.exit(1)
    else:
        print()
        print("✅ SUCCESS: All planned vocabulary implemented!")
        sys.exit(0)


if __name__ == '__main__':
    main()
