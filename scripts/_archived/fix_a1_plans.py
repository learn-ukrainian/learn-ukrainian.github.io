#!/usr/bin/env python3
"""
Fix A1 plans to match actual markdown structure.

Problems being fixed:
1. content_outline sections don't match markdown H2 headers
2. activity_hints contain invalid types

This script:
- Reads each A1 markdown file
- Extracts H2 sections and word counts
- Updates the plan's content_outline to match
- Replaces invalid activity types with valid ones
"""

import re
import sys
from pathlib import Path
import yaml

# Valid activity types
VALID_TYPES = {
    'match-up', 'fill-in', 'quiz', 'true-false', 'group-sort',
    'unjumble', 'error-correction', 'anagram', 'select', 'translate',
    'cloze', 'mark-the-words', 'reading', 'essay-response',
    'critical-analysis', 'comparative-study', 'authorial-intent'
}

# Mapping from invalid to valid types
TYPE_MAPPING = {
    'letter-recognition': 'quiz',
    'audio-match': 'match-up',
    'minimal-pairs': 'group-sort',
    'reading-drill': 'quiz',
    'sorting': 'group-sort',
    'dialogue': 'fill-in',
    'translation': 'translate',
    'role-play': 'fill-in',
    'labeling': 'match-up',
    'conjugation-drill': 'fill-in',
    'matching': 'match-up',
    'question-formation': 'fill-in',
    'transformation': 'fill-in',
    'sentence-building': 'unjumble',
    'word-building': 'anagram',
    'ordering': 'unjumble',
    'listening': 'quiz',
    'reading-comprehension': 'quiz',
    'vocabulary-review': 'match-up',
    'grammar-drill': 'fill-in',
    'sentence-completion': 'fill-in',
    'gap-fill': 'fill-in',
    'multiple-choice': 'quiz',
    'word-formation': 'anagram',
    'map-activity': 'match-up',
    'number-drill': 'fill-in',
    'vocabulary-drill': 'match-up',
    'categorization': 'group-sort',
    'speaking': 'fill-in',
    'description': 'fill-in',
    'problem-solving': 'quiz',
}

# Sections to exclude from content_outline (boilerplate)
EXCLUDED_SECTIONS = {
    'need more practice?',
    'підсумок',
    'summary',
}


def count_words(text: str) -> int:
    """Count words in text, excluding markdown syntax."""
    # Remove code blocks
    text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
    # Remove inline code
    text = re.sub(r'`[^`]+`', '', text)
    # Remove links but keep text
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    # Remove images
    text = re.sub(r'!\[[^\]]*\]\([^)]+\)', '', text)
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Remove table separators
    text = re.sub(r'\|[-:]+\|', '', text)
    # Count remaining words
    words = re.findall(r'\b\w+\b', text)
    return len(words)


def extract_sections_from_markdown(md_path: Path) -> list[dict]:
    """Extract H2 sections and their word counts from markdown."""
    content = md_path.read_text(encoding='utf-8')

    # Split by H2 headers
    sections = []
    h2_pattern = r'^## (.+)$'

    lines = content.split('\n')
    current_section = None
    current_content = []

    for line in lines:
        match = re.match(h2_pattern, line)
        if match:
            # Save previous section
            if current_section:
                section_text = '\n'.join(current_content)
                word_count = count_words(section_text)
                if current_section.lower() not in EXCLUDED_SECTIONS:
                    sections.append({
                        'section': current_section,
                        'words': word_count,
                    })
            current_section = match.group(1).strip()
            current_content = []
        elif current_section:
            current_content.append(line)

    # Don't forget the last section
    if current_section:
        section_text = '\n'.join(current_content)
        word_count = count_words(section_text)
        if current_section.lower() not in EXCLUDED_SECTIONS:
            sections.append({
                'section': current_section,
                'words': word_count,
            })

    return sections


def fix_activity_hints(hints: list) -> list:
    """Replace invalid activity types with valid ones."""
    if not hints:
        return hints

    fixed = []
    for hint in hints:
        if isinstance(hint, dict) and 'type' in hint:
            old_type = hint['type']
            if old_type in TYPE_MAPPING:
                hint = hint.copy()
                hint['type'] = TYPE_MAPPING[old_type]
                print(f"    Activity type: {old_type} -> {hint['type']}")
            elif old_type not in VALID_TYPES:
                print(f"    WARNING: Unknown activity type: {old_type}")
        fixed.append(hint)
    return fixed


def update_plan(plan_path: Path, sections: list[dict], dry_run: bool = False) -> bool:
    """Update plan's content_outline to match extracted sections."""
    content = plan_path.read_text(encoding='utf-8')
    plan = yaml.safe_load(content)

    if not plan:
        print(f"  ERROR: Could not parse {plan_path}")
        return False

    # Check if content_outline needs updating
    old_outline = plan.get('content_outline', [])
    old_sections = [s.get('section', '') for s in old_outline]
    new_sections = [s['section'] for s in sections]

    outline_changed = old_sections != new_sections

    # Check activity_hints
    old_hints = plan.get('activity_hints', [])
    new_hints = fix_activity_hints(old_hints)
    hints_changed = old_hints != new_hints

    if not outline_changed and not hints_changed:
        print(f"  SKIP: Already aligned")
        return False

    # Update content_outline
    if outline_changed:
        # Preserve points from old outline where section names match
        old_by_name = {s.get('section', ''): s for s in old_outline}

        for section in sections:
            old_section = old_by_name.get(section['section'])
            if old_section and 'points' in old_section:
                section['points'] = old_section['points']
            else:
                # Generate placeholder points
                section['points'] = [f"Content for {section['section']}"]

        plan['content_outline'] = sections

        # Update word_target to match sum of sections
        total_words = sum(s['words'] for s in sections)
        plan['word_target'] = total_words

        print(f"  Updated content_outline: {len(old_outline)} -> {len(sections)} sections")
        print(f"  Updated word_target: {plan.get('word_target', 'N/A')} -> {total_words}")

    if hints_changed:
        plan['activity_hints'] = new_hints
        print(f"  Fixed activity_hints")

    if dry_run:
        print(f"  DRY RUN: Would write to {plan_path}")
        return True

    # Write back with preserved formatting
    with open(plan_path, 'w', encoding='utf-8') as f:
        yaml.dump(plan, f, allow_unicode=True, default_flow_style=False, sort_keys=False, width=120)

    return True


def main():
    dry_run = '--dry-run' in sys.argv

    base_path = Path('curriculum/l2-uk-en')
    a1_md_path = base_path / 'a1'
    a1_plans_path = base_path / 'plans' / 'a1'

    if not a1_md_path.exists():
        print(f"ERROR: {a1_md_path} not found")
        sys.exit(1)

    if not a1_plans_path.exists():
        print(f"ERROR: {a1_plans_path} not found")
        sys.exit(1)

    # Get all markdown files
    md_files = sorted(a1_md_path.glob('*.md'))

    updated = 0
    skipped = 0
    errors = 0

    for md_file in md_files:
        # Extract slug from filename (e.g., 02-the-cyrillic-code-ii.md -> 02-the-cyrillic-code-ii)
        slug = md_file.stem
        plan_file = a1_plans_path / f"{slug}.yaml"

        print(f"\n{slug}:")

        if not plan_file.exists():
            print(f"  SKIP: No plan file")
            skipped += 1
            continue

        # Extract sections from markdown
        sections = extract_sections_from_markdown(md_file)

        if not sections:
            print(f"  SKIP: No H2 sections found")
            skipped += 1
            continue

        # Check if markdown uses PPP structure
        section_names = [s['section'] for s in sections]
        has_ppp = any(name in ['Warm-up', 'Presentation', 'Practice'] for name in section_names)

        if not has_ppp:
            print(f"  SKIP: Markdown doesn't use PPP structure")
            skipped += 1
            continue

        try:
            if update_plan(plan_file, sections, dry_run):
                updated += 1
            else:
                skipped += 1
        except Exception as e:
            print(f"  ERROR: {e}")
            errors += 1

    print(f"\n{'='*50}")
    print(f"Summary: {updated} updated, {skipped} skipped, {errors} errors")
    if dry_run:
        print("(DRY RUN - no files were modified)")


if __name__ == '__main__':
    main()
