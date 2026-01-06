#!/usr/bin/env python3
"""
MDX Generator for Docusaurus

Converts curriculum markdown modules to MDX format with React components.

Usage:
    python scripts/generate_mdx.py [lang_pair] [level] [module_num] [--validate]

Examples:
    python scripts/generate_mdx.py l2-uk-en              # All levels
    python scripts/generate_mdx.py l2-uk-en a1           # All A1 modules
    python scripts/generate_mdx.py l2-uk-en a1 5         # Module 5 only
    python scripts/generate_mdx.py l2-uk-en --validate   # Generate + validate
"""

import re
import sys
import json
import yaml
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

# Add current dir to path for imports
SCRIPT_DIR = Path(__file__).parent
sys.path.append(str(SCRIPT_DIR))
from yaml_activities import ActivityParser, Activity

# Paths
PROJECT_ROOT = SCRIPT_DIR.parent
CURRICULUM_DIR = PROJECT_ROOT / "curriculum"
DOCUSAURUS_DIR = PROJECT_ROOT / "docusaurus" / "docs"

def dump_json_for_jsx(data):
    """Dump JSON string escaped for use inside a JSX template literal."""
    s = json.dumps(data, ensure_ascii=False)
    # Escape backslashes first to avoid double escaping other chars
    s = s.replace('\\', '\\\\')
    # Escape backticks for template literals
    s = s.replace('`', '\\`')
    # Escape $ to avoid template interpolation
    s = s.replace('${', '\\${')
    return s

# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class QuizQuestion:
    question: str
    options: list[dict]  # [{"text": str, "correct": bool}]

@dataclass
class MatchPair:
    left: str
    right: str

@dataclass
class FillInItem:
    sentence: str
    answer: str
    options: list[str]

@dataclass
class TrueFalseItem:
    statement: str
    is_true: bool
    explanation: str

@dataclass
class UnjumbleItem:
    jumbled: str
    answer: str

@dataclass
class GroupSortData:
    groups: dict[str, list[str]]  # {group_name: [items]}

@dataclass
class AnagramItem:
    scrambled: str
    answer: str
    hint: str

@dataclass
class ErrorCorrectionItem:
    sentence: str
    errorWord: str
    correctForm: str
    options: list[str]
    explanation: str

@dataclass
class ClozeData:
    passage: str
    blanks: list[dict]  # [{"answer": str, "options": list[str]}]

@dataclass
class SelectQuestion:
    question: str
    options: list[dict]  # [{"text": str, "correct": bool}]

@dataclass
class TranslateQuestion:
    source: str
    options: list[dict]  # [{"text": str, "correct": bool}]

@dataclass
class MarkTheWordsItem:
    text: str  # Plain text with marks removed
    correctWords: list[str]  # List of correct words to mark

@dataclass
class MorphemeItem:
    word: str  # The full word containing the morpheme
    morpheme: str  # The morpheme to highlight within the word
    type: str = 'unknown'  # prefix, root, or suffix

@dataclass
class HighlightMorphemesItem:
    text: str  # Plain text with asterisks removed
    morphemes: list[MorphemeItem]  # List of morphemes to highlight
    instruction: str = ''  # Optional instruction text

@dataclass
class EssayResponseData:
    prompt: str
    modelAnswer: str
    rubric: str

@dataclass
class ComparativeStudyData:
    content: str
    task: str
    modelAnswer: str

# =============================================================================
# UTILITIES
# =============================================================================

def escape_jsx(text: str) -> str:
    """Escape text for use in JSX strings (both template literals and double quotes)."""
    if not text:
        return ''
    # Convert to string if not already (handles int/float from YAML)
    if not isinstance(text, str):
        text = str(text)
    # Escape backslashes first, then other special chars
    text = text.replace('\\', '\\\\')
    text = text.replace('`', '\\`')
    text = text.replace('"', '\\"')
    text = text.replace('${', '\\${')
    return text

def fix_html_for_jsx(text: str) -> str:
    """Convert HTML tags to JSX-compatible self-closing format."""
    # Convert <br> to <br />
    text = re.sub(r'<br\s*/?>', '<br />', text)
    # Convert <hr> to <hr />
    text = re.sub(r'<hr\s*/?>', '<hr />', text)
    # Convert <img ...> to <img ... />
    text = re.sub(r'<img([^>]*?)(?<!/)>', r'<img\1 />', text)
    return text

def parse_frontmatter(content: str) -> tuple[dict, str]:
    """Extract YAML frontmatter and body from markdown."""
    lines = content.split('\n')
    if not lines or lines[0] != '---':
        return {}, content

    end_idx = -1
    for i, line in enumerate(lines[1:], 1):
        if line == '---':
            end_idx = i
            break

    if end_idx == -1:
        return {}, content

    yaml_content = '\n'.join(lines[1:end_idx])
    body = '\n'.join(lines[end_idx + 1:])

    try:
        fm = yaml.safe_load(yaml_content) or {}
    except yaml.YAMLError:
        fm = {}

    return fm, body

# =============================================================================
# YAML ACTIVITY SUPPORT
# =============================================================================

def yaml_activities_to_jsx(activities: list[Activity], is_ukrainian_forced: bool = False) -> str:
    """Convert YAML activities to JSX components using the shared ActivityParser."""
    parser = ActivityParser()
    return parser.to_mdx(activities, is_ukrainian_forced)

# =============================================================================
# ACTIVITY PARSERS
# =============================================================================

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
        elif not stripped.startswith('-'):
            if not options:  # Still building question
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

        # Check for numbered answer line (e.g., "1. від | для | про" or "1. від")
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

# =============================================================================
# JSX GENERATORS
# =============================================================================

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
    - *prefix*rest (e.g., *при*йшов)
    - rest*suffix* (e.g., Чит*ач*)

    DOES NOT match mark-the-words patterns:
    - space *word* space (e.g., " *другові* ")

    Key distinction: Morpheme patterns have Cyrillic letters touching at least one asterisk.
    """
    # Find all *...* patterns with context
    # Check if Cyrillic letters are adjacent to the asterisks
    # Morpheme: [а-я]*X* or *X*[а-я] (Cyrillic touching asterisk)
    # Mark-the-words: [^а-я]*X*[^а-я] (no Cyrillic touching asterisks)

    # Pattern: match *...* with one character before and after for context
    matches = list(re.finditer(r'(.?)\*([а-яіїєґА-ЯІЇЄҐ\s]+)\*(.?)', content, re.IGNORECASE))

    for match in matches:
        before = match.group(1)  # Character before opening *
        inside = match.group(2)  # Content between * *
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
    - *prefix*rest (e.g., *при*йшов → highlight "при" in "прийшов")
    - rest*suffix* (e.g., Чит*ач* → highlight "ач" in "Читач")
    - *wholeWord* (e.g., *Читач* → highlight entire word "Читач")
    - *multi-word phrase* (e.g., *Мені більше подобається* → highlight entire phrase)

    If the first line has no morphemes, treat it as an instruction.
    """
    morphemes = []
    instruction = ''

    # Check if first line is an instruction (no morphemes)
    lines = content.strip().split('\n')
    first_line = lines[0] if lines else ''

    # Pattern: (prefix)*morpheme*(suffix)
    # Group 1: optional text before * (prefix of word)
    # Group 2: morpheme inside * * (can be single word or multi-word phrase)
    # Group 3: optional text after * (suffix of word)
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
            # Skip the callout header itself? No, we might want to keep the content inside
            # But the callout syntax is handled by convert_callouts? 
            # No, if we wrap it in a component, we want the RAW content inside the callout
            # to pass as a prop.
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
    # Split by Task/Assignment header if possible, or just extract model answer
    # Structure: 
    # Content (Tables/Text)
    # **Task:** ...
    # > [!model-answer]
    
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
        
        # Detect task header (bold "Task:" or "Завдання:")
        if current_section == 'content' and re.match(r'\*\*(Task|Завдання).*?:?\*\*', stripped, re.IGNORECASE):
            current_section = 'task'
            task_lines.append(line) # Keep the header line as part of task
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

def highlight_morphemes_to_jsx(item: HighlightMorphemesItem, title: str, is_ukrainian_forced: bool = False) -> str:
    """Convert morpheme highlighting item to JSX HighlightMorphemesActivity component."""
    if not item.morphemes:
        return ''

    # Build morphemes array for JSX
    morphemes_jsx_parts = []
    for m in item.morphemes:
        morphemes_jsx_parts.append(
            f'{{ word: `{escape_jsx(m.word)}`, morpheme: `{escape_jsx(m.morpheme)}`, type: `{m.type}` }}'
        )

    morphemes_jsx = ',\n    '.join(morphemes_jsx_parts)

    instruction_jsx = ''
    if item.instruction:
        instruction_jsx = f'\n  instruction={{`{escape_jsx(item.instruction)}`}}'

    return f'''### {title}

<HighlightMorphemes isUkrainian={{{'true' if is_ukrainian_forced else 'false'}}}>
  <HighlightMorphemesActivity{instruction_jsx}
    text={{`{escape_jsx(item.text)}`}}
    morphemes={{[
    {morphemes_jsx}
  ]}}
  />
</HighlightMorphemes>'''

def essay_response_to_jsx(data: EssayResponseData, title: str, is_ukrainian_forced: bool = False) -> str:
    """Convert essay-response data to JSX EssayResponse component."""
    return f'''### {title}

<EssayResponse
  title="{escape_jsx(title)}"
  prompt={{`{escape_jsx(data.prompt)}`}}
  modelAnswer={{`{escape_jsx(data.modelAnswer)}`}}
  rubric={{`{escape_jsx(data.rubric)}`}}
  isUkrainian={{{'true' if is_ukrainian_forced else 'false'}}}
/>'''

def comparative_study_to_jsx(data: ComparativeStudyData, title: str, is_ukrainian_forced: bool = False) -> str:
    """Convert comparative-study data to JSX ComparativeStudy component."""
    return f'''### {title}

<ComparativeStudy
  title="{escape_jsx(title)}"
  content={{`{escape_jsx(data.content)}`}}
  task={{`{escape_jsx(data.task)}`}}
  modelAnswer={{`{escape_jsx(data.modelAnswer)}`}}
  isUkrainian={{{'true' if is_ukrainian_forced else 'false'}}}
/>'''

# =============================================================================
# CONTENT PROCESSING
# =============================================================================

# Callout mapping
CALLOUT_MAP = {
    'tip': {'type': 'tip'},
    'note': {'type': 'note'},
    'warning': {'type': 'warning'},
    'important': {'type': 'warning'},
    'caution': {'type': 'caution'},
    'info': {'type': 'info'},
    'observe': {'type': 'tip', 'icon': '🔍', 'title': 'Pattern Discovery'},
    'resources': {'type': 'info', 'icon': '🎧', 'title': 'External Resources'},
    'example': {'type': 'info', 'icon': '📝', 'title': 'Example'},
    'conversation': {'type': 'note', 'icon': '💬', 'title': 'Conversation'},
    'summary': {'type': 'note', 'icon': '📋', 'title': 'Summary'},
    'solution': {'type': 'solution'},  # Collapsible answer reveal for checkpoints
    'model-answer': {'type': 'success', 'icon': '✅', 'title': 'Model Answer'},
    'rubric': {'type': 'info', 'icon': '📊', 'title': 'Rubric'},
    'analysis': {'type': 'info', 'icon': '🧐', 'title': 'Analysis'},
    'history-bite': {'type': 'info', 'icon': '🕰️', 'title': 'History Bite'},
    'myth-buster': {'type': 'danger', 'icon': '🛡️', 'title': 'Myth Buster'},
    'quote': {'type': 'note', 'icon': '📜', 'title': 'Quote'},
    'context': {'type': 'info', 'icon': '🌍', 'title': 'Context'},
    'legacy': {'type': 'tip', 'icon': '💎', 'title': 'Legacy'},
    'reflection': {'type': 'info', 'icon': '🤔', 'title': 'Reflection'},
    'source': {'type': 'note', 'icon': '📖', 'title': 'Source'},
}

def convert_callouts(content: str) -> str:
    """Convert GitHub-style callouts to Docusaurus admonitions."""
    lines = content.split('\n')
    result = []
    i = 0

    while i < len(lines):
        line = lines[i]

        # Check for callout start: > [!type] (may have leading whitespace)
        # Allow hyphens in type (e.g. model-answer)
        callout_match = re.match(r'^(\s*)>\s*\[!([\w-]+)\]\s*(.*)', line)
        if callout_match:
            indent = callout_match.group(1)  # Preserve indentation for output
            callout_type = callout_match.group(2).lower()
            title_extra = callout_match.group(3).strip()

            config = CALLOUT_MAP.get(callout_type, {'type': 'note'})
            admon_type = config['type']

            # Build title
            if title_extra:
                title = title_extra
            elif 'title' in config:
                icon = config.get('icon', '')
                title = f"{icon} {config['title']}" if icon else config['title']
            else:
                title = callout_type.title()

            # Collect callout content - check for continuation lines (indented blockquotes too)
            callout_lines = []
            i += 1
            while i < len(lines):
                # Match continuation: optional whitespace + > + content
                cont_match = re.match(r'^\s*>(.*)', lines[i])
                if cont_match:
                    callout_lines.append(cont_match.group(1).strip() if cont_match.group(1) else '')
                    i += 1
                else:
                    break

            # Special handling for solution callouts - use HTML details for collapsible
            if callout_type == 'solution':
                result.append(f'<details className="solution-block">')
                result.append(f'<summary>{title}</summary>')
                result.append('')
                result.extend(callout_lines)
                result.append('')
                result.append('</details>')
                result.append('')
            else:
                # Output Docusaurus admonition
                result.append(f':::{admon_type}[{title}]')
                result.extend(callout_lines)
                result.append(':::')
                result.append('')
        else:
            result.append(line)
            i += 1

    return '\n'.join(result)

def process_story_sections(content: str) -> str:
    """Add blank lines between narrative lines in story sections.

    Story sections (### Story Time, ### Dialogue, etc.) contain narrative
    paragraphs that need blank lines between them for proper Markdown rendering.
    This function detects story headers and adds blank lines between non-blank
    lines until the next header.

    Note: Dialog lines (starting with —) are left consecutive so that
    process_dialogues can wrap them in conversation containers.
    """
    lines = content.split('\n')
    result = []
    i = 0

    # Pattern to detect story section headers
    story_header_pattern = re.compile(r'^###\s+(Story|Dialogue|Reading|Conversation|Text|Passage)', re.IGNORECASE)
    # Pattern to detect any header (to know when story section ends)
    any_header_pattern = re.compile(r'^#{1,4}\s+')

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Check if this is a story section header
        if story_header_pattern.match(stripped):
            result.append(line)
            result.append('')
            i += 1

            # Process lines until next header or end of content
            while i < len(lines):
                current_line = lines[i]
                current_stripped = current_line.strip()

                # Stop at next header
                if any_header_pattern.match(current_stripped):
                    break

                # Skip already-blank lines
                if not current_stripped:
                    result.append(current_line)
                    i += 1
                    continue

                # Add the line
                result.append(current_line)

                # Look ahead - if next line is non-blank content (not a header, not blank),
                # add a blank line after current line UNLESS both lines are dialog lines (—)
                if i + 1 < len(lines):
                    next_stripped = lines[i + 1].strip()
                    current_is_dialog = current_stripped.startswith('—')
                    next_is_dialog = next_stripped.startswith('—')

                    # Add blank line only if NOT both dialog lines
                    if next_stripped and not any_header_pattern.match(next_stripped):
                        if not (current_is_dialog and next_is_dialog):
                            result.append('')

                i += 1
        else:
            result.append(line)
            i += 1

    return '\n'.join(result)


def process_dialogues(content: str) -> str:
    """Group consecutive dialog lines into conversation blocks.

    Detects sequences of lines starting with em-dash (—) and wraps
    them in a styled conversation container. Separates Ukrainian
    from English translations (they're separated by blank lines).
    """
    lines = content.split('\n')
    result = []
    i = 0

    # Track if we're inside a JSX component
    inside_jsx = 0

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Track JSX component depth
        if re.match(r'^<[A-Z][a-zA-Z]*', stripped):
            inside_jsx += 1
        if stripped.endswith('/>'):
            inside_jsx = max(0, inside_jsx - 1)
        if re.match(r'^</[A-Z]', stripped):
            inside_jsx = max(0, inside_jsx - 1)

        # Check if this starts a dialog sequence (outside JSX)
        if stripped.startswith('—') and inside_jsx == 0 and '`' not in line:
            # Collect consecutive dialog lines (stop at blank line)
            dialog_lines = []
            while i < len(lines):
                current = lines[i].strip()
                if current.startswith('—') and '`' not in lines[i]:
                    dialog_lines.append(lines[i])
                    i += 1
                else:
                    # Stop at any non-dialog line (including blank)
                    break

            # Only wrap if we have 2+ dialog lines (actual conversation)
            if len(dialog_lines) >= 2:
                result.append('<div className="conversation">')
                result.append('')
                for dl in dialog_lines:
                    result.append(dl)
                    result.append('')
                result.append('</div>')
            else:
                # Single line - just keep as-is
                for dl in dialog_lines:
                    result.append(dl)
        else:
            result.append(line)
            i += 1

    return '\n'.join(result)

# =============================================================================
# MDX GENERATOR
# =============================================================================

def generate_mdx(md_content: str, module_num: int, yaml_activities: list[Activity] | None = None, meta_data: dict | None = None, vocab_items: list[dict] | None = None, external_resources: dict | None = None, level: str = 'a1') -> str:
    """Convert markdown content to MDX.

    Args:
        md_content: Markdown content
        module_num: Module number for sidebar
        yaml_activities: Optional list of activities from ActivityParser (takes precedence over embedded)
        meta_data: Optional metadata from YAML (replaces frontmatter)
        vocab_items: Optional vocab list from YAML
        external_resources: Optional external resources dict (injected from YAML)
        level: Current level (used for specialized formatting like LIT)
    """
    if meta_data:
        fm = meta_data
        body = md_content # MD file is already stripped if meta exists (usually)
        # But if we are transitioning, MD might still have FM. 
        # parse_frontmatter splits it regardless.
        _, body = parse_frontmatter(md_content)
    else:
        fm, body = parse_frontmatter(md_content)

    # Determine if Ukrainian headers are forced
    is_ukrainian_forced = False
    lvl = level.lower()
    if lvl in ['b2', 'c1', 'c2', 'lit']:
        is_ukrainian_forced = True
    elif lvl == 'b1' and module_num > 5:
        is_ukrainian_forced = True

    # Component imports
    imports = """import Quiz from '@site/src/components/Quiz';
import MatchUp from '@site/src/components/MatchUp';
import FillIn from '@site/src/components/FillIn';
import TrueFalse from '@site/src/components/TrueFalse';
import Unjumble from '@site/src/components/Unjumble';
import GroupSort from '@site/src/components/GroupSort';
import Anagram from '@site/src/components/Anagram';
import ErrorCorrection, { ErrorCorrectionItem } from '@site/src/components/ErrorCorrection';
import Cloze from '@site/src/components/Cloze';
import Select from '@site/src/components/Select';
import Translate from '@site/src/components/Translate';
import MarkTheWords, { MarkTheWordsActivity } from '@site/src/components/MarkTheWords';
import HighlightMorphemes, { HighlightMorphemesActivity } from '@site/src/components/HighlightMorphemes';
import EssayResponse from '@site/src/components/EssayResponse';
import ComparativeStudy from '@site/src/components/ComparativeStudy';"""

    # Frontmatter
    frontmatter = f'''---
sidebar_position: {module_num}
sidebar_label: "{str(module_num).zfill(2)}. {escape_jsx(fm.get('title', 'Untitled'))}"
title: "{escape_jsx(fm.get('title', 'Untitled'))}"
description: "{escape_jsx(fm.get('subtitle', ''))}"
---
'''

    # Inject Vocabulary Table if present
    if vocab_items:
        vocab_header = "Словник" if is_ukrainian_forced else "Vocabulary"
        if level.lower() == 'lit':
            vocab_md = _lit_vocab_items_to_markdown(vocab_items, vocab_header)
        else:
            vocab_md = _vocab_items_to_markdown(vocab_items, vocab_header)
            
        # Append to end of body (Standard Layout: Content -> Activities -> Vocabulary)
        body = body + '\n\n' + vocab_md

    # Process activities
    if yaml_activities:
        # Use YAML activities - inject them into the body
        act_header = "Вправи" if is_ukrainian_forced else "Activities"
        activities_jsx = f'## 🎯 {act_header}\n\n' + yaml_activities_to_jsx(yaml_activities, is_ukrainian_forced)
        # Remove any existing Activities section from body
        body = re.sub(
            r'(^#{1,2}\s+(?:Activities|Вправи(?:\s*\(Activities\))?))\n([\s\S]*?)(?=\n#{1,2}\s+(?:Vocabulary|Словник|Summary|Підсумок|Self-Assessment|Самооцінка|External|Зовнішні|Resources|Ресурси)|\Z)',
            '',
            body,
            flags=re.MULTILINE
        )
        # Find where to inject activities (before Vocabulary/Словник or Self-Assessment/External)
        # Avoid injecting before Summary (Intro)
        inject_match = re.search(r'\n(#{1,2}\s+(?:Vocabulary|Словник|Self-Assessment|Самооцінка|External|Зовнішні))', body)
        if inject_match:
            processed = body[:inject_match.start()] + '\n\n' + activities_jsx + '\n' + body[inject_match.start():]
        else:
            # Append at end if no Vocabulary/Summary section
            processed = body + '\n\n' + activities_jsx
    else:
        # No YAML activities found
        processed = body

    # Convert callouts
    processed = convert_callouts(processed)

    # Fix HTML for JSX compatibility (self-closing tags)
    processed = fix_html_for_jsx(processed)

    # Process story sections (add blank lines between narrative lines)
    processed = process_story_sections(processed)

    # Process dialogues (wrap em-dash lines in conversation divs)
    processed = process_dialogues(processed)

    # Remove duplicate H1 title
    processed = re.sub(r'^#\s+[^\n]+\n', '', processed, count=1)

    # Add emojis to H2 section headings for TOC (Standardize to H2 for Docusaurus)
    
    header_map = {
        'Summary': 'Підсумок',
        'Vocabulary': 'Словник',
        'Self-Assessment': 'Самооцінка',
        'External Resources': 'Зовнішні ресурси'
    }

    # Summary
    sum_text = header_map['Summary'] if is_ukrainian_forced else r'\1'
    processed = re.sub(r'^#{1,2} (Summary|Підсумок)', f'## 📋 {sum_text}', processed, flags=re.MULTILINE)
    
    # Vocabulary
    vocab_text = header_map['Vocabulary'] if is_ukrainian_forced else r'\1'
    processed = re.sub(r'^#{1,2} (Vocabulary|Словник)', f'## 📚 {vocab_text}', processed, flags=re.MULTILINE)
    
    # Self-Assessment
    sa_text = header_map['Self-Assessment'] if is_ukrainian_forced else r'\1'
    processed = re.sub(r'^#{1,2} (Self-Assessment|Самооцінка)', f'## ✅ {sa_text}', processed, flags=re.MULTILINE)
    
    # External Resources
    ext_text = header_map['External Resources'] if is_ukrainian_forced else r'\1'
    processed = re.sub(r'^#{1,2} (External Resources?|Зовнішні ресурси|Resources|Ресурси)', f'## 🔗 {ext_text}', processed, flags=re.MULTILINE)

    # Inject external resources from YAML (if present)
    if external_resources:
        resources_md = format_resources_for_mdx(external_resources, is_ukrainian_forced)
        if resources_md:
            # Append at end of content
            processed = processed.rstrip() + '\n\n' + resources_md

    # Build MDX
    parts = [frontmatter, imports, '', processed]

    return '\n'.join(parts)

# =============================================================================
# EXTERNAL RESOURCES
# =============================================================================

def validate_and_clean_url(url: str, title: str = '') -> str:
    """
    Validate and clean URL for markdown link formatting.

    Detects and fixes common URL issues:
    - Incomplete angle brackets: <https://...  → https://...
    - Unmatched parentheses in URL

    Args:
        url: The URL string to validate
        title: Optional title for error messages

    Returns:
        Cleaned URL string

    Raises:
        Warning if URL has issues
    """
    if not url:
        return url

    original_url = url

    # Remove angle brackets if present (not needed in YAML, causes issues)
    if url.startswith('<'):
        if not url.endswith('>'):
            print(f"  ⚠️  Malformed URL (missing closing '>'): {title}")
            print(f"      {url}")
            url = url.lstrip('<')
        else:
            url = url[1:-1]  # Remove both angle brackets

    # Check for unmatched parentheses
    open_parens = url.count('(')
    close_parens = url.count(')')
    if open_parens != close_parens:
        print(f"  ⚠️  URL has unmatched parentheses: {title}")
        print(f"      {url}")
        print(f"      Expected {open_parens} closing parentheses, found {close_parens}")

    if url != original_url:
        print(f"      Fixed to: {url}")

    return url

def format_resources_for_mdx(resources: dict, is_ukrainian_forced: bool = False) -> str:
    """
    Format external resources for MDX output (emoji template).

    Args:
        resources: Dict with keys: podcasts, youtube, articles, books, websites
        is_ukrainian_forced: Whether to force Ukrainian headers

    Returns:
        Formatted markdown string for [!resources] callout block
    """
    if not resources or not any(resources.get(t) for t in ['podcasts', 'youtube', 'articles', 'books', 'websites']):
        return ""

    header_title = "Зовнішні ресурси" if is_ukrainian_forced else "External Resources"
    
    lines = []
    lines.append(f"> [!resources] 🔗 {header_title}")
    lines.append(">")

    # Emoji icons per resource type
    display_names = {
        'Podcasts': 'Подкасти',
        'YouTube': 'YouTube',
        'Articles': 'Статті',
        'Books': 'Книги',
        'Websites': 'Сайти'
    }

    resource_config = [
        ('podcasts', '🎧', 'Podcasts'),
        ('youtube', '📺', 'YouTube'),
        ('articles', '📖', 'Articles'),
        ('books', '📚', 'Books'),
        ('websites', '🌐', 'Websites')
    ]

    # Priority and relevance maps for sorting
    # Priority 1 = highest (Ukrainian Lessons Priority 1), 5 = lowest
    priority_map = {1: 5, 2: 4, 3: 3, 4: 2, 5: 1, None: 0}
    relevance_priority = {'high': 3, 'medium': 2, 'low': 1}

    for resource_type, icon, display_name in resource_config:
        items = resources.get(resource_type, [])
        if not items:
            continue
            
        final_display_name = display_names.get(display_name, display_name) if is_ukrainian_forced else display_name

        # Sort by: priority (1→5, highest first) → relevance (high→low) → title (A→Z)
        sorted_items = sorted(
            items,
            key=lambda x: (
                -priority_map.get(x.get('priority'), 0),  # Priority 1 appears first
                -relevance_priority.get(x.get('relevance', 'low'), 0),  # High relevance next
                x.get('title', '').lower()  # Alphabetical last
            )
        )

        # Add section header
        lines.append(f"> **{icon} {final_display_name}:**")

        # Format each item
        for item in sorted_items:
            title = item.get('title', 'Unknown')
            url = validate_and_clean_url(item.get('url', ''), title)

            if resource_type == 'podcasts':
                desc = item.get('match_reason') or item.get('description', '')
                if desc:
                    lines.append(f"> - [{title}]({url}) — {desc}")
                else:
                    lines.append(f"> - [{title}]({url})")

            elif resource_type == 'youtube':
                channel = item.get('channel', '')
                desc = item.get('description', channel)
                if desc:
                    lines.append(f"> - [{title}]({url}) — {desc}")
                else:
                    lines.append(f"> - [{title}]({url})")

            elif resource_type == 'articles':
                source = item.get('source', '')
                desc = item.get('description', source)
                if desc:
                    lines.append(f"> - [{title}]({url}) — {desc}")
                else:
                    lines.append(f"> - [{title}]({url})")

            elif resource_type == 'books':
                author = item.get('author', 'Unknown')
                pages = item.get('pages', '')
                desc = item.get('description', '')

                parts = [f"{title} by {author}"]
                if pages:
                    parts.append(f"(pages: {pages})")
                if desc:
                    parts.append(f"— {desc}")
                lines.append(f"> - {' '.join(parts)}")

            elif resource_type == 'websites':
                source = item.get('source', '')
                desc = item.get('description', source)
                if desc:
                    lines.append(f"> - [{title}]({url}) — {desc}")
                else:
                    lines.append(f"> - [{title}]({url})")

        # Add blank line between sections
        lines.append(">")

    # Remove trailing blank line
    if lines and lines[-1] == ">":
        lines.pop()

    return '\n'.join(lines)

# =============================================================================
# MAIN
# =============================================================================

def _vocab_items_to_markdown(items: list[dict], header_text: str = "Vocabulary") -> str:
    lines = [
        f"## {header_text}",
        "",
        "| Word | IPA | English | POS | Gender | Note |",
        "| --- | --- | --- | --- | --- | --- |"
    ]
    for item in items:
        # Map gender m/f/n -> ч/ж/с
        g_map = {'m': 'ч', 'f': 'ж', 'n': 'с', 'pl': 'pl', '-': '-', '': ''}
        raw_g = item.get('gender', '')
        g_val = g_map.get(raw_g, raw_g)
        
        # Map POS propn -> name
        raw_p = item.get('pos', '')
        p_val = 'name' if raw_p == 'propn' else raw_p
        
        line = f"| {item.get('lemma')} | {item.get('ipa','')} | {item.get('translation','')} | {p_val} | {g_val} | {item.get('usage','')} |"
        lines.append(line)
        
    return '\n'.join(lines)

def main():
    args = sys.argv[1:]

    # Parse --validate flag
    validate_after = '--validate' in args
    args = [a for a in args if a != '--validate']

    lang_pair = args[0] if args else 'l2-uk-en'
    target_level = args[1].lower() if len(args) > 1 else None
    target_module = int(args[2]) if len(args) > 2 else None

    print('\n🚀 MDX Generator (Python)\n', flush=True)
    print(f'Source: curriculum/{lang_pair}/', flush=True)
    print(f'Output: docusaurus/docs/\n', flush=True)

    # Load EXTERNAL RESOURCES (YAML Architecture) - loaded once for all modules
    external_resources_file = PROJECT_ROOT / 'docs' / 'resources' / 'external_resources.yaml'
    all_resources = {}
    if external_resources_file.exists():
        with open(external_resources_file, 'r', encoding='utf-8') as f:
            resources_data = yaml.safe_load(f)
            all_resources = resources_data.get('resources', {})
        print(f'📚 Loaded {len(all_resources)} modules with external resources\n', flush=True)

    curriculum_path = CURRICULUM_DIR / lang_pair
    levels = ['a1', 'a2', 'b1', 'b2', 'c1', 'c2', 'lit']

    for level in levels:
        if target_level and level != target_level:
            continue

        level_path = curriculum_path / level
        if not level_path.exists():
            continue

        # Get module files
        module_files = sorted(level_path.glob('*.md'))
        if not module_files:
            continue

        print(f'📁 Level {level.upper()} ({len(module_files)} modules)')

        # Ensure output directory
        output_dir = DOCUSAURUS_DIR / level
        output_dir.mkdir(parents=True, exist_ok=True)

        for md_file in module_files:
            # Extract module number from filename (e.g., "01-intro.md" -> 1)
            match = re.match(r'^(\d+)', md_file.name)
            if not match:
                continue

            module_num = int(match.group(1))

            if target_module and module_num != target_module:
                continue

            # Read and convert
            md_content = md_file.read_text(encoding='utf-8')
            
            # Load META (YAML Architecture)
            meta_file = md_file.parent / 'meta' / (md_file.stem + '.yaml')
            meta_data = None
            if meta_file.exists():
                with open(meta_file, 'r', encoding='utf-8') as f:
                    meta_data = yaml.safe_load(f)
                    
            # Load VOCABULARY (YAML Architecture)
            vocab_file = md_file.parent / 'vocabulary' / (md_file.stem + '.yaml')
            vocab_items = None
            if vocab_file.exists():
                with open(vocab_file, 'r', encoding='utf-8') as f:
                    v_data = yaml.safe_load(f)
                    if v_data and 'items' in v_data:
                        vocab_items = v_data['items']

            # Check for YAML activities file
            # New structure: activities/{module}.yaml
            # Legacy: {module}.activities.yaml
            yaml_file = md_file.parent / 'activities' / (md_file.stem + '.yaml')
            if not yaml_file.exists():
                yaml_file = md_file.parent / (md_file.stem + '.activities.yaml')
            
            yaml_activities = None
            if yaml_file.exists():
                parser = ActivityParser()
                try:
                    yaml_activities = parser.parse(yaml_file)
                    if yaml_activities:
                        print(f'    📋 Loading {len(yaml_activities)} activities from YAML')
                except Exception as e:
                    print(f'    ⚠️ Error parsing YAML activities: {e}')

            # Lookup EXTERNAL RESOURCES by module_id
            # module_id format: {level}-{filename} (e.g., a1-09-food-and-drinks)
            module_id = f"{level}-{md_file.stem}"
            module_resources = all_resources.get(module_id, {})
            if module_resources:
                resource_count = sum(len(module_resources.get(t, [])) for t in ['podcasts', 'youtube', 'articles', 'books', 'websites'])
                print(f'    🔗 Loading {resource_count} external resources from YAML')

            mdx_content = generate_mdx(md_content, module_num, yaml_activities, meta_data, vocab_items, module_resources, level)

            # Write output
            output_file = output_dir / f'module-{str(module_num).zfill(2)}.mdx'
            output_file.write_text(mdx_content, encoding='utf-8')

            print(f'  ✓ Module {str(module_num).zfill(2)}')

    print('\n✅ MDX generation complete!')

    # Run validation if --validate flag was set
    if validate_after:
        print('\n' + '=' * 50)
        print('Running MDX validation...\n')
        import subprocess
        validate_args = [sys.executable, str(SCRIPT_DIR / 'validate_mdx.py'), lang_pair]
        if target_level:
            validate_args.append(target_level)
        if target_module:
            validate_args.append(str(target_module))
        result = subprocess.run(validate_args)
        sys.exit(result.returncode)

# =============================================================================
# VOCABULARY HELPERS
# =============================================================================

def _lit_vocab_items_to_markdown(items: list[dict], header_text: str = "Vocabulary") -> str:
    lines = [
        f"## {header_text}",
        "",
        "| Термін/Слово | Переклад | Примітки |",
        "| --- | --- | --- |"
    ]
    for item in items:
        # Use lemma, translation, notes (standardized fields)
        lemma = item.get('lemma') or item.get('term', '')
        translation = item.get('translation') or item.get('definition', '')
        notes = item.get('notes') or item.get('comment', '')
        
        line = f"| **{lemma}** | {translation} | {notes} |"
        lines.append(line)
        
    return '\n'.join(lines)

if __name__ == '__main__':
    main()
