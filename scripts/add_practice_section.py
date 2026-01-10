#!/usr/bin/env python3
"""
Add "Потрібно більше практики?" section to B1/B2 modules that are missing it.

This script:
1. Scans all B1/B2 modules
2. Checks if they have the "Потрібно більше практики?" section
3. If missing, adds it before any existing external resources section
4. Generates appropriate content based on module metadata
"""

import re
import sys
from pathlib import Path
from typing import Optional

def has_practice_section_with_content(content: str) -> bool:
    """Check if module has practice section WITH CONTENT (not just empty header)."""
    patterns = [
        r'^##\s+Потрібно більше практики\?',
        r'^##\s+Need More Practice\?',
    ]

    for pattern in patterns:
        match = re.search(pattern, content, re.MULTILINE)
        if match:
            # Extract content after the header until next ## section or end of file
            start_pos = match.end()
            next_section = re.search(r'^##\s+', content[start_pos:], re.MULTILINE)

            if next_section:
                section_content = content[start_pos:start_pos + next_section.start()]
            else:
                section_content = content[start_pos:]

            # If section has more than just whitespace, it has content
            if section_content.strip():
                return True

    return False

def extract_module_info(content: str, filepath: Path) -> dict:
    """Extract module metadata from frontmatter."""
    info = {
        'module': filepath.stem,
        'level': filepath.parent.name,
        'type': 'standard',
        'phase': ''
    }

    # Extract from YAML frontmatter
    yaml_match = re.search(r'^---\s*$(.*?)^---\s*$', content, re.MULTILINE | re.DOTALL)
    if yaml_match:
        yaml_content = yaml_match.group(1)

        # Extract phase
        phase_match = re.search(r'^phase:\s*["\']?([^"\'\n]+)["\']?', yaml_content, re.MULTILINE)
        if phase_match:
            info['phase'] = phase_match.group(1)

        # Determine module type from phase or tags
        if 'Grammar' in info['phase'] or 'Граматика' in info['phase']:
            info['type'] = 'grammar'
        elif 'Vocab' in info['phase'] or 'Лексика' in info['phase']:
            info['type'] = 'vocabulary'
        elif 'Cultural' in info['phase'] or 'Культура' in info['phase']:
            info['type'] = 'cultural'
        elif 'History' in info['phase'] or 'Історія' in info['phase']:
            info['type'] = 'history'
        elif 'Integration' in info['phase'] or 'Інтеграція' in info['phase']:
            info['type'] = 'integration'
        elif 'Checkpoint' in info['phase']:
            info['type'] = 'checkpoint'

    return info

def generate_practice_content(info: dict) -> str:
    """Generate appropriate practice section content based on module type."""

    level = info['level'].upper()
    module_type = info['type']

    # Base content for all modules
    content = f"""## Потрібно більше практики?

Ви завершили цей модуль! Ось кілька способів закріпити матеріал:

"""

    # Type-specific suggestions
    if module_type == 'grammar':
        content += """### 📝 Додаткові вправи

- Перегляньте всі приклади з модуля і створіть власні речення за аналогією
- Виконайте вправи ще раз через кілька днів для закріплення
- Спробуйте пояснити граматичне правило своїми словами

### 🎯 Практика в контексті

- Знайдіть приклади цієї граматичної структури в українських текстах (новини, блоги, книги)
- Послухайте українські подкасти і зверніть увагу на використання цієї граматики
- Спробуйте використати нову граматику в розмові з носіями мови

"""
    elif module_type == 'vocabulary':
        content += """### 📚 Розширення словника

- Створіть флеш-картки з новими словами (Anki, Quizlet)
- Складіть власні речення з кожним новим словом
- Знайдіть синоніми та антоніми до вивчених слів

### 🗣️ Активне використання

- Використовуйте нові слова в щоденнику українською мовою
- Опишіть свій день, використовуючи лексику з цього модуля
- Знайдіть відео на YouTube з цієї теми і послухайте носіїв мови

"""
    elif module_type == 'cultural' or module_type == 'history':
        content += """### 🌍 Поглиблення знань

- Знайдіть додаткові матеріали про цю тему українською мовою
- Подивіться документальні фільми або відео про цю тему
- Прочитайте статті в українській Вікіпедії

### 💬 Обговорення

- Обговоріть тему з іншими учнями або носіями мови
- Напишіть коротке есе (150-200 слів) про те, що ви дізналися
- Поділіться своїми думками в українськомовних спільнотах онлайн

"""
    elif module_type == 'checkpoint':
        content += """### 🔄 Повторення

- Перегляньте модулі, які викликали найбільше труднощів
- Виконайте контрольні завдання ще раз через тиждень
- Визначте слабкі місця і приділіть їм додатковий час

### 📊 Оцінка прогресу

- Порівняйте свої результати зараз і на початку фази
- Відзначте, які теми ви засвоїли найкраще
- Складіть план роботи над складнішими темами

"""
    else:  # integration or standard
        content += """### 🔄 Інтеграція знань

- Поєднуйте матеріал цього модуля з попередніми темами
- Створіть mind map зв'язків між різними темами
- Практикуйте використання кількох тем одночасно

### 🎯 Реальне застосування

- Знайдіть ситуації в житті, де можна використати вивчене
- Читайте українські тексти і шукайте знайомі структури
- Спілкуйтеся з носіями мови, застосовуючи нові знання

"""

    # Common footer for all types
    content += f"""### 🌐 Онлайн-ресурси

Додаткові матеріали для практики {level}:

- **Українська мова онлайн:** [https://ukrainian-language.uk](https://ukrainian-language.uk)
- **Словник.ua:** [https://slovnyk.ua](https://slovnyk.ua) — для перевірки слів
- **YouTube канали:** Шукайте "українська мова {level}" для додаткових уроків
- **Мовні обміни:** italki, Tandem, HelloTalk для практики з носіями

---

> 💡 **Порада:** Найкращий спосіб закріпити матеріал — використовувати його регулярно. Виділіть 10-15 хвилин щодня для повторення!
"""

    return content

def add_practice_section(filepath: Path, dry_run: bool = False) -> bool:
    """Add practice section to module if missing or empty."""

    content = filepath.read_text(encoding='utf-8')

    # Check if already has the section WITH CONTENT
    if has_practice_section_with_content(content):
        print(f"  ℹ️  {filepath.name}: Already has practice section with content")
        return False

    # Extract module info
    info = extract_module_info(content, filepath)

    # Generate new section content (includes header)
    practice_full = generate_practice_content(info)

    # Check if empty practice section header exists
    empty_header_patterns = [
        r'^##\s+Потрібно більше практики\?\s*$',
        r'^##\s+Need More Practice\?\s*$',
    ]

    for pattern in empty_header_patterns:
        match = re.search(pattern, content, re.MULTILINE)
        if match:
            # Empty header exists - insert content WITHOUT header (remove first line)
            practice_content_lines = practice_full.split('\n')
            practice_body = '\n'.join(practice_content_lines[1:])  # Skip first line (header)

            insert_pos = match.end()
            new_content = content[:insert_pos] + '\n' + practice_body + content[insert_pos:]

            if dry_run:
                print(f"  🔍 {filepath.name}: Would populate empty practice section")
            else:
                filepath.write_text(new_content, encoding='utf-8')
                print(f"  ✅ {filepath.name}: Populated empty practice section")

            return True

    # No empty header found - need to add full section (header + content)
    new_section = practice_full

    # Find insertion point (before external resources or at end)
    # Look for common end-of-content markers
    insertion_patterns = [
        (r'(^##\s+External Resources.*)', 'before_external'),
        (r'(^---\s*$(?!.*^##))', 'before_final_separator'),
        (r'(\Z)', 'at_end'),  # End of file
    ]

    for pattern, location in insertion_patterns:
        match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
        if match:
            if location == 'at_end':
                # Add before end of file
                new_content = content.rstrip() + '\n\n' + new_section + '\n'
            else:
                # Insert before match
                insert_pos = match.start(1)
                new_content = content[:insert_pos] + new_section + '\n' + content[insert_pos:]

            if dry_run:
                print(f"  🔍 {filepath.name}: Would add section ({location})")
            else:
                filepath.write_text(new_content, encoding='utf-8')
                print(f"  ✅ {filepath.name}: Added section ({location})")

            return True

    print(f"  ⚠️  {filepath.name}: Could not find insertion point")
    return False

def main():
    """Main execution."""

    if len(sys.argv) > 1 and sys.argv[1] == '--dry-run':
        dry_run = True
        print("🔍 DRY RUN MODE - No files will be modified\n")
    else:
        dry_run = False

    base_path = Path(__file__).parent.parent / 'curriculum' / 'l2-uk-en'

    for level in ['b1', 'b2']:
        level_path = base_path / level

        if not level_path.exists():
            print(f"⚠️  Level {level.upper()} not found")
            continue

        print(f"\n{'='*60}")
        print(f"Processing {level.upper()} modules")
        print('='*60)

        # Find all module files
        module_files = sorted(level_path.glob('[0-9]*-*.md'))

        total = len(module_files)
        modified = 0
        skipped = 0

        for module_file in module_files:
            if add_practice_section(module_file, dry_run):
                modified += 1
            else:
                skipped += 1

        print(f"\n📊 {level.upper()} Summary:")
        print(f"   Total modules: {total}")
        print(f"   Modified: {modified}")
        print(f"   Skipped (already has section): {skipped}")

    if dry_run:
        print("\n" + "="*60)
        print("🔍 Dry run complete. Run without --dry-run to apply changes.")
    else:
        print("\n" + "="*60)
        print("✅ All modules processed!")
        print("\nNext steps:")
        print("1. Run git diff to review changes")
        print("2. Re-audit modules: .venv/bin/python scripts/audit_module.py curriculum/l2-uk-en/b1/[NUM]-*.md")

if __name__ == '__main__':
    main()
