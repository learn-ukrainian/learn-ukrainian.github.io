"""Removal-only admission of meanings in the published practice deck (#9160).

This module never cleans a Ukrainian dictionary article into a new meaning.
An unsupported meaning is represented by two empty display fields so grammar,
stress and other independent practice can remain available.
"""

from __future__ import annotations

import re
import sqlite3
import unicodedata
from contextlib import closing
from pathlib import Path
from typing import Any

# Individually identified wrong senses and fragments in the three independent
# language reviews. Quarantine the displayed meaning, not the lexeme or its
# independently keyed non-meaning exercises.
REVIEWED_WRONG_LEMMAS = frozenset({
    "вгору", "тобто", "турецький", "тур", "перебувати", "запланований", "нощно",
    "садка", "прикладка", "сонорний", "зачин", "держава", "кілька", "постав",
    "хрещеник", "звільнення", "виснаження", "грецький", "надмірність",
    "плюнути", "горщик", "меткий", "цілина", "багацько", "друзяка",
    "славно", "хай", "комплект", "піт", "дрова", "гетьман", "хрестини",
    "чайна", "іній", "тихіший", "посинілий", "постарілий", "ялинковий",
    "доповідач", "ясна", "чхання",
    "абітурієнт", "гаразд", "відмова", "хвалити", "узутий", "шумно",
    "розуміння", "коробка", "кардіолог", "джаз", "над", "по", "битися",
    "проте", "малі", "недержавний", "путін", "адрес", "город",
    "гуртожиток", "дебати", "себе", "хтось", "ніхто",
})
_YEAR = re.compile(r"(?<!\d)(?:19[2-8]\d|199[01])(?!\d)")
_HEADER = re.compile(
    r"(?:^|\s)(?:Прикм\.|Присл\.|Дієприкм\.|Дієпр\.|Зменш\.|"
    r"Абстр\.\s*ім\.|Однокр\.|Стос\.|Пестл\.|Збірн\.|Жін\.|"
    r"Вищ\.\s*ст\.|Дія\s+за\s+знач\.|Стан\s+за\s+знач\.|"
    r"Те\s+саме,?\s+що|Див\.)\s",
    re.IGNORECASE,
)
_ARTICLE = re.compile(r"(?:\d+\s*》|\|\||◇|‖|[¹²³⁴⁵⁶⁷⁸⁹⁰]|\b[IVX]{1,3}\s*[-–])")
_QUOTE = re.compile(r"[«»“”„\"\[\]]")
_EN_META = re.compile(r"\b(?:Conjugation:|Synonym of|Initialism of|Augm|Sławno)\b", re.I)


def _key(text: str) -> str:
    text = "".join(char for char in text if unicodedata.category(char) != "Mn")
    return re.sub(r"\s+", " ", text.casefold()).strip(" .,:;")


def english(text: str) -> bool:
    latin = sum("LATIN" in unicodedata.name(char, "") for char in text)
    cyrillic = sum("CYRILLIC" in unicodedata.name(char, "") for char in text)
    return latin > cyrillic


def _candidate_alternatives(candidate: str) -> set[str]:
    """Extract literal alternatives only; never synthesize a translation."""
    candidate = re.split(r"\s+Conjugation:", candidate, flags=re.I)[0]
    candidate = re.sub(r"^\s*\([^)]*\)\s*", "", candidate)
    alternatives = [re.sub(r"^\s*\d+[.)]\s*", "", part) for part in re.split(r"[;,()\[\]]", candidate)]
    return {_key(part) for part in alternatives if _key(part)}


def _candidates_support_display(candidates: list[Any], display: str) -> bool:
    """Every displayed alternative must occur literally in the source field."""
    targets = {_key(part) for part in re.split(r"[;,]", display) if _key(part)}
    options = set().union(*(_candidate_alternatives(candidate) for candidate in candidates if isinstance(candidate, str)))
    return bool(targets) and targets <= options


def meaning_problem(text: str, lemma: str, sum11: list[str] | None = None) -> str | None:
    """Return the first reason a complete displayed field must be removed."""
    if not text.strip():
        return "missing"
    if lemma.casefold() in REVIEWED_WRONG_LEMMAS:
        return "reviewed_wrong_sense"
    if _YEAR.search(text):
        return "dated_citation"
    if "(" in text or ")" in text:
        return "parenthesized_citation"
    if _QUOTE.search(text):
        return "example_quotation"
    if _ARTICLE.search(text) or _HEADER.search(text):
        return "dictionary_fragment"
    if _EN_META.search(text):
        return "dictionary_fragment"
    if not english(text):
        # A second sentence in a raw article is commonly an example or another
        # sense. Do not cut it into an invented Ukrainian definition.
        if re.search(r"[.!?]\s+\S", text) or re.match(r"\s*[А-ЯІЇЄҐ]{2,}\b", text):
            return "dictionary_fragment"
        if re.search(r"\b(?:приск\.|перен\.|заст\.|розм\.|діал\.|ч\.|ж\.|с\.)\s", text, re.I):
            return "dictionary_fragment"
    key = _key(text)
    if key and any(key == _key(definition) or (len(key) >= 24 and key in _key(definition)) for definition in sum11 or []):
        return "same_word_sum11"
    return None


def source_bound_meaning(
    entry: dict[str, Any], displayed: str, clean: str, sense: dict[str, Any] | None,
    sum11: list[str] | None = None, level: str | None = None,
) -> tuple[dict[str, str] | None, str | None]:
    """Admit only existing display text bound to an attributed matching field."""
    lemma = str(entry.get("lemma") or "")
    for field in (displayed, clean):
        problem = meaning_problem(field, lemma, sum11)
        if problem:
            return None, problem
    if english(displayed) != english(clean):
        return None, "field_language_mismatch"
    if sense is not None:
        source = str(sense.get("source") or "").strip()
        field = "learner_en" if english(displayed) else "learner_uk"
        candidates = sense.get(field)
        if isinstance(candidates, str):
            candidates = [candidates]
        if (source and isinstance(candidates, list) and any(
            isinstance(candidate, str) and _key(displayed) == _key(candidate) for candidate in candidates
        ) and (english(displayed) or source.casefold() in {"sum20_vetted", "vts_vetted", "ulif_checked"})):
            return {"source": source, "field": f"senses.{field}"}, None
        return None, "unbound_sense"
    enrichment = entry.get("enrichment")
    enrichment = enrichment if isinstance(enrichment, dict) else {}
    if not english(displayed):
        # Legacy Ukrainian article text has no explicit sense ID. A verbatim,
        # single-definition card is the only safe non-derived legacy binding.
        cards = enrichment.get("definition_cards")
        if isinstance(cards, list):
            matches = [
                card for card in cards if isinstance(card, dict)
                and str(card.get("id") or "").casefold() in {"sum20", "vts"}
                and card.get("definitions") == [displayed]
            ]
            if len(matches) == 1 and _key(displayed) == _key(str(entry.get("gloss") or "")):
                return {"source": str(matches[0].get("source") or matches[0].get("id")),
                        "field": "enrichment.definition_cards.definitions"}, None
        return None, "unbound_ukrainian"
    translation = enrichment.get("translation")
    translation = translation if isinstance(translation, dict) else {}
    source = str(translation.get("source") or "").strip()
    if not source or any(token in source.casefold() for token in ("e2u", "reverse", "en→uk", "en->uk")):
        return None, "unsupported_english_source"
    # A dictionary's reverse candidates cannot bind a Ukrainian display to a
    # sense. Existing English display text is the needed sense anchor.
    original = str(entry.get("gloss") or "")
    if not english(original) and not (level == "A1" and source == "learner_english_gloss"):
        return None, "unbound_english_sense"
    candidates = translation.get("en")
    if isinstance(candidates, str):
        candidates = [candidates]
    if not isinstance(candidates, list) or not _candidates_support_display(candidates, displayed):
        return None, "unattributed_english"
    return {"source": source, "field": "enrichment.translation.en"}, None


def load_sum11_definitions(words: set[str], path: Path) -> dict[str, list[str]]:
    """Read selected same-word rows; a supplied invalid database is an error."""
    if not words:
        return {}
    with closing(sqlite3.connect(f"file:{path}?mode=ro", uri=True)) as conn:
        return {
            word: [str(row[0]) for row in conn.execute(
                "SELECT definition FROM sum11 WHERE word=? COLLATE NOCASE", (word,)
            )]
            for word in sorted(words)
        }
