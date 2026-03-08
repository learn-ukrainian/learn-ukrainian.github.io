"""
Content Gaming Detection

Deterministic checks that catch LLM content-generation gaming patterns:
1. Cross-module plagiarism (recycled sentences across modules)
2. Content-vocabulary alignment (vocab words missing from prose+activities)
3. Example pattern detection (template-identical example runs)
4. Filler phrase density (LLM hedging/padding phrases)
5. Section depth check (header padding with no real content)
6. Section balance (no single H2 section >40% of word count)
7. IPA density cap (inline IPA tokens <5% of word count)

All checks return list[dict] with 'type', 'severity', 'issue', 'fix' keys.
No LLM calls — pure regex/hashing.

Issue: #610
"""

import contextlib
import hashlib
import json
import os
import re
import tempfile
from pathlib import Path

from .cross_file_integrity import (
    extract_ukrainian_words,
    extract_words_from_activities,
    load_module_vocabulary,
    smart_vocabulary_match,
)

# Reuse existing infrastructure
from .prose_quality import _split_narrative_zones

# =============================================================================
# CHECK 4: FILLER PHRASE DENSITY
# =============================================================================

# Ukrainian LLM fillers — hedging/padding phrases that add no content
_UKRAINIAN_FILLERS = [
    r'Варто зазначити',
    r'Як ми бачимо',
    r'Цікаво,?\s+що',
    r'Важливо зрозуміти',
    r'Слід зауважити',
    r'Необхідно підкреслити',
    r'Звернімо увагу',
    r'Не менш важливо',
    r'Варто звернути увагу',
    r'Як було зазначено',
    r'Слід підкреслити',
    r'Важливо відзначити',
]

# English LLM fillers
_ENGLISH_FILLERS = [
    r'It is important to note',
    r'As we can see',
    r'It should be mentioned',
    r'It is worth noting',
    r'As mentioned earlier',
    r'Let us consider',
    r'It goes without saying',
    r'It bears mentioning',
    r'One should note',
    r'It is noteworthy that',
]

# Pre-compile all filler patterns (case-insensitive)
_FILLER_PATTERNS = [
    re.compile(p, re.IGNORECASE) for p in _UKRAINIAN_FILLERS + _ENGLISH_FILLERS
]

# Levels where academic discourse markers are natural (higher thresholds)
_ACADEMIC_LEVELS = {'C1', 'C2'}


def _detect_level(content: str) -> str | None:
    """Detect CEFR level from frontmatter or path hints."""
    m = re.search(r'^level:\s*(a1|a2|b1|b2|c1|c2)', content, re.MULTILINE | re.IGNORECASE)
    if m:
        return m.group(1).upper()
    return None


def _detect_level_from_path(file_path: str) -> str | None:
    """Detect level from file path."""
    path_lower = file_path.lower()
    for lvl in ['a1', 'a2', 'b1', 'b2', 'c1', 'c2']:
        if f'/{lvl}/' in path_lower or f'/{lvl}-' in path_lower:
            return lvl.upper()
    return None


def check_filler_phrases(content: str, file_path: str = '') -> list[dict]:
    """
    Detect LLM filler/hedging phrases that pad word count without adding content.

    Does NOT overlap with naturalness.py (LLM-based) or prose_quality.py
    (which checks different patterns like 'не просто X, а Y').

    Level-aware thresholds: C1/C2 academic tracks get higher limits since
    discourse markers like "Варто зазначити" are natural in academic writing.

    Threshold: >5 (>8 for C1+) = warning; >10 (>15 for C1+) = critical.
    """
    violations = []

    # Detect level for threshold calibration
    level = _detect_level(content) or _detect_level_from_path(file_path)
    is_academic = level in _ACADEMIC_LEVELS

    # Higher thresholds for academic levels
    warn_threshold = 8 if is_academic else 5
    crit_threshold = 15 if is_academic else 10

    # Only check narrative zones (not activities/vocab sections)
    narrative_zones = _split_narrative_zones(content)
    narrative_text = '\n'.join(narrative_zones)

    total_count = 0
    found_fillers = []

    for pattern in _FILLER_PATTERNS:
        matches = pattern.findall(narrative_text)
        if matches:
            total_count += len(matches)
            found_fillers.append(f"'{matches[0]}' x{len(matches)}")

    if total_count > crit_threshold:
        violations.append({
            'type': 'FILLER_PHRASE_OVERUSE',
            'severity': 'critical',
            'issue': f"Found {total_count} filler phrases in content: {', '.join(found_fillers[:5])}",
            'fix': (
                "Remove or replace filler phrases with substantive content. "
                "Each removed phrase should be replaced with a specific example, "
                "explanation, or cultural context — not another hedge."
            ),
        })
    elif total_count > warn_threshold:
        violations.append({
            'type': 'FILLER_PHRASE_OVERUSE',
            'severity': 'warning',
            'issue': f"Found {total_count} filler phrases in content: {', '.join(found_fillers[:5])}",
            'fix': (
                "Reduce filler phrases. Replace with specific examples or explanations."
            ),
        })

    return violations


# =============================================================================
# CHECK 5: SECTION DEPTH CHECK
# =============================================================================

# Standard structural headers that are naturally short
_STRUCTURAL_HEADERS = {
    'підсумок', 'висновок', 'висновки', 'summary', 'conclusion',
    'вступ', 'introduction',
}


def check_section_depth(content: str, file_path: str = '') -> list[dict]:
    """
    Flag H2 sections with insufficient word count (header padding).

    Sections created to satisfy outline compliance but with no real content.
    Excludes standard structural headers (Підсумок, Висновок, Вступ) from
    the shallow count since they are naturally shorter.

    Threshold varies by level:
    - A1-A2: <50 words per section = warning
    - B1+:   <100 words per section = warning
    - 3+ shallow sections = critical (5+ for B1+ to avoid over-triggering)
    """
    violations = []

    # Detect level
    level = _detect_level(content) or _detect_level_from_path(file_path)

    min_words = 50 if level in ('A1', 'A2') else 100
    crit_count = 3 if level in ('A1', 'A2') else 5

    # Get narrative zones only
    narrative_zones = _split_narrative_zones(content)
    narrative_text = '\n'.join(narrative_zones)

    # Split into H2 sections
    sections = re.split(r'^## ', narrative_text, flags=re.MULTILINE)
    shallow_sections = []

    for section in sections[1:]:  # Skip content before first H2
        lines = section.strip().split('\n')
        if not lines:
            continue

        header = lines[0].strip()

        # Skip structural headers that are naturally short
        header_first_word = header.split(':')[0].strip().lower()
        if header_first_word in _STRUCTURAL_HEADERS:
            continue

        body = '\n'.join(lines[1:])
        word_count = len(body.split())

        if word_count < min_words:
            shallow_sections.append((header, word_count))

    if len(shallow_sections) >= crit_count:
        section_list = '; '.join(
            f"'{h}' ({w}w)" for h, w in shallow_sections[:5]
        )
        violations.append({
            'type': 'SECTION_HEADER_PADDING',
            'severity': 'critical',
            'issue': f"{len(shallow_sections)} shallow sections (< {min_words} words each): {section_list}",
            'fix': (
                f"Expand each shallow section to at least {min_words} words with substantive content. "
                "Add examples, cultural context, usage notes, or practice patterns. "
                "If a section truly has nothing to say, merge it with an adjacent section."
            ),
        })
    elif shallow_sections:
        section_list = '; '.join(
            f"'{h}' ({w}w)" for h, w in shallow_sections
        )
        violations.append({
            'type': 'SECTION_HEADER_PADDING',
            'severity': 'warning',
            'issue': f"{len(shallow_sections)} shallow section(s) (< {min_words} words): {section_list}",
            'fix': f"Expand shallow sections to at least {min_words} words with substantive content.",
        })

    return violations


# =============================================================================
# CHECK 6: SECTION BALANCE (MAX %)
# =============================================================================

def check_section_balance(content: str, file_path: str = '') -> list[dict]:
    """
    Flag H2 sections that exceed 40% of total module word count.

    A bloated section means other sections are shallow by comparison.
    Skips modules with <3 H2 sections (too few to judge balance).

    Threshold: >40% = warning; >60% = critical.
    """
    violations = []

    # Get narrative zones only
    narrative_zones = _split_narrative_zones(content)
    narrative_text = '\n'.join(narrative_zones)

    # Split into H2 sections
    sections = re.split(r'^## ', narrative_text, flags=re.MULTILINE)
    section_data = []

    for section in sections[1:]:  # Skip content before first H2
        lines = section.strip().split('\n')
        if not lines:
            continue
        header = lines[0].strip()
        body = '\n'.join(lines[1:])
        word_count = len(body.split())
        section_data.append((header, word_count))

    # Skip if <3 H2 sections
    if len(section_data) < 3:
        return []

    total_words = sum(wc for _, wc in section_data)
    if total_words == 0:
        return []

    bloated = []
    for header, wc in section_data:
        proportion = wc / total_words
        if proportion > 0.40:
            bloated.append((header, wc, proportion))

    if not bloated:
        return []

    worst_header, worst_wc, worst_pct = max(bloated, key=lambda x: x[2])

    if worst_pct > 0.60:
        section_list = '; '.join(
            f"'{h}' ({p:.0%})" for h, _, p in bloated
        )
        violations.append({
            'type': 'SECTION_BALANCE_BLOATED',
            'severity': 'critical',
            'issue': (
                f"Section '{worst_header}' has {worst_wc} words ({worst_pct:.0%} of total). "
                f"Bloated sections: {section_list}"
            ),
            'fix': (
                "Redistribute content more evenly across sections. "
                "Move subtopics from the bloated section into their own H2 sections, "
                "or expand the thinner sections with more examples and context."
            ),
        })
    else:
        section_list = '; '.join(
            f"'{h}' ({p:.0%})" for h, _, p in bloated
        )
        violations.append({
            'type': 'SECTION_BALANCE_BLOATED',
            'severity': 'warning',
            'issue': (
                f"Section '{worst_header}' has {worst_wc} words ({worst_pct:.0%} of total). "
                f"Bloated sections: {section_list}"
            ),
            'fix': (
                "Consider splitting the large section or expanding smaller sections "
                "to improve balance."
            ),
        })

    return violations


def check_ipa_density(content: str, file_path: str = '') -> list[dict]:
    """IPA removed from curriculum. This check is now a no-op."""
    return []


# =============================================================================
# CHECK 2: CONTENT-VOCABULARY ALIGNMENT
# =============================================================================

def check_content_vocab_alignment(content: str, file_path: str) -> list[dict]:
    """
    Verify that vocabulary YAML words actually appear in content or activities.

    Catches authors who add fancy words to YAML but forget to use them.
    Uses smart_vocabulary_match() for fuzzy matching (handles inflections).
    Multi-word terms use smart_vocabulary_match on each word individually
    to handle Ukrainian inflections (e.g. "золота доба" → "золотої доби").

    Threshold: <50% = critical; <70% = warning.
    """
    violations = []
    md_path = Path(file_path)

    # Load vocabulary
    vocab = load_module_vocabulary(md_path)
    if not vocab or len(vocab) < 3:
        return []  # No vocab file or too few entries to check

    # Extract words from content AND activities
    content_words = extract_ukrainian_words(content)
    activity_words = extract_words_from_activities(md_path)
    all_used_words = content_words | activity_words

    # Check each vocab word against used words
    found = 0
    missing = []

    for lemma in vocab:
        # Multi-word terms: check if each word in the phrase matches
        # something in the content (handles inflected forms)
        if ' ' in lemma:
            phrase_words = [w for w in lemma.lower().split() if len(w) > 2]
            if phrase_words:
                all_matched = all(
                    smart_vocabulary_match(pw, all_used_words)[0]
                    for pw in phrase_words
                )
                if all_matched:
                    found += 1
                else:
                    missing.append(lemma)
            else:
                found += 1  # Very short phrase, skip
            continue

        matched, _ = smart_vocabulary_match(lemma, all_used_words)
        if matched:
            found += 1
        else:
            missing.append(lemma)

    total = len(vocab)
    coverage = found / total if total > 0 else 1.0

    if coverage < 0.50:
        violations.append({
            'type': 'VOCAB_NOT_IN_CONTENT',
            'severity': 'critical',
            'issue': (
                f"Only {found}/{total} ({coverage:.0%}) vocabulary words appear in content+activities. "
                f"Missing: {', '.join(sorted(missing)[:10])}"
                + (f" (+{len(missing) - 10} more)" if len(missing) > 10 else "")
            ),
            'fix': (
                "Vocabulary words MUST appear in the module content or activities. "
                "Either use these words in the prose/examples, add activities that practice them, "
                "or remove them from the vocabulary YAML if they don't belong in this module."
            ),
        })
    elif coverage < 0.70:
        violations.append({
            'type': 'VOCAB_NOT_IN_CONTENT',
            'severity': 'warning',
            'issue': (
                f"Only {found}/{total} ({coverage:.0%}) vocabulary words appear in content+activities. "
                f"Missing: {', '.join(sorted(missing)[:8])}"
                + (f" (+{len(missing) - 8} more)" if len(missing) > 8 else "")
            ),
            'fix': (
                "Integrate missing vocabulary words into the prose or activities. "
                "Each vocab word should appear at least once in context."
            ),
        })

    return violations


# =============================================================================
# CHECK 3: EXAMPLE PATTERN DETECTION
# =============================================================================

def _tokenize_ukrainian(text: str) -> set[str]:
    """Extract Ukrainian word tokens from text, including single-char words."""
    # Include single-character Ukrainian words (я, в, у, з, й, і, а)
    # and smart apostrophe (') alongside standard ʼ
    return set(re.findall(r"[а-яіїєґА-ЯІЇЄҐ][а-яіїєґА-ЯІЇЄҐ'ʼ'-]*", text.lower()))


def check_example_diversity(content: str, file_path: str = '') -> list[dict]:
    """
    Detect runs of template-identical examples (same structure, 1-2 words differ).

    Skip A1-A2: repetitive patterns ARE pedagogy at beginner levels
    (verb conjugation drills like "Я бачу книгу" / "Ти бачиш книгу").

    Threshold: 3+ same-template run = warning (B1+); 5+ = critical.
    """
    violations = []

    # Detect level — skip A1/A2
    level = _detect_level(content) or _detect_level_from_path(file_path)

    if level in ('A1', 'A2'):
        return []

    # Get narrative zones
    narrative_zones = _split_narrative_zones(content)
    narrative_text = '\n'.join(narrative_zones)

    # Extract example sentences: lines starting with -, *, or numbered that contain Cyrillic
    example_pattern = re.compile(
        r'^[\s]*[-*]\s+(.+)|^[\s]*\d+\.\s+(.+)', re.MULTILINE
    )
    examples = []
    for m in example_pattern.finditer(narrative_text):
        text = m.group(1) or m.group(2)
        if text and re.search(r'[а-яіїєґ]', text):
            examples.append(text.strip())

    if len(examples) < 3:
        return []

    # Find runs of template-identical examples
    # Two examples are "template-identical" if they share >70% of words
    max_run = 0
    current_run = 1
    longest_run_start = 0

    for i in range(1, len(examples)):
        tokens_prev = _tokenize_ukrainian(examples[i - 1])
        tokens_curr = _tokenize_ukrainian(examples[i])

        if not tokens_prev or not tokens_curr:
            current_run = 1
            continue

        # Calculate overlap
        overlap = len(tokens_prev & tokens_curr)
        total = max(len(tokens_prev), len(tokens_curr))
        similarity = overlap / total if total > 0 else 0

        if similarity > 0.70:
            current_run += 1
        else:
            current_run = 1

        if current_run > max_run:
            max_run = current_run
            longest_run_start = i - current_run + 1

    if max_run >= 5:
        sample = examples[longest_run_start:longest_run_start + 3]
        sample_str = ' | '.join(sample)
        violations.append({
            'type': 'TEMPLATE_EXAMPLE_RUN',
            'severity': 'critical',
            'issue': (
                f"Found run of {max_run} template-identical examples "
                f"(>70% word overlap). Sample: {sample_str}"
            ),
            'fix': (
                "Diversify examples. Each example should demonstrate a different "
                "vocabulary context, sentence structure, or semantic scenario — "
                "not just swap one word in a template."
            ),
        })
    elif max_run >= 3:
        sample = examples[longest_run_start:longest_run_start + 3]
        sample_str = ' | '.join(sample)
        violations.append({
            'type': 'TEMPLATE_EXAMPLE_RUN',
            'severity': 'warning',
            'issue': (
                f"Found run of {max_run} template-identical examples "
                f"(>70% word overlap). Sample: {sample_str}"
            ),
            'fix': "Vary example structures. Avoid changing only 1-2 words per example.",
        })

    return violations


# =============================================================================
# CHECK 1: CROSS-MODULE PLAGIARISM
# =============================================================================

def _normalize_sentence(s: str) -> str:
    """Normalize a sentence for comparison: lowercase, strip, collapse whitespace."""
    return re.sub(r'\s+', ' ', s.lower().strip())


def _hash_sentence(s: str) -> str:
    """Hash a normalized sentence."""
    return hashlib.md5(s.encode('utf-8')).hexdigest()


def _is_header_line(line: str) -> bool:
    """Check if a line is a markdown header."""
    return bool(re.match(r'^#{1,6}\s', line.strip()))


# Common Ukrainian abbreviations that shouldn't split sentences
_ABBREV_PATTERN = re.compile(
    r'\b(т|напр|м|ст|рр?|пор|див|ін|проф|акад|вул|обл)\.\s',
    re.IGNORECASE,
)


def _split_sentences(text: str) -> list[str]:
    """Split text into sentences, filtering out headers and short lines.

    Handles Ukrainian abbreviations (т. д., напр., м. Київ) by temporarily
    replacing their periods to prevent false sentence splits.
    """
    # Protect abbreviation periods from splitting
    protected = _ABBREV_PATTERN.sub(lambda m: m.group(1) + '.\u200B', text)

    # Split on sentence-ending punctuation
    raw = re.split(r'(?<=[.!?])\s+', protected)
    sentences = []
    for s in raw:
        # Restore protected periods
        s = s.replace('\u200B', '').strip()
        # Skip headers, short sentences (<10 words), and empty
        if not s or _is_header_line(s):
            continue
        words = s.split()
        if len(words) > 10:
            sentences.append(s)
    return sentences


def _get_sentence_hashes_cache_path(track_dir: Path) -> Path:
    """Get path for sentence hash cache."""
    audit_dir = track_dir / 'audit'
    audit_dir.mkdir(exist_ok=True)
    return audit_dir / 'sentence_hashes.json'


def _load_sentence_cache(cache_path: Path) -> dict:
    """Load cached sentence hashes. Returns {filename: {mtime, hashes}}."""
    if cache_path.exists():
        try:
            with open(cache_path, encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def _save_sentence_cache(cache_path: Path, cache: dict):
    """Save sentence hash cache atomically to prevent corruption from parallel workers."""
    try:
        # Write to temp file, then atomic rename
        fd, tmp_path = tempfile.mkstemp(
            dir=cache_path.parent, suffix='.tmp', prefix='sentence_hashes_'
        )
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                json.dump(cache, f, indent=2)
            os.replace(tmp_path, cache_path)
        except Exception:
            # Clean up temp file on failure
            with contextlib.suppress(OSError):
                os.unlink(tmp_path)
    except OSError:
        pass


def _get_file_hashes(md_path: Path, cache: dict) -> list[str]:
    """
    Get sentence hashes for a file, using cache if file hasn't changed.
    Returns list of sentence hashes.
    """
    filename = md_path.name
    mtime = os.path.getmtime(md_path)

    # Check cache
    if filename in cache:
        cached = cache[filename]
        if cached.get('mtime') == mtime:
            return cached.get('hashes', [])

    # Recompute
    try:
        content = md_path.read_text(encoding='utf-8')
    except OSError:
        return []

    narrative_zones = _split_narrative_zones(content)
    narrative_text = '\n'.join(narrative_zones)
    sentences = _split_sentences(narrative_text)

    hashes = [_hash_sentence(_normalize_sentence(s)) for s in sentences]

    # Update cache
    cache[filename] = {'mtime': mtime, 'hashes': hashes}

    return hashes


def check_cross_module_plagiarism(content: str, file_path: str) -> list[dict]:
    """
    Detect sentences copied verbatim between modules in the same track.

    Extracts sentences (split on .!?), normalizes and hashes them,
    then compares against all other .md files in the same track directory.

    Only flags sentences >10 words (short transitional sentences are legitimately shared).
    For tracks with >50 modules, uses mtime-based caching with atomic writes.

    Threshold: >3 duplicated sentences = warning; >8 = critical.
    """
    violations = []
    md_path = Path(file_path)
    track_dir = md_path.parent

    # Get all .md files in the same directory (same track)
    all_md_files = sorted(track_dir.glob('*.md'))
    if len(all_md_files) < 2:
        return []  # Nothing to compare against

    # Use caching for large tracks
    use_cache = len(all_md_files) > 50
    cache = {}
    cache_path = None

    if use_cache:
        cache_path = _get_sentence_hashes_cache_path(track_dir)
        cache = _load_sentence_cache(cache_path)

    # Get hashes for current module
    narrative_zones = _split_narrative_zones(content)
    narrative_text = '\n'.join(narrative_zones)
    current_sentences = _split_sentences(narrative_text)
    current_hashes = {
        _hash_sentence(_normalize_sentence(s)): s
        for s in current_sentences
    }

    # Cache the current module's hashes too (Gemini review fix: was missing)
    if use_cache:
        cache[md_path.name] = {
            'mtime': os.path.getmtime(md_path),
            'hashes': list(current_hashes.keys()),
        }

    # Compare against all other modules
    duplicated_sentences = []

    for other_md in all_md_files:
        if other_md.name == md_path.name:
            continue

        other_hashes = _get_file_hashes(other_md, cache)
        other_hash_set = set(other_hashes)

        for h, sentence in current_hashes.items():
            if h in other_hash_set:
                duplicated_sentences.append((sentence, other_md.name))

    # Save cache if we used it
    if use_cache and cache_path:
        _save_sentence_cache(cache_path, cache)

    # Deduplicate (same sentence might match multiple files)
    unique_duplicates = {}
    for sentence, source in duplicated_sentences:
        h = _hash_sentence(_normalize_sentence(sentence))
        if h not in unique_duplicates:
            unique_duplicates[h] = (sentence, [])
        unique_duplicates[h][1].append(source)

    dup_count = len(unique_duplicates)

    if dup_count > 8:
        samples = list(unique_duplicates.values())[:3]
        sample_str = '; '.join(
            f"'{s[:60]}...' (also in {', '.join(files[:2])})"
            for s, files in samples
        )
        violations.append({
            'type': 'CROSS_MODULE_PLAGIARISM',
            'severity': 'critical',
            'issue': f"{dup_count} sentences duplicated from other modules. Samples: {sample_str}",
            'fix': (
                "Rewrite duplicated sentences. Each module must have original prose. "
                "Shared concepts should be explained differently in each module — "
                "same information, different wording and examples."
            ),
        })
    elif dup_count > 3:
        samples = list(unique_duplicates.values())[:3]
        sample_str = '; '.join(
            f"'{s[:60]}...' (also in {', '.join(files[:2])})"
            for s, files in samples
        )
        violations.append({
            'type': 'CROSS_MODULE_PLAGIARISM',
            'severity': 'warning',
            'issue': f"{dup_count} sentences duplicated from other modules. Samples: {sample_str}",
            'fix': "Rephrase duplicated sentences to be unique to this module.",
        })

    return violations


# =============================================================================
# PUBLIC ENTRY POINT
# =============================================================================

def check_content_gaming(content: str, file_path: str) -> list[dict]:
    """
    Run all content gaming detection checks.

    Returns combined list of violations from all sub-checks.
    """
    violations = []

    # Check 4: Filler phrases (fast — regex only)
    violations.extend(check_filler_phrases(content, file_path))

    # Check 5: Section depth (fast — word counting)
    violations.extend(check_section_depth(content, file_path))

    # Check 6: Section balance — max % (fast — word counting)
    violations.extend(check_section_balance(content, file_path))

    # Check 7: IPA density cap (fast — regex counting)
    violations.extend(check_ipa_density(content, file_path))

    # Check 2: Content-vocabulary alignment
    violations.extend(check_content_vocab_alignment(content, file_path))

    # Check 3: Example diversity (skip A1-A2)
    violations.extend(check_example_diversity(content, file_path))

    # Check 1: Cross-module plagiarism (slowest — reads other files)
    violations.extend(check_cross_module_plagiarism(content, file_path))

    return violations
