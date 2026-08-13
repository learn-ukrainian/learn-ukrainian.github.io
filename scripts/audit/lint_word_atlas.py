#!/usr/bin/env python3
"""Sense-first Word Atlas entry lint (#6437): LINT-001 … LINT-004 + LINT-101/102.

Read-only, advisory lint over the `senses[]` array and practice bindings
documented in ``docs/runbooks/word-atlas-entry-model.md`` (§ Sense-Level
Fields, #6437 delta). It never mutates a manifest — it only reports.

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
- stdout: table of findings (rule, entry, sense, field, detail).
- exit 0 always, unless ``--strict`` is passed and findings exist (exit 1).
  No CI gate consumes this yet (advisory only — issue #6437 D6-7 sets the
  residual policy before any blocking wiring).

Related
=======
- Issue #6437 — sense-first lintable entry gate.
- Schema: docs/runbooks/word-atlas-entry-model.md § Sense-Level Fields.
- Sibling guardrails: scripts/audit/check_atlas_manifest_enrichment.py.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Reuse enrich honesty vocabulary — do not invent a parallel source set (#6437).
from scripts.lexicon.enrich_manifest import (
    SENSE_SOURCE_AI_MINIMUM,
    SENSE_SOURCE_SOURCED,
)

DEFAULT_FIXTURE = PROJECT_ROOT / "tests" / "fixtures" / "atlas" / "sense_lint_sample.json"

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


def _check_truncated_text_cutoff(
    entry_slug: str, sense_id: str, sense: dict[str, Any]
) -> list[LintFinding]:
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


def _check_ambiguous_bare_en(
    entry_slug: str, sense_id: str, sense: dict[str, Any]
) -> list[LintFinding]:
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
            detail=(
                f"bare single-word EN {word!r} is a high-risk polysemy target "
                "with no en_disambiguation"
            ),
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


def _check_unvetted_en_source(
    entry_slug: str, sense_id: str, sense: dict[str, Any]
) -> list[LintFinding]:
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

    senses_with_en = [
        (sense, key)
        for sense in senses
        if (key := _learner_en_key(sense)) is not None
    ]

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
                    f"entry has {len(senses)} senses but only 1 publishes "
                    "learner_en; remaining senses lack EN coverage"
                ),
            )
        )
    elif len(senses_with_en) >= 2:
        keys = {key for _sense, key in senses_with_en}
        if len(keys) == 1:
            missing_disambiguation = [
                sense
                for sense, _key in senses_with_en
                if not _has_nonempty_disambiguation(sense)
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
        detail=(
            f"practice binding for lemma {lemma!r} has no senseId/sense_id "
            "(en[0] fallback is not allowed)"
        ),
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


def print_report(findings: list[LintFinding]) -> None:
    if not findings:
        print(
            "No LINT-001/LINT-002/LINT-003/LINT-004/LINT-101/LINT-102 findings — "
            "sense-first entries lint clean."
        )
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
    widths = [
        max(len(headers[i]), max(len(str(row[i])) for row in rows)) for i in range(len(headers))
    ]
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


def write_report(findings: list[LintFinding], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "rule_ids": list(IMPLEMENTED_RULE_IDS),
        "finding_count": len(findings),
        "findings": [asdict(finding) for finding in findings],
    }
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
        help="Exit 1 when findings exist. Default is advisory (always exit 0).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    manifest_path = args.manifest
    if not manifest_path.is_absolute():
        manifest_path = PROJECT_ROOT / manifest_path
    if not manifest_path.exists() or not manifest_path.is_file():
        parser.error(f"manifest does not exist or is not a file: {manifest_path}")

    manifest = _load_manifest(manifest_path)
    findings = lint_manifest(manifest)

    for deck_arg in args.practice_deck or []:
        deck_path = deck_arg if deck_arg.is_absolute() else PROJECT_ROOT / deck_arg
        if not deck_path.exists() or not deck_path.is_file():
            parser.error(f"practice deck does not exist or is not a file: {deck_path}")
        deck = _load_json_object(deck_path)
        findings.extend(lint_practice_items(_practice_cards_from_deck(deck)))

    print_report(findings)

    if args.report:
        report_path = args.report if args.report.is_absolute() else PROJECT_ROOT / args.report
        write_report(findings, report_path)
        print(f"Residual report written to {report_path}")

    return 1 if (args.strict and findings) else 0


if __name__ == "__main__":
    sys.exit(main())
