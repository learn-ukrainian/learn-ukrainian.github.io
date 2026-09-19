#!/usr/bin/env python3
"""Unified Quality Gate for Practice Hub datasets and decks (Issues #7944, #8276).

Audits active Practice Hub assets:
1. Teacher Cloze deck (site/src/data/lexicon-teacher-cloze.json)
2. Textbook Error Correction drills (data/practice/textbook-error-corrections.json)
3. Lexicon Sentence Inventory (site/src/data/lexicon-sentence-inventory.json)
4. Practice Deck Shards across all modes (site/public/lexicon/practice-*.json)

Enforces:
- Exact 1-blank integrity (_____) for fill-in modes (cloze, paronym, homonym, heritage, antonym, imperative)
- Distractor uniqueness and non-empty options (>= 2 options, no duplicate labels except homonyms)
- Answer alignment with blank/target and presence in options list
- Required pedagogical metadata (distinction gloss, rationale, case rule, grammatical notes)
- Intentional error quarantine (no leaked contrastive tables/headers in positive cloze)
- Error-correction drill integrity (substring containment, option validity, explanation)
- 100% morphological attestation against VESUM
- Thin-mode densification thresholds: paronym >= 250, homonym >= 150, heritage >= 250
- TypeSafe System One (Jev 1.13) target exclusivity and distractor plausibility validation
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(PROJECT_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

try:
    from scripts.verification.vesum import verify_word
except ImportError:
    from verification.vesum import verify_word

try:
    from scripts.rag.config import VESUM_DB_PATH as DEFAULT_VESUM_DB
except ImportError:
    try:
        from rag.config import VESUM_DB_PATH as DEFAULT_VESUM_DB
    except ImportError:
        DEFAULT_VESUM_DB = PROJECT_ROOT / "data/vesum.db"

try:
    from scripts.audit.practice_linguistic import INTENTIONAL_ERROR_PATTERNS
except ImportError:
    from practice_linguistic import INTENTIONAL_ERROR_PATTERNS

DEFAULT_TEACHER_CLOZE = PROJECT_ROOT / "site/src/data/lexicon-teacher-cloze.json"
DEFAULT_ERROR_CORRECTIONS = PROJECT_ROOT / "data/practice/textbook-error-corrections.json"
DEFAULT_SENTENCE_INVENTORY = PROJECT_ROOT / "site/src/data/lexicon-sentence-inventory.json"
DEFAULT_SHARDS_DIR = PROJECT_ROOT / "site/public/lexicon"

VOLUME_THRESHOLDS = {
    "paronym": 250,
    "homonym": 150,
    "heritage": 250,
}

ALL_PRACTICE_MODES = (
    "antonym",
    "classify",
    "cloze",
    "heritage",
    "homonym",
    "imperative",
    "paradigm",
    "paronym",
    "stress",
    "synonym",
)

BLANK_MODES = ("cloze", "paronym", "homonym", "heritage", "antonym", "imperative")

_BLANK_RE = re.compile(r"_{3,}")
_INTENTIONAL_ERROR_PATTERNS = INTENTIONAL_ERROR_PATTERNS
_CYRILLIC_WORD_RE = re.compile(r"^[а-яіїєґА-ЯІЇЄҐ'\-]+$")


def _normalize_plain(text: str) -> str:
    """Casefold, strip stress/accent marks, and normalize apostrophes.

    Preserves Ukrainian letters such as 'ї' and distinguishing letters such as 'ё'.
    """
    clean = text.replace("\u0301", "").replace("\u0300", "").replace("\u0341", "")
    return clean.casefold().replace("’", "'").replace("ʼ", "'").replace("`", "'").strip()


def check_word_in_vesum(word: str, db_path: Path | str | None = None) -> bool:
    """Check if word form exists in VESUM with normalization."""
    clean = word.strip().strip(".,!?:;—…\"'«»`()[]")
    clean = clean.replace("\u0301", "").replace("\u0300", "").replace("\u0341", "")
    if not clean or not _CYRILLIC_WORD_RE.match(clean):
        return True  # Skip Latin words, abbreviations, symbols

    clean = clean.replace("’", "'").replace("ʼ", "'").replace("`", "'")
    # Exact check
    if verify_word(clean, db_path=db_path) or verify_word(clean.lower(), db_path=db_path):
        return True

    # Check hyphenated syllable breakdown: ро-бот -> робот
    if "-" in clean:
        dehyphen = clean.replace("-", "")
        if verify_word(dehyphen, db_path=db_path) or verify_word(dehyphen.lower(), db_path=db_path):
            return True
        # Compound words (e.g. бізнес-леді, слово-асоціація): check individual parts
        parts = clean.split("-")
        if all(verify_word(p, db_path=db_path) or verify_word(p.lower(), db_path=db_path) for p in parts if len(p) > 2):
            return True

    return False


def audit_teacher_cloze_deck(path: Path | str, vesum_db: Path | str | None = DEFAULT_VESUM_DB) -> list[dict[str, Any]]:
    """Audit teacher cloze deck for structural, linguistic and quarantine integrity."""
    violations: list[dict[str, Any]] = []
    p = Path(path)
    if not p.exists():
        return [{"type": "FILE_MISSING", "item": str(p), "message": f"File {p} does not exist"}]

    with open(p, encoding="utf-8") as f:
        data = json.load(f)

    items = data.get("cloze", []) if isinstance(data, dict) else data
    seen_ids: set[str] = set()

    for idx, item in enumerate(items, 1):
        cid = item.get("clozeId") or f"row_{idx}"
        if not cid or cid in seen_ids:
            violations.append(
                {
                    "type": "DUPLICATE_OR_EMPTY_ID",
                    "item": cid,
                    "message": f"Cloze item {idx} has duplicate or missing ID: {cid}",
                }
            )
        seen_ids.add(cid)

        sentence = item.get("sentence", "")
        blanks = _BLANK_RE.findall(sentence)
        if len(blanks) != 1:
            violations.append(
                {
                    "type": "INVALID_BLANK_COUNT",
                    "item": cid,
                    "message": f"Sentence must contain exactly 1 blank (found {len(blanks)}): {sentence[:60]!r}",
                }
            )

        for pattern in _INTENTIONAL_ERROR_PATTERNS:
            m = pattern.search(sentence)
            if m:
                violations.append(
                    {
                        "type": "INTENTIONAL_ERROR_LEAK",
                        "item": cid,
                        "message": f"Sentence contains intentional error marker {m.group(0)!r}: {sentence[:60]!r}",
                    }
                )
                break

        options = item.get("options", [])
        if not options or len(options) < 2:
            violations.append(
                {
                    "type": "TOO_FEW_OPTIONS",
                    "item": cid,
                    "message": f"Item has fewer than 2 options: {options}",
                }
            )
        else:
            labels = []
            answer_count = 0
            for opt in options:
                if isinstance(opt, dict):
                    lbl = opt.get("label", "")
                    if opt.get("kind") == "answer":
                        answer_count += 1
                else:
                    lbl = str(opt)
                labels.append(_normalize_plain(lbl))

            if len(set(labels)) != len(labels):
                violations.append(
                    {
                        "type": "DUPLICATE_OPTIONS",
                        "item": cid,
                        "message": f"Options contain duplicates: {labels}",
                    }
                )

            if isinstance(options[0], dict) and answer_count != 1:
                violations.append(
                    {
                        "type": "WRONG_ANSWER_COUNT",
                        "item": cid,
                        "message": f"Expected exactly 1 answer option, got {answer_count}",
                    }
                )

        form = item.get("form", "")
        if vesum_db and form and Path(vesum_db).exists() and not check_word_in_vesum(form, db_path=vesum_db):
            violations.append(
                {
                    "type": "VESUM_UNATTESTED",
                    "item": cid,
                    "message": f"Target form {form!r} is not attested in VESUM",
                }
            )

    return violations


def audit_error_correction_deck(
    path: Path | str, vesum_db: Path | str | None = DEFAULT_VESUM_DB
) -> list[dict[str, Any]]:
    """Audit error-correction dataset for schema, substring match, and pedagogical validity."""
    violations: list[dict[str, Any]] = []
    p = Path(path)
    if not p.exists():
        return [{"type": "FILE_MISSING", "item": str(p), "message": f"File {p} does not exist"}]

    with open(p, encoding="utf-8") as f:
        data = json.load(f)

    items = data.get("drills") or data.get("items") or data.get("corrections") or [] if isinstance(data, dict) else data

    seen_ids: set[str] = set()
    for idx, item in enumerate(items, 1):
        if not isinstance(item, dict):
            continue
        item_id = item.get("id") or f"drill_{idx}"
        if not item_id or item_id in seen_ids:
            violations.append(
                {
                    "type": "DUPLICATE_OR_EMPTY_ID",
                    "item": item_id,
                    "message": f"Item {idx} has duplicate or missing ID: {item_id}",
                }
            )
        seen_ids.add(item_id)

        sentence = item.get("sentence", "")
        error_target = item.get("errorWord") or item.get("errorTarget", "")
        correct_target = item.get("correctForm") or item.get("correctTarget", "")

        if not sentence:
            violations.append({"type": "EMPTY_SENTENCE", "item": item_id, "message": "Sentence is empty"})
        elif error_target not in sentence:
            violations.append(
                {
                    "type": "ERROR_TARGET_NOT_IN_SENTENCE",
                    "item": item_id,
                    "message": f"errorTarget {error_target!r} not found in sentence {sentence!r}",
                }
            )

        if not correct_target:
            violations.append({"type": "EMPTY_CORRECT_TARGET", "item": item_id, "message": "correctTarget is empty"})
        elif _normalize_plain(error_target) == _normalize_plain(correct_target):
            violations.append(
                {
                    "type": "IDENTICAL_TARGETS",
                    "item": item_id,
                    "message": f"errorTarget and correctTarget are identical: {correct_target!r}",
                }
            )

        options = item.get("options", [])
        if not options or len(options) < 2:
            violations.append(
                {
                    "type": "TOO_FEW_OPTIONS",
                    "item": item_id,
                    "message": f"options list must contain at least 2 items (got {len(options)})",
                }
            )
        else:
            opt_plain = [_normalize_plain(o) for o in options]
            if len(set(opt_plain)) != len(opt_plain):
                violations.append(
                    {
                        "type": "DUPLICATE_OPTIONS",
                        "item": item_id,
                        "message": f"Duplicate options found: {options}",
                    }
                )
            if _normalize_plain(correct_target) not in opt_plain:
                violations.append(
                    {
                        "type": "CORRECT_TARGET_MISSING_IN_OPTIONS",
                        "item": item_id,
                        "message": f"correctTarget {correct_target!r} not in options {options}",
                    }
                )

        explanation = item.get("explanation", "")
        if not explanation or not explanation.strip():
            violations.append(
                {
                    "type": "MISSING_EXPLANATION",
                    "item": item_id,
                    "message": "Pedagogical explanation is missing or empty",
                }
            )

        if vesum_db and correct_target and Path(vesum_db).exists():
            clean_correct = correct_target.strip().strip(".,!?:;—…\"'«»`")
            if (
                " " not in clean_correct
                and not clean_correct.isupper()
                and len(clean_correct) > 2
                and not check_word_in_vesum(clean_correct, db_path=vesum_db)
            ):
                violations.append(
                    {
                        "type": "VESUM_UNATTESTED",
                        "item": item_id,
                        "message": f"correctTarget {clean_correct!r} not found in VESUM",
                    }
                )

    return violations


def audit_sentence_inventory(path: Path | str) -> list[dict[str, Any]]:
    """Audit sentence inventory for intentional error leaks."""
    violations: list[dict[str, Any]] = []
    p = Path(path)
    if not p.exists():
        return []

    with open(p, encoding="utf-8") as f:
        data = json.load(f)

    rows = data.get("rows", []) if isinstance(data, dict) else data
    for idx, r in enumerate(rows, 1):
        sent = r.get("sentence", "")
        for pattern in _INTENTIONAL_ERROR_PATTERNS:
            m = pattern.search(sent)
            if m:
                violations.append(
                    {
                        "type": "INTENTIONAL_ERROR_LEAK",
                        "item": f"inventory_row_{idx}:{r.get('lemma')}",
                        "message": f"Inventory row contains error marker {m.group(0)!r}: {sent[:60]!r}",
                    }
                )
                break
    return violations


def audit_practice_shards(
    shards_dir: Path | str = DEFAULT_SHARDS_DIR,
    vesum_db: Path | str | None = DEFAULT_VESUM_DB,
    *,
    check_volume: bool = True,
    verify_vesum: bool = True,
    modes: list[str] | tuple[str, ...] | None = None,
) -> tuple[dict[str, int], list[dict[str, Any]]]:
    """Audit all practice shard files across levels for structural integrity and volume thresholds.

    Validates:
    - Blank syntax (exact 1-blank ___ in blank-based modes)
    - Option count (>= 2) and option uniqueness (no duplicate normalized labels, except homonyms)
    - Target answer presence in options list
    - Required pedagogical metadata (distinction gloss, rationale, case rule, notes)
    - 100% VESUM attestation for target answers/forms (when verify_vesum is True)
    - Volume thresholds: paronym >= 250, homonym >= 150, heritage >= 250 (when check_volume is True)
    """
    p_dir = Path(shards_dir)
    violations: list[dict[str, Any]] = []
    counts: dict[str, int] = {m: 0 for m in ALL_PRACTICE_MODES}
    if not p_dir.exists():
        return counts, [
            {"type": "DIR_MISSING", "item": str(p_dir), "message": f"Shards directory {p_dir} does not exist"}
        ]

    shard_files = sorted(p_dir.glob("practice-*.json"))
    target_modes = set(modes) if modes else set(ALL_PRACTICE_MODES)

    for sf in shard_files:
        name = sf.name
        # Skip index and lexemes metadata shards
        if "index" in name or "lexemes" in name:
            continue
        parts = name.split(".")
        if len(parts) < 3:
            continue
        mode = parts[0].replace("practice-", "")
        if mode not in target_modes:
            continue

        try:
            with open(sf, encoding="utf-8") as f:
                data = json.load(f)
        except Exception as exc:
            violations.append({"type": "JSON_PARSE_ERROR", "item": str(sf), "message": str(exc)})
            continue

        items = data.get(mode, [])
        counts[mode] = counts.get(mode, 0) + len(items)
        seen_ids: set[str] = set()

        for idx, item in enumerate(items, 1):
            cid = item.get(f"{mode}Id") or item.get("id") or f"{mode}_{parts[1]}_{idx}"
            if cid in seen_ids:
                violations.append(
                    {
                        "type": "DUPLICATE_ID",
                        "item": f"{name}:{cid}",
                        "message": f"Duplicate item ID {cid!r} in {name}",
                    }
                )
            seen_ids.add(cid)

            # 1. Blank syntax
            if mode in BLANK_MODES:
                field = "sentence" if mode == "cloze" else ("cueSentence" if mode == "imperative" else "prompt")
                text = item.get(field, "")
                if text:
                    blanks = _BLANK_RE.findall(text)
                    if len(blanks) != 1:
                        violations.append(
                            {
                                "type": "INVALID_BLANK_COUNT",
                                "item": f"{name}:{cid}",
                                "message": f"Expected exactly 1 blank, found {len(blanks)} in: {text[:60]!r}",
                            }
                        )

            # 2. Options validation
            if "options" in item and mode not in ("classify", "stress"):
                opts = item["options"]
                if len(opts) < 2:
                    violations.append(
                        {
                            "type": "TOO_FEW_OPTIONS",
                            "item": f"{name}:{cid}",
                            "message": f"Item has fewer than 2 options (found {len(opts)})",
                        }
                    )
                labels: list[str] = []
                correct_count = 0
                for opt in opts:
                    if isinstance(opt, dict):
                        lbl = opt.get("label") or opt.get("text") or opt.get("word") or ""
                        if opt.get("kind") == "answer" or opt.get("isCorrect") is True:
                            correct_count += 1
                    else:
                        lbl = str(opt)
                    labels.append(_normalize_plain(lbl))

                if mode != "homonym" and len(set(labels)) != len(labels):
                    violations.append(
                        {
                            "type": "DUPLICATE_OPTIONS",
                            "item": f"{name}:{cid}",
                            "message": f"Duplicate option labels in item: {labels}",
                        }
                    )

                if correct_count > 1:
                    violations.append(
                        {
                            "type": "MULTIPLE_ANSWERS_MARKED",
                            "item": f"{name}:{cid}",
                            "message": f"Expected at most 1 answer option, found {correct_count}",
                        }
                    )

                # 3. Target answer presence in options
                ans = item.get("answer") or item.get("form") or item.get("target") or item.get("correctForm")
                if ans:
                    ans_norm = _normalize_plain(ans)
                    acc = [_normalize_plain(a) for a in item.get("acceptedAnswers", [])]
                    if ans_norm not in labels and not any(a in labels for a in acc):
                        violations.append(
                            {
                                "type": "ANSWER_NOT_IN_OPTIONS",
                                "item": f"{name}:{cid}",
                                "message": f"Answer {ans!r} not found in option labels: {labels}",
                            }
                        )

            # 4. Explanation & Pedagogical Metadata
            if mode in ("paronym", "homonym", "antonym"):
                gloss = item.get("distinction_gloss_uk", "")
                if not gloss or not gloss.strip():
                    violations.append(
                        {
                            "type": "MISSING_EXPLANATION",
                            "item": f"{name}:{cid}",
                            "message": "Item is missing distinction_gloss_uk pedagogical explanation",
                        }
                    )
            elif mode == "heritage":
                rationale = item.get("rationale") or item.get("corrections")
                if not rationale:
                    violations.append(
                        {
                            "type": "MISSING_EXPLANATION",
                            "item": f"{name}:{cid}",
                            "message": "Heritage card is missing rationale or corrections metadata",
                        }
                    )
            elif mode == "cloze":
                if not (item.get("caseRule") or item.get("provenance") or item.get("attribution")):
                    violations.append(
                        {
                            "type": "MISSING_EXPLANATION",
                            "item": f"{name}:{cid}",
                            "message": "Cloze card is missing caseRule / provenance metadata",
                        }
                    )
            elif mode == "imperative":
                if not (item.get("notes") or item.get("slotLabelUa")):
                    violations.append(
                        {
                            "type": "MISSING_EXPLANATION",
                            "item": f"{name}:{cid}",
                            "message": "Imperative card is missing grammatical notes metadata",
                        }
                    )

            # 5. Morphological attestation in VESUM
            if verify_vesum and vesum_db and Path(vesum_db).exists():
                ans = item.get("answer") or item.get("form") or item.get("target")
                if ans and not check_word_in_vesum(ans, db_path=vesum_db):
                    violations.append(
                        {
                            "type": "VESUM_UNATTESTED",
                            "item": f"{name}:{cid}",
                            "message": f"Target form {ans!r} is not attested in VESUM morphological dictionary",
                        }
                    )

    # Volume Thresholds check
    if check_volume:
        for v_mode, min_count in VOLUME_THRESHOLDS.items():
            if target_modes and v_mode not in target_modes:
                continue
            act_count = counts.get(v_mode, 0)
            if act_count < min_count:
                violations.append(
                    {
                        "type": "VOLUME_BELOW_THRESHOLD",
                        "item": v_mode,
                        "count": act_count,
                        "threshold": min_count,
                        "message": f"Mode {v_mode!r} card count ({act_count}) is below required threshold ({min_count})",
                    }
                )

    return counts, violations


def audit_card_ambiguity(
    shards_dir: Path | str = DEFAULT_SHARDS_DIR,
    sample_size: int = 5,
    vesum_db: Path | str | None = DEFAULT_VESUM_DB,
    *,
    mock_response: dict[str, Any] | None = None,
    strict_ambiguity: bool = False,
    client: Any | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Validate sample practice cards for target exclusivity and distractor plausibility.

    Uses TypeSafe System One (Jev 1.13) or deterministic Sources/VESUM fallback.
    """
    p_dir = Path(shards_dir)
    violations: list[dict[str, Any]] = []
    verdicts: list[dict[str, Any]] = []

    if not p_dir.exists():
        return verdicts, violations

    from scripts.practice.typesafe_distractor_validator import (
        get_typesafe_client,
        ground_with_sources,
        resolve_api_key,
        validate_practice_card,
    )

    candidate_cards: list[tuple[str, dict[str, Any]]] = []
    for mode in ("cloze", "paronym", "heritage", "antonym"):
        found = False
        for lvl in ("A1", "A2", "B1", "B2", "C1"):
            shard_path = p_dir / f"practice-{mode}.{lvl}.json"
            if shard_path.exists():
                try:
                    with open(shard_path, encoding="utf-8") as f:
                        data = json.load(f)
                    for item in data.get(mode, []):
                        stem = item.get("prompt") or item.get("sentence") or item.get("cueSentence")
                        target = item.get("answer") or item.get("form") or item.get("target")
                        opts = item.get("options", [])
                        if not stem or not target or len(opts) < 2:
                            continue
                        distractors = []
                        for opt in opts:
                            l = opt.get("label") or opt.get("text") if isinstance(opt, dict) else str(opt)
                            if _normalize_plain(l) != _normalize_plain(target):
                                distractors.append(l)
                        if distractors:
                            candidate_cards.append((mode, item))
                            found = True
                            break
                except Exception:
                    continue
            if found:
                break
        if len(candidate_cards) >= sample_size:
            break

    ts_client = client
    if ts_client is None and mock_response is None:
        try:
            if resolve_api_key():
                ts_client = get_typesafe_client()
        except Exception:
            ts_client = None

    for mode, card in candidate_cards[:sample_size]:
        cid = card.get(f"{mode}Id") or card.get("id") or "card"
        stem = card.get("prompt") or card.get("sentence") or card.get("cueSentence", "")
        target = card.get("answer") or card.get("form") or card.get("target", "")
        distractors = []
        for opt in card.get("options", []):
            l = opt.get("label") or opt.get("text") if isinstance(opt, dict) else str(opt)
            if _normalize_plain(l) != _normalize_plain(target):
                distractors.append(l)

        if ts_client is not None or mock_response is not None:
            try:
                v = validate_practice_card(
                    stem=stem,
                    target=target,
                    distractors=distractors,
                    grammar_focus=f"{mode.capitalize()} Practice",
                    client=ts_client,
                    mock_response=mock_response,
                    vesum_db_path=vesum_db,
                )
                verdicts.append(
                    {
                        "cardId": cid,
                        "mode": mode,
                        "stem": stem,
                        "target": target,
                        "distractors": distractors,
                        "verdict": v.verdict,
                        "unambiguous_prob": v.is_unambiguous_prob,
                        "plausibility_score": v.plausibility_score,
                        "model": v.model,
                        "findings": v.findings,
                    }
                )
                if v.verdict == "fail_broken":
                    target_in_vesum = True
                    if v.grounded and v.grounding:
                        target_in_vesum = v.grounding.get("target", {}).get("in_vesum", True)
                    if v.verdict_confidence >= 0.50 or not target_in_vesum:
                        violations.append(
                            {
                                "type": "CARD_BROKEN",
                                "item": cid,
                                "message": f"Card failed validation: {'; '.join(v.findings)}",
                            }
                        )
                elif strict_ambiguity and v.verdict == "fail_ambiguous":
                    violations.append(
                        {
                            "type": "CARD_AMBIGUOUS",
                            "item": cid,
                            "message": f"Target exclusivity low (P={v.is_unambiguous_prob:.2f}): {'; '.join(v.findings)}",
                        }
                    )
            except Exception as exc:
                violations.append(
                    {
                        "type": "AMBIGUITY_CHECK_EXCEPTION",
                        "item": cid,
                        "message": f"Validator raised exception: {exc}",
                    }
                )
        else:
            g = ground_with_sources(target=target, distractors=distractors, vesum_db_path=vesum_db)
            t_ok = g.get("target", {}).get("in_vesum", False)
            verdicts.append(
                {
                    "cardId": cid,
                    "mode": mode,
                    "stem": stem,
                    "target": target,
                    "distractors": distractors,
                    "verdict": "pass" if t_ok else "fail_broken",
                    "unambiguous_prob": 1.0,
                    "plausibility_score": 1.5,
                    "model": "deterministic-grounding",
                    "findings": ["Deterministic Sources/VESUM grounding (offline fallback)"],
                }
            )
            if not t_ok:
                violations.append(
                    {
                        "type": "CARD_BROKEN",
                        "item": cid,
                        "message": f"Target '{target}' not attested in VESUM",
                    }
                )

    return verdicts, violations


class PracticeAuditResults(dict):
    """Container for audit results, preserving list iteration while carrying metadata."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.shard_counts: dict[str, int] = {}
        self.ambiguity_verdicts: list[dict[str, Any]] = []


def run_all_practice_audits(
    teacher_cloze: Path | str = DEFAULT_TEACHER_CLOZE,
    error_corrections: Path | str = DEFAULT_ERROR_CORRECTIONS,
    sentence_inventory: Path | str = DEFAULT_SENTENCE_INVENTORY,
    vesum_db: Path | str | None = DEFAULT_VESUM_DB,
    *,
    all_modes: bool = False,
    shards_dir: Path | str = DEFAULT_SHARDS_DIR,
    verify_vesum: bool = True,
    check_ambiguity: bool = False,
    sample_ambiguity: int = 5,
    strict_ambiguity: bool = False,
    mock_ambiguity: dict[str, Any] | None = None,
) -> PracticeAuditResults:
    """Run all Practice Hub audits, returning a mapped dictionary of violations."""
    results = PracticeAuditResults(
        {
            "teacher_cloze": audit_teacher_cloze_deck(teacher_cloze, vesum_db=vesum_db if verify_vesum else None),
            "error_corrections": audit_error_correction_deck(
                error_corrections, vesum_db=vesum_db if verify_vesum else None
            ),
            "sentence_inventory": audit_sentence_inventory(sentence_inventory),
        }
    )

    if all_modes:
        counts, shard_violations = audit_practice_shards(
            shards_dir=shards_dir,
            vesum_db=vesum_db,
            check_volume=True,
            verify_vesum=verify_vesum,
        )
        results["practice_shards"] = shard_violations
        results.shard_counts = counts

    if check_ambiguity:
        amb_verdicts, amb_violations = audit_card_ambiguity(
            shards_dir=shards_dir,
            sample_size=sample_ambiguity,
            vesum_db=vesum_db,
            mock_response=mock_ambiguity,
            strict_ambiguity=strict_ambiguity,
        )
        results["ambiguity_violations"] = amb_violations
        results.ambiguity_verdicts = amb_verdicts

    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="Unified Practice Hub quality assurance gate (Issues #7944, #8276)")
    parser.add_argument("--teacher-cloze", default=str(DEFAULT_TEACHER_CLOZE))
    parser.add_argument("--error-corrections", default=str(DEFAULT_ERROR_CORRECTIONS))
    parser.add_argument("--sentence-inventory", default=str(DEFAULT_SENTENCE_INVENTORY))
    parser.add_argument("--shards-dir", default=str(DEFAULT_SHARDS_DIR))
    parser.add_argument("--vesum-db", default=str(DEFAULT_VESUM_DB))
    parser.add_argument("--all-modes", action="store_true", help="Audit all practice shards across all 10 modes")
    parser.add_argument("--verify-vesum", action="store_true", help="Verify morphological attestation in VESUM")
    parser.add_argument("--check-ambiguity", action="store_true", help="Validate sample cards with TypeSafe System One")
    parser.add_argument(
        "--sample-ambiguity", type=int, default=5, help="Number of cards to sample for ambiguity validation"
    )
    parser.add_argument("--strict-ambiguity", action="store_true", help="Treat fail_ambiguous as a hard failure")
    args = parser.parse_args()

    # When --all-modes is passed, default verify_vesum to True if not explicitly overridden
    verify_vesum = args.verify_vesum or args.all_modes

    print("--- Practice Hub Unified Quality Gate ---")
    results = run_all_practice_audits(
        teacher_cloze=args.teacher_cloze,
        error_corrections=args.error_corrections,
        sentence_inventory=args.sentence_inventory,
        vesum_db=args.vesum_db,
        all_modes=args.all_modes,
        shards_dir=args.shards_dir,
        verify_vesum=verify_vesum,
        check_ambiguity=args.check_ambiguity,
        sample_ambiguity=args.sample_ambiguity,
        strict_ambiguity=args.strict_ambiguity,
    )

    if args.all_modes and results.shard_counts:
        print("\nPractice Shard Inventory & Thresholds:")
        for mode in ALL_PRACTICE_MODES:
            cnt = results.shard_counts.get(mode, 0)
            threshold_note = ""
            if mode in VOLUME_THRESHOLDS:
                req = VOLUME_THRESHOLDS[mode]
                status = "OK" if cnt >= req else "FAIL"
                threshold_note = f" (target >= {req}: {status})"
            print(f"  - {mode:12s}: {cnt:5d} cards{threshold_note}")

    if args.check_ambiguity and results.ambiguity_verdicts:
        print("\nTypeSafe System One Target Exclusivity & Distractor Evaluation:")
        for v in results.ambiguity_verdicts:
            print(
                f"  - [{v['mode'].upper()}] {v['cardId']}: verdict={v['verdict']} "
                f"(P_unambig={v['unambiguous_prob']:.2f}, plaus={v['plausibility_score']:.2f}, model={v['model']})"
            )
            print(f"    Stem  : {v['stem']}")
            print(f"    Target: {v['target']} | Distractors: {', '.join(v['distractors'])}")

    total_violations = sum(len(v) for v in results.values())
    if total_violations == 0:
        print("\n✅ Practice Quality Gate PASSED: 0 violations across all datasets and modes.")
        return 0

    print(f"\n❌ Practice Quality Gate FAILED with {total_violations} violation(s):")
    for category, viols in results.items():
        if viols:
            print(f"\n[{category.upper()}] ({len(viols)} issues):")
            for v in viols[:10]:
                print(f"  - [{v.get('type')}] {v.get('item', '')}: {v.get('message')}")
            if len(viols) > 10:
                print(f"  ... and {len(viols) - 10} more")

    return 1


if __name__ == "__main__":
    sys.exit(main())
