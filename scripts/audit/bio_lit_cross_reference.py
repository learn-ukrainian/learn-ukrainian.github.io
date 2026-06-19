#!/usr/bin/env python3
"""
Bio↔LIT cross-reference audit.

For every author appearing in LIT-track plans (plans/lit/*.yaml + plans/lit-*/*.yaml),
verify that a corresponding bio exists in plans/bio/*.yaml — or that the author is
on the documented exclusion list.

Run:
    .venv/bin/python -m scripts.audit.bio_lit_cross_reference

Output:
    - stdout: summary of gaps
    - exit code: 0 if no gaps (or all gaps excluded), 1 if undocumented gaps
    - writes docs/audits/bio-lit-cross-reference-gaps.md with current state

Used by: CI (planned) + manual checks before merging new LIT plans.
"""

import re
import sys
from datetime import datetime
from pathlib import Path

import yaml


def transliterate_uk_to_en(text: str) -> str:
    text = text.lower()
    text = text.replace("зг", "zgh")
    text = re.sub(r'(^|[^a-zа-яіїєґ])ї', r'\1yi', text)
    text = re.sub(r'(^|[^a-zа-яіїєґ])й', r'\1y', text)
    text = re.sub(r'(^|[^a-zа-яіїєґ])є', r'\1ye', text)
    text = re.sub(r'(^|[^a-zа-яіїєґ])ю', r'\1yu', text)
    text = re.sub(r'(^|[^a-zа-яіїєґ])я', r'\1ya', text)

    mapping = {
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'h', 'ґ': 'g', 'д': 'd', 'е': 'e',
        'є': 'ie', 'ж': 'zh', 'з': 'z', 'и': 'y', 'і': 'i', 'ї': 'i', 'й': 'i',
        'к': 'k', 'л': 'l', 'м': 'm', 'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r',
        'с': 's', 'т': 't', 'у': 'u', 'ф': 'f', 'х': 'kh', 'ц': 'ts', 'ч': 'ch',
        'ш': 'sh', 'щ': 'shch', 'ь': '', "'": '', '’': '', 'ю': 'iu', 'я': 'ia'
    }

    res = "".join(mapping.get(c, c) for c in text)
    res = re.sub(r'[^a-z\- ]', '', res)
    return res.strip()

def is_thematic_slug(lit_slug: str, title: str) -> bool:
    """Filter out thematic literature tracks that do not map to an individual author."""
    thematic_terms = {
        'anthology', 'poetry', 'literature', 'tradition', 'testimony',
        'folklore', 'memes', 'chronicles', 'essay', 'war', 'holocaust',
        'syntez', 'origins', 'diary', 'letters', 'court', 'oral',
        'deportation', 'satire', 'humor', 'kids', 'documentary',
        'fantastika', 'avdet', 'crimean', 'anthologies', 'poems'
    }
    tokens = set(lit_slug.split('-'))
    if tokens & thematic_terms:
        return True

    title_lower = title.lower()
    uk_thematic = {
        'антологія', 'поезія', 'література', 'традиція', 'свідчення',
        'фольклор', 'хроніки', 'есе', 'війна', 'голокост', 'синтез',
        'щоденник', 'листування', 'гумор', 'сатира', 'документалістика',
        'фантастика', 'антології', 'вірші'
    }
    return any(term in title_lower for term in uk_thematic)

def extract_bio_slug(lit_slug: str, yaml_data: dict, existing_bios: set, bio_aliases: dict | None = None) -> str:
    """
    Extracts the canonical bio slug from a LIT plan.
    """
    if bio_aliases is None:
        bio_aliases = {}

    # 1. Check if the lit_slug explicitly starts with an existing bio slug
    for b in existing_bios:
        if lit_slug == b or lit_slug.startswith(b + '-'):
            return b

    # 2. Check against alias table
    for b, aliases in bio_aliases.items():
        for alias in aliases:
            alias_slug = transliterate_uk_to_en(alias).replace(' ', '-')
            if lit_slug == alias_slug or lit_slug.startswith(alias_slug + '-'):
                return b

    # 3. Check if a surname from existing bios is in the lit_slug tokens
    surname_to_bio = {b.split('-')[-1]: b for b in existing_bios}
    tokens = lit_slug.split('-')
    for t in tokens:
        if t in surname_to_bio:
            return surname_to_bio[t]

    # 4. If it's a gap, try to derive the canonical name from the title
    title = yaml_data.get('title', '') if yaml_data else ''
    match = re.split(r'[:\.,"«—–]', title)
    if match and len(match) > 1:
        author_candidate = match[0].strip()
        # Ensure it looks like a name (1 to 4 words)
        if 1 <= len(author_candidate.split()) <= 4:
            return transliterate_uk_to_en(author_candidate).replace(' ', '-')

    # 5. Fallback to slug derivation
    if len(tokens) == 2 and not yaml_data:
        return lit_slug

    return tokens[0]

def load_exclusions(filepath: Path) -> dict:
    exclusions = {}
    if not filepath.exists():
        return exclusions

    with open(filepath, encoding='utf-8') as f:
        content = f.read()

    in_table = False
    for line in content.splitlines():
        line = line.strip()
        if line.startswith('| LIT plan(s)'):
            in_table = True
            continue
        if in_table and line.startswith('|-'):
            continue
        if in_table and line.startswith('|'):
            parts = [p.strip() for p in line.split('|')]
            if len(parts) >= 3:
                plans_str = parts[1]
                plan_paths = [p.strip() for p in plans_str.split(',')]
                for plan in plan_paths:
                    exclusions[plan] = True

    return exclusions

def main():
    repo_root = Path(__file__).resolve().parent.parent.parent
    bio_dir = repo_root / 'curriculum' / 'l2-uk-en' / 'plans' / 'bio'
    lit_dirs = list(repo_root.glob('curriculum/l2-uk-en/plans/lit*'))

    exclusion_file = repo_root / 'docs' / 'audits' / 'bio-lit-cross-reference-exclusions.md'
    gap_file = repo_root / 'docs' / 'audits' / 'bio-lit-cross-reference-gaps.md'

    exclusions = load_exclusions(exclusion_file)

    bios = set()
    bio_aliases = {}
    for p in bio_dir.glob('*.yaml'):
        bios.add(p.stem)
        try:
            with open(p, encoding='utf-8') as f:
                data = yaml.safe_load(f)
                if data and 'aliases' in data:
                    bio_aliases[p.stem] = data['aliases']
        except Exception:
            pass

    all_lit_plans = []
    for d in lit_dirs:
        if d.is_dir():
            all_lit_plans.extend(d.glob('*.yaml'))

    gaps = []
    current_date = datetime.now().date().isoformat()

    for p in all_lit_plans:
        lit_slug = p.stem
        rel_path = f"plans/{p.parent.name}/{p.name}"

        if rel_path in exclusions:
            continue

        with open(p, encoding='utf-8') as f:
            try:
                data = yaml.safe_load(f)
            except Exception:
                data = {}

        if is_thematic_slug(lit_slug, data.get('title', '')):
            continue

        candidate = extract_bio_slug(lit_slug, data, bios, bio_aliases)

        if candidate not in bios:
            gaps.append((rel_path, f"{candidate}.yaml"))

    if gaps:
        print(f"Found {len(gaps)} gaps (LIT plans missing BIO or exclusions):")
        for plan, candidate in gaps:
            print(f"  - {plan} -> Missing bio candidate: {candidate}")

        with open(gap_file, 'w', encoding='utf-8') as f:
            f.write("# Bio↔LIT Cross-Reference — Current Gaps\n\n")
            f.write(f"Generated {current_date} by `scripts/audit/bio_lit_cross_reference.py`.\n\n")
            f.write("## Confirmed gaps requiring bio creation\n\n")
            f.write("| LIT plan(s) | Missing bio slug | Notes |\n")
            f.write("|---|---|---|\n")
            for plan, candidate in sorted(gaps):
                f.write(f"| {plan} | {candidate} | |\n")

        sys.exit(1)
    else:
        print("All LIT plans are covered by a BIO or an exclusion.")
        with open(gap_file, 'w', encoding='utf-8') as f:
            f.write("# Bio↔LIT Cross-Reference — Current Gaps\n\n")
            f.write(f"Generated {current_date} by `scripts/audit/bio_lit_cross_reference.py`.\n\n")
            f.write("No undocumented gaps found. All clear!\n")
        sys.exit(0)

if __name__ == '__main__':
    main()
