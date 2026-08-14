#!/usr/bin/env python3
"""Sense-first Word Atlas entry lint (#6437): LINT-001 … LINT-004 + LINT-101/102.

Read-only lint over the `senses[]` array and practice bindings
documented in ``docs/runbooks/word-atlas-entry-model.md`` (§ Sense-Level
Fields, #6437 delta). The default mode is advisory. The ``--ratchet`` mode
blocks only findings for new or changed entries while keeping pre-existing
findings visible and advisory.

Rules implemented
==================
- **LINT-001** ``TRUNCATED_TEXT_CUTOFF`` — a learner-facing sense field
  (``uk_source_def``, ``learner_uk``, ``learner_en[]``, ``en_disambiguation``,
  ``grammar_notes``) ends in ``...``/``…`` while ``completeness`` is not
  honestly tagged ``"truncated"``.
- **LINT-002** ``AMBIGUOUS_BARE_EN`` — ``learner_en`` is a single-item list,
  the word is in the high-risk polysemy denylist below, and
  ``en_disambiguation`` is missing or blank.
- **LINT-003** ``DRILL_SENSE_ID_MISSING`` — a practice binding / deck item
  references a lemma (``lemmaId`` / ``lemma``) without a non-empty
  ``senseId`` / ``sense_id``. This prohibits silent ``en[0]`` drill
  fallbacks once sense-first wiring is present.
- **LINT-004** ``UNVETTED_EN_SOURCE`` — a sense has published non-empty
  ``learner_en`` while ``source`` is missing, blank, or outside the
  enrich vocabulary ``SENSE_SOURCE_SOURCED ∪ {ai_minimum}``. Honest
  ``ai_minimum`` does not fire (that tag is already the vetted-thin label).
- **LINT-101** ``MULTI_SENSE_UK_SINGLE_EN`` — entry has ≥2 senses but only
  one published ``learner_en``, or a single shared EN list without
  per-sense ``en_disambiguation`` (entry-level EN, or identical sense EN
  lists with incomplete disambiguation). Bypassed when
  ``is_fixed_expression`` is true.
- **LINT-102** ``POS_TRANSFORM_MISMATCH`` — sense ``pos`` disagrees with
  entry/lexeme POS after coarse normalization, with a clear mismatch
  signal. Documented multi-POS articles
  (``multi_pos`` / slash-separated / multi-value ``pos``) are not flagged.
  Does not infer EN-gloss POS (Gemini consult example deferred — high
  false-positive risk without a vetted EN POS lexicon).

Scope
=====
- LINT-001/002/004/101/102: entries without a ``senses`` array are silently
  skipped — most of the production manifest predates this schema.
- LINT-003: inspects explicit practice bindings on the manifest
  (``practice_items`` / per-entry ``practice_bindings``) and optional
  ``--practice-deck`` shards. Legacy decks without sense-first migration
  are reported as advisory residual, not CI blockers.

Use when
========
- Local dry run against a small fixture while building sense-first content.
- Optional report mode against a local manifest — writes residual findings
  to a gitignored ``batch_state/`` path only; never to a tracked doc.

Examples
========

    .venv/bin/python scripts/audit/lint_word_atlas.py
    .venv/bin/python scripts/audit/lint_word_atlas.py --manifest path/to/manifest.json
    .venv/bin/python scripts/audit/lint_word_atlas.py --manifest path/to/manifest.json \\
        --practice-deck site/public/lexicon/practice-index.A1.json \\
        --report batch_state/atlas-drive/lint-word-atlas-residual.json
    .venv/bin/python scripts/audit/lint_word_atlas.py --strict   # exit 1 on any finding

Outputs
=======
- stdout: table of findings (rule, entry, sense, field, detail), or a compact
  ratchet/debt summary in ``--ratchet`` mode.
- exit 0 by default; ``--strict`` fails on any finding, while ``--ratchet``
  fails only on touched-entry LINT-003/004/101/102 findings or an increased
  debt baseline.

Related
=======
- Issue #6437 — sense-first lintable entry gate.
- Schema: docs/runbooks/word-atlas-entry-model.md § Sense-Level Fields.
- Sibling guardrails: scripts/audit/check_atlas_manifest_enrichment.py.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Reuse enrich honesty vocabulary — do not invent a parallel source set (#6437).
from scripts.lexicon.enrich_manifest import (
    SENSE_SOURCE_AI_MINIMUM,
    SENSE_SOURCE_SOURCED,
)

DEFAULT_FIXTURE = PROJECT_ROOT / "tests" / "fixtures" / "atlas" / "sense_lint_sample.json"
DEFAULT_BASELINE = PROJECT_ROOT / "scripts" / "audit" / "word_atlas_lint_baseline.json"
MANIFEST_POINTER_PATH = "site/src/data/lexicon-manifest.pointer.json"
PRACTICE_DECK_POINTER_PATH = "site/src/data/lexicon-practice-deck.pointer.json"
BASELINE_SCHEMA_VERSION = 1

# Allowed ``source`` values for published ``learner_en`` (LINT-004). Sourced
# dictionary provenance plus the honest AI-minimum thin-gloss label.
_ALLOWED_EN_SOURCES = SENSE_SOURCE_SOURCED | {SENSE_SOURCE_AI_MINIMUM}

# Learner-facing string fields checked by LINT-001. `uk_source_def` is raw
# ingestion text (immutable — see schema doc) but a dishonest completeness
# tag on it is still worth flagging: the lint reads it, it never rewrites it.
_TRUNCATION_CHECKED_FIELDS = (
    "uk_source_def",
    "learner_uk",
    "en_disambiguation",
    "grammar_notes",
)
_ELLIPSIS_MARKERS = ("...", "…")
_HONEST_TRUNCATED_TAG = "truncated"

# High-risk polysemy seed set (Gemini consult, #6437). A bare single-word EN
# target from this set reads as one common sense while hiding an unrelated
# one (e.g. "second" as ordinal vs "seconds" as manufacturing defects/брак).
# Not exhaustive by design — extend as new false-friend cases surface.
AMBIGUOUS_BARE_EN_DENYLIST = frozenset(
    {
        "second",
        "set",
        "bank",
        "match",
        "light",
        "bear",
        "fair",
        "spring",
        "bat",
        "date",
        "fine",
        "left",
        "right",
        "party",
        "book",
        "fly",
        "watch",
        "sound",
        "novel",
        "stable",
        "mine",
        "current",
        "seal",
        "tear",
        "wave",
        "pitch",
        "note",
        "trip",
        "letter",
    }
)

# Practice-deck body keys that carry lemma-bound cards (#6437 LINT-003).
# ``lexemes`` (the atlas-practice-lexemes shard body key, generated by
# ``_build_lexeme`` in generate_practice_deck.py) carries the same
# ``lemmaId``/``senseId`` binding as every drill-mode card and is scanned for
# the identical reason: a lexeme with no ``senseId`` is a residual en[0]
# fallback risk once sense-first wiring exists for its entry (#6437 PR3).
_PRACTICE_CARD_LIST_KEYS = (
    "items",
    "lexemes",
    "cloze",
    "stress",
    "classify",
    "paradigm",
    "synonym",
    "heritage",
    "paronym",
    "antonym",
    "homonym",
)

LINT_001 = "LINT-001"
LINT_002 = "LINT-002"
LINT_003 = "LINT-003"
LINT_004 = "LINT-004"
LINT_101 = "LINT-101"
LINT_102 = "LINT-102"
IMPLEMENTED_RULE_IDS = (LINT_001, LINT_002, LINT_003, LINT_004, LINT_101, LINT_102)
RATCHET_RULE_IDS = frozenset({LINT_003, LINT_004, LINT_101, LINT_102})

# Coarse POS families for LINT-102. Only labels that map into this set can
# produce a "clear mismatch signal"; unknown tags are left alone.
_POS_FAMILY_ALIASES: dict[str, str] = {
    "noun": "noun",
    "n": "noun",
    "іменник": "noun",
    "proper noun": "noun",
    "proper name": "noun",
    "verb": "verb",
    "v": "verb",
    "дієслово": "verb",
    "adjective": "adjective",
    "adj": "adjective",
    "a": "adjective",
    "прикметник": "adjective",
    "adverb": "adverb",
    "adv": "adverb",
    "прислівник": "adverb",
    "numeral": "numeral",
    "numr": "numeral",
    "num": "numeral",
    "числівник": "numeral",
    "preposition": "preposition",
    "prep": "preposition",
    "прийменник": "preposition",
    "conjunction": "conjunction",
    "conj": "conjunction",
    "сполучник": "conjunction",
    "particle": "particle",
    "part": "particle",
    "частка": "particle",
    "pronoun": "pronoun",
    "pron": "pronoun",
    "займенник": "pronoun",
    "interjection": "interjection",
    "intj": "interjection",
    "вигук": "interjection",
}


@dataclass(frozen=True)
class LintFinding:
    rule_id: str
    rule_name: str
    entry_slug: str
    sense_id: str
    field: str
    detail: str


@dataclass(frozen=True)
class DebtBaselineResult:
    current_counts: dict[str, int]
    baseline_counts: dict[str, int] | None
    comparison_counts: dict[str, int] | None
    errors: tuple[str, ...]
    updated: bool

    @property
    def passed(self) -> bool:
        return not self.errors


def finding_counts(findings: list[LintFinding]) -> dict[str, int]:
    """Count findings by every implemented rule, including zeroes."""
    counts = {rule_id: 0 for rule_id in IMPLEMENTED_RULE_IDS}
    for finding in findings:
        counts[finding.rule_id] = counts.get(finding.rule_id, 0) + 1
    return counts


def _canonical_digest(value: object) -> str:
    canonical = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _stable_entry_key(entry: dict[str, Any]) -> str | None:
    for field in ("slug", "lemma"):
        value = entry.get(field)
        if isinstance(value, str) and value.strip():
            return value.strip()
        if value is not None and not isinstance(value, (dict, list)):
            return str(value)
    return None


def _entry_digests(manifest: dict[str, Any]) -> tuple[dict[str, str], tuple[str, ...]]:
    known: dict[str, str] = {}
    unknown: list[str] = []
    for entry in _entries(manifest):
        key = _stable_entry_key(entry)
        digest = _canonical_digest(entry)
        if key is None:
            unknown.append(digest)
            continue
        if key in known:
            raise ValueError(f"duplicate Atlas entry identity: {key!r}")
        known[key] = digest
    return known, tuple(sorted(unknown))


def _practice_entry_digests(
    manifests: list[tuple[str, dict[str, Any]]],
) -> dict[str, str]:
    grouped: dict[str, list[str]] = {}
    for source_name, manifest in manifests:
        items = manifest.get("practice_items")
        if not isinstance(items, list):
            continue
        for item in items:
            if not isinstance(item, dict):
                continue
            lemma = _binding_lemma(item)
            if lemma is None:
                continue
            grouped.setdefault(lemma, []).append(_canonical_digest({"source": source_name, "item": item}))
    return {key: _canonical_digest(sorted(digests)) for key, digests in grouped.items()}


def changed_entry_keys(base_manifest: dict[str, Any], current_manifest: dict[str, Any]) -> set[str]:
    """Return entry identities added, removed, or changed between manifests.

    Entry identity is the stable ``slug``/``lemma`` value. Entries without one
    are conservatively treated as a changed ``<unknown-entry>`` scope whenever
    their serialized content differs, because a finding cannot be safely
    attributed to an untouched anonymous record.
    """
    base, base_unknown = _entry_digests(base_manifest)
    current, current_unknown = _entry_digests(current_manifest)
    changed = {key for key in base.keys() | current.keys() if base.get(key) != current.get(key)}
    if base_unknown != current_unknown:
        changed.add("<unknown-entry>")

    base_practice = _practice_entry_digests([("manifest", base_manifest)])
    current_practice = _practice_entry_digests([("manifest", current_manifest)])
    changed.update(
        key
        for key in base_practice.keys() | current_practice.keys()
        if base_practice.get(key) != current_practice.get(key)
    )
    return changed


def changed_practice_entry_keys(
    base_decks: list[tuple[str, dict[str, Any]]],
    current_decks: list[tuple[str, dict[str, Any]]],
) -> set[str]:
    """Return lemma identities whose practice cards changed between decks."""
    base = _practice_deck_entry_digests(base_decks)
    current = _practice_deck_entry_digests(current_decks)
    return {key for key in base.keys() | current.keys() if base.get(key) != current.get(key)}


def _practice_deck_entry_digests(
    decks: list[tuple[str, dict[str, Any]]],
) -> dict[str, str]:
    grouped: dict[str, list[str]] = {}
    for source_name, deck in decks:
        for item in _practice_cards_from_deck(deck):
            lemma = _binding_lemma(item)
            if lemma is None:
                continue
            grouped.setdefault(lemma, []).append(_canonical_digest({"source": source_name, "item": item}))
    return {key: _canonical_digest(sorted(digests)) for key, digests in grouped.items()}


def ratchet_blocking_findings(findings: list[LintFinding], changed_entries: set[str]) -> list[LintFinding]:
    """Return only touched-entry findings in the four ratcheted rules."""
    return [
        finding for finding in findings if finding.rule_id in RATCHET_RULE_IDS and finding.entry_slug in changed_entries
    ]


def _entries(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    entries = manifest.get("entries")
    if isinstance(entries, list):
        return [entry for entry in entries if isinstance(entry, dict)]
    return []


def _entry_slug(entry: dict[str, Any]) -> str:
    slug = entry.get("slug") or entry.get("lemma")
    return str(slug) if slug else "<unknown-entry>"


def _senses(entry: dict[str, Any]) -> list[dict[str, Any]]:
    senses = entry.get("senses")
    if isinstance(senses, list):
        return [sense for sense in senses if isinstance(sense, dict)]
    return []


def _sense_id(sense: dict[str, Any]) -> str:
    sense_id = sense.get("id")
    return str(sense_id) if sense_id else "<missing-sense-id>"


def _is_truncated_text(value: object) -> bool:
    return isinstance(value, str) and value.rstrip().endswith(_ELLIPSIS_MARKERS)


def _check_truncated_text_cutoff(entry_slug: str, sense_id: str, sense: dict[str, Any]) -> list[LintFinding]:
    if sense.get("completeness") == _HONEST_TRUNCATED_TAG:
        return []

    findings: list[LintFinding] = []
    for field in _TRUNCATION_CHECKED_FIELDS:
        value = sense.get(field)
        if _is_truncated_text(value):
            findings.append(
                LintFinding(
                    rule_id=LINT_001,
                    rule_name="TRUNCATED_TEXT_CUTOFF",
                    entry_slug=entry_slug,
                    sense_id=sense_id,
                    field=field,
                    detail=f"ends in an ellipsis without completeness={_HONEST_TRUNCATED_TAG!r}: {value!r}",
                )
            )

    learner_en = sense.get("learner_en")
    if isinstance(learner_en, list):
        for index, item in enumerate(learner_en):
            if _is_truncated_text(item):
                findings.append(
                    LintFinding(
                        rule_id=LINT_001,
                        rule_name="TRUNCATED_TEXT_CUTOFF",
                        entry_slug=entry_slug,
                        sense_id=sense_id,
                        field=f"learner_en[{index}]",
                        detail=f"ends in an ellipsis without completeness={_HONEST_TRUNCATED_TAG!r}: {item!r}",
                    )
                )
    return findings


def _check_ambiguous_bare_en(entry_slug: str, sense_id: str, sense: dict[str, Any]) -> list[LintFinding]:
    learner_en = sense.get("learner_en")
    if not isinstance(learner_en, list) or len(learner_en) != 1:
        return []

    word = learner_en[0]
    if not isinstance(word, str):
        return []

    normalized = word.strip().casefold()
    if normalized not in AMBIGUOUS_BARE_EN_DENYLIST:
        return []

    disambiguation = sense.get("en_disambiguation")
    if isinstance(disambiguation, str) and disambiguation.strip():
        return []

    return [
        LintFinding(
            rule_id=LINT_002,
            rule_name="AMBIGUOUS_BARE_EN",
            entry_slug=entry_slug,
            sense_id=sense_id,
            field="learner_en",
            detail=(f"bare single-word EN {word!r} is a high-risk polysemy target with no en_disambiguation"),
        )
    ]


def _published_learner_en(sense: dict[str, Any]) -> list[str] | None:
    """Return non-blank published EN strings, or None when EN is not published."""
    learner_en = sense.get("learner_en")
    if not isinstance(learner_en, list) or not learner_en:
        return None
    published = [item.strip() for item in learner_en if isinstance(item, str) and item.strip()]
    if not published:
        return None
    return published


def _source_label(sense: dict[str, Any]) -> str | None:
    """Normalize ``source`` to a non-blank string, or None when absent/blank."""
    source = sense.get("source")
    if source is None:
        return None
    if isinstance(source, str):
        stripped = source.strip()
        return stripped or None
    return str(source)


def _check_unvetted_en_source(entry_slug: str, sense_id: str, sense: dict[str, Any]) -> list[LintFinding]:
    """LINT-004: published learner_en without a known enrich ``source`` label.

    Fires when ``learner_en`` is a non-empty list of non-blank strings AND
    ``source`` is absent, blank, or outside ``SENSE_SOURCE_SOURCED ∪
    {ai_minimum}``. Honest ``ai_minimum`` is allowed (vetted-thin honesty tag).
    """
    if _published_learner_en(sense) is None:
        return []

    source = _source_label(sense)
    if source is not None and source in _ALLOWED_EN_SOURCES:
        return []

    detail_source = "missing" if source is None else repr(source)
    return [
        LintFinding(
            rule_id=LINT_004,
            rule_name="UNVETTED_EN_SOURCE",
            entry_slug=entry_slug,
            sense_id=sense_id,
            field="source",
            detail=(
                f"published learner_en with unvetted source ({detail_source}); "
                f"expected one of {sorted(_ALLOWED_EN_SOURCES)}"
            ),
        )
    ]


def _has_nonempty_disambiguation(sense: dict[str, Any]) -> bool:
    disambiguation = sense.get("en_disambiguation")
    return isinstance(disambiguation, str) and bool(disambiguation.strip())


def _learner_en_key(sense: dict[str, Any]) -> tuple[str, ...] | None:
    """Stable key for comparing published ``learner_en`` lists across senses."""
    published = _published_learner_en(sense)
    if published is None:
        return None
    return tuple(item.casefold() for item in published)


def _entry_level_learner_en(entry: dict[str, Any]) -> list[str] | None:
    """Return published entry-level ``learner_en`` when present (shared list)."""
    return _published_learner_en(entry)


def _check_multi_sense_uk_single_en(entry: dict[str, Any]) -> list[LintFinding]:
    """LINT-101: multi-sense entry with incomplete / shared EN coverage.

    Narrow reading (#6437 binding + Gemini consult):
    - ≥2 senses required.
    - Bypass when ``is_fixed_expression`` is true (A1/A2 chunk mitigation).
    - Fire when exactly one sense publishes ``learner_en``.
    - Fire when entry-level ``learner_en`` is published (shared list).
    - Fire when ≥2 senses share an identical published ``learner_en`` list
      and at least one of those senses lacks non-empty ``en_disambiguation``.
    """
    if entry.get("is_fixed_expression") is True:
        return []

    senses = _senses(entry)
    if len(senses) < 2:
        return []

    slug = _entry_slug(entry)
    findings: list[LintFinding] = []

    senses_with_en = [(sense, key) for sense in senses if (key := _learner_en_key(sense)) is not None]

    if _entry_level_learner_en(entry) is not None:
        findings.append(
            LintFinding(
                rule_id=LINT_101,
                rule_name="MULTI_SENSE_UK_SINGLE_EN",
                entry_slug=slug,
                sense_id="<entry>",
                field="learner_en",
                detail=(
                    f"entry has {len(senses)} senses but a shared entry-level "
                    "learner_en list; prefer per-sense learner_en + en_disambiguation"
                ),
            )
        )

    if len(senses_with_en) == 1:
        sense, _key = senses_with_en[0]
        findings.append(
            LintFinding(
                rule_id=LINT_101,
                rule_name="MULTI_SENSE_UK_SINGLE_EN",
                entry_slug=slug,
                sense_id=_sense_id(sense),
                field="learner_en",
                detail=(
                    f"entry has {len(senses)} senses but only 1 publishes learner_en; remaining senses lack EN coverage"
                ),
            )
        )
    elif len(senses_with_en) >= 2:
        keys = {key for _sense, key in senses_with_en}
        if len(keys) == 1:
            missing_disambiguation = [
                sense for sense, _key in senses_with_en if not _has_nonempty_disambiguation(sense)
            ]
            if missing_disambiguation:
                sense = missing_disambiguation[0]
                findings.append(
                    LintFinding(
                        rule_id=LINT_101,
                        rule_name="MULTI_SENSE_UK_SINGLE_EN",
                        entry_slug=slug,
                        sense_id=_sense_id(sense),
                        field="learner_en",
                        detail=(
                            f"entry has {len(senses_with_en)} senses sharing one "
                            "learner_en list without per-sense en_disambiguation "
                            f"on {_sense_id(sense)}"
                        ),
                    )
                )

    return findings


def _normalize_pos_token(raw: object) -> str | None:
    """Normalize one POS token to a coarse family, or None when unknown."""
    if not isinstance(raw, str):
        return None
    token = raw.strip().casefold().replace("_", " ")
    if not token:
        return None
    # Strip morphology / style suffixes: ``noun:m``, ``proper noun:pl``.
    token = token.split(":", 1)[0].strip()
    return _POS_FAMILY_ALIASES.get(token)


def _split_pos_raw(raw: object) -> list[str]:
    """Split a POS field into candidate tokens (list or slash/semicolon string)."""
    if isinstance(raw, list):
        return [item for item in raw if isinstance(item, str) and item.strip()]
    if isinstance(raw, str) and raw.strip():
        text = raw.strip()
        if "/" in text or ";" in text:
            parts: list[str] = []
            for chunk in text.replace(";", "/").split("/"):
                chunk = chunk.strip()
                if chunk:
                    parts.append(chunk)
            return parts
        return [text]
    return []


def _entry_pos_raw(entry: dict[str, Any]) -> object | None:
    """Resolve entry/lexeme POS for LINT-102 (entry first, then lexeme)."""
    if entry.get("pos") is not None:
        return entry.get("pos")
    lexeme = entry.get("lexeme")
    if isinstance(lexeme, dict) and lexeme.get("pos") is not None:
        return lexeme.get("pos")
    return None


def _is_documented_multi_pos(entry: dict[str, Any]) -> bool:
    """True when the article explicitly documents multi-POS (do not flag)."""
    if entry.get("multi_pos") is True or entry.get("is_multi_pos") is True:
        return True
    allowed = entry.get("allowed_sense_pos")
    if isinstance(allowed, list) and len(allowed) > 1:
        return True
    tokens = _split_pos_raw(_entry_pos_raw(entry))
    return len(tokens) > 1


def _entry_pos_families(entry: dict[str, Any]) -> set[str]:
    families: set[str] = set()
    for token in _split_pos_raw(_entry_pos_raw(entry)):
        family = _normalize_pos_token(token)
        if family is not None:
            families.add(family)
    return families


def _check_pos_transform_mismatch(
    entry: dict[str, Any], entry_slug: str, sense_id: str, sense: dict[str, Any]
) -> list[LintFinding]:
    """LINT-102: sense POS vs entry/lexeme POS clear transform mismatch.

    Conservative: requires both sides to normalize to known coarse families,
    skips documented multi-POS articles, and does not invent EN-gloss POS.
    """
    if _is_documented_multi_pos(entry):
        return []

    entry_families = _entry_pos_families(entry)
    if len(entry_families) != 1:
        # Missing/unknown entry POS, or multi-token without multi_pos flag —
        # not a clear single-POS transform signal.
        return []

    sense_family = _normalize_pos_token(sense.get("pos"))
    if sense_family is None:
        return []

    entry_family = next(iter(entry_families))
    if sense_family == entry_family:
        return []

    return [
        LintFinding(
            rule_id=LINT_102,
            rule_name="POS_TRANSFORM_MISMATCH",
            entry_slug=entry_slug,
            sense_id=sense_id,
            field="pos",
            detail=(
                f"sense pos {sense.get('pos')!r} ({sense_family}) disagrees with "
                f"entry/lexeme pos family {entry_family!r} without multi_pos documentation"
            ),
        )
    ]


def _binding_lemma(item: dict[str, Any]) -> str | None:
    for key in ("lemmaId", "lemma_id", "lemma", "entry_slug", "slug"):
        value = item.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _binding_sense_id(item: dict[str, Any]) -> str | None:
    for key in ("senseId", "sense_id", "sense_slug"):
        value = item.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _check_drill_sense_id_missing(item: dict[str, Any]) -> LintFinding | None:
    lemma = _binding_lemma(item)
    if lemma is None:
        return None
    if _binding_sense_id(item) is not None:
        return None
    return LintFinding(
        rule_id=LINT_003,
        rule_name="DRILL_SENSE_ID_MISSING",
        entry_slug=lemma,
        sense_id="<missing-sense-id>",
        field="senseId",
        detail=(f"practice binding for lemma {lemma!r} has no senseId/sense_id (en[0] fallback is not allowed)"),
    )


def _practice_bindings_from_manifest(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    bindings: list[dict[str, Any]] = []
    top_level = manifest.get("practice_items")
    if isinstance(top_level, list):
        bindings.extend(item for item in top_level if isinstance(item, dict))
    for entry in _entries(manifest):
        per_entry = entry.get("practice_bindings")
        if not isinstance(per_entry, list):
            continue
        slug = _entry_slug(entry)
        for item in per_entry:
            if not isinstance(item, dict):
                continue
            enriched = dict(item)
            if _binding_lemma(enriched) is None:
                enriched.setdefault("lemma", slug)
            bindings.append(enriched)
    return bindings


def _practice_cards_from_deck(deck: dict[str, Any]) -> list[dict[str, Any]]:
    cards: list[dict[str, Any]] = []
    for key in _PRACTICE_CARD_LIST_KEYS:
        value = deck.get(key)
        if isinstance(value, list):
            cards.extend(item for item in value if isinstance(item, dict))
    return cards


def lint_practice_items(items: list[dict[str, Any]]) -> list[LintFinding]:
    """Return LINT-003 findings for lemma-bound practice items missing sense_id."""
    findings: list[LintFinding] = []
    for item in items:
        finding = _check_drill_sense_id_missing(item)
        if finding is not None:
            findings.append(finding)
    return findings


def lint_manifest(manifest: dict[str, Any]) -> list[LintFinding]:
    """Return LINT-001/002/003/004/101/102 findings for a manifest.

    Entries without a ``senses`` array are skipped for sense-level rules
    (LINT-001/002/004/101/102; see module docstring). LINT-003 reads explicit
    practice bindings even when senses are absent, so residual legacy decks
    stay visible during the advisory soak.
    """
    findings: list[LintFinding] = []
    for entry in _entries(manifest):
        slug = _entry_slug(entry)
        senses = _senses(entry)
        if senses:
            findings.extend(_check_multi_sense_uk_single_en(entry))
        for sense in senses:
            sense_id = _sense_id(sense)
            findings.extend(_check_truncated_text_cutoff(slug, sense_id, sense))
            findings.extend(_check_ambiguous_bare_en(slug, sense_id, sense))
            findings.extend(_check_unvetted_en_source(slug, sense_id, sense))
            findings.extend(_check_pos_transform_mismatch(entry, slug, sense_id, sense))
    findings.extend(lint_practice_items(_practice_bindings_from_manifest(manifest)))
    return findings


def _validate_counts(payload: object, source: Path | str) -> dict[str, int]:
    if not isinstance(payload, dict):
        raise ValueError(f"{source} must contain a JSON object")
    if payload.get("schema_version") != BASELINE_SCHEMA_VERSION:
        raise ValueError(f"{source} has unsupported schema_version")
    rules = payload.get("rules")
    if not isinstance(rules, dict) or set(rules) != set(IMPLEMENTED_RULE_IDS):
        raise ValueError(f"{source} must contain exactly one count for every implemented lint rule")
    counts: dict[str, int] = {}
    for rule_id in IMPLEMENTED_RULE_IDS:
        value = rules[rule_id]
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise ValueError(f"{source} has invalid count for {rule_id}")
        counts[rule_id] = value
    total = payload.get("total")
    if total != sum(counts.values()):
        raise ValueError(f"{source} total does not equal the sum of per-rule counts")
    return counts


def load_baseline(path: Path) -> dict[str, int]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read debt baseline {path}: {exc}") from exc
    return _validate_counts(payload, path)


def write_baseline(path: Path, counts: dict[str, int]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": BASELINE_SCHEMA_VERSION,
        "rules": {rule_id: counts[rule_id] for rule_id in IMPLEMENTED_RULE_IDS},
        "total": sum(counts.values()),
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def enforce_debt_baseline(
    current_counts: dict[str, int],
    path: Path,
    *,
    comparison_counts: dict[str, int] | None = None,
    update: bool = False,
) -> DebtBaselineResult:
    """Enforce a non-increasing baseline and optionally write reductions.

    ``comparison_counts`` is the base branch's committed baseline. It prevents
    a PR from lowering its own baseline file without actually lowering the
    measured debt. The current branch baseline must equal the measured counts
    after an update, so a debt reduction is reviewable as a small tracked diff.
    """
    errors: list[str] = []
    baseline_counts: dict[str, int] | None = None
    if path.exists():
        try:
            baseline_counts = load_baseline(path)
        except ValueError as exc:
            errors.append(str(exc))

    for label, reference in (
        ("base", comparison_counts),
        ("tracked", baseline_counts),
    ):
        if reference is None:
            continue
        increases = {
            rule_id: (reference[rule_id], current_counts[rule_id])
            for rule_id in IMPLEMENTED_RULE_IDS
            if current_counts[rule_id] > reference[rule_id]
        }
        if increases:
            formatted = ", ".join(f"{rule_id} {before}->{after}" for rule_id, (before, after) in increases.items())
            errors.append(f"debt baseline increased against {label} baseline: {formatted}")

    updated = False
    if not errors and baseline_counts != current_counts:
        if update:
            write_baseline(path, current_counts)
            baseline_counts = dict(current_counts)
            updated = True
        else:
            errors.append(
                "tracked debt baseline does not match measured counts; rerun with "
                f"--update-baseline to record a decrease: {path}"
            )

    return DebtBaselineResult(
        current_counts=dict(current_counts),
        baseline_counts=baseline_counts,
        comparison_counts=comparison_counts,
        errors=tuple(errors),
        updated=updated,
    )


def _load_json_object(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"::error::cannot read {path}: {exc}", file=sys.stderr)
        sys.exit(2)
    if not isinstance(data, dict):
        print(f"::error::{path} must contain a JSON object", file=sys.stderr)
        sys.exit(2)
    return data


def _load_manifest(path: Path) -> dict[str, Any]:
    return _load_json_object(path)


GIT_SCOPE_ENV_VARS = ("GIT_COMMON_DIR", "GIT_DIR", "GIT_INDEX_FILE", "GIT_PREFIX", "GIT_WORK_TREE")


def _git_show_json(ref: str, repository_path: str) -> dict[str, Any] | None:
    env = os.environ.copy()
    for name in GIT_SCOPE_ENV_VARS:
        env.pop(name, None)
    result = subprocess.run(
        ["git", "show", f"{ref}:{repository_path}"],
        cwd=PROJECT_ROOT,
        env=env,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        return None
    try:
        payload = json.loads(result.stdout.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"git show {ref}:{repository_path} is not valid JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"git show {ref}:{repository_path} must contain a JSON object")
    return payload


def _download_release_json(pointer: dict[str, Any], *, content_hash_key: str, label: str) -> dict[str, Any]:
    url = pointer.get("asset_url")
    if not isinstance(url, str) or not url.startswith("https://"):
        raise ValueError(f"{label} pointer has no valid HTTPS asset_url")
    request = Request(
        url,
        headers={
            "Accept": "application/gzip, application/octet-stream;q=0.9, */*;q=0.1",
            "Cache-Control": "no-cache",
            "User-Agent": "learn-ukrainian-atlas-sense-lint/1.0",
        },
    )
    try:
        with urlopen(request, timeout=120) as response:
            compressed = response.read()
    except OSError as exc:
        raise ValueError(f"failed to download {label} release asset: {exc}") from exc

    expected_gzip_hash = pointer.get("gz_sha256")
    actual_gzip_hash = hashlib.sha256(compressed).hexdigest()
    if expected_gzip_hash != actual_gzip_hash:
        raise ValueError(f"{label} gzip SHA-256 mismatch: expected {expected_gzip_hash}, got {actual_gzip_hash}")
    try:
        content = gzip.decompress(compressed)
    except OSError as exc:
        raise ValueError(f"{label} release asset is not valid gzip: {exc}") from exc

    expected_content_hash = pointer.get(content_hash_key)
    actual_content_hash = hashlib.sha256(content).hexdigest()
    if expected_content_hash != actual_content_hash:
        raise ValueError(
            f"{label} content SHA-256 mismatch: expected {expected_content_hash}, got {actual_content_hash}"
        )
    try:
        payload = json.loads(content.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"{label} release asset is not valid JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"{label} release asset must contain a JSON object")
    return payload


def _load_base_manifest_for_ref(base_ref: str, current_manifest: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    base_pointer = _git_show_json(base_ref, MANIFEST_POINTER_PATH)
    if base_pointer is None:
        raise ValueError(f"{base_ref} does not contain {MANIFEST_POINTER_PATH}")
    current_pointer = _load_json_object(PROJECT_ROOT / MANIFEST_POINTER_PATH)
    if base_pointer.get("json_sha256") == current_pointer.get("json_sha256"):
        return current_manifest, True
    return (
        _download_release_json(base_pointer, content_hash_key="json_sha256", label="Atlas manifest"),
        False,
    )


def _load_base_decks_for_ref(
    base_ref: str, current_decks: list[tuple[str, dict[str, Any]]]
) -> tuple[list[tuple[str, dict[str, Any]]], bool]:
    base_pointer = _git_show_json(base_ref, PRACTICE_DECK_POINTER_PATH)
    if base_pointer is None:
        raise ValueError(f"{base_ref} does not contain {PRACTICE_DECK_POINTER_PATH}")
    current_pointer = _load_json_object(PROJECT_ROOT / PRACTICE_DECK_POINTER_PATH)
    if base_pointer.get("package_sha256") == current_pointer.get("package_sha256"):
        return current_decks, True

    package = _download_release_json(
        base_pointer,
        content_hash_key="package_sha256",
        label="Atlas practice deck",
    )
    raw_files = package.get("files")
    if not isinstance(raw_files, list):
        raise ValueError("base Atlas practice deck package has no files list")
    base_decks: list[tuple[str, dict[str, Any]]] = []
    for raw_file in raw_files:
        if not isinstance(raw_file, dict):
            raise ValueError("base Atlas practice deck package contains a non-object file")
        name = raw_file.get("path")
        content = raw_file.get("content")
        if not isinstance(name, str) or not isinstance(content, str):
            raise ValueError("base Atlas practice deck package file has invalid path/content")
        try:
            deck = json.loads(content)
        except json.JSONDecodeError as exc:
            raise ValueError(f"base Atlas practice deck file {name} is not valid JSON: {exc}") from exc
        if not isinstance(deck, dict):
            raise ValueError(f"base Atlas practice deck file {name} must contain a JSON object")
        base_decks.append((name, deck))
    return base_decks, False


def print_report(findings: list[LintFinding]) -> None:
    if not findings:
        print("No LINT-001/LINT-002/LINT-003/LINT-004/LINT-101/LINT-102 findings — sense-first entries lint clean.")
        return

    rows = [
        (
            finding.rule_id,
            finding.rule_name,
            finding.entry_slug,
            finding.sense_id,
            finding.field,
            finding.detail,
        )
        for finding in findings
    ]
    headers = ("rule", "name", "entry", "sense_id", "field", "detail")
    widths = [max(len(headers[i]), max(len(str(row[i])) for row in rows)) for i in range(len(headers))]
    header_line = "  ".join(h.ljust(w) for h, w in zip(headers, widths, strict=True))
    print(header_line)
    print("-" * len(header_line))
    for row in rows:
        print("  ".join(str(cell).ljust(w) for cell, w in zip(row, widths, strict=True)))

    by_rule: dict[str, int] = {}
    for finding in findings:
        by_rule[finding.rule_id] = by_rule.get(finding.rule_id, 0) + 1
    summary = ", ".join(f"{rule}={count}" for rule, count in sorted(by_rule.items()))
    print()
    print(f"⚠️  {len(findings)} finding(s) ({summary}) — advisory, not blocking.")


def _format_finding(finding: LintFinding) -> str:
    return (
        f"{finding.rule_id} {finding.rule_name} {finding.entry_slug} "
        f"{finding.sense_id} {finding.field} — {finding.detail}"
    )


def _format_counts(counts: dict[str, int]) -> str:
    return ", ".join(f"{rule_id}={counts[rule_id]}" for rule_id in IMPLEMENTED_RULE_IDS)


def print_ratchet_report(
    findings: list[LintFinding],
    changed_entries: set[str],
    blocking_findings: list[LintFinding],
    debt: DebtBaselineResult,
) -> None:
    """Print compact CI evidence without flooding logs with legacy debt."""
    untouched = [finding for finding in findings if finding.entry_slug not in changed_entries]
    touched_advisory = [
        finding for finding in findings if finding.entry_slug in changed_entries and finding not in blocking_findings
    ]
    print("Word Atlas sense-lint ratchet (#6437)")
    print(f"New/changed entry scope: {len(changed_entries)}")
    if changed_entries and len(changed_entries) <= 12:
        print("Changed entries: " + ", ".join(sorted(changed_entries)))

    if blocking_findings:
        print(f"::error::Blocking touched-entry findings: {len(blocking_findings)}")
        for finding in blocking_findings[:20]:
            print(f"::error::{_format_finding(finding)}")
        if len(blocking_findings) > 20:
            print(f"::error::... {len(blocking_findings) - 20} more blocking finding(s)")
    else:
        print("Blocking touched-entry findings: 0")

    print(f"Advisory pre-existing/untouched findings: {len(untouched)}")
    for finding in untouched[:3]:
        print(f"[advisory pre-existing] {_format_finding(finding)}")
    if len(untouched) > 3:
        print(f"[advisory pre-existing] ... {len(untouched) - 3} more finding(s)")

    if touched_advisory:
        print(f"Advisory findings on changed entries (non-ratcheted rules): {len(touched_advisory)}")
        for finding in touched_advisory[:3]:
            print(f"[advisory changed/non-ratcheted] {_format_finding(finding)}")

    baseline_label = "missing" if debt.baseline_counts is None else _format_counts(debt.baseline_counts)
    print(f"Debt baseline: current {_format_counts(debt.current_counts)}")
    print(f"Debt baseline tracked: {baseline_label}")
    if debt.comparison_counts is not None:
        print(f"Debt baseline base: {_format_counts(debt.comparison_counts)}")
    if debt.updated:
        print("Debt baseline updated because measured debt decreased.")
    if debt.errors:
        for error in debt.errors:
            print(f"::error::{error}")
    else:
        print("Debt baseline gate: PASS (non-increasing)")


def write_report(
    findings: list[LintFinding],
    path: Path,
    *,
    changed_entries: set[str] | None = None,
    blocking_findings: list[LintFinding] | None = None,
    debt: DebtBaselineResult | None = None,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "rule_ids": list(IMPLEMENTED_RULE_IDS),
        "finding_count": len(findings),
        "findings": [asdict(finding) for finding in findings],
    }
    if changed_entries is not None:
        payload["changed_entry_count"] = len(changed_entries)
        payload["changed_entries"] = sorted(changed_entries)
    if blocking_findings is not None:
        payload["blocking_finding_count"] = len(blocking_findings)
        payload["blocking_findings"] = [asdict(finding) for finding in blocking_findings]
    if debt is not None:
        payload["debt_counts"] = debt.current_counts
        payload["debt_baseline_counts"] = debt.baseline_counts
        payload["debt_base_counts"] = debt.comparison_counts
        payload["debt_baseline_errors"] = list(debt.errors)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Advisory sense-first Word Atlas lint: LINT-001 TRUNCATED_TEXT_CUTOFF + "
            "LINT-002 AMBIGUOUS_BARE_EN + LINT-003 DRILL_SENSE_ID_MISSING + "
            "LINT-004 UNVETTED_EN_SOURCE + LINT-101 MULTI_SENSE_UK_SINGLE_EN + "
            "LINT-102 POS_TRANSFORM_MISMATCH (issue #6437)."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=DEFAULT_FIXTURE,
        help=f"Manifest JSON path with a top-level 'entries' list. Default: {DEFAULT_FIXTURE}.",
    )
    parser.add_argument(
        "--practice-deck",
        type=Path,
        action="append",
        default=None,
        help=(
            "Optional practice deck shard JSON to scan for LINT-003 "
            "(repeatable). Cards with lemmaId/lemma but no senseId are flagged."
        ),
    )
    parser.add_argument(
        "--practice-deck-dir",
        type=Path,
        action="append",
        default=None,
        help="Scan every JSON shard in this hydrated practice-deck directory (repeatable).",
    )
    parser.add_argument(
        "--base-manifest",
        type=Path,
        default=None,
        help="Explicit base manifest for --ratchet; use instead of --base-ref for fixtures.",
    )
    parser.add_argument(
        "--base-practice-deck",
        type=Path,
        action="append",
        default=None,
        help="Explicit base practice-deck shard for --ratchet (repeatable).",
    )
    parser.add_argument(
        "--base-ref",
        default=None,
        help=(
            "Git ref for the review base. The release pointers are compared and, when they "
            "differ, the base manifest/deck assets are hash-verified and hydrated."
        ),
    )
    parser.add_argument(
        "--baseline",
        type=Path,
        default=DEFAULT_BASELINE,
        help=f"Tracked per-rule debt baseline JSON. Default: {DEFAULT_BASELINE}.",
    )
    parser.add_argument(
        "--ratchet",
        action="store_true",
        help=(
            "Block LINT-003/004/101/102 only for new or changed entries; keep untouched "
            "findings advisory and enforce the non-increasing debt baseline."
        ),
    )
    parser.add_argument(
        "--update-baseline",
        action="store_true",
        help="Write the tracked baseline when measured debt is lower and otherwise fail closed.",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=None,
        help=(
            "Write findings as JSON to this path (residual report mode). Must resolve "
            "under a gitignored location such as batch_state/ — this script does not "
            "enforce that, but committing lint residuals is a policy violation."
        ),
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit 1 when any finding exists. Default is advisory unless --ratchet is used.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.ratchet and not (args.base_manifest or args.base_ref):
        parser.error("--ratchet requires --base-manifest or --base-ref")
    if args.base_manifest and args.base_ref:
        parser.error("--base-manifest and --base-ref are mutually exclusive")
    if args.update_baseline and not args.ratchet:
        parser.error("--update-baseline is only valid with --ratchet")
    if (args.base_manifest or args.base_practice_deck) and not args.ratchet:
        parser.error("base inputs are only valid with --ratchet")

    manifest_path = args.manifest
    if not manifest_path.is_absolute():
        manifest_path = PROJECT_ROOT / manifest_path
    if not manifest_path.exists() or not manifest_path.is_file():
        parser.error(f"manifest does not exist or is not a file: {manifest_path}")

    manifest = _load_manifest(manifest_path)
    findings = lint_manifest(manifest)

    deck_paths = list(args.practice_deck or [])
    for deck_dir_arg in args.practice_deck_dir or []:
        deck_dir = deck_dir_arg if deck_dir_arg.is_absolute() else PROJECT_ROOT / deck_dir_arg
        if not deck_dir.exists() or not deck_dir.is_dir():
            parser.error(f"practice deck directory does not exist or is not a directory: {deck_dir}")
        deck_paths.extend(sorted(deck_dir.glob("*.json")))
    if args.practice_deck_dir and not deck_paths:
        parser.error("practice deck directory contains no JSON shards")

    current_decks: list[tuple[str, dict[str, Any]]] = []
    for deck_arg in deck_paths:
        deck_path = deck_arg if deck_arg.is_absolute() else PROJECT_ROOT / deck_arg
        if not deck_path.exists() or not deck_path.is_file():
            parser.error(f"practice deck does not exist or is not a file: {deck_path}")
        deck = _load_json_object(deck_path)
        current_decks.append((deck_path.name, deck))
        findings.extend(lint_practice_items(_practice_cards_from_deck(deck)))

    changed_entries: set[str] | None = None
    blocking_findings: list[LintFinding] | None = None
    debt: DebtBaselineResult | None = None
    if args.ratchet:
        try:
            manifest_base_is_current = False
            if args.base_manifest:
                base_manifest_path = args.base_manifest
                if not base_manifest_path.is_absolute():
                    base_manifest_path = PROJECT_ROOT / base_manifest_path
                if not base_manifest_path.exists() or not base_manifest_path.is_file():
                    parser.error(f"base manifest does not exist or is not a file: {base_manifest_path}")
                base_manifest = _load_manifest(base_manifest_path)
            else:
                base_manifest, manifest_base_is_current = _load_base_manifest_for_ref(args.base_ref, manifest)

            changed_entries = set() if manifest_base_is_current else changed_entry_keys(base_manifest, manifest)

            if current_decks:
                deck_base_is_current = False
                if args.base_practice_deck:
                    base_decks: list[tuple[str, dict[str, Any]]] = []
                    for base_deck_arg in args.base_practice_deck:
                        base_deck_path = base_deck_arg if base_deck_arg.is_absolute() else PROJECT_ROOT / base_deck_arg
                        if not base_deck_path.exists() or not base_deck_path.is_file():
                            parser.error(f"base practice deck does not exist or is not a file: {base_deck_path}")
                        base_decks.append((base_deck_path.name, _load_json_object(base_deck_path)))
                elif args.base_ref:
                    base_decks, deck_base_is_current = _load_base_decks_for_ref(args.base_ref, current_decks)
                else:
                    base_decks = []
                if not deck_base_is_current and base_decks:
                    changed_entries.update(changed_practice_entry_keys(base_decks, current_decks))

            baseline_path = args.baseline
            if not baseline_path.is_absolute():
                baseline_path = PROJECT_ROOT / baseline_path
            comparison_counts = None
            if args.base_ref:
                baseline_relative = baseline_path.resolve().relative_to(PROJECT_ROOT.resolve())
                base_baseline_payload = _git_show_json(args.base_ref, baseline_relative.as_posix())
                if base_baseline_payload is not None:
                    comparison_counts = _validate_counts(
                        base_baseline_payload,
                        f"git show {args.base_ref}:{baseline_relative.as_posix()}",
                    )
            debt = enforce_debt_baseline(
                finding_counts(findings),
                baseline_path,
                comparison_counts=comparison_counts,
                update=args.update_baseline,
            )
            blocking_findings = ratchet_blocking_findings(findings, changed_entries)
        except ValueError as exc:
            parser.error(str(exc))

    if args.ratchet:
        assert changed_entries is not None
        assert blocking_findings is not None
        assert debt is not None
        print_ratchet_report(findings, changed_entries, blocking_findings, debt)
    else:
        print_report(findings)

    if args.report:
        report_path = args.report if args.report.is_absolute() else PROJECT_ROOT / args.report
        write_report(
            findings,
            report_path,
            changed_entries=changed_entries,
            blocking_findings=blocking_findings,
            debt=debt,
        )
        print(f"Residual report written to {report_path}")

    if args.strict and findings:
        return 1
    if args.ratchet and (blocking_findings or (debt is not None and not debt.passed)):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
