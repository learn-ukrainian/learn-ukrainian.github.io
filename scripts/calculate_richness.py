#!/usr/bin/env python3
"""
Calculate richness score for module content.

Richness measures how engaging and alive the content is beyond basic counts.
This is primarily for B1+ modules where full immersion enables rich content.

Usage:
    python3 scripts/calculate_richness.py <file>
    python3 scripts/calculate_richness.py <file> --json

Components (10 total, weighted):
- Engagement boxes (15%)
- Example sentences (20%)
- Mini-dialogues (15%)
- Variety score (10%)
- Cultural references (10%)
- Real-world contexts (10%)
- Question density (5%)
- Proverbs/idioms (5%)
- Visual elements (5%)
- Paragraph variety (5%)

Returns exit code 0 if richness >= threshold, 1 otherwise.
"""

import sys
import re
import json
import statistics
from pathlib import Path

# Richness targets by level
RICHNESS_TARGETS = {
    'A1': {
        'engagement': 3,
        'examples': 10,
        'dialogues': 1,
        'cultural': 1,
        'realworld': 2,
        'questions': 2,
        'proverbs': 0,
        'visual': 2,
        'threshold': 95,  # Universal 95+ threshold
    },
    'A2': {
        'engagement': 4,
        'examples': 15,
        'dialogues': 2,
        'cultural': 2,
        'realworld': 3,
        'questions': 3,
        'proverbs': 0,
        'visual': 3,
        'threshold': 95,
    },
    'B1': {
        'engagement': 5,
        'examples': 24,
        'dialogues': 4,
        'cultural': 3,
        'realworld': 3,
        'questions': 5,
        'proverbs': 1,
        'visual': 3,
        'threshold': 95,
    },
    'B2': {
        'engagement': 6,
        'examples': 24,
        'dialogues': 4,
        'cultural': 4,
        'realworld': 4,
        'questions': 6,
        'proverbs': 2,
        'visual': 4,
        'threshold': 95,
    },
    'C1': {
        'engagement': 7,
        'examples': 30,
        'dialogues': 5,
        'cultural': 5,
        'realworld': 5,
        'questions': 7,
        'proverbs': 2,
        'visual': 5,
        'threshold': 95,
    },
    'C2': {
        'engagement': 7,
        'examples': 30,
        'dialogues': 5,
        'cultural': 6,
        'realworld': 6,
        'questions': 8,
        'proverbs': 3,
        'visual': 5,
        'threshold': 95,
    },
}

# Weights for each component
WEIGHTS = {
    'engagement': 0.15,
    'examples': 0.20,
    'dialogues': 0.15,
    'variety': 0.10,
    'cultural': 0.10,
    'realworld': 0.10,
    'questions': 0.05,
    'proverbs': 0.05,
    'visual': 0.05,
    'paragraph_var': 0.05,
}

# Ukrainian place names for cultural reference detection
UKRAINIAN_PLACES = {
    'Київ', 'Львів', 'Одеса', 'Харків', 'Дніпро', 'Запоріжжя',
    'Карпати', 'Крим', 'Буковина', 'Закарпаття', 'Волинь', 'Поділля',
    'Полтава', 'Чернігів', 'Суми', 'Вінниця', 'Житомир', 'Рівне',
    'Тернопіль', 'Івано-Франківськ', 'Чернівці', 'Ужгород', 'Луцьк',
    'Хрещатик', 'Майдан', 'Софія', 'Лавра', 'Андріївський',
    'Бесарабський', 'Подол', 'Поштова', 'Говерла', 'Дністер',
}

# Cultural terms and traditions
CULTURAL_TERMS = {
    'вишиванка', 'писанка', 'борщ', 'вареники', 'галушки', 'сало',
    'козак', 'гетьман', 'кобзар', 'бандура', 'трембіта', 'гопак',
    'калина', 'верба', 'рушник', 'вінок', 'коровай', 'весілля',
    'Різдво', 'Великдень', 'Купала', 'Маланка', 'колядки', 'щедрівки',
    'Шевченко', 'Франко', 'Леся', 'Котляревський', 'Сковорода',
    'Мазепа', 'Хмельницький', 'Грушевський', 'Бандера',
}

# Proverb/idiom markers
PROVERB_MARKERS = [
    r'кажуть[:\s]',
    r'приказка',
    r'прислів\'я',
    r'ідіома',
    r'вислів',
    r'«[^»]{10,}»',  # Quoted phrases longer than 10 chars
    r'як кажуть',
    r'є вираз',
]


def extract_level(file_path: Path) -> str:
    """Extract level code from file path."""
    parts = file_path.parts
    for part in parts:
        if part.upper() in ('A1', 'A2', 'B1', 'B2', 'C1', 'C2', 'LIT'):
            return part.upper()
    return 'B1'  # Default


def get_prose_content(content: str) -> str:
    """Extract prose content (excluding activities and vocab)."""
    # Remove frontmatter
    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            content = parts[2]

    # Remove activities section
    for section in ['Activities', 'Вправи']:
        match = re.search(rf'^#\s*{section}\s*$', content, re.MULTILINE)
        if match:
            content = content[:match.start()]
            break

    # Remove vocabulary section
    for section in ['Vocabulary', 'Словник']:
        match = re.search(rf'^#\s*{section}\s*$', content, re.MULTILINE)
        if match:
            content = content[:match.start()]
            break

    return content


def count_engagement_boxes(content: str) -> int:
    """Count engagement boxes (💡🎬🌍🎯🎮 and callouts)."""
    patterns = [
        r'>\s*\[!tip\]',
        r'>\s*\[!note\]',
        r'>\s*\[!observe\]',
        r'>\s*\[!warning\]',
        r'💡\s*\*\*',
        r'🎬\s*\*\*',
        r'🌍\s*\*\*',
        r'🎯\s*\*\*',
        r'🎮\s*\*\*',
        r'🎭\s*\*\*',
        r'📝\s*\*\*',
        r'🔍\s*\*\*',
    ]
    count = 0
    for pattern in patterns:
        count += len(re.findall(pattern, content, re.MULTILINE))
    return count


def count_examples(content: str) -> int:
    """Count Ukrainian example sentences."""
    patterns = [
        r'\*\*[А-ЯІЇЄҐа-яіїєґ][^*]{5,}[.!?]\*\*',  # Bold Ukrainian sentences
        r'^\s*[-–—]\s*[А-ЯІЇЄҐа-яіїєґ][^.!?]{5,}[.!?]',  # Bulleted Ukrainian
        r'^\s*\d+\.\s*[А-ЯІЇЄҐа-яіїєґ][^.!?]{5,}[.!?]',  # Numbered Ukrainian
    ]
    count = 0
    for pattern in patterns:
        count += len(re.findall(pattern, content, re.MULTILINE))
    return min(count, 100)  # Cap to avoid overcounting


def count_dialogues(content: str) -> int:
    """Count mini-dialogues."""
    patterns = [
        r'^[АБВ]:\s',
        r'^\*\*[АБВ]:\*\*\s',
        r'^—\s*[А-ЯІЇЄҐа-яіїєґ]',  # Em-dash dialogue
        r'^\*\*[А-ЯІЇЄҐа-яіїєґ]+:\*\*\s',  # **Speaker:** format
        r'^[А-ЯІЇЄҐа-яіїєґ]+:\s+[А-ЯІЇЄҐа-яіїєґ]',  # Speaker: text format
    ]
    count = 0
    for pattern in patterns:
        count += len(re.findall(pattern, content, re.MULTILINE))
    return count // 2  # Pairs


def calculate_variety_score(content: str) -> float:
    """Calculate sentence starter variety (0.0-1.0)."""
    # Extract sentences
    sentences = re.findall(r'[А-ЯІЇЄҐа-яіїєґA-Za-z][^.!?]*[.!?]', content)
    if len(sentences) < 5:
        return 0.5  # Not enough data

    # Get first 3 words of each sentence
    starters = []
    for sent in sentences:
        words = sent.split()[:3]
        if words:
            starters.append(' '.join(words).lower())

    if not starters:
        return 0.5

    unique = len(set(starters))
    total = len(starters)
    return unique / total


def count_cultural_refs(content: str) -> int:
    """Count cultural references (places, traditions, people)."""
    count = 0

    # Check for place names
    for place in UKRAINIAN_PLACES:
        if place in content:
            count += 1

    # Check for cultural terms
    for term in CULTURAL_TERMS:
        if term.lower() in content.lower():
            count += 1

    return min(count, 20)  # Cap


def count_realworld(content: str) -> int:
    """Count real-world context markers."""
    patterns = [
        r'уявіть',
        r'наприклад',
        r'у реальному житті',
        r'на практиці',
        r'коли ви',
        r'якщо ви',
        r'у магазині',
        r'на роботі',
        r'у ресторані',
        r'на вулиці',
        r'в аеропорту',
        r'на вокзалі',
        r'у лікарні',
        r'в університеті',
        r'imagine',
        r'for example',
        r'in real life',
        r'when you',
        r'at the',
    ]
    count = 0
    for pattern in patterns:
        count += len(re.findall(pattern, content, re.IGNORECASE))
    return min(count, 20)


def count_questions(content: str) -> int:
    """Count interactive questions in prose."""
    # Questions ending with ?
    questions = re.findall(r'[А-ЯІЇЄҐа-яіїєґA-Za-z][^.!?]*\?', content)
    return len(questions)


def count_proverbs(content: str) -> int:
    """Count proverbs and idioms."""
    count = 0
    for pattern in PROVERB_MARKERS:
        count += len(re.findall(pattern, content, re.IGNORECASE))
    return min(count, 10)


def count_visual_elements(content: str) -> int:
    """Count visual elements (tables, callouts, boxes)."""
    patterns = [
        r'^\|[^|]+\|',  # Table rows
        r'>\s*\[!',  # Callout boxes
        r'```',  # Code blocks
    ]
    count = 0
    for pattern in patterns:
        matches = re.findall(pattern, content, re.MULTILINE)
        count += len(matches)
    # Tables count as 1 visual each (not per row)
    table_markers = len(re.findall(r'^\|[-:| ]+\|', content, re.MULTILINE))
    if table_markers > 0:
        count = count - len(re.findall(r'^\|[^|]+\|', content, re.MULTILINE)) + table_markers
    return count


def calculate_paragraph_variety(content: str) -> float:
    """Calculate paragraph length variety (0.0-1.0)."""
    # Split into paragraphs
    paragraphs = re.split(r'\n\s*\n', content)
    lengths = []
    for p in paragraphs:
        words = len(p.split())
        if words > 5:  # Ignore very short paragraphs
            lengths.append(words)

    if len(lengths) < 3:
        return 0.5  # Not enough data

    try:
        std_dev = statistics.stdev(lengths)
        # Normalize: 20+ std dev = perfect variety
        return min(std_dev / 20, 1.0)
    except statistics.StatisticsError:
        return 0.5


def calculate_richness_score(content: str, level: str) -> dict:
    """Calculate richness score and components."""
    targets = RICHNESS_TARGETS.get(level, RICHNESS_TARGETS['B1'])
    prose = get_prose_content(content)

    # Calculate each component
    raw = {
        'engagement': count_engagement_boxes(prose),
        'examples': count_examples(prose),
        'dialogues': count_dialogues(prose),
        'variety': calculate_variety_score(prose),
        'cultural': count_cultural_refs(prose),
        'realworld': count_realworld(prose),
        'questions': count_questions(prose),
        'proverbs': count_proverbs(prose),
        'visual': count_visual_elements(prose),
        'paragraph_var': calculate_paragraph_variety(prose),
    }

    # Calculate normalized scores (0.0-1.0)
    normalized = {}
    for key in raw:
        if key in ('variety', 'paragraph_var'):
            normalized[key] = raw[key]  # Already 0-1
        else:
            target = targets.get(key, 1)
            if target > 0:
                normalized[key] = min(raw[key] / target, 1.0)
            else:
                normalized[key] = 1.0 if raw[key] == 0 else 0.5

    # Calculate weighted total
    total = sum(normalized[k] * WEIGHTS[k] for k in WEIGHTS)
    score = int(total * 100)

    return {
        'score': score,
        'threshold': targets['threshold'],
        'passed': score >= targets['threshold'],
        'raw': raw,
        'normalized': {k: round(v, 2) for k, v in normalized.items()},
        'targets': {k: targets.get(k, 0) for k in raw if k not in ('variety', 'paragraph_var')},
    }


def detect_dryness_flags(content: str, level: str) -> list:
    """Detect dryness indicators."""
    flags = []
    prose = get_prose_content(content)

    # NO_ENGAGEMENT: Less than 2 engagement boxes
    if count_engagement_boxes(prose) < 2:
        flags.append('NO_ENGAGEMENT')

    # WALL_OF_TEXT: Paragraph > 500 words without break
    paragraphs = re.split(r'\n\s*\n', prose)
    for p in paragraphs:
        if len(p.split()) > 500:
            flags.append('WALL_OF_TEXT')
            break

    # REPETITIVE_STARTERS: Variety < 0.4
    if calculate_variety_score(prose) < 0.4:
        flags.append('REPETITIVE_STARTERS')

    # NO_DIALOGUE: No dialogues (B1+ only)
    if level in ('B1', 'B2', 'C1', 'C2') and count_dialogues(prose) == 0:
        flags.append('NO_DIALOGUE')

    # NO_EXAMPLES: Less than 10 examples
    if count_examples(prose) < 10:
        flags.append('NO_EXAMPLES')

    # ABSTRACT_ONLY: No real-world references
    if count_realworld(prose) == 0:
        flags.append('ABSTRACT_ONLY')

    # NO_CULTURAL_ANCHOR: No cultural references (B1+ only)
    if level in ('B1', 'B2', 'C1', 'C2') and count_cultural_refs(prose) == 0:
        flags.append('NO_CULTURAL_ANCHOR')

    return flags


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/calculate_richness.py <file> [--json]")
        sys.exit(1)

    file_path = Path(sys.argv[1])
    output_json = '--json' in sys.argv

    if not file_path.exists():
        print(f"Error: File not found: {file_path}")
        sys.exit(1)

    content = file_path.read_text(encoding='utf-8')
    level = extract_level(file_path)

    result = calculate_richness_score(content, level)
    flags = detect_dryness_flags(content, level)

    if output_json:
        result['flags'] = flags
        print(json.dumps(result, indent=2))
    else:
        print(f"Richness Score: {result['score']}/100 (threshold: {result['threshold']})")
        print(f"Status: {'✅ PASS' if result['passed'] else '❌ FAIL'}")
        print()
        print("Components:")
        for key in WEIGHTS:
            raw = result['raw'].get(key, 0)
            norm = result['normalized'].get(key, 0)
            target = result['targets'].get(key, '—')
            weight = int(WEIGHTS[key] * 100)
            if key in ('variety', 'paragraph_var'):
                print(f"  {key}: {norm:.0%} ({weight}% weight)")
            else:
                print(f"  {key}: {raw}/{target} = {norm:.0%} ({weight}% weight)")
        print()
        if flags:
            print("Dryness Flags:")
            for flag in flags:
                print(f"  ⚠️ {flag}")
            if len(flags) >= 2:
                print()
                print("❌ 2+ flags: Content needs REWRITE, not just fix")
        else:
            print("Dryness Flags: None")

    sys.exit(0 if result['passed'] else 1)


if __name__ == '__main__':
    main()
