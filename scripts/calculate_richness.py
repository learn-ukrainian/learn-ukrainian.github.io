#!/usr/bin/env python3
"""
Calculate richness score for module content.

Richness measures how engaging and alive the content is beyond basic counts.
This is primarily for B1+ modules where full immersion enables rich content.

Usage:
    python3 scripts/calculate_richness.py <file>
    python3 scripts/calculate_richness.py <file> --json

IMPORTANT: Richness criteria vary by MODULE TYPE, not just level.
- Grammar modules: examples, dialogues, proverbs
- History modules: primary sources, decolonization, narrative
- Biography modules: quotes, legacy, timeline
- Style modules: exemplar texts, model answers, transformation
- LIT modules: philological analysis, essays, resources

Returns exit code 0 if richness >= threshold, 1 otherwise.
"""

import sys
import re
import json
import statistics
import yaml
from pathlib import Path
from typing import Union

# Module type detection from pedagogy field
MODULE_TYPE_MAP = {
    # Grammar types
    'ttt': 'grammar',
    'ppp': 'grammar',
    'grammar': 'grammar',
    # Vocabulary types
    'vocabulary': 'vocabulary',
    'vocab': 'vocabulary',
    'lexical': 'vocabulary',
    # Cultural types
    'cultural': 'cultural',
    'cbi': 'content',  # Can be history, biography, or cultural
    # History types
    'history': 'history',
    'historical': 'history',
    # Phraseology types
    'phraseology': 'phraseology',
    'idioms': 'phraseology',
    # Biography types
    'biography': 'biography',
    'biographical': 'biography',
    # Academic types
    'academic': 'academic',
    'sociolinguistics': 'academic',
    # Style types
    'style': 'style',
    'stylistics': 'style',
    'creative production': 'style',
    # Professional types
    'professional': 'professional',
    'specialized': 'professional',
    # Literature types
    'literature': 'literature',
    'literary': 'literature',
    'lit': 'literature',
    # Checkpoint types
    'checkpoint': 'checkpoint',
    'review': 'checkpoint',
    'assessment': 'checkpoint',
}

# Richness targets by MODULE TYPE (not just level)
MODULE_TYPE_TARGETS = {
    'grammar': {
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
    'vocabulary': {
        'engagement': 4,
        'collocations': 20,
        'usage_examples': 15,
        'register_notes': 5,
        'cultural': 3,
        'visual': 3,
        'threshold': 95,
    },
    'cultural': {
        'engagement': 6,
        'authentic_refs': 3,
        'regional_refs': 5,
        'contemporary': 3,
        'cultural': 5,
        'visual': 4,
        'questions': 4,
        'threshold': 95,
    },
    'history': {
        'engagement': 6,
        'primary_sources': 3,
        'timeline_markers': 10,
        'decolonization': 2,
        'cultural': 4,
        'visual': 4,
        'questions': 3,
        'threshold': 95,
    },
    'phraseology': {
        'engagement': 4,
        'idiom_contexts': 15,
        'etymology': 5,
        'register_notes': 5,
        'contrastive': 5,
        'visual': 3,
        'threshold': 95,
    },
    'biography': {
        'engagement': 6,
        'primary_sources': 4,
        'quotes': 3,
        'timeline_markers': 8,
        'legacy': 2,
        'cultural': 4,
        'visual': 4,
        'questions': 3,
        'threshold': 95,
    },
    'academic': {
        'engagement': 5,
        'citations': 5,
        'data_refs': 3,
        'frameworks': 2,
        'case_studies': 2,
        'visual': 5,
        'questions': 4,
        'threshold': 95,
    },
    'style': {
        'engagement': 5,
        'exemplar_texts': 2,
        'model_answers': 3,
        'register_analysis': 5,
        'transformations': 2,
        'visual': 4,
        'threshold': 95,
    },
    'professional': {
        'engagement': 4,
        'domain_terms': 20,
        'document_examples': 3,
        'register_notes': 3,
        'scenarios': 3,
        'visual': 3,
        'threshold': 95,
    },
    'literature': {
        'engagement': 4,
        'analysis_sections': 5,
        'literary_citations': 5,
        'historical_context': 3,
        'essays': 2,
        'resources': 3,
        'visual': 1,
        'threshold': 90,
    },
    'checkpoint': {
        'engagement': 3,
        'activity_types': 8,
        'review_sections': 3,
        'visual': 3,
        'threshold': 85,  # Checkpoints focus on variety, lower threshold
    },
    'content': {  # Generic CBI fallback
        'engagement': 5,
        'examples': 15,
        'cultural': 4,
        'realworld': 3,
        'visual': 4,
        'questions': 4,
        'threshold': 95,
    },
}

# Module type weights - what matters for each type
MODULE_TYPE_WEIGHTS = {
    'grammar': {
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
    },
    'history': {
        'engagement': 0.15,
        'primary_sources': 0.25,
        'timeline_markers': 0.15,
        'decolonization': 0.15,
        'cultural': 0.10,
        'visual': 0.10,
        'variety': 0.05,
        'paragraph_var': 0.05,
    },
    'biography': {
        'engagement': 0.15,
        'primary_sources': 0.20,
        'quotes': 0.15,
        'timeline_markers': 0.10,
        'legacy': 0.10,
        'cultural': 0.10,
        'visual': 0.10,
        'variety': 0.05,
        'paragraph_var': 0.05,
    },
    'style': {
        'engagement': 0.15,
        'exemplar_texts': 0.25,
        'model_answers': 0.20,
        'register_analysis': 0.15,
        'transformations': 0.10,
        'visual': 0.10,
        'variety': 0.05,
    },
    'literature': {
        'engagement': 0.15,
        'analysis_sections': 0.20,
        'literary_citations': 0.20,
        'historical_context': 0.15,
        'essays': 0.15,
        'resources': 0.10,
        'variety': 0.05,
    },
    'vocabulary': {
        'engagement': 0.15,
        'collocations': 0.25,
        'usage_examples': 0.20,
        'register_notes': 0.10,
        'cultural': 0.10,
        'visual': 0.10,
        'variety': 0.05,
        'paragraph_var': 0.05,
    },
    'cultural': {
        'engagement': 0.15,
        'cultural': 0.25,
        'authentic_refs': 0.15,
        'regional_refs': 0.15,
        'contemporary': 0.10,
        'visual': 0.10,
        'variety': 0.05,
        'paragraph_var': 0.05,
    },
    'checkpoint': {
        # Checkpoint modules are assessments - emphasis on activity variety
        'engagement': 0.10,
        'activity_types': 0.25,  # Variety of activity types is key
        'variety': 0.15,  # Sentence variety in review sections
        'cultural': 0.10,
        'visual': 0.10,
        'review_sections': 0.20,  # Comprehensive review coverage
        'paragraph_var': 0.10,
    },
    'phraseology': {
        'engagement': 0.15,
        'collocations': 0.25,
        'usage_examples': 0.20,
        'register_notes': 0.15,
        'cultural': 0.10,
        'variety': 0.10,
        'paragraph_var': 0.05,
    },
    'academic': {
        'engagement': 0.10,
        'citations': 0.25,
        'data_refs': 0.20,
        'questions': 0.15,
        'visual': 0.15,
        'variety': 0.10,
        'paragraph_var': 0.05,
    },
}

# Fallback weights for types not explicitly defined
DEFAULT_WEIGHTS = {
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
    # Traditions and folk culture
    'толока', 'вечорниці', 'обжинки', 'досвітки', 'колядування',
    # Art and crafts
    'петриківський', 'Петриківка', 'косівська', 'опішнянська',
    # Historical figures and chronicles
    'Нестор', 'літопис', 'Повість минулих літ',
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

# Primary source markers (for history/biography)
PRIMARY_SOURCE_MARKERS = [
    r'📜',  # Primary source emoji
    r'\[!quote\]',  # Quote callout
    r'писав:',
    r'казав:',
    r'свідчить:',
    r'згадує:',
    r'у листі',
    r'у мемуарах',
    r'у спогадах',
    r'цитата:',
    r'документ',
    r'джерело:',
    r'«[^»]{30,}»',  # Long quotes (30+ chars)
]

# Timeline markers (for history/biography)
TIMELINE_MARKERS = [
    r'\b1[0-9]{3}\b',  # Years 1000-1999
    r'\b20[0-2][0-9]\b',  # Years 2000-2029
    r'\b[IVX]+\s*ст\.?',  # Roman numeral centuries
    r'\b\d+\s*ст\.?',  # Arabic numeral centuries
    r'століття',
    r'епоха',
    r'період',
    r'доба',
    r'рік',
    r'роки',
    r'році',
]

# Decolonization markers
DECOLONIZATION_MARKERS = [
    r'імпер',
    r'колоніал',
    r'русифікац',
    r'національн',
    r'спротив',
    r'незалежн',
    r'автоном',
    r'самовизначен',
    r'деколоніз',
    r'українськ\w+\s+перспектив',
]

# Academic citation markers
CITATION_MARKERS = [
    r'\(\d{4}\)',  # (Year) format
    r'за\s+\w+\s*\(\d{4}\)',  # "за Author (Year)"
    r'дослідження\s+показ',
    r'згідно\s+з',
    r'науков\w+\s+джерел',
    r'статистик',
    r'\d+\s*%',  # Percentages
]

# Collocation markers (for vocabulary modules)
COLLOCATION_PATTERNS = [
    r'\+\s*[А-ЯІЇЄҐа-яіїєґ]+',  # + noun/verb patterns
    r'типов\w+\s+сполучен',
    r'колокаці',
    r'вживається\s+з',
    r'поєднується\s+з',
]

# Register markers
REGISTER_MARKERS = [
    r'розмовн\w+',
    r'формальн\w+',
    r'офіційн\w+',
    r'нейтральн\w+',
    r'книжн\w+',
    r'літературн\w+',
    r'просторічн\w+',
    r'регістр',
]

# Analysis section markers (for LIT modules)
ANALYSIS_MARKERS = [
    r'аналіз',
    r'інтерпретаці',
    r'символ\w+',
    r'образ\w+',
    r'мотив',
    r'тема',
    r'стиль\w+',
    r'поетик',
    r'наратив',
]

# Legacy markers (for biography)
LEGACY_MARKERS = [
    r'спадщина',
    r'вплив',
    r'значення',
    r'внесок',
    r'пам\'ят',
    r'вшануван',
    r'сьогодні',
    r'сучасн',
]


def extract_level(file_path: Union[str, Path, None]) -> str:
    """Extract level code from file path."""
    if not file_path:
        return 'B1'
    if isinstance(file_path, str):
        file_path = Path(file_path)
    parts = file_path.parts
    for part in parts:
        if part.upper() in ('A1', 'A2', 'B1', 'B2', 'C1', 'C2', 'LIT'):
            return part.upper()
    return 'B1'  # Default


def extract_module_type(content: str, file_path: Union[str, Path, None] = None) -> str:
    """Extract module type from frontmatter or YAML sidecar."""
    fm = None

    # Try to parse embedded frontmatter first
    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            try:
                fm = yaml.safe_load(parts[1])
            except yaml.YAMLError:
                pass

    # If no embedded frontmatter, try YAML sidecar
    if not fm and file_path:
        path = Path(file_path) if isinstance(file_path, str) else file_path
        slug = path.stem
        sidecar_path = path.parent / 'meta' / f'{slug}.yaml'
        if sidecar_path.exists():
            try:
                with open(sidecar_path, 'r', encoding='utf-8') as f:
                    fm = yaml.safe_load(f)
            except (yaml.YAMLError, IOError):
                pass

    # Process frontmatter (from either source)
    if fm:
        # Check focus field FIRST (highest priority)
        focus = str(fm.get('focus', '')).lower().strip()
        if focus in MODULE_TYPE_MAP:
            return MODULE_TYPE_MAP[focus]

        # Then check pedagogy field
        pedagogy = str(fm.get('pedagogy', '')).lower().strip()
        if pedagogy in MODULE_TYPE_MAP:
            return MODULE_TYPE_MAP[pedagogy]

        # Check phase field for hints
        phase = str(fm.get('phase', '')).lower()
        if 'history' in phase:
            return 'history'
        elif 'biography' in phase or 'biographies' in phase:
            return 'biography'
        elif 'style' in phase or 'stylistic' in phase:
            return 'style'
        elif 'academic' in phase or 'sociolinguistic' in phase:
            return 'academic'
        elif 'checkpoint' in phase:
            return 'checkpoint'

    # Fallback: infer from path
    path_str = str(file_path).lower()
    if '/lit/' in path_str:
        return 'literature'

    # Default to grammar for B1-B2, content for others
    level = extract_level(file_path)
    if level in ('B1', 'B2'):
        return 'grammar'
    elif level in ('C1', 'C2'):
        return 'content'

    return 'grammar'  # Default


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
    """Count engagement boxes (💡🎬🌍🎯🎮 and callouts).

    Includes B2+ history/cultural callout types.
    """
    patterns = [
        # Standard callouts
        r'>\s*\[!tip\]',
        r'>\s*\[!note\]',
        r'>\s*\[!observe\]',
        r'>\s*\[!warning\]',
        r'>\s*\[!caution\]',
        r'>\s*\[!important\]',
        r'>\s*\[!cultural\]',
        # B2+ history/cultural callouts
        r'>\s*\[!history-bite\]',
        r'>\s*\[!myth-buster\]',
        r'>\s*\[!quote\]',
        r'>\s*\[!context\]',
        r'>\s*\[!analysis\]',
        r'>\s*\[!source\]',
        r'>\s*\[!legacy\]',
        r'>\s*\[!reflection\]',
        # Emoji patterns
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
    """Count Ukrainian example sentences.

    Matches various example formats used in curriculum:
    - Bold sentences: **Це приклад.**
    - Bulleted items: - Це приклад.
    - Numbered items: 1. Це приклад.
    - Labeled examples: *Приклад:* "Це приклад."
    - Blockquote examples: > *Приклад:* Це приклад.
    - Guillemet quotes: «Це приклад.»
    - Definition format: *   **Word** — definition with example.
    - Inline examples with highlighted words in sentences
    """
    patterns = [
        r'\*\*[А-ЯІЇЄҐа-яіїєґ][^*]{5,}[.!?]\*\*',  # Bold Ukrainian sentences
        r'^\s*[-–—]\s*[А-ЯІЇЄҐа-яіїєґ][^.!?]{5,}[.!?]',  # Bulleted Ukrainian
        r'^\s*[-–—]\s*_[А-ЯІЇЄҐа-яіїєґ][^.!?]{5,}[.!?]_',  # Bulleted Italic Ukrainian
        r'^\s*\d+\.\s*[А-ЯІЇЄҐа-яіїєґ][^.!?]{5,}[.!?]',  # Numbered Ukrainian
        r'\*[Пп]риклад[и|:]?\*[:\s]+[«"]?[А-ЯІЇЄҐа-яіїєґ]',  # *Приклад:* or *приклад:* labels
        r'>\s*\*[Пп]риклад',  # Blockquote example labels
        r'«[А-ЯІЇЄҐа-яіїєґ][^»]{10,}[.!?]?»',  # Guillemet-quoted sentences (10+ chars)
        r'^\s*\*\s+\*\*[А-ЯІЇЄҐа-яіїєґ]+\*\*\s*[—–-]',  # * **Word** — definition format
        r'"[А-ЯІЇЄҐа-яіїєґ][^"]{10,}[.!?]"',  # Double-quoted Ukrainian sentences
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
        r'^>\s*—\s*[А-ЯІЇЄҐа-яіїєґ]',  # Em-dash dialogue inside blockquote
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


def count_primary_sources(content: str) -> int:
    """Count primary source references (history/biography)."""
    count = 0
    for pattern in PRIMARY_SOURCE_MARKERS:
        count += len(re.findall(pattern, content, re.IGNORECASE))
    return min(count, 15)


def count_timeline_markers(content: str) -> int:
    """Count timeline/date references (history/biography)."""
    count = 0
    for pattern in TIMELINE_MARKERS:
        count += len(re.findall(pattern, content, re.IGNORECASE))
    return min(count, 30)


def count_decolonization(content: str) -> int:
    """Count decolonization perspective markers."""
    count = 0
    for pattern in DECOLONIZATION_MARKERS:
        count += len(re.findall(pattern, content, re.IGNORECASE))
    return min(count, 15)


def count_citations(content: str) -> int:
    """Count academic citations and data references."""
    count = 0
    for pattern in CITATION_MARKERS:
        count += len(re.findall(pattern, content, re.IGNORECASE))
    return min(count, 20)


def count_collocations(content: str) -> int:
    """Count collocation patterns (vocabulary modules)."""
    count = 0
    for pattern in COLLOCATION_PATTERNS:
        count += len(re.findall(pattern, content, re.IGNORECASE))
    # Also count table rows in collocation tables
    colloc_table = re.search(r'колокаці[їй]|сполучен', content, re.IGNORECASE)
    if colloc_table:
        # Count table rows after the match
        count += len(re.findall(r'^\|[^|]+\|', content[colloc_table.start():], re.MULTILINE)) // 2
    return min(count, 30)


def count_register_notes(content: str) -> int:
    """Count register/style markers."""
    count = 0
    for pattern in REGISTER_MARKERS:
        count += len(re.findall(pattern, content, re.IGNORECASE))
    return min(count, 15)


def count_analysis_sections(content: str) -> int:
    """Count analysis sections (literature modules).
    
    Counts ANY content section (H2/H3) that is not part of the standard 
    structural exclusions (Summary, Vocabulary, Activities, Intro).
    
    This matches the academic nature of LIT modules where headers are 
    flexible (e.g. "The Role of Fate", "Character Arc").
    """
    # Exclude standard structural headers
    EXCLUDED_HEADERS = [
        r'summary', r'підсумок',
        r'vocabulary', r'словник',
        r'activities', r'вправи',
        r'intro', r'вступ',
        r'resources', r'джерела', r'читальна зала',
        r'practicum', r'практикум',
        r'essay', r'есе', r'твір',
    ]
    
    # Get all H2/H3 headers
    headers = re.findall(r'^#{2,3}\s+([^\n]+)', content, re.MULTILINE)
    
    count = 0
    for header in headers:
        header_lower = header.lower()
        is_excluded = False
        
        # Check against exclusions
        for pattern in EXCLUDED_HEADERS:
            if re.search(pattern, header_lower):
                is_excluded = True
                break
                
        if not is_excluded:
            count += 1
            
    return min(count, 10)


def count_legacy_refs(content: str) -> int:
    """Count legacy/impact references (biography)."""
    count = 0
    for pattern in LEGACY_MARKERS:
        count += len(re.findall(pattern, content, re.IGNORECASE))
    return min(count, 15)


def count_quotes(content: str) -> int:
    """Count direct quotes (biography/history)."""
    # Ukrainian quotes in guillemets
    quotes = re.findall(r'«[^»]{20,}»', content)
    # Also count blockquote callouts
    blockquotes = re.findall(r'>\s*\[!quote\]', content)
    return min(len(quotes) + len(blockquotes), 15)


def count_essays(content: str) -> int:
    """Count essay prompts (literature modules).
    
    Counts sections that look like writing assignments.
    """
    # Look for headers indicating writing tasks
    writing_headers = [
        r'есе',
        r'твір',
        r'critical writing',
        r'debate club',
        r'short response',
        r'аналітичний практикум',
        r'творче завдання',
    ]
    
    header_count = 0
    # Scan matches to catch multiple tasks
    for pattern in writing_headers:
        header_count += len(re.findall(pattern, content, re.IGNORECASE))
        
    # Also look for explicit instruction verbs at start of lines or sentences
    instruction_verbs = [
        r'напишіть',
        r'аргументуйте',
        r'проаналізуйте',
        r'порівняйте',
    ]
    verb_count = 0
    for pattern in instruction_verbs:
        verb_count += len(re.findall(pattern, content, re.IGNORECASE))

    # Heuristic: headers are strong signals (1 point), verbs are weak (0.5 point)
    # But to prevent overcounting, we take the MAX of headers or (verbs // 2)
    # Actually, headers like "Завдання: Есе" are the best indicators.
    
    # Let's count specific "Task" blocks
    task_blocks = len(re.findall(r'Завдання \d+:', content))
    
    # If we have "Tasks", use that count if it's supported by writing keywords
    if task_blocks > 0 and (header_count > 0 or verb_count > 0):
        return min(task_blocks, 5)
        
    # Fallback to old heuristic if no clear tasks
    total_signals = header_count + (verb_count // 2)
    return min(int(total_signals), 5)


def count_resources(content: str) -> int:
    """Count external resource references (literature/cultural)."""
    patterns = [
        r'https?://',
        r'ukrlib',
        r'читальня',
        r'бібліотек',
        r'\[!resources\]',
    ]
    count = 0
    for pattern in patterns:
        matches = len(re.findall(pattern, content, re.IGNORECASE))
        count += matches
        # print(f"DEBUG: Pattern {pattern} found {matches} times.")
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


def calculate_richness_score(content: str, level: str, file_path: Path = None, yaml_activity_types: set = None) -> dict:
    """Calculate richness score and components based on module type.

    Args:
        content: Markdown content of the module
        level: CEFR level (A1, A2, B1, B2, C1, C2)
        file_path: Path to the module file (for type detection)
        yaml_activity_types: Set of activity types from YAML file (optional)
    """
    # Determine module type for type-specific criteria
    module_type = extract_module_type(content, file_path) if file_path else 'grammar'
    targets = MODULE_TYPE_TARGETS.get(module_type, MODULE_TYPE_TARGETS['grammar'])
    weights = MODULE_TYPE_WEIGHTS.get(module_type, DEFAULT_WEIGHTS)

    prose = get_prose_content(content)

    # Calculate base components (all module types)
    raw = {
        'engagement': count_engagement_boxes(prose),
        'variety': calculate_variety_score(prose),
        'cultural': count_cultural_refs(prose),
        'visual': count_visual_elements(prose),
        'paragraph_var': calculate_paragraph_variety(prose),
    }

    # Add type-specific components based on module type
    if module_type == 'grammar':
        raw.update({
            'examples': count_examples(prose),
            'dialogues': count_dialogues(prose),
            'realworld': count_realworld(prose),
            'questions': count_questions(prose),
            'proverbs': count_proverbs(prose),
        })
    elif module_type == 'vocabulary':
        raw.update({
            'collocations': count_collocations(prose),
            'usage_examples': count_examples(prose),
            'register_notes': count_register_notes(prose),
        })
    elif module_type == 'history':
        raw.update({
            'primary_sources': count_primary_sources(prose),
            'timeline_markers': count_timeline_markers(prose),
            'decolonization': count_decolonization(prose),
            'questions': count_questions(prose),
        })
    elif module_type == 'biography':
        raw.update({
            'primary_sources': count_primary_sources(prose),
            'quotes': count_quotes(prose),
            'timeline_markers': count_timeline_markers(prose),
            'legacy': count_legacy_refs(prose),
            'questions': count_questions(prose),
        })
    elif module_type == 'academic':
        raw.update({
            'citations': count_citations(prose),
            'data_refs': count_citations(prose),  # Reuse for data
            'questions': count_questions(prose),
        })
    elif module_type == 'style':
        raw.update({
            'exemplar_texts': count_quotes(prose),  # Extended quotes as exemplars
            'model_answers': count_examples(prose),
            'register_analysis': count_register_notes(prose),
        })
    elif module_type == 'literature':
        raw.update({
            'analysis_sections': count_analysis_sections(prose),
            'literary_citations': count_quotes(prose),
            'historical_context': count_timeline_markers(prose),
            'essays': count_essays(prose),
            'resources': count_resources(prose),
        })
    elif module_type == 'checkpoint':
        # Use YAML activity types if provided (Preferred for YAML-First architecture)
        activity_type_count = 0
        if yaml_activity_types:
            activity_type_count = len(yaml_activity_types)
        
        raw.update({
            'activity_types': activity_type_count,
            'review_sections': len(re.findall(r'^##\s*[^\n]+', prose, re.MULTILINE)),
        })
    else:  # 'content' or 'cultural' - generic fallback
        raw.update({
            'examples': count_examples(prose),
            'realworld': count_realworld(prose),
            'questions': count_questions(prose),
        })

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

    # Calculate weighted total using type-specific weights
    total = 0.0
    for k in normalized:
        weight = weights.get(k, 0.05)  # Default weight for unlisted components
        total += normalized[k] * weight

    # Normalize if weights don't sum to 1.0
    weight_sum = sum(weights.get(k, 0.05) for k in normalized)
    if weight_sum > 0:
        total = total / weight_sum
        
    score = int(total * 100)

    # Return NORMALIZED weights so the report math works (sum of weights = 1.0)
    final_weights = {}
    for k in normalized:
        raw_weight = weights.get(k, 0.05)
        final_weights[k] = raw_weight / weight_sum if weight_sum > 0 else 0

    return {
        'score': score,
        'threshold': targets.get('threshold', 95),
        'passed': score >= targets.get('threshold', 95),
        'module_type': module_type,
        'raw': raw,
        'normalized': {k: round(v, 2) for k, v in normalized.items()},
        'targets': {k: targets.get(k, 0) for k in raw if k not in ('variety', 'paragraph_var')},
        'weights': final_weights,
    }


def detect_dryness_flags(content: str, level: str, file_path: Path = None) -> list:
    """Detect dryness indicators based on module type."""
    flags = []
    prose = get_prose_content(content)
    module_type = extract_module_type(content, file_path) if file_path else 'grammar'

    # Universal flags (all module types)
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

    # Type-specific flags - use 50% of target as threshold
    if module_type == 'grammar':
        # Grammar modules: dialogues (target 4), examples (target 24), realworld (target 3), cultural (target 3), proverbs (target 1)
        dialogue_count = count_dialogues(prose)
        if level in ('B1', 'B2', 'C1', 'C2') and dialogue_count < 2:  # < 50% of target 4
            flags.append('LOW_DIALOGUE' if dialogue_count > 0 else 'NO_DIALOGUE')
        if count_examples(prose) < 12:  # < 50% of target 24
            flags.append('NO_EXAMPLES')
        if count_realworld(prose) < 2:  # < 50% of target 3
            flags.append('ABSTRACT_ONLY')
        # Proverbs check for B1+ grammar
        if level in ('B1', 'B2') and count_proverbs(prose) == 0:
            flags.append('NO_PROVERBS')

    elif module_type == 'vocabulary':
        # Vocabulary modules need collocations and register notes
        if count_collocations(prose) < 5:
            flags.append('NO_COLLOCATIONS')
        if count_register_notes(prose) < 2:
            flags.append('NO_REGISTER_NOTES')

    elif module_type == 'history':
        # History modules need primary sources and timeline
        if count_primary_sources(prose) < 2:
            flags.append('NO_PRIMARY_SOURCES')
        if count_timeline_markers(prose) < 5:
            flags.append('NO_TIMELINE')
        if count_decolonization(prose) == 0:
            flags.append('NO_DECOLONIZATION_PERSPECTIVE')

    elif module_type == 'biography':
        # Biography modules need quotes and legacy
        if count_quotes(prose) < 2:
            flags.append('NO_QUOTES')
        if count_legacy_refs(prose) < 1:
            flags.append('NO_LEGACY_DISCUSSION')
        if count_timeline_markers(prose) < 5:
            flags.append('NO_TIMELINE')

    elif module_type == 'literature':
        # Literature modules need analysis and citations
        if count_analysis_sections(prose) < 3:
            flags.append('NO_ANALYSIS')
        if count_quotes(prose) < 3:
            flags.append('NO_LITERARY_CITATIONS')
        if count_resources(prose) < 2:
            flags.append('NO_RESOURCES')

    elif module_type == 'style':
        # Style modules need exemplar texts and register analysis
        if count_quotes(prose) < 2:
            flags.append('NO_EXEMPLAR_TEXTS')
        if count_register_notes(prose) < 3:
            flags.append('NO_REGISTER_ANALYSIS')

    elif module_type in ('content', 'cultural'):
        # Cultural/content modules need examples and real-world refs
        if count_examples(prose) < 8:
            flags.append('NO_EXAMPLES')
        if count_realworld(prose) == 0:
            flags.append('ABSTRACT_ONLY')

    # Cultural anchor check (B1+ grammar/vocab/content types) - need 2+ (50% of target 3)
    if module_type in ('grammar', 'vocabulary', 'content', 'cultural'):
        cultural_count = count_cultural_refs(prose)
        if level in ('B1', 'B2', 'C1', 'C2') and cultural_count < 2:
            flags.append('LOW_CULTURAL_ANCHOR' if cultural_count > 0 else 'NO_CULTURAL_ANCHOR')

    return flags


def main():
    if len(sys.argv) < 2:
        print("Usage: .venv/bin/python scripts/calculate_richness.py <file> [--json]")
        sys.exit(1)

    file_path = Path(sys.argv[1])
    output_json = '--json' in sys.argv

    if not file_path.exists():
        print(f"Error: File not found: {file_path}")
        sys.exit(1)

    content = file_path.read_text(encoding='utf-8')
    level = extract_level(file_path)

    result = calculate_richness_score(content, level, file_path)
    flags = detect_dryness_flags(content, level, file_path)

    if output_json:
        result['flags'] = flags
        print(json.dumps(result, indent=2))
    else:
        module_type = result.get('module_type', 'grammar')
        weights = result.get('weights', DEFAULT_WEIGHTS)

        print(f"Module Type: {module_type}")
        print(f"Richness Score: {result['score']}/100 (threshold: {result['threshold']})")
        print(f"Status: {'✅ PASS' if result['passed'] else '❌ FAIL'}")
        print()
        print("### Score Breakdown")
        print("| Metric | Count | Target | Score | Weight | Contribution |")
        print("|--------|-------|--------|-------|--------|--------------|")
        
        total_contribution = 0.0
        
        # Sort keys for consistent output (prioritize higher weights)
        sorted_keys = sorted(result['raw'].keys(), key=lambda k: weights.get(k, 0), reverse=True)
        
        for key in sorted_keys:
            raw = result['raw'].get(key, 0)
            norm = result['normalized'].get(key, 0)
            target = result['targets'].get(key, '—')
            weight = weights.get(key, 0.05)
            contribution = norm * weight * 100
            total_contribution += contribution
            
            # Format columns
            if key in ('variety', 'paragraph_var'):
                count_str = f"{raw:.2f}"
                target_str = "-"
            else:
                count_str = str(raw)
                target_str = str(target)
                
            print(f"| {key} | {count_str} | {target_str} | {norm:.0%} | {weight:.0%} | {contribution:.1f}% |")
            
        print(f"| **TOTAL** | | | | | **{total_contribution:.1f}%** |")
        print()

        if flags:
            print("### Dryness Flags")
            for flag in flags:
                print(f"- ⚠️ {flag}")
            if len(flags) >= 2:
                print()
                print("> [!WARNING]")
                print("> ❌ 2+ flags: Content needs REWRITE, not just fix")
        else:
            print("Dryness Flags: None")

    sys.exit(0 if result['passed'] else 1)


if __name__ == '__main__':
    main()
