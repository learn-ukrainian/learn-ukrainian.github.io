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


def _detect_level_from_content(content: str) -> str | None:
    """Detect CEFR level from frontmatter."""
    m = re.search(r'^level:\s*(a1|a2|b1|b2|c1|c2)', content, re.MULTILINE | re.IGNORECASE)
    if m:
        return m.group(1).upper()
    # Fallback: check for CEFR level in module field
    m = re.search(r'^module:\s*\w+-(\w\d)', content, re.MULTILINE | re.IGNORECASE)
    if m:
        return m.group(1).upper()
    return None


def _detect_level_from_path(file_path: str) -> str | None:
    """Detect level from file path (e.g. curriculum/l2-uk-en/a1/foo.md → A1).

    A1/A2 modules in this project ship without frontmatter, so the content-based
    detector returns None for them. Without a path-based fallback the
    INLINE_ENGLISH_IN_PROSE check (which should ONLY fire at B1+) leaks into
    A1/A2 and produces false-positive failures on every A1/A2 module that
    follows the prompt's "(English translation)" rule.
    (Caught by Gemini in a1-a2-pre-rebuild-audit, 2026-04-12.)
    """
    if not file_path:
        return None
    path_lower = file_path.lower()
    for lvl in ('a1', 'a2', 'b1', 'b2', 'c1', 'c2'):
        if f'/{lvl}/' in path_lower or f'/{lvl}-' in path_lower:
            return lvl.upper()
    return None


def check_drill_blocks(content: str) -> list[dict]:
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


def check_glossary_lists(content: str) -> list[dict]:
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
                if run_start is not None and run_length >= 3:
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
        if run_start is not None and run_length >= 3:
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


def check_llm_fingerprints(content: str) -> list[dict]:
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


def check_llm_persona_leaks(content: str) -> list[dict]:
    """Detect LLM persona / teacher voice leaking into content.

    Catches patterns like "I am your teacher", "I am so glad you are here",
    "Let me guide you" — where the model role-plays as a character instead
    of writing neutral educational prose.
    """
    violations = []
    zones = _split_narrative_zones(content)
    zone_text = '\n'.join(zones)

    persona_patterns = [
        (r'I am your\b', 'I am your [teacher/guide/...]'),
        (r'I am so glad', 'I am so glad'),
        (r"I['']m so glad", "I'm so glad"),
        (r'I am here to\b', 'I am here to [teach/help/...]'),
        (r"Let me (?:teach|guide|show|help) you", 'Let me teach/guide you'),
        (r'As your (?:teacher|instructor|guide)', 'As your teacher/guide'),
        (r"I['']m your\b", "I'm your [teacher/...]"),
        (r'(?:my|your) dear (?:student|learner)', 'my/your dear student'),
        (r"(?:I|we)['']?(?:ll| will) (?:explore|discover|learn) together", 'we will explore together'),
    ]

    hits = []
    for pattern, label in persona_patterns:
        for m in re.finditer(pattern, zone_text, re.IGNORECASE):
            line_num = _find_line_in_original(content, m.group(0))
            hits.append((label, m.group(0), line_num))

    for _label, matched, line_num in hits:
        violations.append({
            'type': 'LLM_PERSONA_LEAK',
            'severity': 'critical',
            'issue': f"LLM persona leak: '{matched}' — content should not role-play as a teacher/character",
            'fix': "Rewrite in neutral educational voice. Remove first-person teacher persona.",
            'line': line_num,
        })

    return violations


def check_inline_english(content: str, level: str | None = None) -> list[dict]:
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


def _normalize_opener(text: str) -> str:
    """Normalize a section opener for lexical overlap comparison.

    Strips markdown formatting, numbers, punctuation, and lowercases.
    """
    # Remove markdown bold/italic
    text = re.sub(r'[*_]+', '', text)
    # Remove leading #
    text = re.sub(r'^#+\s*', '', text)
    # Remove numbers and punctuation (keep letters and spaces)
    text = re.sub(r'[^\w\s]', '', text)
    # Collapse whitespace and lowercase
    return ' '.join(text.lower().split())


def _lexical_overlap(a: str, b: str) -> float:
    """Compute word-level Jaccard similarity between two strings."""
    words_a = set(a.split())
    words_b = set(b.split())
    if not words_a or not words_b:
        return 0.0
    intersection = words_a & words_b
    union = words_a | words_b
    return len(intersection) / len(union)


def check_structural_monotony(content: str, max_similar: int = 3) -> list[dict]:
    """Detect monotonous section openers — H2/H3 sections starting the same way.

    Counts section openers (first non-empty line after header) sharing >70%
    lexical overlap. Auto-fails if more than `max_similar` sections match.

    This catches the pattern where an LLM generates "The letter X is..." for
    every subsection — a structural monotony issue that was previously only
    detected by subjective LLM scoring in Phase D reviews.
    """
    violations = []

    # Extract H2 and H3 section openers
    lines = content.split('\n')
    openers: list[tuple[str, str, int]] = []  # (header, opener_text, line_num)

    i = 0
    while i < len(lines):
        line = lines[i]
        if re.match(r'^#{2,3}\s+\S', line):
            header = line.strip()
            # Find first non-empty, non-header line after this header
            j = i + 1
            while j < len(lines):
                next_line = lines[j].strip()
                if next_line and not next_line.startswith('#') and not next_line.startswith('<!--'):
                    openers.append((header, next_line, j + 1))
                    break
                j += 1
        i += 1

    if len(openers) < 4:
        return violations

    # Normalize openers
    normalized = [(hdr, _normalize_opener(opener), opener, ln) for hdr, opener, ln in openers]

    # Find groups of similar openers (>70% lexical overlap)
    # Use a simple clustering: for each pair, check overlap
    n = len(normalized)
    similar_groups: list[list[int]] = []
    assigned = set()

    for i in range(n):
        if i in assigned:
            continue
        group = [i]
        for j in range(i + 1, n):
            if j in assigned:
                continue
            if _lexical_overlap(normalized[i][1], normalized[j][1]) > 0.70:
                group.append(j)
        if len(group) > max_similar:
            similar_groups.append(group)
            assigned.update(group)

    for group in similar_groups:
        sample_openers = [normalized[idx][2][:60] for idx in group[:3]]
        sample_headers = [normalized[idx][0][:40] for idx in group[:3]]
        first_line = normalized[group[0]][3]
        violations.append({
            'type': 'STRUCTURAL_MONOTONY',
            'severity': 'critical',
            'issue': (
                f"{len(group)} of {n} section openers share >70% lexical overlap. "
                f"Sections: {'; '.join(sample_headers)}... "
                f"Opener pattern: \"{sample_openers[0]}...\""
            ),
            'fix': (
                "Diversify section openings. Each section should start with a "
                "unique approach: questions, examples, cultural hooks, direct "
                "instruction, comparisons — not the same template."
            ),
            'line': first_line,
        })

    return violations


def check_prose_quality(
    content: str,
    yaml_content: dict | None = None,
    file_path: str = '',
) -> list[dict]:
    """Main entry point for prose quality checks.

    Args:
        content: The markdown content of the module
        yaml_content: Optional dict (unused, kept for API consistency with content_purity)
        file_path: Optional path to the source file. Used as a fallback for level
            detection when the markdown has no frontmatter (which is the case for
            every A1/A2 module in this project — without it the
            INLINE_ENGLISH_IN_PROSE check leaks into A1/A2 and false-positive-fails
            modules that follow the prompt's "(English translation)" rule).

    Returns:
        List of violation dicts with type, severity, issue, fix, line keys
    """
    violations = []

    # Detect level for English-in-prose check.
    # A1/A2 modules ship without frontmatter, so the content-based detector
    # returns None and we fall back to the path-based detector.
    level = _detect_level_from_content(content) or _detect_level_from_path(file_path)

    violations.extend(check_drill_blocks(content))
    violations.extend(check_glossary_lists(content))
    violations.extend(check_llm_fingerprints(content))
    violations.extend(check_llm_persona_leaks(content))
    violations.extend(check_inline_english(content, level))
    violations.extend(check_structural_monotony(content))

    return violations
