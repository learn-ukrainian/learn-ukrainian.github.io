"""
Vocabulary-related validation checks.

Validates vocabulary section content and checks for words used
but not defined in the vocabulary table.
"""

import re
import sqlite3
from pathlib import Path
from ..config import COMMON_WORDS

# Level ordering for cumulative vocabulary lookup
LEVEL_ORDER = {'A1': 1, 'A2': 2, 'B1': 3, 'B2': 4, 'C1': 5, 'C2': 6}


def get_db_path() -> Path:
    """Get the path to the vocabulary database."""
    return Path(__file__).parent.parent.parent.parent / "curriculum/l2-uk-en/vocabulary.db"


def sync_vocab_to_db(level: str, module_num: int, vocab_items: list[dict], db_path: str = None) -> int:
    """
    Sync vocabulary from a module to the database.

    Called during audit to keep the database in sync with module content.
    Returns the number of new words added.

    Args:
        level: Level code (A1, A2, etc.)
        module_num: Module number within the level
        vocab_items: List of vocabulary items from the module, each with 'uk', 'ipa', 'en' keys
        db_path: Optional path to database
    """
    if db_path is None:
        db_path = get_db_path()

    if not Path(db_path).exists():
        return 0

    added = 0
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        for item in vocab_items:
            uk = item.get('uk', '').strip()
            if not uk:
                continue

            ipa = item.get('ipa', '')
            en = item.get('en', '')
            note = item.get('note', '')

            # Check if it's an expression (multi-word)
            is_expression = ' ' in uk and len(uk.split()) > 1

            if is_expression:
                # Try to insert into expressions table
                cursor.execute("""
                    INSERT OR IGNORE INTO expressions (id, uk, ipa, en, notes, level, first_module)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (f"e-{level}-{module_num}-{uk[:20]}", uk, ipa, en, note, level.upper(), module_num))
            else:
                # Try to insert into lemmas table
                cursor.execute("""
                    INSERT OR IGNORE INTO lemmas (id, uk, ipa, en, notes, level, first_module)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (f"v-{level}-{module_num}-{uk}", uk, ipa, en, note, level.upper(), module_num))

            if cursor.rowcount > 0:
                added += 1

        conn.commit()
        conn.close()
    except Exception as e:
        # Silently fail - don't break audit if DB sync fails
        pass

    return added


def generate_inflections(word: str) -> set[str]:
    """
    Generate common Ukrainian inflected forms from a base word.

    This is a simple heuristic that covers common patterns.
    Not exhaustive, but catches most pedagogical content uses.
    """
    forms = {word}

    # Common noun plural endings
    if word.endswith('а'):
        forms.add(word[:-1] + 'и')  # -а → -и (книга → книги)
        forms.add(word[:-1] + 'у')  # -а → -у (accusative)
        forms.add(word[:-1] + 'ою')  # -а → -ою (instrumental)
        forms.add(word[:-1] + 'і')  # -а → -і (locative)
    elif word.endswith('я'):
        forms.add(word[:-1] + 'і')  # -я → -і (земля → землі)
        forms.add(word[:-1] + 'ю')  # -я → -ю (accusative)
        forms.add(word[:-1] + 'ею')  # -я → -ею (instrumental)
    elif word.endswith('о'):
        forms.add(word[:-1] + 'а')  # -о → -а (вікно → вікна, plural)
        forms.add(word[:-1] + 'і')  # -о → -і (locative)
        forms.add(word[:-1] + 'ом')  # -о → -ом (instrumental)
    elif word.endswith('е'):
        forms.add(word[:-1] + 'я')  # -е → -я (море → моря)
        forms.add(word[:-1] + 'і')  # -е → -і (locative)
        forms.add(word[:-1] + 'ем')  # -е → -ем (instrumental)
    elif not word.endswith(('ь', 'й')):
        # Consonant-ending nouns (masculine)
        forms.add(word + 'а')  # genitive (стіл → стола)
        forms.add(word + 'у')  # dative/locative (стіл → столу)
        forms.add(word + 'ом')  # instrumental (стіл → столом)
        forms.add(word + 'и')  # plural (стіл → столи)
        forms.add(word + 'ів')  # genitive plural
        forms.add(word + 'і')  # locative (стіл → стілі - rare)

        # Handle Ukrainian vowel alternation (і↔о)
        # стіл → столі, пік → покі, etc.
        if 'і' in word:
            alt_stem = word.replace('і', 'о', 1)  # Replace first і with о
            forms.add(alt_stem + 'а')
            forms.add(alt_stem + 'у')
            forms.add(alt_stem + 'ом')
            forms.add(alt_stem + 'и')
            forms.add(alt_stem + 'ів')
            forms.add(alt_stem + 'і')

    # Adjective endings
    if word.endswith('ий'):
        base = word[:-2]
        forms.add(base + 'а')   # feminine
        forms.add(base + 'е')   # neuter
        forms.add(base + 'і')   # plural
        forms.add(base + 'ого')  # genitive
        forms.add(base + 'ому')  # dative

    return forms


def get_cumulative_vocab(level: str, module_num: int, db_path: str = None) -> set[str]:
    """
    Get all vocabulary words introduced up to and including the given module.

    This allows modules to use words from earlier modules without re-declaring them.
    Includes generated inflections to catch common grammatical forms.
    """
    if db_path is None:
        db_path = get_db_path()

    if not Path(db_path).exists():
        return set()

    cumulative = set()
    level_num = LEVEL_ORDER.get(level.upper(), 0)

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Get all words from:
        # 1. All modules in earlier levels (A1 < A2 < B1, etc.)
        # 2. All modules in current level up to and including current module
        base_words = set()
        for lvl, lvl_order in LEVEL_ORDER.items():
            if lvl_order < level_num:
                # All modules from earlier levels
                cursor.execute("SELECT uk FROM lemmas WHERE level = ?", (lvl,))
                for row in cursor.fetchall():
                    base_words.add(row[0].lower())
            elif lvl_order == level_num:
                # Current level: only modules up to current
                cursor.execute(
                    "SELECT uk FROM lemmas WHERE level = ? AND first_module <= ?",
                    (lvl, module_num)
                )
                for row in cursor.fetchall():
                    base_words.add(row[0].lower())

        # Add base words and their inflections
        for word in base_words:
            cumulative.update(generate_inflections(word))

        # Also get expressions
        for lvl, lvl_order in LEVEL_ORDER.items():
            if lvl_order < level_num:
                cursor.execute("SELECT uk FROM expressions WHERE level = ?", (lvl,))
                for row in cursor.fetchall():
                    for word in row[0].lower().split():
                        cumulative.add(word)
            elif lvl_order == level_num:
                cursor.execute(
                    "SELECT uk FROM expressions WHERE level = ? AND first_module <= ?",
                    (lvl, module_num)
                )
                for row in cursor.fetchall():
                    for word in row[0].lower().split():
                        cumulative.add(word)

        conn.close()
    except Exception as e:
        # If database access fails, return empty set (fall back to module-only check)
        pass

    return cumulative


def extract_vocab_items(content: str) -> list[dict]:
    """
    Extract vocabulary items with full metadata from the Vocabulary section.

    Note: Must match level-2 headings (## Vocabulary) not subsections (### Vocabulary Groups).

    Returns list of dicts with keys: uk, ipa, en, note
    """
    items = []
    # Match both # Vocabulary and ## Vocabulary (plus Ukrainian variants)
    # Stop at next H1 or H2 section
    vocab_match = re.search(
        r'^#{1,2}\s+(?:Vocabulary|Словник).*?(?=\n#{1,2}\s|\Z)',
        content, re.DOTALL | re.IGNORECASE | re.MULTILINE
    )
    if vocab_match:
        vocab_text = vocab_match.group(0)
        for line in vocab_text.split('\n'):
            if line.strip().startswith('|') and '---' not in line:
                parts = [p.strip() for p in line.split('|')]
                # Remove empty parts from split
                parts = [p for p in parts if p]

                if len(parts) >= 3:
                    first_col = parts[0]
                    # Skip header row
                    if first_col.lower() in ('word', 'слово', 'дíєслово', 'слово / вираз'):
                        continue

                    # Extract Ukrainian word (first column may have formatting)
                    uk_match = re.search(r'[\u0400-\u04ff][\u0400-\u04ff\s\'\-\!]*', first_col)
                    if not uk_match:
                        continue

                    uk = uk_match.group(0).strip()
                    if len(uk) < 2:
                        continue

                    # Parse other columns based on count
                    # Common formats:
                    # A1: Word | IPA | English | POS | Gender | Note (6 cols)
                    # B2: Слово | Переклад | Примітки (3 cols)
                    ipa = ''
                    en = ''
                    note = ''

                    if len(parts) >= 6:  # Full A1 format
                        ipa = parts[1] if '/' in parts[1] else ''
                        en = parts[2]
                        note = parts[5] if len(parts) > 5 else ''
                    elif len(parts) == 5:  # Tier 3 / B1 format
                        ipa = parts[1] if '/' in parts[1] else ''
                        en = parts[2]
                        note = parts[4]
                    elif len(parts) >= 3:  # Generic/Short format
                        # If 2nd col has slashes, it's likely IPA
                        if '/' in parts[1]:
                            ipa = parts[1]
                            en = parts[2]
                            note = parts[3] if len(parts) > 3 else ''
                        else:
                            en = parts[1]
                            note = parts[2] if len(parts) > 2 else ''

                    items.append({
                        'uk': uk,
                        'ipa': ipa,
                        'en': en,
                        'note': note
                    })
    return items


def extract_vocab_from_section(content: str) -> set[str]:
    """Extract vocabulary words from the Vocabulary section."""
    vocab_words = set()
    items = extract_vocab_items(content)
    for item in items:
        uk = item['uk'].lower()
        # Add the word and any sub-words (for compound entries)
        for word in re.findall(r"[\u0400-\u04ff\'\u2019\u02bc]+", uk):
            if len(word) >= 2:
                vocab_words.add(word)
    return vocab_words


def check_vocab_violations(
    content: str,
    core_content: str,
    vocab_words: set[str],
    cumulative_vocab: set[str] = None
) -> list[dict]:
    """Check if Ukrainian words in core content are in the vocabulary section.

    Args:
        content: Full module content
        core_content: Core instructional content (excluding activities)
        vocab_words: Words from the current module's vocabulary section
        cumulative_vocab: Words from previous modules (from vocabulary database)
    """
    violations = []
    if not vocab_words:
        return violations

    if cumulative_vocab is None:
        cumulative_vocab = set()

    # Extract all Ukrainian words from core content (including apostrophes)
    core_words = set(re.findall(r"[\u0400-\u04ff\'\u2019\u02bc]+", core_content.lower()))

    # Find words not in vocab, not common, and not from previous modules
    unknown_words = core_words - vocab_words - COMMON_WORDS - cumulative_vocab

    # Filter to words that appear multiple times (likely intentional)
    word_counts = {}
    for word in re.findall(r'[\u0400-\u04ff]+', core_content.lower()):
        word_counts[word] = word_counts.get(word, 0) + 1

    significant_unknown = [
        w for w in unknown_words
        if word_counts.get(w, 0) >= 2 and len(w) > 3
    ]

    if significant_unknown[:5]:
        violations.append({
            'type': 'VOCABULARY',
            'issue': f"Words used but not in Vocabulary section: {', '.join(significant_unknown[:5])}",
            'fix': "Add these words to Vocabulary table or replace with known vocabulary."
        })

    return violations


def count_vocab_rows(content: str) -> int:
    """Count vocabulary table rows.

    Matches both H1 and H2 headers in English and Ukrainian.
    Handles checkpoint modules with vocabulary subsections.
    """
    # For H1 Словник section (checkpoints), capture everything to end
    vocab_h1_match = re.search(
        r'^#\s+(Vocabulary|Словник)\s*$(.*)$',
        content, re.DOTALL | re.IGNORECASE | re.MULTILINE
    )
    if vocab_h1_match:
        vocab_text = vocab_h1_match.group(2)
        lines = vocab_text.split('\n')
        # Count table rows (excluding separator rows with ---)
        table_rows = [l for l in lines if l.strip().startswith('|') and '---' not in l]
        # Count header rows (one per subsection table)
        header_count = sum(1 for l in table_rows if '| Слово |' in l or '| Word |' in l)
        return max(0, len(table_rows) - header_count)

    # Fallback: original behavior for regular modules (H2 sections)
    vocab_section_match = re.search(
        r'(^#{1,2}\s+(Vocabulary|Словник).*?)(?=\n#{1,2}\s|\Z)',
        content, re.DOTALL | re.IGNORECASE | re.MULTILINE
    )
    if vocab_section_match:
        vocab_text = vocab_section_match.group(1)
        lines = vocab_text.split('\n')
        v_rows = len([
            l for l in lines
            if l.strip().startswith('|') and '---' not in l
        ])
        return max(0, v_rows - 1)  # Subtract header
    return 0


def get_plan_path(level: str) -> Path:
    """Get the path to the curriculum plan for a level."""
    return Path(__file__).parent.parent.parent.parent / f"docs/l2-uk-en/{level.upper()}-CURRICULUM-PLAN.md"


def parse_plan_vocabulary(plan_path: Path, module_num: int) -> set[str]:
    """
    Extract vocabulary list for a specific module from the curriculum plan.

    The plan uses format: **Vocabulary (N words):**
    followed by a comma-separated list of words.

    Args:
        plan_path: Path to the curriculum plan file
        module_num: Module number to find vocabulary for

    Returns:
        Set of vocabulary words (lowercase) from the plan
    """
    if not plan_path.exists():
        return set()

    try:
        content = plan_path.read_text(encoding='utf-8')
    except Exception:
        return set()

    vocab_words = set()

    # Find the module section (#### Module N: or ### Module N:)
    # Pattern matches module headers like "#### Module 01:" or "### Module 05:"
    module_pattern = rf'###?\s*Module\s*0?{module_num}\s*[:.].*?(?=###?\s*Module\s*\d|---|\Z)'
    module_match = re.search(module_pattern, content, re.DOTALL | re.IGNORECASE)

    if not module_match:
        return set()

    module_text = module_match.group(0)

    # Find vocabulary specification: **Vocabulary (N words):**
    vocab_pattern = r'\*\*Vocabulary\s*\([^)]+\):\*\*\s*\n?([^\n*]+(?:\n[^\n*#]+)*)'
    vocab_match = re.search(vocab_pattern, module_text, re.IGNORECASE)

    if vocab_match:
        vocab_list = vocab_match.group(1).strip()
        # Split by comma and clean each word
        for word in vocab_list.split(','):
            word = word.strip()
            # Extract just the Ukrainian word (skip parenthetical notes)
            word = re.sub(r'\([^)]*\)', '', word).strip()
            # Skip empty or very short words
            if len(word) >= 2:
                # Handle ranges like "один-двадцять (20)" - extract first word
                if '-' in word and not re.search(r'[\u0400-\u04ff].*-.*[\u0400-\u04ff]', word):
                    word = word.split('-')[0].strip()
                # Extract Ukrainian words only (including apostrophes)
                uk_words = re.findall(r"[\u0400-\u04ff\'\u2019\u02bc]+", word.lower())
                for uk in uk_words:
                    if len(uk) >= 2:
                        vocab_words.add(uk)

    return vocab_words


def check_vocab_matches_plan(
    module_path: str,
    level: str,
    module_num: int,
    module_vocab: set[str]
) -> list[dict]:
    """
    Compare module vocabulary section against curriculum plan.

    Args:
        module_path: Path to the module file (for error messages)
        level: Level code (A1, A2, etc.)
        module_num: Module number
        module_vocab: Vocabulary words from the module's vocabulary section

    Returns:
        List of violations with type 'VOCAB_PLAN_MISMATCH'
    """
    violations = []
    plan_path = get_plan_path(level)

    if not plan_path.exists():
        # No plan file = no enforcement (plan not yet created)
        return violations

    plan_vocab = parse_plan_vocabulary(plan_path, module_num)

    if not plan_vocab:
        # No vocabulary spec in plan for this module = no enforcement
        return violations

    # Normalize module vocab to lowercase for comparison
    module_vocab_lower = {w.lower() for w in module_vocab if len(w) >= 2}

    # Note: Extra words beyond the plan are ALLOWED (modules can expand on core vocab)
    # We only check for MISSING core words from the plan

    # Find missing words (in plan but not in module)
    missing = plan_vocab - module_vocab_lower
    
    if missing:
        # Check if missing words are actually in the cumulative database
        cumulative_already = get_cumulative_vocab(level, module_num - 1)
        missing = missing - cumulative_already
        
        # Filter out common words
        missing = missing - COMMON_WORDS
        
        # FINAL FILTER: Simple stem check to catch inflections (nature vs природу)
        # If a missing word's stem matches a word in module_vocab, skip it.
        final_missing = set()
        for m in missing:
            # Simple stem = first 4 chars
            stem = m[:4] if len(m) > 4 else m
            has_match = False
            for v in module_vocab_lower:
                if v.startswith(stem):
                    has_match = True
                    break
            if not has_match:
                final_missing.add(m)
        
        if final_missing and len(final_missing) > 0:
            sample = list(final_missing)[:5]
            # VOCAB_PLAN_MISSING is temporarily non-blocking (Issue #387 - separate vocab issue)
            # TODO: Re-enable blocking after vocab enrichment is complete
            is_blocking = False

            violations.append({
                'type': 'VOCAB_PLAN_MISSING',
                'issue': f"Missing vocabulary from plan ({len(final_missing)} words): {', '.join(sample)}...",
                'fix': "Add missing words from curriculum plan to module vocabulary section.",
                'blocking': is_blocking
            })

    return violations


# Metalanguage terms by level that must be taught before use
METALANGUAGE_BY_LEVEL = {
    'A1': {
        'іменник', 'дієслово', 'прикметник', 'займенник',
        'однина', 'множина', 'рід', 'чоловічий', 'жіночий', 'середній'
    },
    'A2': {
        'відмінок', 'називний', 'знахідний', 'родовий', 'давальний',
        'орудний', 'місцевий', 'кличний', 'час', 'теперішній',
        'минулий', 'майбутній', 'вид', 'доконаний', 'недоконаний'
    },
    'B1': {
        'дієприкметник', 'дієприслівник', 'пасивний', 'активний',
        'умовний', 'наказовий', 'спосіб', 'стан', 'інфінітив'
    },
    'B2': {
        'стиль', 'регістр', 'синонім', 'антонім', 'фразеологізм',
        'метафора', 'омонім', 'пароним'
    },
    'C1': {
        'персоніфікація', 'алітерація', 'метонімія', 'гіпербола',
        'літота', 'оксиморон', 'епітет', 'порівняння'
    },
    'C2': {
        'парцеляція', 'анафора', 'епіфора', 'градація',
        'інверсія', 'еліпсис', 'паралелізм', 'антитеза'
    }
}


def check_metalanguage_scaffolding(
    content: str,
    vocab_words: set[str],
    level: str,
    module_num: int = 0,
    cumulative_vocab: set[str] = None
) -> list[dict]:
    """
    Check if grammatical/linguistic terms used in instructions are taught first.

    At A1-A2, grammar terms should appear in vocabulary before being used
    in Ukrainian instructions. This ensures learners understand instructions.

    Args:
        content: Full module content
        vocab_words: Words from the module's vocabulary section
        level: Level code
        module_num: Module number
        cumulative_vocab: Words from previous modules (optional)

    Returns:
        List of violations for untaught metalanguage terms
    """
    violations = []

    level_upper = level.upper()
    if level_upper in ('B1', 'B2', 'C1', 'C2', 'LIT'):
        return violations  # B1+ and LIT assumes all metalanguage known

    # Get metalanguage for this level and all earlier levels
    level_order = ['A1', 'A2', 'B1', 'B2', 'C1', 'C2']
    current_idx = level_order.index(level_upper) if level_upper in level_order else 0

    relevant_metalang = set()
    for i in range(current_idx + 1):
        relevant_metalang.update(METALANGUAGE_BY_LEVEL.get(level_order[i], set()))

    # Find metalanguage terms used in content but not in current or cumulative vocabulary
    content_lower = content.lower()
    vocab_lower = {w.lower() for w in vocab_words}
    
    # If cumulative_vocab is provided, merge it for the check
    known_vocab = vocab_lower.copy()
    if cumulative_vocab:
        known_vocab.update({w.lower() for w in cumulative_vocab})

    used_but_not_taught = []
    for term in relevant_metalang:
        if term in content_lower and term not in known_vocab:
            # Check it's used in Ukrainian context
            if re.search(rf'\b{term}\b', content_lower):
                used_but_not_taught.append(term)

    if used_but_not_taught:
        # Determine if blocking based on level
        is_blocking = level_upper not in ('A1', 'A2') and 'CHECKPOINT' not in level_upper
        
        violations.append({
            'type': 'METALANGUAGE',
            'issue': f"Metalanguage terms used but not in vocabulary: {', '.join(used_but_not_taught[:5])}",
            'fix': "Add these grammar terms to vocabulary with translations, or use English equivalents.",
            'blocking': is_blocking
        })

    return violations


def check_vocab_table_format(content: str, level: str) -> list[dict]:
    """
    Check if the vocabulary table format (headers and columns) matches level requirements.

    A1/A2 (Tier 1/2):
    - Header: # Vocabulary
    - Columns: | Word | IPA | English | POS | Gender | Note | (6 columns)

    B1 (Tier 3):
    - Header: # Словник
    - Columns: | Слово | Вимова | Переклад | ЧМ | Примітка | (5 columns)
    """
    violations = []
    level_upper = level.upper()

    # 1. Check Header Match
    if level_upper in ('A1', 'A2'):
        # Should be '# Vocabulary'
        if re.search(r'^#{1,2}\s+Словник', content, re.MULTILINE | re.IGNORECASE):
            violations.append({
                'type': 'VOCAB_HEADER',
                'issue': f"Level {level_upper} should use '# Vocabulary' header, but '# Словник' found.",
                'fix': "Change '# Словник' to '# Vocabulary'."
            })
    elif level_upper in ('B1', 'B2', 'C1', 'C2'):
        # Should be '# Словник'
        if re.search(r'^#{1,2}\s+Vocabulary', content, re.MULTILINE | re.IGNORECASE):
            violations.append({
                'type': 'VOCAB_HEADER',
                'issue': f"Level {level_upper} should use '# Словник' header, but '# Vocabulary' found.",
                'fix': "Change '# Vocabulary' to '# Словник'."
            })

    # 2. Check Column Format
    vocab_match = re.search(
        r'^#{1,2}\s+(?:Vocabulary|Словник).*?(?=\n#{1,2}\s|\Z)',
        content, re.DOTALL | re.IGNORECASE | re.MULTILINE
    )

    if vocab_match:
        vocab_text = vocab_match.group(0)
        lines = vocab_text.split('\n')
        header_row = ""
        for line in lines:
            if line.strip().startswith('|') and '---' not in line:
                header_row = line
                break

        if header_row:
            parts = [p.strip() for p in header_row.split('|') if p.strip()]
            num_cols = len(parts)

            if level_upper in ('A1', 'A2', 'A2.1', 'A2.2', 'A2.3'):
                if num_cols != 6:
                    violations.append({
                        'type': 'VOCAB_FORMAT',
                        'issue': f"A1/A2 vocabulary requires 6 columns, found {num_cols}: {header_row}",
                        'fix': "Format: | Word | IPA | English | POS | Gender | Note |"
                    })
            elif level_upper in ('B1', 'B2', 'C1', 'C2'):
                # B1+ accepts 3-column (minimal), 5-column (legacy), or 6-column (new standard) formats
                # 6-column is the new standard as of issue #341
                if num_cols not in (3, 5, 6):
                    violations.append({
                        'type': 'VOCAB_FORMAT',
                        'issue': f"{level_upper} vocabulary requires 3, 5, or 6 columns, found {num_cols}: {header_row}",
                        'fix': "Format: | Слово | Вимова | Переклад | ЧМ | Рід | Примітка | (6-col, preferred)",
                        'blocking': False
                    })
                elif num_cols == 5:
                    # Check column names for 5-column format
                    expected = ['слово', 'вимова', 'переклад', 'чм', 'примітка']
                    actual = [p.lower() for p in parts]

                    # Accept "Слово / Вираз" or similar for first column
                    # Accept "Примітки" for last column
                    if 'слово' not in actual[0] and 'термін' not in actual[0]:
                         violations.append({
                            'type': 'VOCAB_FORMAT',
                            'issue': f"{level_upper} vocabulary headers mismatch. Expected 'Слово' in first column, found '{parts[0]}'",
                            'fix': "Standardize headers to: | Слово | Вимова | Переклад | ЧМ | Примітка |",
                            'blocking': False
                        })
                    if 'приміт' not in actual[4]:
                         violations.append({
                            'type': 'VOCAB_FORMAT',
                            'issue': f"{level_upper} vocabulary headers mismatch. Expected 'Примітка' in fifth column, found '{parts[4]}'",
                            'fix': "Standardize headers to: | Слово | Вимова | Переклад | ЧМ | Примітка |",
                            'blocking': False
                        })
                # 3-column format: | Слово | Переклад | Примітки | - no header check needed

    return violations
