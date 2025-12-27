"""
VESUM word validation for module auditing.

Validates Ukrainian words in module content against the VESUM dictionary
(430k+ lemmas) via the nlp_uk Docker container.

See: https://github.com/brown-uk/dict_uk
"""

import re
from typing import Optional


def check_vesum_words(
    content: str,
    vocab_words: list[str],
    level_code: str,
    module_num: int,
    skip_vesum: bool = False
) -> list[dict]:
    """
    Validate Ukrainian words against VESUM dictionary.

    This check extracts Ukrainian words from vocabulary sections and body text,
    then validates them against VESUM to catch:
    - Misspelled words
    - Non-existent words
    - Words not in standard Ukrainian

    Args:
        content: Full module content
        vocab_words: Words from vocabulary section
        level_code: Level code (A1, A2, B1, etc.)
        module_num: Module number
        skip_vesum: If True, skip VESUM validation (container not running)

    Returns:
        List of violation dicts with type, severity, issue, fix
    """
    violations = []

    if skip_vesum:
        return violations

    # Only check B1+ modules (fully immersed Ukrainian content)
    # B1 M01-M05 are metalanguage bridge but still Ukrainian text - VESUM useful
    if level_code not in ('B1', 'B2', 'C1', 'C2', 'LIT'):
        return violations

    try:
        from ..vesum_client import VesumClient
    except ImportError:
        # Client not available, skip silently
        return violations

    client = VesumClient()

    if not client.is_running():
        # Auto-start container if not running
        print(f"  🐳 Starting VESUM container...")
        try:
            client.start(timeout=120)  # Allow up to 2 min for first build
            print(f"  ✅ VESUM container ready")
        except Exception as e:
            violations.append({
                'type': 'VESUM_START_ERROR',
                'severity': 'warning',
                'issue': f"Failed to start VESUM container: {e}",
                'fix': "Check Docker is running and build with: cd docker/nlp_uk && docker compose build",
                'blocking': False
            })
            return violations

    # Use context-aware tagging instead of word-by-word validation
    # This correctly handles proper nouns, declined forms, etc.
    try:
        # Clean content for tagging (remove markdown formatting but keep sentences)
        clean_text = _prepare_text_for_tagging(content)

        if not clean_text.strip():
            return violations

        # Tag the full text with context
        tag_result = client.tag_text(clean_text)
        unknown_words = tag_result.get('unknown_words', [])

        if unknown_words:
            # Filter out common abbreviations and single letters
            filtered_unknown = [
                w for w in unknown_words
                if len(w) >= 3 and w.upper() not in ('НДВ', 'ДВ', 'ПРИКМ', 'ДІЄСЛ', 'ІМ', 'ЧОЛ', 'ЖІН', 'СЕР')
            ]

            if filtered_unknown:
                # Check if any are in vocabulary section (more serious)
                vocab_set = set(w.lower() for w in vocab_words)
                vocab_invalid = [w for w in filtered_unknown if w.lower() in vocab_set]
                body_invalid = [w for w in filtered_unknown if w.lower() not in vocab_set]

                if vocab_invalid:
                    violations.append({
                        'type': 'VESUM_VOCAB_INVALID',
                        'severity': 'error',
                        'issue': f"Vocabulary words not in VESUM: {', '.join(vocab_invalid[:10])}{'...' if len(vocab_invalid) > 10 else ''}",
                        'fix': "Check spelling against slovnyk.ua or VESUM",
                        'blocking': True
                    })

                if body_invalid:
                    violations.append({
                        'type': 'VESUM_BODY_INVALID',
                        'severity': 'warning',
                        'issue': f"Words not in VESUM: {', '.join(body_invalid[:10])}{'...' if len(body_invalid) > 10 else ''} ({len(body_invalid)} total)",
                        'fix': "Verify spelling or add to exceptions",
                        'blocking': False
                    })

    except Exception as e:
        violations.append({
            'type': 'VESUM_ERROR',
            'severity': 'warning',
            'issue': f"VESUM validation error: {e}",
            'fix': "Check nlp_uk container logs",
            'blocking': False
        })

    return violations


def _is_ukrainian(text: str) -> bool:
    """Check if text contains Ukrainian Cyrillic characters."""
    # Ukrainian-specific letters: і, ї, є, ґ (plus all Cyrillic)
    return bool(re.search(r'[\u0400-\u04FF]', text))


def _prepare_text_for_tagging(content: str) -> str:
    """
    Prepare module content for VESUM tagging.

    Removes markdown formatting but preserves sentence structure
    so nlp_uk can use context for proper noun disambiguation.
    """
    # Remove frontmatter
    text = re.sub(r'^---.*?---\s*', '', content, flags=re.DOTALL)

    # Remove code blocks
    text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)

    # Remove inline code
    text = re.sub(r'`[^`]+`', '', text)

    # Remove URLs
    text = re.sub(r'https?://\S+', '', text)

    # Remove markdown links but keep text: [text](url) -> text
    text = re.sub(r'\[([^\]]*)\]\([^)]*\)', r'\1', text)

    # Remove markdown headers but keep text
    text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)

    # Remove callout syntax but keep content
    text = re.sub(r'>\s*\[![^\]]+\]\s*', '', text)

    # Remove table formatting but keep content
    text = re.sub(r'\|', ' ', text)
    text = re.sub(r'^[-:]+$', '', text, flags=re.MULTILINE)

    # Remove bold/italic markers
    text = re.sub(r'\*+', '', text)
    text = re.sub(r'_+', '', text)

    # Remove list markers
    text = re.sub(r'^\s*[-*]\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*\d+\.\s*', '', text, flags=re.MULTILINE)

    # Collapse multiple whitespace/newlines
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' {2,}', ' ', text)

    return text.strip()


def _extract_ukrainian_words(content: str) -> set[str]:
    """
    Extract Ukrainian words from module content.

    Excludes:
    - English text
    - Headers and markdown syntax
    - Code blocks
    - URLs
    - Table formatting
    """
    words = set()

    # Remove code blocks
    content = re.sub(r'```.*?```', '', content, flags=re.DOTALL)

    # Remove URLs
    content = re.sub(r'https?://\S+', '', content)

    # Remove markdown links keeping just the text
    content = re.sub(r'\[([^\]]*)\]\([^)]*\)', r'\1', content)

    # Remove table formatting but keep content
    content = re.sub(r'\|', ' ', content)

    # Remove frontmatter
    content = re.sub(r'^---.*?---\s*', '', content, flags=re.DOTALL)

    # Find Ukrainian words (Cyrillic + apostrophe which is valid in Ukrainian)
    for match in re.finditer(r"[\u0400-\u04FF][\u0400-\u04FF''ʼ]*", content):
        word = match.group()
        # Skip single letters and very short words
        if len(word) >= 3:
            # Normalize apostrophes
            word = word.replace("'", "'").replace("ʼ", "'")
            words.add(word.lower())

    return words


def check_vesum_activities(
    activities: list[dict],
    level_code: str,
    module_num: int,
    skip_vesum: bool = False
) -> list[dict]:
    """
    Validate Ukrainian words in activity content against VESUM dictionary.

    Extracts text from all activity types and validates:
    - Answer fields (blocking if invalid)
    - General text fields (warning if invalid)
    - Skips 'error' fields in error-correction (intentional errors)

    Args:
        activities: List of parsed activity dictionaries
        level_code: Level code (A1, A2, B1, etc.)
        module_num: Module number
        skip_vesum: If True, skip VESUM validation

    Returns:
        List of violation dicts with type, severity, issue, fix
    """
    violations = []

    if skip_vesum or not activities:
        return violations

    # Only check B1+ modules
    if level_code not in ('B1', 'B2', 'C1', 'C2', 'LIT'):
        return violations

    try:
        from ..vesum_client import VesumClient
    except ImportError:
        return violations

    client = VesumClient()

    if not client.is_running():
        # Container should already be started by check_vesum_words
        # If not running, skip silently (main check will handle startup)
        return violations

    # Extract text from activities, categorized by importance
    answer_texts = []  # Correct answers - must be valid (blocking)
    general_texts = []  # Other text - should be valid (warning)

    for activity in activities:
        act_type = activity.get('type', '')
        title = activity.get('title', '')

        texts = _extract_activity_texts(activity, act_type)
        answer_texts.extend(texts['answers'])
        general_texts.extend(texts['general'])

    # Validate answer texts (blocking)
    if answer_texts:
        combined_answers = ' '.join(answer_texts)
        if combined_answers.strip():
            try:
                tag_result = client.tag_text(combined_answers)
                unknown = tag_result.get('unknown_words', [])
                # Filter: only Ukrainian words, >= 3 chars
                filtered = [
                    w for w in unknown
                    if len(w) >= 3 and _is_ukrainian(w)
                ]
                if filtered:
                    violations.append({
                        'type': 'VESUM_ACTIVITY_ANSWER_INVALID',
                        'severity': 'error',
                        'issue': f"Activity answers not in VESUM: {', '.join(filtered[:10])}{'...' if len(filtered) > 10 else ''}",
                        'fix': "Check spelling of correct answers against slovnyk.ua",
                        'blocking': True
                    })
            except Exception as e:
                pass  # Silent fail, main check handles errors

    # Validate general texts (warning)
    if general_texts:
        combined_general = ' '.join(general_texts)
        if combined_general.strip():
            try:
                tag_result = client.tag_text(combined_general)
                unknown = tag_result.get('unknown_words', [])
                # Filter: only Ukrainian words, >= 3 chars
                filtered = [
                    w for w in unknown
                    if len(w) >= 3 and _is_ukrainian(w)
                ]
                if filtered:
                    violations.append({
                        'type': 'VESUM_ACTIVITY_TEXT_INVALID',
                        'severity': 'warning',
                        'issue': f"Activity text not in VESUM: {', '.join(filtered[:10])}{'...' if len(filtered) > 10 else ''} ({len(filtered)} total)",
                        'fix': "Verify spelling or check if intentional (e.g., proper nouns)",
                        'blocking': False
                    })
            except Exception as e:
                pass  # Silent fail

    return violations


def _extract_activity_texts(activity: dict, act_type: str) -> dict:
    """
    Extract Ukrainian text from an activity, categorized by importance.

    Returns dict with:
        'answers': List of correct answer texts (must be valid)
        'general': List of other text content (should be valid)
        'skip': List of intentionally incorrect text (not validated)
    """
    answers = []
    general = []

    # Add title to general (if Ukrainian)
    title = activity.get('title', '')
    if title and _is_ukrainian(title):
        general.append(title)

    if act_type == 'quiz':
        for item in activity.get('items', []):
            q = item.get('question', '')
            if _is_ukrainian(q):
                general.append(q)
            for opt in item.get('options', []):
                text = opt.get('text', '') if isinstance(opt, dict) else str(opt)
                if _is_ukrainian(text):
                    if isinstance(opt, dict) and opt.get('correct'):
                        answers.append(text)
                    else:
                        general.append(text)
            expl = item.get('explanation', '')
            if expl and _is_ukrainian(expl):
                general.append(expl)

    elif act_type == 'select':
        for item in activity.get('items', []):
            q = item.get('question', '')
            if _is_ukrainian(q):
                general.append(q)
            for opt in item.get('options', []):
                text = opt.get('text', '') if isinstance(opt, dict) else str(opt)
                if _is_ukrainian(text):
                    if isinstance(opt, dict) and opt.get('correct'):
                        answers.append(text)
                    else:
                        general.append(text)

    elif act_type == 'true-false':
        for item in activity.get('items', []):
            stmt = item.get('statement', '')
            if _is_ukrainian(stmt):
                general.append(stmt)

    elif act_type == 'fill-in':
        for item in activity.get('items', []):
            sent = item.get('sentence', '')
            if _is_ukrainian(sent):
                general.append(sent)
            ans = item.get('answer', '')
            if _is_ukrainian(ans):
                answers.append(ans)
            for opt in item.get('options', []):
                if _is_ukrainian(opt):
                    general.append(opt)

    elif act_type == 'cloze':
        passage = activity.get('passage', '')
        if _is_ukrainian(passage):
            # Remove blank markers for validation
            clean_passage = re.sub(r'\{[^}]+\}', '', passage)
            general.append(clean_passage)
        for blank in activity.get('blanks', []):
            ans = blank.get('answer', '')
            if _is_ukrainian(ans):
                answers.append(ans)
            for opt in blank.get('options', []):
                if _is_ukrainian(opt):
                    general.append(opt)

    elif act_type == 'match-up':
        for pair in activity.get('pairs', []):
            left = pair.get('left', '')
            right = pair.get('right', '')
            # Both sides are "correct" answers
            if _is_ukrainian(left):
                answers.append(left)
            if _is_ukrainian(right):
                answers.append(right)

    elif act_type == 'group-sort':
        for group in activity.get('groups', []):
            name = group.get('name', '')
            if _is_ukrainian(name):
                general.append(name)
            for item in group.get('items', []):
                if _is_ukrainian(item):
                    answers.append(item)  # Items are correct placements

    elif act_type == 'unjumble':
        for item in activity.get('items', []):
            # Words are scrambled but all valid Ukrainian
            for word in item.get('words', []):
                if _is_ukrainian(word):
                    answers.append(word)
            ans = item.get('answer', '')
            if _is_ukrainian(ans):
                answers.append(ans)

    elif act_type == 'error-correction':
        for item in activity.get('items', []):
            sent = item.get('sentence', '')
            if _is_ukrainian(sent):
                general.append(sent)
            # SKIP the 'error' field - it's intentionally wrong!
            ans = item.get('answer', '')
            if _is_ukrainian(ans):
                answers.append(ans)  # Correct answer must be valid
            # Options include both correct and distractors
            for opt in item.get('options', []):
                if _is_ukrainian(opt):
                    # Don't know which is correct, add to general
                    general.append(opt)
            expl = item.get('explanation', '')
            if expl and _is_ukrainian(expl):
                general.append(expl)

    elif act_type == 'mark-the-words':
        passage = activity.get('passage', '')
        if _is_ukrainian(passage):
            general.append(passage)
        for word in activity.get('correct_words', []):
            if _is_ukrainian(word):
                answers.append(word)
        instr = activity.get('instruction', '')
        if instr and _is_ukrainian(instr):
            general.append(instr)

    elif act_type == 'dialogue-reorder':
        for line in activity.get('lines', []):
            text = line.get('text', '') if isinstance(line, dict) else str(line)
            if _is_ukrainian(text):
                answers.append(text)  # All lines should be valid

    elif act_type == 'translate':
        for item in activity.get('items', []):
            src = item.get('source', '')
            if _is_ukrainian(src):
                general.append(src)
            for opt in item.get('options', []):
                text = opt.get('text', '') if isinstance(opt, dict) else str(opt)
                if _is_ukrainian(text):
                    if isinstance(opt, dict) and opt.get('correct'):
                        answers.append(text)
                    else:
                        general.append(text)

    elif act_type == 'anagram':
        for item in activity.get('items', []):
            # Scrambled is just reordered letters of answer
            ans = item.get('answer', '')
            if _is_ukrainian(ans):
                answers.append(ans)
            hint = item.get('hint', '')
            if hint and _is_ukrainian(hint):
                general.append(hint)

    return {'answers': answers, 'general': general}


def get_vesum_status() -> dict:
    """
    Get VESUM container status.

    Returns:
        Dict with 'running' bool and 'message' string
    """
    try:
        from ..vesum_client import VesumClient
        client = VesumClient()

        if client.is_running():
            return {
                'running': True,
                'message': 'VESUM container running, validation enabled'
            }
        else:
            return {
                'running': False,
                'message': 'VESUM container not running, validation skipped'
            }
    except ImportError:
        return {
            'running': False,
            'message': 'VESUM client not available'
        }
