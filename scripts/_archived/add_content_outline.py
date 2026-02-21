#!/usr/bin/env python3
"""
Add content_outline to B2 and C1 meta files that are missing it.

Usage:
    .venv/bin/python scripts/add_content_outline.py b2 21
    .venv/bin/python scripts/add_content_outline.py b2 21-40
    .venv/bin/python scripts/add_content_outline.py c1 36-106
    .venv/bin/python scripts/add_content_outline.py b2 --list-missing
"""

import argparse
import re
import sys
from pathlib import Path
from typing import Optional

import yaml

# Custom YAML representer to preserve formatting
def str_representer(dumper, data):
    if '\n' in data:
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
    return dumper.represent_scalar('tag:yaml.org,2002:str', data)

yaml.add_representer(str, str_representer)

BASE_PATH = Path(__file__).parent.parent / "curriculum" / "l2-uk-en"


def has_content_outline(meta_path: Path) -> bool:
    """Check if a meta file already has content_outline."""
    with open(meta_path) as f:
        content = f.read()
    return 'content_outline:' in content


def list_missing_modules(level: str) -> list[str]:
    """List modules missing content_outline."""
    meta_dir = BASE_PATH / level / "meta"
    if not meta_dir.exists():
        print(f"Error: {meta_dir} does not exist")
        return []

    missing = []
    for meta_file in sorted(meta_dir.glob("*.yaml")):
        if not has_content_outline(meta_file):
            # Extract module number
            match = re.match(r'^(\d+)-', meta_file.name)
            if match:
                missing.append(match.group(1))

    return missing


def parse_curriculum_plan(level: str) -> dict:
    """Parse curriculum plan to extract module information."""
    plan_path = BASE_PATH.parent.parent / "docs" / "l2-uk-en" / f"{level.upper()}-CURRICULUM-PLAN.md"

    if not plan_path.exists():
        print(f"Error: Curriculum plan not found at {plan_path}")
        return {}

    with open(plan_path) as f:
        content = f.read()

    modules = {}

    # Parse module sections (#### Module XX: Title)
    module_pattern = r'####\s+Module\s+(\d+):\s+([^\n]+)\n(.*?)(?=####\s+Module|\Z)'

    for match in re.finditer(module_pattern, content, re.DOTALL):
        num = match.group(1)
        title = match.group(2).strip()
        body = match.group(3).strip()

        modules[num] = {
            'title': title,
            'body': body
        }

    return modules


def extract_module_info(module_data: dict) -> dict:
    """Extract structured info from module curriculum plan data."""
    body = module_data['body']
    title = module_data['title']

    info = {
        'title': title,
        'grammar': None,
        'sections': [],
        'activities': []
    }

    # Extract grammar topic
    grammar_match = re.search(r'\*\*Grammar:\*\*\s*([^\n]+)', body)
    if grammar_match:
        info['grammar'] = grammar_match.group(1).strip()

    # Extract main content sections (bolded headers)
    section_pattern = r'\*\*([^*]+):\*\*\n(.*?)(?=\*\*[^*]+:\*\*|\n\n---|\Z)'

    for match in re.finditer(section_pattern, body, re.DOTALL):
        section_name = match.group(1).strip()
        section_content = match.group(2).strip()

        # Skip "Content Guidance" and "Signature Activity Concepts" as separate sections
        if section_name in ['Content Guidance', 'Signature Activity Concepts', 'Key themes/places']:
            if section_name == 'Signature Activity Concepts':
                # Extract activities
                activity_lines = [line.strip() for line in section_content.split('\n') if line.strip().startswith(('1.', '2.', '3.', '4.'))]
                info['activities'] = activity_lines
            continue

        # Extract list items
        items = []
        for line in section_content.split('\n'):
            line = line.strip()
            if line.startswith('- '):
                items.append(line[2:])

        if items:
            info['sections'].append({
                'name': section_name,
                'items': items
            })

    return info


# Ukrainian section name translations
SECTION_TRANSLATIONS = {
    'Technical Contexts': 'Контексти науково-технічного стилю',
    'Key Features': 'Ключові особливості стилю',
    'Literary Features': 'Особливості літературного стилю',
    'Literary Vocabulary': 'Літературна лексика',
    'Stylistic Devices': 'Стилістичні засоби',
    'Media Contexts': 'Контексти медійного стилю',
    'Headline Style': 'Стиль заголовків',
    'Colloquial Features': 'Особливості розмовного стилю',
    'Emotional Particles': 'Емоційні частки',
    'Practice Tasks': 'Практичні завдання',
    'Skills Integration': 'Інтеграція навичок',
    'Political Terms': 'Політична лексика',
    'Political Processes': 'Політичні процеси',
    'Legal Terms': 'Юридична лексика',
    'Legal Processes': 'Юридичні процеси',
    'Economic Terms': 'Економічна лексика',
    'Business Terms': 'Бізнес-лексика',
    'Time Expressions': 'Вирази часу',
    'Date Expressions': 'Вирази дати',
    'Months in Cases': 'Місяці у відмінках',
    'Compound Ordinals': 'Складені порядкові числівники',
    'Compound Cardinals with Cases': 'Складені кількісні числівники',
    'Statistics and Prices': 'Статистика та ціни',
    'Religious Style': 'Релігійний стиль',
    'Epistolary Style': 'Епістолярний стиль',
    'Modern Email Conventions': 'Сучасні правила листування',
    'Indefinite Pronouns': 'Неозначені займенники',
    'Negative Pronouns': 'Заперечні займенники',
    'Defining Pronouns': 'Означальні займенники',
    'Key Usage Patterns': 'Основні моделі вживання',
    'Metaphor Types': 'Типи метафор',
    'Simile Markers': 'Маркери порівняння',
    'Irony Types': 'Типи іронії',
    'Hyperbole Examples': 'Приклади гіпербол',
    'Litotes Examples': 'Приклади літот',
    'Euphemism Categories': 'Категорії евфемізмів',
    'Taboo Topics': 'Табуйовані теми',
    'Rhetorical Question Types': 'Типи риторичних запитань',
    'Certainty Markers': 'Маркери впевненості',
    'Politeness Levels': 'Рівні ввічливості',
    'Formal Register Markers': 'Маркери офіційного регістру',
    'Intimate Register Features': 'Особливості інтимного регістру',
    'Slang Categories': 'Категорії сленгу',
    'Youth Language Features': 'Особливості молодіжної мови',
    'Assessment Areas': 'Сфери оцінювання',
    'Euphonic Patterns': 'Закономірності милозвучності',
    'Advanced Euphony': 'Поглиблена милозвучність',
    'Academic Writing': 'Академічне письмо',
    'Research Principles': 'Принципи наукового дослідження',
    'Legal Language': 'Юридична мова',
    'Official Conventions': 'Офіційно-ділові конвенції',
    'Publicist features': 'Особливості публіцистичного стилю',
    'Media influence': 'Вплив медіа',
    'Artistic Devices': 'Художні засоби',
    'Narrative techniques': 'Техніки оповіді',
    'Archaic vocabulary': 'Архаїчна лексика',
    'Liturgical language': 'Літургійна мова',
    'Epistolary conventions': 'Епістолярні конвенції',
    'Digital communication': 'Цифрова комунікація',
    'Transformation rules': 'Правила трансформації',
    'Register shifts': 'Зміни регістрів',
    'Lexical precision': 'Лексична точність',
    'Syntactic variety': 'Синтаксична різноманітність',
    'Voice development': 'Розвиток індивідуального голосу',
    'Writing style': 'Стиль письма',
    'Text flow': 'Плинність тексту',
    'Coherence markers': 'Маркери зв\'язності',
    'Metaphor and trope mastery': 'Майстерність метафор та тропів',
    'Rhythmic prose': 'Ритмічна проза',
    'Poetic rhythm': 'Поетичний ритм',
    'Intertextual links': 'Інтертекстуальні зв\'язки',
    'Cultural allusions': 'Культурні алюзії',
}

# Item-level translations for common English terms
ITEM_TRANSLATIONS = {
    'Technical documentation': 'Технічна документація',
    'Scientific reports': 'Наукові звіти',
    'User manuals': 'Інструкції користувача',
    'Engineering specifications': 'Інженерні специфікації',
    'Precise terminology': 'Точна термінологія',
    'Abbreviations and acronyms': 'Абревіатури та акроніми',
    'Passive constructions': 'Пасивні конструкції',
    'Numbered procedures': 'Нумеровані процедури',
    'Figurative language (metaphor, simile)': 'Образна мова (метафора, порівняння)',
    'Archaic and elevated vocabulary': 'Архаїчна та піднесена лексика',
    'Inverted word order': 'Інверсія',
    'Dialogue conventions': 'Правила діалогу',
    'News headlines': 'Заголовки новин',
    'News reports': 'Новинні репортажі',
    'Editorials': 'Редакційні статті',
    'Interviews': 'Інтерв\'ю',
}


def translate_section_name(name: str) -> str:
    """Translate English section name to Ukrainian."""
    return SECTION_TRANSLATIONS.get(name, name)


def translate_item(item: str) -> str:
    """Translate English item to Ukrainian if known."""
    return ITEM_TRANSLATIONS.get(item, item)


def generate_content_outline(module_info: dict, module_num: str) -> list:
    """Generate content_outline from module info."""
    outline = []

    title = module_info['title']
    grammar = module_info.get('grammar', '')
    sections = module_info.get('sections', [])
    activities = module_info.get('activities', [])

    # Calculate word distribution (target ~2000 words for B2)
    total_words = 2000
    num_sections = len(sections) + 2  # +2 for intro and practice
    words_per_section = total_words // max(num_sections, 4)

    # Extract short title for intro section
    # If title contains colon, take text after colon
    # If title contains " — ", take text after it
    if ':' in title:
        short_title = title.split(':')[-1].strip()
    elif ' — ' in title:
        short_title = title.split(' — ')[-1].strip()
    elif ' - ' in title:
        short_title = title.split(' - ')[-1].strip()
    else:
        short_title = title

    # Cap title length for section header
    if len(short_title) > 50:
        short_title = short_title[:47] + '...'

    # Introduction section
    intro_points = [
        "Визначення та сфери застосування",
        "Зв'язок із попередніми модулями",
    ]
    if grammar:
        intro_points.append("Роль у системі української мови")

    outline.append({
        'section': f"Вступ — {short_title}",
        'words': min(400, words_per_section),
        'points': intro_points
    })

    # Content sections from curriculum plan
    for section in sections[:4]:  # Limit to 4 main sections
        section_name = translate_section_name(section['name'])
        items = [translate_item(item) for item in section['items'][:5]]  # Limit to 5 items

        outline.append({
            'section': section_name,
            'words': words_per_section,
            'points': items if items else [f"Ключові поняття"]
        })

    # If no sections from plan, generate generic ones
    if not sections:
        outline.append({
            'section': 'Основний матеріал',
            'words': 600,
            'points': [
                "Теоретичні основи",
                "Приклади та ілюстрації",
                "Типові помилки та як їх уникати"
            ]
        })
        outline.append({
            'section': 'Поглиблене вивчення',
            'words': 600,
            'points': [
                "Додаткові випадки",
                "Контекстуальне використання",
                "Стилістичні нюанси"
            ]
        })

    # Practice/summary section
    practice_points = [
        "Практичні вправи на закріплення",
        "Інтеграція з попередніми модулями",
        "Підготовка до наступного модуля"
    ]

    outline.append({
        'section': 'Практика та підсумок',
        'words': 300,
        'points': practice_points
    })

    return outline


def get_ukr_title_from_meta(meta_path: Path) -> Optional[str]:
    """Get Ukrainian title from meta file."""
    try:
        with open(meta_path) as f:
            meta = yaml.safe_load(f)
        return meta.get('title')
    except:
        return None


def update_meta_file(meta_path: Path, content_outline: list, word_target: int = 2000) -> bool:
    """Add content_outline to a meta file."""
    with open(meta_path) as f:
        content = f.read()

    # Check if already has content_outline
    if 'content_outline:' in content:
        print(f"  Skipping {meta_path.name} - already has content_outline")
        return False

    # Parse existing YAML
    try:
        meta = yaml.safe_load(content)
    except yaml.YAMLError as e:
        print(f"  Error parsing {meta_path.name}: {e}")
        return False

    if meta is None:
        meta = {}

    # Add content_outline and word_target
    meta['content_outline'] = content_outline
    if 'word_target' not in meta:
        meta['word_target'] = word_target

    # Write back
    with open(meta_path, 'w') as f:
        yaml.dump(meta, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

    print(f"  Updated {meta_path.name}")
    return True


def process_module(level: str, num: str, curriculum_data: dict) -> bool:
    """Process a single module."""
    # Find meta file
    meta_dir = BASE_PATH / level / "meta"
    
    # Try different naming patterns
    patterns = [
        f"{num.zfill(2)}-*.yaml",
        f"{num}-*.yaml"
    ]
    
    meta_files = []
    for pattern in patterns:
        meta_files.extend(list(meta_dir.glob(pattern)))

    # Special mapping for C2 if not found by number
    if not meta_files and level == 'c2':
        c2_mapping = {
            '1': 'c1-bridge-assessment.yaml',
            '2': 'milozvuchnist-complete.yaml',
            '3': 'naukovyi-styl-mastery.yaml',
            '4': 'ofitsiynyi-styl-mastery.yaml',
            '5': 'publitsystychnyi-styl.yaml',
            '6': 'khudozhniy-styl.yaml',
            '7': 'rozmovnyi-styl.yaml',
            '8': 'relihiynyi-styl.yaml',
            '9': 'epistolyarnyi-styl.yaml',
            '10': 'style-transformation-i.yaml',
            '11': 'style-transformation-ii.yaml',
            '12': 'lexical-stylistics.yaml',
            '13': 'syntactic-stylistics.yaml',
            '14': 'individual-voice-i.yaml',
            '15': 'individual-voice-ii.yaml',
            '16': 'text-coherence.yaml',
            '17': 'c2-1-practice-i.yaml',
            '18': 'c2-1-practice-ii.yaml',
            '19': 'c2-1-review.yaml',
            '20': 'c2-1-checkpoint.yaml',
            '21': 'stylistic-devices-mastery.yaml',
        }
        if num in c2_mapping:
            path = meta_dir / c2_mapping[num]
            if path.exists():
                meta_files = [path]

    if not meta_files:
        print(f"  Warning: No meta file found for module {num}")
        return False

    meta_path = meta_files[0]

    # Check if already has content_outline
    if has_content_outline(meta_path):
        print(f"  Skipping module {num} - already has content_outline")
        return False

    # Get Ukrainian title from meta file
    ukr_title = get_ukr_title_from_meta(meta_path)

    # Get module info from curriculum plan
    if num not in curriculum_data:
        print(f"  Warning: Module {num} not found in curriculum plan")
        # Generate minimal content_outline
        module_info = {
            'title': ukr_title or f"Module {num}",
            'grammar': None,
            'sections': [],
            'activities': []
        }
    else:
        module_info = extract_module_info(curriculum_data[num])
        # Override with Ukrainian title from meta
        if ukr_title:
            module_info['title'] = ukr_title

    # Generate content_outline
    content_outline = generate_content_outline(module_info, num)

    # Update meta file
    return update_meta_file(meta_path, content_outline)


def main():
    parser = argparse.ArgumentParser(description='Add content_outline to meta files')
    parser.add_argument('level', choices=['b2', 'c1', 'c2'], help='Level to process')
    parser.add_argument('modules', nargs='?', help='Module number(s) to process (e.g., 21, 21-40)')
    parser.add_argument('--list-missing', action='store_true', help='List modules missing content_outline')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without making changes')

    args = parser.parse_args()

    if args.list_missing:
        missing = list_missing_modules(args.level)
        if missing:
            print(f"Modules missing content_outline in {args.level.upper()}: {', '.join(missing)}")
            print(f"Total: {len(missing)} modules")
        else:
            print(f"All modules in {args.level.upper()} have content_outline")
        return

    if not args.modules:
        print("Error: Please specify module number(s) or use --list-missing")
        sys.exit(1)

    # Parse module range
    if '-' in args.modules:
        start, end = args.modules.split('-')
        module_nums = [str(i) for i in range(int(start), int(end) + 1)]
    else:
        module_nums = [args.modules]

    # Parse curriculum plan
    print(f"Parsing {args.level.upper()} curriculum plan...")
    curriculum_data = parse_curriculum_plan(args.level)
    print(f"Found {len(curriculum_data)} modules in curriculum plan")

    # Process modules
    updated = 0
    for num in module_nums:
        print(f"Processing module {num}...")
        if process_module(args.level, num, curriculum_data):
            updated += 1

    print(f"\nDone. Updated {updated} of {len(module_nums)} modules.")


if __name__ == '__main__':
    main()
