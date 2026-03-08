"""
File loading utilities for module audits.

Loads YAML metadata, plans, vocabulary, and curriculum manifests
from the filesystem.
"""

import os
import re
from pathlib import Path

import yaml

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from slug_utils import to_bare_slug


def load_yaml_meta(md_file_path: str) -> dict | None:
    """Load metadata from YAML sidecar if exists."""
    md_path = Path(md_file_path)
    bare = to_bare_slug(md_path.stem)
    yaml_path = md_path.parent / 'meta' / (bare + '.yaml')
    if not yaml_path.exists():
        yaml_path = md_path.parent / 'meta' / (md_path.stem + '.yaml')
        if not yaml_path.exists():
            return None
    try:
        with open(yaml_path, encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"  \u274c YAML parse error in meta sidecar: {yaml_path}")
        print(f"     {e}")
        return None


def load_yaml_plan(md_file_path: str) -> dict | None:
    """Load plan data from plans directory if exists (Split Architecture)."""
    md_path = Path(md_file_path)

    try:
        level_part = md_path.parent.name
        if level_part in ['a1', 'a2', 'b1', 'b2', 'c1', 'c2', 'lit', 'hist', 'bio', 'istorio']:
             level = level_part
        else:
             parts = md_path.parts
             if 'l2-uk-en' in parts:
                 idx = parts.index('l2-uk-en')
                 if idx + 1 < len(parts):
                     level = parts[idx+1]
                 else:
                     return None
             else:
                 return None
    except (ValueError, IndexError):
        return None

    base_dir = md_path.parent.parent
    slug = to_bare_slug(md_path.stem)
    plan_path = base_dir / 'plans' / level / (slug + '.yaml')

    if not plan_path.exists():
        plan_path = base_dir / 'plans' / level / (md_path.stem + '.yaml')
        if not plan_path.exists():
            return None

    try:
        with open(plan_path, encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"  \u274c YAML parse error in plan sidecar: {plan_path}")
        print(f"     {e}")
        return None


def load_yaml_vocab(md_file_path: str) -> tuple[list[dict] | None, str | None]:
    """Load vocabulary from YAML sidecar if exists.

    Returns (data, error_msg):
    - (list, None) on success
    - (None, None) if file not found
    - (None, error_string) on parse error
    """
    md_path = Path(md_file_path)
    yaml_path = md_path.parent / 'vocabulary' / (md_path.stem + '.yaml')
    if not yaml_path.exists():
        return None, None
    try:
        with open(yaml_path, encoding='utf-8') as f:
            data = yaml.safe_load(f)
            if isinstance(data, list):
                 return data, None
            if isinstance(data, dict):
                return data.get('vocabulary', data.get('items', [])), None
            return None, None
    except Exception as e:
        print(f"  \u274c YAML parse error in vocabulary sidecar: {yaml_path}")
        print(f"     {e}")
        return None, f"YAML parse error in {yaml_path.name}: {e}"


def get_module_number_from_curriculum(file_path: str, level_code: str) -> int | None:
    """
    Look up module number from curriculum.yaml manifest.

    Returns module number (1-based) or None if not found.
    """
    module_slug = Path(file_path).stem
    bare = to_bare_slug(module_slug)
    slug_variants = [module_slug] if bare == module_slug else [module_slug, bare]

    curriculum_yaml_path = Path(file_path).parent.parent / 'curriculum.yaml'
    if not curriculum_yaml_path.exists():
        return None

    try:
        with open(curriculum_yaml_path, encoding='utf-8') as f:
            curriculum = yaml.safe_load(f)

        level_key_map = {
            'A1': 'a1', 'A2': 'a2', 'B1': 'b1',
            'B2': 'b2', 'C1': 'c1', 'C2': 'c2',
        }

        track_match = re.search(r'/([abc][12]-[a-z]+)/', file_path)
        level_key = track_match.group(1) if track_match else level_key_map.get(level_code, level_code.lower())

        level_data = curriculum.get('levels', {}).get(level_key)
        if not level_data or 'modules' not in level_data:
            return None

        modules = level_data['modules']

        for idx, module_entry in enumerate(modules, start=1):
            module_slug_in_yaml = module_entry.split('#')[0].strip()

            if module_slug_in_yaml in slug_variants:
                return idx

            if module_slug.startswith(f"{idx:02d}-") and module_slug[3:] == module_slug_in_yaml:
                return idx

        return None

    except Exception:
        return None
