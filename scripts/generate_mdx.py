#!/usr/bin/env python3
"""
MDX Generator for Docusaurus

Converts curriculum markdown modules to MDX format with React components.

Usage:
    python scripts/generate_mdx.py [lang_pair] [level] [module_num]

Examples:
    python scripts/generate_mdx.py l2-uk-en           # All levels
    python scripts/generate_mdx.py l2-uk-en a1        # All A1 modules
    python scripts/generate_mdx.py l2-uk-en a1 5      # Module 5 only
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
    incorrect: str
    correct: str
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
    """Parse quiz activity with numbered questions."""
    questions = []

    # Split by numbered items, capturing everything until next number or end
    blocks = re.split(r'(?=^\d+\.\s)', content, flags=re.MULTILINE)

    for block in blocks:
        block = block.strip()
        if not block or not re.match(r'^\d+\.', block):
            continue

        # Remove the number prefix
        block = re.sub(r'^\d+\.\s*', '', block)
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

    # Try table format
    for line in content.split('\n'):
        line = line.strip()
        if line.startswith('|') and '|' in line[1:]:
            cells = [c.strip() for c in line.split('|')[1:-1]]
            if len(cells) >= 2 and cells[0] and cells[1] and not cells[0].startswith('-'):
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
        incorrect = lines[0].strip() if lines else ''
        correct = ''
        explanation = ''

        for line in lines[1:]:
            stripped = line.strip()
            if stripped.startswith('> [!correct]'):
                correct = stripped.replace('> [!correct]', '').strip()
            elif stripped.startswith('> [!explanation]'):
                explanation = stripped.replace('> [!explanation]', '').strip()

        if incorrect and correct:
            items.append(ErrorCorrectionItem(incorrect=incorrect, correct=correct, explanation=explanation))

    return items

def parse_cloze(content: str) -> ClozeData:
    """Parse cloze activity with passage and blanks."""
    lines = content.split('\n')
    passage_lines = []
    blanks = []
    in_passage = True

    for line in lines:
        stripped = line.strip()
        if stripped.startswith('> [!blank]'):
            in_passage = False
            blank_data = stripped.replace('> [!blank]', '').strip()
            # Parse: answer | opt1 | opt2 | opt3
            parts = [p.strip() for p in blank_data.split('|')]
            if parts:
                blanks.append({"answer": parts[0], "options": parts})
        elif in_passage:
            passage_lines.append(line)

    return ClozeData(passage='\n'.join(passage_lines).strip(), blanks=blanks)

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
    """Parse translate activity."""
    questions = []
    blocks = re.split(r'^\d+\.\s+', content, flags=re.MULTILINE)

    for block in blocks:
        if not block.strip():
            continue

        lines = block.split('\n')
        source = ''
        options = []

        for line in lines:
            stripped = line.strip()
            if stripped.startswith('- [x]'):
                options.append({"text": stripped[5:].strip(), "correct": True})
            elif stripped.startswith('- [ ]'):
                options.append({"text": stripped[5:].strip(), "correct": False})
            elif not options and not stripped.startswith('-'):
                source = (source + ' ' + stripped).strip()

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
        jsx_items.append(f'''  {{
    incorrect: `{escape_jsx(item.incorrect)}`,
    correct: `{escape_jsx(item.correct)}`,
    explanation: `{escape_jsx(item.explanation)}`
  }}''')

    return f'''### {title}

<ErrorCorrection items={{[
{",".join(jsx_items)}
]}} />'''

def cloze_to_jsx(data: ClozeData, title: str) -> str:
    """Convert cloze data to JSX Cloze component."""
    if not data.passage:
        return ''

    blanks_jsx = []
    for blank in data.blanks:
        opts = ', '.join([f'`{escape_jsx(o)}`' for o in blank.get("options", [])])
        blanks_jsx.append(f'{{ answer: `{escape_jsx(blank["answer"])}`, options: [{opts}] }}')

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

# =============================================================================
# CONTENT PROCESSING
# =============================================================================

def process_activities(body: str) -> tuple[str, str]:
    """Extract activities section and convert to JSX."""
    # Find Activities section - matches # Activities, # Вправи, # Вправи (Activities)
    match = re.search(
        r'# (?:Activities|Вправи(?:\s*\(Activities\))?)\n([\s\S]*?)(?=\n# (?:Vocabulary|Словник|Summary|Підсумок)|\n---\n# |$)',
        body
    )

    if not match:
        return body, ''

    activities_section = match.group(1)
    # Remove the entire activities section including header
    main_content = re.sub(
        r'# (?:Activities|Вправи(?:\s*\(Activities\))?)\n[\s\S]*?(?=\n# (?:Vocabulary|Словник|Summary|Підсумок)|\n---\n# |$)',
        '',
        body
    )

    # Parse individual activities
    activity_blocks = re.split(r'\n## ', activities_section)
    activities_jsx_parts = []

    for block in activity_blocks:
        if not block.strip():
            continue

        # Parse activity type and title
        type_match = re.match(r'^([\w-]+):\s*(.+?)(?:\n|$)', block)
        if not type_match:
            continue

        activity_type = type_match.group(1).lower()
        title = type_match.group(2).strip()
        raw_content = block[type_match.end():]

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

        if jsx:
            activities_jsx_parts.append(jsx)

    return main_content, '\n\n'.join(activities_jsx_parts)

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
}

def convert_callouts(content: str) -> str:
    """Convert GitHub-style callouts to Docusaurus admonitions."""
    lines = content.split('\n')
    result = []
    i = 0

    while i < len(lines):
        line = lines[i]

        # Check for callout start: > [!type]
        callout_match = re.match(r'^>\s*\[!(\w+)\]\s*(.*)', line)
        if callout_match:
            callout_type = callout_match.group(1).lower()
            title_extra = callout_match.group(2).strip()

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

            # Collect callout content
            callout_lines = []
            i += 1
            while i < len(lines) and lines[i].startswith('>'):
                callout_lines.append(lines[i][1:].strip() if len(lines[i]) > 1 else '')
                i += 1

            # Output Docusaurus admonition
            result.append(f':::{admon_type}[{title}]')
            result.extend(callout_lines)
            result.append(':::')
            result.append('')
        else:
            result.append(line)
            i += 1

    return '\n'.join(result)

def process_dialogues(content: str) -> str:
    """Add line breaks between dialogue turns."""
    # Find conversation admonitions and add breaks between — lines
    def add_breaks(match):
        block = match.group(0)
        lines = block.split('\n')
        result = []
        for j, line in enumerate(lines):
            result.append(line)
            if line.strip().startswith('—') and j + 1 < len(lines) and lines[j + 1].strip().startswith('—'):
                result.append('')
        return '\n'.join(result)

    return re.sub(r':::note\[.*?Conversation.*?\][\s\S]*?:::', add_breaks, content)

# =============================================================================
# MDX GENERATOR
# =============================================================================

def generate_mdx(md_content: str, module_num: int) -> str:
    """Convert markdown content to MDX."""
    fm, body = parse_frontmatter(md_content)

    # Component imports
    imports = """import Quiz from '@site/src/components/Quiz';
import MatchUp from '@site/src/components/MatchUp';
import FillIn from '@site/src/components/FillIn';
import TrueFalse from '@site/src/components/TrueFalse';
import Unjumble from '@site/src/components/Unjumble';
import GroupSort from '@site/src/components/GroupSort';
import Anagram from '@site/src/components/Anagram';
import ErrorCorrection from '@site/src/components/ErrorCorrection';
import Cloze from '@site/src/components/Cloze';
import Select from '@site/src/components/Select';
import Translate from '@site/src/components/Translate';
import DialogueReorder from '@site/src/components/DialogueReorder';"""

    # Frontmatter
    frontmatter = f'''---
sidebar_position: {module_num}
sidebar_label: "{str(module_num).zfill(2)}. {escape_jsx(fm.get('title', 'Untitled'))}"
title: "{escape_jsx(fm.get('title', 'Untitled'))}"
description: "{escape_jsx(fm.get('subtitle', ''))}"
---
'''

    # Process activities
    main_content, activities_jsx = process_activities(body)

    # Convert callouts
    processed = convert_callouts(main_content)

    # Process dialogues
    processed = process_dialogues(processed)

    # Remove duplicate H1 title
    processed = re.sub(r'^#\s+[^\n]+\n', '', processed, count=1)

    # Convert Summary and Vocabulary to H2 for TOC
    processed = re.sub(r'^# (Summary|Підсумок)', r'## 📋 \1', processed, flags=re.MULTILINE)
    processed = re.sub(r'^# (Vocabulary|Словник)', r'## 📚 \1', processed, flags=re.MULTILINE)

    # Build MDX
    parts = [frontmatter, imports, '', processed]

    if activities_jsx.strip():
        parts.extend(['---', '', '## 🎯 Activities', '', activities_jsx])

    return '\n'.join(parts)

# =============================================================================
# MAIN
# =============================================================================

def main():
    args = sys.argv[1:]
    lang_pair = args[0] if args else 'l2-uk-en'
    target_level = args[1].lower() if len(args) > 1 else None
    target_module = int(args[2]) if len(args) > 2 else None

    print('\n🚀 MDX Generator (Python)\n')
    print(f'Source: curriculum/{lang_pair}/')
    print(f'Output: docusaurus/docs/\n')

    curriculum_path = CURRICULUM_DIR / lang_pair
    levels = ['a1', 'a2', 'b1', 'b2', 'c1', 'c2']

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
            mdx_content = generate_mdx(md_content, module_num)

            # Write output
            output_file = output_dir / f'module-{str(module_num).zfill(2)}.mdx'
            output_file.write_text(mdx_content, encoding='utf-8')

            print(f'  ✓ Module {str(module_num).zfill(2)}')

    print('\n✅ MDX generation complete!')

if __name__ == '__main__':
    main()
