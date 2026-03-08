"""Content converters and JSX generators for MDX output.

Handles conversion of parsed activity data to JSX components,
callout processing, story/dialogue formatting, slug link resolution,
and MDX normalization.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

from .dataclasses_ import (
    ComparativeStudyData,
    EssayResponseData,
    HighlightMorphemesItem,
)
from .utils import escape_jsx

# Ensure scripts/ is on sys.path for sibling imports
_SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from manifest_utils import get_module_by_slug  # noqa: E402
from yaml_activities import Activity, ActivityParser  # noqa: E402


def yaml_activities_to_jsx(activities: list[Activity], is_ukrainian_forced: bool = False) -> str:
    """Convert YAML activities to JSX components using the shared ActivityParser."""
    parser = ActivityParser()
    return parser.to_mdx(activities, is_ukrainian_forced)


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
# CALLOUT PROCESSING
# =============================================================================

# Callout mapping
CALLOUT_MAP = {
    'tip': {'type': 'tip', 'icon': '\U0001f4a1', 'title': 'Tip', 'uk_title': 'Порада'},
    'note': {'type': 'note', 'icon': '\U0001f4dd', 'title': 'Note', 'uk_title': 'Примітка'},
    'warning': {'type': 'warning', 'icon': '\u26a0\ufe0f', 'title': 'Warning', 'uk_title': 'Увага'},
    'important': {'type': 'warning', 'icon': '\u2757', 'title': 'Important', 'uk_title': 'Важливо'},
    'caution': {'type': 'caution', 'icon': '\u2622\ufe0f', 'title': 'Caution', 'uk_title': 'Обережно'},
    'info': {'type': 'info', 'icon': '\u2139\ufe0f', 'title': 'Info', 'uk_title': 'Інформація'},
    'observe': {'type': 'tip', 'icon': '\U0001f50d', 'title': 'Pattern Discovery', 'uk_title': 'Спостереження'},
    'resources': {'type': 'info', 'icon': '\U0001f3a7', 'title': 'External Resources', 'uk_title': 'Зовнішні ресурси'},
    'example': {'type': 'info', 'icon': '\U0001f4dd', 'title': 'Example', 'uk_title': 'Приклад'},
    'conversation': {'type': 'note', 'icon': '\U0001f4ac', 'title': 'Conversation', 'uk_title': 'Розмова'},
    'summary': {'type': 'note', 'icon': '\U0001f4cb', 'title': 'Summary', 'uk_title': 'Підсумок'},
    'solution': {'type': 'solution'},  # Collapsible answer reveal for checkpoints
    'model-answer': {'type': 'success', 'icon': '\u2705', 'title': 'Model Answer', 'uk_title': 'Модельна відповідь'},
    'rubric': {'type': 'info', 'icon': '\U0001f4ca', 'title': 'Rubric', 'uk_title': 'Критерії оцінювання'},
    'analysis': {'type': 'info', 'icon': '\U0001f9d0', 'title': 'Analysis', 'uk_title': 'Аналіз'},
    'history-bite': {'type': 'info', 'icon': '\U0001f570\ufe0f', 'title': 'History Bite', 'uk_title': 'Історична довідка'},
    'myth-buster': {'type': 'danger', 'icon': '\U0001f6e1\ufe0f', 'title': 'Myth Buster', 'uk_title': 'Руйнівник міфів'},
    'quote': {'type': 'note', 'icon': '\U0001f4dc', 'title': 'Quote', 'uk_title': 'Цитата'},
    'context': {'type': 'info', 'icon': '\U0001f30d', 'title': 'Context', 'uk_title': 'Контекст'},
    'legacy': {'type': 'tip', 'icon': '\U0001f48e', 'title': 'Legacy', 'uk_title': 'Спадщина'},
    'reflection': {'type': 'info', 'icon': '\U0001f914', 'title': 'Reflection', 'uk_title': 'Роздуми'},
    'source': {'type': 'note', 'icon': '\U0001f4d6', 'title': 'Source', 'uk_title': 'Джерело'},
    'culture': {'type': 'note', 'icon': '\U0001f3fa', 'title': 'Culture', 'uk_title': 'Культура'},
    'cultural': {'type': 'note', 'icon': '\U0001f3fa', 'title': 'Cultural Context', 'uk_title': 'Культура'},
    'culture-note': {'type': 'note', 'icon': '\U0001f3fa', 'title': 'Culture Note', 'uk_title': 'Культурна примітка'},
    'culture-spot': {'type': 'info', 'icon': '\U0001f30d', 'title': 'Culture Spot', 'uk_title': 'Культурний куточок'},
    'heritage': {'type': 'tip', 'icon': '\U0001f48e', 'title': 'Heritage', 'uk_title': 'Спадщина'},
    'history': {'type': 'info', 'icon': '\U0001f570\ufe0f', 'title': 'History', 'uk_title': 'Історія'},
    'historical': {'type': 'info', 'icon': '\U0001f570\ufe0f', 'title': 'Historical Context', 'uk_title': 'Історичний контекст'},
    'narrative': {'type': 'note', 'icon': '\U0001f4d6', 'title': 'Narrative', 'uk_title': 'Розповідь'},
    'interactive': {'type': 'tip', 'icon': '\U0001f3ae', 'title': 'Interactive', 'uk_title': 'Інтерактив'},
    'vocabulary': {'type': 'info', 'icon': '\U0001f4da', 'title': 'Vocabulary', 'uk_title': 'Словник'},
    'grammar': {'type': 'info', 'icon': '\u2699\ufe0f', 'title': 'Grammar', 'uk_title': 'Граматика'},
    'idiom': {'type': 'success', 'icon': '\U0001f5e3\ufe0f', 'title': 'Idiom', 'uk_title': 'Фразеологізм'},
    'proverb': {'type': 'success', 'icon': '\U0001f4dc', 'title': 'Proverb', 'uk_title': "Прислів\u2019я"},
    'language-note': {'type': 'info', 'icon': '\U0001f50d', 'title': 'Language Note', 'uk_title': 'Мовна примітка'},
    'did-you-know': {'type': 'info', 'icon': '\U0001f4a1', 'title': 'Did You Know?', 'uk_title': 'Чи знали ви?'},
    'fact': {'type': 'info', 'icon': '\u2139\ufe0f', 'title': 'Fact', 'uk_title': 'Факт'},
    'profile': {'type': 'note', 'icon': '\U0001f464', 'title': 'Profile', 'uk_title': 'Портрет'},
    'language-point': {'type': 'info', 'icon': '\U0001f4a1', 'title': 'Language Point', 'uk_title': 'Мовний момент'},
    'ponder': {'type': 'info', 'icon': '\U0001f4ad', 'title': 'Ponder', 'uk_title': 'Поміркуйте'},
    'real-world': {'type': 'tip', 'icon': '\U0001f310', 'title': 'Real World', 'uk_title': 'Реальний світ'},
    'realworld': {'type': 'tip', 'icon': '\U0001f310', 'title': 'Real World', 'uk_title': 'Реальний світ'},
}


def convert_callouts(content: str, is_ukrainian_forced: bool = False) -> str:
    """Convert GitHub-style callouts to Docusaurus admonitions.

    Robustly handles:
    1. Standard: > [!type]
    2. Lazy: [!type] (missing marker)
    3. Spaced: [!type] \\n\\n > content (blank lines before content)
    """
    lines = content.split('\n')
    result = []
    i = 0

    while i < len(lines):
        line = lines[i]

        # Check for callout start: any sequence of > and whitespace + [!type] or [\!type]
        callout_match = re.match(r'^(\s*)[>\s]*\[\\?!([\w-]+)\]\s*(.*)', line)
        if callout_match:
            callout_match.group(1)
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
                result.append('<details className="solution-block">')
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

    Note: Dialog lines (starting with em-dash) are left consecutive so that
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
                # add a blank line after current line UNLESS both lines are dialog lines
                if i + 1 < len(lines):
                    next_stripped = lines[i + 1].strip()
                    current_is_dialog = current_stripped.startswith('\u2014')
                    next_is_dialog = next_stripped.startswith('\u2014')

                    # Add blank line only if NOT both dialog lines
                    if next_stripped and not any_header_pattern.match(next_stripped) and not (current_is_dialog and next_is_dialog):
                            result.append('')

                i += 1
        else:
            result.append(line)
            i += 1

    return '\n'.join(result)


def process_dialogues(content: str) -> str:
    """Group consecutive dialog lines into conversation blocks.

    Detects sequences of lines starting with em-dash and wraps
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
        if stripped.startswith('\u2014') and inside_jsx == 0 and '`' not in line:
            # Collect consecutive dialog lines (stop at blank line)
            dialog_lines = []
            while i < len(lines):
                current = lines[i].strip()
                if current.startswith('\u2014') and '`' not in lines[i]:
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


def resolve_slug_links(content: str) -> str:
    """Replace [slug:xxx] links with actual module title and path.

    This allows content to reference other modules by slug instead of
    hardcoded paths, making the curriculum resilient to renumbering.

    Example:
        Input:  See [slug:the-cyrillic-code-i] for details.
        Output: See [The Cyrillic Code I](/a1/module-01) for details.
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
                if j % 2 == 1:  # inside link target or backticks - preserve
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
