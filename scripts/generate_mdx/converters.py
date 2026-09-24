"""Content converters and JSX generators for MDX output.

Handles conversion of parsed activity data to JSX components,
callout processing, story/dialogue formatting, slug link resolution,
and MDX normalization.
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any

import yaml

from .dataclasses_ import (
    ComparativeStudyData,
    EssayResponseData,
    HighlightMorphemesItem,
    MotifFormulaData,
    PerformanceData,
    RitualSequencingData,
    VariantComparisonData,
)
from .reading_links import reading_href_for
from .unit_map import Edit, EditLog, LineEdits, LineSource
from .utils import dump_json_for_jsx, escape_jsx

# Ensure scripts/ is on sys.path for sibling imports
_SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from manifest_utils import get_module_by_slug
from yaml_activities import Activity, ActivityParser


def _activity_id(activity: Activity) -> str:
    if isinstance(activity, dict):
        return str(activity.get('id', '') or '').strip()
    return str(getattr(activity, 'id', '') or '').strip()


def _activity_type(activity: Activity) -> str:
    if isinstance(activity, dict):
        return str(activity.get('type', '') or '').strip() or 'unknown'
    return str(getattr(activity, 'type', '') or '').strip() or 'unknown'


def _activity_title_or_type(activity: Activity) -> str:
    if isinstance(activity, dict):
        title = str(activity.get('title', '') or '').strip()
    else:
        title = str(getattr(activity, 'title', '') or '').strip()
    return title or _activity_type(activity)


def activity_identity_key(activity: Activity) -> str:
    """Return a stable activity key that ignores optional renderer IDs."""
    if is_dataclass(activity):
        payload: Any = asdict(activity)
    elif isinstance(activity, dict):
        payload = dict(activity)
    elif hasattr(activity, '__dict__'):
        payload = dict(vars(activity))
    else:
        payload = repr(activity)

    if isinstance(payload, dict):
        payload.pop('id', None)
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)


def yaml_activities_to_jsx(
    activities: list[Activity],
    is_ukrainian_forced: bool = False,
    inline_cross_ref_ids: set[str] | None = None,
    inline_cross_ref_positions: set[int] | None = None,
    inline_cross_ref_fingerprints: set[str] | None = None,
    inline_cross_ref_section_titles: dict[str, str] | None = None,
) -> str:
    """Convert YAML activities to JSX components using the shared ActivityParser.

    Activities already injected into the Lesson tab render as compact
    cross-references in the workbook tab. Matching uses ID first, plus the
    matched list position; structural fingerprints still suppress duplicate
    idless copies so they do not render in full.
    """
    return '\n\n'.join(
        mdx
        for _activity_id_or_none, mdx in yaml_activity_mdx_parts(
            activities,
            is_ukrainian_forced,
            inline_cross_ref_ids=inline_cross_ref_ids,
            inline_cross_ref_positions=inline_cross_ref_positions,
            inline_cross_ref_fingerprints=inline_cross_ref_fingerprints,
            inline_cross_ref_section_titles=inline_cross_ref_section_titles,
        )
    )


def yaml_activity_mdx_parts(
    activities: list[Activity],
    is_ukrainian_forced: bool = False,
    inline_cross_ref_ids: set[str] | None = None,
    inline_cross_ref_positions: set[int] | None = None,
    inline_cross_ref_fingerprints: set[str] | None = None,
    inline_cross_ref_section_titles: dict[str, str] | None = None,
) -> list[tuple[str | None, str]]:
    """The workbook tab's parts in order: `(activity id, component JSX)` for a full activity,
    `(None, mdx)` for an inline cross-reference. `yaml_activities_to_jsx` joins them."""
    parser = ActivityParser()
    inline_ids = {
        str(activity_id).strip()
        for activity_id in (inline_cross_ref_ids or set())
        if str(activity_id).strip()
    }
    inline_positions = set(inline_cross_ref_positions or set())
    inline_fingerprints = set(inline_cross_ref_fingerprints or set())
    section_titles = inline_cross_ref_section_titles or {}
    cross_referencing = bool(inline_ids or inline_positions or inline_fingerprints)

    parts: list[tuple[str | None, str]] = []
    for index, activity in enumerate(activities):
        activity_id = _activity_id(activity)
        if cross_referencing and (index in inline_positions or activity_id in inline_ids):
            parts.append(
                (
                    None,
                    _inline_activity_cross_ref_to_mdx(
                        activity,
                        section_titles.get(activity_id, ""),
                        is_ukrainian_forced,
                    ),
                )
            )
            continue
        if cross_referencing and activity_identity_key(activity) in inline_fingerprints:
            continue
        mdx = parser._activity_to_mdx(activity, is_ukrainian_forced)
        if not mdx:
            continue
        parts.append((activity_id or None, mdx))
    return parts


def _inline_activity_cross_ref_to_mdx(
    activity: Activity,
    section_title: str,
    is_ukrainian_forced: bool,
) -> str:
    title = escape_jsx(_activity_title_or_type(activity))
    section_title = section_title.strip()
    if section_title:
        if is_ukrainian_forced:
            reference = f"див. розділ, §{escape_jsx(section_title)}"
        else:
            reference = f"see lesson, §{escape_jsx(section_title)}"
    elif is_ukrainian_forced:
        reference = "див. вкладку «Урок»"
    else:
        reference = "see lesson tab"
    return f"### {title}\n\n*({reference})*"


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

<HighlightMorphemes client:only='react' isUkrainian={{{'true' if is_ukrainian_forced else 'false'}}}>
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

<EssayResponse client:only='react'
  title="{escape_jsx(title)}"
  prompt={{`{escape_jsx(data.prompt)}`}}
  modelAnswer={{`{escape_jsx(data.modelAnswer)}`}}
  rubric={{`{escape_jsx(data.rubric)}`}}
  isUkrainian={{{'true' if is_ukrainian_forced else 'false'}}}
/>'''


def comparative_study_to_jsx(data: ComparativeStudyData, title: str, is_ukrainian_forced: bool = False) -> str:
    """Convert comparative-study data to JSX ComparativeStudy component."""
    return f'''### {title}

<ComparativeStudy client:only='react'
  title="{escape_jsx(title)}"
  content={{`{escape_jsx(data.content)}`}}
  task={{`{escape_jsx(data.task)}`}}
  modelAnswer={{`{escape_jsx(data.modelAnswer)}`}}
  isUkrainian={{{'true' if is_ukrainian_forced else 'false'}}}
/>'''


def ritual_sequencing_to_jsx(data: RitualSequencingData, title: str, is_ukrainian_forced: bool = False) -> str:
    """Convert ritual-sequencing data to JSX RitualSequencing component."""
    instruction_prop = f'\n  instruction={{`{escape_jsx(data.instruction)}`}}' if data.instruction else ''
    model_prop = f'\n  modelAnswer={{`{escape_jsx(data.modelAnswer)}`}}' if data.modelAnswer else ''
    return f'''### {title}

<RitualSequencing client:only='react'
  title="{escape_jsx(title)}"{instruction_prop}
  steps={{JSON.parse(`{dump_json_for_jsx(data.steps)}`)}}
  correctOrder={{JSON.parse(`{dump_json_for_jsx(data.correctOrder)}`)}}{model_prop}
  isUkrainian={{{'true' if is_ukrainian_forced else 'false'}}}
/>'''


def variant_comparison_to_jsx(data: VariantComparisonData, title: str, is_ukrainian_forced: bool = False) -> str:
    """Convert variant-comparison data to JSX VariantComparison component."""
    variants = [
        {'label': item.label, 'text': item.text, 'region': item.region, 'source': item.source}
        for item in data.variants
    ]
    instruction_prop = f'\n  instruction={{`{escape_jsx(data.instruction)}`}}' if data.instruction else ''
    prompt_prop = f'\n  prompt={{`{escape_jsx(data.prompt)}`}}' if data.prompt else ''
    model_prop = f'\n  modelAnswer={{`{escape_jsx(data.modelAnswer)}`}}' if data.modelAnswer else ''
    return f'''### {title}

<VariantComparison client:only='react'
  title="{escape_jsx(title)}"{instruction_prop}
  variants={{JSON.parse(`{dump_json_for_jsx(variants)}`)}}
  features={{JSON.parse(`{dump_json_for_jsx(data.features)}`)}}{prompt_prop}{model_prop}
  isUkrainian={{{'true' if is_ukrainian_forced else 'false'}}}
/>'''


def motif_formula_to_jsx(data: MotifFormulaData, title: str, is_ukrainian_forced: bool = False) -> str:
    """Convert motif-formula data to JSX MotifFormula component."""
    formulas = [
        {'text': item.text, 'label': item.label, 'explanation': item.explanation}
        for item in data.formulas
    ]
    instruction_prop = f'\n  instruction={{`{escape_jsx(data.instruction)}`}}' if data.instruction else ''
    prompt_prop = f'\n  prompt={{`{escape_jsx(data.prompt)}`}}' if data.prompt else ''
    model_prop = f'\n  modelAnswer={{`{escape_jsx(data.modelAnswer)}`}}' if data.modelAnswer else ''
    return f'''### {title}

<MotifFormula client:only='react'
  title="{escape_jsx(title)}"{instruction_prop}
  passage={{`{escape_jsx(data.passage)}`}}
  formulas={{JSON.parse(`{dump_json_for_jsx(formulas)}`)}}{prompt_prop}{model_prop}
  isUkrainian={{{'true' if is_ukrainian_forced else 'false'}}}
/>'''


def performance_to_jsx(data: PerformanceData, title: str, is_ukrainian_forced: bool = False) -> str:
    """Convert performance data to JSX PerformanceActivity component."""
    instruction_prop = f'\n  instruction={{`{escape_jsx(data.instruction)}`}}' if data.instruction else ''
    fragment_prop = f'\n  fragment={{`{escape_jsx(data.fragment)}`}}' if data.fragment else ''
    self_check = data.selfCheck or []
    self_check_prop = f'\n  selfCheck={{JSON.parse(`{dump_json_for_jsx(self_check)}`)}}' if self_check else ''
    model_prop = f'\n  modelAnswer={{`{escape_jsx(data.modelAnswer)}`}}' if data.modelAnswer else ''
    record_value = 'true' if data.showRecordButton else 'false'
    return f'''### {title}

<PerformanceActivity client:only='react'
  title="{escape_jsx(title)}"{instruction_prop}
  prompt={{`{escape_jsx(data.prompt)}`}}{fragment_prop}{self_check_prop}
  showRecordButton={{{record_value}}}{model_prop}
  isUkrainian={{{'true' if is_ukrainian_forced else 'false'}}}
/>'''


# =============================================================================
# FOLK CONTENT BLOCK PROCESSING
# =============================================================================

_FOLK_CONTENT_BLOCK_RE = re.compile(
    r"^:::(myth-box|high-culture-bridge|primary-reading)([^\n]*)\n(.*?)\n:::\s*$",
    re.MULTILINE | re.DOTALL,
)
_DIRECTIVE_ATTR_RE = re.compile(r'([A-Za-z_][\w-]*)\s*=\s*"([^"]*)"')
_PRIMARY_READING_ATTRIBUTION_RE = re.compile(r"^—[^\n]*[«\"“](?P<title>[^»\"”]+)[»\"”]", re.MULTILINE)


def _yaml_directive_payload(raw: str) -> dict[str, Any]:
    payload = yaml.safe_load(raw) if raw.strip() else {}
    return payload if isinstance(payload, dict) else {}


def _directive_attrs(raw: str) -> dict[str, str]:
    raw = raw.strip()
    if not raw.startswith("{") or not raw.endswith("}"):
        return {}
    return {match.group(1): match.group(2).strip() for match in _DIRECTIVE_ATTR_RE.finditer(raw[1:-1])}


def _primary_reading_work_title(content: str) -> str:
    matches = list(_PRIMARY_READING_ATTRIBUTION_RE.finditer(content))
    if not matches:
        return ""
    return matches[-1].group("title").strip()


def convert_folk_content_blocks(content: str) -> str:
    """Convert folk text-layer directives to dedicated MDX components."""
    log = EditLog(content, record=False)
    edit_convert_folk_content_blocks(log)
    return log.text


def edit_convert_folk_content_blocks(log: EditLog) -> None:
    """`convert_folk_content_blocks` on an `EditLog`: each directive block is one replacement edit."""

    def replace(match: re.Match[str]) -> str:
        block_type = match.group(1)
        raw_attrs = match.group(2)
        block_content = match.group(3).strip()
        if block_type == 'primary-reading':
            attrs = _directive_attrs(raw_attrs)
            work = attrs.get("reading") or _primary_reading_work_title(block_content)
            href = reading_href_for(work) if work else None
            anchor = f'reading-{attrs["reading"]}' if attrs.get("reading") else ""
            id_prop = f' id="{escape_jsx(anchor)}"' if anchor else ''
            href_prop = f' href="{escape_jsx(href)}"' if href else ''
            return f"<PrimaryReading{id_prop}{href_prop}>\n\n{block_content}\n\n</PrimaryReading>\n"

        payload = _yaml_directive_payload(block_content)
        if block_type == 'myth-box':
            claim = str(payload.get('claim', '')).strip()
            truth = str(payload.get('truth', '')).strip()
            if not claim or not truth:
                return "{/** Invalid myth-box: claim and truth are required */}"
            title = str(payload.get('title', '')).strip()
            claim_source = str(payload.get('claim_source') or payload.get('claimSource') or '').strip()
            truth_source = str(payload.get('truth_source') or payload.get('truthSource') or '').strip()
            title_prop = f'\n  title={{`{escape_jsx(title)}`}}' if title else ''
            claim_source_prop = f'\n  claimSource={{`{escape_jsx(claim_source)}`}}' if claim_source else ''
            truth_source_prop = f'\n  truthSource={{`{escape_jsx(truth_source)}`}}' if truth_source else ''
            return (
                "<MythBuster"
                f"{title_prop}\n"
                f"  claim={{`{escape_jsx(claim)}`}}{claim_source_prop}\n"
                f"  truth={{`{escape_jsx(truth)}`}}{truth_source_prop}\n"
                "/>"
            )

        nodes = payload.get('nodes', [])
        if not isinstance(nodes, list) or len(nodes) < 2:
            return "{/** Invalid high-culture-bridge: at least two nodes are required */}"
        clean_nodes = [str(node).strip() for node in nodes if str(node).strip()]
        if len(clean_nodes) < 2:
            return "{/** Invalid high-culture-bridge: at least two nodes are required */}"
        title = str(payload.get('title', '')).strip()
        note = str(payload.get('note', '')).strip()
        title_prop = f'\n  title={{`{escape_jsx(title)}`}}' if title else ''
        note_prop = f'\n  note={{`{escape_jsx(note)}`}}' if note else ''
        return (
            "<HighCultureBridge"
            f"{title_prop}\n"
            f"  nodes={{JSON.parse(`{dump_json_for_jsx(clean_nodes)}`)}}{note_prop}\n"
            "/>\n\n"
        )

    log.sub(_FOLK_CONTENT_BLOCK_RE, replace)


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

def convert_bad_form_markers(content: str, strip_only: bool = False) -> str:
    """Convert or strip decolonization markers (<!-- bad -->X<!-- /bad -->).

    If strip_only is True, unwraps to the bare form (X).
    Otherwise, converts to semantic strikethrough (<del>X</del>).
    Also strips any orphaned markers.
    """
    log = EditLog(content, record=False)
    edit_convert_bad_form_markers(log, strip_only)
    return log.text


def edit_convert_bad_form_markers(log: EditLog, strip_only: bool = False) -> None:
    """`convert_bad_form_markers` on an `EditLog`: the marked form stays in place, markers are edits."""
    if strip_only:
        # Unwrap to bare form X
        log.sub(r'<!--\s*bad\s*-->(.*?)<!--\s*/bad\s*-->', r'\1', flags=re.DOTALL)
    else:
        # Convert to <del>X</del>
        log.sub(r'<!--\s*bad\s*-->(.*?)<!--\s*/bad\s*-->', r'<del>\1</del>', flags=re.DOTALL)

    # Strip any remaining orphaned/unpaired markers so they don't leak
    log.sub(r'<!--\s*/?bad\s*-->', '')


def convert_callouts(content: str, is_ukrainian_forced: bool = False) -> str:
    """Convert GitHub-style callouts to Site admonitions.

    Robustly handles:
    1. Standard: > [!type]
    2. Lazy: [!type] (missing marker)
    3. Spaced: [!type] \\n\\n > content (blank lines before content)
    """
    log = EditLog(content, record=False)
    edit_convert_callouts(log, is_ukrainian_forced)
    return log.text


def edit_convert_callouts(log: EditLog, is_ukrainian_forced: bool = False) -> None:
    """`convert_callouts` on an `EditLog`.

    Reported line by line: a callout header and the admonition fence lines are edits, a
    blockquote content line keeps its bytes after the stripped `> ` prefix (a slice), a
    lazy-format content line is kept whole, skipped blank lines are removed.
    """
    out = LineEdits(log.text, record=log.record)
    lines = out.lines
    # Content lines of the current callout: `(text, source)` in `LineEdits` terms.
    callout_lines: list[tuple[str, LineSource]]
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
                        content_start = cont_match.start(1)
                        if cont_match.group(1).startswith(' '):
                            content_start += 1
                        callout_lines.append(_line_slice(lines, i, content_start, len(lines[i])))
                        i += 1
                    elif not lines[i].strip():
                        # Peek at next line: if it has > and IS NOT a callout header, keep going
                        if i + 1 < len(lines):
                            next_line = lines[i+1]
                            next_is_bq = next_line.strip().startswith('>')
                            next_is_header = next_is_bq and re.match(r'^(\s*)[>\s]*\[![\w-]+\]', next_line)
                            if next_is_bq and not next_is_header:
                                callout_lines.append(_line_slice(lines, i, 0, 0))
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
                    callout_lines.append(_line_slice(lines, i, 0, len(curr)))
                    i += 1

            # Special handling for solution callouts
            if callout_type == 'solution':
                out.new('<details className="solution-block">')
                out.new(f'<summary>{title}</summary>')
                out.new('')
                for text, source in callout_lines:
                    out._append(text, source)
                out.new('')
                out.new('</details>')
                out.new('')
            else:
                # Output Site admonition
                out.new(f':::{admon_type}[{title}]')
                for text, source in callout_lines:
                    out._append(text, source)
                out.new(':::')
                out.new('')
        else:
            out.keep(i)
            i += 1

    _apply_lines(log, out)


def _line_slice(lines: list[str], index: int, start: int, end: int) -> tuple[str, LineSource]:
    """Output line `lines[index][start:end]` with its `LineEdits` source."""
    return lines[index][start:end], (index, [(start, 0, end - start)])


def _apply_lines(log: EditLog, out: LineEdits) -> None:
    """Advance `log` by a line-based transform's output."""
    if log.record:
        log.apply(out.edits(), out.text())
    else:
        log.text = out.text()


def process_story_sections(content: str) -> str:
    """Add blank lines between narrative lines in story sections.

    Story sections (### Story Time, ### Dialogue, etc.) contain narrative
    paragraphs that need blank lines between them for proper Markdown rendering.
    This function detects story headers and adds blank lines between non-blank
    lines until the next header.

    Note: Dialog lines (starting with em-dash) are left consecutive so that
    process_dialogues can wrap them in conversation containers.
    """
    log = EditLog(content, record=False)
    edit_process_story_sections(log)
    return log.text


def edit_process_story_sections(log: EditLog) -> None:
    """`process_story_sections` on an `EditLog`: every input line is kept, blank lines are insertions."""
    out = LineEdits(log.text, record=log.record)
    lines = out.lines
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
            out.keep(i)
            out.new('')
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
                    out.keep(i)
                    i += 1
                    continue

                # Add the line
                out.keep(i)

                # Look ahead - if next line is non-blank content (not a header, not blank),
                # add a blank line after current line UNLESS both lines are dialog lines or table rows
                if i + 1 < len(lines):
                    next_stripped = lines[i + 1].strip()
                    current_is_dialog = current_stripped.startswith('\u2014')
                    next_is_dialog = next_stripped.startswith('\u2014')
                    current_is_table = current_stripped.startswith('|')
                    next_is_table = next_stripped.startswith('|')

                    # Add blank line only if NOT both dialog lines and NOT both table rows
                    if (
                        next_stripped
                        and not any_header_pattern.match(next_stripped)
                        and not (current_is_dialog and next_is_dialog)
                        and not (current_is_table and next_is_table)
                    ):
                        out.new('')

                i += 1
        else:
            out.keep(i)
            i += 1

    _apply_lines(log, out)


def process_dialogues(content: str) -> str:
    """Group consecutive V6/V7 dialogue blockquotes into DialogueBox components."""
    log = EditLog(content, record=False)
    edit_process_dialogues(log)
    return log.text


def edit_process_dialogues(log: EditLog) -> None:
    """`process_dialogues` on an `EditLog`: a grouped dialogue (and its title line) is replaced."""
    out = LineEdits(log.text, record=log.record)
    lines = out.lines
    result = out.out
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

        # Check if this starts a dialogue sequence (outside JSX)
        first_exchange = _parse_dialogue_line(stripped)
        if first_exchange and inside_jsx == 0 and '`' not in line:
            # Collect consecutive dialog lines (stop at blank line)
            start = i
            exchanges = []
            while i < len(lines):
                current = lines[i].strip()
                parsed = _parse_dialogue_line(current)
                if parsed and '`' not in lines[i]:
                    exchanges.append(parsed)
                    i += 1
                elif re.match(r'^>\s*$', current):
                    i += 1
                else:
                    # Stop at any non-dialog line (including blank)
                    break

            # Only wrap if we have 2+ dialog lines (actual conversation)
            if len(exchanges) >= 2:
                title, title_index = _dialogue_title(result)
                if title_index is not None:
                    out.delete(title_index)
                out.new(_dialogue_box_mdx(exchanges, title))
            else:
                # Single line - just keep as-is
                for index in range(start, i):
                    out.keep(index)
        else:
            out.keep(i)
            i += 1

    _apply_lines(log, out)


_DIALOGUE_LINE_RE = re.compile(
    r'^>\s*(?:\u2014\s*)?\*\*(?P<speaker>[^:*]+):\*\*\s*(?P<text>.+?)\s*$'
)


def _parse_dialogue_line(stripped_line: str) -> dict[str, str] | None:
    match = _DIALOGUE_LINE_RE.match(stripped_line)
    if not match:
        return None
    text = re.sub(r'\s*\*\([^)]*\)\*\s*$', '', match.group('text')).strip()
    return {"speaker": match.group('speaker').strip(), "text": text}


DIALOGUE_BOX_DEFAULT_TITLE = "Діалог"
# The DialogueBox component line that carries the exchanges: a JSON payload (`json.dumps`,
# compact separators) escaped for a single-quoted JS string literal and parsed by the page.
DIALOGUE_BOX_PAYLOAD_PREFIX = "  exchanges={JSON.parse('"
DIALOGUE_BOX_PAYLOAD_SUFFIX = "')}"


def _dialogue_title(previous_lines: list[str]) -> tuple[str, int | None]:
    start = max(0, len(previous_lines) - 3)
    for index in range(len(previous_lines) - 1, start - 1, -1):
        line = previous_lines[index]
        stripped = line.strip()
        match = re.match(r'^\*\*(Діалог\s+\d+\s+[\u2014-]\s+.+?)\*\*$', stripped)
        if match:
            return match.group(1), index
    return DIALOGUE_BOX_DEFAULT_TITLE, None


DIALOGUE_BOX_CLOSING_LINE = "/>"


def dialogue_box_header_lines(title: str) -> list[str]:
    """The DialogueBox component's opening lines, before the exchanges payload line."""
    safe_title = title.replace('"', '&quot;')
    return ['<DialogueBox', '  client:only="react"', f'  title="{safe_title}"']


def dialogue_box_jsx_lines(escaped_payload: str, title: str) -> list[str]:
    """The DialogueBox component, line by line, around an already escaped exchanges payload."""
    return [
        *dialogue_box_header_lines(title),
        f"{DIALOGUE_BOX_PAYLOAD_PREFIX}{escaped_payload}{DIALOGUE_BOX_PAYLOAD_SUFFIX}",
        DIALOGUE_BOX_CLOSING_LINE,
    ]


def _dialogue_box_mdx(exchanges: list[dict[str, str]], title: str) -> str:
    payload = json.dumps(exchanges, ensure_ascii=False, separators=(',', ':'))
    payload = payload.replace('\\', '\\\\').replace("'", "\\'")
    return '\n'.join(dialogue_box_jsx_lines(payload, title))


def resolve_slug_links(content: str) -> str:
    """Replace [slug:xxx] links with actual module title and path.

    This allows content to reference other modules by slug instead of
    hardcoded paths, making the curriculum resilient to renumbering.

    Example:
        Input:  See [slug:the-cyrillic-code-i] for details.
        Output: See [The Cyrillic Code I](/a1/module-01) for details.
    """
    log = EditLog(content, record=False)
    edit_resolve_slug_links(log)
    return log.text


def edit_resolve_slug_links(log: EditLog) -> None:
    """`resolve_slug_links` on an `EditLog`: each resolved link is one replacement edit."""
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
    log.sub(r'\[slug:([a-z0-9-]+)\]', replace_slug)


def normalize_mdx(text: str) -> str:
    """Normalize MDX output to fix common markdownlint violations.

    Fixes: MD009 (trailing spaces), MD004 (list marker *->-), MD030 (list spacing),
    MD049 (_->*), MD050 (__->**), MD012 (multiple blanks), MD022 (heading blanks),
    MD047 (trailing newline).

    Skips JSX blocks, fenced code blocks, URLs, and inline code to avoid corruption.
    """
    log = EditLog(text, record=False)
    edit_normalize_mdx(log)
    return log.text


_EMPHASIS_SPLIT_RE = re.compile(r'(\[[^\]]*\]\([^)]*\)|`[^`]+`)')


def edit_normalize_mdx(log: EditLog) -> None:
    """`normalize_mdx` on an `EditLog`.

    Every per-line fix is recorded on the line's own log (trailing whitespace, list markers
    and emphasis markers are edits; list text and emphasized text stay in place), the
    heading blank lines are insertions, and the fenced code blocks stashed while those
    run are reported as replaced by their placeholder and back (a unit inside a fenced
    code block is therefore lost by this transform; the renderer emits none).
    """
    out = LineEdits(log.text, record=log.record)
    in_code_fence = False

    for i, line in enumerate(out.lines):
        stripped = line.strip()

        # Track fenced code blocks
        if stripped.startswith('```'):
            in_code_fence = not in_code_fence
            out.slice(i, 0, len(line.rstrip()))
            continue

        if in_code_fence:
            out.slice(i, 0, len(line.rstrip()))
            continue

        # Skip JSX / import lines (only strip trailing whitespace)
        if (stripped.startswith(('<', '{', '/>', '</', 'import ')) or
                'className=' in line):
            out.slice(i, 0, len(line.rstrip()))
            continue

        # Skip table rows (pipes would cause false positives)
        if stripped.startswith('|'):
            out.slice(i, 0, len(line.rstrip()))
            continue

        line_log = EditLog(line, record=log.record)

        # MD009: strip trailing whitespace
        line_log.replace(len(line.rstrip()), len(line), '')

        # MD004: * list marker -> - (including inside blockquotes)
        line_log.sub(r'^(\s*(?:>\s*)*)\*(?= )', r'\1-')

        # MD030: normalize spaces after list markers to exactly 1
        line_log.sub(r'^(\s*(?:>\s*)*(?:[-*+]|\d+\.))\s{2,}', r'\1 ')

        # MD049/MD050: normalize emphasis markers
        # Split on code spans AND markdown link targets to preserve URLs and code
        if '_' in line_log.text:
            edits: list[Edit] = []
            new_parts = []
            offset = 0
            for j, part in enumerate(_EMPHASIS_SPLIT_RE.split(line_log.text)):
                if j % 2 == 1:  # inside link target or backticks - preserve
                    new_parts.append(part)
                else:
                    part_log = EditLog(part, record=log.record)
                    # MD050: __text__ -> **text**
                    part_log.sub(r'(?<!\w)__(?!\s)(.+?)(?<!\s)__(?!\w)', r'**\1**')
                    # MD049: _text_ -> *text*
                    part_log.sub(r'(?<!\w)_(?!\s)([^_]+?)(?<!\s)_(?!\w)', r'*\1*')
                    if log.record:
                        edits.extend(
                            Edit(edit.start + offset, edit.end + offset, edit.replacement)
                            for edit in part_log.edits()
                        )
                    new_parts.append(part_log.text)
                offset += len(part)
            line_log.apply(edits, ''.join(new_parts))

        out.edited(i, line_log)

    _apply_lines(log, out)

    # MD022: blank lines around headings
    # Protect fenced code blocks from heading regex by temporarily replacing them
    code_blocks = []
    def _stash_code_block(match):
        code_blocks.append(match.group(0))
        return f'\x00CODEBLOCK{len(code_blocks) - 1}\x00'
    log.sub(r'```[^\n]*\n.*?```', _stash_code_block, flags=re.DOTALL)

    log.sub(r'(\S[^\n]*)\n(#{1,6} )', r'\1\n\n\2')
    log.sub(r'(#{1,6} [^\n]+)\n(\S)', r'\1\n\n\2')

    # Restore code blocks
    for i, block in enumerate(code_blocks):
        log.sub(re.escape(f'\x00CODEBLOCK{i}\x00'), lambda _match, block=block: block)

    # MD012: collapse 3+ consecutive newlines to 2 (max 1 blank line)
    log.sub(r'\n{3,}', '\n\n')

    # MD047: ensure single trailing newline
    log.replace(len(log.text.rstrip('\n')), len(log.text), '\n')
