"""Activity content parsers for MDX generation.

Parses markdown-formatted activity content (quiz, match-up, fill-in,
true-false, unjumble, group-sort, anagram, error-correction, cloze,
select, translate, mark-the-words, highlight-morphemes, essay-response,
comparative-study) into typed dataclass structures.
"""

from __future__ import annotations

import re

from .dataclasses_ import (
    AnagramItem,
    ClozeData,
    ComparativeStudyData,
    ErrorCorrectionItem,
    EssayResponseData,
    FillInItem,
    GroupSortData,
    HighlightMorphemesItem,
    MarkTheWordsItem,
    MatchPair,
    MorphemeItem,
    QuizQuestion,
    SelectQuestion,
    TranslateQuestion,
    TrueFalseItem,
    UnjumbleItem,
)


def parse_quiz(content: str) -> list[QuizQuestion]:
    """Parse quiz activity with numbered questions or --- separated questions."""
    questions = []

    # Check if content has numbered format (1. question)
    has_numbered = bool(re.search(r'^\d+\.\s', content, flags=re.MULTILINE))

    if has_numbered:
        # Split by numbered items
        blocks = re.split(r'(?=^\d+\.\s)', content, flags=re.MULTILINE)
        for block in blocks:
            block = block.strip()
            if not block or not re.match(r'^\d+\.', block):
                continue
            block = re.sub(r'^\d+\.\s*', '', block)
            q = _parse_quiz_block(block)
            questions.extend(q)
    else:
        # Split by --- separators (horizontal rules)
        blocks = re.split(r'\n---+\n', content)
        for block in blocks:
            block = block.strip()
            if not block:
                continue
            q = _parse_quiz_block(block)
            questions.extend(q)

    return questions


def _parse_quiz_block(block: str) -> list[QuizQuestion]:
    """Parse a single quiz question block."""
    lines = block.strip().split('\n')
    question = ''
    options = []

    for line in lines:
        stripped = line.strip()
        # Check for option lines
        if stripped.startswith('- [x]'):
            options.append({"text": stripped[5:].strip(), "correct": True})
        elif stripped.startswith('- [ ]'):
            options.append({"text": stripped[5:].strip(), "correct": False})
        elif not stripped.startswith('-') and not options:  # Still building question
            question = (question + ' ' + stripped).strip()

    if options:
        return [QuizQuestion(question=question, options=options)]
    return []


def parse_match_up(content: str) -> list[MatchPair]:
    """Parse match-up activity with :: separator or table format."""
    pairs = []

    # Try :: separator format first
    for line in content.split('\n'):
        line = line.strip()
        if '::' in line:
            if line.startswith('- '):
                line = line[2:]
            parts = line.split('::', 1)
            if len(parts) == 2:
                pairs.append(MatchPair(left=parts[0].strip(), right=parts[1].strip()))

    if pairs:
        return pairs

    # Try table format (skip header row and separator)
    header_skipped = False
    for line in content.split('\n'):
        line = line.strip()
        if line.startswith('|') and '|' in line[1:]:
            cells = [c.strip() for c in line.split('|')[1:-1]]
            # Skip separator line (|---|---|)
            if cells and cells[0].startswith('-'):
                continue
            # Skip header row (first non-separator row)
            if not header_skipped:
                header_skipped = True
                continue
            if len(cells) >= 2 and cells[0] and cells[1]:
                pairs.append(MatchPair(left=cells[0], right=cells[1]))

    return pairs


def parse_fill_in(content: str) -> list[FillInItem]:
    """Parse fill-in activity with answer and options callouts."""
    items = []
    # Split by numbered items
    blocks = re.split(r'^\d+\.\s+', content, flags=re.MULTILINE)

    for block in blocks:
        if not block.strip():
            continue

        lines = block.split('\n')
        sentence = lines[0].strip() if lines else ''
        answer = ''
        options = []

        for line in lines[1:]:
            stripped = line.strip()
            if stripped.startswith('> [!answer]'):
                answer = stripped.replace('> [!answer]', '').strip()
            elif stripped.startswith('> [!options]'):
                opts_str = stripped.replace('> [!options]', '').strip()
                options = [o.strip() for o in opts_str.split('|')]

        if sentence and answer:
            items.append(FillInItem(sentence=sentence, answer=answer, options=options))

    return items


def parse_true_false(content: str) -> list[TrueFalseItem]:
    """Parse true-false activity with checkbox format."""
    items = []
    lines = content.split('\n')

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        if line.startswith('- [x]'):
            statement = line[5:].strip()
            explanation = ''
            # Check for explanation on next line
            if i + 1 < len(lines) and lines[i + 1].strip().startswith('>'):
                explanation = lines[i + 1].strip()[1:].strip()
                i += 1
            items.append(TrueFalseItem(statement=statement, is_true=True, explanation=explanation))
        elif line.startswith('- [ ]'):
            statement = line[5:].strip()
            explanation = ''
            if i + 1 < len(lines) and lines[i + 1].strip().startswith('>'):
                explanation = lines[i + 1].strip()[1:].strip()
                i += 1
            items.append(TrueFalseItem(statement=statement, is_true=False, explanation=explanation))

        i += 1

    return items


def parse_unjumble(content: str) -> list[UnjumbleItem]:
    """Parse unjumble activity with answer callouts."""
    items = []
    blocks = re.split(r'^\d+\.\s+', content, flags=re.MULTILINE)

    for block in blocks:
        if not block.strip():
            continue

        lines = block.split('\n')
        jumbled = lines[0].strip() if lines else ''
        answer = ''

        for line in lines[1:]:
            stripped = line.strip()
            if stripped.startswith('> [!answer]'):
                answer = stripped.replace('> [!answer]', '').strip()
                break

        if jumbled and answer:
            items.append(UnjumbleItem(jumbled=jumbled, answer=answer))

    return items


def parse_group_sort(content: str) -> GroupSortData:
    """Parse group-sort activity with ### group headers."""
    groups = {}
    current_group = None

    for line in content.split('\n'):
        stripped = line.strip()

        if stripped.startswith('### '):
            current_group = stripped[4:].strip()
            groups[current_group] = []
        elif stripped.startswith('- ') and current_group:
            groups[current_group].append(stripped[2:].strip())

    return GroupSortData(groups=groups)


def parse_anagram(content: str) -> list[AnagramItem]:
    """Parse anagram activity."""
    items = []
    blocks = re.split(r'^\d+\.\s+', content, flags=re.MULTILINE)

    for block in blocks:
        if not block.strip():
            continue

        lines = block.split('\n')
        scrambled = lines[0].strip() if lines else ''
        answer = ''
        hint = ''

        for line in lines[1:]:
            stripped = line.strip()
            if stripped.startswith('> [!answer]'):
                answer = stripped.replace('> [!answer]', '').strip()
            elif stripped.startswith('> [!hint]'):
                hint = stripped.replace('> [!hint]', '').strip()

        if scrambled and answer:
            items.append(AnagramItem(scrambled=scrambled, answer=answer, hint=hint))

    return items


def parse_error_correction(content: str) -> list[ErrorCorrectionItem]:
    """Parse error-correction activity."""
    items = []
    blocks = re.split(r'^\d+\.\s+', content, flags=re.MULTILINE)

    for block in blocks:
        if not block.strip():
            continue

        lines = block.split('\n')
        sentence = lines[0].strip() if lines else ''
        error_word = ''
        correct_form = ''
        options = []
        explanation = ''

        for line in lines[1:]:
            stripped = line.strip()
            if stripped.startswith('> [!error]'):
                error_word = stripped.replace('> [!error]', '').strip()
            elif stripped.startswith('> [!answer]') or stripped.startswith('> [!correct]'):
                correct_form = re.sub(r'^> \[!(answer|correct)\]\s*', '', stripped).strip()
            elif stripped.startswith('> [!options]'):
                opts_str = stripped.replace('> [!options]', '').strip()
                options = [o.strip() for o in opts_str.split('|') if o.strip()]
            elif stripped.startswith('> [!explanation]'):
                explanation = stripped.replace('> [!explanation]', '').strip()

        if sentence and error_word and correct_form:
            # Ensure correct_form is in options
            if options and correct_form not in options:
                options.append(correct_form)
            items.append(ErrorCorrectionItem(
                sentence=sentence,
                errorWord=error_word,
                correctForm=correct_form,
                options=options,
                explanation=explanation
            ))

    return items


def parse_cloze(content: str) -> ClozeData:
    """Parse cloze activity with passage and blanks.

    Format (new - inline options):
    - Passage with [___:N] markers for blanks
    - Numbered answer sections:
      N. opt1 | opt2 | opt3
         > [!answer] correct_answer

    Format (legacy - [!options] callout):
    - Passage with [___:N] markers for blanks
    - Numbered answer sections:
      N. default_answer
      > [!answer] correct_answer
      > [!options] opt1 | opt2 | opt3
    """
    lines = content.split('\n')
    passage_lines = []
    blanks = {}  # Use dict to maintain blank number order
    current_blank_num = None
    current_answer = None
    current_options = []

    # First pass: separate passage from answer blocks
    in_answers = False
    for line in lines:
        stripped = line.strip()

        # Check for numbered answer line (e.g., "1. vid | dlya | pro" or "1. vid")
        num_match = re.match(r'^(\d+)\.\s*(.*)$', stripped)
        if num_match:
            # Save previous blank if exists
            if current_blank_num is not None and current_answer:
                blanks[current_blank_num] = {"answer": current_answer, "options": current_options if current_options else [current_answer]}

            current_blank_num = int(num_match.group(1))
            default_val = num_match.group(2).strip()

            # Check if options are inline (new format: "1. opt1 | opt2 | opt3")
            if '|' in default_val:
                current_options = [o.strip() for o in default_val.split('|')]
                current_answer = current_options[0]  # First option as default answer
            else:
                current_answer = default_val  # Default answer from the line itself
                current_options = []

            in_answers = True
            continue

        # Parse answer callout (overrides default answer)
        if stripped.startswith('> [!answer]'):
            current_answer = stripped.replace('> [!answer]', '').strip()
            continue

        # Parse options callout (legacy format)
        if stripped.startswith('> [!options]'):
            opts = stripped.replace('> [!options]', '').strip()
            current_options = [o.strip() for o in opts.split('|')]
            continue

        # If we haven't started answers yet, it's passage
        if not in_answers:
            passage_lines.append(line)

    # Save last blank
    if current_blank_num is not None and current_answer:
        blanks[current_blank_num] = {"answer": current_answer, "options": current_options if current_options else [current_answer]}

    # Convert to ordered list
    blanks_list = []
    for i in sorted(blanks.keys()):
        blanks_list.append(blanks[i])

    return ClozeData(passage='\n'.join(passage_lines).strip(), blanks=blanks_list)


def parse_select(content: str) -> list[SelectQuestion]:
    """Parse select (multi-choice) activity."""
    questions = []
    blocks = re.split(r'^\d+\.\s+', content, flags=re.MULTILINE)

    for block in blocks:
        if not block.strip():
            continue

        lines = block.split('\n')
        question = ''
        options = []

        for line in lines:
            stripped = line.strip()
            if stripped.startswith('- [x]'):
                options.append({"text": stripped[5:].strip(), "correct": True})
            elif stripped.startswith('- [ ]'):
                options.append({"text": stripped[5:].strip(), "correct": False})
            elif not options and not stripped.startswith('-'):
                question = (question + ' ' + stripped).strip()

        if options:
            questions.append(SelectQuestion(question=question, options=options))

    return questions


def parse_translate(content: str) -> list[TranslateQuestion]:
    """Parse translate activity with checkbox or callout format."""
    questions = []
    blocks = re.split(r'^\d+\.\s+', content, flags=re.MULTILINE)

    for block in blocks:
        if not block.strip():
            continue

        lines = block.split('\n')
        source = ''
        options = []
        answer = ''
        option_texts = []

        for line in lines:
            stripped = line.strip()
            # Checkbox format
            if stripped.startswith('- [x]'):
                options.append({"text": stripped[5:].strip(), "correct": True})
            elif stripped.startswith('- [ ]'):
                options.append({"text": stripped[5:].strip(), "correct": False})
            # Callout format
            elif stripped.startswith('> [!answer]'):
                answer = stripped.replace('> [!answer]', '').strip()
            elif stripped.startswith('> [!options]'):
                option_texts = [o.strip() for o in stripped.replace('> [!options]', '').split('|')]
            elif not options and not option_texts and not stripped.startswith('-') and not stripped.startswith('>'):
                source = (source + ' ' + stripped).strip()

        # Convert callout format to options
        if answer and option_texts:
            for opt in option_texts:
                options.append({"text": opt, "correct": opt == answer})

        if options:
            questions.append(TranslateQuestion(source=source, options=options))

    return questions


def parse_mark_the_words(content: str) -> list[MarkTheWordsItem]:
    """Parse mark-the-words content into items.

    Format: [word](correct) or [word](category) marks correct words
    Each paragraph (separated by ---) is a separate item
    """
    items = []
    # Split by horizontal rule to get separate exercises
    paragraphs = re.split(r'\n---+\n', content.strip())

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        # Find all marked words: [word](category)
        correct_words = []
        pattern = r'\[([^\]]+)\]\([^)]+\)'
        for match in re.finditer(pattern, para):
            word = match.group(1).strip()
            correct_words.append(word)

        # Remove the markdown-style marks to get plain text
        plain_text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', para)

        if correct_words:
            items.append(MarkTheWordsItem(text=plain_text, correctWords=correct_words))

    return items


def has_morpheme_patterns(content: str) -> bool:
    """Detect if content uses morpheme highlighting patterns.

    Supports pattern types:
    - *prefix*rest (e.g., *pri*yshov)
    - rest*suffix* (e.g., Chyt*ach*)

    DOES NOT match mark-the-words patterns:
    - space *word* space (e.g., " *druhovi* ")

    Key distinction: Morpheme patterns have Cyrillic letters touching at least one asterisk.
    """
    # Find all *...* patterns with context
    # Check if Cyrillic letters are adjacent to the asterisks
    matches = list(re.finditer(r'(.?)\*([а-яіїєґА-ЯІЇЄҐ\s]+)\*(.?)', content, re.IGNORECASE))

    for match in matches:
        before = match.group(1)  # Character before opening *
        match.group(2)  # Content between * *
        after = match.group(3)   # Character after closing *

        # Check if Cyrillic letter touches either asterisk
        before_is_cyrillic = before and re.match(r'[а-яіїєґА-ЯІЇЄҐ]', before, re.IGNORECASE)
        after_is_cyrillic = after and re.match(r'[а-яіїєґА-ЯІЇЄҐ]', after, re.IGNORECASE)

        # Morpheme pattern: at least one side has Cyrillic touching the asterisk
        if before_is_cyrillic or after_is_cyrillic:
            return True

    return False


def parse_highlight_morphemes(content: str) -> HighlightMorphemesItem:
    """Parse morpheme highlighting content.

    Supports pattern types:
    - *prefix*rest (e.g., *pri*yshov -> highlight "pri" in "priyshov")
    - rest*suffix* (e.g., Chyt*ach* -> highlight "ach" in "Chytach")
    - *wholeWord* (e.g., *Chytach* -> highlight entire word "Chytach")
    - *multi-word phrase* (e.g., *Meni bilshe podobaietsia* -> highlight entire phrase)

    If the first line has no morphemes, treat it as an instruction.
    """
    morphemes = []
    instruction = ''

    # Check if first line is an instruction (no morphemes)
    lines = content.strip().split('\n')
    first_line = lines[0] if lines else ''

    # Pattern: (prefix)*morpheme*(suffix)
    pattern = r'([а-яіїєґА-ЯІЇЄҐ]*)\*([а-яіїєґА-ЯІЇЄҐ\s]+)\*([а-яіїєґА-ЯІЇЄҐ]*)'

    # If first line has no morphemes, it's likely an instruction
    if first_line and not re.search(pattern, first_line):
        instruction = first_line.strip()
        # Remove instruction from content
        content = '\n'.join(lines[1:]).strip()

    for match in re.finditer(pattern, content):
        prefix = match.group(1)      # Text before morpheme
        morpheme = match.group(2)    # The morpheme to highlight
        suffix = match.group(3)      # Text after morpheme

        # Construct the full word
        full_word = prefix + morpheme + suffix

        # Detect morpheme type based on position
        if not prefix and suffix:
            morph_type = 'prefix'
        elif prefix and not suffix:
            morph_type = 'suffix'
        elif not prefix and not suffix:
            morph_type = 'whole'
        else:
            morph_type = 'root'

        morphemes.append(MorphemeItem(
            word=full_word,
            morpheme=morpheme,
            type=morph_type
        ))

    # Remove asterisks to get plain text
    plain_text = re.sub(r'[а-яіїєґА-ЯІЇЄҐ]*\*([а-яіїєґА-ЯІЇЄҐ\s]+)\*[а-яіїєґА-ЯІЇЄҐ]*',
                        lambda m: m.group(0).replace('*', ''), content)

    return HighlightMorphemesItem(text=plain_text.strip(), morphemes=morphemes, instruction=instruction)


def parse_essay_response(content: str) -> EssayResponseData:
    """Parse essay-response activity."""
    prompt_lines = []
    model_answer_lines = []
    rubric_lines = []

    current_section = 'prompt'

    lines = content.split('\n')
    for line in lines:
        if line.strip().startswith('> [!model-answer]'):
            current_section = 'model'
            continue
        elif line.strip().startswith('> [!rubric]'):
            current_section = 'rubric'
            continue

        if current_section == 'prompt':
            prompt_lines.append(line)
        elif current_section == 'model':
            # Remove '>' prefix from callout content if present
            clean_line = re.sub(r'^>\s?', '', line)
            model_answer_lines.append(clean_line)
        elif current_section == 'rubric':
            clean_line = re.sub(r'^>\s?', '', line)
            rubric_lines.append(clean_line)

    return EssayResponseData(
        prompt='\n'.join(prompt_lines).strip(),
        modelAnswer='\n'.join(model_answer_lines).strip(),
        rubric='\n'.join(rubric_lines).strip()
    )


def parse_comparative_study(content: str) -> ComparativeStudyData:
    """Parse comparative-study activity."""
    content_lines = []
    task_lines = []
    model_lines = []

    current_section = 'content'

    lines = content.split('\n')
    for line in lines:
        stripped = line.strip()

        if stripped.startswith('> [!model-answer]'):
            current_section = 'model'
            continue

        # Detect task header (bold "Task:" or "Zavdannia:")
        if current_section == 'content' and re.match(r'\*\*(Task|Завдання).*?:?\*\*', stripped, re.IGNORECASE):
            current_section = 'task'
            task_lines.append(line)  # Keep the header line as part of task
            continue

        if current_section == 'content':
            content_lines.append(line)
        elif current_section == 'task':
            task_lines.append(line)
        elif current_section == 'model':
            clean_line = re.sub(r'^>\s?', '', line)
            model_lines.append(clean_line)

    return ComparativeStudyData(
        content='\n'.join(content_lines).strip(),
        task='\n'.join(task_lines).strip(),
        modelAnswer='\n'.join(model_lines).strip()
    )
