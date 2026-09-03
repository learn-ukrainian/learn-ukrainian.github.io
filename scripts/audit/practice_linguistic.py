"""Mechanical Practice Hub linguistic quality gate.

Pure library: injectable VesumVerifier, structured findings with rule_id +
item_id. Generator drops failing items; checker/publisher fail closed.

Identity uses NFC-casefold + apostrophe-normalized equality (same contract as
``czNorm`` / generate_practice_deck ``_plain``). Never raw ``form == lemmaId``.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

LINGUISTIC_GATE_VERSION = 1

LEADING_QUIZ_MARKER_RE = re.compile(r"^\s*[БГДЕҐ]\s+")
_WORD_RE = re.compile(r"[^\W_]+(?:[-'’ʼ][^\W_]+)*", re.UNICODE)

STRESS_MARK = "\u0301"
UKRAINIAN_VOWELS = frozenset("аеєиіїоуюяАЕЄИІЇОУЮЯ")

CASE_VESUM_TAGS = {
    "nominative": "v_naz",
    "genitive": "v_rod",
    "dative": "v_dav",
    "accusative": "v_zna",
    "instrumental": "v_oru",
    "locative": "v_mis",
    "vocative": "v_kly",
}
TAG_TO_CASE = {tag: case for case, tag in CASE_VESUM_TAGS.items()}
OBLIQUE_CASES = frozenset({"genitive", "dative", "accusative", "instrumental", "locative"})
NOM_VOC_CASES = frozenset({"nominative", "vocative"})
UK_CASE_TO_EN = {
    "називний": "nominative",
    "родовий": "genitive",
    "давальний": "dative",
    "знахідний": "accusative",
    "орудний": "instrumental",
    "місцевий": "locative",
    "кличний": "vocative",
}
INDECLINABLE_POS = frozenset({"adv", "prep", "part", "conj", "intj", "noninfl", "onomat"})

RULE_SOURCE_ATTESTED = "source_attested_blank"
RULE_AGREEMENT = "cloze_blank_context_agrees"
RULE_HOMOGRAPH = "identity_oblique_homograph"
RULE_PREP_NOM = "nominative_only_after_prep"
RULE_IDENTITY_LABEL = "identity_rule_consistency"
RULE_LEADING_QUIZ = "leading_quiz_marker"
RULE_STRESS = "stress_self_consistency"
RULE_PARADIGM_SLOT = "paradigm_declared_slot"
RULE_GOLD_LEMMA = "gold_lemma_match"


class VesumVerifier(Protocol):
    def verify_words(
        self,
        words: list[str],
        pos_filter: str | None = None,
    ) -> dict[str, list[dict[str, Any]]]:
        """Return VESUM matches keyed by submitted word form."""


@dataclass(frozen=True)
class Finding:
    rule_id: str
    item_id: str
    message: str

    def format(self) -> str:
        return f"{self.rule_id} [{self.item_id}]: {self.message}"


@dataclass(frozen=True)
class ClozeSourceRecord:
    key: str
    lemma_id: str
    form: str
    sentence: str  # blanked surface with exactly one ___
    original_sentence: str | None = None
    source_kind: str = "curated"


@dataclass
class ClozeSourceIndex:
    """Canonical join from emitted cloze → inventory/curated source row."""

    by_key: dict[str, ClozeSourceRecord]
    ambiguous_keys: frozenset[str]

    def get(self, key: str) -> ClozeSourceRecord | None:
        if key in self.ambiguous_keys:
            return None
        return self.by_key.get(key)


def plain(value: str) -> str:
    """NFC-casefold + apostrophe-normalized equality (czNorm / _plain)."""
    text = unicodedata.normalize("NFD", value)
    text = text.replace(STRESS_MARK, "").replace("́", "")
    text = unicodedata.normalize("NFC", text)
    return (
        text.casefold()
        .replace("’", "'")
        .replace("ʼ", "'")
        .replace("`", "'")
        .strip()
    )


def is_identity_form(form: str, lemma: str) -> bool:
    return bool(form) and bool(lemma) and plain(form) == plain(lemma)


def _clean(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    return text or None


def _surface_variants(value: str) -> tuple[str, ...]:
    return tuple(dict.fromkeys((value, value.casefold(), plain(value))))


def verified_surface_matches(
    form: str,
    verifier: VesumVerifier,
    pos_filter: str | None = None,
) -> list[dict[str, Any]]:
    matches: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for variant in _surface_variants(form):
        for match in verifier.verify_words([variant], pos_filter).get(variant, []):
            if not isinstance(match, dict):
                continue
            key = (
                str(match.get("lemma") or ""),
                str(match.get("pos") or ""),
                str(match.get("tags") or ""),
            )
            if key not in seen:
                seen.add(key)
                matches.append(match)
    if not matches and pos_filter:
        return verified_surface_matches(form, verifier)
    return matches


def match_cases(match: dict[str, Any]) -> set[str]:
    tokens = set(str(match.get("tags") or "").replace(":", " ").split())
    return {TAG_TO_CASE[tag] for tag in tokens if tag in TAG_TO_CASE}


def match_number(match: dict[str, Any]) -> str | None:
    tokens = set(str(match.get("tags") or "").replace(":", " ").split())
    if "p" in tokens:
        return "plural"
    if {"m", "f", "n"} & tokens:
        return "singular"
    return None


def normalize_case_name(value: str | None) -> str | None:
    if not value:
        return None
    key = value.strip()
    lower = key.casefold()
    if lower in CASE_VESUM_TAGS:
        return lower
    return UK_CASE_TO_EN.get(lower)


def cloze_source_key(
    *,
    lemma_id: str,
    provenance: dict[str, Any] | None,
    sentence: str | None = None,
    cloze_id: str | None = None,
) -> str | None:
    """Stable join key for inventory/curated cloze sources."""
    if cloze_id and ":inventory:" in cloze_id:
        return f"clozeId:{cloze_id}"
    if isinstance(provenance, dict):
        status = _clean(provenance.get("status")) or ""
        locator = _clean(provenance.get("locator"))
        path = _clean(provenance.get("path"))
        if status == "sentence_inventory" and locator:
            return f"inventory:{plain(lemma_id)}:{locator}"
        if status and path and locator:
            return f"curated:{plain(lemma_id)}:{status}:{path}:{locator}"
        if status and path and sentence:
            return f"curated:{plain(lemma_id)}:{status}:{path}:{plain(sentence)}"
    if cloze_id:
        return f"clozeId:{cloze_id}"
    if sentence:
        return f"sentence:{plain(lemma_id)}:{plain(sentence)}"
    return None


def _blank_sentence(sentence: str, target_form: str) -> str | None:
    dash = r"\-\u2010\u2011\u2012\u2013\u2014\u2015"
    pattern = re.compile(
        rf"(?<![\wʼ'’{dash}]){re.escape(target_form)}(?![\wʼ'’{dash}])"
    )
    blanked, count = pattern.subn("___", sentence)
    if count != 1:
        return None
    return blanked


def build_cloze_source_index(
    inventory_rows: list[dict[str, Any]] | None = None,
    curated_rows: list[dict[str, Any]] | None = None,
    *,
    inventory_path: str | None = None,
) -> ClozeSourceIndex:
    """Build a fail-closed join index from independent source rows."""
    by_key: dict[str, ClozeSourceRecord] = {}
    ambiguous: set[str] = set()

    def _add(key: str | None, record: ClozeSourceRecord) -> None:
        if not key:
            return
        existing = by_key.get(key)
        if existing is None:
            by_key[key] = record
            return
        if (
            plain(existing.form) != plain(record.form)
            or plain(existing.sentence) != plain(record.sentence)
        ):
            ambiguous.add(key)
            by_key.pop(key, None)

    for index, row in enumerate(inventory_rows or []):
        if not isinstance(row, dict):
            continue
        uses = row.get("uses")
        if isinstance(uses, list) and "example" not in uses:
            continue
        lemma_id = _clean(row.get("lemmaId"))
        sentence = _clean(row.get("sentence"))
        target = _clean(row.get("targetForm"))
        if not lemma_id or not sentence or not target:
            continue
        blanked = _blank_sentence(sentence, target)
        if blanked is None:
            continue
        provenance = row.get("provenance")
        if not isinstance(provenance, dict):
            provenance = {}
        cloze_id = f"{lemma_id}:inventory:{index + 1}"
        # Prefer locator join; also index clozeId for emit-time candidates that
        # keep the generator's inventory numbering after prefer-filter.
        locator = _clean(provenance.get("locator"))
        record = ClozeSourceRecord(
            key="",
            lemma_id=lemma_id,
            form=target,
            sentence=blanked,
            original_sentence=sentence,
            source_kind="sentence_inventory",
        )
        if locator:
            key = f"inventory:{plain(lemma_id)}:{locator}"
            record = ClozeSourceRecord(
                key=key,
                lemma_id=lemma_id,
                form=target,
                sentence=blanked,
                original_sentence=sentence,
                source_kind="sentence_inventory",
            )
            _add(key, record)
        # Path-based inventory provenance used by read_sentence_inventory.
        if inventory_path:
            path_key = cloze_source_key(
                lemma_id=lemma_id,
                provenance={
                    "status": "sentence_inventory",
                    "path": inventory_path,
                    "locator": locator,
                },
                sentence=blanked,
                cloze_id=cloze_id,
            )
            _add(
                path_key,
                ClozeSourceRecord(
                    key=path_key or "",
                    lemma_id=lemma_id,
                    form=target,
                    sentence=blanked,
                    original_sentence=sentence,
                    source_kind="sentence_inventory",
                ),
            )

    for row in curated_rows or []:
        if not isinstance(row, dict):
            continue
        if row.get("sourceType") == "sentence_inventory":
            # Already covered when inventory rows were supplied; emit-time
            # candidates still join via clozeId / locator below.
            lemma_id = _clean(row.get("lemmaId"))
            form = _clean(row.get("form"))
            sentence = _clean(row.get("sentence"))
            cloze_id = _clean(row.get("clozeId"))
            provenance = row.get("provenance") if isinstance(row.get("provenance"), dict) else {}
            if not lemma_id or not form or not sentence:
                continue
            key = cloze_source_key(
                lemma_id=lemma_id,
                provenance=provenance,
                sentence=sentence,
                cloze_id=cloze_id,
            )
            _add(
                key,
                ClozeSourceRecord(
                    key=key or "",
                    lemma_id=lemma_id,
                    form=form,
                    sentence=sentence,
                    original_sentence=_clean(row.get("originalSentence")),
                    source_kind="sentence_inventory",
                ),
            )
            continue
        lemma_id = _clean(row.get("lemmaId"))
        form = _clean(row.get("form"))
        sentence = _clean(row.get("sentence"))
        if not lemma_id or not form or not sentence:
            continue
        provenance = row.get("provenance") if isinstance(row.get("provenance"), dict) else {}
        cloze_id = _clean(row.get("clozeId"))
        key = cloze_source_key(
            lemma_id=lemma_id,
            provenance=provenance,
            sentence=sentence,
            cloze_id=cloze_id,
        )
        _add(
            key,
            ClozeSourceRecord(
                key=key or "",
                lemma_id=lemma_id,
                form=form,
                sentence=sentence,
                source_kind="curated",
            ),
        )

    return ClozeSourceIndex(by_key=by_key, ambiguous_keys=frozenset(ambiguous))


def index_from_generator_candidates(
    candidates: list[dict[str, Any]],
) -> ClozeSourceIndex:
    """Index already-normalized generator cloze candidates (inventory + curated)."""
    return build_cloze_source_index(curated_rows=candidates)


def _load_agreement_checker() -> Any:
    import importlib.util
    import sys

    name = "practice_linguistic._morphological_validator"
    if name in sys.modules:
        return sys.modules[name]
    path = Path(__file__).resolve().parent / "checks" / "morphological_validator.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def cloze_blank_context_agrees(
    sentence: str,
    form: str,
    verifier: VesumVerifier,
) -> bool:
    """Adj–noun agreement at the blank (same scope as generate_practice_deck)."""
    validator = _load_agreement_checker()
    agreement_skip = validator._AGREEMENT_SKIP
    check_agreement = validator.check_agreement
    before_blank = sentence.split("___", 1)[0]
    previous_tokens = _WORD_RE.findall(before_blank)
    if not previous_tokens:
        return True
    previous = previous_tokens[-1]
    previous_key = unicodedata.normalize(
        "NFC",
        unicodedata.normalize("NFD", previous).replace(STRESS_MARK, ""),
    ).lower()
    form_key = unicodedata.normalize(
        "NFC",
        unicodedata.normalize("NFD", form).replace(STRESS_MARK, ""),
    ).lower()
    if previous_key in agreement_skip or form_key in agreement_skip:
        return True
    vesum_results = {
        previous_key: verified_surface_matches(previous, verifier),
        form_key: verified_surface_matches(form, verifier),
    }
    pair_line = f"{previous} {form}"
    word_lines = [(previous, 1, pair_line), (form, 1, pair_line)]
    return not check_agreement(word_lines, vesum_results, max_issues=1)


def _target_lemma_plain(item: dict[str, Any], lemma_plain: str | None = None) -> str:
    if lemma_plain:
        return plain(lemma_plain)
    for key in ("lemma", "lemmaId"):
        value = _clean(item.get(key))
        if value:
            return plain(value)
    return ""


def _item_id(item: dict[str, Any], fallback: str) -> str:
    for key in ("clozeId", "stressId", "paradigmId", "heritageId", "paronymId", "antonymId", "homonymId"):
        value = _clean(item.get(key))
        if value:
            return value
    return fallback


def _is_indeclinable_matches(matches: list[dict[str, Any]]) -> bool:
    if not matches:
        return False
    saw_case = False
    for match in matches:
        tags = str(match.get("tags") or "")
        tokens = set(tags.replace(":", " ").split())
        if "nv_noninfl" in tokens or "noninfl" in tokens:
            return True
        pos = str(match.get("pos") or "").casefold()
        if pos in INDECLINABLE_POS:
            return True
        if match_cases(match):
            saw_case = True
    return not saw_case


def _previous_token(sentence: str) -> str | None:
    before = sentence.split("___", 1)[0]
    tokens = _WORD_RE.findall(before)
    return tokens[-1] if tokens else None


def _is_vesum_prep(token: str, verifier: VesumVerifier) -> bool:
    for match in verified_surface_matches(token, verifier):
        pos = str(match.get("pos") or "").casefold()
        tags = str(match.get("tags") or "")
        if pos == "prep" or "prep" in tags.split(":"):
            return True
    return False


def check_leading_quiz(item_id: str, text: str | None) -> list[Finding]:
    if not text:
        return []
    if LEADING_QUIZ_MARKER_RE.match(text):
        return [
            Finding(
                RULE_LEADING_QUIZ,
                item_id,
                f"learner-facing text starts with a quiz letter marker: {text[:24]!r}",
            )
        ]
    return []


def check_source_attested_blank(
    item: dict[str, Any],
    source_index: ClozeSourceIndex | None,
    *,
    item_id: str,
) -> list[Finding]:
    if source_index is None:
        return []
    lemma_id = _clean(item.get("lemmaId")) or ""
    provenance = item.get("provenance") if isinstance(item.get("provenance"), dict) else {}
    sentence = _clean(item.get("sentence"))
    form = _clean(item.get("form"))
    cloze_id = _clean(item.get("clozeId"))
    key = cloze_source_key(
        lemma_id=lemma_id,
        provenance=provenance,
        sentence=sentence,
        cloze_id=cloze_id,
    )
    if key is None:
        return [
            Finding(
                RULE_SOURCE_ATTESTED,
                item_id,
                "missing stable source join key",
            )
        ]
    if key in source_index.ambiguous_keys:
        return [
            Finding(
                RULE_SOURCE_ATTESTED,
                item_id,
                f"ambiguous source join key {key!r}",
            )
        ]
    record = source_index.get(key)
    if record is None:
        return [
            Finding(
                RULE_SOURCE_ATTESTED,
                item_id,
                f"no source row for join key {key!r}",
            )
        ]
    findings: list[Finding] = []
    if not form or plain(form) != plain(record.form):
        findings.append(
            Finding(
                RULE_SOURCE_ATTESTED,
                item_id,
                f"gold form {form!r} != source surface {record.form!r}",
            )
        )
    if not sentence or sentence != record.sentence:
        findings.append(
            Finding(
                RULE_SOURCE_ATTESTED,
                item_id,
                "blanked sentence does not match source surface",
            )
        )
    return findings


def check_identity_rule_consistency(
    item: dict[str, Any],
    *,
    item_id: str,
    lemma_plain: str | None = None,
) -> list[Finding]:
    form = _clean(item.get("form")) or ""
    lemma = _target_lemma_plain(item, lemma_plain)
    if not form or not lemma:
        return []
    identity = is_identity_form(form, lemma)
    case_rule = item.get("caseRule") if isinstance(item.get("caseRule"), dict) else {}
    rule_id = _clean(case_rule.get("ruleId"))
    blank_case = normalize_case_name(_clean(item.get("blankCase")))
    rule_case = normalize_case_name(_clean(case_rule.get("case")))
    findings: list[Finding] = []
    if identity and rule_id != "nominative_identification":
        findings.append(
            Finding(
                RULE_IDENTITY_LABEL,
                item_id,
                f"normalized identity form requires nominative_identification, got {rule_id!r}",
            )
        )
    if rule_id == "nominative_identification" and not identity:
        findings.append(
            Finding(
                RULE_IDENTITY_LABEL,
                item_id,
                "nominative_identification requires normalized identity form==lemma",
            )
        )
    if identity or rule_id == "nominative_identification":
        if blank_case not in (None, "nominative"):
            findings.append(
                Finding(
                    RULE_IDENTITY_LABEL,
                    item_id,
                    f"identity cloze blankCase must be nominative, got {blank_case!r}",
                )
            )
        if rule_case not in (None, "nominative"):
            findings.append(
                Finding(
                    RULE_IDENTITY_LABEL,
                    item_id,
                    f"identity cloze caseRule.case must be nominative, got {rule_case!r}",
                )
            )
        feedback = _clean(case_rule.get("feedback")) or ""
        if "називний" in feedback.casefold():
            findings.append(
                Finding(
                    RULE_IDENTITY_LABEL,
                    item_id,
                    "identity feedback must use словникова форма, never називний",
                )
            )
    return findings


def check_homograph_oblique(
    item: dict[str, Any],
    verifier: VesumVerifier,
    *,
    item_id: str,
    lemma_plain: str | None = None,
) -> list[Finding]:
    form = _clean(item.get("form")) or ""
    target = _target_lemma_plain(item, lemma_plain)
    if not form or not target or not is_identity_form(form, target):
        return []
    matches = verified_surface_matches(form, verifier)
    target_matches = [m for m in matches if plain(str(m.get("lemma") or "")) == target]
    target_cases: set[str] = set()
    for match in target_matches:
        target_cases |= match_cases(match)
    # Indeclinable / adverb identity (no case tags on target) stays.
    if not target_cases:
        return []
    other_oblique = False
    for match in matches:
        other = plain(str(match.get("lemma") or ""))
        if not other or other == target:
            continue
        if match_cases(match) & OBLIQUE_CASES:
            other_oblique = True
            break
    if other_oblique and target_cases <= NOM_VOC_CASES:
        return [
            Finding(
                RULE_HOMOGRAPH,
                item_id,
                "identity surface is an oblique form of a different VESUM lemma",
            )
        ]
    return []


def check_nominative_only_after_prep(
    item: dict[str, Any],
    verifier: VesumVerifier,
    *,
    item_id: str,
    lemma_plain: str | None = None,
) -> list[Finding]:
    form = _clean(item.get("form")) or ""
    sentence = _clean(item.get("sentence")) or ""
    target = _target_lemma_plain(item, lemma_plain)
    if not form or not sentence or "___" not in sentence:
        return []
    previous = _previous_token(sentence)
    if not previous or not _is_vesum_prep(previous, verifier):
        return []
    matches = verified_surface_matches(form, verifier)
    target_matches = [
        m for m in matches if plain(str(m.get("lemma") or "")) == target
    ] or matches
    if _is_indeclinable_matches(target_matches):
        return []
    target_cases: set[str] = set()
    for match in target_matches:
        if target and plain(str(match.get("lemma") or "")) != target:
            continue
        target_cases |= match_cases(match)
    if target_cases and target_cases <= NOM_VOC_CASES:
        return [
            Finding(
                RULE_PREP_NOM,
                item_id,
                f"nominative/vocative-only form after preposition {previous!r}",
            )
        ]
    return []


def check_gold_lemma(
    item: dict[str, Any],
    verifier: VesumVerifier,
    *,
    item_id: str,
    lemma_plain: str | None = None,
) -> list[Finding]:
    form = _clean(item.get("form")) or ""
    target = _target_lemma_plain(item, lemma_plain)
    if not form or not target:
        return []
    matches = verified_surface_matches(form, verifier)
    target_matches = [m for m in matches if plain(str(m.get("lemma") or "")) == target]
    if not target_matches:
        return [
            Finding(
                RULE_GOLD_LEMMA,
                item_id,
                f"gold {form!r} has no VESUM analysis for lemma {target!r}",
            )
        ]
    identity = is_identity_form(form, target)
    if identity:
        return []
    blank_case = normalize_case_name(_clean(item.get("blankCase")))
    if not blank_case:
        return []
    if not any(blank_case in match_cases(match) for match in target_matches):
        return [
            Finding(
                RULE_GOLD_LEMMA,
                item_id,
                f"gold {form!r} has no {blank_case} analysis for lemma {target!r}",
            )
        ]
    return []


def check_cloze_item(
    item: dict[str, Any],
    verifier: VesumVerifier,
    *,
    source_index: ClozeSourceIndex | None = None,
    lemma_plain: str | None = None,
    check_agreement: bool = True,
) -> list[Finding]:
    item_id = _item_id(item, "cloze")
    findings: list[Finding] = []
    findings.extend(check_source_attested_blank(item, source_index, item_id=item_id))
    findings.extend(
        check_identity_rule_consistency(item, item_id=item_id, lemma_plain=lemma_plain)
    )
    findings.extend(check_leading_quiz(item_id, _clean(item.get("sentence"))))
    findings.extend(
        check_homograph_oblique(item, verifier, item_id=item_id, lemma_plain=lemma_plain)
    )
    findings.extend(
        check_nominative_only_after_prep(
            item, verifier, item_id=item_id, lemma_plain=lemma_plain
        )
    )
    findings.extend(
        check_gold_lemma(item, verifier, item_id=item_id, lemma_plain=lemma_plain)
    )
    if check_agreement:
        sentence = _clean(item.get("sentence")) or ""
        form = _clean(item.get("form")) or ""
        if sentence and form and not cloze_blank_context_agrees(sentence, form, verifier):
            findings.append(
                Finding(
                    RULE_AGREEMENT,
                    item_id,
                    "adj–noun agreement fails at the blank",
                )
            )
    return findings


def _strip_stress(value: str) -> str:
    return unicodedata.normalize(
        "NFC",
        unicodedata.normalize("NFD", value).replace(STRESS_MARK, ""),
    )


def _stress_position(stressed: str) -> tuple[str, int | None]:
    nfd = unicodedata.normalize("NFD", stressed)
    if nfd.count(STRESS_MARK) != 1:
        return (_strip_stress(stressed), None)
    prefix, _suffix = nfd.split(STRESS_MARK, 1)
    prefix_nfc = unicodedata.normalize("NFC", prefix)
    if not prefix_nfc:
        return (_strip_stress(stressed), None)
    return (_strip_stress(stressed), len(prefix_nfc) - 1)


def _vowel_nuclei(value: str) -> list[dict[str, Any]]:
    return [
        {"index": index, "label": char}
        for index, char in enumerate(value)
        if char in UKRAINIAN_VOWELS
    ]


def check_stress_item(item: dict[str, Any]) -> list[Finding]:
    item_id = _item_id(item, "stress")
    stressed = _clean(item.get("stressed")) or ""
    unstressed = _clean(item.get("unstressed")) or ""
    lemma = _clean(item.get("lemma")) or _clean(item.get("lemmaId")) or ""
    findings: list[Finding] = []
    if not stressed:
        return [Finding(RULE_STRESS, item_id, "missing stressed form")]
    recomputed_unstressed, stress_index = _stress_position(stressed)
    nuclei = _vowel_nuclei(recomputed_unstressed)
    if stress_index is None:
        findings.append(
            Finding(RULE_STRESS, item_id, "stressed form must carry exactly one acute")
        )
    if len(nuclei) < 2:
        findings.append(
            Finding(RULE_STRESS, item_id, "stress item needs at least two vowel nuclei")
        )
    if stress_index is not None and sum(1 for n in nuclei if n["index"] == stress_index) != 1:
        findings.append(
            Finding(RULE_STRESS, item_id, "stressIndex must land on exactly one nucleus")
        )
    if unstressed != recomputed_unstressed:
        findings.append(
            Finding(
                RULE_STRESS,
                item_id,
                f"unstressed {unstressed!r} != recomputed {recomputed_unstressed!r}",
            )
        )
    stored_index = item.get("stressIndex")
    if stress_index is not None and stored_index != stress_index:
        findings.append(
            Finding(
                RULE_STRESS,
                item_id,
                f"stressIndex {stored_index!r} != recomputed {stress_index!r}",
            )
        )
    stored_nuclei = item.get("nuclei")
    if not isinstance(stored_nuclei, list) or stored_nuclei != nuclei:
        findings.append(
            Finding(RULE_STRESS, item_id, "nuclei do not match recomputed vowel nuclei")
        )
    if lemma and plain(recomputed_unstressed) != plain(lemma):
        findings.append(
            Finding(
                RULE_STRESS,
                item_id,
                f"unstressed form does not match lemma {lemma!r}",
            )
        )
    return findings


def check_paradigm_item(
    item: dict[str, Any],
    verifier: VesumVerifier,
    *,
    lemma_plain: str | None = None,
) -> list[Finding]:
    item_id = _item_id(item, "paradigm")
    form = _clean(item.get("form")) or ""
    target = _target_lemma_plain(item, lemma_plain)
    slot = item.get("slot") if isinstance(item.get("slot"), dict) else {}
    case_name = normalize_case_name(_clean(slot.get("case")))
    number = _clean(slot.get("number"))
    if number not in {"singular", "plural"}:
        number = None
    if not form or not target or not case_name or not number:
        return [
            Finding(
                RULE_PARADIGM_SLOT,
                item_id,
                "paradigm item missing form/lemma/case/number",
            )
        ]
    matches = verified_surface_matches(form, verifier)
    target_matches = [m for m in matches if plain(str(m.get("lemma") or "")) == target]
    if not target_matches:
        return [
            Finding(
                RULE_PARADIGM_SLOT,
                item_id,
                f"answer {form!r} is not a VESUM form of {target!r}",
            )
        ]
    for match in target_matches:
        cases = match_cases(match)
        match_num = match_number(match)
        if case_name in cases and (match_num is None or match_num == number):
            return []
    return [
        Finding(
            RULE_PARADIGM_SLOT,
            item_id,
            f"answer {form!r} does not match declared slot {case_name}/{number}",
        )
    ]


def check_mode_prompts(mode: str, item: dict[str, Any]) -> list[Finding]:
    item_id = _item_id(item, mode)
    findings: list[Finding] = []
    for field in ("sentence", "prompt", "sentence_with_slot"):
        findings.extend(check_leading_quiz(item_id, _clean(item.get(field))))
    return findings


def audit_cloze_items(
    items: list[dict[str, Any]],
    verifier: VesumVerifier,
    *,
    source_index: ClozeSourceIndex | None = None,
    lexeme_plain_by_id: dict[str, str] | None = None,
) -> list[Finding]:
    findings: list[Finding] = []
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            continue
        lemma_id = _clean(item.get("lemmaId"))
        lemma_plain = None
        if lexeme_plain_by_id and lemma_id:
            lemma_plain = lexeme_plain_by_id.get(lemma_id)
        findings.extend(
            check_cloze_item(
                item,
                verifier,
                source_index=source_index,
                lemma_plain=lemma_plain,
            )
        )
        if not findings and index < 0:  # pragma: no cover - keeps enumerate used
            pass
    return findings


def audit_practice_payloads(
    *,
    cloze_items: list[dict[str, Any]] | None = None,
    stress_items: list[dict[str, Any]] | None = None,
    paradigm_items: list[dict[str, Any]] | None = None,
    heritage_items: list[dict[str, Any]] | None = None,
    paronym_items: list[dict[str, Any]] | None = None,
    antonym_items: list[dict[str, Any]] | None = None,
    homonym_items: list[dict[str, Any]] | None = None,
    verifier: VesumVerifier,
    source_index: ClozeSourceIndex | None = None,
    lexeme_plain_by_id: dict[str, str] | None = None,
) -> list[Finding]:
    findings: list[Finding] = []
    for item in cloze_items or []:
        if not isinstance(item, dict):
            continue
        lemma_id = _clean(item.get("lemmaId"))
        lemma_plain = lexeme_plain_by_id.get(lemma_id) if lexeme_plain_by_id and lemma_id else None
        findings.extend(
            check_cloze_item(
                item,
                verifier,
                source_index=source_index,
                lemma_plain=lemma_plain,
            )
        )
    for item in stress_items or []:
        if isinstance(item, dict):
            findings.extend(check_stress_item(item))
    for item in paradigm_items or []:
        if not isinstance(item, dict):
            continue
        lemma_id = _clean(item.get("lemmaId"))
        lemma_plain = lexeme_plain_by_id.get(lemma_id) if lexeme_plain_by_id and lemma_id else None
        findings.extend(check_paradigm_item(item, verifier, lemma_plain=lemma_plain))
    for mode, items in (
        ("heritage", heritage_items),
        ("paronym", paronym_items),
        ("antonym", antonym_items),
        ("homonym", homonym_items),
    ):
        for item in items or []:
            if isinstance(item, dict):
                findings.extend(check_mode_prompts(mode, item))
    return findings


def format_findings(findings: list[Finding], *, limit: int = 20) -> str:
    lines = [finding.format() for finding in findings[:limit]]
    if len(findings) > limit:
        lines.append(f"... and {len(findings) - limit} more")
    return "; ".join(lines)
