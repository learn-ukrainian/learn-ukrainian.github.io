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
    convert_callouts,
    normalize_mdx,
    process_dialogues,
    process_story_sections,
    resolve_slug_links,
    yaml_activities_to_jsx,
)
from .utils import fix_html_for_jsx
from .resources import (
    embed_youtube_video_links,
    format_resources_for_mdx,
    b1_vocab_items_to_markdown,
    vocab_items_to_markdown,
)
from .utils import CURRICULUM_DIR, DOCUSAURUS_DIR, PROJECT_ROOT, SCRIPT_DIR, escape_jsx

# Ensure scripts/ is on sys.path for sibling imports
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from manifest_utils import CORE_LEVELS, TRACKS, Module, get_modules_for_level  # noqa: E402
from slug_utils import to_bare_slug  # noqa: E402
from yaml_activities import ActivityParser  # noqa: E402

# Re-export Activity for type annotations used by callers
from yaml_activities import Activity  # noqa: E402, F401


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
        pipeline_version: Optional pipeline version ("v3" or "v4")
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
            'register', 'phase', 'persona', 'word_target',
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

    # Determine if Ukrainian headers are forced
    is_ukrainian_forced = False
    lvl = level.lower()
    if any(lvl.startswith(p) for p in ['b2', 'c1', 'c2', 'lit']) or (lvl.startswith('b1') and module_num > 5):
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
    body = re.sub(r'(^#{1,2}\s+(?:Activities|Вправи))[\s\S]*?(?=\n#{1,2}|\Z)', '', body, flags=re.MULTILINE)
    body = re.sub(r'(^#{1,2}\s+(?:Vocabulary|Словник))[\s\S]*?(?=\n#{1,2}|\Z)', '', body, flags=re.MULTILINE)
    body = re.sub(r'>\s*\[!resources\].*?(\n>.*)*', '', body, flags=re.MULTILINE | re.IGNORECASE)

    # =========================================================================
    # TABBED LAYOUT: Build 4 separate content blocks
    # =========================================================================

    # --- TAB 1: Lesson (prose only) ---
    lesson_content = body

    # --- TAB 2: Vocabulary ---
    if vocab_items:
        vocab_header = "\u0421\u043b\u043e\u0432\u043d\u0438\u043a" if is_ukrainian_forced else "Vocabulary"
        if is_ukrainian_forced:
            vocab_content = b1_vocab_items_to_markdown(vocab_items, vocab_header)
        else:
            vocab_content = vocab_items_to_markdown(vocab_items, vocab_header)
        # Strip the H2 header - the tab label serves as the header
        vocab_content = re.sub(r'^## [^\n]+\n+', '', vocab_content)
    else:
        no_vocab_msg = "\u041d\u0435\u043c\u0430\u0454 \u0441\u043b\u043e\u0432\u043d\u0438\u043a\u0430 \u0434\u043b\u044f \u0446\u044c\u043e\u0433\u043e \u043c\u043e\u0434\u0443\u043b\u044f." if is_ukrainian_forced else "No vocabulary for this module."
        vocab_content = f"*{no_vocab_msg}*"

    # --- TAB 3: Activities ---
    if yaml_activities:
        activities_content = yaml_activities_to_jsx(yaml_activities, is_ukrainian_forced)
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

    # Embed YouTube video links as clickable thumbnails (lesson prose only)
    lesson_content = embed_youtube_video_links(lesson_content)

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
        ("Activities", "\u0412\u043f\u0440\u0430\u0432\u0438",   activities_content),
        ("Resources",  "\u0420\u0435\u0441\u0443\u0440\u0441\u0438",  resources_content),
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
    print('Output: starlight/src/content/docs/\n', flush=True)

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
            output_dir = DOCUSAURUS_DIR / mod.level
            output_dir.mkdir(parents=True, exist_ok=True)

        # Find the physical file
        level_dir = CURRICULUM_DIR / lang_pair / mod.level
        md_file = level_dir / f"{mod.slug}.md"

        if not md_file.exists():
            print(f"DEBUG: Checked path {md_file.absolute()}")
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
            except Exception as e:
                print(f'\n\u274c CRITICAL: Error parsing plan file for {mod.slug}: {e}')
                sys.exit(1)

        # Load VOCABULARY
        vocab_file = level_dir / 'vocabulary' / f"{mod.slug}.yaml"

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

        yaml_activities = None
        if yaml_file.exists():
            parser = ActivityParser()
            try:
                yaml_activities = parser.parse(yaml_file)
            except Exception as e:
                print(f'\n\u274c CRITICAL: Error parsing YAML activities for {mod.slug}: {e}')
                sys.exit(1)

        # EXTERNAL RESOURCES
        module_id = f"{mod.level}-{mod.slug}"
        module_resources = all_resources.get(module_id, {})

        # Detect pipeline version and build status
        pv, bs = detect_pipeline_info(level_dir, mod.slug)

        mdx_content = generate_mdx(md_content, mod.local_num, yaml_activities, meta_data, vocab_items, module_resources, mod.level, pipeline_version=pv, build_status=bs)

        # Write output
        output_file = output_dir / f'{mod.slug}.mdx'
        output_file.write_text(mdx_content, encoding='utf-8')

    print('\n\u2705 MDX generation complete!')

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
