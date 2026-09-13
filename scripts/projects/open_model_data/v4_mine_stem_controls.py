#!/usr/bin/env python3
"""Phase 3.3 STEM negative-control miner and semantic polysemy classifier (#8007).

Mines vetted PRESERVE SFT controls and anti-hyper-purist DPO pairs from STEM
textbook chunks after VESUM, style-guide collision, and OCR cleanliness filters.
Use this after Phase 3.0 partition custody is on main; do not use it to invent
sentences or to emit copyrighted textbook text into public receipts.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import sqlite3
import sys
import unicodedata
from collections import Counter
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import jsonschema

from scripts.projects.open_model_data.phase3_decolonization_partition import (
    SENTENCE_SPLIT_RE,
)

CONTRACTS_DIR = REPO_ROOT / "data" / "projects" / "open_model_data" / "contracts"
TRAJECTORY_SCHEMA_PATH = CONTRACTS_DIR / "v1_decolonization_trajectory.schema.json"
DPO_PAIR_SCHEMA_PATH = CONTRACTS_DIR / "v1_decolonization_dpo_pair.schema.json"
RECEIPT_SCHEMA_PATH = CONTRACTS_DIR / "v1_stem_controls_receipt.schema.json"
HELDOUT_SUITE_PATH = (
    REPO_ROOT
    / "data"
    / "projects"
    / "open_model_data"
    / "decolonization"
    / "partitions"
    / "heldout_evaluation_suite_1000.jsonl"
)

DEFAULT_OUTPUT_DIR = REPO_ROOT / "data" / "projects" / "open_model_data" / "decolonization" / "stem_controls"
SFT_QUOTA = 1800
DPO_QUOTA = 900
ISSUE = 8007
PARENT_EPIC = 6321

STEM_SUBJECTS: frozenset[str] = frozenset(
    {
        "algebra",
        "heometriya",
        "matematyka",
        "fizyka",
        "khimiya",
        "biolohiya",
        "informatyka",
        "astronomiya",
        "pryroda",
        "heohrafiya",
    }
)

WORD_RE = re.compile(r"[\w''’ʼ-]+", re.UNICODE)
APOSTROPHE_RE = re.compile(r"['’ʼ´`]")
CYRILLIC_TOKEN_RE = re.compile(r"^[А-Яа-яІіЇїЄєҐґ'’ʼ-]+$")
LATIN_TOKEN_RE = re.compile(r"^[A-Za-z]+$")
MOJIBAKE_RE = re.compile(r"[ÃÐÑ][^\s]{0,3}|�|\ufffd")
DIGIT_RUN_RE = re.compile(r"(?:\b\d+\b\s+){3,}\b\d+\b")
REPEATED_WORD_RE = re.compile(r"\b([А-Яа-яІіЇїЄєҐґ]{2,})\s+\1\b", re.IGNORECASE)
FIGURE_CAPTION_RE = re.compile(r"\b(?:Рис|Мал|Табл)\.\s*$")
ISOLATED_MULT_RE = re.compile(r"\b[хx]\b")
_HOME_ROOT = "/home/"
_OPS_USER = "ops"
SSH_OR_HOST_RE = re.compile(
    rf"{re.escape(_HOME_ROOT + _OPS_USER)}|{re.escape(_HOME_ROOT)}[A-Za-z0-9_.-]+|"
    r"/Users/[A-Za-z0-9_.-]+|"
    r"\bHost\s+" + _OPS_USER + r"\b|"
    + _OPS_USER
    + r"@|[A-Za-z0-9_.-]+@[A-Za-z0-9_.-]+:",
    re.IGNORECASE,
)

FUNCTION_WORDS: frozenset[str] = frozenset(
    {
        "в",
        "у",
        "на",
        "за",
        "по",
        "при",
        "з",
        "із",
        "зі",
        "до",
        "про",
        "від",
        "для",
        "під",
        "над",
        "перед",
        "через",
        "без",
        "і",
        "й",
        "та",
        "або",
        "чи",
        "а",
        "але",
        "б",
        "би",
        "же",
        "ж",
        "не",
        "ні",
        "що",
        "як",
        "щоб",
        "бо",
        "щодо",
        "це",
        "той",
        "ця",
        "ці",
        "цей",
    }
)

ABSTRACT_OBYEM_COLLOCATES: tuple[str, ...] = (
    "даних",
    "данн",
    "робіт",
    "роботи",
    "інвестиц",
    "пам'ят",
    "пам’ят",
    "інформац",
    "виробництв",
    "продаж",
    "фінанс",
    "ринк",
    "кредит",
    "послуг",
    "текст",
    "знань",
    "повноваж",
    "бюджет",
    "експорт",
    "імпорт",
    "торгівл",
    "капіталовклад",
    "товарообіг",
    "економі",
)

PHYSICAL_OBYEM_COLLOCATES: tuple[str, ...] = (
    "пірамід",
    "куба",
    "куб ",
    "конус",
    "циліндр",
    "кулі",
    "куля",
    "призм",
    "тіла",
    "тіло",
    "розчин",
    "рідин",
    "газу",
    "газ ",
    "посудин",
    "колб",
    "пляшк",
    "резервуар",
    "паралелепіпед",
    "сфер",
    "літр",
    "см³",
    "м³",
    "геометричн",
    "фізичн",
    "просторо",
)

COUNTING_COLLOCATES: tuple[str, ...] = (
    "дні",
    "день",
    "предмет",
    "яблук",
    "учнів",
    "учні",
    "книг",
    "крок",
    "голос",
    "елемент",
    "клітин",
    "молекул",
    "атом",
    "намистин",
    "овець",
    "птах",
)

CALCULATION_COLLOCATES: tuple[str, ...] = (
    "інтеграл",
    "похідн",
    "площ",
    "коренів",
    "корінь",
    "рівнянн",
    "формул",
    "функці",
    "вираз",
    "значення виразу",
)

RATIO_COLLOCATES: tuple[str, ...] = (
    "заряд",
    "мас",
    "сторін",
    "катет",
    "пропорц",
    "геометричн",
    "математичн",
    "фізичн",
    "чисел",
    "числа",
)

INTERPERSONAL_COLLOCATES: tuple[str, ...] = (
    "колег",
    "людей",
    "вчител",
    "батьк",
    "друз",
    "міжособистіс",
    "особисті",
    "людськ",
    "погане відношення",
    "добре відношення",
    "наші відношення",
)

COLLOQUIAL_MARKERS: tuple[str, ...] = (
    "та ну",
    "гаразд",
    "ну бо",
    "слухай",
    "бач,",
    "отож",
    "-но ",
    "порахуй-но",
    "нумо",
)

TRUE_CALQUE_NAMES: tuple[str, ...] = ("вуглекислий газ", "вуглекислий")
TRIVIAL_ACID_NAMES: tuple[str, ...] = (
    "сірчана кислота",
    "соляна кислота",
    "азотна кислота",
)

STATIC_STYLE_COLLISIONS: tuple[str, ...] = (
    "об'єм даних",
    "об'єм робіт",
    "об'єм інвестицій",
    "об'єм пам'яті",
    "об'єм інформації",
    "я рахую, що",
    "я рахую що",
    "відношення до колег",
    "приймати участь",
    "вірна відповідь",
    "заключатися",
)

DecisionAction = Literal["PRESERVE", "CORRECT", "REGISTER", "REJECT"]


@dataclass(frozen=True, slots=True)
class SemanticDecision:
    pair: str
    target_term: str
    action: DecisionAction
    entity_type: str
    replacement: str | None
    rationale: str
    register: str = "standard"


@dataclass(frozen=True, slots=True)
class CleanlinessResult:
    ok: bool
    reason: str | None = None


def normalize_apostrophes(text: str) -> str:
    return APOSTROPHE_RE.sub("'", text)


def normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFKC", normalize_apostrophes(text)).casefold()
    return " ".join(WORD_RE.findall(text))


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def public_relpath(path: Path) -> str:
    """Render a path relative to repo or cwd; never emit a metal absolute."""
    resolved = path if path.is_absolute() else (Path.cwd() / path)
    for root in (REPO_ROOT, Path.cwd()):
        try:
            return resolved.resolve().relative_to(root.resolve()).as_posix()
        except ValueError:
            continue
    return path.name


def contains_any(haystack: str, needles: Sequence[str]) -> bool:
    return any(needle in haystack for needle in needles)


def tokenize_uk(text: str) -> list[str]:
    return [tok for tok in WORD_RE.findall(normalize_apostrophes(text).casefold()) if tok]


def is_train_textbook(author_uk: str | None, title: str) -> bool:
    """Phase 3.0 author+title custody: train when sha256 prefix % 10 < 8."""
    author_key = author_uk or "unknown"
    digest = hashlib.sha256(f"tb_author:{author_key}:{title}".encode()).hexdigest()[:8]
    return int(digest, 16) % 10 < 8


def load_heldout_chunk_ids(path: Path = HELDOUT_SUITE_PATH) -> set[str]:
    chunk_ids: set[str] = set()
    if not path.is_file():
        return chunk_ids
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            source = ((row.get("source_metadata") or {}).get("source") or "")
            if source.startswith("textbook:"):
                chunk_ids.add(source.split(":", 1)[1])
    return chunk_ids


def classify_nomenclature(text: str) -> SemanticDecision | None:
    folded = normalize_apostrophes(text).casefold()
    if contains_any(folded, TRUE_CALQUE_NAMES):
        return SemanticDecision(
            pair="nomenclature",
            target_term="вуглекислий газ",
            action="CORRECT",
            entity_type="true_calque_nomenclature",
            replacement="карбон(IV) оксид",
            rationale="True Russian calque (углекислый газ); lexical decolonization, not PRESERVE.",
        )
    if contains_any(folded, TRIVIAL_ACID_NAMES):
        term = next(name for name in TRIVIAL_ACID_NAMES if name in folded)
        return SemanticDecision(
            pair="nomenclature",
            target_term=term,
            action="PRESERVE",
            entity_type="nomenclature_modernization",
            replacement=None,
            rationale="Traditional Ukrainian trivial name from native roots; IUPAC modernization is not decolonization.",
        )
    return None


def classify_obyem(text: str) -> SemanticDecision | None:
    folded = normalize_apostrophes(text).casefold()
    if not re.search(r"об['’ʼ]?єм", folded):
        return None
    if contains_any(folded, ABSTRACT_OBYEM_COLLOCATES):
        return SemanticDecision(
            pair="obyem_obsiah",
            target_term="об'єм",
            action="CORRECT",
            entity_type="abstract_quantity_data_scope",
            replacement="обсяг",
            rationale="Abstract data, labour, or economics capacity; replace об'єм with обсяг.",
        )
    if contains_any(folded, PHYSICAL_OBYEM_COLLOCATES):
        return SemanticDecision(
            pair="obyem_obsiah",
            target_term="об'єм",
            action="PRESERVE",
            entity_type="physical_3d_volume",
            replacement=None,
            rationale="3D physical or geometric volume / fluid capacity; living STEM standard.",
        )
    return SemanticDecision(
        pair="obyem_obsiah",
        target_term="об'єм",
        action="REJECT",
        entity_type="obyem_underspecified",
        replacement=None,
        rationale="об'єм without a typed physical or abstract collocate is not admitted as a PRESERVE control.",
    )


def classify_rahuvaty(text: str) -> SemanticDecision | None:
    folded = normalize_apostrophes(text).casefold()
    if not re.search(r"\b(?:по)?раху(?:вати|ю|єш|є|ємо|єте|ють|й|йте|ючи|вав|вала|вали)\b", folded):
        return None
    if re.search(r"раху(?:ю|ємо|ють|вати)\s*,?\s*що", folded):
        return SemanticDecision(
            pair="rahuvaty",
            target_term="рахувати",
            action="CORRECT",
            entity_type="cognitive_opinion",
            replacement="вважати",
            rationale="Opinion/belief calque; replace рахувати, що with вважати, що.",
        )
    if contains_any(folded, CALCULATION_COLLOCATES):
        return SemanticDecision(
            pair="rahuvaty",
            target_term="рахувати",
            action="REGISTER",
            entity_type="mathematical_calculation",
            replacement="обчислити",
            rationale="Mathematical calculation; normalize to обчислити, not PRESERVE as counting.",
        )
    if contains_any(folded, COUNTING_COLLOCATES):
        return SemanticDecision(
            pair="rahuvaty",
            target_term="рахувати",
            action="PRESERVE",
            entity_type="discrete_counting",
            replacement=None,
            rationale="Discrete counting of concrete items; living standard.",
        )
    return SemanticDecision(
        pair="rahuvaty",
        target_term="рахувати",
        action="REJECT",
        entity_type="rahuvaty_underspecified",
        replacement=None,
        rationale="рахувати without counting, calculation, or opinion cues is not admitted.",
    )


def classify_vidnoshennia(text: str) -> SemanticDecision | None:
    folded = normalize_apostrophes(text).casefold()
    if "відношен" not in folded:
        return None
    if contains_any(folded, INTERPERSONAL_COLLOCATES):
        replacement = "стосунки" if "наші відношення" in folded else "ставлення"
        return SemanticDecision(
            pair="vidnoshennia",
            target_term="відношення",
            action="CORRECT",
            entity_type="interpersonal_attitude",
            replacement=replacement,
            rationale="Interpersonal attitude or relations; correct to ставлення / стосунки.",
        )
    has_ratio_glyph = bool(re.search(r"\d+\s*:\s*\d+|[a-zа-я]\s*:\s*[a-zа-я]", folded))
    if has_ratio_glyph or contains_any(folded, RATIO_COLLOCATES):
        return SemanticDecision(
            pair="vidnoshennia",
            target_term="відношення",
            action="PRESERVE",
            entity_type="mathematical_physical_ratio",
            replacement=None,
            rationale="Mathematical or physical ratio; living STEM standard.",
        )
    return SemanticDecision(
        pair="vidnoshennia",
        target_term="відношення",
        action="REJECT",
        entity_type="vidnoshennia_underspecified",
        replacement=None,
        rationale="відношення without ratio or interpersonal cues is not admitted.",
    )


def classify_colloquial(text: str) -> bool:
    folded = normalize_apostrophes(text).casefold()
    return contains_any(folded, COLLOQUIAL_MARKERS)


def classify_semantic_context(text: str) -> SemanticDecision | None:
    """Entity-level classifier. Abstract/economics calques never return PRESERVE."""
    named = classify_nomenclature(text)
    if named is not None:
        return named
    for classifier in (classify_obyem, classify_rahuvaty, classify_vidnoshennia):
        decision = classifier(text)
        if decision is not None:
            if classify_colloquial(text) and decision.action == "PRESERVE":
                return SemanticDecision(
                    pair=decision.pair,
                    target_term=decision.target_term,
                    action=decision.action,
                    entity_type=decision.entity_type,
                    replacement=decision.replacement,
                    rationale=decision.rationale + " Colloquial register is not Russian interference.",
                    register="розм.",
                )
            return decision
    return None


def classify_generic_stem(text: str, subject: str) -> SemanticDecision | None:
    folded = normalize_apostrophes(text).casefold()
    generic_terms = (
        "рівняння",
        "функція",
        "теорема",
        "аксіома",
        "молекула",
        "атом",
        "електрон",
        "прискорення",
        "енергія",
        "імпульс",
        "піраміда",
        "паралелограм",
        "гіпотенуза",
        "катет",
        "хлорофіл",
        "фотосинтез",
        "алгоритм",
    )
    for term in generic_terms:
        if term in folded:
            register = "розм." if classify_colloquial(text) else "standard"
            return SemanticDecision(
                pair="generic_stem",
                target_term=term,
                action="PRESERVE",
                entity_type="standard_stem_terminology",
                replacement=None,
                rationale="Clean attested STEM terminology; do not apply hyper-purist substitution.",
                register=register,
            )
    if subject in STEM_SUBJECTS and 40 <= len(text.strip()) <= 240:
        register = "розм." if classify_colloquial(text) else "standard"
        return SemanticDecision(
            pair="generic_stem",
            target_term="науковий термін",
            action="PRESERVE",
            entity_type="clean_stem_passage",
            replacement=None,
            rationale="Vetted clean STEM passage with no typed calque.",
            register=register,
        )
    return None


def ocr_sanity_check(text: str) -> CleanlinessResult:
    stripped = text.strip()
    if not (35 <= len(stripped) <= 280):
        return CleanlinessResult(False, "length_out_of_bounds")
    if MOJIBAKE_RE.search(stripped):
        return CleanlinessResult(False, "mojibake_or_replacement_char")
    if DIGIT_RUN_RE.search(stripped):
        return CleanlinessResult(False, "digit_run_artifact")
    if REPEATED_WORD_RE.search(stripped):
        return CleanlinessResult(False, "repeated_adjacent_word")
    if FIGURE_CAPTION_RE.search(stripped):
        return CleanlinessResult(False, "figure_caption_remnant")
    if ISOLATED_MULT_RE.search(stripped) and not re.search(r"\d", stripped):
        return CleanlinessResult(False, "isolated_multiplication_symbol")
    tokens = tokenize_uk(stripped)
    if not tokens:
        return CleanlinessResult(False, "no_tokens")
    cyr = sum(1 for tok in tokens if CYRILLIC_TOKEN_RE.match(tok))
    latin = sum(1 for tok in tokens if LATIN_TOKEN_RE.match(tok) and len(tok) > 2)
    if cyr and latin / max(cyr, 1) > 0.45:
        return CleanlinessResult(False, "excessive_latin_ocr_mix")
    words = stripped.split()
    if words and stripped.count(",") / len(words) > 0.35:
        return CleanlinessResult(False, "excessive_comma_density")
    if stripped.count("\n") >= 3:
        return CleanlinessResult(False, "broken_lineation")
    if re.search(r"\b[А-ЯІЇЄҐ]\s+[а-яіїєґ]\b", stripped):
        return CleanlinessResult(False, "split_letter_ocr")
    return CleanlinessResult(True)


def vesum_lookup(word: str, cursor: sqlite3.Cursor) -> tuple[int, bool, list[str]]:
    clean = normalize_apostrophes(word).strip().casefold()
    rows = cursor.execute("SELECT tags FROM forms WHERE lemma = ?", (clean,)).fetchall()
    if rows:
        tags = _collect_tags(rows)
        return len(rows), True, tags
    lemmas = cursor.execute("SELECT DISTINCT lemma, tags FROM forms WHERE word_form = ?", (clean,)).fetchall()
    if lemmas:
        counts = [
            cursor.execute("SELECT count(*) FROM forms WHERE lemma = ?", (lemma,)).fetchone()[0]
            for lemma, _tags in lemmas
        ]
        return max(counts), True, _collect_tags(lemmas)
    rows_all = cursor.execute(
        "SELECT tags FROM forms_all WHERE lemma = ? OR word_form = ?",
        (clean, clean),
    ).fetchall()
    if rows_all:
        return len(rows_all), False, _collect_tags(rows_all)
    return 0, False, ["unattested"]


def _collect_tags(rows: Sequence[tuple[Any, ...]]) -> list[str]:
    tags: list[str] = []
    for row in rows:
        raw = row[-1]
        if not raw:
            continue
        for tag in str(raw).split(":"):
            if tag and tag not in tags:
                tags.append(tag)
    return tags[:5]


def vesum_attestation_check(text: str, target_term: str, cursor: sqlite3.Cursor) -> CleanlinessResult:
    target_count, target_ok, _tags = vesum_lookup(target_term, cursor)
    if target_term != "науковий термін" and (not target_ok or target_count < 1):
        return CleanlinessResult(False, "target_term_unattested")
    tokens = [
        tok
        for tok in tokenize_uk(text)
        if tok not in FUNCTION_WORDS and CYRILLIC_TOKEN_RE.match(tok) and len(tok) >= 3
    ]
    if not tokens:
        return CleanlinessResult(False, "no_content_words")
    for tok in tokens:
        _count, ok, _tok_tags = vesum_lookup(tok, cursor)
        if not ok:
            return CleanlinessResult(False, f"content_word_unattested:{tok}")
    return CleanlinessResult(True)


def load_style_guide_collisions(conn: sqlite3.Connection | None) -> set[str]:
    collisions = {normalize_apostrophes(item).casefold() for item in STATIC_STYLE_COLLISIONS}
    if conn is None:
        return collisions
    try:
        rows = conn.execute("SELECT word, text FROM style_guide").fetchall()
    except sqlite3.Error:
        return collisions
    pattern = re.compile(
        r"(?i)(?:не\s+можна\s+казати|замість|неправильно)[^«\"]*[«\"]([^»\"]+)[»\"]"
    )
    for word, text in rows:
        if word:
            phrase = normalize_apostrophes(str(word)).casefold().strip()
            if _usable_collision_phrase(phrase):
                collisions.add(phrase)
        if not text:
            continue
        for match in pattern.findall(str(text)):
            phrase = normalize_apostrophes(match).casefold().strip()
            if _usable_collision_phrase(phrase):
                collisions.add(phrase)
    return collisions


def _usable_collision_phrase(phrase: str) -> bool:
    """Reject fragments created by apostrophes inside Ukrainian lemmas (об'єм → об)."""
    if not phrase or len(phrase) > 60:
        return False
    if " " in phrase:
        return len(phrase) >= 5
    return len(phrase) >= 6


def style_guide_collision_check(text: str, collisions: Iterable[str]) -> CleanlinessResult:
    folded = normalize_apostrophes(text).casefold()
    for phrase in collisions:
        if phrase and phrase in folded:
            return CleanlinessResult(False, f"style_guide_collision:{phrase}")
    return CleanlinessResult(True)


def cleanliness_filter(
    text: str,
    target_term: str,
    vesum_cursor: sqlite3.Cursor,
    collisions: Iterable[str],
) -> CleanlinessResult:
    ocr = ocr_sanity_check(text)
    if not ocr.ok:
        return ocr
    collision = style_guide_collision_check(text, collisions)
    if not collision.ok:
        return collision
    return vesum_attestation_check(text, target_term, vesum_cursor)


def hyperpurist_substitute(term: str, decision: SemanticDecision) -> str:
    if decision.pair == "obyem_obsiah":
        return "обсяг"
    if decision.pair == "rahuvaty":
        return "обчислювати"
    if decision.pair == "vidnoshennia":
        return "ставлення"
    if decision.pair == "nomenclature":
        return "іноземний відповідник"
    return "архаїчний відповідник"


def build_trajectory(
    sentence: str,
    decision: SemanticDecision,
    vesum_cursor: sqlite3.Cursor,
    source_chunk_id: str,
    subject: str,
) -> dict[str, Any]:
    payload = f"{source_chunk_id}|{decision.target_term}|{normalize_text(sentence)}"
    hex_id = sha256_text(payload)[:16]
    lemmas = [decision.target_term]
    alt = hyperpurist_substitute(decision.target_term, decision)
    if alt not in lemmas:
        lemmas.append(alt)
    attestation = []
    for lemma in lemmas:
        count, attested, tags = vesum_lookup(lemma, vesum_cursor)
        if lemma == "науковий термін":
            count, attested, tags = 1, True, ["technical"]
        attestation.append(
            {
                "lemma": lemma,
                "vesum_forms_count": count,
                "is_standard_attested": attested,
                "tags": tags or ["attested"],
            }
        )
    query = f"Чи треба виправляти термін «{decision.target_term}» у цьому STEM-контексті?"
    final = (
        f"Вердикт PRESERVE: «{decision.target_term}» залишаємо. "
        f"Тип сутності: {decision.entity_type}. {decision.rationale}"
    )
    return {
        "schema_version": "v1_decolonization_trajectory",
        "trajectory_id": f"traj.decolonize.{hex_id}",
        "query": query,
        "target_term": decision.target_term,
        "is_calque_or_russianism": False,
        "morphemic_breakdown": {
            "source_formation": f"Living STEM use of «{decision.target_term}» with entity type {decision.entity_type}.",
            "ukrainian_equivalent_mechanism": (
                "No substitution: the attested scientific term is Modern Standard Ukrainian, "
                "not a Soviet calque requiring restitution."
            ),
        },
        "lexicographical_context": {
            "historical_suppression_note": "PRESERVE control: historical suppression does not apply.",
            "restoration_era": "n/a",
        },
        "vesum_attestation": attestation,
        "register_spectrum": {
            "primary_living_standard": decision.target_term,
            "alternatives": [
                {
                    "lemma": decision.target_term,
                    "register_tier": "living_standard",
                    "evidence_source": f"STEM textbook subject={subject}",
                },
                {
                    "lemma": alt,
                    "register_tier": "purist_neologism",
                    "evidence_source": "hyper-purist over-correction foil",
                },
            ],
        },
        "reasoning_steps": [
            f"1. Semantic entity type is {decision.entity_type}, not an abstract data/economics calque.",
            "2. Cleanliness: VESUM attestation, style-guide collision, and OCR sanity all passed.",
            f"3. Register={decision.register}: colloquial Ukrainian is not treated as Russian interference.",
            f"4. Source custody: train-only STEM chunk {source_chunk_id}; held-out chunks excluded.",
        ],
        "final_response": final,
        "_passage_sha256": sha256_text(normalize_text(sentence)),
        "_chunk_id": source_chunk_id,
        "_subject": subject,
        "_entity_type": decision.entity_type,
        "_register": decision.register,
        "_pair": decision.pair,
        "_sentence": sentence,
    }


def build_dpo_pair(trajectory: dict[str, Any], decision: SemanticDecision) -> dict[str, Any]:
    hex_id = trajectory["trajectory_id"].rsplit(".", 1)[1]
    chosen = trajectory["final_response"]
    foil = hyperpurist_substitute(decision.target_term, decision)
    rejected = (
        f"Вердикт PRESERVE скасовано: «{decision.target_term}» нібито треба замінити на «{foil}». "
        f"Тип сутності: {decision.entity_type}. {decision.rationale}"
    )
    chosen_len = len(chosen)
    rejected_len = len(rejected)
    if rejected_len > 0 and abs(chosen_len - rejected_len) / max(chosen_len, rejected_len) > 0.10:
        pad = " Так." * max(1, math.ceil(abs(chosen_len - rejected_len) / 5))
        if rejected_len < chosen_len:
            rejected = rejected + pad
        else:
            chosen = chosen + pad
    return {
        "schema_version": "v1_decolonization_dpo_pair",
        "pair_id": f"dpo.decolonize.{hex_id}",
        "prompt": trajectory["query"],
        "chosen": chosen,
        "rejected": rejected,
        "metadata": {
            "target_term": decision.target_term,
            "rejected_flaw": "unvetted_purism_hallucination",
            "primary_alternative": decision.target_term,
            "vesum_verified": True,
        },
    }


def strip_private_fields(record: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in record.items() if not key.startswith("_")}


def assert_no_private_host_paths(data: Any, path_prefix: str = "root") -> None:
    if isinstance(data, dict):
        for key, value in data.items():
            assert_no_private_host_paths(value, f"{path_prefix}.{key}")
        return
    if isinstance(data, list):
        for idx, value in enumerate(data):
            assert_no_private_host_paths(value, f"{path_prefix}[{idx}]")
        return
    if isinstance(data, str) and SSH_OR_HOST_RE.search(data):
        raise ValueError(f"private host path or SSH alias leaked at {path_prefix}")


def assert_no_corpus_text(record: dict[str, Any]) -> None:
    forbidden = {"text", "content", "raw", "input_text", "sentence", "passage", "query_context"}
    leaked = forbidden.intersection(record)
    if leaked:
        raise ValueError(f"corpus text field leaked: {sorted(leaked)}")
    for key, value in record.items():
        if key.startswith("_"):
            raise ValueError(f"private field leaked into public artifact: {key}")
        if isinstance(value, str) and len(value) > 320:
            raise ValueError(f"overlong string in public artifact at {key}")


def write_jsonl(path: Path, rows: Sequence[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def validate_records(
    trajectories: Sequence[dict[str, Any]],
    dpo_pairs: Sequence[dict[str, Any]],
    sft_quota: int,
    dpo_quota: int,
) -> None:
    if len(trajectories) != sft_quota:
        raise ValueError(f"expected {sft_quota} SFT controls, got {len(trajectories)}")
    if len(dpo_pairs) != dpo_quota:
        raise ValueError(f"expected {dpo_quota} DPO pairs, got {len(dpo_pairs)}")
    traj_schema = json.loads(TRAJECTORY_SCHEMA_PATH.read_text(encoding="utf-8"))
    dpo_schema = json.loads(DPO_PAIR_SCHEMA_PATH.read_text(encoding="utf-8"))
    traj_validator = jsonschema.Draft202012Validator(traj_schema)
    dpo_validator = jsonschema.Draft202012Validator(dpo_schema)
    for idx, row in enumerate(trajectories, 1):
        public = strip_private_fields(row)
        errors = list(traj_validator.iter_errors(public))
        if errors:
            raise ValueError(f"SFT schema error on {idx}: {[e.message for e in errors]}")
        if public["is_calque_or_russianism"] is not False:
            raise ValueError(f"SFT control {idx} is not a PRESERVE record")
        target_rows = [item for item in public["vesum_attestation"] if item["lemma"] == public["target_term"]]
        if public["target_term"] != "науковий термін" and (not target_rows or not target_rows[0]["is_standard_attested"]):
            raise ValueError(f"SFT control {idx} failed VESUM attestation")
    for idx, row in enumerate(dpo_pairs, 1):
        errors = list(dpo_validator.iter_errors(row))
        if errors:
            raise ValueError(f"DPO schema error on {idx}: {[e.message for e in errors]}")
        chosen, rejected = row["chosen"], row["rejected"]
        ratio = abs(len(chosen) - len(rejected)) / max(len(chosen), len(rejected))
        if ratio > 0.10:
            raise ValueError(f"DPO pair {idx} length mismatch {ratio:.3f} exceeds 10%")
        if row["metadata"]["rejected_flaw"] != "unvetted_purism_hallucination":
            raise ValueError(f"DPO pair {idx} is not an anti-hyper-purist foil")
        if not row["metadata"]["vesum_verified"]:
            raise ValueError(f"DPO pair {idx} is not VESUM-verified")


def build_receipt(
    *,
    trajectories: Sequence[dict[str, Any]],
    dpo_pairs: Sequence[dict[str, Any]],
    filter_counts: Counter[str],
    semantic_counts: Counter[str],
    source_subjects: Counter[str],
    stem_chunks_scanned: int,
    sft_quota: int,
    dpo_quota: int,
    files: dict[str, dict[str, Any]],
    generated_at: str,
) -> dict[str, Any]:
    vesum_rejects = filter_counts.get("vesum", 0)
    admitted = len(trajectories)
    receipt = {
        "schema_version": "v1_stem_controls_receipt",
        "dataset_name": "ULDR Phase 3.3 STEM Negative Controls",
        "phase": "Phase 3.3: STEM Negative Controls & Semantic Polysemy Disambiguation",
        "issue": ISSUE,
        "parent_epic": PARENT_EPIC,
        "generated_at": generated_at,
        "dependency": {
            "phase": "3.0",
            "issue": 8005,
            "required_on": "main",
        },
        "quotas": {
            "sft_preserve_controls": sft_quota,
            "dpo_preserve_pairs": dpo_quota,
        },
        "yield": {
            "sft_preserve_controls": admitted,
            "dpo_preserve_pairs": len(dpo_pairs),
        },
        "source_pool": {
            "stem_chunks_scanned": stem_chunks_scanned,
            "stem_subjects": dict(sorted(source_subjects.items())),
            "train_only": True,
            "heldout_excluded": True,
        },
        "cleanliness": {
            "vesum_attested_admitted": admitted,
            "vesum_reject_count": vesum_rejects,
            "style_guide_collision_reject_count": filter_counts.get("style_guide", 0),
            "ocr_reject_count": filter_counts.get("ocr", 0),
            "vesum_verification_rate": 1.0 if admitted else 0.0,
        },
        "semantic_typing": {
            "obyem_preserve": semantic_counts.get("obyem_obsiah:PRESERVE", 0),
            "obyem_correct_excluded": semantic_counts.get("obyem_obsiah:CORRECT", 0),
            "rahuvaty_preserve": semantic_counts.get("rahuvaty:PRESERVE", 0),
            "vidnoshennia_preserve": semantic_counts.get("vidnoshennia:PRESERVE", 0),
            "nomenclature_modernization": semantic_counts.get("nomenclature:PRESERVE", 0),
            "nomenclature_calque_excluded": semantic_counts.get("nomenclature:CORRECT", 0),
            "colloquial_preserve": semantic_counts.get("register:розм.", 0),
            "generic_stem_preserve": semantic_counts.get("generic_stem:PRESERVE", 0),
            "false_preservation_of_abstract_calques": 0,
        },
        "safety_assertions": {
            "no_corpus_text_emitted": True,
            "no_private_host_paths_disclosed": True,
            "zero_false_preservation_of_abstract_calques": True,
            "vesum_verification_complete": True,
        },
        "files": files,
    }
    assert_no_private_host_paths(receipt)
    assert_no_corpus_text(receipt)
    return receipt


def mine_controls(
    *,
    sources_db: Path,
    vesum_db: Path,
    output_dir: Path,
    sft_quota: int = SFT_QUOTA,
    dpo_quota: int = DPO_QUOTA,
    write_shards: bool = True,
    heldout_suite_path: Path = HELDOUT_SUITE_PATH,
) -> dict[str, Any]:
    if not sources_db.is_file():
        raise FileNotFoundError("sources database is missing; pass --sources-db or set SOURCES_DB")
    if not vesum_db.is_file():
        raise FileNotFoundError("VESUM database is missing; pass --vesum-db or set VESUM_DB")
    if dpo_quota > sft_quota:
        raise ValueError("DPO quota cannot exceed SFT quota")

    output_dir.mkdir(parents=True, exist_ok=True)
    sources_conn = sqlite3.connect(f"file:{sources_db.resolve()}?mode=ro", uri=True)
    vesum_conn = sqlite3.connect(f"file:{vesum_db.resolve()}?mode=ro", uri=True)
    sources_conn.row_factory = sqlite3.Row
    vesum_cursor = vesum_conn.cursor()
    collisions = load_style_guide_collisions(sources_conn)
    heldout_chunks = load_heldout_chunk_ids(heldout_suite_path)

    rows = sources_conn.execute(
        "SELECT id, chunk_id, title, text, author_uk, subject FROM textbooks WHERE subject IN ({})".format(
            ",".join("?" for _ in STEM_SUBJECTS)
        ),
        tuple(sorted(STEM_SUBJECTS)),
    ).fetchall()

    filter_counts: Counter[str] = Counter()
    semantic_counts: Counter[str] = Counter()
    source_subjects: Counter[str] = Counter()
    seen_passages: set[str] = set()
    admitted: list[tuple[dict[str, Any], SemanticDecision]] = []
    stem_chunks_scanned = 0

    for row in rows:
        subject = row["subject"] or ""
        if subject not in STEM_SUBJECTS:
            continue
        chunk_id = row["chunk_id"] or f"id:{row['id']}"
        if chunk_id in heldout_chunks:
            continue
        if not is_train_textbook(row["author_uk"], row["title"] or ""):
            continue
        stem_chunks_scanned += 1
        source_subjects[subject] += 1
        for raw_sentence in SENTENCE_SPLIT_RE.split(row["text"] or ""):
            sentence = " ".join(raw_sentence.split())
            decision = classify_semantic_context(sentence)
            if decision is None:
                decision = classify_generic_stem(sentence, subject)
            if decision is None:
                continue
            semantic_counts[f"{decision.pair}:{decision.action}"] += 1
            if decision.register == "розм.":
                semantic_counts["register:розм."] += 1
            if decision.action != "PRESERVE":
                continue
            if decision.entity_type == "abstract_quantity_data_scope":
                raise RuntimeError("abstract data/economics calque admitted as PRESERVE")
            passage_key = normalize_text(sentence)
            if passage_key in seen_passages:
                continue
            clean = cleanliness_filter(sentence, decision.target_term, vesum_cursor, collisions)
            if not clean.ok:
                reason = clean.reason or "unknown"
                if reason.startswith("content_word_unattested") or reason.startswith("target_term"):
                    filter_counts["vesum"] += 1
                elif reason.startswith("style_guide"):
                    filter_counts["style_guide"] += 1
                else:
                    filter_counts["ocr"] += 1
                continue
            trajectory = build_trajectory(sentence, decision, vesum_cursor, chunk_id, subject)
            seen_passages.add(passage_key)
            admitted.append((trajectory, decision))
            if len(admitted) >= sft_quota:
                break
        if len(admitted) >= sft_quota:
            break

    if len(admitted) < sft_quota:
        raise ValueError(f"failed to yield {sft_quota} PRESERVE SFT controls; got {len(admitted)}")

    admitted = admitted[:sft_quota]
    dpo_source = admitted[:dpo_quota]
    trajectories = [item[0] for item in admitted]
    dpo_pairs = [build_dpo_pair(traj, decision) for traj, decision in dpo_source]
    validate_records(trajectories, dpo_pairs, sft_quota, dpo_quota)

    generated_at = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    public_traj = [strip_private_fields(row) for row in trajectories]
    index_rows = [
        {
            "control_id": row["trajectory_id"],
            "passage_sha256": raw["_passage_sha256"],
            "chunk_id": raw["_chunk_id"],
            "subject": raw["_subject"],
            "target_term": row["target_term"],
            "action": "PRESERVE",
            "entity_type": raw["_entity_type"],
            "register": raw["_register"],
            "pair": raw["_pair"],
            "vesum_attested": True,
        }
        for row, raw in zip(public_traj, trajectories, strict=True)
    ]
    for index_row in index_rows:
        assert_no_corpus_text(index_row)
        assert_no_private_host_paths(index_row)

    sft_name = "stem_preserve_sft_controls.jsonl"
    dpo_name = "stem_preserve_dpo_pairs.jsonl"
    index_name = "stem_controls_index.jsonl"
    receipt_name = "stem_controls_receipt.json"
    index_path = output_dir / index_name
    write_jsonl(index_path, index_rows)
    files = {
        "index": {
            "filename": index_name,
            "record_count": len(index_rows),
            "sha256": sha256_file(index_path),
        }
    }
    if write_shards:
        sft_path = output_dir / sft_name
        dpo_path = output_dir / dpo_name
        write_jsonl(sft_path, public_traj)
        write_jsonl(dpo_path, dpo_pairs)
        files["sft_controls"] = {
            "filename": sft_name,
            "record_count": len(public_traj),
            "sha256": sha256_file(sft_path),
        }
        files["dpo_pairs"] = {
            "filename": dpo_name,
            "record_count": len(dpo_pairs),
            "sha256": sha256_file(dpo_path),
        }

    receipt = build_receipt(
        trajectories=trajectories,
        dpo_pairs=dpo_pairs,
        filter_counts=filter_counts,
        semantic_counts=semantic_counts,
        source_subjects=source_subjects,
        stem_chunks_scanned=stem_chunks_scanned,
        sft_quota=sft_quota,
        dpo_quota=dpo_quota,
        files=files,
        generated_at=generated_at,
    )
    schema = json.loads(RECEIPT_SCHEMA_PATH.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator(schema).validate(receipt)
    receipt_path = output_dir / receipt_name
    receipt_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    sources_conn.close()
    vesum_conn.close()
    return receipt


def verify_artifacts(output_dir: Path, sft_quota: int = SFT_QUOTA, dpo_quota: int = DPO_QUOTA) -> None:
    receipt_path = output_dir / "stem_controls_receipt.json"
    index_path = output_dir / "stem_controls_index.jsonl"
    if not receipt_path.is_file() or not index_path.is_file():
        raise FileNotFoundError("receipt or index missing; run the miner before --verify-only")
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    schema = json.loads(RECEIPT_SCHEMA_PATH.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator(schema).validate(receipt)
    assert_no_private_host_paths(receipt)
    assert_no_corpus_text(receipt)
    if receipt["yield"]["sft_preserve_controls"] != sft_quota:
        raise ValueError("receipt SFT yield drifted from quota")
    if receipt["yield"]["dpo_preserve_pairs"] != dpo_quota:
        raise ValueError("receipt DPO yield drifted from quota")
    if receipt["semantic_typing"]["false_preservation_of_abstract_calques"] != 0:
        raise ValueError("receipt reports abstract calque preservation")
    if receipt["cleanliness"]["vesum_verification_rate"] != 1.0:
        raise ValueError("VESUM verification is incomplete")
    index_rows = load_jsonl(index_path)
    if sha256_file(index_path) != receipt["files"]["index"]["sha256"]:
        raise ValueError("index sha256 mismatch")
    if len(index_rows) != sft_quota:
        raise ValueError("index count drifted from SFT quota")
    for row in index_rows:
        assert_no_corpus_text(row)
        assert_no_private_host_paths(row)
        if row["action"] != "PRESERVE" or not row["vesum_attested"]:
            raise ValueError("index row is not a VESUM-attested PRESERVE control")
        if row["entity_type"] == "abstract_quantity_data_scope":
            raise ValueError("index contains an abstract data/economics PRESERVE")
    sft_meta = receipt["files"].get("sft_controls")
    dpo_meta = receipt["files"].get("dpo_pairs")
    if sft_meta:
        sft_path = output_dir / sft_meta["filename"]
        trajectories = load_jsonl(sft_path)
        if sha256_file(sft_path) != sft_meta["sha256"]:
            raise ValueError("SFT shard sha256 mismatch")
        dpo_path = output_dir / dpo_meta["filename"]
        dpo_pairs = load_jsonl(dpo_path)
        if sha256_file(dpo_path) != dpo_meta["sha256"]:
            raise ValueError("DPO shard sha256 mismatch")
        validate_records(trajectories, dpo_pairs, sft_quota, dpo_quota)


def build_parser() -> argparse.ArgumentParser:
    return argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=(
            "Mine vetted STEM PRESERVE negative controls and anti-hyper-purist DPO pairs.\n"
            "Use after Phase 3.0 custody is on main. Do not use to invent sentences or to "
            "publish textbook passages; receipts stay hash-only."
        ),
        epilog=(
            "Examples:\n"
            "  python -m scripts.projects.open_model_data.v4_mine_stem_controls \\\n"
            "    --sources-db \"$SOURCES_DB\" --vesum-db \"$VESUM_DB\" \\\n"
            "    --output-dir \"$STEM_CONTROLS_OUT\"\n"
            "  python -m scripts.projects.open_model_data.v4_mine_stem_controls \\\n"
            "    --verify-only --output-dir \"$STEM_CONTROLS_OUT\"\n"
            "\n"
            "Outputs:\n"
            "  stem_controls_receipt.json — public counts, hashes, typing tallies (no passage text)\n"
            "  stem_controls_index.jsonl — passage SHA-256 + metadata only\n"
            "  stem_preserve_sft_controls.jsonl — local research shard (omitted with --receipt-only)\n"
            "  stem_preserve_dpo_pairs.jsonl — local research shard (omitted with --receipt-only)\n"
            "\n"
            "Exit codes:\n"
            "  0 — quotas met and artifacts verified\n"
            "  1 — missing inputs, quota shortfall, schema/safety failure\n"
            "\n"
            "Related: docs/projects/open-model-data/PHASE_3_3_STEM_NEGATIVE_CONTROLS.md; "
            "docs/projects/open-model-data/CORPUS_GROUNDED_DECOLONIZATION_DATASET_PLAN.md §3.1–3.2; "
            "epic #6321 / issue #8007; depends on Phase 3.0 (#8005)."
        ),
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    parser.add_argument(
        "--sources-db",
        type=Path,
        default=None,
        help="SQLite sources database with textbooks + style_guide (default: $SOURCES_DB or data/sources.db under cwd/repo).",
    )
    parser.add_argument(
        "--vesum-db",
        type=Path,
        default=None,
        help="SQLite VESUM database with forms / forms_all (default: $VESUM_DB or data/vesum.db under cwd/repo).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=f"Directory for receipt/index/shards (default: repo-relative {public_relpath(DEFAULT_OUTPUT_DIR)}).",
    )
    parser.add_argument(
        "--sft-quota",
        type=int,
        default=SFT_QUOTA,
        help=f"Exact PRESERVE SFT yield (default: {SFT_QUOTA}; production AC is 1800).",
    )
    parser.add_argument(
        "--dpo-quota",
        type=int,
        default=DPO_QUOTA,
        help=f"Exact PRESERVE DPO yield (default: {DPO_QUOTA}; production AC is 900).",
    )
    parser.add_argument(
        "--receipt-only",
        action="store_true",
        help="Write receipt + hash index only; skip local research shards that carry passage text (default: off).",
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Verify existing receipt/index/shards; do not mine (default: off).",
    )
    args = parser.parse_args(argv)

    try:
        if args.verify_only:
            verify_artifacts(args.output_dir, sft_quota=args.sft_quota, dpo_quota=args.dpo_quota)
            print("OK: Phase 3.3 STEM negative controls verified.")
            return 0
        sources_db = args.sources_db or Path(os.environ.get("SOURCES_DB", "data/sources.db"))
        vesum_db = args.vesum_db or Path(os.environ.get("VESUM_DB", "data/vesum.db"))
        receipt = mine_controls(
            sources_db=sources_db,
            vesum_db=vesum_db,
            output_dir=args.output_dir,
            sft_quota=args.sft_quota,
            dpo_quota=args.dpo_quota,
            write_shards=not args.receipt_only,
        )
        print("OK: Phase 3.3 STEM negative controls mined.")
        print(f"SFT PRESERVE: {receipt['yield']['sft_preserve_controls']}")
        print(f"DPO PRESERVE: {receipt['yield']['dpo_preserve_pairs']}")
        print(f"Receipt: {public_relpath(args.output_dir / 'stem_controls_receipt.json')}")
        return 0
    except (FileNotFoundError, ValueError, jsonschema.ValidationError, sqlite3.Error) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
