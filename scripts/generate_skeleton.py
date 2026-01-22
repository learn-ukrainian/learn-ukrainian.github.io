#!/usr/bin/env python3
"""
Generate module skeleton from curriculum plan and template.

Usage:
    python3 scripts/generate_skeleton.py <curriculum> <level> <module_num>
    python3 scripts/generate_skeleton.py l2-uk-en b1 43

Reads:
- docs/l2-uk-en/{LEVEL}-CURRICULUM-PLAN.md
- docs/l2-uk-en/templates/{level}-{type}-module-template.md

Outputs:
- curriculum/l2-uk-en/{level}/{NN}-{slug}-skeleton.md

The skeleton includes:
- Frontmatter from curriculum plan
- Section headers from template
- Vocabulary table structure
- Activity placeholders with specs
- Word count targets
"""

import sys
import re
from pathlib import Path
from datetime import datetime


def slugify(text: str) -> str:
    """Convert text to URL-friendly slug."""
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    text = re.sub(r'-+', '-', text)
    return text.strip('-')


def determine_module_type(level: str, module_num: int) -> str:
    """Determine module type based on level and number."""
    level = level.upper()

    if level == 'A1':
        return 'a1'
    elif level == 'A2':
        return 'a2'
    elif level == 'B1':
        if module_num <= 5:
            return 'b1-metalanguage'
        elif module_num in (15, 25, 34, 41, 51):
            return 'b1-checkpoint'
        elif module_num <= 51:
            return 'b1-grammar'
        elif module_num <= 71:
            return 'b1-vocab'
        elif module_num <= 81:
            return 'b1-cultural'
        else:
            return 'b1-integration'
    elif level == 'B2':
        if module_num in (15, 30, 45, 60, 75, 90, 110):
            return 'b2-checkpoint'
        return 'b2-grammar'
    elif level == 'B2-HIST':
        return 'b2-history'
    elif level == 'C1':
        return 'c1'
    elif level == 'C2':
        return 'c2'
    else:
        return level.lower()


def get_template_path(level: str, module_type: str) -> Path:
    """Get path to appropriate template."""
    base = Path('docs/l2-uk-en/templates')

    # Map module types to template files
    type_to_template = {
        'a1': 'a1-module-template.md',
        'a2': 'a2-module-template.md',
        'b1-metalanguage': 'b1-metalanguage-module-template.md',
        'b1-grammar': 'b1-grammar-module-template.md',
        'b1-vocab': 'b1-vocab-module-template.md',
        'b1-checkpoint': 'b1-checkpoint-module-template.md',
        'b1-cultural': 'b1-cultural-module-template.md',
        'b1-integration': 'b1-integration-module-template.md',
        'b2-grammar': 'b2-grammar-module-template.md',
        'b2-checkpoint': 'b2-checkpoint-module-template.md',
        'b2-history': 'b2-history-module-template.md',
        'c1': 'c1-module-template.md',
        'c2': 'c2-module-template.md',
    }

    template_file = type_to_template.get(module_type, f'{level.lower()}-module-template.md')
    return base / template_file


def get_curriculum_plan_path(curriculum: str, level: str) -> Path:
    """Get path to curriculum plan."""
    return Path(f'docs/{curriculum}/{level.upper()}-CURRICULUM-PLAN.md')


def parse_curriculum_plan(plan_path: Path, module_num: int) -> dict:
    """Extract module info from curriculum plan."""
    if not plan_path.exists():
        return {}

    content = plan_path.read_text(encoding='utf-8')

    # Find module section
    # Pattern: | NN | Title | focus | grammar | vocab |
    pattern = rf'\|\s*{module_num:02d}?\s*\|\s*([^|]+)\|([^|]*)\|([^|]*)\|([^|]*)\|'
    match = re.search(pattern, content)

    if not match:
        # Try without leading zero
        pattern = rf'\|\s*{module_num}\s*\|\s*([^|]+)\|([^|]*)\|([^|]*)\|([^|]*)\|'
        match = re.search(pattern, content)

    if match:
        return {
            'title': match.group(1).strip(),
            'focus': match.group(2).strip(),
            'grammar': match.group(3).strip(),
            'vocab_notes': match.group(4).strip(),
        }

    return {}


def get_word_targets(level: str, module_type: str) -> dict:
    """Get word count targets by level and type."""
    targets = {
        'a1': {'total': 750, 'presentation': 400, 'practice': 200, 'summary': 100},
        'a2': {'total': 1000, 'presentation': 500, 'practice': 300, 'summary': 100},
        'b1-metalanguage': {'total': 1200, 'test': 150, 'explanation': 700, 'practice': 200, 'summary': 100},
        'b1-grammar': {'total': 1500, 'test': 150, 'explanation': 900, 'practice': 250, 'summary': 150},
        'b1-vocab': {'total': 1500, 'test': 150, 'explanation': 900, 'practice': 250, 'summary': 150},
        'b1-checkpoint': {'total': 800, 'overview': 200, 'skills': 400, 'summary': 100},
        'b1-cultural': {'total': 1500, 'test': 150, 'content': 1000, 'practice': 200, 'summary': 100},
        'b1-integration': {'total': 1200, 'overview': 300, 'review': 600, 'summary': 150},
        'b2-grammar': {'total': 1750, 'test': 150, 'explanation': 1100, 'practice': 300, 'summary': 150},
        'b2-checkpoint': {'total': 1000, 'overview': 200, 'skills': 500, 'summary': 150},
        'c1': {'total': 2000, 'content': 1400, 'practice': 400, 'summary': 150},
        'c2': {'total': 2000, 'content': 1400, 'practice': 400, 'summary': 150},
    }
    return targets.get(module_type, targets.get(level.lower(), targets['b1-grammar']))


def get_activity_specs(level: str, module_type: str) -> list:
    """Get activity specifications for level."""
    specs = {
        'a1': [
            ('quiz', 12, 'Multiple choice recognition'),
            ('match-up', 12, 'Word-meaning pairs'),
            ('fill-in', 12, 'Gap completion'),
            ('group-sort', 14, 'Category sorting'),
            ('unjumble', 8, 'Word ordering (6-8 words)'),
            ('true-false', 12, 'Statement validation'),
            ('anagram', 10, 'Letter unscrambling (M01-10 only)'),
        ],
        'a2': [
            ('quiz', 12, 'Multiple choice'),
            ('match-up', 12, 'Pairs'),
            ('fill-in', 12, 'Gap completion'),
            ('group-sort', 14, 'Sorting'),
            ('unjumble', 8, 'Word ordering (10-12 words)'),
            ('true-false', 12, 'Validation'),
            ('error-correction', 8, 'Find and fix (REQUIRED)'),
            ('cloze', 14, 'Passage completion'),
            ('mark-the-words', 10, 'Click matching'),
        ],
        'b1': [
            ('quiz', 12, 'Multiple choice'),
            ('match-up', 14, 'Pairs'),
            ('fill-in', 14, 'Gap completion (10-14 words)'),
            ('group-sort', 16, 'Sorting'),
            ('unjumble', 10, 'Word ordering (12-16 words)'),
            ('true-false', 12, 'Validation'),
            ('error-correction', 10, 'Find and fix'),
            ('cloze', 16, 'Passage completion'),
            ('mark-the-words', 12, 'Click matching'),
            ('select', 8, 'Multi-select'),
            ('translate', 8, 'Translation choice'),
        ],
    }

    level_key = level.lower()
    if level_key in ('b2', 'c1', 'c2'):
        level_key = 'b1'  # Same activity types, higher counts

    return specs.get(level_key, specs['b1'])


def generate_skeleton(
    curriculum: str,
    level: str,
    module_num: int,
    output_path: Path = None
) -> str:
    """Generate skeleton content."""

    level = level.upper()
    module_type = determine_module_type(level, module_num)
    template_path = get_template_path(level, module_type)
    plan_path = get_curriculum_plan_path(curriculum, level)

    # Get module info from curriculum plan
    module_info = parse_curriculum_plan(plan_path, module_num)
    title = module_info.get('title', f'Module {module_num} Title')
    focus = module_info.get('focus', 'grammar')
    grammar = module_info.get('grammar', '')
    vocab_notes = module_info.get('vocab_notes', '')

    # Get targets
    word_targets = get_word_targets(level, module_type)
    activity_specs = get_activity_specs(level, module_type)

    # Determine phase
    if level == 'A1':
        if module_num <= 10:
            phase = 'A1.1'
        elif module_num <= 20:
            phase = 'A1.2'
        else:
            phase = 'A1.3'
    elif level == 'A2':
        if module_num <= 15:
            phase = 'A2.1'
        elif module_num <= 35:
            phase = 'A2.2'
        else:
            phase = 'A2.3'
    elif level == 'B1':
        if module_num <= 5:
            phase = 'B1.0'
        elif module_num <= 51:
            phase = 'B1.1-2'
        elif module_num <= 71:
            phase = 'B1.3'
        else:
            phase = 'B1.4'
    else:
        phase = f'{level}.1'

    # Determine pedagogy
    pedagogy = 'PPP' if level in ('A1', 'A2') else 'TTT'
    if 'checkpoint' in module_type:
        pedagogy = 'TTT'

    # Generate slug
    slug = slugify(title)

    # Build skeleton
    skeleton = f'''---
module: {level.lower()}-{module_num:02d}
title: "{title}"
subtitle: "<!-- Add subtitle -->"
version: "1.0"
phase: "{phase}"
pedagogy: "{pedagogy}"
duration: "60 min"
focus: "{focus}"
tags:
  - {focus}
  - <!-- add more tags -->
grammar:
  - {grammar if grammar else '<!-- grammar points -->'}
objectives:
  - "Learner can <!-- objective 1 -->"
  - "Learner can <!-- objective 2 -->"
  - "Learner can <!-- objective 3 -->"
vocabulary_count: <!-- N -->
---

# {title if level in ('A1', 'A2') else '<!-- Ukrainian Title -->'}

<!-- Word target: {word_targets['total']} words total -->

'''

    # Add section structure based on pedagogy
    if pedagogy == 'PPP':
        skeleton += f'''## Warm-up

<!-- {word_targets.get('presentation', 100)} words -->
<!-- Engaging intro, hook the learner -->

## Presentation

<!-- {word_targets.get('presentation', 500)} words -->

### <!-- Subsection 1 -->

<!-- Introduce concept with table and examples -->

> 💡 **Did You Know?**
>
> <!-- Interesting fact -->

### <!-- Subsection 2 -->

<!-- Continue with next concept -->

## Practice

<!-- {word_targets.get('practice', 200)} words -->
<!-- Guided exercises -->

## Summary

<!-- {word_targets.get('summary', 100)} words -->
<!-- Brief recap -->

'''
    elif pedagogy == 'seminar' or 'hist' in module_type: # History/Seminar
        skeleton += f'''## Вступ

<!-- {word_targets.get('presentation', 300)} words -->
<!-- Hook, Context, Why this matters -->

## Читання

<!-- {word_targets.get('content', 1000)} words -->
<!-- Main historical narrative -->

### <!-- Subsection 1 -->

### <!-- Subsection 2 -->

## Первинні джерела

<!-- {word_targets.get('practice', 300)} words -->
<!-- Primary source excerpts -->

## Деколонізаційний погляд

<!-- {word_targets.get('content', 500)} words -->
<!-- Critical analysis and myth-busting -->

## Підсумок

<!-- {word_targets.get('summary', 150)} words -->
<!-- Summary in Ukrainian -->

## Потрібно більше практики?

<!-- 100 words -->
<!-- Next steps and resources -->

'''
    else:  # TTT
        skeleton += f'''## Тест

<!-- {word_targets.get('test', 150)} words -->
<!-- Diagnostic pre-test in Ukrainian -->

## Пояснення

<!-- {word_targets.get('explanation', 900)} words -->

### <!-- Підрозділ 1 -->

<!-- Grammar explanation with examples -->

> 💡 **Чому це важливо?**
>
> <!-- Cultural/practical significance -->

### <!-- Підрозділ 2 -->

<!-- Continue explanation -->

## Практика

<!-- {word_targets.get('practice', 250)} words -->
<!-- Guided exercises -->

## Діалоги

<!-- 2-4 mini-dialogues demonstrating the grammar point -->

**А:** <!-- Speaker A -->
**Б:** <!-- Speaker B -->

## Підсумок

<!-- {word_targets.get('summary', 150)} words -->
<!-- Summary in Ukrainian -->

'''

    # Add activities section
    skeleton += '''## Activities

'''
    for act_type, min_items, description in activity_specs:
        skeleton += f'''## {act_type}: <!-- Title -->
<!-- {description} -->
<!-- Minimum {min_items} items -->

'''

    # Add vocabulary section
    if level in ('A1', 'A2'):
        skeleton += '''## Vocabulary

| Word | IPA | English | POS | Gender | Note |
|------|-----|---------|-----|--------|------|
| <!-- слово --> | /.../ | <!-- translation --> | noun/verb/adj | m/f/n | — |

'''
    else:
        skeleton += '''## Словник

| Слово | Вимова | Переклад | ЧМ | Примітка |
|-------|--------|----------|-----|----------|
| <!-- слово --> | /.../ | <!-- translation --> | ім/дієсл | <!-- note --> |

'''

    # Add vocab notes if available
    if vocab_notes:
        skeleton += f'''<!-- Vocabulary from curriculum plan: {vocab_notes} -->

'''

    # Add metadata footer
    skeleton += f'''---
<!-- Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")} -->
<!-- Template: {template_path.name if template_path.exists() else "default"} -->
<!-- Module type: {module_type} -->
'''

    return skeleton


def main():
    if len(sys.argv) < 4:
        print("Usage: python3 scripts/generate_skeleton.py <curriculum> <level> <module_num>")
        print("Example: python3 scripts/generate_skeleton.py l2-uk-en b1 43")
        sys.exit(1)

    curriculum = sys.argv[1]
    level = sys.argv[2].upper()
    module_num = int(sys.argv[3])

    # Generate skeleton
    skeleton = generate_skeleton(curriculum, level, module_num)

    # Determine output path
    module_type = determine_module_type(level, module_num)
    slug = 'skeleton'  # Will be renamed by LLM after filling

    output_dir = Path(f'curriculum/{curriculum}/{level.lower()}')
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / f'{module_num:02d}-{slug}.md'

    # Write skeleton
    output_path.write_text(skeleton, encoding='utf-8')

    print(f"Generated: {output_path}")
    print(f"Module type: {module_type}")
    print(f"Next step: Fill in content, then run check_gate.py content {output_path}")


if __name__ == '__main__':
    main()
