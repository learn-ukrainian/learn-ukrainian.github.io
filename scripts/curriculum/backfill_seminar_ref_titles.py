#!/usr/bin/env python3
"""
Backfill `references[].title` across all seminar plans.

Derivation rules (first match wins):
1. `work`
2. `name`
3. `source`
4. `path` -> last segment, drop extension, replace dashes/underscores with spaces, Title Case.
5. `url` or `source_url` -> same as 4.
6. `note` -> first 80 chars + ellipsis if truncated.

Does not modify CORE plans (a1, a2, b1, b2, c1, c2).
Preserves existing non-empty `title:` fields.
Idempotent.
"""

import sys
from pathlib import Path
from urllib.parse import unquote, urlparse

import yaml


def derive_from_url_or_path(val: str) -> str:
    val = unquote(val)
    parts = [p for p in val.split('/') if p]
    if not parts:
        return ""
    last_seg = parts[-1]

    for ext in ['.md', '.html', '.htm']:
        if last_seg.endswith(ext):
            last_seg = last_seg[:-len(ext)]
            break

    last_seg = last_seg.replace('-', ' ').replace('_', ' ')
    return ' '.join(word.capitalize() for word in last_seg.split())

def derive_title(ref: dict) -> str:
    if ref.get('work'):
        return str(ref['work']).strip()
    if ref.get('name'):
        return str(ref['name']).strip()
    if ref.get('source'):
        return str(ref['source']).strip()

    path = ref.get('path')
    if path:
        derived = derive_from_url_or_path(path)
        if derived:
            return derived

    url = ref.get('url') or ref.get('source_url')
    if url:
        derived = derive_from_url_or_path(url)
        if derived:
            return derived

    note = ref.get('note')
    if note:
        note = str(note).strip()
        if len(note) > 80:
            return note[:80] + '...'
        return note

    return ""

def backfill_plan(plan_path: Path) -> bool:
    try:
        with open(plan_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except Exception as e:
        print(f"Error loading {plan_path}: {e}")
        return False

    if not isinstance(data, dict):
        return False

    file_changed = False

    if 'references' not in data or not isinstance(data['references'], list):
        data['references'] = []
        file_changed = True

    if len(data['references']) == 0:
        data['references'].append({'title': 'Pending Reference', 'type': 'wiki', 'note': 'Placeholder added during title backfill'})
        file_changed = True

    new_refs = []
    for ref in data['references']:
        if not isinstance(ref, dict):
            new_refs.append(ref)
            continue

        if not ref.get('title'):
            new_title = derive_title(ref)
            if new_title:
                new_ref = {'title': new_title}
                new_ref.update(ref)
                new_refs.append(new_ref)
                file_changed = True
            else:
                new_refs.append(ref)
        else:
            new_refs.append(ref)

    if file_changed:
        data['references'] = new_refs
        with open(plan_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(
                data,
                f,
                allow_unicode=True,
                sort_keys=False,
                default_flow_style=False,
                width=10**9
            )
        return True
    return False

def main():
    plans_dir = Path("curriculum/l2-uk-en/plans")
    seminar_levels = {
        'hist', 'bio', 'istorio', 'lit', 'lit-essay', 'lit-hist-fic',
        'lit-fantastika', 'lit-war', 'lit-humor', 'lit-youth', 'lit-doc',
        'lit-drama', 'lit-crimea', 'oes', 'ruth', 'folk'
    }

    changed_files = 0

    for level in seminar_levels:
        level_dir = plans_dir / level
        if not level_dir.exists():
            continue

        for plan_file in level_dir.glob("**/*.yaml"):
            if backfill_plan(plan_file):
                changed_files += 1

    print(f"Backfilled refs across {changed_files} files.")

if __name__ == '__main__':
    main()
