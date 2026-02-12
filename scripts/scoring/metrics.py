"""
Metric extraction functions for track scoring.

All functions in this module are fully automated (no LLM calls).
They extract quantitative metrics from module content files.
"""

import re
import json
import sys
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field

# Ensure scripts/ is importable for audit.status_cache
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from audit.status_cache import read_status


@dataclass
class ModuleMetrics:
    """Container for all extracted metrics from a single module."""
    module_slug: str
    level: str

    # File existence
    md_exists: bool = False
    meta_exists: bool = False
    activities_exists: bool = False
    vocabulary_exists: bool = False
    status_exists: bool = False

    # Audit status (from status JSON)
    audit_status: str = 'unknown'  # pass, fail, unknown
    naturalness_score: Optional[float] = None
    validation_tier: str = 'automated'  # automated, llm-verified, gold-standard

    # Word counts
    word_count: int = 0
    target_word_count: int = 0

    # Callout counts
    quote_callouts: int = 0         # [!quote] blocks
    myth_buster_callouts: int = 0   # [!myth-buster] blocks
    history_bite_callouts: int = 0  # [!history-bite] blocks
    analysis_callouts: int = 0      # [!analysis] blocks
    context_callouts: int = 0       # Cultural/historical context callouts
    resources_callouts: int = 0     # [!resources] blocks

    # Agency markers (Ukrainian subjects with active verbs)
    agency_markers: int = 0
    total_sentences: int = 0

    # Toponym analysis
    toponym_violations: int = 0     # Colonial/Russian place names found
    ukrainian_toponyms: int = 0     # Proper Ukrainian place names

    # Vocabulary
    vocab_items: int = 0
    era_vocab_items: int = 0        # Period-specific vocabulary
    archaic_vocab_items: int = 0    # Archaic/literary vocabulary

    # Cross-references
    cross_references: int = 0       # "Related:" or internal links
    intertextual_links: int = 0     # References to other literary works

    # Literary metrics
    citation_ratio: float = 0.0     # Proportion of direct quotes
    stylistic_devices: int = 0      # Literary devices mentioned
    analysis_sections: int = 0      # H2/H3 sections with analysis keywords
    legacy_sections: int = 0        # Sections discussing legacy/impact

    # Activity metrics
    activity_count: int = 0
    activity_items: int = 0
    critical_analysis_activities: int = 0
    reading_activities: int = 0
    essay_activities: int = 0

    # Raw content for debugging
    errors: list[str] = field(default_factory=list)


# =============================================================================
# CALLOUT EXTRACTION
# =============================================================================

# Regex patterns for callout blocks (Obsidian-style and custom)
CALLOUT_PATTERNS = {
    'quote': [
        r'>\s*\[!quote\]',
        r'>\s*«[^»]+»',  # Direct quotes in Ukrainian quote marks
        r'> «[^»]+»\s*\n>\s*—\s*\*[^*]+\*',  # Quote with attribution
    ],
    'myth_buster': [
        r'>\s*\[!myth-buster\]',
        r'>\s*\[!myth\]',
        r'###?\s*(?:Міф|Myth)',  # Section headers
    ],
    'history_bite': [
        r'>\s*\[!history-bite\]',
        r'>\s*\[!history\]',
        r'>\s*🏛️',  # History emoji callout
    ],
    'analysis': [
        r'>\s*\[!analysis\]',
        r'###?\s*Аналіз:',
        r'###?\s*Інтерпретація:',
        r'###?\s*Символіка:',
    ],
    'context': [
        r'>\s*🇺🇦\s*\*\*Культурний момент\*\*',
        r'>\s*🌍\s*\*\*У реальному житті\*\*',
        r'>\s*💡\s*\*\*Чи знали ви\?\*\*',
    ],
    'resources': [
        r'>\s*\[!resources\]',
        r'###?\s*Додаткові ресурси',
    ],
}


def count_callouts(content: str) -> dict[str, int]:
    """
    Count different types of callout blocks in markdown content.

    Args:
        content: Markdown file content

    Returns:
        Dictionary of callout type -> count
    """
    counts = {}
    for callout_type, patterns in CALLOUT_PATTERNS.items():
        count = 0
        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE | re.MULTILINE)
            count += len(matches)
        counts[callout_type] = count
    return counts


# =============================================================================
# AGENCY MARKER DETECTION
# =============================================================================

# Ukrainian subject patterns (nominative case nouns/pronouns that indicate Ukrainian agency)
UKRAINIAN_AGENCY_SUBJECTS = [
    # People
    r'українці', r'українки', r'українець', r'українка',
    r'народ', r'люди', r'громада', r'суспільство',
    r'козаки', r'козак', r'гетьман', r'отаман',
    r'селяни', r'селянин', r'ремісники', r'міщани',
    r'вчені', r'письменники', r'художники', r'митці',
    r'повстанці', r'борці', r'захисники', r'воїни',
    # Collective/institutional
    r'Україна', r'УНР', r'ЗУНР', r'Січ', r'Рада',
    r'Запорозька Січ', r'Гетьманщина', r'Галичина',
    # Pronouns (when context is Ukrainian)
    # Exclude state-of-being verbs (був/була/було/були)
    r'вони\s+(?!бул[аиов])',  # "they" with active verb
    r'ми\s+(?!бул[аиов])',    # "we" with active verb
]

# Active verb patterns (past tense, excluding passive)
ACTIVE_VERB_PATTERNS = [
    r'\b\w+ли\b',   # Past tense plural
    r'\b\w+ав\b',   # Past tense masculine singular
    r'\b\w+ла\b',   # Past tense feminine singular
    r'\b\w+ло\b',   # Past tense neuter singular
    r'\b\w+ить\b',  # Present tense 3rd person singular
    r'\b\w+ять\b',  # Present tense 3rd person plural
    r'\b\w+уть\b',  # Present tense 3rd person plural (variation)
]


def count_agency_markers(content: str) -> tuple[int, int]:
    """
    Count sentences where Ukrainian subjects have active verbs.

    This measures decolonization perspective by detecting how often
    Ukrainians are portrayed as active agents vs passive recipients.

    Args:
        content: Markdown file content

    Returns:
        Tuple of (agency_marker_count, total_sentence_count)
    """
    # Split into sentences (rough approximation)
    sentences = re.split(r'[.!?]+', content)
    sentences = [s.strip() for s in sentences if s.strip()]

    total_sentences = len(sentences)
    agency_count = 0

    for sentence in sentences:
        # Check if sentence contains Ukrainian agency subject
        has_ukrainian_subject = False
        for pattern in UKRAINIAN_AGENCY_SUBJECTS:
            if re.search(pattern, sentence, re.IGNORECASE):
                has_ukrainian_subject = True
                break

        if not has_ukrainian_subject:
            continue

        # Check if sentence has active verb
        has_active_verb = False
        for pattern in ACTIVE_VERB_PATTERNS:
            if re.search(pattern, sentence):
                has_active_verb = True
                break

        if has_active_verb:
            agency_count += 1

    return agency_count, total_sentences


# =============================================================================
# TOPONYM ANALYSIS
# =============================================================================

# Colonial/Russian place names (violations)
COLONIAL_TOPONYMS = [
    r'\bКиев\b',        # Russian form of Kyiv
    r'\bХарьков\b',     # Russian form of Kharkiv
    r'\bЛьвов\b',       # Russian form of Lviv
    r'\bОдесса\b',      # Russian form of Odesa
    r'\bДнепр(?:опетровск)?\b',  # Russian forms
    r'\bНиколаев\b',    # Russian form of Mykolaiv
    r'\bЗапорожье\b',   # Russian form of Zaporizhzhia
    r'\bЧернигов\b',    # Russian form of Chernihiv
    r'\bМалороссия\b',  # Colonial term
    r'\bЮго-запад(?:ная|ный)\sРусь\b',  # Colonial framing
    r'\bЮжная Русь\b',  # Colonial framing
]

# Correct Ukrainian toponyms
UKRAINIAN_TOPONYMS = [
    r'\bКиїв\b', r'\bХарків\b', r'\bЛьвів\b', r'\bОдеса\b',
    r'\bДніпро\b', r'\bМиколаїв\b', r'\bЗапоріжжя\b', r'\bЧернігів\b',
    r'\bПолтава\b', r'\bВінниця\b', r'\bЖитомир\b', r'\bСуми\b',
    r'\bЧеркаси\b', r'\bІвано-Франківськ\b', r'\bТернопіль\b',
    r'\bРівне\b', r'\bЛуцьк\b', r'\bУжгород\b', r'\bХерсон\b',
    r'\bМаріуполь\b', r'\bКременчук\b', r'\bКропивницький\b',
]


def analyze_toponyms(content: str) -> tuple[int, int]:
    """
    Analyze place name usage for decolonization compliance.

    Args:
        content: Markdown file content

    Returns:
        Tuple of (violations_count, correct_ukrainian_count)
    """
    violations = 0
    correct = 0

    for pattern in COLONIAL_TOPONYMS:
        matches = re.findall(pattern, content, re.IGNORECASE)
        violations += len(matches)

    for pattern in UKRAINIAN_TOPONYMS:
        matches = re.findall(pattern, content)
        correct += len(matches)

    return violations, correct


# =============================================================================
# CROSS-REFERENCE EXTRACTION
# =============================================================================

CROSS_REFERENCE_PATTERNS = [
    r'(?:^|\n)Related:\s*\S',   # "Related:" at line start with content (actual format)
    r'Related:\s*\[',           # "Related:" blocks with markdown links
    r'\[\[M\d+',                # Wiki-style internal links
    r'див\.\s*модуль',          # Ukrainian "see module"
    r'Пов\'язано:',             # Ukrainian "Related:"
    r'\(див\.\s*M\d+',          # See module reference
    r'Дивіться також:',         # "See also:"
]


def count_cross_references(content: str) -> int:
    """
    Count cross-references to other modules.

    Args:
        content: Markdown file content

    Returns:
        Number of cross-references found
    """
    count = 0
    for pattern in CROSS_REFERENCE_PATTERNS:
        matches = re.findall(pattern, content, re.IGNORECASE)
        count += len(matches)
    return count


# =============================================================================
# CITATION RATIO CALCULATION
# =============================================================================

def calculate_citation_ratio(content: str) -> float:
    """
    Calculate the ratio of directly quoted text to total content.

    For literary tracks, this measures engagement with original texts.

    Args:
        content: Markdown file content

    Returns:
        Float between 0.0 and 1.0 representing citation ratio
    """
    # Find all quoted text (Ukrainian quote marks or blockquotes)
    quote_patterns = [
        r'«([^»]+)»',           # Ukrainian quotes
        r'>\s*«([^»]+)»',       # Blockquote with Ukrainian quotes
        r'"([^"]+)"',           # English quotes
    ]

    quoted_chars = 0
    for pattern in quote_patterns:
        matches = re.findall(pattern, content)
        for match in matches:
            quoted_chars += len(match)

    # Get total character count (excluding markdown syntax)
    clean_content = re.sub(r'[#*_`\[\]()]', '', content)
    total_chars = len(clean_content)

    if total_chars == 0:
        return 0.0

    return quoted_chars / total_chars


# =============================================================================
# LITERARY METRICS
# =============================================================================

STYLISTIC_DEVICE_KEYWORDS = [
    # Ukrainian terms
    r'метафор[аи]', r'порівнянн[яі]', r'епітет',
    r'алітераці[яї]', r'анафор[аи]', r'гіпербол[аи]',
    r'іроні[яї]', r'символ', r'алегорі[яї]',
    r'персоніфікаці[яї]', r'оксюморон', r'антитез[аи]',
    r'риторичн\w+\s+питання', r'паралелізм',
    # English terms (for bilingual modules)
    r'metaphor', r'simile', r'epithet', r'alliteration',
    r'anaphora', r'hyperbole', r'irony', r'symbol',
]

ANALYSIS_SECTION_KEYWORDS = [
    r'##\s*.*аналіз',
    r'##\s*.*інтерпретаці',
    r'##\s*.*символіка',
    r'##\s*.*тема',
    r'##\s*.*художні засоби',
    r'##\s*.*стиль',
    r'##\s*.*композиці',
]

LEGACY_SECTION_KEYWORDS = [
    r'##\s*.*спадщина',
    r'##\s*.*вплив',
    r'##\s*.*legacy',
    r'##\s*.*значення',
    r'##\s*.*наслідки',
]


def count_stylistic_devices(content: str) -> int:
    """Count mentions of literary/stylistic devices."""
    count = 0
    for pattern in STYLISTIC_DEVICE_KEYWORDS:
        matches = re.findall(pattern, content, re.IGNORECASE)
        count += len(matches)
    return count


def count_analysis_sections(content: str) -> int:
    """Count H2/H3 sections with analysis keywords."""
    count = 0
    for pattern in ANALYSIS_SECTION_KEYWORDS:
        matches = re.findall(pattern, content, re.IGNORECASE)
        count += len(matches)
    return count


def count_legacy_sections(content: str) -> int:
    """Count H2/H3 sections discussing legacy/impact."""
    count = 0
    for pattern in LEGACY_SECTION_KEYWORDS:
        matches = re.findall(pattern, content, re.IGNORECASE)
        count += len(matches)
    return count


# =============================================================================
# ACTIVITY ANALYSIS
# =============================================================================

def analyze_activities(activities_path: Path) -> dict:
    """
    Analyze activity file for metrics.

    Args:
        activities_path: Path to activities YAML file

    Returns:
        Dictionary of activity metrics
    """
    result = {
        'activity_count': 0,
        'activity_items': 0,
        'critical_analysis_activities': 0,
        'reading_activities': 0,
        'essay_activities': 0,
    }

    if not activities_path.exists():
        return result

    try:
        import yaml
        with open(activities_path, 'r', encoding='utf-8') as f:
            activities = yaml.safe_load(f)

        if not activities:
            return result

        if isinstance(activities, dict) and 'activities' in activities:
            activities = activities['activities']

        if not isinstance(activities, list):
            return result

        result['activity_count'] = len(activities)

        for activity in activities:
            if not isinstance(activity, dict):
                continue

            act_type = activity.get('type', '')

            # Count items in activity
            items = activity.get('items', [])
            if isinstance(items, list):
                result['activity_items'] += len(items)
            elif 'text' in activity:  # Some activities have text instead of items
                result['activity_items'] += 1

            # Categorize by type
            if act_type in ('critical-analysis', 'comparative-study', 'source-analysis'):
                result['critical_analysis_activities'] += 1
            elif act_type == 'reading':
                result['reading_activities'] += 1
            elif act_type in ('essay-response', 'essay'):
                result['essay_activities'] += 1

    except Exception as e:
        result['error'] = str(e)

    return result


# =============================================================================
# VOCABULARY ANALYSIS
# =============================================================================

def analyze_vocabulary(vocab_path: Path) -> dict:
    """
    Analyze vocabulary file for metrics.

    Args:
        vocab_path: Path to vocabulary YAML file

    Returns:
        Dictionary of vocabulary metrics
    """
    result = {
        'vocab_items': 0,
        'era_vocab_items': 0,
        'archaic_vocab_items': 0,
    }

    if not vocab_path.exists():
        return result

    try:
        import yaml
        with open(vocab_path, 'r', encoding='utf-8') as f:
            vocab = yaml.safe_load(f)

        if not vocab:
            return result

        # Handle different YAML structures
        items = []
        if isinstance(vocab, list):
            items = vocab
        elif isinstance(vocab, dict):
            items = vocab.get('vocabulary', vocab.get('items', []))

        if not isinstance(items, list):
            return result

        result['vocab_items'] = len(items)

        # Check for era/archaic markers
        for item in items:
            if not isinstance(item, dict):
                continue

            # Check for era markers
            era = item.get('era', item.get('period', ''))
            if era:
                result['era_vocab_items'] += 1

            # Check for archaic/literary markers
            register = item.get('register', item.get('style', ''))
            if register and any(x in str(register).lower() for x in ['archaic', 'literary', 'застаріл', 'книжн']):
                result['archaic_vocab_items'] += 1

    except Exception as e:
        result['error'] = str(e)

    return result


# =============================================================================
# STATUS JSON PARSING
# =============================================================================

def parse_status_json(status_path: Path) -> dict:
    """
    Parse status JSON file for audit results via shared status cache layer.

    Args:
        status_path: Path to status JSON file

    Returns:
        Dictionary of audit metrics
    """
    result = {
        'audit_status': 'unknown',
        'naturalness_score': None,
        'word_count': 0,
        'target_word_count': 0,
    }

    # Use shared access layer (no freshness check — scoring is informational)
    status_result = read_status(status_path)
    if status_result is None:
        return result

    try:
        status = status_result.data

        # Overall status
        overall = status.get('overall', {})
        result['audit_status'] = overall.get('status', 'unknown')

        # Gates
        gates = status.get('gates', {})

        # Naturalness
        naturalness = gates.get('naturalness', {})
        if naturalness:
            msg = naturalness.get('message', '')
            # Parse "10/10 (High)" format
            match = re.search(r'(\d+(?:\.\d+)?)/10', msg)
            if match:
                result['naturalness_score'] = float(match.group(1))

        # Word count
        lesson = gates.get('lesson', {})
        if lesson:
            msg = lesson.get('message', '')
            # Parse "1418/300 (raw: 1818)" format
            match = re.search(r'(\d+)/(\d+)', msg)
            if match:
                result['word_count'] = int(match.group(1))
                result['target_word_count'] = int(match.group(2))

    except Exception as e:
        result['error'] = str(e)

    return result


# =============================================================================
# MAIN EXTRACTION FUNCTION
# =============================================================================

def extract_module_metrics(
    level_dir: Path,
    module_slug: str,
    level_code: str
) -> ModuleMetrics:
    """
    Extract all metrics from a single module.

    This is the main entry point for metric extraction.
    All operations are automated (no LLM calls).

    Args:
        level_dir: Path to level directory (e.g., curriculum/l2-uk-en/b2-hist)
        module_slug: Module slug (e.g., "01-trypilska-kultura")
        level_code: Level code (e.g., "b2-hist")

    Returns:
        ModuleMetrics dataclass with all extracted metrics
    """
    metrics = ModuleMetrics(module_slug=module_slug, level=level_code)

    # Find module files
    # Try to find MD file with or without number prefix
    md_candidates = list(level_dir.glob(f"*{module_slug}.md"))
    if not md_candidates:
        md_candidates = list(level_dir.glob(f"{module_slug}.md"))

    md_path = md_candidates[0] if md_candidates else level_dir / f"{module_slug}.md"
    meta_path = level_dir / 'meta' / f"{module_slug}.yaml"
    activities_path = level_dir / 'activities' / f"{module_slug}.yaml"
    vocab_path = level_dir / 'vocabulary' / f"{module_slug}.yaml"
    status_path = level_dir / 'status' / f"{module_slug}.json"

    # Check file existence
    metrics.md_exists = md_path.exists()
    metrics.meta_exists = meta_path.exists()
    metrics.activities_exists = activities_path.exists()
    metrics.vocabulary_exists = vocab_path.exists()
    metrics.status_exists = status_path.exists()

    # Parse status JSON first (for word counts and audit status)
    if metrics.status_exists:
        status_data = parse_status_json(status_path)
        metrics.audit_status = status_data['audit_status']
        metrics.naturalness_score = status_data['naturalness_score']
        metrics.word_count = status_data['word_count']
        metrics.target_word_count = status_data['target_word_count']

    # Extract from metadata
    if metrics.meta_exists:
        try:
            import yaml
            with open(meta_path, 'r', encoding='utf-8') as f:
                meta_data = yaml.safe_load(f)
                if meta_data:
                    metrics.validation_tier = meta_data.get('validation_tier', 'automated')
        except Exception as e:
            metrics.errors.append(f"Meta parsing error: {e}")

    # Extract from markdown content
    if metrics.md_exists:
        try:
            with open(md_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Callout counts
            callouts = count_callouts(content)
            metrics.quote_callouts = callouts.get('quote', 0)
            metrics.myth_buster_callouts = callouts.get('myth_buster', 0)
            metrics.history_bite_callouts = callouts.get('history_bite', 0)
            metrics.analysis_callouts = callouts.get('analysis', 0)
            metrics.context_callouts = callouts.get('context', 0)
            metrics.resources_callouts = callouts.get('resources', 0)

            # Agency markers
            agency, total = count_agency_markers(content)
            metrics.agency_markers = agency
            metrics.total_sentences = total

            # Toponyms
            violations, correct = analyze_toponyms(content)
            metrics.toponym_violations = violations
            metrics.ukrainian_toponyms = correct

            # Cross-references
            metrics.cross_references = count_cross_references(content)

            # Literary metrics
            metrics.citation_ratio = calculate_citation_ratio(content)
            metrics.stylistic_devices = count_stylistic_devices(content)
            metrics.analysis_sections = count_analysis_sections(content)
            metrics.legacy_sections = count_legacy_sections(content)

        except Exception as e:
            metrics.errors.append(f"MD parsing error: {e}")

    # Extract from activities
    if metrics.activities_exists:
        activity_data = analyze_activities(activities_path)
        metrics.activity_count = activity_data['activity_count']
        metrics.activity_items = activity_data['activity_items']
        metrics.critical_analysis_activities = activity_data['critical_analysis_activities']
        metrics.reading_activities = activity_data['reading_activities']
        metrics.essay_activities = activity_data['essay_activities']
        if 'error' in activity_data:
            metrics.errors.append(f"Activities parsing error: {activity_data['error']}")

    # Extract from vocabulary
    if metrics.vocabulary_exists:
        vocab_data = analyze_vocabulary(vocab_path)
        metrics.vocab_items = vocab_data['vocab_items']
        metrics.era_vocab_items = vocab_data['era_vocab_items']
        metrics.archaic_vocab_items = vocab_data['archaic_vocab_items']
        if 'error' in vocab_data:
            metrics.errors.append(f"Vocabulary parsing error: {vocab_data['error']}")

    return metrics


def extract_all_module_metrics(
    curriculum_path: Path,
    track_id: str
) -> list[ModuleMetrics]:
    """
    Extract metrics from all modules in a track.

    Args:
        curriculum_path: Path to curriculum directory (e.g., curriculum/l2-uk-en)
        track_id: Track identifier (e.g., "b2-hist")

    Returns:
        List of ModuleMetrics for all modules in the track
    """
    from .config import get_track_config

    config = get_track_config(track_id)
    level_dir = curriculum_path / config['level_dir']

    if not level_dir.exists():
        raise FileNotFoundError(f"Level directory not found: {level_dir}")

    # Find all module slugs
    # Look for status JSON files as source of truth for module list
    status_dir = level_dir / 'status'
    if status_dir.exists():
        module_slugs = [p.stem for p in status_dir.glob("*.json")]
    else:
        # Fallback: find MD files
        md_files = list(level_dir.glob("*.md"))
        module_slugs = [p.stem for p in md_files if not p.name.startswith('_')]

    # Sort by module number if present
    def sort_key(slug):
        match = re.match(r'^(\d+)-', slug)
        if match:
            return int(match.group(1))
        return 999

    module_slugs.sort(key=sort_key)

    # Extract metrics for each module
    metrics_list = []
    for slug in module_slugs:
        metrics = extract_module_metrics(level_dir, slug, track_id)
        metrics_list.append(metrics)

    return metrics_list
