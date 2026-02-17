"""
Prose Quality Checker

Detects structural problems in narrative prose that survive audit
but produce terrible reading quality:
- Drill blocks (_Приклади:_) embedded in prose instead of activities
- Glossary-style definition lists in narrative sections
- Repetitive LLM fingerprint rhetorical patterns
- Inline English translations in B1+ immersion content
"""

import re
from typing import List, Dict, Optional


def _split_narrative_zones(content: str) -> list[str]:
    """Extract only narrative (non-activity) zones from content.

    Strips:
    - Activity blocks between <!-- activity-start --> / <!-- activity-end -->
    - YAML frontmatter
    - Vocabulary sections (## Словник / ## Vocabulary)
    - Bibliography sections (## Бібліографія / ## Джерела)
    """
    # Strip frontmatter
    text = re.sub(r'^---.*?---\n', '', content, flags=re.DOTALL)

    # Remove activity blocks
    text = re.sub(
        r'<!--\s*activity-start\s*-->.*?<!--\s*activity-end\s*-->',
        '', text, flags=re.DOTALL
    )

    # Remove vocabulary sections (## Словник through next ## or EOF)
    text = re.sub(
        r'^##\s+(Словник|Vocabulary|Лексика).*?(?=^##\s|\Z)',
        '', text, flags=re.MULTILINE | re.DOTALL
    )

    # Remove bibliography sections
    text = re.sub(
        r'^##\s+(Бібліографія|Джерела|Література|Використані джерела).*?(?=^##\s|\Z)',
        '', text, flags=re.MULTILINE | re.DOTALL
    )

    # Remove self-assessment sections
    text = re.sub(
        r'^##\s+(Самооцінювання|Self-Assessment|Самоперевірка).*?(?=^##\s|\Z)',
        '', text, flags=re.MULTILINE | re.DOTALL
    )

    return [text]


def _detect_level_from_content(content: str) -> Optional[str]:
    """Detect CEFR level from frontmatter."""
    m = re.search(r'^level:\s*(a1|a2|b1|b2|c1|c2)', content, re.MULTILINE | re.IGNORECASE)
    if m:
        return m.group(1).upper()
    # Fallback: check for CEFR level in module field
    m = re.search(r'^module:\s*\w+-(\w\d)', content, re.MULTILINE | re.IGNORECASE)
    if m:
        return m.group(1).upper()
    return None


def check_drill_blocks(content: str) -> List[Dict]:
    """Detect _Приклади:_ / _Приклад:_ drill blocks in narrative prose.

    Drill blocks belong in activity YAML, not in narrative sections.
    Pattern: _Приклад(и):_ followed within 3 lines by numbered or bulleted list.
    """
    violations = []
    zones = _split_narrative_zones(content)

    for zone in zones:
        lines = zone.split('\n')
        for i, line in enumerate(lines):
            # Match _Приклад:_ or _Приклади:_ (italic markers)
            if re.search(r'_Приклад[и]?:_', line):
                # Check if followed within 3 lines by numbered/bulleted list
                lookahead = lines[i+1:i+4]
                has_list = any(
                    re.match(r'\s*(\d+[.)]\s|[-*]\s)', la)
                    for la in lookahead
                )
                if has_list:
                    # Find approximate line in original content
                    orig_line = _find_line_in_original(content, line.strip())
                    violations.append({
                        'type': 'DRILL_BLOCK_IN_PROSE',
                        'severity': 'critical',
                        'issue': f"Drill block in narrative prose: '{line.strip()[:80]}' — drills belong in activities YAML, not inline",
                        'fix': "Move example drill to activities/ YAML file or rewrite as flowing narrative with examples woven into paragraphs",
                        'line': orig_line,
                    })

    return violations


def check_glossary_lists(content: str) -> List[Dict]:
    """Detect glossary-style definition lists in narrative sections.

    Pattern: 3+ consecutive lines matching **word** — definition
    These belong in vocabulary YAML, not inline.
    """
    violations = []
    zones = _split_narrative_zones(content)

    glossary_pattern = re.compile(r'^\s*\*\*[^*]+\*\*\s*[—–-]\s*\S')

    for zone in zones:
        lines = zone.split('\n')
        run_start = None
        run_length = 0

        for i, line in enumerate(lines):
            if glossary_pattern.match(line):
                if run_start is None:
                    run_start = i
                run_length += 1
            else:
                if run_length >= 3:
                    sample = lines[run_start].strip()[:80]
                    orig_line = _find_line_in_original(content, lines[run_start].strip())
                    violations.append({
                        'type': 'GLOSSARY_LIST_IN_PROSE',
                        'severity': 'critical',
                        'issue': f"Glossary-style list ({run_length} items) in narrative prose starting: '{sample}' — vocab tables belong in vocabulary YAML",
                        'fix': "Move vocabulary definitions to vocabulary/{slug}.yaml or rewrite as natural prose with words introduced in context",
                        'line': orig_line,
                    })
                run_start = None
                run_length = 0

        # Check trailing run
        if run_length >= 3:
            sample = lines[run_start].strip()[:80]
            orig_line = _find_line_in_original(content, lines[run_start].strip())
            violations.append({
                'type': 'GLOSSARY_LIST_IN_PROSE',
                'severity': 'critical',
                'issue': f"Glossary-style list ({run_length} items) in narrative prose starting: '{sample}' — vocab tables belong in vocabulary YAML",
                'fix': "Move vocabulary definitions to vocabulary/{slug}.yaml or rewrite as natural prose with words introduced in context",
                'line': orig_line,
            })

    return violations


def check_llm_fingerprints(content: str) -> List[Dict]:
    """Detect repetitive LLM fingerprint rhetorical patterns.

    Flags when formulaic patterns appear 4+ times — a sign of
    robotic, template-driven generation.
    """
    violations = []
    zones = _split_narrative_zones(content)
    zone_text = '\n'.join(zones)

    fingerprint_patterns = [
        (r'не\s+просто', 'не просто X, а Y'),
        (r'це\s+не\s+бул[оиа]', 'це не було/були/була'),
        (r'це\s+не\s+лише', 'це не лише'),
        (r'не\s+лише\s+[^,]+,\s*(а\s+й|але\s+й)', 'не лише X, а й Y'),
    ]

    total_hits = 0
    hit_details = []

    for pattern, label in fingerprint_patterns:
        matches = re.findall(pattern, zone_text, re.IGNORECASE)
        count = len(matches)
        if count >= 2:
            hit_details.append(f"'{label}' x{count}")
            total_hits += count

    if total_hits >= 4:
        violations.append({
            'type': 'LLM_FINGERPRINT_REPETITION',
            'severity': 'warning',
            'issue': f"Repetitive LLM rhetorical patterns ({total_hits} total): {', '.join(hit_details)} — robotic prose",
            'fix': "Vary sentence structures. Replace formulaic 'не просто X, а Y' with diverse rhetorical devices",
            'line': 0,
        })

    return violations


def check_inline_english(content: str, level: Optional[str] = None) -> List[Dict]:
    """Detect inline English translations in B1+ content.

    B1+ immersion target is 85%+; inline English like (English translation)
    breaks immersion. Only flags in narrative prose, not vocab sections.
    """
    # Only check B1+ content (B1 modules 6+ should not have inline English)
    if level and level.upper() in ('A1', 'A2'):
        return []

    violations = []
    zones = _split_narrative_zones(content)

    # Pattern: (English words) — 2+ English words in parentheses
    # Must start with capital letter to distinguish from Ukrainian abbreviations
    english_paren_pattern = re.compile(
        r'\(([A-Z][a-z]+(?:\s+[a-z]+){1,5})\)'
    )

    hit_count = 0
    examples = []

    for zone in zones:
        for match in english_paren_pattern.finditer(zone):
            text = match.group(1)
            # Verify it's actually English (contains only Latin chars)
            if re.match(r'^[A-Za-z\s]+$', text):
                hit_count += 1
                if len(examples) < 3:
                    examples.append(text)

    if hit_count >= 3:
        examples_str = ', '.join(f'({e})' for e in examples)
        violations.append({
            'type': 'INLINE_ENGLISH_IN_PROSE',
            'severity': 'warning',
            'issue': f"Inline English translations in B1+ prose ({hit_count} occurrences): {examples_str} — breaks immersion target",
            'fix': "Remove inline English translations. Use context clues, Ukrainian definitions, or move translations to vocabulary section",
            'line': 0,
        })

    return violations


def _find_line_in_original(content: str, search_text: str) -> int:
    """Find the line number of search_text in the original content."""
    if not search_text:
        return 0
    for i, line in enumerate(content.split('\n'), 1):
        if search_text in line:
            return i
    return 0


def check_prose_quality(content: str, yaml_content: dict | None = None) -> List[Dict]:
    """Main entry point for prose quality checks.

    Args:
        content: The markdown content of the module
        yaml_content: Optional dict (unused, kept for API consistency with content_purity)

    Returns:
        List of violation dicts with type, severity, issue, fix, line keys
    """
    violations = []

    # Detect level for English-in-prose check
    level = _detect_level_from_content(content)

    violations.extend(check_drill_blocks(content))
    violations.extend(check_glossary_lists(content))
    violations.extend(check_llm_fingerprints(content))
    violations.extend(check_inline_english(content, level))

    return violations
