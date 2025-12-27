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
import yaml
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

# Paths
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
CURRICULUM_DIR = PROJECT_ROOT / "curriculum"
DOCUSAURUS_DIR = PROJECT_ROOT / "docusaurus" / "docs"

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
class DialogueLine:
    text: str
    order: int

@dataclass
class MarkTheWordsItem:
    text: str  # Plain text with marks removed
    correctWords: list[str]  # List of correct words to mark

# =============================================================================
# UTILITIES
# =============================================================================

def escape_jsx(text: str) -> str:
    """Escape text for use in JSX strings (both template literals and double quotes)."""
    if not text:
        return ''
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

def load_yaml_activities(yaml_path: Path) -> list[dict] | None:
    """Load activities from YAML file if it exists."""
    if not yaml_path.exists():
        return None
    try:
        with open(yaml_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        # Support both formats:
        # 1. Root list: [{ type: quiz, ... }, ...]
        # 2. Dict with 'activities' key: { activities: [{ type: quiz, ... }, ...] }
        if isinstance(data, list):
            return data
        elif isinstance(data, dict) and 'activities' in data:
            activities = data['activities']
            if isinstance(activities, list):
                return activities
        return None
    except (yaml.YAMLError, IOError) as e:
        print(f"  ⚠️ Error loading YAML activities: {e}")
        return None

def yaml_activities_to_jsx(activities: list[dict]) -> str:
    """Convert YAML activities to JSX components."""
    jsx_parts = []

    for activity in activities:
        activity_type = activity.get('type', '')
        title = activity.get('title', 'Activity')
        jsx = ''

        if activity_type == 'quiz':
            jsx = _yaml_quiz_to_jsx(activity, title)
        elif activity_type == 'match-up':
            jsx = _yaml_match_up_to_jsx(activity, title)
        elif activity_type == 'fill-in':
            jsx = _yaml_fill_in_to_jsx(activity, title)
        elif activity_type == 'true-false':
            jsx = _yaml_true_false_to_jsx(activity, title)
        elif activity_type == 'group-sort':
            jsx = _yaml_group_sort_to_jsx(activity, title)
        elif activity_type == 'unjumble':
            jsx = _yaml_unjumble_to_jsx(activity, title)
        elif activity_type == 'cloze':
            jsx = _yaml_cloze_to_jsx(activity, title)
        elif activity_type == 'error-correction':
            jsx = _yaml_error_correction_to_jsx(activity, title)
        elif activity_type == 'select':
            jsx = _yaml_select_to_jsx(activity, title)
        elif activity_type == 'translate':
            jsx = _yaml_translate_to_jsx(activity, title)
        elif activity_type == 'dialogue-reorder':
            jsx = _yaml_dialogue_reorder_to_jsx(activity, title)
        elif activity_type == 'mark-the-words':
            jsx = _yaml_mark_the_words_to_jsx(activity, title)
        elif activity_type == 'anagram':
            jsx = _yaml_anagram_to_jsx(activity, title)

        if jsx:
            jsx_parts.append(jsx)

    return '\n\n'.join(jsx_parts)

def _yaml_quiz_to_jsx(activity: dict, title: str) -> str:
    """Convert YAML quiz to JSX."""
    items = activity.get('items', [])
    questions_json = []
    for item in items:
        q = {
            "question": escape_jsx(item.get('question', '')),
            "options": [
                {"text": escape_jsx(opt.get('text', '')), "correct": opt.get('correct', False)}
                for opt in item.get('options', [])
            ]
        }
        questions_json.append(q)

    import json
    return f'''### {escape_jsx(title)}

<Quiz
  title="{escape_jsx(title)}"
  questions={{JSON.parse(`{json.dumps(questions_json, ensure_ascii=False)}`)}}
/>'''

def _yaml_match_up_to_jsx(activity: dict, title: str) -> str:
    """Convert YAML match-up to JSX."""
    # Support both 'pairs' (preferred) and 'items' with left/right keys
    pairs = activity.get('pairs', [])
    if not pairs:
        items = activity.get('items', [])
        if items and isinstance(items[0], dict) and 'left' in items[0]:
            pairs = items
    pairs_json = [
        {"left": escape_jsx(p.get('left', '')), "right": escape_jsx(p.get('right', ''))}
        for p in pairs
    ]

    import json
    return f'''### {escape_jsx(title)}

<MatchUp
  title="{escape_jsx(title)}"
  pairs={{JSON.parse(`{json.dumps(pairs_json, ensure_ascii=False)}`)}}
/>'''

def _yaml_fill_in_to_jsx(activity: dict, title: str) -> str:
    """Convert YAML fill-in to JSX."""
    items = activity.get('items', [])
    items_json = [
        {
            "sentence": escape_jsx(item.get('sentence', '')),
            "answer": escape_jsx(item.get('answer', '')),
            "options": [escape_jsx(opt) for opt in item.get('options', [])]
        }
        for item in items
    ]

    import json
    return f'''### {escape_jsx(title)}

<FillIn
  title="{escape_jsx(title)}"
  items={{JSON.parse(`{json.dumps(items_json, ensure_ascii=False)}`)}}
/>'''

def _yaml_true_false_to_jsx(activity: dict, title: str) -> str:
    """Convert YAML true-false to JSX."""
    items = activity.get('items', [])
    items_json = [
        {
            "statement": escape_jsx(item.get('statement', '')),
            "isTrue": item.get('correct', False),
            "explanation": escape_jsx(item.get('explanation', ''))
        }
        for item in items
    ]

    import json
    return f'''### {escape_jsx(title)}

<TrueFalse
  title="{escape_jsx(title)}"
  items={{JSON.parse(`{json.dumps(items_json, ensure_ascii=False)}`)}}
/>'''

def _yaml_group_sort_to_jsx(activity: dict, title: str) -> str:
    """Convert YAML group-sort to JSX."""
    groups = activity.get('groups', [])
    groups_dict = {}
    for group in groups:
        name = group.get('name', '')
        items = [escape_jsx(item) for item in group.get('items', [])]
        groups_dict[name] = items

    import json
    return f'''### {escape_jsx(title)}

<GroupSort
  title="{escape_jsx(title)}"
  groups={{JSON.parse(`{json.dumps(groups_dict, ensure_ascii=False)}`)}}
/>'''

def _yaml_unjumble_to_jsx(activity: dict, title: str) -> str:
    """Convert YAML unjumble to JSX."""
    items = activity.get('items', [])
    items_json = [
        {
            "jumbled": escape_jsx(item.get('scrambled', '')),
            "answer": escape_jsx(item.get('answer', ''))
        }
        for item in items
    ]

    import json
    return f'''### {escape_jsx(title)}

<Unjumble
  title="{escape_jsx(title)}"
  items={{JSON.parse(`{json.dumps(items_json, ensure_ascii=False)}`)}}
/>'''

def _yaml_cloze_to_jsx(activity: dict, title: str) -> str:
    """Convert YAML cloze to JSX."""
    passage = activity.get('passage', '')

    # Parse blanks from passage: {answer|opt1|opt2|opt3}
    blanks = []
    blank_pattern = r'\{([^}]+)\}'

    def replace_blank(match):
        parts = match.group(1).split('|')
        answer = parts[0] if parts else ''
        options = parts[1:] if len(parts) > 1 else [answer]
        # Ensure answer is in options
        if answer not in options:
            options.insert(0, answer)
        blanks.append({
            "answer": escape_jsx(answer),
            "options": [escape_jsx(opt) for opt in options]
        })
        return '___'

    clean_passage = re.sub(blank_pattern, replace_blank, passage)

    import json
    # Use template literal for passage to properly handle newlines and special characters
    return f'''### {escape_jsx(title)}

<Cloze
  title="{escape_jsx(title)}"
  passage={{`{escape_jsx(clean_passage)}`}}
  blanks={{JSON.parse(`{json.dumps(blanks, ensure_ascii=False)}`)}}
/>'''

def _yaml_error_correction_to_jsx(activity: dict, title: str) -> str:
    """Convert YAML error-correction to JSX."""
    items = activity.get('items', [])
    jsx_items = []

    for item in items:
        options_jsx = ', '.join([f'`{escape_jsx(opt)}`' for opt in item.get('options', [])])
        jsx_items.append(f'''  <ErrorCorrectionItem
    sentence={{`{escape_jsx(item.get('sentence', ''))}`}}
    errorWord={{`{escape_jsx(item.get('error', ''))}`}}
    correctForm={{`{escape_jsx(item.get('answer', ''))}`}}
    options={{[{options_jsx}]}}
    explanation={{`{escape_jsx(item.get('explanation', ''))}`}}
  />''')

    return f'''### {escape_jsx(title)}

<ErrorCorrection title="{escape_jsx(title)}">
{chr(10).join(jsx_items)}
</ErrorCorrection>'''

def _yaml_select_to_jsx(activity: dict, title: str) -> str:
    """Convert YAML select to JSX."""
    items = activity.get('items', [])
    questions_json = []
    for item in items:
        q = {
            "question": escape_jsx(item.get('question', '')),
            "options": [
                {"text": escape_jsx(opt.get('text', '')), "correct": opt.get('correct', False)}
                for opt in item.get('options', [])
            ]
        }
        questions_json.append(q)

    import json
    return f'''### {escape_jsx(title)}

<Select
  title="{escape_jsx(title)}"
  questions={{JSON.parse(`{json.dumps(questions_json, ensure_ascii=False)}`)}}
/>'''

def _yaml_translate_to_jsx(activity: dict, title: str) -> str:
    """Convert YAML translate to JSX."""
    items = activity.get('items', [])
    questions_json = []
    for item in items:
        q = {
            "source": escape_jsx(item.get('source', '')),
            "options": [
                {"text": escape_jsx(opt.get('text', '')), "correct": opt.get('correct', False)}
                for opt in item.get('options', [])
            ]
        }
        questions_json.append(q)

    import json
    return f'''### {escape_jsx(title)}

<Translate
  title="{escape_jsx(title)}"
  questions={{JSON.parse(`{json.dumps(questions_json, ensure_ascii=False)}`)}}
/>'''

def _yaml_dialogue_reorder_to_jsx(activity: dict, title: str) -> str:
    """Convert YAML dialogue-reorder to JSX."""
    lines = activity.get('lines', [])
    lines_json = [
        {
            "text": escape_jsx(line.get('text', '')),
            "order": line.get('order', 0),
            "speaker": escape_jsx(line.get('speaker', ''))
        }
        for line in lines
    ]

    import json
    return f'''### {escape_jsx(title)}

<DialogueReorder
  title="{escape_jsx(title)}"
  lines={{JSON.parse(`{json.dumps(lines_json, ensure_ascii=False)}`)}}
/>'''

def _yaml_mark_the_words_to_jsx(activity: dict, title: str) -> str:
    """Convert YAML mark-the-words to JSX."""
    instruction = activity.get('instruction', 'Click the correct words.')
    text = activity.get('text', '')

    # Extract correct words (marked with *word*)
    correct_words = re.findall(r'\*([^*]+)\*', text)
    clean_text = re.sub(r'\*([^*]+)\*', r'\1', text)

    import json
    # Use template literals for text to properly handle special characters like ! and ?
    return f'''### {escape_jsx(title)}

<MarkTheWords>
  <MarkTheWordsActivity
    instruction={{`{escape_jsx(instruction)}`}}
    text={{`{escape_jsx(clean_text)}`}}
    correctWords={{JSON.parse(`{json.dumps(correct_words, ensure_ascii=False)}`)}}
  />
</MarkTheWords>'''

def _yaml_anagram_to_jsx(activity: dict, title: str) -> str:
    """Convert YAML anagram to JSX."""
    items = activity.get('items', [])
    items_json = [
        {
            "scrambled": escape_jsx(item.get('scrambled', '')),
            "answer": escape_jsx(item.get('answer', '')),
            "hint": escape_jsx(item.get('hint', ''))
        }
        for item in items
    ]

    import json
    return f'''### {escape_jsx(title)}

<Anagram
  title="{escape_jsx(title)}"
  items={{JSON.parse(`{json.dumps(items_json, ensure_ascii=False)}`)}}
/>'''

def extract_instruction(content: str) -> tuple[str, str]:
    """Extract instruction blockquote from activity content."""
    lines = content.split('\n')
    instruction_lines = []
    content_start = 0

    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith('>') and not stripped.startswith('> [!'):
            instruction_lines.append(stripped[1:].strip())
            content_start = i + 1
        elif stripped == '':
            content_start = i + 1
        else:
            break

    instruction = ' '.join(instruction_lines).strip()
    remaining = '\n'.join(lines[content_start:])
    return instruction, remaining

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

def parse_dialogue_reorder(content: str) -> list[DialogueLine]:
    """Parse dialogue-reorder activity."""
    lines_data = []
    order = 1

    for line in content.split('\n'):
        stripped = line.strip()
        if stripped.startswith('- '):
            text = stripped[2:].strip()
            lines_data.append(DialogueLine(text=text, order=order))
            order += 1

    return lines_data

# =============================================================================
# JSX GENERATORS
# =============================================================================

def quiz_to_jsx(questions: list[QuizQuestion], title: str) -> str:
    """Convert quiz questions to JSX Quiz component."""
    if not questions:
        return ''

    items = []
    for q in questions:
        opts = ',\n      '.join([
            f'{{ text: `{escape_jsx(o["text"])}`, correct: {"true" if o["correct"] else "false"} }}'
            for o in q.options
        ])
        items.append(f'''  {{
    question: `{escape_jsx(q.question)}`,
    options: [
      {opts}
    ]
  }}''')

    return f'''### {title}

<Quiz questions={{[
{",".join(items)}
]}} />'''

def match_up_to_jsx(pairs: list[MatchPair], title: str) -> str:
    """Convert match pairs to JSX MatchUp component."""
    if not pairs:
        return ''

    items = ',\n  '.join([
        f'{{ left: `{escape_jsx(p.left)}`, right: `{escape_jsx(p.right)}` }}'
        for p in pairs
    ])

    return f'''### {title}

<MatchUp pairs={{[
  {items}
]}} />'''

def fill_in_to_jsx(items: list[FillInItem], title: str) -> str:
    """Convert fill-in items to JSX FillIn component."""
    if not items:
        return ''

    jsx_items = []
    for item in items:
        opts = ', '.join([f'`{escape_jsx(o)}`' for o in item.options])
        jsx_items.append(f'''  {{
    sentence: `{escape_jsx(item.sentence)}`,
    answer: `{escape_jsx(item.answer)}`,
    options: [{opts}]
  }}''')

    return f'''### {title}

<FillIn items={{[
{",".join(jsx_items)}
]}} />'''

def true_false_to_jsx(items: list[TrueFalseItem], title: str) -> str:
    """Convert true-false items to JSX TrueFalse component."""
    if not items:
        return ''

    jsx_items = []
    for item in items:
        jsx_items.append(f'''  {{
    statement: `{escape_jsx(item.statement)}`,
    isTrue: {"true" if item.is_true else "false"},
    explanation: `{escape_jsx(item.explanation)}`
  }}''')

    return f'''### {title}

<TrueFalse items={{[
{",".join(jsx_items)}
]}} />'''

def unjumble_to_jsx(items: list[UnjumbleItem], title: str) -> str:
    """Convert unjumble items to JSX Unjumble component."""
    if not items:
        return ''

    jsx_items = ',\n  '.join([
        f'{{ jumbled: `{escape_jsx(item.jumbled)}`, answer: `{escape_jsx(item.answer)}` }}'
        for item in items
    ])

    return f'''### {title}

<Unjumble items={{[
  {jsx_items}
]}} />'''

def group_sort_to_jsx(data: GroupSortData, title: str) -> str:
    """Convert group-sort data to JSX GroupSort component."""
    if not data.groups:
        return ''

    groups_jsx = []
    for group_name, items in data.groups.items():
        items_str = ', '.join([f'"{escape_jsx(i)}"' for i in items])
        groups_jsx.append(f'  "{escape_jsx(group_name)}": [{items_str}]')

    groups_str = ",\n".join(groups_jsx)
    return f'''### {title}

<GroupSort groups={{{{
{groups_str}
}}}} />'''

def anagram_to_jsx(items: list[AnagramItem], title: str) -> str:
    """Convert anagram items to JSX Anagram component."""
    if not items:
        return ''

    jsx_items = ',\n  '.join([
        f'{{ scrambled: `{escape_jsx(item.scrambled)}`, answer: `{escape_jsx(item.answer)}`, hint: `{escape_jsx(item.hint)}` }}'
        for item in items
    ])

    return f'''### {title}

<Anagram items={{[
  {jsx_items}
]}} />'''

def error_correction_to_jsx(items: list[ErrorCorrectionItem], title: str) -> str:
    """Convert error-correction items to JSX ErrorCorrection component."""
    if not items:
        return ''

    jsx_items = []
    for item in items:
        options_jsx = ', '.join([f'`{escape_jsx(o)}`' for o in item.options])
        jsx_items.append(f'''  <ErrorCorrectionItem
    sentence={{`{escape_jsx(item.sentence)}`}}
    errorWord={{`{escape_jsx(item.errorWord)}`}}
    correctForm={{`{escape_jsx(item.correctForm)}`}}
    options={{[{options_jsx}]}}
    explanation={{`{escape_jsx(item.explanation)}`}}
  />''')

    return f'''### {title}

<ErrorCorrection>
{chr(10).join(jsx_items)}
</ErrorCorrection>'''

def cloze_to_jsx(data: ClozeData, title: str) -> str:
    """Convert cloze data to JSX Cloze component."""
    if not data.passage:
        return ''

    blanks_jsx = []
    for idx, blank in enumerate(data.blanks):
        opts = ', '.join([f'`{escape_jsx(o)}`' for o in blank.get("options", [])])
        blanks_jsx.append(f'{{ index: {idx}, answer: `{escape_jsx(blank["answer"])}`, options: [{opts}] }}')

    return f'''### {title}

<Cloze
  passage={{`{escape_jsx(data.passage)}`}}
  blanks={{[{", ".join(blanks_jsx)}]}}
/>'''

def select_to_jsx(questions: list[SelectQuestion], title: str) -> str:
    """Convert select questions to JSX Select component."""
    if not questions:
        return ''

    items = []
    for q in questions:
        opts = ',\n      '.join([
            f'{{ text: `{escape_jsx(o["text"])}`, correct: {"true" if o["correct"] else "false"} }}'
            for o in q.options
        ])
        items.append(f'''  {{
    question: `{escape_jsx(q.question)}`,
    options: [
      {opts}
    ]
  }}''')

    return f'''### {title}

<Select questions={{[
{",".join(items)}
]}} />'''

def translate_to_jsx(questions: list[TranslateQuestion], title: str) -> str:
    """Convert translate questions to JSX Translate component."""
    if not questions:
        return ''

    items = []
    for q in questions:
        opts = ',\n      '.join([
            f'{{ text: `{escape_jsx(o["text"])}`, correct: {"true" if o["correct"] else "false"} }}'
            for o in q.options
        ])
        items.append(f'''  {{
    source: `{escape_jsx(q.source)}`,
    options: [
      {opts}
    ]
  }}''')

    return f'''### {title}

<Translate questions={{[
{",".join(items)}
]}} />'''

def dialogue_reorder_to_jsx(lines: list[DialogueLine], title: str) -> str:
    """Convert dialogue lines to JSX DialogueReorder component."""
    if not lines:
        return ''

    jsx_lines = ',\n  '.join([
        f'{{ text: `{escape_jsx(line.text)}`, order: {line.order} }}'
        for line in lines
    ])

    return f'''### {title}

<DialogueReorder lines={{[
  {jsx_lines}
]}} />'''

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

def mark_the_words_to_jsx(items: list[MarkTheWordsItem], title: str) -> str:
    """Convert mark-the-words items to JSX MarkTheWordsActivity components."""
    if not items:
        return ''

    jsx_parts = []
    for item in items:
        words_jsx = ', '.join([f'`{escape_jsx(w)}`' for w in item.correctWords])
        jsx_parts.append(f'''<MarkTheWordsActivity
  text={{`{escape_jsx(item.text)}`}}
  correctWords={{[{words_jsx}]}}
/>''')

    return f'''### {title}

<MarkTheWords>
{chr(10).join(jsx_parts)}
</MarkTheWords>'''

# =============================================================================
# CONTENT PROCESSING
# =============================================================================

def process_activities(body: str) -> str:
    """Convert activities section to JSX in-place, preserving document order."""
    # Find Activities section - matches # or ## Activities, Вправи, etc.
    match = re.search(
        r'(^#{1,2}\s+(?:Activities|Вправи(?:\s*\(Activities\))?))\n([\s\S]*?)(?=\n#{1,2}\s+(?:Vocabulary|Словник|Summary|Підсумок|Self-Assessment|Самооцінка|External|Зовнішні)|\Z)',
        body, re.MULTILINE
    )

    if not match:
        return body

    activities_header = match.group(1)
    activities_section = match.group(2)

    # Parse individual activities - these should remain H2
    activity_blocks = re.split(r'\n## ', '\n' + activities_section)
    activities_jsx_parts = []

    for block in activity_blocks:
        if not block.strip():
            continue

        # Parse activity type and title
        type_match = re.match(r'^([\w-]+):\s*(.+?)(?:\n|$)', block.strip())
        if not type_match:
            continue

        activity_type = type_match.group(1).lower()
        title = type_match.group(2).strip()
        raw_content = block.strip()[type_match.end():]

        # Extract instruction
        instruction, content = extract_instruction(raw_content)

        jsx = ''
        if activity_type == 'quiz':
            questions = parse_quiz(content)
            jsx = quiz_to_jsx(questions, title)
        elif activity_type == 'match-up':
            pairs = parse_match_up(content)
            jsx = match_up_to_jsx(pairs, title)
        elif activity_type == 'fill-in':
            items = parse_fill_in(content)
            jsx = fill_in_to_jsx(items, title)
        elif activity_type == 'true-false':
            items = parse_true_false(content)
            jsx = true_false_to_jsx(items, title)
        elif activity_type == 'unjumble':
            items = parse_unjumble(content)
            jsx = unjumble_to_jsx(items, title)
        elif activity_type == 'group-sort':
            data = parse_group_sort(content)
            jsx = group_sort_to_jsx(data, title)
        elif activity_type == 'anagram':
            items = parse_anagram(content)
            jsx = anagram_to_jsx(items, title)
        elif activity_type == 'error-correction':
            items = parse_error_correction(content)
            jsx = error_correction_to_jsx(items, title)
        elif activity_type == 'cloze':
            data = parse_cloze(content)
            jsx = cloze_to_jsx(data, title)
        elif activity_type == 'select':
            questions = parse_select(content)
            jsx = select_to_jsx(questions, title)
        elif activity_type == 'translate':
            questions = parse_translate(content)
            jsx = translate_to_jsx(questions, title)
        elif activity_type == 'dialogue-reorder':
            lines = parse_dialogue_reorder(content)
            jsx = dialogue_reorder_to_jsx(lines, title)
        elif activity_type == 'mark-the-words':
            items = parse_mark_the_words(content)
            jsx = mark_the_words_to_jsx(items, title)

        if jsx:
            activities_jsx_parts.append(jsx)

    # Build activities replacement with header (Standardize to H2 for Docusaurus TOC)
    if activities_jsx_parts:
        activities_jsx = '## 🎯 Activities\n\n' + '\n\n'.join(activities_jsx_parts)
    else:
        activities_jsx = ''

    # Replace activities section in-place (preserving document order)
    result = body[:match.start()] + activities_jsx + body[match.end():]
    return result

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
}

def convert_callouts(content: str) -> str:
    """Convert GitHub-style callouts to Docusaurus admonitions."""
    lines = content.split('\n')
    result = []
    i = 0

    while i < len(lines):
        line = lines[i]

        # Check for callout start: > [!type] (may have leading whitespace)
        callout_match = re.match(r'^(\s*)>\s*\[!(\w+)\]\s*(.*)', line)
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

def generate_mdx(md_content: str, module_num: int, yaml_activities: list[dict] | None = None) -> str:
    """Convert markdown content to MDX.

    Args:
        md_content: Markdown content
        module_num: Module number for sidebar
        yaml_activities: Optional list of activities from YAML file (takes precedence over embedded)
    """
    fm, body = parse_frontmatter(md_content)

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
import DialogueReorder from '@site/src/components/DialogueReorder';
import MarkTheWords, { MarkTheWordsActivity } from '@site/src/components/MarkTheWords';"""

    # Frontmatter
    frontmatter = f'''---
sidebar_position: {module_num}
sidebar_label: "{str(module_num).zfill(2)}. {escape_jsx(fm.get('title', 'Untitled'))}"
title: "{escape_jsx(fm.get('title', 'Untitled'))}"
description: "{escape_jsx(fm.get('subtitle', ''))}"
---
'''

    # Process activities
    if yaml_activities:
        # Use YAML activities - inject them into the body
        activities_jsx = '## 🎯 Activities\n\n' + yaml_activities_to_jsx(yaml_activities)
        # Remove any existing Activities section from body
        body = re.sub(
            r'(^#{1,2}\s+(?:Activities|Вправи(?:\s*\(Activities\))?))\n([\s\S]*?)(?=\n#{1,2}\s+(?:Vocabulary|Словник|Summary|Підсумок|Self-Assessment|Самооцінка|External|Зовнішні)|\Z)',
            '',
            body,
            flags=re.MULTILINE
        )
        # Find where to inject activities (before Vocabulary/Словник or Summary/Підсумок)
        inject_match = re.search(r'\n(#{1,2}\s+(?:Vocabulary|Словник|Summary|Підсумок))', body)
        if inject_match:
            processed = body[:inject_match.start()] + '\n\n' + activities_jsx + '\n' + body[inject_match.start():]
        else:
            # Append at end if no Vocabulary/Summary section
            processed = body + '\n\n' + activities_jsx
    else:
        # Process embedded activities (original behavior)
        processed = process_activities(body)

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
    processed = re.sub(r'^#{1,2} (Summary|Підсумок)', r'## 📋 \1', processed, flags=re.MULTILINE)
    processed = re.sub(r'^#{1,2} (Vocabulary|Словник)', r'## 📚 \1', processed, flags=re.MULTILINE)
    processed = re.sub(r'^#{1,2} (Self-Assessment|Самооцінка)', r'## ✅ \1', processed, flags=re.MULTILINE)
    processed = re.sub(r'^#{1,2} (External Resources?|Зовнішні ресурси)', r'## 🔗 \1', processed, flags=re.MULTILINE)

    # Build MDX
    parts = [frontmatter, imports, '', processed]

    return '\n'.join(parts)

# =============================================================================
# MAIN
# =============================================================================

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

            # Check for YAML activities file (e.g., 52-abstract.md -> 52-abstract.activities.yaml)
            yaml_file = md_file.parent / (md_file.stem + '.activities.yaml')
            yaml_activities = load_yaml_activities(yaml_file)
            if yaml_activities:
                print(f'    📋 Loading {len(yaml_activities)} activities from YAML')

            mdx_content = generate_mdx(md_content, module_num, yaml_activities)

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

if __name__ == '__main__':
    main()
