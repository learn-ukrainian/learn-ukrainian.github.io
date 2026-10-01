"""Source-faithful ULIF form readings and conservative grammatical joins."""
from __future__ import annotations

import json
from typing import Any

from scripts.curriculum.evidence.tags import TagMapper
from scripts.lexicon.runner.ulif_dictua_parse import lookup_ulif_label
from scripts.wiki.sources_db import normalize_ulif_dictua_query, ulif_stress_rows


def _features(row: dict) -> set[str]:
    """Map the existing parser's VESUM atoms and entry label to UD features."""
    atoms = set(json.loads(row['grammatical_tags']))
    grammar = lookup_ulif_label(row['grammatical_label'])
    if grammar:
        atoms.update(grammar.tags)
    # These two source labels are not mapped by the forms parser yet.
    if row['grammatical_label'] == 'сполучник':
        atoms.add('conj')
    if row['grammatical_label'] == 'займенник':
        atoms.update(('noun', 'pron'))
    return set(TagMapper()(':'.join(sorted(atoms))))


def compatible(required: set[str], supplied: set[str]) -> bool:
    """No shared feature may conflict; unknown features cannot select a reading."""
    wanted = dict(tag.split('=', 1) for tag in supplied if '=' in tag)
    return all(wanted.get(k, v) == v or (k == 'upos' and {wanted.get(k), v} <= {'NOUN', 'PROPN'})
               for k, v in (tag.split('=', 1) for tag in required if '=' in tag))


def readings(form: str, *, supplied: set[str], lemma: str | None, vesum: list[dict]) -> list[dict[str, Any]]:
    """Return each stress choice once, retaining every supporting form row."""
    from scripts.verification.stress import (
        _build_match,
        _stress_positions_in_marked_string,
        _strip_stress,
    )

    rows = ulif_stress_rows(form)
    if lemma:
        for spelling in (form.lower(), form.title()):
            rows += [row for row in ulif_stress_rows(spelling) if row not in rows]
    selected: list[tuple[dict, set[str], list[dict]]] = []
    for row in rows:
        indices = json.loads(row['stress_vowel_indices'])
        if not indices or any(i < 0 or i >= len(form) for i in indices):
            continue
        if lemma:
            bare = normalize_ulif_dictua_query(_strip_stress(lemma))
            if row['normalized_query'] != bare:
                continue
            if _stress_positions_in_marked_string(lemma)[1] and (
                _stress_positions_in_marked_string(lemma)[1] !=
                _stress_positions_in_marked_string(row['canonical_headword'])[1]
            ):
                continue
        features = _features(row)
        if supplied and not compatible(features, supplied):
            continue
        # Join on lemma and compatible morphology. Absence is not a reason
        # to discard a source-attested ULIF reading.
        witnesses = [v for v in vesum if normalize_ulif_dictua_query(_strip_stress(v.get('lemma', ''))) == row['normalized_query']
                     and compatible(features, set(TagMapper()(v.get('tags', ''))))]
        selected.append((row, features, witnesses))

    # If a supplied case/number is represented, omit lemma-only rows, which
    # otherwise could reintroduce a stress rejected by the paradigm filter.
    grammatical = {t.split('=', 1)[0] for t in supplied} & {'Case', 'Number', 'Tense', 'Person', 'VerbForm'}
    if grammatical and any(not row['is_lemma'] for row, _, _ in selected):
        selected = [(row, features, witnesses) for row, features, witnesses in selected
                    if not row['is_lemma']]

    grouped: dict[tuple[int, ...], dict] = {}
    for row, features, witnesses in selected:
        indices = tuple(json.loads(row['stress_vowel_indices']))
        match = grouped.get(indices)
        if match is None:
            match = _build_match(form, [i + 1 for i in indices], sorted(features), override_applied=False)
            match.update(source='ulif', evidence=[], grammatical_tags=[], vesum_analyses=[],
                         dual_stress=False, variants=[])
            grouped[indices] = match
        match['evidence'].append({k: row[k] for k in ('id', 'entry_id', 'entry_key', 'source_page_sha256',
                                                      'source_entry_fingerprint', 'grammatical_tags')})
        match['grammatical_tags'].append(json.loads(row['grammatical_tags']))
        match['dual_stress'] |= bool(row['dual_stress_flag'])
        for witness in witnesses:
            if witness not in match['vesum_analyses']:
                match['vesum_analyses'].append(witness)
        if row['pedagogical_stressed_form']:
            choice = row['pedagogical_stressed_form']
            previous = match.get('pedagogical_stressed_form')
            if previous is None:
                match['pedagogical_stressed_form'] = choice
            elif previous != choice:
                match['pedagogical_conflict'] = True
        if row['dual_stress_flag'] and '-' not in form:
            match['variants'] = [form[:i + 1] + '\u0301' + form[i + 1:] for i in indices]
        else:
            match['variants'] = [match['stressed_form']]
    for match in grouped.values():
        witnesses = match['vesum_analyses']
        match['vesum'] = witnesses[0] if len(witnesses) == 1 else None
    return list(grouped.values())
