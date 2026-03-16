"""Content counter functions for richness scoring.

Each function counts a specific type of content element (engagement boxes,
examples, dialogues, cultural references, etc.) in module markdown text.
Used by the main calculate_richness module to compute richness scores.
"""

from __future__ import annotations

import re
import statistics
from pathlib import Path

import yaml
from calculate_richness_config import (
    CITATION_MARKERS,
    COLLOCATION_PATTERNS,
    CULTURAL_TERMS,
    DECOLONIZATION_MARKERS,
    LEGACY_MARKERS,
    PRIMARY_SOURCE_MARKERS,
    PROVERB_MARKERS,
    REGISTER_MARKERS,
    TIMELINE_MARKERS,
    UKRAINIAN_PLACES,
)
from slug_utils import to_bare_slug


def count_engagement_boxes(content: str) -> int:
    """Count engagement boxes (callouts and emoji-prefixed bold sections)."""
    patterns = [
        r'>\s*\[!tip\]',
        r'>\s*\[!note\]',
        r'>\s*\[!observe\]',
        r'>\s*\[!warning\]',
        r'>\s*\[!caution\]',
        r'>\s*\[!important\]',
        r'>\s*\[!cultural\]',
        r'>\s*\[!history-bite\]',
        r'>\s*\[!myth-buster\]',
        r'>\s*\[!quote\]',
        r'>\s*\[!context\]',
        r'>\s*\[!analysis\]',
        r'>\s*\[!source\]',
        r'>\s*\[!legacy\]',
        r'>\s*\[!reflection\]',
        r'💡\s*\*\*',
        r'🎬\s*\*\*',
        r'🌍\s*\*\*',
        r'🎯\s*\*\*',
        r'🎮\s*\*\*',
        r'🎭\s*\*\*',
        r'📝\s*\*\*',
        r'🔍\s*\*\*',
        r'📚\s*\*\*',
        r'🎓\s*\*\*',
        r'⚠️\s*\*\*',
        r'🗣️\s*\*\*',
    ]
    count = 0
    for pattern in patterns:
        count += len(re.findall(pattern, content, re.MULTILINE))
    return count


def count_examples(content: str) -> int:
    """Count Ukrainian example sentences and word-level examples.

    Matches both sentence-level examples (Ukrainian sentences with punctuation)
    and word-level examples common in A1 beginner modules:
    - **слово** — translation
    - **слово** (translation)
    """
    patterns = [
        # Sentence-level examples
        r'\*\*[А-ЯІЇЄҐа-яіїєґ][^*]{5,}[.!?]\*\*',
        r'^\s*[-–—]\s*[А-ЯІЇЄҐа-яіїєґ][^.!?]{5,}[.!?]',
        r'^\s*[-–—]\s*_[А-ЯІЇЄҐа-яіїєґ][^.!?]{5,}[.!?]_',
        r'^\s*\d+\.\s*[А-ЯІЇЄҐа-яіїєґ][^.!?]{5,}[.!?]',
        r'\*[Пп]риклад[и|:]?\*[:\s]+[«"]?[А-ЯІЇЄҐа-яіїєґ]',
        r'>\s*\*[Пп]риклад',
        r'«[А-ЯІЇЄҐа-яіїєґ][^»]{10,}[.!?]?»',
        r'"[А-ЯІЇЄҐа-яіїєґ][^"]{10,}[.!?]"',
        # Word-level examples: **word** — translation or **word** (translation)
        r'^\s*[-–—*]\s*\*\*[А-ЯІЇЄҐа-яіїєґ][^*]+\*\*\s*[—–\-]\s*\w',
        r'^\s*[-–—*]\s*\*\*[А-ЯІЇЄҐа-яіїєґ][^*]+\*\*\s*\([^)]+\)',
    ]
    count = 0
    for pattern in patterns:
        count += len(re.findall(pattern, content, re.MULTILINE))
    return min(count, 100)


def count_dialogues(content: str) -> int:
    """Count mini-dialogues (pairs of dialogue lines)."""
    patterns = [
        r'^[АБВ]:\s',
        r'^\*\*[АБВ]:\*\*\s',
        r'^—\s*[А-ЯІЇЄҐа-яіїєґ]',
        r'^>\s*—\s*[А-ЯІЇЄҐа-яіїєґ]',
        r'^>\s*\*\*[А-ЯІЇЄҐа-яіїєґ][^*]*?:\*\*\s',
        r'^[А-ЯІЇЄҐа-яіїєґ]+:\s+[А-ЯІЇЄҐа-яіїєґ]',
    ]
    count = 0
    for pattern in patterns:
        count += len(re.findall(pattern, content, re.MULTILINE))
    return count // 2


def calculate_variety_score(content: str) -> float:
    """Calculate sentence starter variety (0.0-1.0)."""
    sentences = re.findall(r'[А-ЯІЇЄҐа-яіїєґA-Za-z][^.!?]*[.!?]', content)
    if len(sentences) < 5:
        return 0.5

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
    """Count cultural references (places, traditions, people, cultural boxes)."""
    count = 0
    for place in UKRAINIAN_PLACES:
        if place in content:
            count += 1
    for term in CULTURAL_TERMS:
        if term.lower() in content.lower():
            count += 1
    # Count [!cultural] and [!culture] engagement boxes (common in A1)
    count += len(re.findall(r'>\s*\[!cultur', content, re.IGNORECASE))
    return min(count, 20)


def count_realworld(content: str) -> int:
    """Count real-world context markers."""
    patterns = [
        r'уявіть', r'наприклад', r'у реальному житті', r'на практиці',
        r'коли ви', r'якщо ви', r'у магазині', r'на роботі',
        r'у ресторані', r'на вулиці', r'в аеропорту', r'на вокзалі',
        r'у лікарні', r'в університеті',
        r'imagine', r'for example', r'in real life', r'when you', r'at the',
    ]
    count = 0
    for pattern in patterns:
        count += len(re.findall(pattern, content, re.IGNORECASE))
    return min(count, 20)


def count_questions(content: str) -> int:
    """Count interactive questions in prose."""
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
    colloc_table = re.search(r'колокаці[їй]|сполучен', content, re.IGNORECASE)
    if colloc_table:
        count += len(re.findall(
            r'^[> ]*\|[^|]+\|', content[colloc_table.start():], re.MULTILINE
        )) // 2
    return min(count, 30)


def count_register_notes(content: str) -> int:
    """Count register/style markers."""
    count = 0
    for pattern in REGISTER_MARKERS:
        count += len(re.findall(pattern, content, re.IGNORECASE))
    return min(count, 15)


def count_analysis_sections(content: str) -> int:
    """Count content sections (H2/H3) excluding standard structural headers."""
    excluded_headers = [
        r'summary', r'підсумок',
        r'vocabulary', r'словник',
        r'activities', r'вправи',
        r'intro', r'вступ',
        r'resources', r'джерела', r'читальна зала',
        r'practicum', r'практикум',
        r'essay', r'есе', r'твір',
    ]

    headers = re.findall(r'^#{2,3}\s+([^\n]+)', content, re.MULTILINE)
    count = 0
    for header in headers:
        header_lower = header.lower()
        is_excluded = any(
            re.search(pattern, header_lower) for pattern in excluded_headers
        )
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
    quotes = re.findall(r'«[^»]{20,}»', content)
    blockquotes = re.findall(r'>\s*\[!quote\]', content)
    return min(len(quotes) + len(blockquotes), 15)


def count_essays(content: str) -> int:
    """Count essay prompts (literature modules)."""
    writing_headers = [
        r'есе', r'твір', r'critical writing', r'debate club',
        r'short response', r'аналітичний практикум', r'творче завдання',
    ]
    header_count = 0
    for pattern in writing_headers:
        header_count += len(re.findall(pattern, content, re.IGNORECASE))

    instruction_verbs = [
        r'напишіть', r'аргументуйте', r'проаналізуйте', r'порівняйте',
    ]
    verb_count = 0
    for pattern in instruction_verbs:
        verb_count += len(re.findall(pattern, content, re.IGNORECASE))

    task_blocks = len(re.findall(r'Завдання \d+:', content))
    if task_blocks > 0 and (header_count > 0 or verb_count > 0):
        return min(task_blocks, 5)

    total_signals = header_count + (verb_count // 2)
    return min(int(total_signals), 5)


def count_resources(content: str) -> int:
    """Count external resource references (literature/cultural)."""
    patterns = [
        r'https?://', r'ukrlib', r'читальня', r'бібліотек', r'\[!resources\]',
    ]
    count = 0
    for pattern in patterns:
        count += len(re.findall(pattern, content, re.IGNORECASE))
    return min(count, 10)


def count_visual_elements(content: str) -> int:
    """Count visual elements (callouts, code blocks, mermaid). Tables scored separately."""
    callouts = len(re.findall(r'>\s*\[!', content, re.MULTILINE))
    mermaid = len(re.findall(r'```mermaid', content))
    code_fences = len(re.findall(r'```', content, re.MULTILINE))
    code_blocks = max(0, (code_fences - mermaid * 2) // 2)
    return callouts + code_blocks + mermaid


def count_tables(content: str) -> int:
    """Count distinct markdown tables (by separator rows)."""
    return len(re.findall(r'^\|[-:| ]+\|', content, re.MULTILINE))


def count_video_embeds(content: str) -> int:
    """Count YouTube video links and Starlight youtubeVideo embeds."""
    youtube_links = len(re.findall(r'youtube\.com/watch', content))
    youtube_components = len(re.findall(r'\{%\s*youtubeVideo\s', content))
    mdx_youtube = len(re.findall(r'<YouTubeVideo\b', content, re.IGNORECASE))
    return youtube_links + youtube_components + mdx_youtube


def count_mermaid_diagrams(content: str) -> int:
    """Count mermaid diagram blocks."""
    return len(re.findall(r'```mermaid', content))


def calculate_paragraph_variety(content: str) -> float:
    """Calculate paragraph length variety (0.0-1.0)."""
    paragraphs = re.split(r'\n\s*\n', content)
    lengths = [len(p.split()) for p in paragraphs if len(p.split()) > 5]

    if len(lengths) < 3:
        return 0.5

    try:
        std_dev = statistics.stdev(lengths)
        return min(std_dev / 20, 1.0)
    except statistics.StatisticsError:
        return 0.5


def count_external_yaml_resources(file_path: Path | str | None) -> int:
    """Count resources defined in docs/resources/external_resources.yaml."""
    if not file_path:
        return 0

    if isinstance(file_path, str):
        file_path = Path(file_path)

    try:
        script_path = Path(__file__).resolve()
        project_root = script_path.parent.parent
        resource_yaml_path = project_root / 'docs' / 'resources' / 'external_resources.yaml'

        if not resource_yaml_path.exists():
            return 0

        with open(resource_yaml_path, encoding='utf-8') as f:
            data = yaml.safe_load(f)

        if not data or 'resources' not in data:
            return 0

        slug = file_path.stem
        clean_slug = to_bare_slug(slug) if slug else slug

        resources = data['resources']
        count = 0

        for key in [slug, clean_slug]:
            if key and key in resources:
                module_res = resources[key]
                if module_res and isinstance(module_res, dict):
                    for cat_list in module_res.values():
                        if isinstance(cat_list, list):
                            count += len(cat_list)
                if count > 0:
                    break

        return count
    except Exception:
        return 0
