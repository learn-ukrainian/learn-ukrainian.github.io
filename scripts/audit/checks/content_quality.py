"""
Content quality validation using LLM evaluation.

Checks if the lesson content is:
- Coherent and well-structured
- Actually teaches what it claims to teach
- Educational (not word salad)
- Has clear explanations and examples

Also includes context-aware character validation for historical quotes (Issue #498).
"""

import os
import re
import json
from typing import Optional

# Check if LLM evaluation is enabled
CONTENT_QUALITY_ENABLED = os.getenv('AUDIT_CONTENT_QUALITY', 'false').lower() == 'true'

# =============================================================================
# Character Classes for Historical Text Validation (Issue #498)
# =============================================================================

# Always invalid - distinctly Russian characters that never appear in Ukrainian
# or historical East Slavic texts
RUSSIAN_ONLY_CHARS = {
    'ы',  # Russian ы (Ukrainian uses и/і)
    'э',  # Russian э (Ukrainian uses е)
    'ё',  # Russian ё (Ukrainian uses ьо/йо)
    'Ы', 'Э', 'Ё',  # Uppercase variants
}

# Valid in historical quotes only - Old Church Slavonic / Old East Slavic characters
# These appear in authentic historical texts (OES, RUTH, LIT, chronicles)
HISTORICAL_CYRILLIC_CHARS = {
    'ъ',  # Hard sign (yer) - e.g., сънъ → сон
    'ѣ',  # Yat - e.g., лѣсъ → ліс
    'ѫ',  # Big yus (nasal o)
    'ѧ',  # Little yus (nasal e)
    'ѳ',  # Fita (Greek theta)
    'ѵ',  # Izhitsa (Greek upsilon)
    'ѡ',  # Omega
    'ѯ',  # Ksi
    'ѱ',  # Psi
    'ѭ',  # Iotified big yus
    'ѩ',  # Iotified little yus
    'ѥ',  # Iotified e
    'ꙗ',  # Iotified a (alternative ya)
    'ꙋ',  # Uk (digraph ou)
    'Ъ', 'Ѣ', 'Ѫ', 'Ѧ', 'Ѳ', 'Ѵ', 'Ѡ',  # Uppercase variants
    'Ѯ', 'Ѱ', 'Ѭ', 'Ѩ', 'Ѥ',
}

# Combined set for quick lookup
ALL_FORBIDDEN_IN_MODERN = RUSSIAN_ONLY_CHARS | HISTORICAL_CYRILLIC_CHARS

# Tracks that legitimately quote historical texts
HISTORICAL_TRACKS = {'oes', 'ruth', 'lit', 'b2-hist', 'c1-bio', 'c1-hist'}

# Tracks that TEACH historical linguistics - fully exempt from character checks
# These tracks explicitly analyze historical Cyrillic (including Russian-like forms)
LINGUISTIC_ANALYSIS_TRACKS = {'oes', 'ruth'}


def is_inside_quoted_string(line: str, char_pos: int) -> bool:
    """
    Check if a character position is inside a quoted string.

    Supports:
    - Double quotes: "..."
    - Guillemets: «...»
    - Single quotes: '...'

    This allows Russian characters in educational quotes (e.g., showing what
    Russian propaganda says with Ukrainian translation).
    """
    # Count open/close quote pairs before this position
    text_before = line[:char_pos]

    # Check double quotes
    double_quote_count = text_before.count('"')
    if double_quote_count % 2 == 1:  # Odd number means we're inside
        return True

    # Check guillemets (Ukrainian/Russian quote marks)
    open_guillemet = text_before.count('«')
    close_guillemet = text_before.count('»')
    if open_guillemet > close_guillemet:
        return True

    return False


def is_historical_quote_line(line: str) -> bool:
    """
    Detect if a line is a historical quote that should allow historical characters.

    Recognized patterns:
    - Blockquotes: > ...
    - Labeled quotes: > **Оригінал:** ...
    - Callout quotes: > [!quote] ...
    - Primary source markers: > [!primary-source] ...
    """
    stripped = line.strip()

    # Must be a blockquote
    if not stripped.startswith('>'):
        return False

    # All blockquotes in historical tracks are considered historical quotes
    return True


def is_historical_context_block(lines: list[str], line_idx: int) -> bool:
    """
    Check if a line is within a historical context block.

    Looks for markers like:
    - > **Оригінал:**
    - > [!quote]
    - > [!primary-source]
    - Being part of a continuous blockquote section
    """
    # Check current line
    current_line = lines[line_idx].strip()
    if not current_line.startswith('>'):
        return False

    # Check for explicit markers in current line
    quote_content = current_line[1:].strip().lower()
    explicit_markers = [
        '**оригінал',
        '[!quote]',
        '[!primary-source]',
        '[!chronicle]',
        '[!historical]',
        '**первинне джерело',
        '**джерело:',
    ]
    for marker in explicit_markers:
        if marker in quote_content:
            return True

    # Check if part of a blockquote block that started with a marker
    # Look backwards for the start of this blockquote section
    for i in range(line_idx - 1, -1, -1):
        prev_line = lines[i].strip()
        if not prev_line.startswith('>'):
            # End of blockquote section going backwards
            break
        prev_content = prev_line[1:].strip().lower()
        for marker in explicit_markers:
            if marker in prev_content:
                return True

    return False


def detect_track_from_path(file_path: str) -> str | None:
    """Extract track identifier from file path."""
    if not file_path:
        return None

    path_lower = file_path.lower()

    # Check for track directories
    track_patterns = [
        (r'/oes/', 'oes'),
        (r'/ruth/', 'ruth'),
        (r'/lit/', 'lit'),
        (r'/b2-hist/', 'b2-hist'),
        (r'/c1-bio/', 'c1-bio'),
        (r'/c1-hist/', 'c1-hist'),
    ]

    for pattern, track in track_patterns:
        if re.search(pattern, path_lower):
            return track

    return None


# YAML fields that allow historical characters
HISTORICAL_YAML_FIELDS = {
    'oes',           # Old East Slavic original text
    'ruth',          # Ruthenian original text
    'original',      # Generic original historical text
    'church_slavonic',  # Church Slavonic text
    'source_text',   # Primary source text
}


def validate_yaml_vocabulary(yaml_content: str, file_path: str = "") -> list[dict]:
    """
    Validate character usage in YAML vocabulary files.

    Allows historical characters in specific fields (oes, ruth, original, etc.)
    but flags them in modern Ukrainian fields.

    Args:
        yaml_content: Raw YAML content string
        file_path: Path to file for track detection

    Returns:
        List of violations
    """
    violations = []
    track = detect_track_from_path(file_path)

    # Parse line by line to identify field context
    lines = yaml_content.split('\n')
    current_field = None
    russian_found = []
    historical_in_modern = []

    for idx, line in enumerate(lines):
        # Detect field name from YAML structure
        field_match = re.match(r'^[\s-]*(\w+):\s*(.*)$', line)
        if field_match:
            current_field = field_match.group(1).lower()
            value = field_match.group(2)
        else:
            # Continuation of previous field or multiline
            value = line

        # Skip if in a historical field
        if current_field in HISTORICAL_YAML_FIELDS:
            # Still check for Russian-only chars even in historical fields
            for char in value:
                if char in RUSSIAN_ONLY_CHARS:
                    russian_found.append({
                        'char': char,
                        'line': idx + 1,
                        'field': current_field
                    })
            continue

        # Check all characters in non-historical fields
        for char in value:
            if char in RUSSIAN_ONLY_CHARS:
                russian_found.append({
                    'char': char,
                    'line': idx + 1,
                    'field': current_field
                })
            elif char in HISTORICAL_CYRILLIC_CHARS:
                historical_in_modern.append({
                    'char': char,
                    'line': idx + 1,
                    'field': current_field
                })

    # Report violations
    if russian_found:
        chars = set(m['char'] for m in russian_found)
        violations.append({
            'type': 'RUSSIAN_CHARACTERS_YAML',
            'severity': 'error',
            'issue': f"Found Russian-only characters in vocabulary YAML: {', '.join(chars)}",
            'fix': "Replace with Ukrainian equivalents: ы→и, э→е, ё→ьо/йо"
        })

    if historical_in_modern:
        chars = set(m['char'] for m in historical_in_modern)
        fields = set(m['field'] for m in historical_in_modern if m['field'])
        violations.append({
            'type': 'HISTORICAL_CHARS_IN_MODERN_YAML',
            'severity': 'error',
            'issue': f"Found historical characters in modern fields: {', '.join(chars)} (fields: {', '.join(fields) if fields else 'unknown'})",
            'fix': f"Move historical text to 'oes:', 'ruth:', or 'original:' fields. Allowed fields: {', '.join(HISTORICAL_YAML_FIELDS)}"
        })

    return violations


def validate_characters_in_content(
    content: str,
    level_code: str,
    file_path: str = ""
) -> list[dict]:
    """
    Context-aware character validation for historical quotes.

    Rules:
    - RUSSIAN_ONLY chars (ы, э, ё): Always flagged as errors
    - HISTORICAL_CYRILLIC chars (ъ, ѣ, etc.):
      - Allowed in historical quote blocks
      - Allowed in historical tracks (OES, RUTH, LIT, B2-HIST, C1-BIO)
      - Flagged in modern Ukrainian prose

    Exception: OES and RUTH tracks are FULLY EXEMPT from these checks
    because they explicitly teach historical Cyrillic orthography.

    Returns list of violations.
    """
    violations = []

    # Detect track from file path
    track = detect_track_from_path(file_path)
    is_historical_track = track in HISTORICAL_TRACKS if track else False

    # Also check level_code for track info
    level_lower = level_code.lower() if level_code else ''
    if level_lower in HISTORICAL_TRACKS:
        is_historical_track = True

    # OES and RUTH are linguistic analysis tracks - fully exempt from character checks
    # These tracks explicitly teach historical Cyrillic including forms like ы, ъ, ь, ѣ
    is_linguistic_track = (track in LINGUISTIC_ANALYSIS_TRACKS if track else False) or \
                          (level_lower in LINGUISTIC_ANALYSIS_TRACKS)
    if is_linguistic_track:
        return violations  # Skip all character checks for OES/RUTH

    lines = content.split('\n')
    russian_only_found = []
    historical_in_modern_found = []

    for idx, line in enumerate(lines):
        # Check each character in the line
        for char_pos, char in enumerate(line):
            # print(f"DEBUG: line[{idx}] char[{char_pos}]='{char}'")
            # Russian-only chars are invalid UNLESS inside quoted strings
            # (educational context showing Russian terms with Ukrainian translation)
            if char in RUSSIAN_ONLY_CHARS:
                # print(f"DEBUG: Found Russian char '{char}' at line {idx+1}")
                # Allow Russian chars inside quotes (for "Prosecutor's Voice" exception)
                # e.g., "исконно русский Крым" (укр. «споконвічно російський Крим»)
                if is_inside_quoted_string(line, char_pos):
                    continue

                russian_only_found.append({
                    'char': char,
                    'line': idx + 1,
                    'context': line[:80]
                })
                continue

            # Historical chars need context check
            if char in HISTORICAL_CYRILLIC_CHARS:
                # Check if this line is in a historical quote context
                is_quote = is_historical_quote_line(line)
                is_explicit_historical = is_historical_context_block(lines, idx)

                # Allow if:
                # 1. In a historical track AND in a blockquote
                # 2. In an explicitly marked historical quote block
                if is_historical_track and is_quote:
                    continue
                if is_explicit_historical:
                    continue

                # Otherwise, flag it
                historical_in_modern_found.append({
                    'char': char,
                    'line': idx + 1,
                    'context': line[:80]
                })

    # Report Russian-only chars (always error)
    if russian_only_found:
        chars = set(m['char'] for m in russian_only_found)
        lines_affected = sorted(set(m['line'] for m in russian_only_found))[:5]
        violations.append({
            'type': 'RUSSIAN_CHARACTERS',
            'severity': 'error',
            'issue': f"Found Russian-only characters: {', '.join(chars)} (lines: {lines_affected})",
            'fix': "Replace with Ukrainian equivalents: ы→и, э→е, ё→ьо/йо. These characters never appear in Ukrainian."
        })

    # Report historical chars in modern context
    if historical_in_modern_found:
        chars = set(m['char'] for m in historical_in_modern_found)
        lines_affected = sorted(set(m['line'] for m in historical_in_modern_found))[:5]

        if is_historical_track:
            fix_msg = "Move historical text into a blockquote (> ) to mark it as a primary source quote."
        else:
            fix_msg = "Remove historical characters from modern Ukrainian prose, or use [!quote] callout for authentic historical quotes."

        violations.append({
            'type': 'HISTORICAL_CHARS_IN_MODERN',
            'severity': 'error',
            'issue': f"Found historical Cyrillic characters outside quote context: {', '.join(chars)} (lines: {lines_affected})",
            'fix': fix_msg
        })

    return violations


def extract_lesson_content(content: str) -> str:
    """Extract the main lesson content (everything before Activities section)."""
    # Find the Activities section
    activities_match = re.search(
        r'^## (?:Activities|Вправи)',
        content,
        re.MULTILINE
    )

    if activities_match:
        lesson_content = content[:activities_match.start()]
    else:
        # If no Activities section, take everything up to Vocabulary
        vocab_match = re.search(
            r'^## (?:Vocabulary|Словник)',
            content,
            re.MULTILINE
        )
        if vocab_match:
            lesson_content = content[:vocab_match.start()]
        else:
            # Take everything
            lesson_content = content

    # Remove frontmatter
    frontmatter_match = re.match(r'^---\n.*?\n---\n', lesson_content, re.DOTALL)
    if frontmatter_match:
        lesson_content = lesson_content[frontmatter_match.end():]

    return lesson_content.strip()


def extract_module_metadata(content: str) -> dict:
    """Extract module metadata for context."""
    metadata = {}

    # Extract title
    title_match = re.search(r'^title:\s*(.+)$', content, re.MULTILINE)
    if title_match:
        metadata['title'] = title_match.group(1).strip()

    # Extract phase/level
    phase_match = re.search(r'^phase:\s*(.+)$', content, re.MULTILINE)
    if phase_match:
        metadata['phase'] = phase_match.group(1).strip()

    # Extract module number from title or content
    module_match = re.search(r'^module:\s*(\d+)$', content, re.MULTILINE)
    if module_match:
        metadata['module'] = int(module_match.group(1))

    # Extract pedagogy
    pedagogy_match = re.search(r'^pedagogy:\s*"?([^"\n]+)"?$', content, re.MULTILINE)
    if pedagogy_match:
        metadata['pedagogy'] = pedagogy_match.group(1).strip()

    # Extract first H1 heading as topic
    h1_match = re.search(r'^# (.+)$', content, re.MULTILINE)
    if h1_match:
        metadata['topic'] = h1_match.group(1).strip()

    return metadata


def call_gemini_api(lesson_content: str, metadata: dict) -> Optional[dict]:
    """Call Gemini API to evaluate content quality."""
    try:
        import google.generativeai as genai

        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            return None

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash-exp')

        prompt = f"""You are a Ukrainian language curriculum auditor. Evaluate this lesson content for educational quality.

**Module Metadata:**
- Title: {metadata.get('title', 'Unknown')}
- Level: {metadata.get('phase', 'Unknown')}
- Topic: {metadata.get('topic', 'Unknown')}
- Pedagogy: {metadata.get('pedagogy', 'Unknown')}

**Lesson Content:**
{lesson_content[:4000]}  # Limit to avoid token overflow

**Evaluation Criteria:**
1. **Coherence**: Is the content logically organized and easy to follow?
2. **Relevance**: Does it actually teach what the title/topic claims?
3. **Educational Value**: Are there clear explanations and useful examples?
4. **Language Quality**: Is it well-written, not repetitive or confusing?
5. **Word Salad Check**: Does it contain meaningless filler or repetitive patterns?
6. **Linguistic Accuracy**: Are all examples valid Ukrainian words? (Flag any Russian words like 'брать', 'кон', 'ы' disguised as Ukrainian).

**Response Format (JSON only):**
{{
  "coherence_score": 1-5,
  "relevance_score": 1-5,
  "educational_score": 1-5,
  "language_score": 1-5,
  "overall_score": 1-5,
  "is_word_salad": true/false,
  "issues": ["issue 1", "issue 2"],
  "strengths": ["strength 1", "strength 2"],
  "recommendation": "PASS" or "NEEDS_IMPROVEMENT" or "REWRITE"
}}

Respond with ONLY valid JSON, no markdown fences or explanations."""

        response = model.generate_content(prompt)

        # Extract JSON from response
        response_text = response.text.strip()

        # Remove markdown code fences if present
        response_text = re.sub(r'^```json\s*', '', response_text)
        response_text = re.sub(r'\s*```$', '', response_text)

        result = json.loads(response_text)
        return result

    except ImportError:
        print("⚠️  google-generativeai not installed. Install with: pip install google-generativeai")
        return None
    except Exception as e:
        print(f"⚠️  Gemini API error: {e}")
        return None


def call_claude_api(lesson_content: str, metadata: dict) -> Optional[dict]:
    """Call Claude API to evaluate content quality."""
    try:
        import anthropic

        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            return None

        client = anthropic.Anthropic(api_key=api_key)

        prompt = f"""You are a Ukrainian language curriculum auditor. Evaluate this lesson content for educational quality.

**Module Metadata:**
- Title: {metadata.get('title', 'Unknown')}
- Level: {metadata.get('phase', 'Unknown')}
- Topic: {metadata.get('topic', 'Unknown')}
- Pedagogy: {metadata.get('pedagogy', 'Unknown')}

**Lesson Content:**
{lesson_content[:4000]}  # Limit to avoid token overflow

**Evaluation Criteria:**
1. **Coherence**: Is the content logically organized and easy to follow?
2. **Relevance**: Does it actually teach what the title/topic claims?
3. **Educational Value**: Are there clear explanations and useful examples?
4. **Language Quality**: Is it well-written, not repetitive or confusing?
5. **Word Salad Check**: Does it contain meaningless filler or repetitive patterns?

**Response Format (JSON only):**
{{
  "coherence_score": 1-5,
  "relevance_score": 1-5,
  "educational_score": 1-5,
  "language_score": 1-5,
  "overall_score": 1-5,
  "is_word_salad": true/false,
  "issues": ["issue 1", "issue 2"],
  "strengths": ["strength 1", "strength 2"],
  "recommendation": "PASS" or "NEEDS_IMPROVEMENT" or "REWRITE"
}}

Respond with ONLY valid JSON."""

        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )

        response_text = message.content[0].text.strip()

        # Remove markdown code fences if present
        response_text = re.sub(r'^```json\s*', '', response_text)
        response_text = re.sub(r'\s*```$', '', response_text)

        result = json.loads(response_text)
        return result

    except ImportError:
        print("⚠️  anthropic not installed. Install with: pip install anthropic")
        return None
    except Exception as e:
        print(f"⚠️  Claude API error: {e}")
        return None


def check_content_quality(
    content: str,
    level_code: str,
    module_num: int,
    file_path: str = ""
) -> list[dict]:
    """
    Check if lesson content is educational and coherent using LLM evaluation.

    Also performs context-aware character validation (Issue #498).

    Returns:
        List of violations with format:
        {
            'type': 'CONTENT_QUALITY',
            'severity': 'warning' | 'error',
            'message': 'Description of issue',
            'fix': 'Suggested fix'
        }
    """
    violations = []

    # --- Deterministic Checks (Run regardless of API Key or Enabled Flag) ---

    # Extract metadata first to check if this is a Surzhyk module
    metadata = extract_module_metadata(content)
    is_surzhyk_module = False

    # Check if module is about Surzhyk (allow Russian characters for pedagogical purposes)
    for field in ['title', 'topic', 'pedagogy']:
        if field in metadata:
            value = metadata[field].lower()
            if 'surzhyk' in value or 'сурж' in value:
                is_surzhyk_module = True
                break

    # Context-aware character validation (Issue #498)
    # Skip for Surzhyk modules which intentionally contain Russian
    if not is_surzhyk_module:
        char_violations = validate_characters_in_content(content, level_code, file_path)
        violations.extend(char_violations)


    if not CONTENT_QUALITY_ENABLED:
        return violations

    # Extract lesson content for LLM checks (metadata already extracted above)
    lesson_content = extract_lesson_content(content)

    # Skip if lesson content is too short (less than 500 chars)
    if len(lesson_content) < 500:
        violations.append({
            'type': 'CONTENT_QUALITY',
            'severity': 'warning',
            'issue': f'Lesson content too short ({len(lesson_content)} chars)',
            'fix': 'Expand lesson content with more explanations and examples'
        })
        return violations

    # Try Gemini first, fall back to Claude
    evaluation = call_gemini_api(lesson_content, metadata)
    if evaluation is None:
        evaluation = call_claude_api(lesson_content, metadata)

    if evaluation is None:
        # LLM evaluation unavailable
        violations.append({
            'type': 'CONTENT_QUALITY',
            'severity': 'info',
            'issue': 'LLM evaluation unavailable (set GEMINI_API_KEY or ANTHROPIC_API_KEY)',
            'fix': 'Set API key in environment to enable content quality checks'
        })
        return violations

    if evaluation is None:
        return violations


    # Check overall score
    overall_score = evaluation.get('overall_score', 0)
    if overall_score < 3:
        violations.append({
            'type': 'CONTENT_QUALITY',
            'severity': 'error',
            'issue': f'Low quality score: {overall_score}/5',
            'fix': f"Issues: {', '.join(evaluation.get('issues', []))}"
        })
    elif overall_score == 3:
        violations.append({
            'type': 'CONTENT_QUALITY',
            'severity': 'warning',
            'issue': f'Moderate quality score: {overall_score}/5',
            'fix': f"Consider improvements: {', '.join(evaluation.get('issues', []))}"
        })

    # Check for word salad
    if evaluation.get('is_word_salad', False):
        violations.append({
            'type': 'CONTENT_QUALITY',
            'severity': 'error',
            'issue': 'Content appears to be word salad or meaningless filler',
            'fix': 'Rewrite with clear educational structure and meaningful examples'
        })

    # Check individual scores
    for metric in ['coherence_score', 'relevance_score', 'educational_score', 'language_score']:
        score = evaluation.get(metric, 5)
        if score < 3:
            metric_name = metric.replace('_score', '').title()
            violations.append({
                'type': 'CONTENT_QUALITY',
                'severity': 'warning',
                'issue': f'Low {metric_name} score: {score}/5',
                'fix': f"Improve {metric_name.lower()}"
            })

    # Add recommendation-based violation
    recommendation = evaluation.get('recommendation', 'PASS')
    if recommendation == 'REWRITE':
        violations.append({
            'type': 'CONTENT_QUALITY',
            'severity': 'error',
            'issue': 'LLM recommends complete rewrite',
            'fix': f"Major issues: {', '.join(evaluation.get('issues', []))}"
        })
    elif recommendation == 'NEEDS_IMPROVEMENT':
        violations.append({
            'type': 'CONTENT_QUALITY',
            'severity': 'warning',
            'issue': 'LLM recommends improvements',
            'fix': f"Suggested: {', '.join(evaluation.get('issues', []))}"
        })

    return violations
