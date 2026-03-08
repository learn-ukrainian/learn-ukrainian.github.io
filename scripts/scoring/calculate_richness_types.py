"""Module type detection for richness scoring.

Determines the module type (grammar, history, biography, etc.) from
frontmatter, sidecar YAML, plan files, file paths, and CEFR levels.
Used by the main calculate_richness module to select appropriate
scoring criteria and weights.
"""

from __future__ import annotations

import contextlib
import re
from pathlib import Path

import yaml
from slug_utils import to_bare_slug

from calculate_richness_config import MODULE_TYPE_MAP


def extract_level(file_path: str | Path | None) -> str:
    """Extract level code from file path."""
    if not file_path:
        return 'B1'
    if isinstance(file_path, str):
        file_path = Path(file_path)
    parts = file_path.parts
    for part in parts:
        if part.upper() in ('A1', 'A2', 'B1', 'B2', 'C1', 'C2', 'LIT'):
            return part.upper()
    return 'B1'


def _parse_frontmatter(content: str) -> dict | None:
    """Try to parse embedded frontmatter from markdown content."""
    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            with contextlib.suppress(yaml.YAMLError):
                return yaml.safe_load(parts[1])
    return None


def _load_sidecar_meta(file_path: Path) -> dict | None:
    """Try to load YAML sidecar meta file."""
    slug = file_path.stem
    sidecar_path = file_path.parent / 'meta' / f'{slug}.yaml'
    if sidecar_path.exists():
        try:
            with open(sidecar_path, encoding='utf-8') as f:
                return yaml.safe_load(f)
        except (OSError, yaml.YAMLError):
            pass
    return None


def _load_plan_focus(file_path: Path) -> str | None:
    """Try to load focus field from plan file."""
    level_dir = file_path.parent.name.lower()
    slug = file_path.stem
    clean_slug = to_bare_slug(slug)
    plan_paths = [
        file_path.parents[1] / 'plans' / level_dir / f'{clean_slug}.yaml',
        file_path.parents[1] / 'plans' / level_dir / f'{slug}.yaml',
    ]
    for plan_path in plan_paths:
        if plan_path.exists():
            try:
                with open(plan_path, encoding='utf-8') as f:
                    plan_data = yaml.safe_load(f)
                    if plan_data and plan_data.get('focus'):
                        return str(plan_data['focus']).lower().strip()
            except (OSError, yaml.YAMLError):
                pass
    return None


def _type_from_frontmatter(fm: dict) -> str | None:
    """Determine module type from frontmatter fields."""
    tags = fm.get('tags', [])
    if isinstance(tags, list) and 'bridge' in [t.lower() for t in tags]:
        return 'bridge'

    if fm.get('module_type') == 'bridge':
        return 'bridge'

    focus = str(fm.get('focus', '')).lower().strip()
    if focus in MODULE_TYPE_MAP:
        return MODULE_TYPE_MAP[focus]

    pedagogy = str(fm.get('pedagogy', '')).lower().strip()
    if pedagogy in MODULE_TYPE_MAP:
        return MODULE_TYPE_MAP[pedagogy]

    phase = str(fm.get('phase', '')).lower()
    if 'history' in phase:
        return 'history'
    elif 'biography' in phase or 'biographies' in phase:
        return 'biography'
    elif 'style' in phase or 'stylistic' in phase:
        return 'style'
    elif 'academic' in phase or 'sociolinguistic' in phase:
        return 'academic'
    elif 'checkpoint' in phase:
        return 'checkpoint'

    return None


def _type_from_path(file_path: str | Path | None) -> str | None:
    """Infer module type from file path."""
    if not file_path:
        return None
    path_str = str(file_path).lower()
    if '/lit/' in path_str:
        return 'literature'
    if '/hist/' in path_str or '/istorio/' in path_str:
        return 'history'
    if '/bio/' in path_str:
        return 'biography'
    return None


def _type_from_level(file_path: str | Path | None) -> str:
    """Determine default module type based on level and slug."""
    level = extract_level(file_path)

    if level in ('A1', 'A2'):
        return 'beginner'

    if level == 'B1' and file_path:
        slug = Path(file_path).stem
        bridge_slugs = [
            'how-to-talk-about-grammar',
            'language-about-verbs',
            'sentence-structure',
            'parts-of-speech-depth',
            'case-system-logic',
            'verb-categories-metalanguage',
            'syntax-and-sentence-structure'
        ]
        num_prefix_match = re.match(r'^0?([1-5])-([a-z-]+)', slug)
        if any(bs in slug for bs in bridge_slugs) or num_prefix_match:
            return 'bridge'

    if level in ('B1', 'B2'):
        return 'grammar'
    elif level in ('C1', 'C2'):
        return 'content'

    return 'grammar'


def extract_module_type(content: str, file_path: str | Path | None = None) -> str:
    """Extract module type from frontmatter, sidecar, plan, or path heuristics."""
    fm = _parse_frontmatter(content)

    if not fm and file_path:
        path = Path(file_path) if isinstance(file_path, str) else file_path
        fm = _load_sidecar_meta(path)

    if file_path:
        path = Path(file_path) if isinstance(file_path, str) else file_path
        plan_focus = _load_plan_focus(path)
        if plan_focus and plan_focus in MODULE_TYPE_MAP:
            return MODULE_TYPE_MAP[plan_focus]

    if fm:
        result = _type_from_frontmatter(fm)
        if result:
            return result

    result = _type_from_path(file_path)
    if result:
        return result

    return _type_from_level(file_path)


def get_prose_content(content: str) -> str:
    """Extract prose content (excluding activities and vocab)."""
    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            content = parts[2]
    elif re.match(r'^[a-z_]+:', content):
        heading_match = re.search(r'^#\s', content, re.MULTILINE)
        if heading_match:
            content = content[heading_match.start():]

    for section in ['Activities', 'Вправи']:
        match = re.search(rf'^#\s*{section}\s*$', content, re.MULTILINE)
        if match:
            content = content[:match.start()]
            break

    for section in ['Vocabulary', 'Словник']:
        match = re.search(rf'^#\s*{section}\s*$', content, re.MULTILINE)
        if match:
            content = content[:match.start()]
            break

    return content
