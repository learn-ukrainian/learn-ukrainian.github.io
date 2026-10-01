"""Read-only ULIF/trie comparison for the complete evidence + deployed A1 corpus."""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
from pathlib import Path

import yaml

from scripts.verification import stress
from scripts.wiki.sources_db import ulif_stress_build, ulif_stress_rows

WORD_RE = re.compile(r"[А-Яа-яЄєІіЇїҐґ][А-Яа-яЄєІіЇїҐґ\u0301\u0300'’ʼ-]*")


def corpus_forms(root: Path) -> tuple[list[str], list[dict]]:
    """Union of every word-store form and every Ukrainian token in shipped A1 MDX."""
    forms: set[str] = set()
    inputs: list[dict] = []
    stores = sorted((root / 'curriculum/l2-uk-en/evidence').glob('*/_words.yaml'))
    lessons = sorted(path for track in ('a1', 'a1-v1')
                     for path in (root / 'site/src/content/docs' / track).rglob('*.mdx'))
    if not stores or not lessons:
        raise ValueError('Both evidence word stores and deployed A1 lessons are required')
    for path in stores + lessons:
        raw = path.read_bytes()
        inputs.append({'path': str(path.relative_to(root)), 'sha256': hashlib.sha256(raw).hexdigest()})
        if path in stores:
            doc = yaml.safe_load(raw)
            forms.update(stress._strip_stress(f['form']) for w in doc['words'] for f in w['forms'])
        else:
            forms.update(stress._strip_stress(m.group()).strip("'-’ʼ") for m in WORD_RE.finditer(raw.decode()))
    return sorted(forms - {''}), inputs


def compare_form(form: str) -> dict:
    """Compare raw authorities, excluding overrides and policy selection."""
    rows = ulif_stress_rows(form)
    value = stress._trie_value(stress._load_trie(), form)
    trie = [] if value is None else [
        {'tags': tags, 'vowel_indices': [p - 1 for p in positions]}
        for tags, positions in stress._parse_dictionary_value(value)
    ]
    ulif = [{k: row[k] for k in ('id', 'entry_id', 'entry_key', 'form_stressed', 'grammatical_tags',
                                'stress_vowel_indices', 'dual_stress_flag', 'pedagogical_stressed_form')}
            for row in rows]
    positions = {tuple(json.loads(row['stress_vowel_indices'])) for row in rows}
    trie_positions = {tuple(r['vowel_indices']) for r in trie}
    category = ('agree' if positions == trie_positions else 'disagree') if positions and trie_positions else (
        'ulif_only' if positions else 'trie_only' if trie_positions else 'neither')
    return {'form': form, 'category': category, 'ulif': ulif, 'trie': trie,
            'vesum': stress._vesum_lookup(form), 'ambiguous': len(positions) > 1,
            'dual': any(row['dual_stress_flag'] for row in rows)}


def write_report(root: Path, out: Path, *, seed: int = 8398) -> dict:
    """Write the full corpus comparison, disagreements, sample and hashed denominator."""
    forms, inputs = corpus_forms(root)
    out.mkdir(parents=True, exist_ok=True)
    counts = dict.fromkeys(('agree', 'disagree', 'ulif_only', 'trie_only', 'neither', 'ambiguous', 'dual'), 0)
    disagreements = []
    with (out / 'comparison.jsonl').open('w', encoding='utf-8') as stream:
        for form in forms:
            record = compare_form(form)
            counts[record['category']] += 1
            counts['ambiguous'] += int(record['ambiguous'])
            counts['dual'] += int(record['dual'])
            stream.write(json.dumps(record, ensure_ascii=False) + '\n')
            if record['category'] == 'disagree':
                disagreements.append(record)
    sample = random.Random(seed).sample(disagreements, min(60, len(disagreements)))
    for name, records in (('disagreements.jsonl', disagreements), ('sample-60.jsonl', sample)):
        (out / name).write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in records), encoding='utf-8')
    summary = {'denominator': len(forms), 'counts': counts, 'sample_seed': seed, 'sample_size': len(sample),
               'inputs': inputs, 'ulif_build': ulif_stress_build(), 'trie_digest': stress._trie_digest(),
               'categories': 'agree/disagree/ulif_only/trie_only/neither partition; ambiguous and dual overlap'}
    (out / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Compare checked ULIF forms with the raw stress trie over evidence and public A1 MDX.\n"
                    "Use for measurement and adjudication before a stress-policy change, never to choose a winner.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  .venv/bin/python -m scripts.verification.stress_comparison
  .venv/bin/python -m scripts.verification.stress_comparison --root . --seed 8398
Outputs: comparison.jsonl, disagreements.jsonl, sample-60.jsonl and summary.json in --out.
Sources DB and trie are read-only; existing report files in --out are replaced.
Exit codes: 0 = complete corpus report; >=1 = unavailable inputs or failed lookup.
Related: #8398 part B, #8400 steps 8-9; docs/verification/ulif-first-stress.md.
""",
    )
    parser.add_argument("--root", type=Path, default=Path.cwd(),
                        help="Repository input root (default: current directory; example: .).")
    parser.add_argument("--out", type=Path, default=Path("batch_state/stress-ulif-vs-trie"),
                        help="Report directory (default: batch_state/stress-ulif-vs-trie; example: batch_state/report).")
    parser.add_argument("--seed", type=int, default=8398,
                        help="Deterministic sample seed (default: 8398; example: 8400).")
    args = parser.parse_args(argv)
    result = write_report(args.root, args.out, seed=args.seed)
    print(json.dumps({k: result[k] for k in ("denominator", "counts", "sample_seed", "sample_size")}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
