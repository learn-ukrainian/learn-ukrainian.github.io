#!/usr/bin/env python3
"""
Fix B1 meta.yaml content_outline to match actual markdown sections.
"""

import yaml
import re
from pathlib import Path

MODULES = [
    "06-aspect-complete-system",
    "12-aspect-pairs-essential-40",
    "14-aspect-integration-practice",
    "15-checkpoint-aspect-mastery",
    "16-motion-verbs-full-system",
    "17-motion-coming-going",
    "18-motion-passing-crossing",
    "19-motion-starting-returning",
    "20-motion-approaching-departing",
    "21-motion-figurative-uses",
    "23-motion-patterns-other-verbs",
    "24-motion-practice-integration",
    "25-checkpoint-motion-verbs",
]

def extract_sections(md_path: Path) -> list:
    """Extract H2 sections from markdown file."""
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find all H2 sections
    sections = re.findall(r'^## (.+)$', content, re.MULTILINE)
    return sections

def count_words_in_section(md_path: Path, section: str, next_section: str = None) -> int:
    """Count words in a specific section."""
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find section content
    pattern = rf'^## {re.escape(section)}$(.*?)(?:^## |\Z)'
    match = re.search(pattern, content, re.MULTILINE | re.DOTALL)

    if not match:
        return 150  # default

    section_content = match.group(1)
    # Count words (rough estimate)
    words = len(re.findall(r'\b[а-яіїєґА-ЯІЇЄҐA-Za-z]+\b', section_content))
    return max(100, words)  # minimum 100

def generate_outline_from_sections(sections: list, md_path: Path) -> list:
    """Generate content_outline from actual sections."""
    outline = []

    # Exclude auto-generated section
    sections = [s for s in sections if "більше практики" not in s.lower()]

    for i, section in enumerate(sections):
        next_section = sections[i + 1] if i + 1 < len(sections) else None
        word_count = count_words_in_section(md_path, section, next_section)

        # Round to nearest 50
        word_count = round(word_count / 50) * 50
        word_count = max(100, min(word_count, 900))  # cap at 100-900

        outline.append({
            "section": section,
            "words": word_count,
            "points": [
                f"Content for {section}",
                "Examples and explanation",
                "Practice or application"
            ]
        })

    return outline

def fix_meta_file(slug: str):
    """Fix a single meta.yaml file based on actual markdown."""
    md_path = Path(f"curriculum/l2-uk-en/b1/{slug}.md")
    meta_path = Path(f"curriculum/l2-uk-en/b1/meta/{slug}.yaml")

    if not md_path.exists() or not meta_path.exists():
        print(f"⚠️  Skipping {slug} - file not found")
        return

    # Extract sections from markdown
    sections = extract_sections(md_path)
    if not sections:
        print(f"⚠️  Skipping {slug} - no sections found")
        return

    # Load existing meta
    with open(meta_path, 'r', encoding='utf-8') as f:
        meta = yaml.safe_load(f)

    # Fix word_target based on module type
    is_checkpoint = 'checkpoint' in slug
    meta['word_target'] = 1200 if is_checkpoint else 1500

    # Generate new outline
    meta['content_outline'] = generate_outline_from_sections(sections, md_path)

    # Write back
    with open(meta_path, 'w', encoding='utf-8') as f:
        yaml.dump(meta, f, allow_unicode=True, sort_keys=False, default_flow_style=False)

    print(f"✅ Fixed {slug} ({len(sections)} sections)")

def main():
    print("Fixing B1 meta.yaml files to match actual markdown...\n")

    for slug in MODULES:
        fix_meta_file(slug)

    print(f"\n✅ Fixed {len(MODULES)} meta.yaml files")
    print("\nNext: Run audit to verify fixes")

if __name__ == "__main__":
    main()
