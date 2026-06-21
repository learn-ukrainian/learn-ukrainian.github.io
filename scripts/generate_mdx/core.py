"""Core MDX generation logic.

Contains the main generate_mdx function, frontmatter parsing,
pipeline detection, manifest module listing, and CLI entry point.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import yaml

from .converters import (
    activity_identity_key,
    convert_bad_form_markers,
    convert_callouts,
    convert_folk_content_blocks,
    normalize_mdx,
    process_dialogues,
    process_story_sections,
    resolve_slug_links,
    yaml_activities_to_jsx,
)
from .reading_links import reading_href_for
from .resources import (
    embed_youtube_video_links,
    format_resources_for_mdx,
    vocab_items_to_components,
)
from .utils import (
    CURRICULUM_DIR,
    PROJECT_ROOT,
    SCRIPT_DIR,
    STARLIGHT_DOCS_DIR,
    escape_jsx,
    fix_html_for_jsx,
)

# Ensure scripts/ is on sys.path for sibling imports
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from manifest_utils import CORE_LEVELS, TRACKS, Module, get_modules_for_level
from slug_utils import to_bare_slug

# Re-export Activity for type annotations used by callers
from yaml_activities import (
    Activity,
    ActivityParser,
)

from scripts.audit.wiki_completeness_gate import SEMINAR_LEVELS

VENV_PYTHON = PROJECT_ROOT / ".venv" / "bin" / "python"


def detect_pipeline_info(level_dir: Path, slug: str) -> tuple[str | None, str | None]:
    """Detect pipeline version and build status from orchestration dir.

    Returns (pipeline_version, build_status) where:
      pipeline_version: "v6", "v5", "v3", or None (unbuilt)
      build_status: "draft", "validated", "reviewed", or None
    """
    orch_dir = level_dir / "orchestration" / slug

    # Detect version
    v3_file = orch_dir / "state-v3.json"
    v2_file = orch_dir / "state.json"

    version = None
    phases = {}

    if v3_file.exists():
        version = "v3"
        try:
            data = json.loads(v3_file.read_text()) or {}
            phases = data.get("phases", {})
        except Exception:
            pass
    elif v2_file.exists():
        try:
            data = json.loads(v2_file.read_text()) or {}
            mode = data.get("mode", "")
            if mode == "v6":
                version = "v6"
            elif mode == "v5":
                version = "v5"
            elif mode and mode != "v3":
                return None, None
            elif data:
                version = "v3"
            phases = data.get("phases", {})
        except Exception:
            pass

    if version is None:
        return None, None

    # Determine build_status from phase completion
    build_status = "draft"
    if version == "v6":
        if phases.get("review", {}).get("status") == "complete":
            build_status = "reviewed"
        elif phases.get("verify", {}).get("status") == "complete":
            build_status = "validated"
    elif version == "v5":
        if phases.get("review", {}).get("status") == "complete":
            build_status = "reviewed"
        elif phases.get("validate", {}).get("status") == "complete":
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


def _activity_plans_to_jsx(plans: list[dict]) -> str:
    """Render activity plans as ActivityPlaceholder JSX components."""
    parts = []
    for plan in plans:
        atype = escape_jsx(plan.get('type', 'unknown'))
        desc = escape_jsx(plan.get('description', ''))
        item_count = plan.get('item_count', '')
        focus = escape_jsx(plan.get('focus', ''))

        attrs = [f'type="{atype}"', f'description="{desc}"']
        if item_count:
            attrs.append(f'itemCount={{{item_count}}}')
        if focus:
            attrs.append(f'focus="{focus}"')
        parts.append(f'<ActivityPlaceholder {" ".join(attrs)} />')
    return '\n\n'.join(parts)


_INJECT_ACTIVITY_RE = re.compile(r'<!--\s*INJECT_ACTIVITY:\s*([A-Za-z0-9_-]+)\s*-->')
_INLINE_SECTION_HEADING_RE = re.compile(r'^#{2,3}\s+(.+?)\s*#*\s*$')
_READING_SECTION_RE = re.compile(r'^(##\s+(?:Читання|Reading)[^\n]*\n)', re.MULTILINE)


def _activity_id(activity: Activity | dict) -> str:
    activity_id = activity.get('id', '') if isinstance(activity, dict) else getattr(activity, 'id', '')
    return '' if activity_id is None else str(activity_id).strip()


def _activity_type(activity: Activity | dict) -> str:
    activity_type = activity.get('type', '') if isinstance(activity, dict) else getattr(activity, 'type', '')
    if activity_type is None:
        return 'unknown'
    return str(activity_type).strip() or 'unknown'


def _set_activity_id(activity: Activity | dict, activity_id: str) -> None:
    if isinstance(activity, dict):
        activity['id'] = activity_id
    else:
        activity.id = activity_id


def backfill_missing_activity_ids(activities: list[Activity | dict]) -> list[Activity | dict]:
    """Assign deterministic IDs to idless activities without changing existing IDs."""
    used_ids = {
        activity_id
        for activity in activities
        if (activity_id := _activity_id(activity))
    }

    for index, activity in enumerate(activities, start=1):
        if _activity_id(activity):
            continue

        preferred_id = f'act-{index}'
        candidate_id = preferred_id
        if candidate_id in used_ids:
            candidate_id = f'{preferred_id}-{_activity_type(activity)}'

        suffix = 2
        base_id = candidate_id
        while candidate_id in used_ids:
            candidate_id = f'{base_id}-{suffix}'
            suffix += 1

        _set_activity_id(activity, candidate_id)
        used_ids.add(candidate_id)

    return activities


def _inline_activity_section_titles(body: str) -> dict[str, str]:
    """Map inline activity ids to the nearest preceding H2/H3 section title."""
    section_title = ""
    titles: dict[str, str] = {}
    for line in body.splitlines():
        heading_match = _INLINE_SECTION_HEADING_RE.match(line.strip())
        if heading_match:
            section_title = heading_match.group(1).strip()
        for marker_match in _INJECT_ACTIVITY_RE.finditer(line):
            titles[marker_match.group(1)] = section_title
    return titles


def _inject_inline_activities(
    body: str,
    yaml_activities: list[Activity] | None,
    is_ukrainian_forced: bool,
) -> tuple[str, set[str], set[int], set[str], dict[str, str]]:
    """Replace Tab 1 INJECT_ACTIVITY markers with matching component JSX."""
    if not yaml_activities or "INJECT_ACTIVITY" not in body:
        return body, set(), set(), set(), {}

    parser = ActivityParser()
    section_titles = _inline_activity_section_titles(body)
    by_id = {
        _activity_id(activity): (index, activity)
        for index, activity in enumerate(yaml_activities)
        if _activity_id(activity)
    }
    injected_ids: set[str] = set()
    injected_positions: set[int] = set()
    injected_fingerprints: set[str] = set()

    def replace_marker(match: re.Match[str]) -> str:
        activity_id = match.group(1)
        matched = by_id.get(activity_id)
        if matched is None:
            raise ValueError(f"Unresolved INJECT_ACTIVITY id: {activity_id}")
        index, activity = matched
        injected_ids.add(activity_id)
        injected_positions.add(index)
        injected_fingerprints.add(activity_identity_key(activity))
        return parser._activity_to_mdx(activity, is_ukrainian_forced)

    return (
        _INJECT_ACTIVITY_RE.sub(replace_marker, body),
        injected_ids,
        injected_positions,
        injected_fingerprints,
        section_titles,
    )


def _format_plan_readings_for_mdx(readings: object) -> str:
    """Render the plan-level reading assignment as an integrity-gated MDX list."""
    if not isinstance(readings, list):
        return ""

    lines = ["**Texts you'll read**", ""]
    for item in readings:
        if not isinstance(item, dict):
            continue
        title = str(item.get("title") or "").strip()
        slug = str(item.get("reading_slug") or "").strip()
        if not title or not slug:
            continue
        href = reading_href_for(slug)
        if not href:
            continue
        genre = str(item.get("genre") or "").strip()
        title_en = str(item.get("title_en") or "").strip()
        detail = " · ".join(value for value in (genre, title_en) if value)
        suffix = f" — {detail}" if detail else ""
        lines.append(f"- [{title}]({href}){suffix}")

    return "\n".join(lines) if len(lines) > 2 else ""


def _insert_plan_readings_block(body: str, readings: object) -> str:
    block = _format_plan_readings_for_mdx(readings)
    if not block:
        return body

    def replace(match: re.Match[str]) -> str:
        return f"{match.group(1)}\n{block}\n\n"

    updated, count = _READING_SECTION_RE.subn(replace, body, count=1)
    if count:
        return updated
    return f"{block}\n\n{body}"


def generate_mdx(
    md_content: str,
    module_num: int,
    yaml_activities: list | None = None,
    meta_data: dict | None = None,
    vocab_items: list[dict] | None = None,
    external_resources: dict | None = None,
    level: str = 'a1',
    pipeline_version: str | None = None,
    build_status: str | None = None,
    activity_plans: list[dict] | None = None,
) -> str:
    """Convert markdown content to MDX.

    Args:
        md_content: Markdown content
        module_num: Module number for sidebar
        yaml_activities: Optional list of activities from ActivityParser (takes precedence over embedded)
        meta_data: Optional metadata from YAML (replaces frontmatter)
        vocab_items: Optional vocab list from YAML
        external_resources: Optional external resources dict (injected from YAML)
        level: Current level (used for specialized formatting like LIT)
        pipeline_version: Optional pipeline version ("v3", "v5", or "v6")
        build_status: Optional build status ("draft", "validated", "reviewed")
    """
    if meta_data:
        fm = meta_data
        body = md_content
        _, body = parse_frontmatter(md_content)
        # Strip inline YAML preamble when frontmatter delimiters (---) were missing.
        _YAML_META_KEYS = {
            'module', 'level', 'sequence', 'slug', 'version', 'title', 'subtitle',
            'content_outline', 'vocabulary_hints', 'activity_hints', 'focus',
            'pedagogy', 'prerequisites', 'connects_to', 'objectives', 'grammar',
            'register', 'phase', 'persona', 'word_target', 'readings',
        }
        if body and not md_content.lstrip().startswith('---'):
            first_line = body.lstrip().split('\n')[0]
            first_key = first_line.split(':')[0].strip()
            if first_key in _YAML_META_KEYS:
                heading_match = re.search(r'^#{1,2} ', body, flags=re.MULTILINE)
                if heading_match and heading_match.start() > 0:
                    print("  \u26a0\ufe0f  Stripping inline YAML preamble (missing --- delimiters)")
                    body = body[heading_match.start():]
    else:
        fm, body = parse_frontmatter(md_content)

    if yaml_activities:
        yaml_activities = backfill_missing_activity_ids(list(yaml_activities))

    # Determine if Ukrainian headers are forced
    is_ukrainian_forced = False
    lvl = level.lower()
    is_a2_2_preview = lvl.startswith('a2') and module_num >= 9
    if (
        lvl in SEMINAR_LEVELS
        or any(lvl.startswith(p) for p in ['b2', 'c1', 'c2', 'lit'])
        or is_a2_2_preview
        or lvl.startswith('b1')
    ):
        is_ukrainian_forced = True

    # Component imports. Keep the legacy broad preamble stable for existing
    # generated MDX, but gate newer rare components so ordinary A1/A2
    # regeneration does not drift just by importing unused seminar widgets.
    optional_imports = {
        "RitualSequencing": "import RitualSequencing from '@site/src/components/RitualSequencing';",
        "VariantComparison": "import VariantComparison from '@site/src/components/VariantComparison';",
        "MotifFormula": "import MotifFormula from '@site/src/components/MotifFormula';",
        "MythBuster": "import MythBuster from '@site/src/components/MythBuster';",
        "PrimaryReading": "import PrimaryReading from '@site/src/components/PrimaryReading';",
        "PerformanceActivity": "import PerformanceActivity from '@site/src/components/PerformanceActivity';",
        "HighCultureBridge": "import HighCultureBridge from '@site/src/components/HighCultureBridge';",
    }

    # Frontmatter
    extra_fm_lines = ""
    if pipeline_version:
        extra_fm_lines += f"\npipeline: {pipeline_version}"
    if build_status:
        extra_fm_lines += f"\nbuild_status: {build_status}"
    should_hide_draft = (
        pipeline_version
        and pipeline_version not in ("v5", "v6")
        and not (pipeline_version == "linear-phase-4" and build_status in {"validated", "reviewed"})
    )
    explicit_draft = fm.get("draft")
    if isinstance(explicit_draft, bool):
        extra_fm_lines += f"\ndraft: {str(explicit_draft).lower()}"
    elif should_hide_draft:
        extra_fm_lines += "\ndraft: true"

    try:
        from build.prev_next import get_prev_next_links
        prev_link, next_link = get_prev_next_links(level, module_num)
        extra_fm_lines += f"\nprev: {prev_link}" if prev_link else "\nprev: false"
        extra_fm_lines += f"\nnext: {next_link}" if next_link else "\nnext: false"
    except Exception:
        pass

    frontmatter = f'''---
title: "{escape_jsx(fm.get('title', 'Untitled'))}"
description: "{escape_jsx(fm.get('subtitle', ''))}"
sidebar:
  order: {module_num}
  label: "{str(module_num).zfill(2)}. {escape_jsx(fm.get('title', 'Untitled'))}"{extra_fm_lines}
---
'''

    # 1. Clean up body: Remove existing Vocabulary, Activities, and Resources placeholders
    body = re.sub(r'(^#{1,2}\s+(?:Activities|Вправи))[\s\S]*?(?=\n#{1,2}|\Z)', '', body, flags=re.MULTILINE)
    body = re.sub(r'(^#{1,2}\s+(?:Vocabulary|Словник))[\s\S]*?(?=\n#{1,2}|\Z)', '', body, flags=re.MULTILINE)
    body = re.sub(r'>\s*\[!resources\].*?(\n>.*)*', '', body, flags=re.MULTILINE | re.IGNORECASE)

    # =========================================================================
    # TABBED LAYOUT: Build 4 separate content blocks
    # =========================================================================

    # --- TAB 1: Lesson (prose only) ---
    lesson_content = body
    lesson_content = _insert_plan_readings_block(lesson_content, fm.get("readings"))
    lesson_content = embed_youtube_video_links(lesson_content)
    (
        lesson_content,
        injected_activity_ids,
        _injected_activity_positions,
        _injected_activity_fingerprints,
        _injected_activity_section_titles,
    ) = _inject_inline_activities(
        lesson_content,
        yaml_activities,
        is_ukrainian_forced,
    )

    # --- TAB 2: Vocabulary ---
    if vocab_items:
        vocab_header = "\u0421\u043b\u043e\u0432\u043d\u0438\u043a" if is_ukrainian_forced else "Vocabulary"
        vocab_content = vocab_items_to_components(vocab_items, vocab_header)
        # Strip the H2 header - the tab label serves as the header
        vocab_content = re.sub(r'^## [^\n]+\n+', '', vocab_content)
    else:
        no_vocab_msg = "\u041d\u0435\u043c\u0430\u0454 \u0441\u043b\u043e\u0432\u043d\u0438\u043a\u0430 \u0434\u043b\u044f \u0446\u044c\u043e\u0433\u043e \u043c\u043e\u0434\u0443\u043b\u044f." if is_ukrainian_forced else "No vocabulary for this module."
        vocab_content = f"*{no_vocab_msg}*"

    # --- TAB 3: Activities ---
    tab3_activities = list(yaml_activities or [])
    no_workbook_msg = (
        "Немає окремих вправ у робочому зошиті; дивіться вкладку «Урок»."
        if is_ukrainian_forced
        else "No workbook activities for this module; see the Lesson tab."
    )
    if tab3_activities:
        activities_content = yaml_activities_to_jsx(
            tab3_activities,
            is_ukrainian_forced,
            inline_cross_ref_ids=injected_activity_ids,
            inline_cross_ref_positions=_injected_activity_positions,
            inline_cross_ref_fingerprints=_injected_activity_fingerprints,
            inline_cross_ref_section_titles=_injected_activity_section_titles,
        )
        if not activities_content.strip() and injected_activity_ids:
            activities_content = f"*{no_workbook_msg}*"
    elif activity_plans:
        activities_content = _activity_plans_to_jsx(activity_plans)
    else:
        no_act_msg = "\u041d\u0435\u043c\u0430\u0454 \u0432\u043f\u0440\u0430\u0432 \u0434\u043b\u044f \u0446\u044c\u043e\u0433\u043e \u043c\u043e\u0434\u0443\u043b\u044f." if is_ukrainian_forced else "No activities for this module."
        activities_content = f"*{no_act_msg}*"

    # --- TAB 4: Resources ---
    resources_content = ""
    if external_resources:
        resources_content = format_resources_for_mdx(external_resources, is_ukrainian_forced)
    if not resources_content:
        no_res_msg = "\u041d\u0435\u043c\u0430\u0454 \u0437\u043e\u0432\u043d\u0456\u0448\u043d\u0456\u0445 \u0440\u0435\u0441\u0443\u0440\u0441\u0456\u0432 \u0434\u043b\u044f \u0446\u044c\u043e\u0433\u043e \u043c\u043e\u0434\u0443\u043b\u044f." if is_ukrainian_forced else "No external resources for this module."
        resources_content = f"*{no_res_msg}*"

    # =========================================================================
    # Process lesson content (Tab 1 only)
    # =========================================================================

    # =========================================================================
    # Apply shared transforms to all content blocks
    # =========================================================================
    def _apply_shared_transforms(text: str, strip_bad_forms: bool = False) -> str:
        """Apply callout conversion, slug links, HTML fixes, comments, stories, dialogues."""
        text = convert_folk_content_blocks(text)
        text = convert_callouts(text, is_ukrainian_forced)
        text = resolve_slug_links(text)
        text = convert_bad_form_markers(text, strip_only=strip_bad_forms)
        text = fix_html_for_jsx(text)
        text = re.sub(r'<!--.*?-->\n?', '', text, flags=re.DOTALL)
        text = process_story_sections(text)
        text = process_dialogues(text)
        return text

    lesson_content = _apply_shared_transforms(lesson_content)

    # We pass strip_bad_forms=True to vocab and activities because they contain JSON-embedded JSX props.
    # Putting <del> inside a JSON string value would render literal <del> text in a card instead of semantic strikethrough.
    vocab_content = _apply_shared_transforms(vocab_content, strip_bad_forms=True)
    activities_content = _apply_shared_transforms(activities_content, strip_bad_forms=True)

    resources_content = _apply_shared_transforms(resources_content)

    # Remove duplicate H1 title (from lesson tab only)
    lesson_content = re.sub(r'^#\s+[^\n]+\n', '', lesson_content, count=1, flags=re.MULTILINE)

    # Add emojis to H2 section headings (data-driven)
    _HEADING_RULES = [
        ('\u041f\u0456\u0434\u0441\u0443\u043c\u043e\u043a',            '\U0001f4cb', r'Summary|\u041f\u0456\u0434\u0441\u0443\u043c\u043e\u043a',                                                                  'lesson'),
        ('\u0421\u0430\u043c\u043e\u043e\u0446\u0456\u043d\u043a\u0430',          '\u2705', r'Self-Assessment|\u0421\u0430\u043c\u043e\u043e\u0446\u0456\u043d\u043a\u0430',                                                         'lesson'),
        ('\u0417\u043e\u0432\u043d\u0456\u0448\u043d\u0456 \u0440\u0435\u0441\u0443\u0440\u0441\u0438',    '\U0001f517', r'External Resources?|\u0417\u043e\u0432\u043d\u0456\u0448\u043d\u0456 \u0440\u0435\u0441\u0443\u0440\u0441\u0438|Resources|\u0420\u0435\u0441\u0443\u0440\u0441\u0438',                              'resources'),
        ('\u041a\u0443\u043b\u044c\u0442\u0443\u0440\u0430',            '\U0001f3fa', r'Culture|\u041a\u0443\u043b\u044c\u0442\u0443\u0440\u0430|Cultural Context|\u041a\u0443\u043b\u044c\u0442\u0443\u0440\u043d\u0438\u0439 \u043a\u043e\u043d\u0442\u0435\u043a\u0441\u0442|Folk Culture|\u041d\u0430\u0440\u043e\u0434\u043d\u0430 \u043a\u0443\u043b\u044c\u0442\u0443\u0440\u0430', 'lesson'),
        ('\u0406\u0441\u0442\u043e\u0440\u0438\u0447\u043d\u0438\u0439 \u043a\u043e\u043d\u0442\u0435\u043a\u0441\u0442', '\U0001f570\ufe0f',  r'History|Historical Context|\u0406\u0441\u0442\u043e\u0440\u0438\u0447\u043d\u0438\u0439 \u043a\u043e\u043d\u0442\u0435\u043a\u0441\u0442|Heritage|\u0421\u043f\u0430\u0434\u0449\u0438\u043d\u0430',                   'lesson'),
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
    tabs = [
        ("Lesson",     "\u0423\u0440\u043e\u043a",    lesson_content),
        ("Vocabulary", "\u0421\u043b\u043e\u0432\u043d\u0438\u043a",  vocab_content),
        ("Activities", "\u0417\u043e\u0448\u0438\u0442" if is_a2_2_preview else "\u0412\u043f\u0440\u0430\u0432\u0438",   activities_content),
        ("Resources",  "\u0420\u0435\u0441\u0443\u0440\u0441\u0438",  resources_content),
    ]
    tab_items = '\n'.join(
        f'<TabItem label="{uk if is_ukrainian_forced else en}">\n\n'
        f'{content.strip()}\n\n</TabItem>'
        for en, uk, content in tabs
    )
    tabbed = f'\n<Tabs syncKey="module-tab">\n{tab_items}\n</Tabs>\n\n<HashTabSync />\n'

    import_lines = [
        "import Quiz from '@site/src/components/Quiz';",
        "import MatchUp from '@site/src/components/MatchUp';",
        "import FillIn from '@site/src/components/FillIn';",
        "import TrueFalse from '@site/src/components/TrueFalse';",
        "import Unjumble from '@site/src/components/Unjumble';",
        "import GroupSort from '@site/src/components/GroupSort';",
        "import Anagram from '@site/src/components/Anagram';",
        "import ErrorCorrection from '@site/src/components/ErrorCorrection';",
        "import { ErrorCorrectionItem } from '@site/src/components/ErrorCorrection';",
        "import Cloze from '@site/src/components/Cloze';",
        "import Select from '@site/src/components/Select';",
        "import Translate from '@site/src/components/Translate';",
        "import MarkTheWords from '@site/src/components/MarkTheWords';",
        "import { MarkTheWordsActivity } from '@site/src/components/MarkTheWords';",
        "import HighlightMorphemes from '@site/src/components/HighlightMorphemes';",
        "import { HighlightMorphemesActivity } from '@site/src/components/HighlightMorphemes';",
    ]
    for component in ("RitualSequencing", "VariantComparison", "MotifFormula", "PerformanceActivity", "PrimaryReading"):
        if re.search(rf"<{component}\b", tabbed):
            import_lines.append(optional_imports[component])
    import_lines.extend([
        "import EssayResponse from '@site/src/components/EssayResponse';",
        "import ComparativeStudy from '@site/src/components/ComparativeStudy';",
        "import ReadingActivity from '@site/src/components/ReadingActivity';",
        "import CriticalAnalysis from '@site/src/components/CriticalAnalysis';",
        "import AuthorialIntent from '@site/src/components/AuthorialIntent';",
    ])
    for component in ("MythBuster", "HighCultureBridge"):
        if re.search(rf"<{component}\b", tabbed):
            import_lines.append(optional_imports[component])
    import_lines.extend([
        "import SourceEvaluation from '@site/src/components/SourceEvaluation';",
        "import Debate from '@site/src/components/Debate';",
        "import EtymologyTrace from '@site/src/components/EtymologyTrace';",
        "import GrammarIdentify from '@site/src/components/GrammarIdentify';",
        "import PaleographyAnalysis from '@site/src/components/PaleographyAnalysis';",
        "import DialectComparison from '@site/src/components/DialectComparison';",
        "import TranslationCritique from '@site/src/components/TranslationCritique';",
        "import Transcription from '@site/src/components/Transcription';",
        "import Observe from '@site/src/components/Observe';",
        "import Order from '@site/src/components/Order';",
        "import CountSyllables from '@site/src/components/CountSyllables';",
        "import DivideWords from '@site/src/components/DivideWords';",
        "import OddOneOut from '@site/src/components/OddOneOut';",
        "import PickSyllables from '@site/src/components/PickSyllables';",
        "import LetterGrid from '@site/src/components/LetterGrid';",
        "import FlashcardDeck from '@site/src/components/FlashcardDeck';",
        "import VocabCard from '@site/src/components/VocabCard';",
        "import DialogueBox from '@site/src/components/DialogueBox';",
        "import HashTabSync from '@site/src/components/HashTabSync';",
        "import ActivityHelp from '@site/src/components/ActivityHelp';",
        "import YouTubeVideo from '@site/src/components/YouTubeVideo';",
        "import WatchAndRepeat from '@site/src/components/WatchAndRepeat';",
        "import Classify from '@site/src/components/Classify';",
        "import ImageToLetter from '@site/src/components/ImageToLetter';",
        "import ActivityPlaceholder from '@site/src/components/ActivityPlaceholder';",
        "import { Tabs, TabItem } from '@astrojs/starlight/components';",
    ])
    imports = "\n".join(import_lines)

    # Build MDX
    parts = [frontmatter, imports, '', tabbed]

    return normalize_mdx('\n'.join(parts))


def get_modules_from_manifest(target_level: str | None = None) -> list[Module]:
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
    """CLI entry point for MDX generation."""
    args = sys.argv[1:]

    # Parse --validate flag
    validate_after = '--validate' in args
    args = [a for a in args if a != '--validate']

    print('\n\U0001f680 MDX Generator (Manifest-Driven)\n', flush=True)

    target_level = None
    target_module = None
    lang_pair = 'l2-uk-en'

    if args:
        if args[0].endswith('.md'):
            # Specific file logic: extract level and slug from path
            file_path = Path(args[0])
            level_from_path = file_path.parent.name
            slug = to_bare_slug(file_path.stem)

            # Find all modules with this slug from manifest
            all_available_modules = get_modules_from_manifest()
            matching_modules = [m for m in all_available_modules if m.slug == slug]

            if not matching_modules:
                print(f"  \u26a0\ufe0f  Could not find module with slug '{slug}' in manifest for: {args[0]}")
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
                print(f"  \u2139\ufe0f  Using fallback module mapping: {mod_obj.level}/{mod_obj.slug}")

            process_modules = [mod_obj]
        else:
            lang_pair = args[0]
            target_level = args[1].lower() if len(args) > 1 else None
            target_module = int(args[2]) if len(args) > 2 else None
            process_modules = get_modules_from_manifest(target_level)
    else:
        process_modules = get_modules_from_manifest()

    print(f'Source: curriculum/{lang_pair}/', flush=True)
    print('Output: site/src/content/docs/\n', flush=True)

    # Load EXTERNAL RESOURCES
    external_resources_file = PROJECT_ROOT / 'docs' / 'resources' / 'external_resources.yaml'
    all_resources = {}
    if external_resources_file.exists():
        with open(external_resources_file, encoding='utf-8') as f:
            resources_data = yaml.safe_load(f)
            all_resources = resources_data.get('resources', {})
        print(f'\U0001f4da Loaded {len(all_resources)} modules with external resources\n', flush=True)

    current_level = None
    for mod in process_modules:
        if target_module and mod.local_num != target_module:
            continue

        if mod.level != current_level:
            print(f'\U0001f4c1 Level {mod.level.upper()}')
            current_level = mod.level
            output_dir = STARLIGHT_DOCS_DIR / mod.level
            output_dir.mkdir(parents=True, exist_ok=True)

        # Find the physical file. Newer v7 modules use a folder layout:
        # a1/<slug>/module.md with sibling activities/vocabulary/resources YAML.
        level_dir = CURRICULUM_DIR / lang_pair / mod.level
        md_file = level_dir / f"{mod.slug}.md"
        module_dir = level_dir / mod.slug

        if not md_file.exists():
            folder_md_file = module_dir / "module.md"
            if folder_md_file.exists():
                md_file = folder_md_file
            else:
                print(f"DEBUG: Checked path {md_file.absolute()}")
                print(f"DEBUG: Checked path {folder_md_file.absolute()}")
                print(f"  \u26a0\ufe0f  Physical file not found for slug '{mod.slug}' in {mod.level}")
                continue

        # Read and convert
        md_content = md_file.read_text(encoding='utf-8')

        # Load META
        meta_file = level_dir / 'meta' / f"{mod.slug}.yaml"

        meta_data = None
        if meta_file.exists():
            try:
                with open(meta_file, encoding='utf-8') as f:
                    meta_data = yaml.safe_load(f)
            except Exception as e:
                print(f'\n\u274c CRITICAL: Error parsing YAML metadata for {mod.slug}: {e}')
                sys.exit(1)

        # Load PLAN file for title/subtitle
        plan_data = None
        plan_file = CURRICULUM_DIR / lang_pair / 'plans' / mod.level.lower() / f"{mod.slug}.yaml"
        if plan_file.exists():
            try:
                with open(plan_file, encoding='utf-8') as f:
                    plan_data = yaml.safe_load(f)
                    if meta_data is None:
                        meta_data = {}
                    if plan_data and 'title' in plan_data and 'title' not in meta_data:
                        meta_data['title'] = plan_data['title']
                    if plan_data and 'subtitle' in plan_data and 'subtitle' not in meta_data:
                        meta_data['subtitle'] = plan_data['subtitle']
                    if plan_data and 'readings' in plan_data:
                        meta_data['readings'] = plan_data['readings']
            except Exception as e:
                print(f'\n\u274c CRITICAL: Error parsing plan file for {mod.slug}: {e}')
                sys.exit(1)

        # Load VOCABULARY
        vocab_file = level_dir / 'vocabulary' / f"{mod.slug}.yaml"
        if not vocab_file.exists():
            folder_vocab_file = module_dir / "vocabulary.yaml"
            if folder_vocab_file.exists():
                vocab_file = folder_vocab_file

        vocab_items = None
        if vocab_file.exists():
            try:
                with open(vocab_file, encoding='utf-8') as f:
                    v_data = yaml.safe_load(f)
                    if isinstance(v_data, list):
                        vocab_items = v_data
                    elif isinstance(v_data, dict) and 'items' in v_data:
                        vocab_items = v_data['items']
            except Exception as e:
                print(f'\n\u274c CRITICAL: Error parsing YAML vocabulary for {mod.slug}: {e}')
                sys.exit(1)

        # Load ACTIVITIES
        yaml_file = level_dir / 'activities' / f"{mod.slug}.yaml"
        if not yaml_file.exists():
            folder_yaml_file = module_dir / "activities.yaml"
            if folder_yaml_file.exists():
                yaml_file = folder_yaml_file

        yaml_activities = None
        if yaml_file.exists():
            parser = ActivityParser()
            try:
                yaml_activities = parser.parse(yaml_file)
            except Exception as e:
                print(f'\n\u274c CRITICAL: Error parsing YAML activities for {mod.slug}: {e}')
                sys.exit(1)

        # Load ACTIVITY PLANS (fallback when activities not yet built)
        plans_file = level_dir / 'activities' / f"{mod.slug}-plans.yaml"
        loaded_activity_plans = None
        if not yaml_activities and plans_file.exists():
            try:
                with open(plans_file, encoding='utf-8') as f:
                    p_data = yaml.safe_load(f)
                    if isinstance(p_data, list):
                        loaded_activity_plans = p_data
            except Exception as e:
                print(f'  \u26a0\ufe0f  Error parsing activity plans for {mod.slug}: {e}')

        # EXTERNAL RESOURCES
        module_id = f"{mod.level}-{mod.slug}"
        module_resources = all_resources.get(module_id, {})

        folder_resources_file = module_dir / "resources.yaml"
        if folder_resources_file.exists():
            try:
                with open(folder_resources_file, encoding='utf-8') as f:
                    resource_data = yaml.safe_load(f)
                if isinstance(resource_data, list | dict):
                    module_resources = resource_data
            except Exception as e:
                print(f'\n❌ CRITICAL: Error parsing YAML resources for {mod.slug}: {e}')
                sys.exit(1)

        # Add pronunciation videos from plan to resources
        if isinstance(module_resources, dict) and plan_data and plan_data.get("pronunciation_videos"):
            pv = plan_data["pronunciation_videos"]
            yt_resources = module_resources.get("youtube", [])
            if pv.get("overview"):
                yt_resources.append({"title": "Alphabet Overview", "url": pv["overview"],
                                     "source": pv.get("credit", "")})
            if pv.get("poster"):
                yt_resources.append({"title": "Alphabet Poster", "url": pv["poster"],
                                     "source": pv.get("credit", "")})
            if pv.get("playlist"):
                yt_resources.append({"title": "Letter Pronunciation Playlist", "url": pv["playlist"],
                                     "source": pv.get("credit", "")})
            for letter, url in (pv.get("letters") or {}).items():
                yt_resources.append({"title": f"Літера {letter}", "url": url,
                                     "source": pv.get("credit", "")})
            if yt_resources:
                module_resources["youtube"] = yt_resources

        # Detect pipeline version and build status
        pv, bs = detect_pipeline_info(level_dir, mod.slug)

        mdx_content = generate_mdx(md_content, mod.local_num, yaml_activities, meta_data, vocab_items, module_resources, mod.level, pipeline_version=pv, build_status=bs, activity_plans=loaded_activity_plans)

        # Write output
        output_file = output_dir / f'{mod.slug}.mdx'
        output_file.write_text(mdx_content, encoding='utf-8')  # codeql[py/clear-text-storage-sensitive-data] - .mdx curriculum content, never sensitive data

    print('\n\u2705 MDX generation complete!')

    # Run validation if --validate flag was set
    if validate_after:
        print('\n' + '=' * 50)
        print('Running MDX validation...\n')
        import subprocess
        validate_args = [str(VENV_PYTHON), str(SCRIPT_DIR / 'validate_mdx.py'), lang_pair]
        if target_level:
            validate_args.append(target_level)
        if target_module:
            validate_args.append(str(target_module))
        result = subprocess.run(validate_args)
        sys.exit(result.returncode)
