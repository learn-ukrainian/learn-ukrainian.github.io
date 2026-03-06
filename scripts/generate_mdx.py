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

from slug_utils import to_bare_slug

# Add current dir to path for imports
SCRIPT_DIR = Path(__file__).parent
sys.path.append(str(SCRIPT_DIR))
from yaml_activities import ActivityParser, Activity
from manifest_utils import get_module_by_slug

# Paths
PROJECT_ROOT = SCRIPT_DIR.parent
CURRICULUM_DIR = PROJECT_ROOT / "curriculum"
DOCUSAURUS_DIR = PROJECT_ROOT / "starlight" / "src" / "content" / "docs"

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
    """Escape text for use in JSX strings (both template literals and double quotes).
    
    Uses HTML entities for special chars to avoid JSX parsing errors.
    See issue #396 for details.
    """
    if not text:
        return ''
    # Convert to string if not already (handles int/float from YAML)
    if not isinstance(text, str):
        text = str(text)
    # Escape backslashes first
    text = text.replace('\\', '\\\\')
    text = text.replace('`', '\\`')
    text = text.replace('"', '&quot;')  # HTML entity
    text = text.replace('<', '&lt;')    # Escape <
    text = text.replace('>', '&gt;')    # Escape >
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

def detect_pipeline_info(level_dir: Path, slug: str) -> tuple[str | None, str | None]:
    """Detect pipeline version and build status from orchestration dir.

    Returns (pipeline_version, build_status) where:
      pipeline_version: "v4", "v3", or None (unbuilt)
      build_status: "draft", "validated", "reviewed", or None
    """
    orch_dir = level_dir / "orchestration" / slug

    # Detect version
    v4_file = orch_dir / "state-v4.json"
    v3_file = orch_dir / "state-v3.json"
    v2_file = orch_dir / "state.json"

    version = None
    phases = {}

    if v4_file.exists():
        version = "v4"
        try:
            data = json.loads(v4_file.read_text()) or {}
            phases = data.get("phases", {})
        except Exception:
            pass
    elif v3_file.exists():
        version = "v3"
        try:
            data = json.loads(v3_file.read_text()) or {}
            phases = data.get("phases", {})
        except Exception:
            pass
    elif v2_file.exists():
        try:
            data = json.loads(v2_file.read_text()) or {}
            if data.get("mode") == "v4":
                version = "v4"
            elif data:
                version = "v3"
            phases = data.get("phases", {})
        except Exception:
            pass

    if version is None:
        return None, None

    # Determine build_status from phase completion
    build_status = "draft"
    if version == "v4":
        if phases.get("v4-review", {}).get("status") == "complete":
            build_status = "reviewed"
        elif phases.get("v4-validate", {}).get("status") == "complete":
            build_status = "validated"
    else:
        # v3: D = review, audit = validated
        if phases.get("v3-D", {}).get("status") == "complete":
            build_status = "reviewed"
        elif phases.get("v3-audit", {}).get("status") == "complete":
            build_status = "validated"

    return version, build_status


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

<HighlightMorphemes client:load isUkrainian={{{'true' if is_ukrainian_forced else 'false'}}}>
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

<EssayResponse client:load
  title="{escape_jsx(title)}"
  prompt={{`{escape_jsx(data.prompt)}`}}
  modelAnswer={{`{escape_jsx(data.modelAnswer)}`}}
  rubric={{`{escape_jsx(data.rubric)}`}}
  isUkrainian={{{'true' if is_ukrainian_forced else 'false'}}}
/>'''

def comparative_study_to_jsx(data: ComparativeStudyData, title: str, is_ukrainian_forced: bool = False) -> str:
    """Convert comparative-study data to JSX ComparativeStudy component."""
    return f'''### {title}

<ComparativeStudy client:load
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
    'tip': {'type': 'tip', 'icon': '💡', 'title': 'Tip', 'uk_title': 'Порада'},
    'note': {'type': 'note', 'icon': '📝', 'title': 'Note', 'uk_title': 'Примітка'},
    'warning': {'type': 'warning', 'icon': '⚠️', 'title': 'Warning', 'uk_title': 'Увага'},
    'important': {'type': 'warning', 'icon': '❗', 'title': 'Important', 'uk_title': 'Важливо'},
    'caution': {'type': 'caution', 'icon': '☢️', 'title': 'Caution', 'uk_title': 'Обережно'},
    'info': {'type': 'info', 'icon': 'ℹ️', 'title': 'Info', 'uk_title': 'Інформація'},
    'observe': {'type': 'tip', 'icon': '🔍', 'title': 'Pattern Discovery', 'uk_title': 'Спостереження'},
    'resources': {'type': 'info', 'icon': '🎧', 'title': 'External Resources', 'uk_title': 'Зовнішні ресурси'},
    'example': {'type': 'info', 'icon': '📝', 'title': 'Example', 'uk_title': 'Приклад'},
    'conversation': {'type': 'note', 'icon': '💬', 'title': 'Conversation', 'uk_title': 'Розмова'},
    'summary': {'type': 'note', 'icon': '📋', 'title': 'Summary', 'uk_title': 'Підсумок'},
    'solution': {'type': 'solution'},  # Collapsible answer reveal for checkpoints
    'model-answer': {'type': 'success', 'icon': '✅', 'title': 'Model Answer', 'uk_title': 'Модельна відповідь'},
    'rubric': {'type': 'info', 'icon': '📊', 'title': 'Rubric', 'uk_title': 'Критерії оцінювання'},
    'analysis': {'type': 'info', 'icon': '🧐', 'title': 'Analysis', 'uk_title': 'Аналіз'},
    'history-bite': {'type': 'info', 'icon': '🕰️', 'title': 'History Bite', 'uk_title': 'Історична довідка'},
    'myth-buster': {'type': 'danger', 'icon': '🛡️', 'title': 'Myth Buster', 'uk_title': 'Руйнівник міфів'},
    'quote': {'type': 'note', 'icon': '📜', 'title': 'Quote', 'uk_title': 'Цитата'},
    'context': {'type': 'info', 'icon': '🌍', 'title': 'Context', 'uk_title': 'Контекст'},
    'legacy': {'type': 'tip', 'icon': '💎', 'title': 'Legacy', 'uk_title': 'Спадщина'},
    'reflection': {'type': 'info', 'icon': '🤔', 'title': 'Reflection', 'uk_title': 'Роздуми'},
    'source': {'type': 'note', 'icon': '📖', 'title': 'Source', 'uk_title': 'Джерело'},
    'culture': {'type': 'note', 'icon': '🏺', 'title': 'Culture', 'uk_title': 'Культура'},
    'cultural': {'type': 'note', 'icon': '🏺', 'title': 'Cultural Context', 'uk_title': 'Культура'},
    'culture-note': {'type': 'note', 'icon': '🏺', 'title': 'Culture Note', 'uk_title': 'Культурна примітка'},
    'culture-spot': {'type': 'info', 'icon': '🌍', 'title': 'Culture Spot', 'uk_title': 'Культурний куточок'},
    'heritage': {'type': 'tip', 'icon': '💎', 'title': 'Heritage', 'uk_title': 'Спадщина'},
    'history': {'type': 'info', 'icon': '🕰️', 'title': 'History', 'uk_title': 'Історія'},
    'historical': {'type': 'info', 'icon': '🕰️', 'title': 'Historical Context', 'uk_title': 'Історичний контекст'},
    'history-bite': {'type': 'info', 'icon': '🕰️', 'title': 'History Bite', 'uk_title': 'Історична довідка'},
    'narrative': {'type': 'note', 'icon': '📖', 'title': 'Narrative', 'uk_title': 'Розповідь'},
    'interactive': {'type': 'tip', 'icon': '🎮', 'title': 'Interactive', 'uk_title': 'Інтерактив'},
    'vocabulary': {'type': 'info', 'icon': '📚', 'title': 'Vocabulary', 'uk_title': 'Словник'},
    'grammar': {'type': 'info', 'icon': '⚙️', 'title': 'Grammar', 'uk_title': 'Граматика'},
    'idiom': {'type': 'success', 'icon': '🗣️', 'title': 'Idiom', 'uk_title': 'Фразеологізм'},
    'proverb': {'type': 'success', 'icon': '📜', 'title': 'Proverb', 'uk_title': 'Прислів’я'},
    'language-note': {'type': 'info', 'icon': '🔍', 'title': 'Language Note', 'uk_title': 'Мовна примітка'},
    'did-you-know': {'type': 'info', 'icon': '💡', 'title': 'Did You Know?', 'uk_title': 'Чи знали ви?'},
    'fact': {'type': 'info', 'icon': 'ℹ️', 'title': 'Fact', 'uk_title': 'Факт'},
    'profile': {'type': 'note', 'icon': '👤', 'title': 'Profile', 'uk_title': 'Портрет'},
    'language-point': {'type': 'info', 'icon': '💡', 'title': 'Language Point', 'uk_title': 'Мовний момент'},
    'ponder': {'type': 'info', 'icon': '💭', 'title': 'Ponder', 'uk_title': 'Поміркуйте'},
    'real-world': {'type': 'tip', 'icon': '🌐', 'title': 'Real World', 'uk_title': 'Реальний світ'},
    'realworld': {'type': 'tip', 'icon': '🌐', 'title': 'Real World', 'uk_title': 'Реальний світ'},
}

def convert_callouts(content: str, is_ukrainian_forced: bool = False) -> str:
    """Convert GitHub-style callouts to Docusaurus admonitions.

    Robustly handles:
    1. Standard: > [!type]
    2. Lazy: [!type] (missing marker)
    3. Spaced: [!type] \n\n > content (blank lines before content)
    """
    lines = content.split('\n')
    result = []
    i = 0

    while i < len(lines):
        line = lines[i]

        # Check for callout start: any sequence of > and whitespace + [!type] or [\!type]
        callout_match = re.match(r'^(\s*)[>\s]*\[\\?!([\w-]+)\]\s*(.*)', line)
        if callout_match:
            indent = callout_match.group(1)
            callout_type = callout_match.group(2).lower()
            title_extra = callout_match.group(3).strip()

            config = CALLOUT_MAP.get(callout_type, {'type': 'note'})
            admon_type = config['type']
            icon = config.get('icon', '')

            # Build title
            if title_extra:
                # If we have an icon, prepend it to the custom title
                title = f"{icon} {title_extra}" if icon else title_extra
            elif 'title' in config:
                eng_title = config['title']
                uk_title = config.get('uk_title', eng_title)
                
                display_title = uk_title if is_ukrainian_forced else eng_title
                title = f"{icon} {display_title}" if icon else display_title
            else:
                title = f"{icon} {callout_type.title()}" if icon else callout_type.title()

            # Collect callout content
            callout_lines = []
            i += 1
            
            # Skip leading blank lines (lazy spacing)
            while i < len(lines) and not lines[i].strip():
                i += 1
                
            # Detect if content follows blockquote pattern
            if i < len(lines) and lines[i].strip().startswith('>'):
                # Blockquote continuation
                while i < len(lines):
                    # STOP if this line is a NEW callout header (even if nested)
                    if re.match(r'^(\s*)[>\s]*\[\\?!([\w-]+)\]', lines[i]):
                        break

                    # Match continuation: optional whitespace + > + optional space + content
                    cont_match = re.match(r'^\s*>(.*)', lines[i])
                    if cont_match:
                        content_line = cont_match.group(1)
                        if content_line.startswith(' '):
                            content_line = content_line[1:]
                        callout_lines.append(content_line)
                        i += 1
                    elif not lines[i].strip():
                        # Peek at next line: if it has > and IS NOT a callout header, keep going
                        if i + 1 < len(lines):
                            next_line = lines[i+1]
                            next_is_bq = next_line.strip().startswith('>')
                            next_is_header = next_is_bq and re.match(r'^(\s*)[>\s]*\[![\w-]+\]', next_line)
                            if next_is_bq and not next_is_header:
                                callout_lines.append('')
                                i += 1
                                continue
                        break
                    else:
                        break
            else:
                # Non-blockquote continuation (lazy format)
                while i < len(lines):
                    curr = lines[i]
                    curr_stripped = curr.strip()
                    if not curr_stripped:
                        break
                    if re.match(r'^#{1,6}\s', curr_stripped):
                        break
                    if re.match(r'^(\s*)[>\s]*\[\\?!([\w-]+)\]', curr_stripped):
                        break
                    callout_lines.append(curr)
                    i += 1

            # Special handling for solution callouts
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
# SLUG LINK RESOLVER
# =============================================================================

def resolve_slug_links(content: str) -> str:
    """
    Replace [slug:xxx] links with actual module title and path.

    This allows content to reference other modules by slug instead of
    hardcoded paths, making the curriculum resilient to renumbering.

    Example:
        Input:  See [slug:the-cyrillic-code-i] for details.
        Output: See [The Cyrillic Code I](/a1/module-01) for details.

    Args:
        content: Markdown content with potential [slug:xxx] links

    Returns:
        Content with slug links resolved to actual paths
    """
    def replace_slug(match):
        slug = match.group(1)
        try:
            module = get_module_by_slug(slug)
            if module:
                return f"[{module.title}]({module.path})"
            else:
                # Module not found - leave as-is but log warning
                print(f"  Warning: Unknown slug '{slug}' - link not resolved")
                return match.group(0)
        except Exception as e:
            print(f"  Warning: Error resolving slug '{slug}': {e}")
            return match.group(0)

    # Match [slug:xxx] pattern
    return re.sub(r'\[slug:([a-z0-9-]+)\]', replace_slug, content)


# =============================================================================
# MDX NORMALIZATION
# =============================================================================

def normalize_mdx(text: str) -> str:
    """Normalize MDX output to fix common markdownlint violations.

    Fixes: MD009 (trailing spaces), MD004 (list marker *->-), MD030 (list spacing),
    MD049 (_->*), MD050 (__->**), MD012 (multiple blanks), MD022 (heading blanks),
    MD047 (trailing newline).

    Skips JSX blocks, fenced code blocks, URLs, and inline code to avoid corruption.
    """
    lines = text.split('\n')
    result = []
    in_code_fence = False

    for line in lines:
        stripped = line.strip()

        # Track fenced code blocks
        if stripped.startswith('```'):
            in_code_fence = not in_code_fence
            result.append(line.rstrip())
            continue

        if in_code_fence:
            result.append(line.rstrip())
            continue

        # Skip JSX / import lines (only strip trailing whitespace)
        if (stripped.startswith(('<', '{', '/>', '</', 'import ')) or
                'className=' in line):
            result.append(line.rstrip())
            continue

        # Skip table rows (pipes would cause false positives)
        if stripped.startswith('|'):
            result.append(line.rstrip())
            continue

        # MD009: strip trailing whitespace
        line = line.rstrip()

        # MD004: * list marker -> - (including inside blockquotes)
        line = re.sub(r'^(\s*(?:>\s*)*)\*(?= )', r'\1-', line)

        # MD030: normalize spaces after list markers to exactly 1
        line = re.sub(r'^(\s*(?:>\s*)*(?:[-*+]|\d+\.))\s{2,}', r'\1 ', line)

        # MD049/MD050: normalize emphasis markers
        # Split on code spans AND markdown link targets to preserve URLs and code
        if '_' in line:
            parts = re.split(r'(\[[^\]]*\]\([^)]*\)|`[^`]+`)', line)
            new_parts = []
            for j, part in enumerate(parts):
                if j % 2 == 1:  # inside link target or backticks — preserve
                    new_parts.append(part)
                else:
                    # MD050: __text__ -> **text**
                    part = re.sub(r'(?<!\w)__(?!\s)(.+?)(?<!\s)__(?!\w)', r'**\1**', part)
                    # MD049: _text_ -> *text*
                    part = re.sub(r'(?<!\w)_(?!\s)([^_]+?)(?<!\s)_(?!\w)', r'*\1*', part)
                    new_parts.append(part)
            line = ''.join(new_parts)

        result.append(line)

    text = '\n'.join(result)

    # MD022: blank lines around headings
    # Protect fenced code blocks from heading regex by temporarily replacing them
    code_blocks = []
    def _stash_code_block(match):
        code_blocks.append(match.group(0))
        return f'\x00CODEBLOCK{len(code_blocks) - 1}\x00'
    text = re.sub(r'```[^\n]*\n.*?```', _stash_code_block, text, flags=re.DOTALL)

    text = re.sub(r'(\S[^\n]*)\n(#{1,6} )', r'\1\n\n\2', text)
    text = re.sub(r'(#{1,6} [^\n]+)\n(\S)', r'\1\n\n\2', text)

    # Restore code blocks
    for i, block in enumerate(code_blocks):
        text = text.replace(f'\x00CODEBLOCK{i}\x00', block)

    # MD012: collapse 3+ consecutive newlines to 2 (max 1 blank line)
    text = re.sub(r'\n{3,}', '\n\n', text)

    # MD047: ensure single trailing newline
    text = text.rstrip('\n') + '\n'

    return text


# =============================================================================
# MDX GENERATOR
# =============================================================================

def generate_mdx(md_content: str, module_num: int, yaml_activities: list[Activity] | None = None, meta_data: dict | None = None, vocab_items: list[dict] | None = None, external_resources: dict | None = None, level: str = 'a1', pipeline_version: str | None = None, build_status: str | None = None) -> str:
    """Convert markdown content to MDX.

    Args:
        md_content: Markdown content
        module_num: Module number for sidebar
        yaml_activities: Optional list of activities from ActivityParser (takes precedence over embedded)
        meta_data: Optional metadata from YAML (replaces frontmatter)
        vocab_items: Optional vocab list from YAML
        external_resources: Optional external resources dict (injected from YAML)
        level: Current level (used for specialized formatting like LIT)
        pipeline_version: Optional pipeline version ("v3" or "v4")
        build_status: Optional build status ("draft", "validated", "reviewed")
    """
    if meta_data:
        fm = meta_data
        body = md_content # MD file is already stripped if meta exists (usually)
        # But if we are transitioning, MD might still have FM.
        # parse_frontmatter splits it regardless.
        _, body = parse_frontmatter(md_content)
        # Strip inline YAML preamble when frontmatter delimiters (---) were missing.
        # Some .md files have raw YAML meta at the top without --- delimiters,
        # which parse_frontmatter can't detect. Strip up to first heading.
        # Uses strict key matching to avoid false positives on prose like "Note:".
        _YAML_META_KEYS = {
            'module', 'level', 'sequence', 'slug', 'version', 'title', 'subtitle',
            'content_outline', 'vocabulary_hints', 'activity_hints', 'focus',
            'pedagogy', 'prerequisites', 'connects_to', 'objectives', 'grammar',
            'register', 'phase', 'persona', 'word_target',
        }
        if body and not md_content.lstrip().startswith('---'):
            first_line = body.lstrip().split('\n')[0]
            first_key = first_line.split(':')[0].strip()
            if first_key in _YAML_META_KEYS:
                heading_match = re.search(r'^#{1,2} ', body, flags=re.MULTILINE)
                if heading_match and heading_match.start() > 0:
                    print(f"  ⚠️  Stripping inline YAML preamble (missing --- delimiters)")
                    body = body[heading_match.start():]
    else:
        fm, body = parse_frontmatter(md_content)

    # Determine if Ukrainian headers are forced
    is_ukrainian_forced = False
    lvl = level.lower()
    if any(lvl.startswith(p) for p in ['b2', 'c1', 'c2', 'lit']):
        is_ukrainian_forced = True
    elif lvl.startswith('b1') and module_num > 5:
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
import ComparativeStudy from '@site/src/components/ComparativeStudy';
import ReadingActivity from '@site/src/components/ReadingActivity';
import CriticalAnalysis from '@site/src/components/CriticalAnalysis';
import AuthorialIntent from '@site/src/components/AuthorialIntent';
import SourceEvaluation from '@site/src/components/SourceEvaluation';
import Debate from '@site/src/components/Debate';
import EtymologyTrace from '@site/src/components/EtymologyTrace';
import GrammarIdentify from '@site/src/components/GrammarIdentify';
import PaleographyAnalysis from '@site/src/components/PaleographyAnalysis';
import DialectComparison from '@site/src/components/DialectComparison';
import TranslationCritique from '@site/src/components/TranslationCritique';
import Transcription from '@site/src/components/Transcription';
import Observe from '@site/src/components/Observe';
import ActivityHelp from '@site/src/components/ActivityHelp';
import YouTubeVideo from '@site/src/components/YouTubeVideo';
import WatchAndRepeat from '@site/src/components/WatchAndRepeat';
import Classify from '@site/src/components/Classify';
import ImageToLetter from '@site/src/components/ImageToLetter';
import { Tabs, TabItem } from '@astrojs/starlight/components';"""

    # Frontmatter
    extra_fm_lines = ""
    if pipeline_version:
        extra_fm_lines += f"\npipeline: {pipeline_version}"
    if build_status:
        extra_fm_lines += f"\nbuild_status: {build_status}"
    if pipeline_version and pipeline_version != "v4":
        extra_fm_lines += "\ndraft: true"
    frontmatter = f'''---
title: "{escape_jsx(fm.get('title', 'Untitled'))}"
description: "{escape_jsx(fm.get('subtitle', ''))}"
sidebar:
  order: {module_num}
  label: "{str(module_num).zfill(2)}. {escape_jsx(fm.get('title', 'Untitled'))}"{extra_fm_lines}
---
'''

    # 1. Clean up body: Remove existing Vocabulary, Activities, and Resources placeholders
    # Remove Activities
    body = re.sub(r'(^#{1,2}\s+(?:Activities|Вправи))[\s\S]*?(?=\n#{1,2}|\Z)', '', body, flags=re.MULTILINE)
    # Remove Vocabulary
    body = re.sub(r'(^#{1,2}\s+(?:Vocabulary|Словник))[\s\S]*?(?=\n#{1,2}|\Z)', '', body, flags=re.MULTILINE)
    # Remove Resources callout
    body = re.sub(r'>\s*\[!resources\].*?(\n>.*)*', '', body, flags=re.MULTILINE | re.IGNORECASE)

    # =========================================================================
    # TABBED LAYOUT: Build 4 separate content blocks
    # =========================================================================

    # --- TAB 1: Lesson (prose only) ---
    lesson_content = body

    # --- TAB 2: Vocabulary ---
    if vocab_items:
        vocab_header = "Словник" if is_ukrainian_forced else "Vocabulary"
        if is_ukrainian_forced:
            vocab_content = _b1_vocab_items_to_markdown(vocab_items, vocab_header)
        else:
            vocab_content = _vocab_items_to_markdown(vocab_items, vocab_header)
        # Strip the H2 header — the tab label serves as the header
        vocab_content = re.sub(r'^## [^\n]+\n+', '', vocab_content)
    else:
        no_vocab_msg = "Немає словника для цього модуля." if is_ukrainian_forced else "No vocabulary for this module."
        vocab_content = f"*{no_vocab_msg}*"

    # --- TAB 3: Activities ---
    if yaml_activities:
        activities_content = yaml_activities_to_jsx(yaml_activities, is_ukrainian_forced)
    else:
        no_act_msg = "Немає вправ для цього модуля." if is_ukrainian_forced else "No activities for this module."
        activities_content = f"*{no_act_msg}*"

    # --- TAB 4: Resources ---
    resources_content = ""
    if external_resources:
        resources_content = format_resources_for_mdx(external_resources, is_ukrainian_forced)
    if not resources_content:
        no_res_msg = "Немає зовнішніх ресурсів для цього модуля." if is_ukrainian_forced else "No external resources for this module."
        resources_content = f"*{no_res_msg}*"

    # =========================================================================
    # Process lesson content (Tab 1 only)
    # =========================================================================

    # Embed YouTube video links as clickable thumbnails (lesson prose only)
    lesson_content = _embed_youtube_video_links(lesson_content)

    # =========================================================================
    # Apply shared transforms to all content blocks
    # =========================================================================
    def _apply_shared_transforms(text: str) -> str:
        """Apply callout conversion, slug links, HTML fixes, comments, stories, dialogues."""
        text = convert_callouts(text, is_ukrainian_forced)
        text = resolve_slug_links(text)
        text = fix_html_for_jsx(text)
        text = re.sub(r'<!--(.*?)-->', r'{/**/}', text, flags=re.DOTALL)
        text = process_story_sections(text)
        text = process_dialogues(text)
        return text

    lesson_content = _apply_shared_transforms(lesson_content)
    vocab_content = _apply_shared_transforms(vocab_content)
    activities_content = _apply_shared_transforms(activities_content)
    resources_content = _apply_shared_transforms(resources_content)

    # Remove duplicate H1 title (from lesson tab only)
    lesson_content = re.sub(r'^#\s+[^\n]+\n', '', lesson_content, count=1, flags=re.MULTILINE)

    # Add emojis to H2 section headings (data-driven)
    # (uk_text, emoji, regex_pattern, target_tab)
    _HEADING_RULES = [
        ('Підсумок',            '📋', r'Summary|Підсумок',                                                                  'lesson'),
        ('Самооцінка',          '✅', r'Self-Assessment|Самооцінка',                                                         'lesson'),
        ('Зовнішні ресурси',    '🔗', r'External Resources?|Зовнішні ресурси|Resources|Ресурси',                              'resources'),
        ('Культура',            '🏺', r'Culture|Культура|Cultural Context|Культурний контекст|Folk Culture|Народна культура', 'lesson'),
        ('Історичний контекст', '🕰️',  r'History|Historical Context|Історичний контекст|Heritage|Спадщина',                   'lesson'),
    ]
    content_blocks = {'lesson': lesson_content, 'resources': resources_content}
    for uk_text, emoji, pattern, target in _HEADING_RULES:
        replacement = uk_text if is_ukrainian_forced else r'\g<1>'
        content_blocks[target] = re.sub(
            rf'^#{{1,2}} ({pattern})', f'## {emoji} {replacement}',
            content_blocks[target], flags=re.MULTILINE,
        )
    lesson_content = content_blocks['lesson']
    resources_content = content_blocks['resources']

    # =========================================================================
    # Wrap in Tabs
    # =========================================================================
    # (label_en, label_uk, content)
    tabs = [
        ("Lesson",     "Урок",    lesson_content),
        ("Vocabulary", "Словник",  vocab_content),
        ("Activities", "Вправи",   activities_content),
        ("Resources",  "Ресурси",  resources_content),
    ]
    tab_items = '\n'.join(
        f'<TabItem label="{uk if is_ukrainian_forced else en}">\n\n'
        f'{content.strip()}\n\n</TabItem>'
        for en, uk, content in tabs
    )
    tabbed = f'\n<Tabs syncKey="module-tab">\n{tab_items}\n</Tabs>\n'

    # Build MDX
    parts = [frontmatter, imports, '', tabbed]

    return normalize_mdx('\n'.join(parts))

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


# ---------------------------------------------------------------------------
# YouTube embed helper
# ---------------------------------------------------------------------------

_YT_VIDEO_LINK_RE = re.compile(
    r'\[([^\]]+)\]'                              # [link text]
    r'\('                                        # (
    r'(https?://(?:www\.)?'                      # http(s)://
    r'(?:youtube\.com/watch\?v=|youtu\.be/)'     # youtube.com/watch?v= or youtu.be/
    r'[^\)]+)'                                   # video ID + params
    r'\)'                                        # )
    r'\.?'                                       # optional trailing period
)

_YT_VID_ID_RE = re.compile(r'(?:v=|/embed/|youtu\.be/)([A-Za-z0-9_-]{11})')


_YT_JINJA_RE = re.compile(
    r'\{%\s*youtubeVideo\s+"(https?://(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/)[\w-]+[^"]*?)"\s*%\}'
)
# Also match {% youtubeVideo id="VIDEO_ID" %} variant (Gemini sometimes produces this)
_YT_JINJA_ID_RE = re.compile(
    r'\{%\s*youtubeVideo\s+id="([A-Za-z0-9_-]{11})"\s*%\}'
)


def _embed_youtube_video_links(body: str) -> str:
    """Replace YouTube markdown links with inline ``<YouTubeVideo>`` components.

    Transforms ``[text](youtube-watch-url)`` into a React component that shows
    a thumbnail and plays the video inline when clicked (no page navigation).
    Only matches watch / short-link URLs — playlist links are left as-is.

    Also handles Jinja/Nunjucks-style ``{% youtubeVideo "url" %}`` tags that
    Gemini sometimes produces instead of markdown links.
    """

    def _yt_replace(m: re.Match) -> str:
        text = m.group(1)
        url = m.group(2)
        vid_match = _YT_VID_ID_RE.search(url)
        if not vid_match:
            return m.group(0)
        label = escape_jsx(text)
        return (
            f'\n\n<YouTubeVideo client:load url="{url}" label="{label}" />\n\n'
        )

    def _yt_jinja_replace(m: re.Match) -> str:
        url = m.group(1)
        vid_match = _YT_VID_ID_RE.search(url)
        if not vid_match:
            return m.group(0)
        return (
            f'\n\n<YouTubeVideo client:load url="{url}" label="Video" />\n\n'
        )

    def _yt_jinja_id_replace(m: re.Match) -> str:
        vid_id = m.group(1)
        url = f"https://www.youtube.com/watch?v={vid_id}"
        return (
            f'\n\n<YouTubeVideo client:load url="{url}" label="Video" />\n\n'
        )

    body = _YT_JINJA_ID_RE.sub(_yt_jinja_id_replace, body)
    body = _YT_JINJA_RE.sub(_yt_jinja_replace, body)
    return _YT_VIDEO_LINK_RE.sub(_yt_replace, body)


# ---------------------------------------------------------------------------
# Discovery → MDX resources bridge
# ---------------------------------------------------------------------------

def _load_discovery_resources(level_dir: Path, slug: str) -> dict:
    """Load discovery.yaml and convert to external_resources format.

    Reads from the canonical sidecar location: discovery/{slug}.yaml.
    Filters blogs with relevance_score >= 0.5 and maps content_type
    to the appropriate resource category (podcasts vs articles).

    Returns dict with keys: articles, podcasts (matching format_resources_for_mdx).
    """
    discovery_path = level_dir / "discovery" / f"{slug}.yaml"
    if not discovery_path.exists():
        return {}

    try:
        data = yaml.safe_load(discovery_path.read_text(encoding="utf-8"))
    except Exception:
        return {}

    if not data or not isinstance(data, dict):
        return {}

    articles: list[dict] = []
    podcasts: list[dict] = []

    for blog in data.get("blogs", []):
        score = blog.get("relevance_score", 0)
        if score < 0.5:
            continue
        item = {
            "title": blog.get("title", ""),
            "url": blog.get("url", ""),
            "source": blog.get("source", ""),
            "relevance": "high" if score >= 0.7 else "medium",
        }
        content_type = blog.get("content_type", "")
        if content_type.startswith("podcast_episode"):
            podcasts.append(item)
        else:
            articles.append(item)

    result: dict[str, list] = {}
    if articles:
        result["articles"] = articles
    if podcasts:
        result["podcasts"] = podcasts
    return result


def _merge_resources(curated: dict, discovery: dict) -> dict:
    """Merge curated and discovery resources, deduplicating by URL.

    Curated items appear first (higher priority). For each category
    (articles, podcasts, youtube, websites, books), items are merged
    and deduplicated by URL.
    """
    if not discovery:
        return curated
    if not curated:
        return discovery

    merged = dict(curated)  # shallow copy
    for category in ("articles", "podcasts", "youtube", "websites", "books"):
        curated_items = curated.get(category, [])
        discovery_items = discovery.get(category, [])
        if not discovery_items:
            continue
        seen_urls = {item.get("url", "") for item in curated_items if item.get("url")}
        deduped = list(curated_items)
        for item in discovery_items:
            url = item.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                deduped.append(item)
        merged[category] = deduped
    return merged


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

            elif resource_type == 'youtube':
                channel = item.get('channel', '')
                if channel:
                    lines.append(f"> - [{title}]({url}) — {channel}")
                else:
                    lines.append(f"> - [{title}]({url})")

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
    """Tier 1/2 (A1/A2): 6 columns (Scaffolding)."""
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

def _b1_vocab_items_to_markdown(items: list[dict], header_text: str = "Словник") -> str:
    """Tier 3/4 (B1-C2): 5 columns (Ukrainian, IPA included)."""
    lines = [
        f"## {header_text}",
        "",
        "| Слово | Вимова | Переклад | ЧМ | Примітка |",
        "| --- | --- | --- | --- | --- |"
    ]
    for item in items:
        # Map POS to Ukrainian abbreviation
        pos_map = {
            'noun': 'ім', 'verb': 'дієсл', 'adj': 'прикм', 'adv': 'присл', 
            'prep': 'прийм', 'conj': 'спол', 'pron': 'займ', 'phrase': 'фраза',
            'propn': 'назва'
        }
        raw_p = item.get('pos', '')
        p_val = pos_map.get(raw_p, raw_p)
        
        line = f"| **{item.get('lemma')}** | {item.get('ipa','')} | {item.get('translation','')} | {p_val} | {item.get('usage','')} |"
        lines.append(line)
        
    return '\n'.join(lines)

from manifest_utils import load_manifest, get_module_by_slug, get_modules_for_level, Module, CORE_LEVELS, TRACKS

def get_modules_from_manifest(target_level: Optional[str] = None) -> list[Module]:
    """Get list of modules to process from manifest."""
    all_modules = []

    # Process core levels
    for level in CORE_LEVELS:
        if target_level and level != target_level:
            continue
        all_modules.extend(get_modules_for_level(level))

    # Process tracks (hist, bio, lit)
    for track_name in TRACKS:
        if target_level and track_name != target_level:
            continue
        all_modules.extend(get_modules_for_level(track_name))

    return all_modules

def main():
    args = sys.argv[1:]

    # Parse --validate flag
    validate_after = '--validate' in args
    args = [a for a in args if a != '--validate']

    print('\n🚀 MDX Generator (Manifest-Driven)\n', flush=True)

    target_level = None
    target_module = None
    lang_pair = 'l2-uk-en'

    if args:
        if args[0].endswith('.md'):
            # Specific file logic: extract level and slug from path
            file_path = Path(args[0])
            # Path format: curriculum/l2-uk-en/{level}/{slug}.md
            level_from_path = file_path.parent.name
            slug = to_bare_slug(file_path.stem)
            
            # Find all modules with this slug from manifest
            all_available_modules = get_modules_from_manifest()
            matching_modules = [m for m in all_available_modules if m.slug == slug]
            
            if not matching_modules:
                print(f"  ⚠️  Could not find module with slug '{slug}' in manifest for: {args[0]}")
                sys.exit(1)
            
            # Filter by level from path
            mod_obj = None
            for m in matching_modules:
                if m.level.lower() == level_from_path.lower():
                    mod_obj = m
                    break
            
            # If no level match, take the first one (fallback)
            if not mod_obj:
                mod_obj = matching_modules[0]
                print(f"  ℹ️  Using fallback module mapping: {mod_obj.level}/{mod_obj.slug}")
            
            process_modules = [mod_obj]
        else:
            lang_pair = args[0]
            target_level = args[1].lower() if len(args) > 1 else None
            target_module = int(args[2]) if len(args) > 2 else None
            process_modules = get_modules_from_manifest(target_level)
    else:
        process_modules = get_modules_from_manifest()

    print(f'Source: curriculum/{lang_pair}/', flush=True)
    print(f'Output: starlight/src/content/docs/\n', flush=True)

    # Load EXTERNAL RESOURCES
    external_resources_file = PROJECT_ROOT / 'docs' / 'resources' / 'external_resources.yaml'
    all_resources = {}
    if external_resources_file.exists():
        with open(external_resources_file, 'r', encoding='utf-8') as f:
            resources_data = yaml.safe_load(f)
            all_resources = resources_data.get('resources', {})
        print(f'📚 Loaded {len(all_resources)} modules with external resources\n', flush=True)

    current_level = None
    for mod in process_modules:
        if target_module and mod.local_num != target_module:
            continue

        if mod.level != current_level:
            print(f'📁 Level {mod.level.upper()}')
            current_level = mod.level
            output_dir = DOCUSAURUS_DIR / mod.level
            output_dir.mkdir(parents=True, exist_ok=True)

        # Find the physical file
        level_dir = CURRICULUM_DIR / lang_pair / mod.level
        md_file = level_dir / f"{mod.slug}.md"
        
        if not md_file.exists():
            print(f"DEBUG: Checked path {md_file.absolute()}")
            print(f"  ⚠️  Physical file not found for slug '{mod.slug}' in {mod.level}")
            continue

        # Read and convert
        md_content = md_file.read_text(encoding='utf-8')
        
        # Load META
        meta_file = level_dir / 'meta' / f"{mod.slug}.yaml"
            
        meta_data = None
        if meta_file.exists():
            try:
                with open(meta_file, 'r', encoding='utf-8') as f:
                    meta_data = yaml.safe_load(f)
            except Exception as e:
                print(f'\n❌ CRITICAL: Error parsing YAML metadata for {mod.slug}: {e}')
                sys.exit(1)

        # Load PLAN file for title/subtitle (Architecture v2.0: title lives in plan, not meta)
        plan_file = CURRICULUM_DIR / lang_pair / 'plans' / mod.level.lower() / f"{mod.slug}.yaml"
        if plan_file.exists():
            try:
                with open(plan_file, 'r', encoding='utf-8') as f:
                    plan_data = yaml.safe_load(f)
                    # Merge title/subtitle from plan into meta_data
                    if meta_data is None:
                        meta_data = {}
                    if plan_data and 'title' in plan_data:
                        if 'title' not in meta_data:
                            meta_data['title'] = plan_data['title']
                    if plan_data and 'subtitle' in plan_data:
                        if 'subtitle' not in meta_data:
                            meta_data['subtitle'] = plan_data['subtitle']
            except Exception as e:
                print(f'\n❌ CRITICAL: Error parsing plan file for {mod.slug}: {e}')
                sys.exit(1)
                
        # Load VOCABULARY
        vocab_file = level_dir / 'vocabulary' / f"{mod.slug}.yaml"
            
        vocab_items = None
        if vocab_file.exists():
            try:
                with open(vocab_file, 'r', encoding='utf-8') as f:
                    v_data = yaml.safe_load(f)
                    if isinstance(v_data, list):
                        vocab_items = v_data
                    elif isinstance(v_data, dict) and 'items' in v_data:
                        vocab_items = v_data['items']
            except Exception as e:
                print(f'\n❌ CRITICAL: Error parsing YAML vocabulary for {mod.slug}: {e}')
                sys.exit(1)

        # Load ACTIVITIES
        yaml_file = level_dir / 'activities' / f"{mod.slug}.yaml"
        
        yaml_activities = None
        if yaml_file.exists():
            parser = ActivityParser()
            try:
                yaml_activities = parser.parse(yaml_file)
            except Exception as e:
                print(f'\n❌ CRITICAL: Error parsing YAML activities for {mod.slug}: {e}')
                sys.exit(1)

        # EXTERNAL RESOURCES — single source of truth: external_resources.yaml
        # Discovery files are pipeline intermediates, not rendered directly.
        module_id = f"{mod.level}-{mod.slug}"
        module_resources = all_resources.get(module_id, {})

        # Detect pipeline version and build status
        pv, bs = detect_pipeline_info(level_dir, mod.slug)

        mdx_content = generate_mdx(md_content, mod.local_num, yaml_activities, meta_data, vocab_items, module_resources, mod.level, pipeline_version=pv, build_status=bs)

        # Write output — all tracks use slug-based filenames
        output_file = output_dir / f'{mod.slug}.mdx'
        output_file.write_text(mdx_content, encoding='utf-8')

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


if __name__ == '__main__':
    main()
