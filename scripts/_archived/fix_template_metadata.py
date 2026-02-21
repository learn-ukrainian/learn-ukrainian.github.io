#!/usr/bin/env python3
"""
Fix template metadata to use Ukrainian-only section names for immersed levels (B1 M06+, B2, C1, C2, LIT).

Issue: Templates have English|Ukrainian alternatives, but immersed modules should validate against Ukrainian-only names.
"""

import re
from pathlib import Path

# Templates that need Ukrainian-only section names (100% immersion)
IMMERSED_TEMPLATES = [
    # B1 templates (M06-91 are immersed)
    'b1-grammar-module-template.md',
    'b1-vocab-module-template.md',
    'b1-cultural-module-template.md',
    'b1-integration-module-template.md',
    'b1-checkpoint-module-template.md',
    # B2 templates (all immersed)
    'b2-checkpoint-module-template.md',
    'b2-grammar-module-template.md',
    'b2-history-module-template.md',
    'b2-history-synthesis-module-template.md',
    'b2-integration-module-template.md',
    'b2-module-template.md',
    'b2-phraseology-module-template.md',
    'b2-synthesis-module-template.md',
    # C1 templates (all immersed)
    'c1-academic-module-template.md',
    'c1-biography-module-template.md',
    'c1-checkpoint-module-template.md',
    'c1-fine-arts-module-template.md',
    'c1-folk-culture-module-template.md',
    'c1-literature-module-template.md',
    'c1-module-template.md',
    'c1-sociolinguistics-module-template.md',
    # C2 templates (all immersed)
    'c2-checkpoint-module-template.md',
    'c2-literary-module-template.md',
    'c2-meta-skills-module-template.md',
    'c2-module-template.md',
    'c2-professional-module-template.md',
    'c2-style-module-template.md',
    # LIT track (post-C1, fully immersed)
    'lit-module-template.md',
]

# Section name mappings: English|Ukrainian → Ukrainian only
SECTION_REPLACEMENTS = {
    # Standard sections
    'Warm-up|Introduction|Objectives|Контекст|Вступ|Розминка|Тест': 'Вступ|Контекст|Розминка|Тест',
    'Warm-up|Introduction|Objectives|Контекст|Вступ|Розминка': 'Вступ|Контекст|Розминка',
    'Presentation|Grammar|Focus|Презентація|Граматика|Теорія|Пояснення': 'Пояснення|Граматика|Теорія',
    'Practice|Exercises|Activity|Практика|Вправи': 'Практика|Вправи',
    'Summary|Підсумок': 'Підсумок',
    'Need More Practice?|Потрібно більше практики?': 'Потрібно більше практики?',
    'Need More Practice?': 'Потрібно більше практики?',

    # Vocabulary specific
    'Vocabulary|Словник|Лексика': 'Словник|Лексика',
    'Usage|Вживання': 'Вживання',

    # Cultural/History specific
    'History and Culture|Історія та культура': 'Історія та культура',
    'Modern Context|Сучасність': 'Сучасність',
    'Reading|Читання': 'Читання',
}

def fix_template(template_path):
    """Remove English section names from template metadata."""
    content = template_path.read_text(encoding='utf-8')

    # Find TEMPLATE_METADATA block
    metadata_pattern = r'(<!--\s*TEMPLATE_METADATA:.*?-->)'
    match = re.search(metadata_pattern, content, re.DOTALL)

    if not match:
        return False

    metadata_block = match.group(1)
    original_metadata = metadata_block

    # Apply replacements
    modified = False
    for eng_ukr, ukr_only in SECTION_REPLACEMENTS.items():
        if eng_ukr in metadata_block:
            metadata_block = metadata_block.replace(eng_ukr, ukr_only)
            modified = True
            print(f"  Replaced: {eng_ukr[:50]}... → {ukr_only}")

    if modified:
        content = content.replace(original_metadata, metadata_block)
        template_path.write_text(content, encoding='utf-8')
        return True

    return False

def main():
    templates_dir = Path('docs/l2-uk-en/templates')

    print("Fixing template metadata for immersed levels (B1 M06+, B2, C1, C2, LIT)...\n")

    fixed_count = 0
    for template_name in IMMERSED_TEMPLATES:
        template_path = templates_dir / template_name
        if not template_path.exists():
            print(f"⚠️  Template not found: {template_name}")
            continue

        print(f"Processing {template_name}...")
        if fix_template(template_path):
            fixed_count += 1
            print(f"  ✅ Fixed\n")
        else:
            print(f"  ℹ️  No changes needed\n")

    print(f"\nDone: Fixed {fixed_count}/{len(IMMERSED_TEMPLATES)} templates")
    print("\nNext steps:")
    print("1. Re-audit B1, B2, C1 levels to get accurate violation counts")
    print("2. Update GitHub issues with real numbers")
    print("3. Start fixing modules based on correct baseline")

if __name__ == '__main__':
    main()
