#!/usr/bin/env python3
"""Deterministic local heritage-status classifier for Word Atlas and gates.

The classifier is deliberately source-backed and offline-only. VESUM proves
modern standard status; heritage dictionaries and verified corpus quotes prove
authentic non-VESUM status; Russian-shadow morphology is recorded as a warning
signal but never decides by itself.
"""

from __future__ import annotations

import hashlib
import html
import json
import os
import re
import sqlite3
import sys
import threading
from collections.abc import Iterator
from contextlib import contextmanager, suppress
from functools import lru_cache
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

SOURCES_DB = ROOT / "data" / "sources.db"
LT_REPLACEMENTS = ROOT / "registry" / "lt_replacements.json"
HERITAGE_PAIRS_YAML = ROOT / "registry" / "lexicon" / "heritage_pairs.yaml"

_CYRILLIC_WORD_CHARS = "A-Za-zА-Яа-яЄєІіЇїҐґ0-9'’ʼ-"
_ACUTE_RE = re.compile("[\u0301\u0300]")
_SPACE_RE = re.compile(r"\s+")

_AUTHENTIC_CLASSIFICATIONS = {
    "authentic-archaism",
    "dialect",
    "historism",
    "borrowing",
    "standard",
}
_TREASURED_CLASSIFICATIONS = {
    "authentic-archaism",
    "dialect",
    "historism",
    "borrowing",
}
_POSITIVE_ATTESTATION_PREFIXES = ("grinchenko", "literary")
_POSITIVE_ATTESTATION_SOURCES = {"vesum", "esum", "гринченко", "есум"}

_KNOWN_STANDARD_ALTERNATIVES: dict[str, tuple[str, ...]] = {
    "аранжировка": ("аранжування",),
    "діюча": ("чинна",),
    "діючий": ("чинний", "дійовий"),
    "діючі": ("чинні",),
    "протиріччя": ("суперечність",),
}

_SURFACE_QUOTE_HINTS: dict[str, tuple[str, str]] = {
    # Spec evidence case: exact Kupala quotation in ЕУ-1955 literary_texts.
    "другоє": ("на другоє літо поховаємо", "authentic-archaism"),
}

_DIALECT_OR_FOLK_TERMS = {
    "гагілка",
    "гагілки",
    "гаївка",
    "гаївки",
    "риндзівка",
    "риндзівки",
    "ягівка",
    "ягівки",
    "ягілка",
    "ягілки",
}

_SLOVNYK_HERITAGE_SLUGS = {
    "newsum",
    "vts",
    "holoskevych",
    "obsolete_words",
    "bukovina",
    "franko",
    "slang_lviv",
    "slang",
    "slang_modern",
}

_ARCHAIC_MARKERS = (
    "заст.",
    "застар",
    "архаї",
    "ц.-с.",
    "церк.-слов",
    "церковнослов",
)
_DIALECT_MARKERS = (
    "діал.",
    " діал ",
    "діалект",
    "зах.",
    " зах ",
    "говір",
    "гуц",
    "бойк",
    "лемк",
    "буковин",
    "львів",
)
_HISTORISM_MARKERS = (
    "іст.",
    "істор.",
    "(іст.)",
    "у xvi",
    "у xvii",
    "у xviii",
    "у xix",
    "в xvi",
    "в xvii",
    "в xviii",
    "в xix",
    "до 1764",
    "епоху феодалізму",
    "феодально",
    "козацького війська",
    "запорізької січі",
    "запорозької січі",
    "стара російська одиниця",
    "десята частина доходів",
)
_BORROWING_MARKERS = (
    "запозич",
    "з польської",
    "з німецької",
    "з французької",
    "з латинської",
)


def classify_lemma(
    lemma: str,
    db_path: str | Path | None = None,
    vesum_db_path: str | Path | None = None,
) -> dict[str, Any]:
    """Classify a lemma for Word Atlas ``heritage_status`` badges."""
    variants = _lemma_variants(lemma)
    if len(variants) <= 1:
        return _classify(
            variants[0] if variants else "",
            surface=False,
            db_path=db_path,
            vesum_db_path=vesum_db_path,
        )
    return _merge_variant_statuses(
        [
            _classify(
                variant,
                surface=False,
                db_path=db_path,
                vesum_db_path=vesum_db_path,
            )
            for variant in variants
        ],
        headword=lemma,
    )


def classify_surface_form(
    form: str,
    db_path: str | Path | None = None,
    vesum_db_path: str | Path | None = None,
) -> dict[str, Any]:
    """Classify an inflected/surface form for VESUM-gate importers."""
    term = _normalize_word(form)
    return _classify(term, surface=True, db_path=db_path, vesum_db_path=vesum_db_path)


def _classify(
    term: str,
    *,
    surface: bool,
    db_path: str | Path | None = None,
    vesum_db_path: str | Path | None = None,
) -> dict[str, Any]:
    if not term:
        return _status(
            "unknown",
            [],
            is_russianism=False,
            russian_shadow=False,
            vesum_attested=False,
        )

    russian_shadow, russian_shadow_detail = _check_russian_shadow(
        term,
        vesum_db_path=vesum_db_path,
    )
    sovietization_risk = _sum11_sovietization_risk_for_term(term, db_path=db_path)

    vesum = _vesum_attestation(term, surface=surface, vesum_db_path=vesum_db_path)
    vesum_archaism = _vesum_archaism_attestation(
        term,
        surface=surface,
        vesum_db_path=vesum_db_path,
    )
    has_modern_vesum = bool(vesum) and not (vesum_archaism and not vesum_archaism["has_modern"])

    curated_calque = _lookup_curated_calque(
        term,
        lemmas=_extract_vesum_lemmas(vesum) if vesum else None,
    )
    built_calque_warning: dict[str, Any] | None = None
    if curated_calque:
        built_calque_warning = {
            "standard_alternatives": list(curated_calque.get("corrections") or []),
            "kind": curated_calque.get("kind", "lexical"),
        }
        if curated_calque.get("rationale") or curated_calque.get("note"):
            built_calque_warning["note"] = curated_calque.get("rationale") or curated_calque.get("note")
        if curated_calque.get("rationaleUk") or curated_calque.get("noteUk"):
            built_calque_warning["noteUk"] = curated_calque.get("rationaleUk") or curated_calque.get("noteUk")
        if curated_calque.get("calqueSense") or curated_calque.get("calque_sense"):
            built_calque_warning["calque_sense"] = curated_calque.get("calqueSense") or curated_calque.get(
                "calque_sense"
            )
        if curated_calque.get("authenticSense") or curated_calque.get("authentic_sense"):
            built_calque_warning["authentic_sense"] = curated_calque.get("authenticSense") or curated_calque.get(
                "authentic_sense"
            )
        if curated_calque.get("citations"):
            built_calque_warning["citations"] = list(curated_calque["citations"])
        # #9603: the source proof that may bind the claim to this headword.
        if curated_calque.get("evidence"):
            built_calque_warning["evidence"] = list(curated_calque["evidence"])
        if curated_calque.get("judgments"):
            built_calque_warning["judgments"] = list(curated_calque["judgments"])

    russianism = (
        None
        if curated_calque
        else _russianism_status(
            term,
            russian_shadow=russian_shadow,
            vesum_attested=bool(vesum),
        )
    )

    attestations: list[dict[str, Any]] = []
    classification = "unknown"
    with _source_conn(db_path) as conn:
        auth_hits = _strict_heritage_attestations(conn, term, surface=surface)
        has_standard_hit = any(hit["classification"] == "standard" for hit in auth_hits)
        for hit in auth_hits:
            candidate = str(hit["classification"])
            if candidate == "standard" and vesum_archaism and not vesum_archaism["has_modern"]:
                candidate = "authentic-archaism"
            if candidate == "standard":
                continue
            if (
                candidate == "authentic-archaism"
                and hit.get("weak_when_modern")
                and (has_modern_vesum or has_standard_hit or russianism)
            ):
                continue
            if (
                candidate == "dialect"
                and hit.get("weak_when_modern")
                and (has_modern_vesum or has_standard_hit or russianism)
            ):
                continue
            if has_modern_vesum and candidate == "borrowing":
                continue
            attestations.append(hit["attestation"])
            classification = _prefer_classification(classification, candidate)
            sovietization_risk = max(sovietization_risk, int(hit.get("sovietization_risk") or 0))

        if surface and not attestations and russianism and term in _KNOWN_STANDARD_ALTERNATIVES:
            return russianism

        if not attestations and not vesum:
            for hit in _standard_dictionary_attestations(conn, term):
                attestations.append(hit["attestation"])
                classification = _prefer_classification(classification, "standard")
                sovietization_risk = max(sovietization_risk, int(hit.get("sovietization_risk") or 0))

    if surface and russianism and term in _KNOWN_STANDARD_ALTERNATIVES:
        return russianism

    if attestations and classification in _AUTHENTIC_CLASSIFICATIONS:
        if (
            curated_calque
            and curated_calque.get("kind") not in ("sense_restricted",)
            and classification not in ("authentic-archaism", "dialect", "historism")
        ):
            classification = "calque"
        return _status(
            classification,
            attestations,
            is_russianism=False,
            russian_shadow=russian_shadow,
            vesum_attested=bool(vesum),
            sovietization_risk=sovietization_risk,
            calque_warning=built_calque_warning,
            headword=term,
        )

    if russianism:
        return russianism

    if vesum:
        target_classification = "standard"
        if curated_calque:
            target_classification = "standard" if curated_calque.get("kind") == "sense_restricted" else "calque"
        return _status(
            target_classification,
            [vesum],
            is_russianism=False,
            russian_shadow=russian_shadow,
            vesum_attested=True,
            sovietization_risk=sovietization_risk,
            calque_warning=built_calque_warning,
            headword=term,
        )

    calque_warning = built_calque_warning or _calque_warning(term, russian_shadow_detail)
    target_class = "calque" if (curated_calque and curated_calque.get("kind") != "sense_restricted") else "unknown"
    return _status(
        target_class,
        [],
        is_russianism=False,
        russian_shadow=russian_shadow,
        vesum_attested=False,
        calque_warning=calque_warning,
        headword=term,
    )


def _status(
    classification: str,
    attestations: list[dict[str, Any]],
    *,
    is_russianism: bool,
    russian_shadow: bool,
    vesum_attested: bool = False,
    sovietization_risk: int = 0,
    calque_warning: dict[str, Any] | None = None,
    headword: str | None = None,
) -> dict[str, Any]:
    status = {
        "classification": classification,
        "attestations": _dedupe_attestations(attestations),
        "is_russianism": is_russianism,
        "russian_shadow": russian_shadow,
        "vesum_attested": vesum_attested,
        "sovietization_risk": sovietization_risk,
        "calque_warning": calque_warning,
    }
    status["warning_severity"] = compute_warning_severity(
        status,
        vesum_attested=vesum_attested,
        max_sovietization_risk=sovietization_risk,
        headword=headword,
    )
    return status


def has_positive_attestation(heritage_status: dict[str, Any]) -> bool:
    """Return True for source-backed positive lexical attestation only."""
    for attestation in heritage_status.get("attestations") or []:
        if not isinstance(attestation, dict):
            continue
        source = str(attestation.get("source") or "").strip().casefold()
        if not source:
            continue
        if source in _POSITIVE_ATTESTATION_SOURCES:
            return True
        if any(source.startswith(prefix) for prefix in _POSITIVE_ATTESTATION_PREFIXES):
            return True
    return False


def _has_calque_alternative(heritage_status: dict[str, Any]) -> bool:
    curated = heritage_status.get("curated_calque")
    if isinstance(curated, dict) and curated.get("corrections"):
        return True

    calque_warning = heritage_status.get("calque_warning")
    if isinstance(calque_warning, dict) and calque_warning.get("standard_alternatives"):
        return True

    section_six = heritage_status.get("§6_note")
    return isinstance(section_six, dict) and bool(section_six.get("corrections"))


def _has_reverse_calque(heritage_status: dict[str, Any]) -> bool:
    """A word that is the recommended replacement for a calque (§6 reverse note)."""
    reverse = heritage_status.get("reverse_calques")
    return isinstance(reverse, list) and bool(reverse)


# ---------------------------------------------------------------------------
# Usage-label scope (#9603). Contract: docs/atlas/usage-label-scope.md.
#
# A public Word Atlas label («русизм», «калька», «архаїзм», «діалектизм»,
# «історизм», «запозичення») describes the whole headword only with source
# proof of that scope. A Russianism or calque needs a reviewed directional
# judgment whose rejected form is the headword, bound by digest to a passage
# from a normative source; a register label needs a dictionary marker in the
# headword slot of the same headword. Sense, phrase and reverse (replacement)
# guidance stays contextual; anything else is unresolved, never a lexical
# condemnation. ``site/src/lib/lexicon/heritage-severity.ts`` mirrors this.
# ---------------------------------------------------------------------------

USAGE_LABEL_CODES = {
    "russianism": "rus",
    "calque": "calq",
    "authentic-archaism": "arch",
    "archaism": "arch",
    "dialect": "dial",
    "historism": "hist",
    "borrowing": "borr",
}
_CONTEXTUAL_CALQUE_SCOPES = {"sense_restricted": "sense", "phrasal": "phrase"}
# An unresolved Russianism/calque claim is neutral: neither a warning nor a
# heritage defence (#7982: no green badge for convergence calques).
UNRESOLVED_CLAIM_REASONS = frozenset(
    {"no_lemma_scoped_authority", "no_headword_bound_evidence", "curated_kind_without_scope"}
)
# The only curated kind that claims the whole word. ``participle`` names a
# word-formation type, not a scope (the діючий record is sense-split), and any
# other or missing kind states no scope at all.
_LEMMA_CALQUE_KINDS = {"lexical"}
# Normative Russianism/calque authorities (rules P5), cited by sources.db chunk
# id: Антоненко-Давидович «Як ми говоримо» pages, Караванський, Волощак and
# named school textbooks.
_NORMATIVE_SOURCE_FAMILIES = ("antonenko", "karavansk", "voloshchak", "voloschak")
_NORMATIVE_TEXTBOOK_AUTHORS = {"avramenko", "zabolotnyi", "glazova", "litvinova", "voron"}
_CHUNK_LOCATOR_RE = re.compile(r"^[0-9a-z]+(?:-[0-9a-z]+)*_[ps]\d{3,4}$")
_WORD_RE = re.compile(r"[а-яіїєґʼ'a-z]+(?:-[а-яіїєґʼ'a-z]+)*")
_LETTER_CLASS = "а-яіїєґa-z"
_USAGE_MARKER_RES = {
    "historism": re.compile(rf"(?<![{_LETTER_CLASS}])(?:іст|істор)\."),
    "dialect": re.compile(rf"(?<![{_LETTER_CLASS}])діал\."),
    "authentic-archaism": re.compile(rf"(?<![{_LETTER_CLASS}])(?:заст\.|застар|архаї)"),
}
_MODERN_DICTIONARY_CARDS = (("sum20", "СУМ-20"), ("vts", "ВТС"))
_SUPERSCRIPT_DIGITS = "¹²³⁴⁵⁶⁷⁸⁹⁰"
_HOMONYM_INDEX_RE = re.compile(rf"^(?:[{_SUPERSCRIPT_DIGITS}]+|I|II|III|IV|V)[,.]?$")
_SENSE_START_RE = re.compile(r"^(?:\d|[《◊/]|[А-ЯІЇЄҐA-Z])")
_SECOND_SENSE_RE = re.compile(r"(?<!\S)2[.)]")
_EDGE_PUNCT = ",.;:!?«»\"'()[]"
# An ЕСУМ headword slot: the word, its marker, then a «gloss» or a
# parenthesised explanation (``тіун (іст.) (назва ряду службових осіб …)``).
_ESUM_HEADWORD_SLOT_RE = re.compile(
    r"^\s*(?P<word>[^\s(«]+)\s*\((?P<marker>[^)]{1,40})\)\s*"
    r"(?:«(?P<gloss>[^»]{1,200})»|\((?P<explanation>[^()]{1,300})\))"
)
_ESUM_REF_RE = re.compile(r"^[^:]*:(?P<volume>\d+):(?P<page>\d+)$")
# Referent comparison ignores short function words.
_MIN_REFERENT_TOKEN_LEN = 5
# ``passageSha256`` normalisation, as ``_normalize_source_text`` in
# scripts/audit/generate_practice_deck.py (docs/practice/heritage-pairs-growth.md).
_SOURCE_TEXT_TRANSLATION = str.maketrans(
    {"–": "-", "—": "-", "‑": "-", "«": '"', "»": '"', "“": '"', "”": '"', "„": '"', "’": "'", "ʼ": "'"}
)


def _citation_list(value: object) -> list[str]:
    if isinstance(value, str):
        return [value] if value.strip() else []
    if isinstance(value, list):
        return [str(item) for item in value if str(item or "").strip()]
    return []


def is_normative_locator(locator: str) -> bool:
    """True when ``locator`` is a sources.db chunk of a normative style guide or textbook.

    ``antonenko-davydovych-yak-my-hovorymo_p031`` and
    ``9-klas-ukrajinska-mova-avramenko-2017_s0159`` qualify. An attribution
    (``Антоненко-Давидович``), an author-grade citation (``voron-9``) or any
    other source names no passage and does not.
    """
    text = str(locator or "").strip().casefold()
    if not _CHUNK_LOCATOR_RE.match(text):
        return False
    parts = re.split(r"[-_]", text)
    if any(part.startswith(_NORMATIVE_SOURCE_FAMILIES) for part in parts):
        return True
    return "klas" in parts and any(part in _NORMATIVE_TEXTBOOK_AUTHORS for part in parts)


def _words(text: str) -> list[str]:
    return _WORD_RE.findall(_normalize_word(text).replace("ʼ", "'"))


def source_text_digest(text: str) -> str:
    """SHA-256 of a source passage, normalised as for a heritage pair's ``passageSha256``."""
    text = re.sub(r"(?<=[а-яіїєґ'’ʼ])[-­]\s*\n\s*(?=[а-яіїєґ])", "", str(text).replace("́", ""))
    normalized = _SPACE_RE.sub(" ", text.translate(_SOURCE_TEXT_TRANSLATION)).strip().casefold()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def reviewed_judgments(pair: dict[str, Any]) -> list[dict[str, str]]:
    """A heritage pair's reviewed directional judgments, each bound to its passage.

    A frame's ``normativeJudgment`` names the rejected and endorsed forms and
    the sense; ``passageSha256`` (and ``currentNormPassageSha256``) lock it to
    the exact ``normativeSupport`` (``currentNormSupport``) passage the curator
    reviewed. A judgment matching no stored passage is dropped: form
    occurrence alone never states a correction's direction.
    """
    passages = [
        item
        for key in ("normativeSupport", "currentNormSupport")
        for item in pair.get(key) or []
        if isinstance(item, dict)
    ]
    judgments: list[dict[str, str]] = []
    for frame in pair.get("frames") or []:
        judgment = frame.get("normativeJudgment") if isinstance(frame, dict) else None
        if not isinstance(judgment, dict):
            continue
        direction = {name: str(judgment.get(name) or "").strip() for name in ("rejectedForm", "endorsedForm", "sense")}
        if not all(direction.values()):
            continue
        for locator_key, digest_key in (
            ("locator", "passageSha256"),
            ("currentNormLocator", "currentNormPassageSha256"),
        ):
            for item in passages:
                passage = str(item.get("passage") or "")
                if (
                    passage
                    and item.get("locator") == judgment.get(locator_key)
                    and source_text_digest(passage) == judgment.get(digest_key)
                ):
                    bound = {"locator": str(item["locator"]), "passage": passage, "passageSha256": judgment[digest_key]}
                    if {**bound, **direction} not in judgments:
                        judgments.append({**bound, **direction})
    return judgments


def _evidence_items(record: dict[str, Any]) -> list[tuple[str, str]]:
    """``(locator, excerpt)`` pairs of a curated record's ``locator: excerpt`` evidence."""
    items: list[tuple[str, str]] = []
    for item in _citation_list(record.get("evidence")):
        locator, separator, excerpt = item.partition(":")
        if separator:
            items.append((locator.strip(), excerpt.strip()))
    return items


def _source_checked_chunks() -> dict[str, tuple[str, str, tuple[str, ...], str]]:
    try:
        from scripts.lexicon.calque_corrections import SOURCE_CHECKED_CHUNKS
    except ImportError:  # loaded as a file: only scripts/ is on sys.path
        from lexicon.calque_corrections import SOURCE_CHECKED_CHUNKS  # type: ignore[no-redef]
    return SOURCE_CHECKED_CHUNKS


def admitted_source_proof(record: object, headword: str | None) -> dict[str, Any] | None:
    """The source proof a curated record carries for ``headword``, or ``None``.

    ``judgments`` are reviewed judgments (:func:`reviewed_judgments`) whose
    rejected form is the headword, from a normative chunk, with the passage
    still matching its digest; only they establish a whole-word Russianism or
    calque. ``citations`` cite a sense- or phrase-restricted caution: curated
    ``locator: excerpt`` evidence whose chunk a reviewer checked in sources.db
    and bound to one correction (``SOURCE_CHECKED_CHUNKS``). The excerpt must
    be that reviewed passage (by digest), and the binding's scope, rejected
    form (the headword) and an endorsed form among the record's corrections
    must match; corrections keep their source context (``активний (вулкан)``). A
    locator, a source name or co-occurring words admit nothing (Atlas reference).
    """
    head = _normalize_word(headword or "")
    if not head or not isinstance(record, dict):
        return None
    kind = str(record.get("kind") or "").strip()
    judgments = [
        dict(item)
        for item in record.get("judgments") or []
        if isinstance(item, dict)
        and _normalize_word(str(item.get("rejectedForm") or "")) == head
        and is_normative_locator(str(item.get("locator") or ""))
        and source_text_digest(str(item.get("passage") or "")) == item.get("passageSha256")
    ]
    corrections = [str(item) for item in record.get("corrections") or [] if str(item or "").strip()]
    pooled = len({item["sense"] for item in judgments}) > 1
    citations, endorsed = [], [item["endorsedForm"] + (f" ({item['sense']})" if pooled else "") for item in judgments]
    for locator, excerpt in _evidence_items(record):
        scope, rejected, forms, digest = _source_checked_chunks().get(locator, ("", "", (), ""))
        supported = [form for form in forms if form.partition(" (")[0] in corrections]
        if (
            scope == _CONTEXTUAL_CALQUE_SCOPES.get(kind)
            and _normalize_word(rejected) == head
            and supported
            and source_text_digest(excerpt) == digest
        ):
            citations.append({"locator": locator, "excerpt": excerpt})
            endorsed += supported
    if not judgments and not citations:
        return None
    return {
        "kind": kind,
        "corrections": list(dict.fromkeys(endorsed)),
        "sense": judgments[0]["sense"]
        if judgments
        else str(record.get("calque_sense") or record.get("calqueSense") or ""),
        "judgments": judgments,
        "citations": citations,
    }


def usage_source_records() -> dict[str, dict[str, Any]]:
    """Admitted source proof of every curated record, keyed by the headword it binds.

    ``scripts/audit/generate_search_index.py`` writes this view into
    ``lexicon-browse-meta.json`` (``usageSources``), so browse and entry pages
    judge stored Atlas records by current curated proof, never by citations
    copied into the database.
    """
    import yaml  # noqa: F401 -- the reviewed judgments live in heritage_pairs.yaml; never drop them silently

    records: dict[str, dict[str, Any]] = {}
    for key, record in sorted(_curated_calque_map().items()):
        proof = admitted_source_proof(record, key)
        if proof:
            records[key] = proof
    return records


def _curated_scope_record(status: dict[str, Any]) -> dict[str, Any] | None:
    """The curated calque record whose explicit ``kind`` states its scope."""
    for key in ("curated_calque", "calque_warning"):
        record = status.get(key)
        if isinstance(record, dict) and str(record.get("kind") or "").strip():
            return record
    return None


def _usage_marker_classes(text: str) -> set[str]:
    return {name for name, pattern in _USAGE_MARKER_RES.items() if pattern.search(text)}


def _strip_accents(text: str) -> str:
    return _ACUTE_RE.sub("", html.unescape(str(text or "")))


def card_headword_matches(definition: str, headword: str | None) -> bool:
    """True when a dictionary card's leading headword is ``headword``."""
    head = _normalize_word(headword or "").split()
    tokens = _strip_accents(definition).split()
    if not head or len(tokens) < len(head):
        return False
    # A homonym index (``ДИВАН²``) still names this headword; the card is then
    # ambiguous (see :func:`modern_headword_labels`), never another word's.
    leading = [_normalize_word(token.strip(_EDGE_PUNCT + _SUPERSCRIPT_DIGITS)) for token in tokens[: len(head)]]
    return leading == head


def modern_headword_labels(definition: str) -> tuple[set[str], bool]:
    """Usage-label classes in a СУМ-20/ВТС headword slot, plus an ambiguity flag.

    The headword slot is the grammar/label run before the first sense
    (a capitalised gloss, a sense number or ``《``). A homonym index (``²``,
    ``ДИВАН²``, ``II``) makes the card ambiguous for a single Atlas headword.
    """
    plain = _strip_accents(definition)
    tokens = plain.split()
    slot: list[str] = []
    ambiguous = bool(tokens) and any(char in _SUPERSCRIPT_DIGITS for char in tokens[0])
    for index, token in enumerate(tokens):
        if _HOMONYM_INDEX_RE.match(token):
            ambiguous = True
            continue
        if index == 0:
            continue
        if _SENSE_START_RE.match(token):
            break
        slot.append(token)
    if re.search(r"(?<!\S)II(?!\S)", plain):
        ambiguous = True
    return _usage_marker_classes(_normalize_word(" ".join(slot))), ambiguous


def _modern_dictionary_card(definition_cards: object, headword: str | None) -> tuple[str, str] | None:
    """The first СУМ-20 (else ВТС) definition whose headword is the article's."""
    if not isinstance(definition_cards, list):
        return None
    for card_id, label in _MODERN_DICTIONARY_CARDS:
        for card in definition_cards:
            if not isinstance(card, dict) or card.get("id") != card_id:
                continue
            for definition in card.get("definitions") or []:
                if str(definition or "").strip() and card_headword_matches(str(definition), headword):
                    return label, str(definition)
    return None


def _esum_locator(ref: object) -> str:
    match = _ESUM_REF_RE.match(str(ref or ""))
    if match:
        return f"ЕСУМ, т. {match['volume']}, с. {match['page']}"
    return "ЕСУМ"


def shares_referent(source_gloss: str, article_gloss: str | None) -> bool:
    """True when two glosses share a content word (five letters or more)."""
    source = {word for word in _words(source_gloss) if len(word) >= _MIN_REFERENT_TOKEN_LEN}
    article = {word for word in _words(article_gloss or "") if len(word) >= _MIN_REFERENT_TOKEN_LEN}
    return bool(source & article)


def _esum_headword_marker(
    status: dict[str, Any],
    marker_class: str,
    *,
    headword: str | None,
    gloss: str | None,
) -> dict[str, Any] | None:
    """An ЕСУМ marker in the headword slot of the same headword and referent.

    ЕСУМ is a historical witness: ``гридь (іст.) «нижча верхівка княжої
    дружини»`` binds «історизм» to the article whose gloss names the same
    referent. Markers on cognates, later derivatives, quotations, homonyms or
    another sense never reach the headword slot or fail the referent check.
    """
    head = _normalize_word(headword or "")
    if not head:
        return None
    for attestation in status.get("attestations") or []:
        if not isinstance(attestation, dict) or str(attestation.get("source") or "").casefold() not in {
            "esum",
            "есум",
        }:
            continue
        if _normalize_word(str(attestation.get("word") or "")) != head:
            continue
        match = _ESUM_HEADWORD_SLOT_RE.match(_strip_accents(str(attestation.get("detail") or "")))
        if not match or _normalize_word(match["word"]) != head:
            continue
        if marker_class not in _usage_marker_classes(_normalize_word(match["marker"])):
            continue
        if not shares_referent(match["gloss"] or match["explanation"], gloss):
            continue
        return _usage_label(
            USAGE_LABEL_CODES[marker_class],
            "lemma",
            [_esum_locator(attestation.get("ref"))],
            match.group(0).strip(),
        )
    return None


def _treasured_label(
    status: dict[str, Any],
    classification: str,
    *,
    headword: str | None,
    definition_cards: object,
    gloss: str | None,
) -> dict[str, Any]:
    if classification == "borrowing":
        for attestation in status.get("attestations") or []:
            if (
                isinstance(attestation, dict)
                and attestation.get("source") == "esum"
                and headword
                and _normalize_word(str(attestation.get("word") or "")) == _normalize_word(headword)
                and "запозич" in _normalize_word(str(attestation.get("detail") or ""))
            ):
                return _usage_label("borr", "lemma", [_esum_locator(attestation.get("ref"))], attestation.get("detail"))
        return _usage_label(None, "unresolved", [], None, reason="no_headword_etymology")
    code = USAGE_LABEL_CODES[classification]
    marker_class = "authentic-archaism" if code == "arch" else classification
    # Each source keeps its evidential role (rules P5). A label in the headword
    # slot of the article's modern explanatory card for the same headword
    # binds; a label on one numbered sense or a homonym-indexed card does not.
    # An ЕСУМ marker in the headword slot of the same headword and referent is
    # a historical witness. Archaism and dialect are claims about current
    # register, which the modern card decides: an unlabelled card outweighs
    # the witness (платівка). A historism names a historical referent, which
    # an unlabelled single-sense card does not contradict; homonyms or several
    # senses limit it to one sense. Грінченко and VESUM tags stay attestations.
    modern = _modern_dictionary_card(definition_cards, headword)
    whole_word = True
    if modern is not None:
        source_label, definition = modern
        classes, ambiguous = modern_headword_labels(definition)
        if not ambiguous and marker_class in classes:
            return _usage_label(code, "lemma", [source_label], definition[:240])
        whole_word = (
            marker_class == "historism" and not ambiguous and not _SECOND_SENSE_RE.search(_strip_accents(definition))
        )
    witness = _esum_headword_marker(status, marker_class, headword=headword, gloss=gloss)
    if witness is not None:
        if whole_word:
            return witness
        return {**witness, "code": None, "scope": "unresolved", "reason": "source_marker_not_whole_word"}
    reason = f"{modern[0]}_headword_unlabelled" if modern is not None else "no_headword_bound_label"
    return _usage_label(None, "unresolved", [], None, reason=reason)


def _usage_label(
    code: str | None, scope: str, authority: list[str], evidence: object, *, reason: str = ""
) -> dict[str, Any]:
    return {
        "code": code,
        "scope": scope,
        "authority": authority,
        "evidence": str(evidence) if evidence else None,
        "reason": reason or scope,
    }


def resolve_usage_label(
    heritage_status: dict[str, Any] | None,
    *,
    headword: str | None = None,
    definition_cards: object = None,
    gloss: str | None = None,
    source_proof: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Resolve the source-scoped Word Atlas usage label for one record.

    Returns ``{"code", "scope", "authority", "evidence", "reason"}``. ``code``
    is set only for ``scope == "lemma"``; ``sense``/``phrase`` are contextual
    calque cautions on this headword, ``reverse`` marks a recommended
    replacement, ``unresolved`` marks warnings or labels whose scope or
    authority the record does not establish. Without ``headword`` nothing can
    bind to the word, so no lemma label is returned.

    ``source_proof`` is the current curated proof for this headword
    (:func:`usage_source_records`; ``{}`` when there is none). Consumers of
    stored records always pass it: citations stored in an old record are
    provenance, never authority. Without it (the producer, whose record is
    current) the record's own proof is admitted.
    """
    status = heritage_status or {}
    classification = str(status.get("classification") or "unknown")

    treasured: dict[str, Any] | None = None
    if classification in USAGE_LABEL_CODES and USAGE_LABEL_CODES[classification] not in {"rus", "calq"}:
        treasured = _treasured_label(
            status,
            classification,
            headword=headword,
            definition_cards=definition_cards,
            gloss=gloss,
        )
        if treasured["scope"] == "lemma":
            return treasured

    stored = _curated_scope_record(status)
    proof = (admitted_source_proof(stored, headword) if source_proof is None else source_proof) or {}
    curated = proof if proof.get("kind") else stored
    if curated is not None:
        kind = str(curated.get("kind")).strip()
        judgments = list(proof.get("judgments") or [])
        authority = list(dict.fromkeys(item["locator"] for item in judgments + list(proof.get("citations") or [])))
        contextual = _CONTEXTUAL_CALQUE_SCOPES.get(kind)
        if contextual:
            scope_text = (
                proof.get("sense") or curated.get("calque_sense") or curated.get("calqueSense") or curated.get("note")
            )
            return _usage_label(None, contextual, authority, scope_text)
        if kind not in _LEMMA_CALQUE_KINDS:
            return _usage_label(None, "unresolved", [], None, reason="curated_kind_without_scope")
        if not judgments:
            return _usage_label(None, "unresolved", [], None, reason="no_headword_bound_evidence")
        is_rus = bool(status.get("is_russianism")) and classification not in _AUTHENTIC_CLASSIFICATIONS
        passage = judgments[0]["passage"]
        excerpt = f"{passage[:240]}…" if len(passage) > 240 else passage
        return _usage_label("rus" if is_rus else "calq", "lemma", authority, excerpt)

    if status.get("is_russianism") or classification in {"russianism", "calque"} or _has_calque_alternative(status):
        return _usage_label(None, "unresolved", [], None, reason="no_lemma_scoped_authority")
    if treasured is not None:
        return treasured
    if _has_reverse_calque(status):
        return _usage_label(None, "reverse", [], None)
    return _usage_label(None, "none", [], None)


def compute_warning_severity(
    heritage_status: dict[str, Any] | None,
    *,
    vesum_attested: bool,
    max_sovietization_risk: int = 0,
    headword: str | None = None,
) -> str:
    """Compute the Word Atlas warning severity from status data only.

    Red and yellow follow :func:`resolve_usage_label`: red only for a
    lemma-scoped Russianism bound to ``headword`` by normative evidence;
    yellow for a lemma-scoped calque or a sense/phrase-scoped caution on this
    headword. A recommended replacement (reverse calque), a bare replacement
    suggestion and a Russian morphological shadow never raise a warning by
    themselves (#9603).
    """
    status = heritage_status or {}
    classification = str(status.get("classification") or "unknown")
    positive_attestation = has_positive_attestation(status)
    label = resolve_usage_label(status, headword=headword)

    if label["scope"] == "lemma" and label["code"] == "rus":
        return "russianism_red"

    if (label["scope"] == "lemma" and label["code"] == "calq") or label["scope"] in {"sense", "phrase"}:
        return "calque_yellow"

    unresolved_claim = label["scope"] == "unresolved" and label["reason"] in UNRESOLVED_CLAIM_REASONS
    if not unresolved_claim and (
        classification in _TREASURED_CLASSIFICATIONS or (classification == "standard" and positive_attestation)
    ):
        return "treasured"

    if max_sovietization_risk > 0:
        return "soviet_def_blue"

    return "none"


_THREAD_LOCAL = threading.local()


def close_cached_connections() -> None:
    """Close and clear all thread-local source DB connections on current thread."""
    conns = getattr(_THREAD_LOCAL, "conns", None)
    if conns:
        for conn in list(conns.values()):
            with suppress(Exception):
                conn.close()
        conns.clear()


def _clear_thread_local_cache_in_child() -> None:
    if hasattr(_THREAD_LOCAL, "conns"):
        _THREAD_LOCAL.conns = {}


if hasattr(os, "register_at_fork"):
    with suppress(Exception):
        os.register_at_fork(after_in_child=_clear_thread_local_cache_in_child)


@lru_cache(maxsize=1)
def _resolve_primary_checkout() -> Path | None:
    """Primary checkout root via the shared ``.git`` common dir (#6571).

    Returns None outside a git repo so callers fall back honestly.
    """
    try:
        from guardrails.worktree_containment import (
            NotAGitRepositoryError,
            resolve_main_root,
        )
    except ImportError:  # repo root on sys.path instead of scripts/
        from scripts.guardrails.worktree_containment import (  # type: ignore[no-redef]
            NotAGitRepositoryError,
            resolve_main_root,
        )
    try:
        return resolve_main_root(ROOT)
    except NotAGitRepositoryError:
        return None


def _source_db_path(db_path: str | Path | None = None) -> Path:
    target = Path(db_path) if db_path is not None else SOURCES_DB
    if target.is_file() and target.stat().st_size >= 1_000_000:
        return target
    # Sparse worktree fallback: the multi-GB sources.db lives only in the
    # primary checkout. Try the worktree-local path first (often a symlink into
    # it), then the primary checkout resolved from the shared .git common dir
    # instead of a hardcoded absolute path (#6571).
    primary = ROOT / "data" / "sources.db"
    if primary.is_file() and primary.stat().st_size >= 1_000_000:
        return primary
    primary_checkout = _resolve_primary_checkout()
    if primary_checkout is not None:
        abs_primary = primary_checkout / "data" / "sources.db"
        if abs_primary.is_file() and abs_primary.stat().st_size >= 1_000_000:
            return abs_primary
    return target


def _get_thread_local_conn(source_db: Path) -> sqlite3.Connection:
    if not hasattr(_THREAD_LOCAL, "conns"):
        _THREAD_LOCAL.conns = {}
    key = str(source_db.resolve())
    conn = _THREAD_LOCAL.conns.get(key)
    if conn is None:
        conn = sqlite3.connect(f"file:{source_db.resolve()}?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA query_only = 1")
        _THREAD_LOCAL.conns[key] = conn
    return conn


@contextmanager
def _source_conn(db_path: str | Path | None = None) -> Iterator[sqlite3.Connection]:
    source_db = _source_db_path(db_path)
    if not source_db.exists():
        raise FileNotFoundError(f"local sources database not found: {source_db}")
    yield _get_thread_local_conn(source_db)


def _normalize_word(word: str) -> str:
    text = html.unescape(str(word or "")).strip().casefold()
    text = _ACUTE_RE.sub("", text)
    text = text.replace("`", "'").replace("’", "ʼ")
    return _SPACE_RE.sub(" ", text)


def _lemma_variants(lemma: str) -> list[str]:
    variants: list[str] = []
    seen: set[str] = set()
    for part in re.split(r"[/,]", str(lemma or "")):
        term = _normalize_word(part)
        if term and term not in seen:
            seen.add(term)
            variants.append(term)
    return variants


def _is_single_token(term: str) -> bool:
    return bool(re.fullmatch(r"[А-Яа-яЄєІіЇїҐґ'’ʼ-]+", term))


def _clean_text(text: object, *, limit: int = 500) -> str:
    cleaned = _SPACE_RE.sub(" ", html.unescape(str(text or ""))).strip()
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 1].rstrip() + "…"


def _whole_token_pattern(term: str) -> re.Pattern[str]:
    return re.compile(
        rf"(?<![{_CYRILLIC_WORD_CHARS}]){re.escape(term)}(?![{_CYRILLIC_WORD_CHARS}])",
        re.IGNORECASE,
    )


def _contains_whole_token(text: str, term: str) -> bool:
    return bool(_whole_token_pattern(term).search(_normalize_word(text)))


def _apostrophe_variants(term: str) -> tuple[str, ...]:
    variants = {term}
    for char in ("'", "’", "ʼ"):
        if char in term:
            for replacement in ("'", "’", "ʼ"):
                variants.add(term.replace(char, replacement))
    return tuple(sorted(variants))


_CURATED_CALQUE_MAP: dict[str, dict[str, Any]] | None = None


def _curated_calque_map() -> dict[str, dict[str, Any]]:
    global _CURATED_CALQUE_MAP
    if _CURATED_CALQUE_MAP is not None:
        return _CURATED_CALQUE_MAP

    calque_map: dict[str, dict[str, Any]] = {}

    # 1. Load from calque_corrections.py if available
    try:
        try:
            from scripts.lexicon.calque_corrections import (
                CURATED_CALQUES,
                PHRASAL_CALQUES,
                SENSE_RESTRICTED_CALQUES,
            )
        except ImportError:
            # Loaded as a file (generate_search_index.py): only scripts/ is on sys.path.
            from lexicon.calque_corrections import (  # type: ignore[no-redef]
                CURATED_CALQUES,
                PHRASAL_CALQUES,
                SENSE_RESTRICTED_CALQUES,
            )

        for term, data in CURATED_CALQUES.items():
            norm = _normalize_word(term)
            if norm:
                calque_map[norm] = {
                    "kind": data.get("kind", "participle"),
                    "corrections": list(data.get("corrections") or []),
                    "note": data.get("note", ""),
                    "citations": list(data.get("source") or []),
                    "evidence": list(data.get("evidence") or []),
                    "source": "calque_corrections",
                }
        for term, data in SENSE_RESTRICTED_CALQUES.items():
            norm = _normalize_word(term)
            if norm:
                calque_map[norm] = {
                    "kind": "sense_restricted",
                    "corrections": list(data.get("corrections") or []),
                    "calque_sense": data.get("calque_sense", ""),
                    "authentic_sense": data.get("authentic_sense", ""),
                    "note": data.get("note", ""),
                    "citations": list(data.get("source") or []),
                    "evidence": list(data.get("evidence") or []),
                    "source": "calque_corrections",
                }
        for term, data in PHRASAL_CALQUES.items():
            norm = _normalize_word(term)
            if norm:
                calque_map[norm] = {
                    "kind": "phrasal",
                    "corrections": list(data.get("corrections") or []),
                    "note": data.get("note", ""),
                    "citations": list(data.get("source") or []),
                    "evidence": list(data.get("evidence") or []),
                    "source": "calque_corrections",
                }
    except ImportError:
        pass

    # 2. Load from heritage_pairs.yaml (enriches / overrides)
    if HERITAGE_PAIRS_YAML.exists():
        try:
            import yaml

            payload = yaml.safe_load(HERITAGE_PAIRS_YAML.read_text(encoding="utf-8")) or {}
            pairs = payload.get("pairs", [])
            for p in pairs:
                label = p.get("calqueLabel")
                if not label:
                    continue
                surfaces = p.get("calqueSurfaces") or []
                corrections = list(p.get("corrections") or [])
                entry = {
                    "kind": p.get("kind", "lexical"),
                    "corrections": corrections,
                    "rationale": p.get("rationale", ""),
                    "rationaleUk": p.get("rationaleUk", ""),
                    "calqueSense": p.get("calqueSense"),
                    "authenticSense": p.get("authenticSense"),
                    "citations": list(p.get("citations") or []),
                    "judgments": reviewed_judgments(p),
                    "source": "heritage_pairs",
                    "severity": p.get("severity", "calque_yellow"),
                    "curator": p.get("curator", ""),
                }
                keys = [label] + [s for s in surfaces if s]
                for k in keys:
                    norm_k = _normalize_word(k)
                    if not norm_k:
                        continue
                    if norm_k in calque_map:
                        existing = calque_map[norm_k]
                        is_sense_restricted = (
                            existing.get("kind") == "sense_restricted"
                            or entry.get("kind") == "sense_restricted"
                            or bool(existing.get("authentic_sense"))
                            or bool(existing.get("authenticSense"))
                            or bool(entry.get("authenticSense"))
                        )
                        merged_corrections = list(existing.get("corrections") or [])
                        for corr in entry.get("corrections") or []:
                            if corr not in merged_corrections:
                                merged_corrections.append(corr)

                        curator_existing = str(existing.get("curator") or "")
                        curator_new = str(p.get("curator") or "")
                        prefer_existing = existing.get("source") == "calque_corrections" or (
                            not curator_existing.startswith("script:") and curator_new.startswith("script:")
                        )

                        merged = dict(existing if prefer_existing else entry)
                        merged["corrections"] = merged_corrections
                        if is_sense_restricted:
                            merged["kind"] = "sense_restricted"
                            merged["authenticSense"] = (
                                entry.get("authenticSense")
                                or existing.get("authenticSense")
                                or existing.get("authentic_sense")
                                or entry.get("authentic_sense")
                            )
                            merged["calqueSense"] = (
                                entry.get("calqueSense")
                                or existing.get("calqueSense")
                                or existing.get("calque_sense")
                                or entry.get("calqueSense")
                            )
                        if not merged.get("rationaleUk"):
                            merged["rationaleUk"] = existing.get("rationaleUk") or entry.get("rationaleUk") or ""
                        merged["judgments"] = list(existing.get("judgments") or []) + [
                            item
                            for item in entry.get("judgments") or []
                            if item not in (existing.get("judgments") or [])
                        ]
                        calque_map[norm_k] = merged
                    else:
                        calque_map[norm_k] = entry
        except Exception as e:
            print(f"WARN: Failed to load heritage_pairs.yaml in heritage_classifier: {e}", file=sys.stderr)

    _CURATED_CALQUE_MAP = calque_map
    return _CURATED_CALQUE_MAP


def _lookup_curated_calque(term: str, lemmas: list[str] | None = None) -> dict[str, Any] | None:
    cmap = _curated_calque_map()
    norm = _normalize_word(term)
    if norm in cmap:
        return cmap[norm]
    if lemmas:
        for lem in lemmas:
            norm_lem = _normalize_word(lem)
            if norm_lem in cmap:
                return cmap[norm_lem]
    return None


def _extract_vesum_lemmas(vesum: dict[str, Any] | None) -> list[str]:
    if not vesum:
        return []
    ref = str(vesum.get("ref") or "")
    return [part.strip() for part in ref.split(",") if part.strip()]


def _capitalize_term(term: str) -> str:
    if "-" in term:
        return "-".join(part.capitalize() for part in term.split("-"))
    return term.capitalize()


def _vesum_attestation(
    term: str,
    *,
    surface: bool,
    vesum_db_path: str | Path | None = None,
) -> dict[str, Any] | None:
    try:
        cap_term = _capitalize_term(term)
        if surface:
            from scripts.verification.vesum import verify_word

            matches = verify_word(term, db_path=vesum_db_path)
            if not matches and cap_term != term:
                matches = verify_word(cap_term, db_path=vesum_db_path)
            if not matches:
                return None
            lemmas = sorted({str(match.get("lemma") or "") for match in matches if match.get("lemma")})
            return {
                "source": "VESUM",
                "ref": ",".join(lemmas) or term,
                "detail": f"word_form match ({len(matches)} form analysis)",
            }

        from scripts.verification.vesum import verify_lemma, verify_word

        forms = verify_lemma(term, db_path=vesum_db_path)
        if not forms and cap_term != term:
            forms = verify_lemma(cap_term, db_path=vesum_db_path)
        if forms:
            return {
                "source": "VESUM",
                "ref": term,
                "detail": f"lemma match ({len(forms)} forms)",
            }
        matches = verify_word(term, db_path=vesum_db_path)
        if not matches and cap_term != term:
            matches = verify_word(cap_term, db_path=vesum_db_path)
        if matches:
            lemmas = sorted({str(match.get("lemma") or "") for match in matches if match.get("lemma")})
            return {
                "source": "VESUM",
                "ref": ",".join(lemmas) or term,
                "detail": "word_form match for lemma query",
            }
    except Exception:
        return None
    return None


def _is_archaic_tags(tags: str | None) -> bool:
    return "arch" in str(tags or "").split(":")


def _vesum_archaism_attestation(
    term: str,
    *,
    surface: bool,
    vesum_db_path: str | Path | None = None,
) -> dict[str, Any] | None:
    try:
        from scripts.verification.vesum import verify_lemma, verify_word

        rows = verify_word(term, db_path=vesum_db_path) if surface else verify_lemma(term, db_path=vesum_db_path)
        if not rows and not surface:
            rows = verify_word(term, db_path=vesum_db_path)
    except Exception:
        return None
    if not rows:
        return None

    archaic_rows = [row for row in rows if _is_archaic_tags(row.get("tags"))]
    if not archaic_rows:
        return None
    sample = archaic_rows[0]
    return {
        "has_modern": len(archaic_rows) < len(rows),
        "attestation": {
            "source": "VESUM",
            "ref": term,
            "detail": (
                f"archaic tag in VESUM ({len(archaic_rows)}/{len(rows)} forms; sample tags={sample.get('tags')})"
            ),
        },
    }


def _check_russian_shadow(
    term: str,
    *,
    vesum_db_path: str | Path | None = None,
) -> tuple[bool, dict[str, Any]]:
    if not _is_single_token(term):
        return False, {"available": False, "reason": "not_single_token"}
    try:
        from scripts.verification.check_ru_morph import is_russian_pattern

        result = is_russian_pattern(term, vesum_db_path=vesum_db_path)
    except Exception as exc:
        return False, {"available": False, "error": str(exc)}
    return bool(result.get("matches_russian")), {"available": True, **result}


def _strict_heritage_attestations(
    conn: sqlite3.Connection,
    term: str,
    *,
    surface: bool,
) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    hits.extend(_grinchenko_exact_hits(conn, term))
    hits.extend(_esum_exact_hits(conn, term))
    hits.extend(_esum_variant_hits(conn, term))
    if surface:
        hits.extend(_grinchenko_surface_usage_hits(conn, term))
    return hits


def _standard_dictionary_attestations(
    conn: sqlite3.Connection,
    term: str,
) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    for hit in _wiktionary_exact_hits(conn, term):
        if hit["classification"] == "standard":
            hits.append(hit)
    return hits


def _default_slovnyk_cache_dir() -> Path:
    override = os.environ.get("LEXICON_SLOVNYK_CACHE")
    if override:
        return Path(override).expanduser()
    local = ROOT / "data" / "lexicon" / "slovnyk_cache"
    if local.exists():
        return local
    parts = ROOT.parts
    if ".worktrees" in parts:
        main_root = Path(*parts[: parts.index(".worktrees")])
        main_cache = main_root / "data" / "lexicon" / "slovnyk_cache"
        if main_cache.exists():
            return main_cache
    return local


def _slovnyk_cache_path(term: str) -> Path:
    stem = re.sub(r"[^0-9A-Za-zА-Яа-яЄєІіЇїҐґ'’ʼ-]+", "-", term).strip("-")
    return _default_slovnyk_cache_dir() / f"{stem or 'empty'}.json"


def _cached_slovnyk_hits(term: str) -> list[dict[str, Any]]:
    # Deferred import: enrich_manifest imports classify_lemma/compute_warning_severity
    # from this module at its own top level, so a module-level import here would
    # be circular. _load_current_slovnyk_cache_file() is the one gated reader that
    # refuses a stale schema_version instead of handing back a v2 row with
    # corrupted `text` (#6524).
    from scripts.lexicon.enrich_manifest import _load_current_slovnyk_cache_file

    cache = _load_current_slovnyk_cache_file(_slovnyk_cache_path(term))
    if cache is None:
        return []
    lookups = cache.get("lookups")
    if not isinstance(lookups, dict):
        return []

    hits: list[dict[str, Any]] = []
    for slug, row in lookups.items():
        if slug not in _SLOVNYK_HERITAGE_SLUGS or not isinstance(row, dict):
            continue
        text = _clean_text(row.get("text"), limit=500)
        if not text:
            continue
        hits.append(
            {
                "query": term,
                "source_family": "slovnyk_me",
                "source": row.get("dictionary_label") or "slovnyk.me",
                "word": row.get("word") or term,
                "text": text,
                "classification": "cached_slovnyk_attestation",
                "is_authentic_ukrainian": True,
                "is_russianism": False,
                "is_modern": slug in {"newsum", "vts"},
                "is_dialect": _classification_from_source_text(text, default="standard") == "dialect",
                "sovietization_risk": 0,
                "evidence_tags": ["slovnyk_me_cache", slug],
            }
        )
    return hits


def _search_heritage_attestations(
    term: str,
    db_path: str | Path | None = None,
) -> list[dict[str, Any]]:
    try:
        from wiki.sources_db import search_heritage

        hits = search_heritage(term, limit=10, include_live_slovnyk=False, db_path=db_path)
    except Exception:
        hits = []
    hits.extend(_cached_slovnyk_hits(term))

    out: list[dict[str, Any]] = []
    for hit in hits:
        if hit.get("is_russianism"):
            continue
        hit_word = _normalize_word(str(hit.get("word") or ""))
        if hit_word and hit_word != term:
            continue
        text = _clean_text(_heritage_hit_text(hit), limit=500)
        classification = _classification_from_heritage_hit(hit, text)
        if classification == "standard":
            continue
        out.append(
            {
                "classification": classification,
                "attestation": {
                    "source": _heritage_source_id(hit),
                    "ref": str(hit.get("word") or hit.get("source") or term),
                    "detail": text,
                },
                "sovietization_risk": int(hit.get("sovietization_risk") or 0),
            }
        )
    return out


def _heritage_hit_text(hit: dict[str, Any]) -> str:
    return str(hit.get("text") or hit.get("definition") or hit.get("etymology_text") or hit.get("snippet") or "")


def _heritage_source_id(hit: dict[str, Any]) -> str:
    family = str(hit.get("source_family") or "heritage")
    source = str(hit.get("source") or "")
    if family == "slovnyk_me":
        return f"search_heritage:slovnyk_me:{source}".rstrip(":")
    if family == "esum":
        return "search_heritage:esum"
    if family == "grinchenko":
        return "search_heritage:grinchenko_1907"
    if family == "style_guide":
        return "search_heritage:style_guide"
    return f"search_heritage:{family}"


def _has_any_marker(text: str, markers: tuple[str, ...]) -> bool:
    return any(marker in text for marker in markers)


def _classification_from_source_text(text: str, *, default: str) -> str:
    lower = _normalize_word(text)
    if _has_any_marker(lower, _HISTORISM_MARKERS):
        return "historism"
    if _has_any_marker(lower, _DIALECT_MARKERS):
        return "dialect"
    if _has_any_marker(lower, _ARCHAIC_MARKERS):
        return "authentic-archaism"
    if "рідко" in lower and not re.search(r"\b[12]\.", lower):
        return "authentic-archaism"
    if _has_any_marker(lower, _BORROWING_MARKERS):
        return "borrowing"
    return default


def _strict_classification_from_source_text(text: str, *, default: str) -> str:
    lower = _normalize_word(text)
    if _has_any_marker(lower, ("іст.", "істор.", "(іст.)")):
        return "historism"
    if _has_any_marker(lower, ("діал.", " діал ", "діалект")):
        return "dialect"
    if _has_any_marker(lower, ("заст.", "застар", "архаї")):
        return "authentic-archaism"
    if _has_any_marker(lower, _BORROWING_MARKERS):
        return "borrowing"
    return default


def _esum_headword_classification(text: str, term: str, *, exact: bool) -> str:
    if term in _DIALECT_OR_FOLK_TERMS:
        return "dialect"
    if not exact:
        return "standard"

    lower = _normalize_word(text)
    term_pattern = re.escape(_normalize_word(term))
    headword_marker_re = re.compile(
        rf"^\[?{term_pattern}\]?\s*(?:\([^)]*(?:іст\.|істор\.|діал\.|заст\.|застар|архаї)[^)]*\)|"
        rf"«[^»]{{0,160}}(?:\(іст\.\)|\(діал\.\)|\(заст\.\))"
        rf")"
    )
    if not headword_marker_re.search(lower):
        return "standard"
    return _strict_classification_from_source_text(lower, default="standard")


def _classification_from_heritage_hit(hit: dict[str, Any], text: str) -> str:
    classification = _classification_from_source_text(text, default="standard")
    if classification != "standard":
        return classification
    if bool(hit.get("is_dialect")) and _has_any_marker(_normalize_word(text), _DIALECT_MARKERS):
        return "dialect"
    return "standard"


def _grinchenko_exact_hits(conn: sqlite3.Connection, term: str) -> list[dict[str, Any]]:
    hits = []
    for variant in _apostrophe_variants(term):
        rows = conn.execute(
            "SELECT id, word, definition, source FROM grinchenko WHERE lower(word) = ? LIMIT 3",
            (variant,),
        ).fetchall()
        for row in rows:
            text = _clean_text(row["definition"])
            classification = _strict_classification_from_source_text(text, default="standard")
            hits.append(
                {
                    "classification": classification,
                    "attestation": {
                        "source": "grinchenko_1907",
                        "ref": str(row["id"]),
                        "word": row["word"],
                        "detail": text,
                    },
                    "sovietization_risk": 0,
                    "weak_when_modern": classification == "authentic-archaism"
                    and _classification_from_source_text(text, default="standard") == "standard",
                }
            )
    return hits


def _grinchenko_crossref_hits(conn: sqlite3.Connection, term: str) -> list[dict[str, Any]]:
    rows = conn.execute(
        "SELECT id, word, definition, source FROM grinchenko WHERE lower(definition) LIKE ? LIMIT 20",
        (f"%{term}%",),
    ).fetchall()
    hits = []
    crossref_re = re.compile(rf"(?:=|див\.)\s*{re.escape(term)}(?=\W|$)", re.IGNORECASE)
    for row in rows:
        definition = _normalize_word(row["definition"])
        if not crossref_re.search(definition):
            continue
        text = _clean_text(row["definition"])
        classification = _classification_from_definition(text, default="dialect")
        hits.append(
            {
                "classification": classification,
                "attestation": {
                    "source": "grinchenko_1907",
                    "ref": str(row["id"]),
                    "word": row["word"],
                    "detail": text,
                },
                "sovietization_risk": 0,
                "weak_when_modern": classification == "dialect"
                and _classification_from_source_text(text, default="standard") == "standard",
            }
        )
    return hits


def _grinchenko_surface_usage_hits(conn: sqlite3.Connection, term: str) -> list[dict[str, Any]]:
    rows = conn.execute(
        "SELECT id, word, definition, source FROM grinchenko WHERE lower(definition) LIKE ? LIMIT 8",
        (f"%{term}%",),
    ).fetchall()
    hits = []
    for row in rows:
        if not _contains_whole_token(str(row["definition"]), term):
            continue
        text = _clean_text(row["definition"])
        hits.append(
            {
                "classification": _classification_from_definition(text, default=_form_default_classification(term)),
                "attestation": {
                    "source": "grinchenko_1907",
                    "ref": str(row["id"]),
                    "word": row["word"],
                    "detail": text,
                },
                "sovietization_risk": 0,
            }
        )
    return hits


def _sum11_has_flag_columns(conn: sqlite3.Connection) -> bool:
    cols = {row[1] for row in conn.execute("PRAGMA table_info(sum11);").fetchall()}
    return {"sovietization_risk", "sovietization_keywords"}.issubset(cols)


@lru_cache(maxsize=8)
def _sum11_has_flag_columns_for_db(
    db_path: str,
    mtime_ns: int,
    size: int,
) -> bool:
    del mtime_ns, size  # cache-key invalidators; not used in the query itself.
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        return _sum11_has_flag_columns(conn)
    finally:
        conn.close()


def _source_sum11_has_flag_columns(db_path: str | Path | None = None) -> bool:
    try:
        source_db = _source_db_path(db_path)
        stat = source_db.stat()
        return _sum11_has_flag_columns_for_db(
            str(source_db.resolve()),
            stat.st_mtime_ns,
            stat.st_size,
        )
    except (OSError, sqlite3.Error):
        return False


def _sum11_sovietization_risk_for_term(
    term: str,
    db_path: str | Path | None = None,
) -> int:
    try:
        has_flag_columns = _source_sum11_has_flag_columns(db_path)
        with _source_conn(db_path) as conn:
            if has_flag_columns:
                risk = 0
                for variant in _apostrophe_variants(term):
                    row = conn.execute(
                        "SELECT MAX(sovietization_risk) FROM sum11 WHERE lower(word) = ?",
                        (variant,),
                    ).fetchone()
                    if row:
                        risk = max(risk, int(row[0] or 0))
                return risk

            risk = 0
            for variant in _apostrophe_variants(term):
                rows = conn.execute(
                    "SELECT definition, text FROM sum11 WHERE lower(word) = ? LIMIT 3",
                    (variant,),
                ).fetchall()
                for row in rows:
                    risk = max(
                        risk,
                        _sum11_sovietization_risk(
                            str(row["definition"] or ""),
                            str(row["text"] or ""),
                        ),
                    )
            return risk
    except (FileNotFoundError, sqlite3.Error):
        return 0


def _esum_exact_hits(conn: sqlite3.Connection, term: str) -> list[dict[str, Any]]:
    if not _table_exists(conn, "esum_etymology_meta"):
        return []
    hits = []
    for variant in _apostrophe_variants(term):
        rows = conn.execute(
            """
            SELECT id, lemma, etymology_text, cognates, vol, page, source
            FROM esum_etymology_meta
            WHERE lemma = ? COLLATE NOCASE
            ORDER BY vol, page, lemma
            LIMIT 3
            """,
            (variant,),
        ).fetchall()
        for row in rows:
            hits.append(_esum_hit(term, row, exact=True))
    return hits


def _esum_variant_hits(conn: sqlite3.Connection, term: str) -> list[dict[str, Any]]:
    if not _table_exists(conn, "esum_etymology_meta"):
        return []
    if term not in _DIALECT_OR_FOLK_TERMS:
        return []

    rows: list[sqlite3.Row] = []
    if _table_exists(conn, "esum_etymology"):
        try:
            rows = conn.execute(
                """
                SELECT rowid AS id, lemma, etymology_text, cognates, vol, page, 'ЕСУМ' AS source
                FROM esum_etymology
                WHERE esum_etymology MATCH ?
                ORDER BY rank
                LIMIT 20
                """,
                (_fts_phrase_query(term),),
            ).fetchall()
        except sqlite3.OperationalError:
            rows = []

    if not rows:
        rows = conn.execute(
            """
            SELECT id, lemma, etymology_text, cognates, vol, page, source
            FROM esum_etymology_meta
            WHERE lower(etymology_text) LIKE ?
            ORDER BY vol, page, lemma
            LIMIT 20
            """,
            (f"%{term}%",),
        ).fetchall()

    hits = []
    for row in rows:
        if _normalize_word(row["lemma"]) == term:
            continue
        if not _contains_whole_token(str(row["etymology_text"] or ""), term):
            continue
        hit = _esum_hit(term, row, exact=False)
        if hit["classification"] == "standard":
            continue
        hits.append(hit)
    return hits


def _esum_hit(term: str, row: sqlite3.Row, *, exact: bool) -> dict[str, Any]:
    text = _clean_text(row["etymology_text"])
    classification = _classification_from_etymology(text, term, exact=exact)
    return {
        "classification": classification,
        "attestation": {
            "source": "esum",
            "ref": f"{row['lemma']}:{row['vol']}:{row['page']}",
            "word": row["lemma"] if not exact else term,
            "detail": text,
        },
        "sovietization_risk": 0,
        "weak_when_modern": exact
        and classification == "authentic-archaism"
        and _classification_from_source_text(text, default="standard") == "standard",
    }


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type IN ('table', 'view') AND name = ? LIMIT 1",
        (table,),
    ).fetchone()
    return row is not None


def _wiktionary_exact_hits(conn: sqlite3.Connection, term: str) -> list[dict[str, Any]]:
    hits = []
    for variant in _apostrophe_variants(term):
        rows = conn.execute(
            "SELECT id, word, definitions, text, source FROM wiktionary WHERE lower(word) = ? LIMIT 3",
            (variant,),
        ).fetchall()
        for row in rows:
            text = _clean_text(row["text"] or row["definitions"])
            hits.append(
                {
                    "classification": _classification_from_definition(text, default="standard"),
                    "attestation": {
                        "source": "wiktionary",
                        "ref": str(row["id"]),
                        "word": row["word"],
                        "detail": text,
                    },
                    "sovietization_risk": 0,
                }
            )
    return hits


def _classification_from_definition(text: str, *, default: str) -> str:
    classification = _classification_from_source_text(text, default=default)
    if classification == "borrowing" and default == "standard":
        return default
    return classification


def _classification_from_etymology(text: str, term: str, *, exact: bool) -> str:
    classification = _esum_headword_classification(text, term, exact=exact)
    if classification == "borrowing" and exact:
        return "borrowing"
    return classification


def _sum11_sovietization_risk(definition: str, text: str) -> int:
    try:
        from scripts.audit.sum11_sovietization_scan import classify_entry

        risk, _keywords = classify_entry(definition, text)
    except Exception:
        return 0
    return int(risk)


def _literary_surface_attestations(conn: sqlite3.Connection, term: str) -> list[dict[str, Any]]:
    hint = _SURFACE_QUOTE_HINTS.get(term)
    if hint:
        phrase, classification = hint
        rows = _verified_literary_quote_rows(conn, phrase)
        hits = []
        for row in rows:
            if phrase not in _normalize_quote(row["text"]):
                continue
            hits.append(
                {
                    "classification": classification,
                    "attestation": {
                        "source": "literary_fts",
                        "ref": row["chunk_id"],
                        "quote": phrase,
                        "score": 1.0,
                        "detail": _literary_ref_detail(row),
                    },
                }
            )
        if hits:
            return hits

    return _literary_term_hits(conn, term)


def _verified_literary_quote_rows(conn: sqlite3.Connection, phrase: str) -> list[sqlite3.Row]:
    query = _fts_phrase_query(phrase)
    rows: list[sqlite3.Row] = []
    if query:
        try:
            rows = conn.execute(
                """
                SELECT t.chunk_id, t.author, t.work, t.source_file, t.year, t.language_period, t.text
                FROM literary_fts f
                JOIN literary_texts t ON t.id = f.rowid
                WHERE literary_fts MATCH ?
                ORDER BY t.chunk_id
                LIMIT 50
                """,
                (query,),
            ).fetchall()
        except sqlite3.OperationalError:
            rows = []

    normalized_phrase = _normalize_quote(phrase)
    verified = [row for row in rows if normalized_phrase in _normalize_quote(row["text"])]
    if verified:
        return verified

    return conn.execute(
        """
        SELECT chunk_id, author, work, source_file, year, language_period, text
        FROM literary_texts
        WHERE lower(text) LIKE ?
        ORDER BY chunk_id
        LIMIT 50
        """,
        (f"%{normalized_phrase}%",),
    ).fetchall()


def _literary_term_hits(conn: sqlite3.Connection, term: str) -> list[dict[str, Any]]:
    query = _fts_phrase(term)
    if not query:
        return []
    try:
        rows = conn.execute(
            """
            SELECT t.chunk_id, t.author, t.work, t.source_file, t.year, t.language_period, t.text,
                   bm25(literary_fts) AS rank
            FROM literary_fts f
            JOIN literary_texts t ON t.id = f.rowid
            WHERE literary_fts MATCH ?
            ORDER BY rank
            LIMIT 10
            """,
            (query,),
        ).fetchall()
    except sqlite3.OperationalError:
        return []

    hits = []
    for row in rows:
        if not _contains_whole_token(str(row["text"]), term):
            continue
        hits.append(
            {
                "classification": _literary_classification(term, row),
                "attestation": {
                    "source": "literary_fts",
                    "ref": row["chunk_id"],
                    "quote": _snippet_around(str(row["text"]), term),
                    "score": 1.0,
                    "detail": _literary_ref_detail(row),
                },
            }
        )
    return hits[:3]


def _fts_phrase(term: str) -> str:
    if not re.fullmatch(r"[А-Яа-яЄєІіЇїҐґ'’ʼ-]+", term):
        return ""
    return '"' + term.replace('"', '""') + '"'


def _fts_phrase_query(text: str) -> str:
    tokens = re.findall(r"[А-Яа-яЄєІіЇїҐґA-Za-z0-9'’ʼ-]+", _normalize_word(text))
    if not tokens:
        return ""
    return '"' + " ".join(token.replace('"', '""') for token in tokens) + '"'


def _normalize_quote(text: object) -> str:
    return _SPACE_RE.sub(" ", _normalize_word(str(text))).strip(' .,;:!?«»"“”')


def _snippet_around(text: str, term: str, *, radius: int = 90) -> str:
    normalized_text = _normalize_word(text)
    idx = normalized_text.find(term)
    if idx < 0:
        return _clean_text(text, limit=220)
    start = max(0, idx - radius)
    end = min(len(text), idx + len(term) + radius)
    return _clean_text(text[start:end], limit=220)


def _literary_ref_detail(row: sqlite3.Row) -> str:
    pieces = [str(row[key] or "") for key in ("author", "work", "source_file") if row[key]]
    if row["year"]:
        pieces.append(str(row["year"]))
    if row["language_period"]:
        pieces.append(str(row["language_period"]))
    return "; ".join(pieces)


def _literary_classification(term: str, row: sqlite3.Row) -> str:
    period = str(row["language_period"] or "")
    if period in {"middle_ukrainian", "old_east_slavic"}:
        return "authentic-archaism"
    if term in _DIALECT_OR_FOLK_TERMS:
        return "dialect"
    return "standard"


def _form_default_classification(term: str) -> str:
    if term in _DIALECT_OR_FOLK_TERMS:
        return "dialect"
    return "standard"


def _russianism_status(
    term: str,
    *,
    russian_shadow: bool,
    vesum_attested: bool = False,
) -> dict[str, Any] | None:
    alternatives = _standard_alternatives(term)
    if not alternatives:
        return None
    attestations = [
        {
            "source": "standard_alternative",
            "ref": alternative,
            "detail": f"Ukrainian standard alternative for {term}",
        }
        for alternative in alternatives
    ]
    source = "heritage_spec"
    if _lt_alternatives(term):
        source = "lt_replacements"
    attestations.append(
        {
            "source": source,
            "ref": "docs/best-practices/heritage-attestation-engine.md",
            "detail": "local correction evidence; no authentic dictionary attestation found",
        }
    )
    return _status(
        "russianism",
        attestations,
        is_russianism=True,
        russian_shadow=russian_shadow,
        vesum_attested=vesum_attested,
        calque_warning={"standard_alternatives": alternatives},
        headword=term,
    )


def _standard_alternatives(term: str) -> list[str]:
    alternatives = list(_KNOWN_STANDARD_ALTERNATIVES.get(term, ()))
    for alternative in _lt_alternatives(term):
        if alternative not in alternatives:
            alternatives.append(alternative)
    return alternatives


def _lt_alternatives(term: str) -> list[str]:
    if not LT_REPLACEMENTS.exists():
        return []
    try:
        data = json.loads(LT_REPLACEMENTS.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    row = data.get(term)
    if not isinstance(row, dict):
        return []
    suggestions = row.get("suggestions")
    if not isinstance(suggestions, list):
        return []
    return [str(suggestion) for suggestion in suggestions[:5] if suggestion]


def _calque_warning(term: str, russian_shadow_detail: dict[str, Any]) -> dict[str, Any] | None:
    if russian_shadow_detail.get("matches_russian"):
        return {
            "type": "russian_shadow_only",
            "russian_lemma": russian_shadow_detail.get("russian_lemma"),
            "confidence": russian_shadow_detail.get("confidence"),
            "note": "negative signal only; no Ukrainian standard alternative was found",
        }
    return None


def _prefer_classification(current: str, candidate: str) -> str:
    priority = {
        "dialect": 80,
        "historism": 75,
        "authentic-archaism": 70,
        "borrowing": 60,
        "standard": 50,
        "calque": 45,
        "russianism": 40,
        "unknown": 0,
    }
    return candidate if priority.get(candidate, 0) > priority.get(current, 0) else current


def _merge_variant_statuses(statuses: list[dict[str, Any]], *, headword: str | None = None) -> dict[str, Any]:
    classification = "unknown"
    attestations: list[dict[str, Any]] = []
    calque_warning = None
    for status in statuses:
        if status["classification"] in _AUTHENTIC_CLASSIFICATIONS or status["classification"] == "calque":
            classification = _prefer_classification(classification, str(status["classification"]))
        elif classification == "unknown" and status["classification"] == "russianism":
            classification = "russianism"
        attestations.extend(status.get("attestations") or [])
        if not calque_warning and status.get("calque_warning"):
            calque_warning = status["calque_warning"]

    is_russianism = classification == "russianism" and all(status.get("is_russianism") for status in statuses)
    return _status(
        classification,
        attestations,
        is_russianism=is_russianism,
        russian_shadow=any(bool(status.get("russian_shadow")) for status in statuses),
        vesum_attested=any(bool(status.get("vesum_attested")) for status in statuses),
        sovietization_risk=max(int(status.get("sovietization_risk") or 0) for status in statuses),
        calque_warning=calque_warning,
        headword=headword,
    )


def _dedupe_attestations(attestations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[str, str]] = set()
    deduped = []
    for item in attestations:
        source = str(item.get("source") or "")
        ref = str(item.get("ref") or "")
        key = (source, ref)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped
