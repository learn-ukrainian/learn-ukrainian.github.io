#!/usr/bin/env python3
"""Enrich the Word Atlas lexicon manifest with source-verified dictionary data.

For each lemma in ``site/src/data/lexicon-manifest.json`` this adds an
``enrichment`` block built from DETERMINISTIC local-dictionary lookups (no LLM,
no fabrication):

- **morphology** — full VESUM paradigm (``data/vesum.db``), forms decoded into
  human-readable Ukrainian grammatical labels, with optional stress display
  forms from ``ukrainian-word-stress``.
- **meaning** — legacy single-source meaning kept for compatibility.
- **definition_cards** — separate СУМ-20 and СУМ-11 definition cards with
  source caveats.
- **cefr** — PULS CEFR lookup when available.
- **literary_attestation** — exact-form literary corpus hit when available.
- **synonyms** — source-attested Ukrainian candidates from clean slovnyk.me
  synonym dictionaries, with noisy legacy sources kept A1-sense allowlisted.
- **sections.synonyms / sections.idioms** — slovnyk.me per-lemma lookup cache
  (Караванський + Словник синонімів; Фразеологічний).
- **heritage warning alternatives** — slovnyk.me correction dictionaries
  (Антоненко-Давидович, «Неправильно-правильно», Штепа чужослів).
- **etymology** — Goroh cached extracts first, ЕСУМ fallback, uk.wiktionary
  dump fallback for remaining single-word gaps
  (``data/sources.db``; deterministic local lookup only).

Every field carries its ``source`` so the UI can attribute it. Lemmas with no
dictionary hit simply get an empty enrichment and the UI keeps its honest
"not yet available" note. Multi-word phrases are skipped for single-lemma
morphology and etymology.

Run from the repo root (needs ``data/`` which is excluded from worktrees)::

    .venv/bin/python scripts/lexicon/enrich_manifest.py
"""

from __future__ import annotations

import datetime as dt
import html
import json
import os
import re
import sqlite3
import sys
import time
import unicodedata
from functools import lru_cache
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import quote

import requests

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.lexicon.build_kaikki_lookup import KAIKKI_SOURCE
from scripts.lexicon.build_kaikki_lookup import lookup_key as kaikki_lookup_key
from scripts.lexicon.heritage_classifier import classify_lemma
from scripts.verification.vesum import verify_lemma, verify_word
from scripts.wiki.slovnyk_me import primary_synonym_sense_text

MANIFEST = ROOT / "site" / "src" / "data" / "lexicon-manifest.json"
SOURCES_DB = ROOT / "data" / "sources.db"
KAIKKI_LOOKUP = ROOT / "data" / "lexicon" / "kaikki_uk_lookup.json"


def _default_slovnyk_cache() -> Path:
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


SLOVNYK_CACHE = _default_slovnyk_cache()

_CYRILLIC_WORD_CHARS = "A-Za-zА-Яа-яЄєІіЇїҐґ0-9'’ʼ-"
_LATIN_RE = re.compile(r"[A-Za-z]")
_UKRAINIAN_TEXT_RE = re.compile(r"^[А-Яа-яЄєІіЇїҐґ'’ʼ -]+$")
_STRESS_MARK_RE = re.compile("[\u0300\u0301]")
_NON_CACHE_CHARS_RE = re.compile(r"[^0-9A-Za-zА-Яа-яЄєІіЇїҐґ'’ʼ-]+")
_SOURCE_TAIL_RE = re.compile(r"\s+Джерело:.*$", flags=re.IGNORECASE | re.DOTALL)
_IDIOM_DOT_PLACEHOLDER = "<DOT>"
_IDIOM_ABBREVIATIONS_WITH_INTERNAL_DOTS = (
    "і т. ін.",
    "і т. д.",
    "т. ін.",
    "т. д.",
    "перев.",
    "зі сл.",
)
_SLOVNYK_DELAY_SECONDS = 0.12
_SLOVNYK_USER_AGENT = "learn-ukrainian-word-atlas/1.0 (noncommercial educational per-lemma lookup; issue #2985)"
_STRESS_SOURCE = "ukrainian-word-stress"
_CEFR_SOURCE = "PULS CEFR"
_LITERARY_SOURCE = "literary_fts"
_TRANSLATION_SOURCE = "dmklinger"
_SUM20_COVERED_INITIALS = set("абвгґдеєжзиіїйклмнопр")
_UKRAINIAN_WORD_RE = re.compile(r"^[А-Яа-яЄєІіЇїҐґ'’ʼ-]+$")
_UKRAINIAN_VOWELS = set("аеєиіїоуюяАЕЄИІЇОУЮЯ")
_RUSSIAN_LABELED_CYRILLIC_RE = re.compile(r"Russian[^.;:]*[А-Яа-яЁёЫыЭэЪъ]", flags=re.IGNORECASE)

_SLOVNYK_DICT_LABELS: dict[str, str] = {
    "newsum": "Словник української мови у 20 томах (СУМ-20)",
    "synonyms": "Словник синонімів української мови",
    "synonyms_karavansky": "Словник синонімів Караванського",
    "phraseology": "Фразеологічний словник української мови",
    "davydov": "«Як ми говоримо» Антоненка-Давидовича",
    "voloschak": "Неправильно-правильно",
    "foreign_shtepa": "Словник чужослів Павла Штепи",
}
_SLOVNYK_LOOKUP_SLUGS = tuple(_SLOVNYK_DICT_LABELS)
_SLOVNYK_SYNONYM_SLUGS = ("synonyms_karavansky", "synonyms")
_SLOVNYK_WARNING_SLUGS = ("davydov", "voloschak", "foreign_shtepa")
_SLOVNYK_BASE = "https://slovnyk.me"
_SLOVNYK_CACHE_SCHEMA_VERSION = 2
_WARNING_CLASSIFICATIONS = {"russianism", "sovietism", "surzhyk"}

_SYNONYM_LABEL_WORDS = {
    "ант",
    "г",
    "див",
    "діал",
    "д",
    "жм",
    "зах",
    "з",
    "заст",
    "збірн",
    "зневажл",
    "жарт",
    "ід",
    "ім",
    "іс",
    "кн",
    "книжн",
    "лайл",
    "нар",
    "ок",
    "перен",
    "пестл",
    "поет",
    "пор",
    "предик",
    "пр",
    "підсил",
    "р",
    "рідко",
    "рідше",
    "розм",
    "с",
    "син",
    "уроч",
    "фам",
    "фольк",
    "част",
}
_WARNING_ALT_STOP_WORDS = {"див"}
_SYNONYM_STOP_STARTS = {
    "від",
    "для",
    "з",
    "за",
    "зі",
    "із",
    "коли",
    "на",
    "про",
    "сл",
    "у",
    "який",
    "яка",
    "яке",
    "які",
    "як",
}
_SYNONYM_LABEL_RE = re.compile(
    r"\b(" + "|".join(re.escape(word) for word in sorted(_SYNONYM_LABEL_WORDS, key=len, reverse=True)) + r")\.?\b",
    flags=re.IGNORECASE,
)

_last_slovnyk_fetch = 0.0
_stressifier: Any | None = None

# Same-sense A1 allowlist. A synonym is emitted only when it is both present in
# a source row and included here for the lemma's course gloss sense.
_A1_SENSE_SYNONYMS: dict[str, tuple[str, ...]] = {
    "абетка": ("алфавіт", "азбука"),
    "актор": ("артист", "лицедій", "комедіант", "виконавець"),
    "батько": ("тато", "отець", "татусь", "татко"),
    "вранці": ("зранку", "ранком", "рано"),
    "вставати": ("зводитися", "підводитися", "підхоплюватися"),
    "вчитель": ("педагог", "викладач", "вихователь", "навчитель"),
    "гарний": ("красивий", "вродливий", "хороший", "гожий"),
    "добре": ("гаразд", "нормально", "непогано", "незле", "славно"),
    "дім": ("будинок", "хата", "домівка"),
    "книга": ("книжка",),
    "ліжко": ("постіль",),
    "літера": ("буква",),
    "мама": ("мати", "матуся", "мамуся"),
    "навчатися": ("вчитися", "учитися"),
    "нарешті": ("зрештою", "врешті-решт"),
    "поспішати": ("спішити", "квапитися"),
    "потім": ("тоді", "далі"),
    "привіт": ("вітання", "привітання", "уклін", "поклін"),
    "робота": ("праця",),
    "сон": ("сновидіння",),
    "спочатку": ("спершу",),
    "стілець": ("крісло", "стільчик"),
    "тато": ("батько", "татусь"),
    "фото": ("фотографія", "світлина", "знімок", "фотознімок"),
    "чудово": ("блискуче", "прекрасно", "чудесно"),
}

_SYNONYM_HEADWORD_POS_OVERRIDES: dict[str, str] = {
    "добре": "adv",
    "голосний": "noun",
    "привіт": "noun",
}

_MANIFEST_POS_TO_VESUM_POS: dict[str, str] = {
    "adjective": "adj",
    "adj": "adj",
    "adverb": "adv",
    "adv": "adv",
    "infinitive": "verb",
    "noun": "noun",
    "proper noun": "noun",
    "verb": "verb",
}

_BALLA_LOOKUPS: dict[str, tuple[str, ...]] = {
    "дім": ("house",),
    "книга": ("book",),
    "ліжко": ("bed",),
    "літера": ("letter",),
    "мама": ("mother",),
    "навчатися": ("study",),
    "нарешті": ("finally",),
    "поспішати": ("hurry",),
    "потім": ("then",),
    "робота": ("work",),
    "сон": ("dream",),
    "спочатку": ("first",),
    "стілець": ("chair",),
    "тато": ("father", "dad"),
    "фото": ("photo", "photograph"),
    "чудово": ("wonderful", "great", "fine"),
}

_BLOCKED_SYNONYMS = {
    "java",
    "ma",
    "hot seat",
    "електричний стілець",
    "стілець смерті",
    "жахливо",
    "лихо",
    "умбра",
    "палена умбра",
    "темно-коричневий",
    "шоколад",
    "хризантема флористів",
    "флористська хризантема",
}

_COMPOSITIONAL_ETYMOLOGY_EXCLUSIONS = {
    "а тебе?",
    "а у тебе?",
    "до побачення!",
    "добрий вечір",
    "доброго ранку",
    "добрий день",
    "дуже приємно",
    "на все добре",
    "як справи?",
}

_DERIVATIONAL_ETYMLOGY_BASES: dict[str, tuple[str, ...]] = {
    "добре": ("добрий", "добро"),
    "чудово": ("чудо", "чудовий"),
    "пізно": ("пізній",),
    "нормально": ("нормальний", "норма"),
    "сьома": ("сьомий", "сім"),
    "сьомий": ("сім",),
    "навчатися": ("навчати", "вчити", "учити"),
    "навчати": ("вчити", "учити"),
    "вмиватися": ("вмивати", "мити"),
    "вмивати": ("мити",),
    "збиратися": ("збирати", "брати"),
    "збирати": ("брати",),
    "одягатися": ("одягати", "одяг"),
    "одягати": ("одяг",),
    "повертатися": ("повертати", "вертати"),
    "повертати": ("вертати",),
}

_ORDINAL_ETYMLOGY_BASES: dict[str, tuple[str, ...]] = {
    "перша": ("перший", "один"),
    "перше": ("перший", "один"),
    "перший": ("один",),
    "друга": ("другий", "два"),
    "друге": ("другий", "два"),
    "другий": ("два",),
    "третя": ("третій", "три"),
    "третє": ("третій", "три"),
    "третій": ("три",),
    "четверта": ("четвертий", "чотири"),
    "четверте": ("четвертий", "чотири"),
    "четвертий": ("чотири",),
    "п'ята": ("п'ятий", "п'ять"),
    "п'яте": ("п'ятий", "п'ять"),
    "п'ятий": ("п'ять",),
    "шоста": ("шостий", "шість"),
    "шосте": ("шостий", "шість"),
    "шостий": ("шість",),
    "сьома": ("сьомий", "сім"),
    "сьоме": ("сьомий", "сім"),
    "сьомий": ("сім",),
    "восьма": ("восьмий", "вісім"),
    "восьме": ("восьмий", "вісім"),
    "восьмий": ("вісім",),
    "дев'ята": ("дев'ятий", "дев'ять"),
    "дев'яте": ("дев'ятий", "дев'ять"),
    "дев'ятий": ("дев'ять",),
}

# VESUM tag token → human-readable Ukrainian grammatical label.
_TAG_LABELS: dict[str, str] = {
    "v_naz": "називний",
    "v_rod": "родовий",
    "v_dav": "давальний",
    "v_zna": "знахідний",
    "v_oru": "орудний",
    "v_mis": "місцевий",
    "v_kly": "кличний",
    "s": "однина",
    "p": "множина",
    "m": "чол.",
    "f": "жін.",
    "n": "сер.",
    "pres": "теперішній",
    "futr": "майбутній",
    "past": "минулий",
    "impf": "наказовий",
    "impr": "наказовий",
    "inf": "інфінітив",
    "1": "1 ос.",
    "2": "2 ос.",
    "3": "3 ос.",
}

_POS_LABELS: dict[str, str] = {
    "noun": "іменник",
    "verb": "дієслово",
    "adj": "прикметник",
    "adv": "прислівник",
    "numr": "числівник",
    "prep": "прийменник",
    "conj": "сполучник",
    "part": "частка",
    "pron": "займенник",
    "intj": "вигук",
}

_NOUN_CASE_ORDER = (
    "називний",
    "родовий",
    "давальний",
    "знахідний",
    "орудний",
    "місцевий",
    "кличний",
)
_NOUN_GENDERS = {"чол.", "жін.", "сер."}
_NUMBERS = ("однина", "множина")
_PERSONS = ("1", "2", "3")
_VERB_TENSES = ("теперішній", "майбутній")
_PAST_KEYS = ("чол.", "жін.", "сер.", "множина")


def _decode_tag(tag: str) -> str:
    """Turn a raw VESUM tag into a short human label, dropping noise tokens."""
    parts = [p for p in tag.split(":") if p not in {"verb", "noun", "adj", "adv"}]
    labels = [_TAG_LABELS[p] for p in parts if p in _TAG_LABELS]
    # De-dup while preserving order.
    seen: set[str] = set()
    out = [x for x in labels if not (x in seen or seen.add(x))]
    return ", ".join(out)


def _split_label(label: str) -> list[str]:
    return [part.strip() for part in label.split(",") if part.strip()]


def _join_variants(forms: list[str]) -> str:
    seen: set[str] = set()
    variants = [form for form in forms if form and not (form in seen or seen.add(form))]
    return " / ".join(variants)


def _is_infinitive_form(form: str) -> bool:
    return form.endswith(("ти", "тися", "тись"))


def _parse_noun_label(label: str) -> tuple[str, str] | None:
    parts = _split_label(label)
    if len(parts) != 2:
        return None
    head, case = parts
    if case not in _NOUN_CASE_ORDER:
        return None
    if head in _NOUN_GENDERS:
        return case, "singular"
    if head == "множина":
        return case, "plural"
    return None


def _build_noun_paradigm(forms: list[dict[str, str]]) -> dict | None:
    cells: dict[str, dict[str, list[str]]] = {
        case: {"singular": [], "plural": []} for case in _NOUN_CASE_ORDER
    }
    for row in forms:
        parsed = _parse_noun_label(row.get("label", ""))
        if not parsed:
            return None
        case, number = parsed
        cells[case][number].append(row.get("form", ""))

    cases: dict[str, dict[str, str]] = {}
    for case in _NOUN_CASE_ORDER:
        singular = _join_variants(cells[case]["singular"])
        plural = _join_variants(cells[case]["plural"])
        if not singular or not plural:
            return None
        cases[case] = {"singular": singular, "plural": plural}
    return {"kind": "noun", "cases": cases}


def _parse_person_slot(parts: list[str]) -> tuple[str, str] | None:
    if len(parts) != 3 or parts[1] not in _NUMBERS:
        return None
    person = parts[2].removesuffix(" ос.").strip()
    if person not in _PERSONS:
        return None
    return parts[1], person


def _build_verb_paradigm(forms: list[dict[str, str]]) -> dict | None:
    infinitive: list[str] = []
    tenses: dict[str, dict[str, dict[str, list[str]]]] = {
        tense: {number: {person: [] for person in _PERSONS} for number in _NUMBERS}
        for tense in _VERB_TENSES
    }
    imperative: dict[str, dict[str, list[str]]] = {
        number: {person: [] for person in _PERSONS} for number in _NUMBERS
    }
    past: dict[str, list[str]] = {key: [] for key in _PAST_KEYS}

    for row in forms:
        form = row.get("form", "")
        label = row.get("label", "")
        parts = _split_label(label)
        if label == "інфінітив":
            # VESUM also emits short/non-primary raw-tag variants under the same
            # decoded label; keep the structured infinitive to actual -ти forms.
            if _is_infinitive_form(form):
                infinitive.append(form)
            continue
        if len(parts) == 2 and parts[0] == "минулий" and parts[1] in past:
            past[parts[1]].append(form)
            continue
        if parts and parts[0] == "наказовий":
            parsed = _parse_person_slot(parts)
            if not parsed:
                return None
            number, person = parsed
            imperative[number][person].append(form)
            continue
        if parts and parts[0] in tenses:
            parsed = _parse_person_slot(parts)
            if not parsed:
                return None
            number, person = parsed
            tenses[parts[0]][number][person].append(form)
            continue
        return None

    infinitive_value = _join_variants(infinitive)
    if not infinitive_value:
        return None

    collapsed_tenses: dict[str, dict[str, dict[str, str]]] = {}
    for tense in _VERB_TENSES:
        has_tense = any(
            tenses[tense][number][person] for number in _NUMBERS for person in _PERSONS
        )
        if not has_tense:
            continue
        collapsed_tenses[tense] = {"однина": {}, "множина": {}}
        for number in _NUMBERS:
            for person in _PERSONS:
                value = _join_variants(tenses[tense][number][person])
                if not value:
                    return None
                collapsed_tenses[tense][number][person] = value

    collapsed_imperative: dict[str, dict[str, str]] = {}
    for number in _NUMBERS:
        for person in _PERSONS:
            value = _join_variants(imperative[number][person])
            if not value:
                continue
            collapsed_imperative.setdefault(number, {})[person] = value

    collapsed_past: dict[str, str] = {}
    has_past = any(past.values())
    if has_past:
        for key in _PAST_KEYS:
            value = _join_variants(past[key])
            if not value:
                return None
            collapsed_past[key] = value

    if not collapsed_tenses and not collapsed_imperative and not collapsed_past:
        return None

    paradigm: dict[str, object] = {"kind": "verb", "infinitive": infinitive_value}
    if collapsed_tenses:
        paradigm["tenses"] = collapsed_tenses
    if collapsed_imperative:
        paradigm["imperative"] = collapsed_imperative
    if collapsed_past:
        paradigm["past"] = collapsed_past
    return paradigm


def _build_paradigm(pos_raw: str, forms: list[dict[str, str]]) -> dict | None:
    if pos_raw == "noun":
        return _build_noun_paradigm(forms)
    if pos_raw == "verb":
        return _build_verb_paradigm(forms)
    return None


def get_apostrophe_variants(word: str) -> list[str]:
    """Generate apostrophe variants for source rows with inconsistent encoding."""
    variants = {word}
    for char in ("'", "’", "ʼ"):
        if char in word:
            for replacement in ("'", "’", "ʼ"):
                variants.add(word.replace(char, replacement))
    return sorted(variants)


def _unescape_html_entities(text: str) -> str:
    """Unescape HTML entities, including double-escaped ones."""
    if not text:
        return text
    previous = text
    for _ in range(3):
        current = html.unescape(previous)
        if current == previous:
            break
        previous = current
    return previous.replace("\u00a0", " ")


def clean_html_entities(text: str) -> str:
    """Unescape HTML entities, including double-escaped ones, and normalise spaces."""
    return re.sub(r"\s+", " ", _unescape_html_entities(text)).strip()


def clean_gloss(gloss: str) -> str:
    """Strip pedagogical ``chunk`` annotations from user-facing glosses."""
    if not gloss:
        return gloss
    text = clean_html_entities(gloss)
    text = re.sub(r"\s+[—-]\s*[^—-]*\bchunk\b.*$", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\bchunk\b", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+,", ",", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip(" ,;:—-")


def _clean_html_entities_in_obj(value: object) -> object:
    """Recursively unescape text fields before writing the generated manifest."""
    if isinstance(value, str):
        return clean_html_entities(value)
    if isinstance(value, list):
        return [_clean_html_entities_in_obj(v) for v in value]
    if isinstance(value, dict):
        return {k: _clean_html_entities_in_obj(v) for k, v in value.items()}
    return value


class _SlovnykArticleParser(HTMLParser):
    """Extract only the dictionary article from a slovnyk.me direct-entry page."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title_parts: list[str] = []
        self.h1_parts: list[str] = []
        self.article_parts: list[str] = []
        self.canonical_url = ""
        self._in_title = False
        self._in_article_section = False
        self._in_article = False
        self._in_h1 = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = {key: value or "" for key, value in attrs}
        if tag == "title":
            self._in_title = True
        if tag == "link" and attr.get("rel") == "canonical":
            self.canonical_url = attr.get("href", "")
        if tag == "section" and attr.get("id") in {"dictionary-acticle", "dictionary-article"}:
            self._in_article_section = True
        if tag == "article" and self._in_article_section:
            self._in_article = True
        if tag == "h1" and self._in_article:
            self._in_h1 = True
        if tag in {"p", "li", "br", "div", "h1", "h2", "h3", "small"} and self._in_article:
            self.article_parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self._in_title = False
        if tag == "h1":
            self._in_h1 = False
        if tag == "article" and self._in_article:
            self._in_article = False
        if tag == "section" and self._in_article_section:
            self._in_article_section = False
        if tag in {"p", "li", "br", "div", "h1", "h2", "h3", "small"} and self._in_article:
            self.article_parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self.title_parts.append(data)
        if self._in_article:
            self.article_parts.append(data)
        if self._in_h1:
            self.h1_parts.append(data)


def _strip_stress(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", clean_html_entities(str(text or "")))
    normalized = _STRESS_MARK_RE.sub("", normalized)
    return unicodedata.normalize("NFC", normalized)


def _count_vowels(text: str) -> int:
    return sum(1 for char in text if char in _UKRAINIAN_VOWELS)


def _get_stressifier() -> Any:
    global _stressifier
    if _stressifier is None:
        from ukrainian_word_stress import Stressifier, StressSymbol

        _stressifier = Stressifier(stress_symbol=StressSymbol.CombiningAcuteAccent)
    return _stressifier


@lru_cache(maxsize=32768)
def _stress_word(word: str) -> str:
    clean = _strip_stress(word).strip()
    if (
        not clean
        or _has_whitespace(clean)
        or not _UKRAINIAN_WORD_RE.fullmatch(clean)
        or _count_vowels(clean) < 2
    ):
        return ""
    try:
        stressed = str(_get_stressifier()(clean))
    except Exception:
        return ""
    if not _STRESS_MARK_RE.search(stressed):
        return ""
    if _strip_stress(stressed).casefold() != clean.casefold():
        return ""
    return stressed


def _stress_display_form(form: str) -> str:
    text = str(form or "").strip()
    if not text:
        return ""
    variants = [part.strip() for part in text.split(" / ")]
    if len(variants) > 1:
        stressed_variants = [_stress_display_form(part) or part for part in variants]
        if stressed_variants == variants:
            return ""
        return " / ".join(stressed_variants)
    return _stress_word(text)


def _collect_string_values(value: object) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        out: list[str] = []
        for item in value.values():
            out.extend(_collect_string_values(item))
        return out
    if isinstance(value, list):
        out: list[str] = []
        for item in value:
            out.extend(_collect_string_values(item))
        return out
    return []


_LEMMA_EDGE_PUNCTUATION = ' .,…?!;:()[]{}«»"“”'


def _base_lemma(lemma: str) -> str:
    if "/" not in lemma:
        return lemma
    return lemma.split("/", 1)[0].strip(_LEMMA_EDGE_PUNCTUATION)


def _slovnyk_lookup_word(lemma: str) -> str:
    base = _lookup_key(lemma).strip(_LEMMA_EDGE_PUNCTUATION)
    # Pair/aspectual & inflection-paired lemmas ("варити / зварити",
    # "березень / березня") have NO combined slovnyk.me entry, so the joined
    # string misses every dictionary (and the miss gets cached). Look up the
    # first (imperfective / base) form, which carries the canonical article.
    # This also re-keys the cache file, bypassing the previously cached miss.
    if "/" in base:
        base = base.split("/", 1)[0].strip(_LEMMA_EDGE_PUNCTUATION)
    return base


def _slovnyk_cache_path(lemma: str) -> Path:
    stem = _NON_CACHE_CHARS_RE.sub("-", _slovnyk_lookup_word(lemma)).strip("-")
    return SLOVNYK_CACHE / f"{stem or 'empty'}.json"


def _entry_text_without_headword(text: str, lemma: str, headword: str | None = None) -> str:
    cleaned = clean_html_entities(text)
    seen_candidates: set[str] = set()
    for candidate in (headword, lemma, _slovnyk_lookup_word(lemma)):
        if not candidate:
            continue
        normalized_candidate = _strip_stress(candidate).casefold()
        if normalized_candidate in seen_candidates:
            continue
        seen_candidates.add(normalized_candidate)
        pattern = re.compile(rf"^\s*{re.escape(_strip_stress(candidate))}\b", flags=re.IGNORECASE)
        if pattern.search(_strip_stress(cleaned)):
            cleaned = pattern.sub("", _strip_stress(cleaned), count=1).strip()
    return cleaned


def _truncate_text(text: str, limit: int) -> str:
    cleaned = clean_html_entities(text)
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 1].rstrip() + "…"


def _parse_slovnyk_entry(
    page_html: str,
    *,
    lemma: str,
    lookup_word: str,
    slug: str,
    url: str,
) -> dict[str, Any] | None:
    parser = _SlovnykArticleParser()
    parser.feed(page_html)
    article_text = clean_html_entities(" ".join(parser.article_parts))
    if not article_text:
        return None
    headword = clean_html_entities(" ".join(parser.h1_parts)) or lookup_word
    title = clean_html_entities(" ".join(parser.title_parts)) or headword
    return {
        "dictionary_slug": slug,
        "dictionary_label": _SLOVNYK_DICT_LABELS.get(slug, slug),
        "word": headword,
        "source_url": parser.canonical_url or url,
        "title": title,
        "text": _truncate_text(article_text, 5000),
        "query": lemma,
        "lookup_word": lookup_word,
    }


class _SlovnykTransientError(Exception):
    """Retryable slovnyk.me lookup failure that must not be cached as a miss."""


def _polite_slovnyk_delay() -> None:
    global _last_slovnyk_fetch
    if _last_slovnyk_fetch:
        elapsed = time.monotonic() - _last_slovnyk_fetch
        if elapsed < _SLOVNYK_DELAY_SECONDS:
            time.sleep(_SLOVNYK_DELAY_SECONDS - elapsed)
    _last_slovnyk_fetch = time.monotonic()


def _fetch_slovnyk_entry(lemma: str, lookup_word: str, slug: str) -> dict[str, Any] | None:
    _polite_slovnyk_delay()
    url = f"{_SLOVNYK_BASE}/dict/{slug}/{quote(lookup_word)}"
    try:
        response = requests.get(
            url,
            timeout=20,
            headers={"User-Agent": _SLOVNYK_USER_AGENT},
        )
        if response.status_code == 404:
            return None
        if response.status_code >= 500:
            msg = f"transient slovnyk.me status {response.status_code} for {url}"
            raise _SlovnykTransientError(msg)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise _SlovnykTransientError(f"transient slovnyk.me request failure for {url}") from exc
    return _parse_slovnyk_entry(
        response.text,
        lemma=lemma,
        lookup_word=lookup_word,
        slug=slug,
        url=url,
    )


def _load_slovnyk_cache_file(path: Path) -> dict[str, Any] | None:
    try:
        cache = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return cache if isinstance(cache, dict) else None


def _new_slovnyk_cache(lemma: str, lookup_word: str) -> dict[str, Any]:
    return {
        "schema_version": _SLOVNYK_CACHE_SCHEMA_VERSION,
        "lemma": lemma,
        "lookup_word": lookup_word,
        "fetched_at": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat(),
        "lookups": {},
    }


def _slovnyk_cache(lemma: str) -> dict[str, Any]:
    """Read or populate the one-file-per-lemma slovnyk.me cache."""
    lookup_word = _slovnyk_lookup_word(lemma)
    path = _slovnyk_cache_path(lemma)
    cache = _load_slovnyk_cache_file(path)
    changed = False
    if cache and cache.get("lookup_word") == lookup_word:
        if cache.get("schema_version") == 1:
            raw_lookups = cache.get("lookups")
            if isinstance(raw_lookups, dict):
                cache["lookups"] = {
                    slug: row for slug, row in raw_lookups.items() if row is not None
                }
            else:
                cache["lookups"] = {}
            cache["schema_version"] = _SLOVNYK_CACHE_SCHEMA_VERSION
            changed = True
        elif cache.get("schema_version") != _SLOVNYK_CACHE_SCHEMA_VERSION:
            cache = _new_slovnyk_cache(lemma, lookup_word)
            changed = True
        lookups = cache.setdefault("lookups", {})
        if not isinstance(lookups, dict):
            lookups = {}
            cache["lookups"] = lookups
            changed = True
    else:
        cache = _new_slovnyk_cache(lemma, lookup_word)
        lookups = cache["lookups"]

    for slug in _SLOVNYK_LOOKUP_SLUGS:
        if slug in lookups:
            continue
        try:
            lookups[slug] = _fetch_slovnyk_entry(lemma, lookup_word, slug) if lookup_word else None
        except _SlovnykTransientError:
            continue
        changed = True

    if changed:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(cache, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return cache


def _cache_lookup(cache: dict[str, Any] | None, slug: str) -> dict[str, Any] | None:
    if not isinstance(cache, dict):
        return None
    lookups = cache.get("lookups")
    if not isinstance(lookups, dict):
        return None
    row = lookups.get(slug)
    return row if isinstance(row, dict) and row.get("text") else None


def _cache_store_lookup(lemma: str, cache: dict[str, Any], slug: str, row: dict[str, Any] | None) -> None:
    lookups = cache.setdefault("lookups", {})
    if not isinstance(lookups, dict):
        return
    lookups[slug] = row
    path = _slovnyk_cache_path(lemma)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(cache, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


@lru_cache(maxsize=4096)
def _vesum_word_analyses(word: str) -> tuple[tuple[str, str], ...]:
    """Return immutable ``(lemma, pos)`` VESUM analyses for one word form."""
    try:
        rows = verify_word(word)
    except Exception:
        return ()
    analyses = {
        (str(row.get("lemma") or ""), str(row.get("pos") or ""))
        for row in rows
        if row.get("lemma") and row.get("pos")
    }
    return tuple(sorted(analyses))


def _vesum_word_poses(word: str) -> set[str]:
    return {pos for _lemma, pos in _vesum_word_analyses(word)}


def _safe_synonym_set(lemma: str) -> set[str]:
    return {_lookup_key(item) for item in _A1_SENSE_SYNONYMS.get(_lookup_key(lemma), ())}


def _headword_pos_for_synonyms(lemma: str, entry_pos: str | None = None) -> str | None:
    normalized = _lookup_key(lemma)
    if normalized in _SYNONYM_HEADWORD_POS_OVERRIDES:
        return _SYNONYM_HEADWORD_POS_OVERRIDES[normalized]

    mapped_pos = _MANIFEST_POS_TO_VESUM_POS.get(_lookup_key(entry_pos or ""))
    if mapped_pos:
        return mapped_pos

    lookup_word = _slovnyk_lookup_word(lemma)
    if not lookup_word or " " in lookup_word:
        return None
    poses = _vesum_word_poses(lookup_word)
    if len(poses) == 1:
        return next(iter(poses))
    return None


def _candidate_is_headword_variant(lemma: str, candidate: str, headword_pos: str) -> bool:
    headword = _slovnyk_lookup_word(lemma)
    headword_lemmas = {
        analysis_lemma
        for analysis_lemma, pos in _vesum_word_analyses(headword)
        if pos == headword_pos
    }
    if not headword_lemmas:
        headword_lemmas = {_lookup_key(variant) for variant in _split_lemma_variants(_strip_stress(lemma))}
    return any(
        pos == headword_pos and analysis_lemma in headword_lemmas
        for analysis_lemma, pos in _vesum_word_analyses(candidate)
    )


def _candidate_matches_headword_pos(candidate: str, headword_pos: str) -> bool:
    return any(pos == headword_pos for _lemma, pos in _vesum_word_analyses(candidate))


def _synonym_body(text: str, lemma: str, headword: str | None, slug: str | None = None) -> str:
    body = _SOURCE_TAIL_RE.sub("", _entry_text_without_headword(text, lemma, headword))
    body = primary_synonym_sense_text(body, slug or "")
    body = re.split(r"\s+[—–]\s+[А-ЯІЇЄҐA-Z]", body, maxsplit=1)[0]
    body = re.sub(
        r"\((?:про|який|яка|яке|які|на|зі сл\.|сл\.|від|для|у|в)\b[^)]*\)",
        " ",
        body,
        flags=re.IGNORECASE,
    )
    body = re.sub(r"\([^)]*\)", " ", body)
    return body


def _clean_synonym_candidate(candidate: str, lemma: str) -> str | None:
    term = _strip_stress(candidate)
    term = term.replace("�", " ")
    term = re.sub(r"<[^>]+>", " ", term)
    term = term.replace("(", ",").replace(")", ",")
    term = _SYNONYM_LABEL_RE.sub(" ", term)
    term = re.sub(r"\s+", " ", term).strip()
    term = term.strip(' \t\r\n.,;:!?/\\[]{}«»"“”<>')
    term = term.casefold()
    if not term or term in _BLOCKED_SYNONYMS:
        return None
    if _LATIN_RE.search(term) or not _UKRAINIAN_TEXT_RE.fullmatch(term):
        return None
    words = term.split()
    if len(words) > 3 or words[0] in _SYNONYM_STOP_STARTS:
        return None
    for label in _SYNONYM_LABEL_WORDS:
        if term == label or term.startswith(f"{label} "):
            return None
    for variant in _split_lemma_variants(_strip_stress(lemma)):
        normalized_variant = variant.casefold()
        if term == normalized_variant or _contains_whole_token(term, normalized_variant):
            return None
    return term


def _slovnyk_synonym_group_head(row: dict[str, Any], lemma: str) -> str:
    body = _synonym_body(
        str(row.get("text") or ""),
        lemma,
        str(row.get("word") or ""),
        str(row.get("dictionary_slug") or ""),
    )
    first = re.split(r"[,;(]", body, maxsplit=1)[0]
    first = _SYNONYM_LABEL_RE.sub(" ", _strip_stress(first))
    first = re.sub(r"\s+", " ", first).strip(' \t\r\n.,;:!?/\\[]{}«»"“”<>').casefold()
    return first


def _is_safe_slovnyk_synonym(
    lemma: str,
    candidate: str,
    headword_pos: str,
    *,
    require_allowlist: bool = False,
) -> bool:
    if require_allowlist and candidate not in _safe_synonym_set(lemma):
        return False
    if not _candidate_matches_headword_pos(candidate, headword_pos):
        return False
    return not _candidate_is_headword_variant(lemma, candidate, headword_pos)


def _synonyms_from_slovnyk_row(
    row: dict[str, Any],
    lemma: str,
    headword_pos: str,
    *,
    require_allowlist: bool = False,
) -> list[str]:
    body = _synonym_body(
        str(row.get("text") or ""),
        lemma,
        str(row.get("word") or ""),
        str(row.get("dictionary_slug") or ""),
    )
    chunks = re.split(r"[,;/]", body)
    out: list[str] = []
    seen: set[str] = set()
    for chunk in chunks:
        for part in re.split(r"[()]", chunk):
            term = _clean_synonym_candidate(part, lemma)
            if (
                term
                and term not in seen
                and _is_safe_slovnyk_synonym(
                    lemma,
                    term,
                    headword_pos,
                    require_allowlist=require_allowlist,
                )
            ):
                seen.add(term)
                out.append(term)
    return out


def _synonyms_slovnyk(
    lemma: str,
    cache: dict[str, Any] | None = None,
    *,
    entry_pos: str | None = None,
) -> dict[str, Any] | None:
    """Synonym chips from slovnyk.me synonyms dictionaries, omitted when empty."""
    lookup_lemma = _slovnyk_lookup_word(_base_lemma(lemma))
    if not lookup_lemma or _has_whitespace(lookup_lemma):
        return None
    headword_pos = _headword_pos_for_synonyms(lookup_lemma, entry_pos)
    if not headword_pos:
        return None
    cache = cache if cache is not None else _slovnyk_cache(lookup_lemma)
    items: list[str] = []
    seen: set[str] = set()
    sources: list[str] = []
    urls: list[str] = []
    for slug in _SLOVNYK_SYNONYM_SLUGS:
        row = _cache_lookup(cache, slug)
        if not row:
            continue
        row_items = _synonyms_from_slovnyk_row(row, lookup_lemma, headword_pos)
        if slug == "synonyms" and row_items:
            group_head = _slovnyk_synonym_group_head(row, lookup_lemma)
            allowlisted = _safe_synonym_set(lookup_lemma)
            if (
                group_head != lookup_lemma.casefold()
                and not seen.intersection(row_items)
                and not allowlisted.intersection(row_items)
            ):
                continue
        if not row_items:
            continue
        for synonym in row_items:
            if synonym not in seen:
                seen.add(synonym)
                items.append(synonym)
        sources.append(str(row.get("dictionary_label") or _SLOVNYK_DICT_LABELS[slug]))
        if row.get("source_url"):
            urls.append(str(row["source_url"]))
    if not items:
        return None
    return {
        "items": items[:24],
        "source": "slovnyk.me: " + " + ".join(dict.fromkeys(sources)),
        "source_urls": list(dict.fromkeys(urls)),
    }


def _protect_idiom_abbreviation_periods(text: str) -> str:
    protected = text
    for abbreviation in _IDIOM_ABBREVIATIONS_WITH_INTERNAL_DOTS:
        pattern = re.escape(abbreviation).replace(r"\ ", r"\s+")
        protected = re.sub(
            pattern,
            lambda match: match.group(0).replace(".", _IDIOM_DOT_PLACEHOLDER),
            protected,
            flags=re.IGNORECASE,
        )
    return protected


def _restore_idiom_abbreviation_periods(text: str) -> str:
    return text.replace(_IDIOM_DOT_PLACEHOLDER, ".")


def _split_idiom_text(text: str, lemma: str, headword: str | None) -> tuple[str, str] | None:
    body = _SOURCE_TAIL_RE.sub("", _entry_text_without_headword(text, lemma, headword))
    body = clean_html_entities(body).strip(" .")
    if not body:
        return None
    protected_body = _protect_idiom_abbreviation_periods(body)
    match = re.match(r"(.{3,220}?\.)\s+(.+)", protected_body, flags=re.DOTALL)
    if match:
        phrase = _restore_idiom_abbreviation_periods(match.group(1)).strip(" .")
        definition = _restore_idiom_abbreviation_periods(match.group(2)).strip()
    else:
        words = body.split()
        phrase = " ".join(words[: min(len(words), 8)]).strip(" .")
        definition = " ".join(words[min(len(words), 8) :]).strip() or body
    if not phrase:
        return None
    return phrase, _truncate_text(definition, 650)


def _idioms_slovnyk(lemma: str, cache: dict[str, Any] | None = None) -> dict[str, Any] | None:
    """Phraseology card from the slovnyk.me Фразеологічний page."""
    cache = cache if cache is not None else _slovnyk_cache(lemma)
    row = _cache_lookup(cache, "phraseology")
    if not row:
        return None
    split = _split_idiom_text(str(row.get("text") or ""), lemma, str(row.get("word") or ""))
    if not split:
        return None
    phrase, definition = split
    return {
        "items": [
            {
                "text": phrase,
                "phrase": phrase,
                "definition": definition,
                "source": str(row.get("dictionary_label") or _SLOVNYK_DICT_LABELS["phraseology"]),
                "source_url": str(row.get("source_url") or ""),
            }
        ],
        "source": "slovnyk.me: Фразеологічний словник української мови",
        "source_urls": [str(row["source_url"])] if row.get("source_url") else [],
    }


def _warning_alternatives_from_row(row: dict[str, Any], lemma: str) -> list[str]:
    text = _SOURCE_TAIL_RE.sub(
        "", _entry_text_without_headword(str(row.get("text") or ""), lemma, str(row.get("word") or ""))
    )
    if not text:
        return []
    slug = str(row.get("dictionary_slug") or "")
    if slug in {"davydov", "voloschak"}:
        if slug == "davydov" and not re.search(
            r"неправильно|російськ|кальк|відповідником|не було|не слід|не треба|краще",
            text,
            flags=re.IGNORECASE,
        ):
            return []
        match = re.search(r"[—-]\s*([^.;:]+)", text)
        if match:
            text = match.group(1)
        else:
            match = re.search(r"\b(?:є|буде|кажемо|вживайте)\s+([^.;:]+)", text, flags=re.IGNORECASE)
            if match:
                text = match.group(1)
    else:
        text = re.split(r"[.;]", text, maxsplit=1)[0]
    text = re.split(
        r"\s+(?:Коли|Особовий|Російськ\w*|Українськ\w*|Слово|Такого|Відповідником)\b",
        text,
        maxsplit=1,
    )[0]

    out: list[str] = []
    seen: set[str] = set()
    for chunk in re.split(r"[,;/]|\s+або\s+|\s+чи\s+", text, flags=re.IGNORECASE):
        term = _strip_stress(chunk).strip(' \t\r\n.,;:!?()[]{}«»"“”').casefold()
        term = re.sub(r"\s+", " ", term)
        if not term or term in _WARNING_ALT_STOP_WORDS:
            continue
        if term.startswith("див ") or _LATIN_RE.search(term) or not _UKRAINIAN_TEXT_RE.fullmatch(term):
            continue
        if len(term.split()) > 3:
            continue
        if term == _slovnyk_lookup_word(lemma).casefold():
            continue
        if term not in seen:
            seen.add(term)
            out.append(term)
    return out[:6]


def _warning_slovnyk(lemma: str, cache: dict[str, Any] | None = None) -> dict[str, Any] | None:
    """Wrong/foreign → Ukrainian correction from slovnyk.me warning dictionaries."""
    cache = cache if cache is not None else _slovnyk_cache(lemma)
    alternatives: list[str] = []
    seen: set[str] = set()
    evidence: list[dict[str, str]] = []
    for slug in _SLOVNYK_WARNING_SLUGS:
        row = _cache_lookup(cache, slug)
        if not row:
            continue
        row_alternatives = _warning_alternatives_from_row(row, lemma)
        if not row_alternatives:
            continue
        for alternative in row_alternatives:
            if alternative not in seen:
                seen.add(alternative)
                alternatives.append(alternative)
        evidence.append(
            {
                "source": str(row.get("dictionary_label") or _SLOVNYK_DICT_LABELS[slug]),
                "url": str(row.get("source_url") or ""),
                "detail": _truncate_text(str(row.get("text") or ""), 280),
            }
        )
    if not alternatives:
        return None
    return {
        "alternatives": alternatives,
        "source": "slovnyk.me correction dictionaries",
        "evidence": evidence,
    }


def _clear_unsourced_warning(status: dict[str, Any]) -> dict[str, Any]:
    if not (status.get("is_russianism") or str(status.get("classification") or "") in _WARNING_CLASSIFICATIONS):
        return status
    clean_status = dict(status)
    clean_status["classification"] = "unknown"
    clean_status["is_russianism"] = False
    clean_status["calque_warning"] = None
    clean_status["attestations"] = [
        attestation
        for attestation in clean_status.get("attestations", [])
        if not (
            isinstance(attestation, dict)
            and attestation.get("source") in {"standard_alternative", "lt_replacements", "heritage_spec"}
        )
    ]
    return clean_status


def _merge_slovnyk_warning(status: dict[str, Any], warning: dict[str, Any] | None) -> dict[str, Any]:
    if not warning:
        return _clear_unsourced_warning(status)
    status = dict(status)
    attestations = list(status.get("attestations") or [])
    existing_alternatives = {
        str(attestation.get("ref"))
        for attestation in attestations
        if isinstance(attestation, dict) and attestation.get("source") == "standard_alternative"
    }
    for alternative in warning.get("alternatives", []):
        if alternative in existing_alternatives:
            continue
        attestations.append(
            {
                "source": "standard_alternative",
                "ref": alternative,
                "detail": "slovnyk.me correction dictionary alternative",
            }
        )
    for row in warning.get("evidence", []):
        if not isinstance(row, dict):
            continue
        attestations.append(
            {
                "source": "slovnyk_me_correction",
                "ref": row.get("url") or row.get("source") or "slovnyk.me",
                "detail": row.get("detail") or row.get("source") or "",
            }
        )
    alternatives = list(dict.fromkeys(str(item) for item in warning.get("alternatives", []) if item))
    classification = status.get("classification")
    if classification not in _WARNING_CLASSIFICATIONS:
        classification = "russianism"
    status.update(
        {
            "classification": classification,
            "attestations": attestations,
            "is_russianism": True,
            "calque_warning": {"standard_alternatives": alternatives},
        }
    )
    return status


def _entry_scoped_heritage_status(status: dict[str, Any]) -> dict[str, Any]:
    clean_status = dict(status)
    clean_status.pop("sovietization_risk", None)
    return clean_status


def _is_slovnyk_warning_candidate(entry: dict[str, Any], status: dict[str, Any]) -> bool:
    return bool(
        entry.get("primary_source") == "surzhyk_to_avoid"
        or status.get("is_russianism")
        or str(status.get("classification") or "") in _WARNING_CLASSIFICATIONS
    )


def _morphology(lemma: str) -> dict | None:
    """Full VESUM paradigm for a single-token lemma, decoded and de-duplicated."""
    if " " in lemma.strip():
        return None  # phrases have no single-lemma paradigm
    try:
        forms = verify_lemma(lemma)
    except Exception:
        return None
    if not forms:
        return None
    pos_raw = forms[0].get("pos") or ""
    seen: set[tuple[str, str]] = set()
    decoded: list[dict[str, str]] = []
    for row in forms:
        form = row.get("word_form") or ""
        label = _decode_tag(row.get("tags") or "")
        key = (form, label)
        if not form or key in seen:
            continue
        seen.add(key)
        decoded_row = {"form": form, "label": label}
        stressed_form = _stress_display_form(form)
        if stressed_form:
            decoded_row["stress"] = stressed_form
        decoded.append(decoded_row)
    if not decoded:
        return None
    morphology = {
        "pos": _POS_LABELS.get(pos_raw, pos_raw),
        "form_count": len(decoded),
        "forms": decoded[:40],
        "source": "VESUM",
    }
    paradigm = _build_paradigm(pos_raw, decoded)
    if paradigm:
        morphology["paradigm"] = paradigm
    stressed_forms = {
        row["form"]: row["stress"]
        for row in decoded
        if row.get("stress") and row.get("form") != row.get("stress")
    }
    if paradigm:
        for form in _collect_string_values(paradigm):
            stressed_form = _stress_display_form(form)
            if stressed_form and stressed_form != form:
                stressed_forms[form] = stressed_form
    if stressed_forms:
        morphology["stress"] = {"source": _STRESS_SOURCE, "forms": stressed_forms}
    return morphology


def _clean_wiki_def(raw: str) -> str:
    """Strip Вікісловник wiki-markup noise (templates, quote leaks, refs)."""
    text = _unescape_html_entities(raw)
    text = re.sub(r"<br\s*/?>", " ", text, flags=re.IGNORECASE)
    # [\s\S] (not .) so multi-line comments are stripped too — `.` stops at the
    # first newline, leaking the rest of a multi-line comment (CodeQL
    # py/bad-tag-filter). Input is trusted Вікісловник DB text, but match fully.
    text = re.sub(r"<!--[\s\S]*?-->", "", text)
    text = re.sub(r"\{\{[^{}]*\}\}", "", text)
    text = re.split(r"\.\s{2,}", text)[0]  # cut a leaked quotation after the def
    text = re.split(r"[|{}\[]", text)[0]  # cut residual template/ref markers
    text = re.sub(r"\s+", " ", text).strip()
    return text.strip(" .,;:—-")


def _clean_wiki_defs(raw: str | None) -> list[str]:
    try:
        arr = json.loads(raw or "[]")
    except (ValueError, TypeError):
        return []
    out: list[str] = []
    for d in arr:
        cleaned = _clean_wiki_def(str(d))
        if len(cleaned) >= 6 and cleaned not in out:
            out.append(cleaned)
    return out[:3]


def _split_lemma_variants(lemma: str) -> list[str]:
    variants: list[str] = []
    for part in re.split(r"[/,]", lemma):
        word = part.strip()
        if not word:
            continue
        variants.extend(get_apostrophe_variants(word))
    seen: set[str] = set()
    return [v for v in variants if not (v.casefold() in seen or seen.add(v.casefold()))]


def _whole_token_pattern(term: str) -> re.Pattern[str]:
    return re.compile(
        rf"(?<![{_CYRILLIC_WORD_CHARS}]){re.escape(term)}(?![{_CYRILLIC_WORD_CHARS}])",
        re.IGNORECASE,
    )


def _contains_whole_token(text: str, term: str) -> bool:
    return bool(_whole_token_pattern(term).search(text))


def _normalise_synonym(raw: str) -> str:
    text = clean_html_entities(str(raw))
    text = text.replace("`", "")
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    text = text.strip(" \t\r\n.,;:!?()[]{}«»\"“”")
    return text.casefold()


def _candidate_allowed(lemma: str, candidate: str) -> bool:
    term = _normalise_synonym(candidate)
    if not term or term in _BLOCKED_SYNONYMS:
        return False
    if _LATIN_RE.search(term) or not _UKRAINIAN_TEXT_RE.fullmatch(term):
        return False
    if len(term.split()) > 2:
        return False
    for variant in _split_lemma_variants(lemma):
        if term == variant.casefold() or _contains_whole_token(term, variant.casefold()):
            return False
    return _lookup_key(term) in _safe_synonym_set(lemma)


def _add_candidate(
    out: list[str],
    seen: set[str],
    lemma: str,
    candidate: str,
) -> None:
    term = _normalise_synonym(candidate)
    if _candidate_allowed(lemma, term) and term not in seen:
        seen.add(term)
        out.append(term)


def _synonyms_from_wiktionary(conn: sqlite3.Connection, lemma: str, out: list[str], seen: set[str]) -> None:
    for variant in _split_lemma_variants(lemma):
        row = conn.execute(
            "SELECT synonyms FROM wiktionary WHERE word = ? LIMIT 1",
            (variant,),
        ).fetchone()
        if not row:
            continue
        try:
            synonyms = json.loads(row[0] or "[]")
        except (TypeError, ValueError):
            continue
        for candidate in synonyms:
            _add_candidate(out, seen, lemma, str(candidate))


def _synonyms_from_ukrajinet(conn: sqlite3.Connection, lemma: str, out: list[str], seen: set[str]) -> None:
    for variant in _split_lemma_variants(lemma):
        rows = conn.execute(
            "SELECT words FROM ukrajinet WHERE lower(words) LIKE ?",
            (f"%{variant.casefold()}%",),
        ).fetchall()
        for (words_json,) in rows:
            try:
                words = [str(w).strip() for w in json.loads(words_json or "[]")]
            except (TypeError, ValueError):
                continue
            if not any(_contains_whole_token(_normalise_synonym(word), variant.casefold()) for word in words):
                continue
            for candidate in words:
                _add_candidate(out, seen, lemma, candidate)


def _synonyms_from_balla(conn: sqlite3.Connection, lemma: str, out: list[str], seen: set[str]) -> None:
    allowed = _A1_SENSE_SYNONYMS.get(_lookup_key(lemma), ())
    lookup_words = _BALLA_LOOKUPS.get(_lookup_key(lemma), ())
    if not allowed or not lookup_words:
        return
    for lookup_word in lookup_words:
        rows = conn.execute(
            "SELECT definition, text FROM balla_en_uk WHERE word = ?",
            (lookup_word,),
        ).fetchall()
        for definition, text in rows:
            haystack = clean_html_entities(f"{definition or ''} {text or ''}").casefold()
            for candidate in allowed:
                if _contains_whole_token(haystack, candidate.casefold()):
                    _add_candidate(out, seen, lemma, candidate)


def _synonyms_from_sum11(conn: sqlite3.Connection, lemma: str, out: list[str], seen: set[str]) -> None:
    allowed = _A1_SENSE_SYNONYMS.get(_lookup_key(lemma), ())
    if not allowed:
        return
    for variant in _split_lemma_variants(lemma):
        row = conn.execute(
            "SELECT definition FROM sum11 WHERE word = ? AND definition != '' LIMIT 1",
            (variant,),
        ).fetchone()
        if not row:
            continue
        haystack = clean_html_entities(row[0]).casefold()
        for candidate in allowed:
            if _contains_whole_token(haystack, candidate.casefold()):
                _add_candidate(out, seen, lemma, candidate)


def _sense_correct_synonyms(conn: sqlite3.Connection, lemma: str) -> list[str]:
    """Return source-attested synonyms for the lemma's A1 sense, capped at six."""
    out: list[str] = []
    seen: set[str] = set()
    _synonyms_from_balla(conn, lemma, out, seen)
    _synonyms_from_sum11(conn, lemma, out, seen)
    return out[:6]


def _sum11_has_flag_columns(conn: sqlite3.Connection) -> bool:
    cols = {row[1] for row in conn.execute("PRAGMA table_info(sum11);").fetchall()}
    return {"sovietization_risk", "sovietization_keywords"}.issubset(cols)


def _split_sum11_keywords(raw: object) -> list[str]:
    return [part.strip() for part in str(raw or "").split(",") if part.strip()]


def _sum11_row_flags(row: tuple, *, has_flag_columns: bool) -> tuple[int, list[str]]:
    if has_flag_columns:
        try:
            return int(row[2] or 0), _split_sum11_keywords(row[3])
        except (IndexError, TypeError, ValueError):
            return 0, []

    from scripts.audit.sum11_sovietization_scan import classify_entry

    return classify_entry(str(row[0] or ""), str(row[1] or ""))


def _meaning(
    conn: sqlite3.Connection,
    lemma: str,
    *,
    has_sum11_flags: bool | None = None,
) -> dict | None:
    """Modern Ukrainian meaning: Вікісловник (clean, + synonyms) → СУМ-11 fallback.

    Грінченко is intentionally NOT used here — its 1907 glosses are Russian
    and must not surface in rendered Atlas pages.
    """
    word = lemma.strip()
    row = None
    for variant in _split_lemma_variants(word):
        row = conn.execute(
            "SELECT definitions FROM wiktionary WHERE word = ? LIMIT 1",
            (variant,),
        ).fetchone()
        if row:
            break
    if row:
        defs = _clean_wiki_defs(row[0])
        if defs:
            block: dict[str, object] = {"definitions": defs, "source": "Вікісловник"}
            syns = _sense_correct_synonyms(conn, word)
            if syns:
                block["synonyms"] = syns
            return block
    row = None
    if has_sum11_flags is None:
        has_sum11_flags = _sum11_has_flag_columns(conn)
    sum11_fields = "definition, text"
    if has_sum11_flags:
        sum11_fields += ", sovietization_risk, sovietization_keywords"
    for variant in _split_lemma_variants(word):
        row = conn.execute(
            f"SELECT {sum11_fields} FROM sum11 WHERE word = ? AND definition != '' LIMIT 1",
            (variant,),
        ).fetchone()
        if row:
            break
    if row and row[0]:
        risk, keywords = _sum11_row_flags(row, has_flag_columns=has_sum11_flags)
        block = {
            "definitions": [row[0].strip()[:600]],
            "source": "СУМ-11",
            "sovietization_risk": risk,
            "note": "СУМ-11 — радянське видання; перевіряйте ідеологічно навантажені статті.",
        }
        if keywords:
            block["sovietization_keywords"] = keywords
        syns = _sense_correct_synonyms(conn, word)
        if syns:
            block["synonyms"] = syns
        return block
    return None


def _definition_body(
    text: object,
    *,
    headword: str | None = None,
    strip_leading_headword: bool = False,
    limit: int = 900,
) -> str:
    body = _SOURCE_TAIL_RE.sub("", clean_html_entities(str(text or "")))
    if strip_leading_headword and headword:
        pattern = re.compile(rf"^\s*{re.escape(headword)}\b\s*", flags=re.IGNORECASE)
        body = pattern.sub("", body, count=1)
    body = re.sub(r"\s+", " ", clean_html_entities(body)).strip()
    return _truncate_text(body, limit) if body else ""

def _sum20_in_coverage(lemma: str) -> bool:
    lookup = _slovnyk_lookup_word(lemma)
    if not lookup or _has_whitespace(lookup):
        return False
    return lookup[0].casefold() in _SUM20_COVERED_INITIALS


def _sum20_definition_card(
    lemma: str,
    cache: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    if not _sum20_in_coverage(lemma):
        return None
    lookup_word = _slovnyk_lookup_word(lemma)
    row = _cache_lookup(cache, "newsum") if cache is not None else None
    if not row:
        transient = False
        try:
            row = _fetch_slovnyk_entry(lemma, lookup_word, "newsum") if lookup_word else None
        except _SlovnykTransientError:
            transient = True
            row = None
        if cache is not None and not transient:
            _cache_store_lookup(lemma, cache, "newsum", row)
    if not row:
        return None
    text = _definition_body(
        row.get("text"),
        headword=str(row.get("word") or lookup_word),
        strip_leading_headword=True,
    )
    if not text:
        return None
    return {
        "id": "sum20",
        "source": "СУМ-20",
        "source_pill": "СУМ-20",
        "note": "сучасний тлумачний словник",
        "definitions": [text],
        "source_url": str(row.get("source_url") or ""),
    }


def _sum11_definition_card(
    conn: sqlite3.Connection,
    lemma: str,
    *,
    has_sum11_flags: bool,
) -> dict[str, Any] | None:
    sum11_fields = "definition, text"
    if has_sum11_flags:
        sum11_fields += ", sovietization_risk, sovietization_keywords"
    for variant in _split_lemma_variants(lemma):
        row = conn.execute(
            f"SELECT {sum11_fields} FROM sum11 WHERE word = ? AND definition != '' LIMIT 1",
            (variant,),
        ).fetchone()
        if not row or not row[0]:
            continue
        risk, keywords = _sum11_row_flags(row, has_flag_columns=has_sum11_flags)
        text = _definition_body(row[0])
        if not text:
            return None
        card: dict[str, Any] = {
            "id": "sum11-flagged" if risk > 0 else "sum11",
            "source": "СУМ-11",
            "source_pill": "СУМ-11",
            "note": f"радянське видання · risk={risk}" if risk > 0 else "радянське видання · перевірено: чисто",
            "definitions": [text],
            "sovietization_risk": risk,
        }
        if keywords:
            card["sovietization_keywords"] = keywords
            card["flag_note"] = "⚠ СУМ-11 — радянське видання; подаємо обережно, перевага СУМ-20/Вікісловнику"
        elif risk > 0:
            card["flag_note"] = "⚠ СУМ-11 — радянське видання; подаємо обережно, перевага СУМ-20/Вікісловнику"
        return card
    return None


def _definition_cards(
    conn: sqlite3.Connection,
    lemma: str,
    *,
    has_sum11_flags: bool,
    cache: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    cards = [
        _sum20_definition_card(lemma, cache),
        _sum11_definition_card(conn, lemma, has_sum11_flags=has_sum11_flags),
    ]
    return [card for card in cards if card]


def _lookup_key(value: str) -> str:
    """Match Goroh headwords without stress marks or apostrophe variants."""
    normalized = unicodedata.normalize("NFKD", clean_html_entities(str(value or "")))
    normalized = _STRESS_MARK_RE.sub("", normalized)
    normalized = unicodedata.normalize("NFC", normalized)
    normalized = normalized.replace("`", "'").replace("’", "'").replace("ʼ", "'")
    return re.sub(r"\s+", " ", normalized).strip().casefold()


def _etymology_lookup_variants(lemma: str) -> list[str]:
    variants = [lemma.strip()]
    variants.extend(_split_lemma_variants(lemma))
    seen: set[str] = set()
    return [v for v in variants if v and not (v.casefold() in seen or seen.add(v.casefold()))]


def _append_unique_candidate(out: list[str], seen: set[str], candidate: str, original: str) -> None:
    key = _lookup_key(candidate)
    if not key or key == original or key in seen or _has_whitespace(key):
        return
    seen.add(key)
    out.append(key)


def _direct_etymology_base_candidates(word: str) -> list[str]:
    candidates: list[str] = []
    key = _lookup_key(word)
    if not key:
        return candidates
    candidates.extend(_DERIVATIONAL_ETYMLOGY_BASES.get(key, ()))
    candidates.extend(_ORDINAL_ETYMLOGY_BASES.get(key, ()))

    if key.endswith(("ся", "сь")) and len(key) > 4:
        candidates.append(key[:-2])
    if key.endswith("е") and len(key) > 3:
        candidates.append(f"{key[:-1]}ий")
    if key.endswith("о") and len(key) > 3:
        stem = key[:-1]
        candidates.append(f"{stem}ий")
        if stem.endswith("н"):
            candidates.append(f"{stem}ій")
    for prefix in ("пере", "від", "над", "під", "при", "роз", "без", "по", "за", "до", "ви", "з", "в", "у"):
        if key.startswith(prefix) and len(key) > len(prefix) + 3:
            candidates.append(key[len(prefix) :])
            break
    if key.endswith("ати") and len(key) > 5:
        candidates.append(key[:-3])
    if key.endswith("ити") and len(key) > 5:
        candidates.append(key[:-3])
    return candidates


def _derivational_etymology_candidates(lemma: str) -> list[str]:
    word = _lookup_key(_base_lemma(lemma))
    if not word or _has_whitespace(word) or word in _COMPOSITIONAL_ETYMOLOGY_EXCLUSIONS:
        return []
    out: list[str] = []
    seen: set[str] = {word}
    queue: list[tuple[str, int]] = [(word, 0)]
    while queue:
        current, depth = queue.pop(0)
        if depth >= 2:
            continue
        for candidate in _direct_etymology_base_candidates(current):
            before = len(out)
            _append_unique_candidate(out, seen, candidate, word)
            if len(out) > before:
                queue.append((_lookup_key(candidate), depth + 1))
    return out


def _has_whitespace(value: str) -> bool:
    return bool(re.search(r"\s", str(value or "").strip()))


def _missing_table(exc: sqlite3.OperationalError) -> bool:
    return "no such table" in str(exc).casefold()


def _goroh_etymology(conn: sqlite3.Connection, lemma: str) -> dict | None:
    """Goroh cached etymology, by requested Atlas lemma then canonical headword."""
    variants = _etymology_lookup_variants(lemma)
    row = None
    try:
        for variant in variants:
            row = conn.execute(
                "SELECT etymology_text, source_url FROM goroh_etymology "
                "WHERE requested_lemma = ? AND etymology_text != '' LIMIT 1",
                (variant,),
            ).fetchone()
            if row:
                break
        if not row:
            for variant in variants:
                row = conn.execute(
                    "SELECT etymology_text, source_url FROM goroh_etymology "
                    "WHERE headword = ? AND etymology_text != '' LIMIT 1",
                    (_lookup_key(variant),),
                ).fetchone()
                if row:
                    break
    except sqlite3.OperationalError as exc:
        if _missing_table(exc):
            return None
        raise
    if not row or not row[0]:
        return None
    return {
        "text": clean_html_entities(row[0].strip()[:600]),
        "source": "Горох (за ЕСУМ)",
        "source_url": row[1],
    }


def _esum_etymology(conn: sqlite3.Connection, lemma: str) -> dict | None:
    """ЕСУМ etymology (А–Г PoC coverage), by lemma."""
    word = lemma.strip()
    if _has_whitespace(word):
        return None
    row = None
    try:
        for variant in _split_lemma_variants(word):
            row = conn.execute(
                "SELECT etymology_text, vol, page FROM esum_etymology "
                "WHERE lemma = ? AND etymology_text != '' LIMIT 1",
                (variant,),
            ).fetchone()
            if row:
                break
    except sqlite3.OperationalError as exc:
        if _missing_table(exc):
            return None
        raise
    if not row or not row[0]:
        return None
    cite = "ЕСУМ"
    if row[1]:
        cite += f", т. {row[1]}"
    if row[2]:
        cite += f", с. {row[2]}"
    return {"text": clean_html_entities(row[0].strip()[:600]), "source": cite}


def _wiktionary_etymology(conn: sqlite3.Connection, lemma: str) -> dict | None:
    """uk.wiktionary dump fallback, by requested Atlas lemma and variants."""
    word = lemma.strip()
    if _has_whitespace(word):
        return None
    row = None
    variants = _etymology_lookup_variants(word)
    try:
        for variant in variants:
            row = conn.execute(
                "SELECT etymology_text, source_url FROM wiktionary_etymology "
                "WHERE requested_lemma = ? AND etymology_text != '' LIMIT 1",
                (variant,),
            ).fetchone()
            if row:
                break
        if not row:
            for variant in variants:
                row = conn.execute(
                    "SELECT etymology_text, source_url FROM wiktionary_etymology "
                    "WHERE headword = ? AND etymology_text != '' LIMIT 1",
                    (variant,),
                ).fetchone()
                if row:
                    break
    except sqlite3.OperationalError as exc:
        if _missing_table(exc):
            return None
        raise
    if not row or not row[0]:
        return None
    return {
        "text": clean_html_entities(row[0].strip()[:600]),
        "source": "Вікісловник (uk.wiktionary)",
        "source_url": row[1],
    }


def _load_kaikki_lookup(path: Path = KAIKKI_LOOKUP) -> dict[str, dict[str, Any]]:
    """Load the compact Kaikki lookup if it has been preprocessed."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def _kaikki_row(lookup: dict[str, dict[str, Any]], lemma: str) -> dict[str, Any] | None:
    if not lookup or _has_whitespace(lemma):
        return None
    for variant in _etymology_lookup_variants(lemma):
        row = lookup.get(kaikki_lookup_key(variant))
        if isinstance(row, dict):
            return row
    return None


def _kaikki_pronunciation(lookup: dict[str, dict[str, Any]], lemma: str) -> dict[str, str] | None:
    row = _kaikki_row(lookup, lemma)
    if not row:
        return None
    ipa_values = row.get("ipa")
    if not isinstance(ipa_values, list):
        return None
    for value in ipa_values:
        ipa = clean_html_entities(str(value or "")).strip()
        if ipa:
            return {"ipa": ipa, "source": KAIKKI_SOURCE}
    return None


def _kaikki_etymology(lookup: dict[str, dict[str, Any]], lemma: str) -> dict | None:
    row = _kaikki_row(lookup, lemma)
    if not row:
        return None
    text = clean_html_entities(str(row.get("etymology_text") or "").strip()[:600])
    if not text:
        return None
    if _RUSSIAN_LABELED_CYRILLIC_RE.search(text):
        return None
    return {"text": text, "source": KAIKKI_SOURCE}


def _source_etymology(
    conn: sqlite3.Connection,
    lemma: str,
    kaikki_lookup: dict[str, dict[str, Any]] | None = None,
) -> dict | None:
    return (
        _goroh_etymology(conn, lemma)
        or _esum_etymology(conn, lemma)
        or _wiktionary_etymology(conn, lemma)
        or _kaikki_etymology(kaikki_lookup or {}, lemma)
    )


def _with_base_etymology_label(etymology: dict, base_form: str) -> dict:
    labeled = dict(etymology)
    source = str(labeled.get("source") or "").strip()
    label = f"etymology of base form {base_form}"
    labeled["source"] = f"{source} ({label})" if source else label
    return labeled


def _etymology(conn: sqlite3.Connection, lemma: str, kaikki_lookup: dict[str, dict[str, Any]] | None = None) -> dict | None:
    """Cached etymology by authority order, with derived-lemma base fallback."""
    lookup_word = _lookup_key(_base_lemma(lemma))
    if lookup_word in _COMPOSITIONAL_ETYMOLOGY_EXCLUSIONS:
        return None
    exact = _source_etymology(conn, lemma, kaikki_lookup)
    if exact:
        return exact
    for base_form in _derivational_etymology_candidates(lemma):
        etymology = _source_etymology(conn, base_form, kaikki_lookup)
        if etymology:
            return _with_base_etymology_label(etymology, base_form)
    return None


def _cefr(conn: sqlite3.Connection, lemma: str) -> dict[str, str] | None:
    for variant in _split_lemma_variants(lemma):
        try:
            row = conn.execute(
                "SELECT level, pos, text FROM puls_cefr "
                "WHERE word = ? COLLATE NOCASE AND level != '' LIMIT 1",
                (variant,),
            ).fetchone()
        except sqlite3.OperationalError as exc:
            if _missing_table(exc):
                return None
            raise
        if row and row[0]:
            block = {"level": str(row[0]).strip().upper(), "source": _CEFR_SOURCE}
            if row[1]:
                block["pos"] = clean_html_entities(str(row[1]).strip())
            if row[2]:
                block["text"] = clean_html_entities(str(row[2]).strip())
            return block
    return None


def _parse_translations(raw: object) -> list[str]:
    """Parse a dmklinger `translations` cell (JSON array of English gloss strings)."""
    if not raw:
        return []
    try:
        data = json.loads(raw) if isinstance(raw, str) else raw
    except (TypeError, ValueError):
        return []
    if not isinstance(data, list):
        return []
    out: list[str] = []
    for item in data:
        text = re.sub(r"\s+", " ", clean_html_entities(str(item)).strip())
        if text:
            out.append(text)
    return out


_DMKLINGER_INDEX: dict[str, list[tuple[str, str]]] | None = None


def _dmklinger_key(word: str) -> str:
    """Normalize a word for dmklinger matching: strip stress marks + casefold.

    dmklinger_uk_en stores STRESSED headwords (e.g. `робо́та`, `бу́ти`) while
    manifest lemmas are unstressed — so an exact match misses ~93%. Both sides
    are reduced to a stress-free, casefolded key.
    """
    return _strip_stress(word).strip().casefold()


def _load_dmklinger_index(conn: sqlite3.Connection) -> dict[str, list[tuple[str, str]]]:
    """Load dmklinger_uk_en once, keyed by stress-stripped/casefolded headword."""
    global _DMKLINGER_INDEX
    if _DMKLINGER_INDEX is not None:
        return _DMKLINGER_INDEX
    index: dict[str, list[tuple[str, str]]] = {}
    try:
        rows = conn.execute("SELECT word, pos, translations FROM dmklinger_uk_en").fetchall()
    except sqlite3.OperationalError as exc:
        if _missing_table(exc):
            _DMKLINGER_INDEX = {}
            return _DMKLINGER_INDEX
        raise
    for word, pos, translations in rows:
        key = _dmklinger_key(str(word or ""))
        if key:
            index.setdefault(key, []).append((pos, translations))
    _DMKLINGER_INDEX = index
    return index


def _translation(conn: sqlite3.Connection, lemma: str) -> dict[str, object] | None:
    """English translations for a Ukrainian lemma (Переклад, §11).

    Source is the dmklinger UK→EN dictionary (`dmklinger_uk_en`). Балла is EN→UK
    only — no clean reverse — so it is intentionally NOT used here; an exact
    UK→EN match avoids the noise of reverse-lookup. Returns up to six glosses.
    """
    index = _load_dmklinger_index(conn)
    if not index:
        return None
    for variant in _split_lemma_variants(lemma):
        rows = index.get(_dmklinger_key(variant))
        if not rows:
            continue
        english: list[str] = []
        seen: set[str] = set()
        pos: str | None = None
        for row_pos, raw in rows:
            if pos is None and row_pos:
                pos = clean_html_entities(str(row_pos).strip())
            for gloss in _parse_translations(raw):
                key = gloss.casefold()
                if key not in seen:
                    seen.add(key)
                    english.append(gloss)
        if english:
            block: dict[str, object] = {"en": english[:6], "source": _TRANSLATION_SOURCE}
            if pos:
                block["pos"] = pos
            return block
    return None


def _fts_phrase(term: str) -> str:
    cleaned = term.replace('"', " ").strip()
    return f'"{cleaned}"' if cleaned else ""


def _literary_excerpt(text: str, lemma: str, *, radius: int = 180) -> str:
    cleaned = re.sub(r"\s+", " ", clean_html_entities(text)).strip()
    term = _strip_stress(lemma).casefold()
    cleaned_stripped = _strip_stress(cleaned)
    match = _whole_token_pattern(term).search(cleaned_stripped.casefold())
    if not match:
        return ""
    start = max(0, match.start() - radius)
    end = min(len(cleaned_stripped), match.end() + radius)
    excerpt = cleaned_stripped[start:end].strip()
    if start > 0:
        excerpt = "…" + excerpt
    if end < len(cleaned_stripped):
        excerpt += "…"
    return excerpt


def _literary_attestation(conn: sqlite3.Connection, lemma: str) -> dict[str, Any] | None:
    if _has_whitespace(lemma):
        return None
    term = _strip_stress(_slovnyk_lookup_word(lemma)).casefold()
    query = _fts_phrase(term)
    if not query:
        return None
    try:
        rows = conn.execute(
            """
            SELECT
                l.chunk_id,
                l.author,
                l.work,
                l.title,
                l.year,
                l.text
            FROM literary_fts
            JOIN literary_texts l ON literary_fts.rowid = l.id
            WHERE literary_fts MATCH ?
            LIMIT 20
            """,
            (query,),
        ).fetchall()
    except sqlite3.OperationalError as exc:
        if _missing_table(exc):
            return None
        raise
    for chunk_id, author, work, title, year, text in rows:
        if not _contains_whole_token(_strip_stress(str(text or "")).casefold(), term):
            continue
        excerpt = _literary_excerpt(str(text or ""), term)
        if not excerpt:
            continue
        label_parts = [str(part).strip() for part in (author, work or title) if str(part or "").strip()]
        if year:
            label_parts.append(str(year))
        return {
            "text": excerpt,
            "source": _LITERARY_SOURCE,
            "source_label": " · ".join(label_parts) if label_parts else _LITERARY_SOURCE,
            "chunk_id": str(chunk_id or ""),
        }
    return None


def _single_word_etymology_coverage(manifest: dict) -> tuple[int, int]:
    entries = [
        entry
        for entry in manifest.get("entries", [])
        if entry.get("lemma") and not _has_whitespace(entry.get("lemma"))
    ]
    covered = sum(1 for entry in entries if (entry.get("enrichment") or {}).get("etymology"))
    return covered, len(entries)


def enrich() -> tuple[int, int]:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    kaikki_lookup = _load_kaikki_lookup()
    conn = sqlite3.connect(f"file:{SOURCES_DB}?mode=ro", uri=True)
    enriched = 0
    try:
        has_sum11_flags = _sum11_has_flag_columns(conn)
        for entry in manifest["entries"]:
            if entry.get("gloss"):
                entry["gloss"] = clean_gloss(str(entry["gloss"]))
            lemma = entry["lemma"]
            base = _base_lemma(lemma)
            slovnyk_cache = _slovnyk_cache(lemma)
            definition_cards = _definition_cards(
                conn,
                lemma,
                has_sum11_flags=has_sum11_flags,
                cache=slovnyk_cache,
            )
            heritage_status = classify_lemma(lemma)
            warning = (
                _warning_slovnyk(lemma, slovnyk_cache)
                if _is_slovnyk_warning_candidate(entry, heritage_status)
                else None
            )
            entry["heritage_status"] = _entry_scoped_heritage_status(
                _merge_slovnyk_warning(heritage_status, warning)
            )
            pronunciation = _kaikki_pronunciation(kaikki_lookup, lemma)
            if pronunciation:
                entry["pronunciation"] = pronunciation
            else:
                entry.pop("pronunciation", None)
            sections: dict[str, object] = {}
            synonyms = _synonyms_slovnyk(base, slovnyk_cache, entry_pos=entry.get("pos"))
            if synonyms:
                sections["synonyms"] = synonyms
            idioms = _idioms_slovnyk(lemma, slovnyk_cache)
            if idioms:
                sections["idioms"] = idioms
            if sections:
                entry["sections"] = sections
            else:
                entry.pop("sections", None)
            block: dict[str, object] = {}
            stressed_lemma = _stress_display_form(lemma)
            if stressed_lemma:
                block["stress"] = {"form": stressed_lemma, "source": _STRESS_SOURCE}
            cefr = _cefr(conn, lemma)
            if cefr:
                block["cefr"] = cefr
            morph = _morphology(base)
            if morph:
                block["morphology"] = morph
            meaning = _meaning(conn, lemma, has_sum11_flags=has_sum11_flags)
            if meaning:
                block["meaning"] = meaning
            if definition_cards:
                block["definition_cards"] = definition_cards
            etym = _etymology(conn, base, kaikki_lookup)
            if etym:
                block["etymology"] = etym
            literary = _literary_attestation(conn, lemma)
            if literary:
                block["literary_attestation"] = literary
            translation = _translation(conn, lemma)
            if translation:
                block["translation"] = translation
            if block:
                sources = {v["source"] for v in block.values() if isinstance(v, dict) and v.get("source")}
                for card in definition_cards:
                    if card.get("source"):
                        sources.add(str(card["source"]))
                for section in sections.values():
                    if isinstance(section, dict) and section.get("source"):
                        sources.add(str(section["source"]))
                block["sources"] = sorted(sources)
                entry["enrichment"] = block
            else:
                entry.pop("enrichment", None)
            if block or sections or pronunciation:
                enriched += 1
    finally:
        conn.close()
    manifest["enrichment_generated"] = True
    manifest = _clean_html_entities_in_obj(manifest)
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return enriched, len(manifest["entries"])


def main() -> None:
    enriched, total = enrich()
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    etymology_covered, etymology_total = _single_word_etymology_coverage(manifest)
    pronunciation_covered = sum(
        1
        for entry in manifest.get("entries", [])
        if isinstance(entry.get("pronunciation"), dict) and entry["pronunciation"].get("ipa")
    )
    print(
        "enriched "
        f"{enriched}/{total} lexicon entries from "
        "VESUM + СУМ + Горох/ЕСУМ/Вікісловник/kaikki + slovnyk.me"
    )
    print(f"pronunciation {pronunciation_covered}/{total}")
    print(f"single-word etymology {etymology_covered}/{etymology_total}")


if __name__ == "__main__":
    main()
