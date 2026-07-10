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
- **cefr** — PULS CEFR lookup when available, otherwise a visibly labelled
  GRAC-frequency estimate for entries outside PULS.
- **literary_attestation** — exact-form literary corpus hit when available.
- **synonyms** — source-attested Ukrainian candidates from clean slovnyk.me
  synonym dictionaries, with noisy legacy sources kept A1-sense allowlisted.
- **sections.synonyms / sections.antonyms / sections.idioms** — slovnyk.me
  per-lemma lookup cache and local dictionary rows (Караванський + Словник
  синонімів; Вікісловник antonyms; Фразеологічний).
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
import functools
import html
import json
import os
import random
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

from scripts.lexicon.build_data_manifest import _slug_for_url
from scripts.lexicon.build_kaikki_lookup import KAIKKI_SOURCE
from scripts.lexicon.build_kaikki_lookup import _clean_gloss as _clean_translation_gloss
from scripts.lexicon.build_kaikki_lookup import lookup_key as kaikki_lookup_key
from scripts.lexicon.calque_corrections import (
    CURATED_CALQUES,
    PHRASAL_CALQUES,
    SENSE_RESTRICTED_CALQUES,
)
from scripts.lexicon.esum_garbled import (
    garbled_esum_entry,
    has_mojibake_marker,
    strip_garbled_tail,
    trim_curated_goroh_text,
)
from scripts.lexicon.heritage_classifier import classify_lemma, compute_warning_severity
from scripts.lexicon.lemma_normalization import strip_acute_stress
from scripts.lexicon.manifest_fingerprint import DEFAULT_FINGERPRINT, write_fingerprint
from scripts.verification.vesum import verify_lemma, verify_word
from scripts.wiki.slovnyk_me import primary_synonym_sense_text

MANIFEST = ROOT / "site" / "src" / "data" / "lexicon-manifest.json"
SOURCES_DB = ROOT / "data" / "sources.db"
KAIKKI_LOOKUP = ROOT / "data" / "lexicon" / "kaikki_uk_lookup.json"
WIKI_REFERENCE_CACHE = ROOT / "data" / "lexicon" / "cache" / "wiki_reference.json"
GRAC_FREQUENCY_CACHE = ROOT / "data" / "lexicon" / "cache" / "grac_frequency.json"


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
# slovnyk.me is Cloudflare-fronted and rate-limits bursts (429). 0.12s (~8 req/s) tripped
# it: 429 -> _SlovnykTransientError -> never cached -> re-fetched every run (#3097). 0.34s
# (~3 req/s) is Cloudflare-friendly for sustained scraping; the mirror builder can override
# via LEXICON_SLOVNYK_DELAY. Paired with Retry-After + exponential backoff in _fetch_slovnyk_entry.
_SLOVNYK_DELAY_SECONDS = float(os.environ.get("LEXICON_SLOVNYK_DELAY", "0.34"))
_SLOVNYK_MAX_RETRIES = int(os.environ.get("LEXICON_SLOVNYK_MAX_RETRIES", "5"))
_SLOVNYK_BACKOFF_BASE_SECONDS = 1.5
_SLOVNYK_BACKOFF_CAP_SECONDS = 90.0
_SLOVNYK_USER_AGENT = "learn-ukrainian-word-atlas/1.0 (noncommercial educational per-lemma lookup; issue #2985)"
_STRESS_SOURCE = "ukrainian-word-stress"
_CEFR_SOURCE = "PULS CEFR"
_CEFR_ESTIMATED_SOURCE = "estimated (GRAC frequency)"
_LITERARY_SOURCE = "literary_fts"
_TRANSLATION_SOURCE = "dmklinger"
_SUM20_COVERED_INITIALS = set("абвгґдеєжзиіїйклмнопр")
_UKRAINIAN_WORD_RE = re.compile(r"^[А-Яа-яЄєІіЇїҐґ'’ʼ-]+$")
_UKRAINIAN_VOWELS = set("аеєиіїоуюяАЕЄИІЇОУЮЯ")
_IPA_STRESS_RE = re.compile(r"[ˈˌ]")
_IPA_PRIMARY_STRESS_RE = re.compile(r"ˈ")
_IPA_NON_SYLLABIC_MARK_RE = re.compile(r"[\u032f\u0311]")
_IPA_VOWEL_RE = re.compile(r"[aeiouyɐɑɒæɛɜɞɘəɚɝɨɪɯɵøœɔɤʊʉɾ]+", flags=re.IGNORECASE)
_KAIKKI_GARBLED_ETYMOLOGY_RE = re.compile(r"\bEtymology tree\b|\[Term\?\]", flags=re.IGNORECASE)
_GRAC_WORDLIST_URL = "https://sketch.uacorpus.org/bonito/run.cgi/wordlist"
_GRAC_CORPUS = "grac19a"
_GRAC_BATCH_SIZE = 25

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
_SLOVNYK_UKRENG_SLUG = "ukreng"
_SLOVNYK_UKRENG_LABEL = "Українсько-англійський словник"
_SLOVNYK_UKRENG_SOURCE = f"slovnyk.me: {_SLOVNYK_UKRENG_LABEL}"
_SLOVNYK_BASE = "https://slovnyk.me"
_SLOVNYK_CACHE_SCHEMA_VERSION = 2
_OFFLINE_VALUES = {"1", "true", "yes", "on"}
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

# Transparent learner-facing glosses for common particles/interjections where
# the Ukrainian dictionaries have exact definition cards but the local bilingual
# and Kaikki/Wiktionary sources have no English row. Keep this small and
# high-confidence; never pretend these are dictionary imports.
_CURATED_LEARNER_TRANSLATIONS: dict[str, tuple[str, ...]] = {
    "ого": ("wow", "whoa"),
}

_BALLA_REVERSE_SOURCE = "Балла EN→UK reverse exact"
_BALLA_REVERSE_MAX_HEADWORDS = 1
_BALLA_REVERSE_UKRAINIAN_TOKEN_RE = re.compile(r"[А-Яа-яЄєІіЇїҐґ][А-Яа-яЄєІіЇїҐґ'’ʼ-]*")
_BALLA_REVERSE_SURFACE_GLOSS_RE = re.compile(r"surface gloss='([^']+)'")
_BALLA_REVERSE_SOURCE_POS_RE = re.compile(r"pos='([^']+)'")
_BALLA_REVERSE_HINT_SPLIT_RE = re.compile(r"[,;/]")
_BALLA_REVERSE_LEADING_LABEL_RE = re.compile(
    r"^\s*(?:\d+\.?\s*)?(?:(?:n|v|adj|adv|prep|pron|conj|interj|num|part|abbr)\.?\s+)+",
    flags=re.IGNORECASE,
)
_BALLA_REVERSE_HEADWORD_RE = re.compile(r"[a-z][a-z -]{1,39}", flags=re.IGNORECASE)
_BALLA_REVERSE_STOP_TOKENS = {
    "а",
    "або",
    "без",
    "біля",
    "в",
    "від",
    "до",
    "за",
    "з",
    "зі",
    "із",
    "на",
    "над",
    "не",
    "під",
    "по",
    "при",
    "про",
    "та",
    "у",
    "чи",
    "як",
    "амер",
    "англ",
    "бот",
    "буд",
    "військ",
    "грам",
    "див",
    "зоол",
    "іст",
    "книжн",
    "лінгв",
    "мед",
    "мін",
    "мор",
    "муз",
    "перен",
    "поет",
    "розм",
    "спорт",
    "тех",
    "тж",
    "фіз",
    "хім",
    "церк",
    "юр",
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

# #3116 — curated PER-LEMMA wrong-sense synonym exclusions. Each listed word is
# authentic Ukrainian (Грінченко/ЕСУМ-attested, NOT a Russianism) that the
# Karavansky synset over-includes under a sense the lemma does NOT carry. It is
# excluded only for that specific lemma — NEVER globally (cf. _BLOCKED_SYNONYMS) —
# so the word stays valid for the lemmas where it IS correct. This is the
# блискучий/кам'янка heritage lesson: fix the wrong (lemma, sense) pair, never
# stoplist a valid word.
#   шлях → кам'яниця: Грінченко = "Каменное строеніе" (stone building) / sparrow
#          trap; ЕСУМ adds the stone-bramble berry — no road sense. The road term
#          is кам'янка (Грінченко sense 4: "Шосе. Кам'янкою їхати").
#   річка → звір: Грінченко звір I = "Овраг, лощина" (ravine), звір II = "зверь"
#          (beast) — neither is a river.
_WRONG_SENSE_SYNONYMS: dict[str, frozenset[str]] = {
    "шлях": frozenset({"кам'яниця"}),
    "річка": frozenset({"звір"}),
}

# #3197 — Вікісловник's explicit antonym column carries pedagogical noise the POS
# gate alone can't catch: alphabet meta-pairs (а→зет), co-hyponyms / paradigm
# members dressed as opposites (дочка→матка, він→ми), wrong-sense opposites
# (газ→гальмо, ім'я→неслава) and Russian contamination (не→да). Mirror the #3168
# _WRONG_SENSE_SYNONYMS lesson: curated per-lemma filter, NEVER a global stoplist.
# Two layers, both verified via the sources MCP (СУМ-11 / VESUM / russian_shadow):
#   _DROP_ANTONYM_LEMMAS — lemmas whose ENTIRE antonym set is noise:
#     а→зет (letter-name sequence); брат (no lexical antonym — сестра is the
#     gendered pair, not an opposite); він→ми (pronoun paradigm, not opposition —
#     the contrast is вона); газ→гальмо (holds only for the accelerator-pedal
#     sense, misleading for газ="gas"); мавпа (no opposite — оригінал/красуня are
#     folk-insult noise); не→да (да: check_russian_shadow matches_russian=1.0 and
#     absent from VESUM → Russian); так ("не так" are negations, the real opposite
#     ні is absent); четвер (a weekday has no opposite — "день тижня" is a
#     hypernym); ім'я→неслава (wrong-sense: ім'я="name", not "good repute"); шлях
#     (same family as #3168 — стежка is a co-hyponym; obstacle terms aren't
#     opposites of a path).
#   _WRONG_ANTONYMS — per-lemma term drops where SOME opposites survive:
#     дочка: keep син; drop the мати-variants + матка (СУМ-11 "плідна самиця" /
#       uterus / queen bee, not a daughter-opposite) + батько/падчірка (relatives);
#     друг: keep ворог/недруг; drop екс (slang) + нелюб (archaic, off-sense);
#     село: keep місто; drop міщанство/град + город (СУМ-11 modern sense =
#       kitchen-garden, NOT city — false friend with Russian город);
#     тло: keep фігура (figure↔ground); drop сильвета/сильветка (silhouette).
_DROP_ANTONYM_LEMMAS: frozenset[str] = frozenset(
    {
        "а",
        "брат",
        "він",
        "газ",
        "мавпа",
        "не",
        "так",
        "четвер",
        "ім'я",
        "шлях",
    }
)

_WRONG_ANTONYMS: dict[str, frozenset[str]] = {
    "дочка": frozenset(
        {
            "мати",
            "батько",
            "падчірка",
            "матка",
            "матінка",
            "мама",
            "матір",
            "матірка",
            "матуся",
            "матіночка",
            "матусенька",
        }
    ),
    "друг": frozenset({"екс", "нелюб"}),
    "село": frozenset({"міщанство", "град", "город"}),
    "тло": frozenset({"сильвета", "сильветка"}),
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

_DERIVATIONAL_ETYMOLOGY_BASES: dict[str, tuple[str, ...]] = {
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

_ORDINAL_ETYMOLOGY_BASES: dict[str, tuple[str, ...]] = {
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

# VESUM style/register markers → learner-facing Ukrainian label. Forms carrying any
# of these are non-standard/stylistic and must NOT render inline with the modern
# paradigm (#4891 — корисная «нестягнена» read as ordinary «жін., називний» beside
# корисна). Marker semantics are quoted verbatim from the official dict_uk tagset
# doc (``doc/tags.txt`` @ github.com/brown-uk/dict_uk), cross-checked against
# ground-truth forms in ``data/vesum.db``:
#   long  L40 "нестягнені форми прикметників" · L32 "наказові форми на -іте"
#         · L61 "звортні дієприслівники на -ся"
#   arch  L114 "застаріле/архаїчне/(інколи) діалектне"
#   short L39 "короткі форми прикметників" · L31 "короткі форми дієслів 3-ї особи…"
#   rare  L112 "другий зн. в. для істот (в президенти), плюс декілька рідкісних форм"
#   slang L115 "сленг та (проф)жаргонізми"
#   coll  L113 "розмовне слово/розмовна форма (наразі не генеруємо на виході)"
#   obsc  L118 "обсценне"
#   bad   L109 "покруч"
#   alt   L116 "альтернативне написання (не за чинним правописом)"
#   up19  L121 "за правописом 2019 (на виході вилучаємо)"
#   up92  L120 "за правописом 1992 (на виході конвертуємо в alt)"
# `ns` (L92 "множинний іменник") is DELIBERATELY EXCLUDED: it is a grammatical
# sub-class (pluralia tantum — двері, окуляри, ножиці, гроші), whose plural forms
# ARE the modern literary norm; segregating it would empty those paradigms.
# `coll`/`bad` never appear in our VESUM build ("не генеруємо на виході") but are
# mapped for completeness so any future dictionary refresh stays labelled.
_STYLE_MARKER_LABELS: dict[str, str] = {
    "long": "нестягнена форма",
    "arch": "застаріла форма",
    "short": "коротка форма",
    "rare": "рідковживана форма",
    "slang": "сленгова форма",
    "coll": "розмовна форма",
    "obsc": "обсценна форма",
    "bad": "спотворена форма",
    "alt": "альтернативне написання",
    "up19": "форма за правописом 2019 року",
    "up92": "форма за правописом 1992 року",
}

# Tokens that move a form out of the modern paradigm. Equal to the verified-label keys
# today, kept as a distinct set so a future VESUM style flag can be segregated (falling
# back to the generic label below) BEFORE its Ukrainian label is authored — without ever
# silently reclassifying a grammatical token. Grammatical sub-tags (rev/adjp/pasv/actv/
# comps/compc/impers/xp1/xp2/subst/nv/ns …) are deliberately absent.
_STYLE_MARKERS: frozenset[str] = frozenset(_STYLE_MARKER_LABELS)

# Never guess a description for a marker we have not verified (#M-4): an unlabelled but
# segregated marker gets this honest generic label rather than a fabricated meaning.
_GENERIC_STYLE_MARKER_LABEL = "інша маркована форма"

# Cap on rows shipped per paradigm section. ``form_count`` is reported AFTER the cap
# so it never disagrees with the rows actually rendered (pre-#4891 it reported the
# uncapped total → «41 форм» beside 40 rows for корисний).
_MORPHOLOGY_FORM_CAP = 40

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


def _style_markers_in_tag(tag: str) -> list[str]:
    """Style/register markers present in a raw VESUM tag, in tag-token order.

    Matches whole colon-delimited tokens (never substrings) so grammatical tokens
    are never mistaken for a marker. Returns ``[]`` for a plain modern-paradigm tag.
    """
    return [token for token in tag.split(":") if token in _STYLE_MARKERS]


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
    cells: dict[str, dict[str, list[str]]] = {case: {"singular": [], "plural": []} for case in _NOUN_CASE_ORDER}
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
        tense: {number: {person: [] for person in _PERSONS} for number in _NUMBERS} for tense in _VERB_TENSES
    }
    imperative: dict[str, dict[str, list[str]]] = {number: {person: [] for person in _PERSONS} for number in _NUMBERS}
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
        has_tense = any(tenses[tense][number][person] for number in _NUMBERS for person in _PERSONS)
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


def _phase1_offline_mode() -> bool:
    return os.environ.get("LEXICON_SLOVNYK_OFFLINE", "").strip().casefold() in _OFFLINE_VALUES


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


def _manifest_lemma_key(lemma: str) -> str:
    return _lookup_key(strip_acute_stress(lemma)).casefold()


def _merge_unique_dicts(
    target: dict[str, Any],
    source: dict[str, Any],
    field: str,
    identity_fields: tuple[str, ...],
) -> None:
    source_items = source.get(field)
    if not isinstance(source_items, list):
        return
    target_items = target.setdefault(field, [])
    if not isinstance(target_items, list):
        target[field] = target_items = []
    seen = {
        tuple(str(item.get(key) or "") for key in identity_fields) for item in target_items if isinstance(item, dict)
    }
    for item in source_items:
        if not isinstance(item, dict):
            continue
        identity = tuple(str(item.get(key) or "") for key in identity_fields)
        if identity in seen:
            continue
        seen.add(identity)
        target_items.append(item)


def _merge_duplicate_manifest_entry(target: dict[str, Any], source: dict[str, Any]) -> None:
    _merge_unique_dicts(target, source, "course_usage", ("track", "module_num", "slug"))
    _merge_unique_dicts(target, source, "atlas_normalizations", ("kind", "source_lemma", "target_lemma"))
    variants = target.setdefault("slug_variants", [])
    for variant in source.get("slug_variants", []):
        if not isinstance(variant, str):
            continue
        clean_variant = strip_acute_stress(variant)
        if clean_variant == target.get("lemma"):
            continue
        if isinstance(variants, list) and clean_variant not in variants:
            variants.append(clean_variant)
    for field, value in source.items():
        if field in {"lemma", "url_slug", "course_usage", "atlas_normalizations", "slug_variants"}:
            continue
        if field not in target or target[field] in (None, "", [], {}):
            target[field] = value


def _normalize_manifest_entries(manifest: dict[str, Any]) -> int:
    """Strip acute stress from manifest lemma keys and merge resulting duplicates."""
    entries = manifest.get("entries")
    if not isinstance(entries, list):
        return 0
    normalized_entries: list[Any] = []
    by_key: dict[str, dict[str, Any]] = {}
    changes = 0
    for entry in entries:
        if not isinstance(entry, dict):
            normalized_entries.append(entry)
            continue
        raw_lemma = entry.get("lemma")
        if not isinstance(raw_lemma, str):
            normalized_entries.append(entry)
            continue
        lemma = strip_acute_stress(raw_lemma)
        if lemma != raw_lemma:
            entry["lemma"] = lemma
            changes += 1
        slug = _slug_for_url(lemma)
        if entry.get("url_slug") != slug:
            entry["url_slug"] = slug
            changes += 1
        key = _manifest_lemma_key(lemma)
        existing = by_key.get(key)
        if existing is not None:
            _merge_duplicate_manifest_entry(existing, entry)
            changes += 1
            continue
        by_key[key] = entry
        normalized_entries.append(entry)
    if changes:
        manifest["entries"] = sorted(
            normalized_entries,
            key=lambda item: str(item.get("lemma") or "") if isinstance(item, dict) else "",
        )
    return changes


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
    if not clean or _has_whitespace(clean) or not _UKRAINIAN_WORD_RE.fullmatch(clean) or _count_vowels(clean) < 2:
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


def _parse_retry_after(value: str | None) -> float | None:
    """Parse a ``Retry-After`` header (delta-seconds form; Cloudflare uses integers)."""
    if not value:
        return None
    try:
        return max(0.0, float(value))
    except (TypeError, ValueError):
        return None


def _slovnyk_backoff_sleep(attempt: int, retry_after: float | None) -> None:
    """Sleep before a retry: honor Retry-After, else exponential backoff + jitter."""
    if retry_after is not None:
        delay = retry_after
    else:
        delay = min(_SLOVNYK_BACKOFF_CAP_SECONDS, _SLOVNYK_BACKOFF_BASE_SECONDS * (2**attempt))
    time.sleep(delay + random.uniform(0.0, 0.5))


def _fetch_slovnyk_entry(lemma: str, lookup_word: str, slug: str) -> dict[str, Any] | None:
    """Fetch one slovnyk.me dictionary entry, 429-friendly.

    Retries 429/5xx/network errors with Retry-After + exponential backoff (so a rate-limit
    resolves into a real result instead of a transient miss that is never cached, #3097).
    Returns the parsed entry, ``None`` for a genuine 404 (cached as a known miss), or raises
    ``_SlovnykTransientError`` only after exhausting retries (caller leaves the slug uncached
    so a later run retries it).
    """
    if _phase1_offline_mode():
        return None

    url = f"{_SLOVNYK_BASE}/dict/{slug}/{quote(lookup_word)}"
    for attempt in range(_SLOVNYK_MAX_RETRIES + 1):
        _polite_slovnyk_delay()
        try:
            response = requests.get(url, timeout=20, headers={"User-Agent": _SLOVNYK_USER_AGENT})
        except requests.RequestException as exc:
            if attempt < _SLOVNYK_MAX_RETRIES:
                _slovnyk_backoff_sleep(attempt, None)
                continue
            raise _SlovnykTransientError(f"transient slovnyk.me request failure for {url}") from exc

        if response.status_code == 404:
            return None
        if response.status_code == 429 or response.status_code >= 500:
            if attempt < _SLOVNYK_MAX_RETRIES:
                _slovnyk_backoff_sleep(attempt, _parse_retry_after(response.headers.get("Retry-After")))
                continue
            raise _SlovnykTransientError(f"transient slovnyk.me status {response.status_code} for {url}")
        try:
            response.raise_for_status()
        except requests.HTTPError as exc:
            raise _SlovnykTransientError(f"transient slovnyk.me request failure for {url}") from exc
        return _parse_slovnyk_entry(
            response.text,
            lemma=lemma,
            lookup_word=lookup_word,
            slug=slug,
            url=url,
        )
    raise _SlovnykTransientError(f"transient slovnyk.me exhausted retries for {url}")


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
                cache["lookups"] = {slug: row for slug, row in raw_lookups.items() if row is not None}
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

    if _phase1_offline_mode():
        return cache

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


def _cache_has_lookup(cache: dict[str, Any] | None, slug: str) -> bool:
    if not isinstance(cache, dict):
        return False
    lookups = cache.get("lookups")
    return isinstance(lookups, dict) and slug in lookups


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
        (str(row.get("lemma") or ""), str(row.get("pos") or "")) for row in rows if row.get("lemma") and row.get("pos")
    }
    return tuple(sorted(analyses))


def _vesum_word_poses(word: str) -> set[str]:
    return {pos for _lemma, pos in _vesum_word_analyses(word)}


def _vesum_base_lemma(word: str) -> str | None:
    """Resolve an inflected surface form to its VESUM base lemma (моєму → мій,
    п'ємо → пити) ONLY when that base is unambiguous. If the form maps to several
    distinct lemmas — a homograph, e.g. «став» → стати (verb) / став (noun) — return
    None rather than guess, so we never show an unrelated word's definition. Also
    returns None when the word is already its own lemma or VESUM has no analysis."""
    surface = _lookup_key(word).casefold()
    bases = {lemma for lemma, _pos in _vesum_word_analyses(surface) if lemma and lemma.casefold() != surface}
    return next(iter(bases)) if len(bases) == 1 else None


def _vesum_base_lemma_for_entry_pos(word: str, entry_pos: object) -> str | None:
    """Resolve an inflected form to a VESUM base matching the entry POS."""
    target_pos = _MANIFEST_POS_TO_VESUM_POS.get(_lookup_key(str(entry_pos or "")))
    if not target_pos:
        return None
    surface = _lookup_key(word).casefold()
    bases = {
        lemma
        for lemma, pos in _vesum_word_analyses(surface)
        if lemma and lemma.casefold() != surface and pos == target_pos
    }
    return next(iter(bases)) if len(bases) == 1 else None


def _base_lookup_for_entry(lemma: str, entry_pos: object) -> str | None:
    base = _vesum_base_lemma_for_entry_pos(lemma, entry_pos)
    if not base or _has_whitespace(base):
        return None
    direct = _lookup_key(_base_lemma(lemma)).casefold()
    base_key = _lookup_key(base).casefold()
    return base if base_key and base_key != direct else None


def _with_base_source_label(block: dict[str, Any], base_form: str) -> dict[str, Any]:
    labeled = dict(block)
    source = str(labeled.get("source") or "").strip()
    label = f"base form {base_form}"
    labeled["source"] = f"{source} ({label})" if source else label
    return labeled


@lru_cache(maxsize=8192)
def _slovnyk_base_row(base_lemma: str, slug: str) -> dict[str, Any] | None:
    """Fetch a slovnyk.me row for a resolved base lemma, deduped within a run so a
    base shared by many forms (мій ← моєму, мого, моїй …) is fetched once."""
    lookup_word = _slovnyk_lookup_word(base_lemma)
    if not lookup_word:
        return None
    try:
        return _fetch_slovnyk_entry(base_lemma, lookup_word, slug)
    except _SlovnykTransientError:
        return None


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
    headword_lemmas = {analysis_lemma for analysis_lemma, pos in _vesum_word_analyses(headword) if pos == headword_pos}
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
    body = re.sub(r"\((діал|розм|заст|д|з)\.?\)", r" \1. ", body, flags=re.IGNORECASE)
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
    excluded = _WRONG_SENSE_SYNONYMS.get(_base_lemma(lemma).casefold())
    if excluded:
        normalized = term.replace("’", "'").replace("ʼ", "'").replace("`", "'")
        if normalized in excluded:
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


def _extract_qualifier(text: str) -> str | None:
    lower_text = text.lower()
    if re.search(r"\bдіал\b\.?|\bд\.", lower_text):
        return "діал."
    if re.search(r"\bрозм\b\.?", lower_text):
        return "розм."
    if re.search(r"\bзаст\b\.?|\bз\.", lower_text):
        return "заст."
    if re.search(r"\bрідше\b\.?", lower_text):
        return "рідше"
    if re.search(r"\bрідко\b\.?", lower_text):
        return "рідко"
    return None


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
            qualifier = _extract_qualifier(part)
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
                term_with_tag = f"{term} ({qualifier})" if qualifier else term
                out.append(term_with_tag)
    return out


def _base_word(term: str) -> str:
    return term.split(" (")[0]


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
        row_bases = [_base_word(item) for item in row_items]
        if slug == "synonyms" and row_items:
            group_head = _slovnyk_synonym_group_head(row, lookup_lemma)
            allowlisted = _safe_synonym_set(lookup_lemma)
            if (
                group_head != lookup_lemma.casefold()
                and not seen.intersection(row_bases)
                and not allowlisted.intersection(row_bases)
            ):
                continue
        if not row_items:
            continue
        for synonym in row_items:
            base = _base_word(synonym)
            if base not in seen:
                seen.add(base)
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


def _clean_atlas_chip_candidate(candidate: str, lemma: str) -> str | None:
    term = _strip_stress(candidate)
    term = re.sub(r"<[^>]+>", " ", term)
    term = re.sub(r"\s+", " ", term).strip()
    term = term.strip(' \t\r\n.,;:!?/\\[]{}«»"“”<>')
    term = term.casefold()
    if not term or term in _BLOCKED_SYNONYMS:
        return None
    if _LATIN_RE.search(term) or not _UKRAINIAN_TEXT_RE.fullmatch(term):
        return None
    words = term.split()
    if len(words) > 4:
        return None
    for variant in _split_lemma_variants(_strip_stress(lemma)):
        if term == variant.casefold():
            return None
    return term


def _wiktionary_has_antonyms_column(conn: sqlite3.Connection) -> bool:
    try:
        return any(row[1] == "antonyms" for row in conn.execute("PRAGMA table_info(wiktionary)"))
    except sqlite3.OperationalError as exc:
        if _missing_table(exc):
            return False
        raise


def _candidate_matches_entry_pos(candidate: str, entry_pos: str | None) -> bool:
    mapped_pos = _MANIFEST_POS_TO_VESUM_POS.get(_lookup_key(entry_pos or ""))
    if not mapped_pos or _has_whitespace(candidate):
        return True
    return _candidate_matches_headword_pos(candidate, mapped_pos)


def _antonyms_wiktionary(
    conn: sqlite3.Connection,
    lemma: str,
    *,
    entry_pos: str | None = None,
) -> dict[str, Any] | None:
    """Antonym chips from explicit Wiktionary antonym rows, omitted when empty."""
    if not _wiktionary_has_antonyms_column(conn):
        return None

    # #3197 — per-lemma pedagogy filter over the raw Вікісловник antonym column.
    base_key = _base_lemma(lemma).casefold().replace("’", "'").replace("ʼ", "'").replace("`", "'")
    if base_key in _DROP_ANTONYM_LEMMAS:
        return None
    wrong_terms = _WRONG_ANTONYMS.get(base_key)

    items: list[str] = []
    seen: set[str] = set()
    try:
        for variant in _etymology_lookup_variants(_base_lemma(lemma)):
            row = conn.execute(
                "SELECT antonyms FROM wiktionary WHERE word = ? COLLATE NOCASE AND antonyms != '' LIMIT 1",
                (variant,),
            ).fetchone()
            if not row:
                continue
            try:
                candidates = json.loads(row[0] or "[]")
            except (TypeError, ValueError):
                candidates = []
            if not isinstance(candidates, list):
                continue
            for candidate in candidates:
                term = _clean_atlas_chip_candidate(str(candidate), lemma)
                if not term or term in seen:
                    continue
                if wrong_terms:
                    normalized = term.replace("’", "'").replace("ʼ", "'").replace("`", "'")
                    if normalized in wrong_terms:
                        continue
                if _candidate_matches_entry_pos(term, entry_pos):
                    seen.add(term)
                    items.append(term)
            if items:
                break
    except sqlite3.OperationalError as exc:
        if _missing_table(exc):
            return None
        raise

    if not items:
        return None
    return {
        "items": items[:12],
        "source": "Вікісловник: explicit antonym list",
        "source_urls": [f"https://uk.wiktionary.org/wiki/{quote(_base_lemma(lemma))}"],
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


_PHRASEOLOGY_MARKUP_REPLACEMENTS = (
    ("[']", ""),
    ("[/']", ""),
    ("≤", ""),
    ("≥", ""),
    ("{{</fras>}}", ""),
    ("{{", ""),
    ("}}", ""),
)


def _clean_phraseology_text(text: str) -> str:
    cleaned = clean_html_entities(str(text or ""))
    cleaned = re.sub(r"<[^>]+>", " ", cleaned)
    for old, new in _PHRASEOLOGY_MARKUP_REPLACEMENTS:
        cleaned = cleaned.replace(old, new)
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip()


def _leading_phraseology_phrase(definition: str, headword: str) -> str:
    cleaned_definition = _clean_phraseology_text(definition)
    protected = _protect_idiom_abbreviation_periods(cleaned_definition)
    match = re.match(r"(.{3,220}?\.)\s+", protected)
    if match:
        return _restore_idiom_abbreviation_periods(match.group(1)).strip(" .")
    return _clean_phraseology_text(headword).strip(" .")


def _phrase_contains_lemma(phrase: str, lemma: str) -> bool:
    clean_phrase = _lookup_key(_clean_phraseology_text(phrase))
    variants = [_lookup_key(variant) for variant in _split_lemma_variants(_base_lemma(lemma))]
    variants = [variant for variant in variants if variant]
    if any(_contains_whole_token(clean_phrase, variant) for variant in variants):
        return True
    if _has_whitespace(clean_phrase):
        tokens = re.findall(rf"[{_CYRILLIC_WORD_CHARS}]+", clean_phrase)
        expected = set(variants)
        for token in tokens:
            if any(analysis_lemma in expected for analysis_lemma, _pos in _vesum_word_analyses(token)):
                return True
    return False


def _phraseology_definition_body(definition: str, phrase: str) -> str:
    body = _clean_phraseology_text(definition)
    if phrase:
        pattern = re.compile(rf"^\s*{re.escape(_clean_phraseology_text(phrase))}\.?\s*", flags=re.IGNORECASE)
        body = pattern.sub("", body, count=1).strip()
    body = re.sub(r"^\d+\.\s*", "", body)
    return _truncate_text(body, 650)


_FRAZEOLOHICHNYI_FTS_AVAILABLE: dict[str, bool] = {}
_FRAZEOLOHICHNYI_FTS_WARN_LOGGED = False

_ASCII_LOWER_TABLE = str.maketrans("ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz")


def _db_cache_key(conn: sqlite3.Connection) -> str | None:
    """Stable per-database cache key: the main DB file path, or ``None`` for
    in-memory/temporary (pathless) databases — those are never cached.

    Index-availability verdicts are properties of the DATABASE, not the
    process — a process-global cache would let DB A's verdict leak onto
    DB B (codex review of #4514, finding 2). Pathless DBs get no key at
    all: an ``id(conn)``-based sentinel is reused by the allocator after
    the connection closes, leaking a stale verdict onto an unrelated new
    connection (codex re-review, reproduced).
    """
    try:
        for _seq, name, path in conn.execute("PRAGMA database_list"):
            if name == "main":
                return path or None
    except sqlite3.Error:
        pass
    return None


def _cache_verdict(cache: dict[str, bool], key: str | None, verdict: bool) -> bool:
    """Record an availability verdict for file-backed DBs; pathless DBs
    (key=None) are never cached."""
    if key is not None:
        cache[key] = verdict
    return verdict


def _ascii_lower_contains(text: str, needle: str) -> bool:
    """Replicate SQLite's ASCII-only ``lower()`` + ``LIKE '%needle%'``
    semantics — the parity predicate for index-accelerated paths (SQLite's
    ``lower()`` does not fold Cyrillic)."""
    return needle in text.translate(_ASCII_LOWER_TABLE)


def _is_connection_readonly(conn: sqlite3.Connection) -> bool:
    try:
        val = conn.execute("PRAGMA user_version;").fetchone()[0]
        conn.execute(f"PRAGMA user_version = {val};")
        return False
    except sqlite3.Error:
        return True

def _ensure_frazeolohichnyi_fts(conn: sqlite3.Connection) -> bool:
    global _FRAZEOLOHICHNYI_FTS_WARN_LOGGED
    key = _db_cache_key(conn)
    cached = _FRAZEOLOHICHNYI_FTS_AVAILABLE.get(key)
    if cached is not None:
        return cached

    # 1. Verify SQLite runtime supports trigram (3.34+)
    if sqlite3.sqlite_version_info < (3, 34, 0):
        return _cache_verdict(_FRAZEOLOHICHNYI_FTS_AVAILABLE, key, False)

    # Check if frazeolohichnyi table exists
    try:
        cur = conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='frazeolohichnyi'")
        if not cur.fetchone():
            return _cache_verdict(_FRAZEOLOHICHNYI_FTS_AVAILABLE, key, False)
    except sqlite3.Error:
        return _cache_verdict(_FRAZEOLOHICHNYI_FTS_AVAILABLE, key, False)

    # Check if index table exists
    try:
        cur = conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='frazeolohichnyi_fts'")
        exists = cur.fetchone() is not None
    except sqlite3.Error:
        return _cache_verdict(_FRAZEOLOHICHNYI_FTS_AVAILABLE, key, False)

    if exists:
        try:
            row = conn.execute("SELECT COUNT(*) FROM frazeolohichnyi_fts_docsize").fetchone()
            if row and row[0] == 0:
                if _is_connection_readonly(conn):
                    if not _FRAZEOLOHICHNYI_FTS_WARN_LOGGED:
                        print("Warning: frazeolohichnyi_fts table is missing and connection is read-only. Falling back to LIKE.", file=sys.stderr)
                        _FRAZEOLOHICHNYI_FTS_WARN_LOGGED = True
                    return False

                conn.execute(
                    "INSERT INTO frazeolohichnyi_fts(rowid, word, definition) "
                    "SELECT id, word, definition FROM frazeolohichnyi"
                )
            return _cache_verdict(_FRAZEOLOHICHNYI_FTS_AVAILABLE, key, True)
        except sqlite3.Error as e:
            if not _FRAZEOLOHICHNYI_FTS_WARN_LOGGED:
                print(f"Warning: Failed to verify/populate frazeolohichnyi_fts ({e}). Falling back to LIKE.", file=sys.stderr)
                _FRAZEOLOHICHNYI_FTS_WARN_LOGGED = True
            return False

    if _is_connection_readonly(conn):
        if not _FRAZEOLOHICHNYI_FTS_WARN_LOGGED:
            print("Warning: frazeolohichnyi_fts table is missing and connection is read-only. Falling back to LIKE.", file=sys.stderr)
            _FRAZEOLOHICHNYI_FTS_WARN_LOGGED = True
        return _cache_verdict(_FRAZEOLOHICHNYI_FTS_AVAILABLE, key, False)

    try:
        conn.execute(
            "CREATE VIRTUAL TABLE IF NOT EXISTS frazeolohichnyi_fts USING fts5("
            "word, definition, content='frazeolohichnyi', content_rowid='id', tokenize='trigram'"
            ")"
        )
        conn.execute(
            "INSERT INTO frazeolohichnyi_fts(rowid, word, definition) "
            "SELECT id, word, definition FROM frazeolohichnyi"
        )
        return _cache_verdict(_FRAZEOLOHICHNYI_FTS_AVAILABLE, key, True)
    except sqlite3.Error as e:
        if not _FRAZEOLOHICHNYI_FTS_WARN_LOGGED:
            print(f"Warning: Failed to create/populate frazeolohichnyi_fts ({e}). Falling back to LIKE.", file=sys.stderr)
            _FRAZEOLOHICHNYI_FTS_WARN_LOGGED = True
        return _cache_verdict(_FRAZEOLOHICHNYI_FTS_AVAILABLE, key, False)


_UKRAJINET_INDEX_AVAILABLE: dict[str, bool] = {}
_UKRAJINET_INDEX_WARN_LOGGED = False

def _populate_ukrajinet_word_index(conn: sqlite3.Connection) -> None:
    cursor = conn.execute("SELECT id, words FROM ukrajinet")
    inserts = []
    for rowid, words_json in cursor:
        try:
            words = json.loads(words_json or "[]")
        except (TypeError, ValueError):
            continue
        for candidate in words:
            normalized = _normalise_synonym(candidate)
            tokens = re.findall(rf"[{_CYRILLIC_WORD_CHARS}]+", normalized)
            for token in tokens:
                inserts.append((token, rowid))

    if inserts:
        conn.executemany(
            "INSERT INTO ukrajinet_word_index (word_key, rowid) VALUES (?, ?)",
            inserts
        )

def _ensure_ukrajinet_word_index(conn: sqlite3.Connection) -> bool:
    global _UKRAJINET_INDEX_WARN_LOGGED
    key = _db_cache_key(conn)
    cached = _UKRAJINET_INDEX_AVAILABLE.get(key)
    if cached is not None:
        return cached

    try:
        cur = conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='ukrajinet'")
        if not cur.fetchone():
            return _cache_verdict(_UKRAJINET_INDEX_AVAILABLE, key, False)
    except sqlite3.Error:
        return _cache_verdict(_UKRAJINET_INDEX_AVAILABLE, key, False)

    try:
        cur = conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='ukrajinet_word_index'")
        exists = cur.fetchone() is not None
    except sqlite3.Error:
        return _cache_verdict(_UKRAJINET_INDEX_AVAILABLE, key, False)

    if exists:
        try:
            row = conn.execute("SELECT COUNT(*) FROM ukrajinet_word_index").fetchone()
            if row and row[0] == 0:
                if _is_connection_readonly(conn):
                    if not _UKRAJINET_INDEX_WARN_LOGGED:
                        print("Warning: ukrajinet_word_index table is missing and connection is read-only. Falling back to LIKE.", file=sys.stderr)
                        _UKRAJINET_INDEX_WARN_LOGGED = True
                    return False

                _populate_ukrajinet_word_index(conn)
            return _cache_verdict(_UKRAJINET_INDEX_AVAILABLE, key, True)
        except sqlite3.Error as e:
            if not _UKRAJINET_INDEX_WARN_LOGGED:
                print(f"Warning: Failed to verify/populate ukrajinet_word_index ({e}). Falling back to LIKE.", file=sys.stderr)
                _UKRAJINET_INDEX_WARN_LOGGED = True
            return False

    if _is_connection_readonly(conn):
        if not _UKRAJINET_INDEX_WARN_LOGGED:
            print("Warning: ukrajinet_word_index table is missing and connection is read-only. Falling back to LIKE.", file=sys.stderr)
            _UKRAJINET_INDEX_WARN_LOGGED = True
        return _cache_verdict(_UKRAJINET_INDEX_AVAILABLE, key, False)

    try:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS ukrajinet_word_index ("
            "word_key TEXT, rowid INTEGER"
            ")"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_ukrajinet_word_index_key ON ukrajinet_word_index(word_key)"
        )
        _populate_ukrajinet_word_index(conn)
        return _cache_verdict(_UKRAJINET_INDEX_AVAILABLE, key, True)
    except sqlite3.Error as e:
        if not _UKRAJINET_INDEX_WARN_LOGGED:
            print(f"Warning: Failed to create/populate ukrajinet_word_index ({e}). Falling back to LIKE.", file=sys.stderr)
            _UKRAJINET_INDEX_WARN_LOGGED = True
        return _cache_verdict(_UKRAJINET_INDEX_AVAILABLE, key, False)


def _idioms_frazeolohichnyi(conn: sqlite3.Connection, lemma: str, *, limit: int = 3) -> dict[str, Any] | None:
    """Phraseology rows from local DB, matched on the idiom phrase not loose definition mentions."""
    variants = [_lookup_key(variant) for variant in _split_lemma_variants(_base_lemma(lemma))]
    variants = [variant for variant in variants if variant]
    if not variants:
        return None

    rows: list[tuple[str, str, str]] = []
    seen_ids: set[int] = set()
    try:
        for variant in variants:
            use_fts = len(variant) >= 3 and _ensure_frazeolohichnyi_fts(conn)
            cursor = None
            if use_fts:
                try:
                    # The FTS subquery only NARROWS the scanned rows; the
                    # original lower()+LIKE predicate stays in SQL so the
                    # emitted row set — including the LIMIT-80 cutoff — is
                    # identical to the fallback by construction (trigram
                    # folds Cyrillic case, SQLite lower() does not; codex
                    # review of #4514, finding 1).
                    query_val = '"' + variant.replace('"', '""') + '"'
                    cursor = conn.execute(
                        "SELECT id, word, definition, source FROM frazeolohichnyi "
                        "WHERE id IN ("
                        "  SELECT rowid FROM frazeolohichnyi_fts WHERE frazeolohichnyi_fts MATCH ?"
                        ") AND (lower(word) LIKE ? OR lower(definition) LIKE ?) "
                        "ORDER BY id LIMIT 80",
                        (query_val, f"%{variant}%", f"%{variant}%"),
                    )
                except sqlite3.Error:
                    cursor = None

            if cursor is None:
                cursor = conn.execute(
                    "SELECT id, word, definition, source FROM frazeolohichnyi "
                    "WHERE lower(word) LIKE ? OR lower(definition) LIKE ? LIMIT 80",
                    (f"%{variant}%", f"%{variant}%"),
                )

            for row in cursor:
                row_id = int(row[0])
                if row_id in seen_ids:
                    continue
                seen_ids.add(row_id)
                rows.append((str(row[1] or ""), str(row[2] or ""), str(row[3] or "")))
    except sqlite3.OperationalError as exc:
        if _missing_table(exc):
            return None
        raise

    items: list[dict[str, str]] = []
    seen_phrases: set[str] = set()
    for headword, definition, source in rows:
        phrase = _leading_phraseology_phrase(definition, headword)
        if not phrase or not _phrase_contains_lemma(phrase, lemma):
            continue
        phrase = _truncate_text(phrase, 160)
        key = _lookup_key(phrase)
        if key in seen_phrases:
            continue
        seen_phrases.add(key)
        items.append(
            {
                "text": phrase,
                "phrase": phrase,
                "definition": _phraseology_definition_body(definition, phrase),
                "source": source or "Фразеологічний словник української мови",
                "source_url": "",
            }
        )
        if len(items) >= limit:
            break

    if not items:
        return None
    return {
        "items": items,
        "source": "Фразеологічний словник української мови",
        "source_urls": [],
    }


def _merge_idiom_sections(*sections: dict[str, Any] | None) -> dict[str, Any] | None:
    items: list[dict[str, str]] = []
    sources: list[str] = []
    urls: list[str] = []
    seen: set[str] = set()
    for section in sections:
        if not section:
            continue
        for item in section.get("items", []):
            if not isinstance(item, dict):
                continue
            phrase = str(item.get("phrase") or item.get("text") or "").strip()
            key = _lookup_key(phrase)
            if not phrase or key in seen:
                continue
            seen.add(key)
            items.append(item)
        if section.get("source"):
            sources.append(str(section["source"]))
        urls.extend(str(url) for url in section.get("source_urls", []) if url)
    if not items:
        return None
    return {
        "items": items[:4],
        "source": " + ".join(dict.fromkeys(sources)),
        "source_urls": list(dict.fromkeys(urls)),
    }


def _idioms(
    conn: sqlite3.Connection,
    lemma: str,
    cache: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    return _merge_idiom_sections(
        _idioms_slovnyk(lemma, cache),
        _idioms_frazeolohichnyi(conn, lemma),
    )


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


_HERITAGE_PAIRS_CACHE = None


def _get_heritage_pairs_rationale_uk() -> dict[str, str]:
    global _HERITAGE_PAIRS_CACHE
    if _HERITAGE_PAIRS_CACHE is not None:
        return _HERITAGE_PAIRS_CACHE
    import yaml
    path = ROOT / "data" / "lexicon" / "heritage_pairs.yaml"
    _HERITAGE_PAIRS_CACHE = {}
    if path.exists():
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            pairs = data.get("pairs", [])
            for p in pairs:
                label = p.get("calqueLabel")
                rat_uk = p.get("rationaleUk")
                if label and rat_uk:
                    _HERITAGE_PAIRS_CACHE[label] = rat_uk
        except Exception as e:
            print(f"WARN: Failed to load heritage_pairs.yaml for rationaleUk: {e}", file=sys.stderr)
    return _HERITAGE_PAIRS_CACHE


def _curated_calque(lemma: str, base: str) -> dict[str, Any] | None:
    """Curated §6 calque card from exact dataset lookups only."""
    rationale_uk_map = _get_heritage_pairs_rationale_uk()
    for key in (lemma, base):
        if key in CURATED_CALQUES:
            row = CURATED_CALQUES[key]
            res = {
                "kind": str(row.get("kind", "participle")),
                "corrections": list(row["corrections"]),
                "note": str(row["note"]),
                "source": list(row["source"]),
                "evidence": list(row.get("evidence", [])),
                "heritage_guard": str(row.get("heritage_guard", "")),
            }
            rat_uk = rationale_uk_map.get(key)
            if rat_uk:
                res["noteUk"] = rat_uk
            return res

    for key in (lemma, base):
        if key in SENSE_RESTRICTED_CALQUES:
            row = SENSE_RESTRICTED_CALQUES[key]
            res = {
                "kind": "sense_restricted",
                "corrections": list(row["corrections"]),
                "calque_sense": str(row["calque_sense"]),
                "authentic_sense": str(row["authentic_sense"]),
                "note": str(row["note"]),
                "source": list(row["source"]),
                "evidence": list(row.get("evidence", [])),
                "heritage_guard": str(row.get("heritage_guard", "")),
            }
            rat_uk = rationale_uk_map.get(key)
            if rat_uk:
                res["noteUk"] = rat_uk
            return res

    if lemma in PHRASAL_CALQUES:
        row = PHRASAL_CALQUES[lemma]
        res = {
            "kind": "phrasal",
            "corrections": list(row["corrections"]),
            "note": str(row["note"]),
            "source": list(row["source"]),
            "evidence": list(row.get("evidence", [])),
            "heritage_guard": str(row.get("heritage_guard", "")),
        }
        rat_uk = rationale_uk_map.get(lemma)
        if rat_uk:
            res["noteUk"] = rat_uk
        return res

    return None


def _reverse_calques(lemma: str, base: str) -> list[dict[str, Any]] | None:
    """Find calques where this lemma is the recommended correction."""
    results: list[dict[str, Any]] = []
    rationale_uk_map = _get_heritage_pairs_rationale_uk()

    for calque_dict in (CURATED_CALQUES, SENSE_RESTRICTED_CALQUES, PHRASAL_CALQUES):
        for calque, row in calque_dict.items():
            corrections = row.get("corrections", [])
            if lemma in corrections or base in corrections:
                kind = row.get("kind", "participle")
                if calque_dict is SENSE_RESTRICTED_CALQUES:
                    kind = "sense_restricted"
                elif calque_dict is PHRASAL_CALQUES:
                    kind = "phrasal"

                result = {
                    "calque": calque,
                    "kind": str(kind),
                    "note": str(row.get("note", "")),
                    "source": list(row.get("source", [])),
                }
                if "calque_sense" in row:
                    result["calque_sense"] = str(row["calque_sense"])

                rat_uk = rationale_uk_map.get(calque)
                if rat_uk:
                    result["noteUk"] = rat_uk

                results.append(result)

    return results if results else None


def _entry_scoped_heritage_status(status: dict[str, Any]) -> dict[str, Any]:
    clean_status = dict(status)
    clean_status.pop("sovietization_risk", None)
    return clean_status


def _vesum_attested_from_morphology(morphology: dict[str, Any] | None) -> bool:
    if not isinstance(morphology, dict):
        return False
    return str(morphology.get("source") or "").upper() == "VESUM" and int(morphology.get("form_count") or 0) > 0


def _max_definition_sovietization_risk(cards: list[dict[str, Any]]) -> int:
    risks = [int(card.get("sovietization_risk") or 0) for card in cards if isinstance(card, dict)]
    return max(risks, default=0)


def _finalize_heritage_status(
    status: dict[str, Any],
    *,
    morphology: dict[str, Any] | None,
    definition_cards: list[dict[str, Any]],
) -> dict[str, Any]:
    finalized = dict(status)
    vesum_attested = bool(finalized.get("vesum_attested")) or _vesum_attested_from_morphology(morphology)
    max_sovietization_risk = _max_definition_sovietization_risk(definition_cards)
    finalized["vesum_attested"] = vesum_attested
    finalized["warning_severity"] = compute_warning_severity(
        finalized,
        vesum_attested=vesum_attested,
        max_sovietization_risk=max_sovietization_risk,
    )
    return finalized


def _is_slovnyk_warning_candidate(entry: dict[str, Any], status: dict[str, Any]) -> bool:
    return bool(
        entry.get("primary_source") == "surzhyk_to_avoid"
        or status.get("is_russianism")
        or str(status.get("classification") or "") in _WARNING_CLASSIFICATIONS
    )


def _morphology(lemma: str) -> dict | None:
    """Full VESUM paradigm for a single-token lemma, decoded and de-duplicated.

    Style/register-marked forms (нестягнені, застарілі, розмовні … — any tag token
    in ``_STYLE_MARKER_LABELS``) are partitioned into ``marked_forms`` so they never
    render inline with the modern paradigm (#4891). The main ``forms``, ``form_count``
    and ``paradigm`` describe the modern (unmarked) paradigm only; ``marked_forms``
    carries ``{form, label, marker, marker_label, stress?}`` rows with the Ukrainian
    style label, and ``marked_form_count`` its post-cap length. Both keys are omitted
    when the lemma has no marked forms, so unmarked lemmas are unaffected.
    """
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
    seen_marked: set[tuple[str, str, str]] = set()
    decoded: list[dict[str, str]] = []
    marked: list[dict[str, str]] = []
    for row in forms:
        form = row.get("word_form") or ""
        if not form:
            continue
        raw_tag = row.get("tags") or ""
        label = _decode_tag(raw_tag)
        markers = _style_markers_in_tag(raw_tag)
        if markers:
            marker = markers[0]
            marked_key = (form, label, marker)
            if marked_key in seen_marked:
                continue
            seen_marked.add(marked_key)
            marked_row = {
                "form": form,
                "label": label,
                "marker": marker,
                "marker_label": _STYLE_MARKER_LABELS.get(marker, _GENERIC_STYLE_MARKER_LABEL),
            }
            stressed_form = _stress_display_form(form)
            if stressed_form:
                marked_row["stress"] = stressed_form
            marked.append(marked_row)
            continue
        key = (form, label)
        if key in seen:
            continue
        seen.add(key)
        decoded_row = {"form": form, "label": label}
        stressed_form = _stress_display_form(form)
        if stressed_form:
            decoded_row["stress"] = stressed_form
        decoded.append(decoded_row)
    if not decoded and not marked:
        return None
    forms_out = decoded[:_MORPHOLOGY_FORM_CAP]
    morphology = {
        "pos": _POS_LABELS.get(pos_raw, pos_raw),
        "form_count": len(forms_out),
        "forms": forms_out,
        "source": "VESUM",
    }
    paradigm = _build_paradigm(pos_raw, decoded)
    if paradigm:
        morphology["paradigm"] = paradigm
    stressed_forms = {
        row["form"]: row["stress"] for row in decoded if row.get("stress") and row.get("form") != row.get("stress")
    }
    if paradigm:
        for form in _collect_string_values(paradigm):
            stressed_form = _stress_display_form(form)
            if stressed_form and stressed_form != form:
                stressed_forms[form] = stressed_form
    if stressed_forms:
        morphology["stress"] = {"source": _STRESS_SOURCE, "forms": stressed_forms}
    if marked:
        marked_out = marked[:_MORPHOLOGY_FORM_CAP]
        morphology["marked_forms"] = marked_out
        morphology["marked_form_count"] = len(marked_out)
    return morphology


# Foreign-script (kana / CJK / hangul) detector. Вікісловник occasionally leaks a
# "запис кирилицею <foreign word>" transliteration note that is pure noise for a
# Ukrainian learner-facing meaning — drop any definition that contains such glyphs.
_NON_UKRAINIAN_SCRIPT_RE = re.compile(r"[぀-ヿ㐀-鿿가-힯]")


def _clean_wiki_def(raw: str) -> str:
    """Strip Вікісловник wiki-markup noise (templates, quote leaks, refs)."""
    text = _unescape_html_entities(raw)
    text = re.sub(r"<br\s*/?>", " ", text, flags=re.IGNORECASE)
    # [\s\S] (not .) so multi-line comments are stripped too — `.` stops at the
    # first newline, leaking the rest of a multi-line comment (CodeQL
    # py/bad-tag-filter). Input is trusted Вікісловник DB text, but match fully.
    text = re.sub(r"<!--[\s\S]*?-->", "", text)
    # Strip residual HTML/XML tags (<ref>, <span title=…>, </text>) that leak from
    # Вікісловник wikitext — the [|{}\[] split below does NOT cut on `<`, so these
    # survived into learner-facing meanings (#2882 spot-check garbage).
    text = re.sub(r"<[^>]*>", " ", text)
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
        # Reject residual tag fragments (lone `<`/`>` after stripping) and
        # foreign-script transliteration noise — better an empty meaning than garbage.
        if "<" in cleaned or ">" in cleaned:
            continue
        if _NON_UKRAINIAN_SCRIPT_RE.search(cleaned):
            continue
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
    text = text.strip(' \t\r\n.,;:!?()[]{}«»"“”')
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
    use_idx = _ensure_ukrajinet_word_index(conn)
    for variant in _split_lemma_variants(lemma):
        needle = variant.casefold()
        indexed = False
        cursor = None
        if use_idx:
            # Derive the lookup token with the SAME normalizer the index was
            # built with, so build-time and lookup-time keys can never drift.
            tokens = re.findall(rf"[{_CYRILLIC_WORD_CHARS}]+", _normalise_synonym(variant))
            if tokens:
                try:
                    cursor = conn.execute(
                        "SELECT words FROM ukrajinet WHERE rowid IN ("
                        "  SELECT rowid FROM ukrajinet_word_index WHERE word_key = ?"
                        ")",
                        (tokens[0],),
                    )
                    indexed = True
                except sqlite3.Error:
                    cursor = None
                    indexed = False

        if cursor is None:
            cursor = conn.execute(
                "SELECT words FROM ukrajinet WHERE lower(words) LIKE ?",
                (f"%{needle}%",),
            )

        rows = cursor.fetchall()
        for (words_json,) in rows:
            raw_text = str(words_json or "")
            # Parity guard: the index folds Cyrillic case (casefold at build
            # time) but SQLite's lower()+LIKE does not, so the indexed path
            # can surface rows the fallback never matched. Re-apply the exact
            # LIKE predicate so both paths emit identical sets.
            if indexed and not _ascii_lower_contains(raw_text, needle):
                continue
            try:
                words = [str(w).strip() for w in json.loads(words_json or "[]")]
            except (TypeError, ValueError):
                continue
            if not any(_contains_whole_token(_normalise_synonym(word), needle) for word in words):
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
    # СУМ-11 synonym verification removed — decolonization decision 2026-06-26.
    # We do not read the Soviet-era dictionary for any purpose.
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
    kaikki_lookup: dict[str, dict[str, Any]] | None = None,
) -> dict | None:
    """Modern Ukrainian meaning: Вікісловник (clean, + synonyms) → kaikki fallback.

    СУМ-11 (the Soviet-era dictionary, 1970-80) is intentionally NEVER used as a
    source — decolonization decision 2026-06-26. Грінченко is likewise NOT used
    here — its 1907 glosses are Russian and must not surface in rendered Atlas
    pages. After Вікісловник, fall through to kaikki only.
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
    return _kaikki_meaning(kaikki_lookup or {}, lemma)


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
        # Inflected-form entry (e.g. моєму) → resolve to its base lemma (мій) and
        # fetch the base's clean СУМ-20 definition. Closes the coverage gap, zero Soviet.
        base = _vesum_base_lemma(lemma)
        if base and _sum20_in_coverage(base):
            row = _slovnyk_base_row(base, "newsum")
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


def _vts_definition_card(
    lemma: str,
    cache: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Великий тлумачний словник (VTS) — a modern, Ukrainian-only explanatory
    dictionary on slovnyk.me, fetched live (cached per lookup word). Shown as the
    top definition card, with СУМ-20 below. Non-Soviet replacement for the removed
    СУМ-11 source (decolonization decision 2026-06-26). For inflected-form entries it
    falls back to the base lemma's entry via _slovnyk_base_row."""
    lookup_word = _slovnyk_lookup_word(lemma)
    if not lookup_word:
        return None
    cached_present = isinstance(cache, dict) and "vts" in (cache.get("lookups") or {})
    row = _cache_lookup(cache, "vts") if cache is not None else None
    if not row and not cached_present:
        transient = False
        try:
            row = _fetch_slovnyk_entry(lemma, lookup_word, "vts")
        except _SlovnykTransientError:
            transient = True
            row = None
        if cache is not None and not transient:
            _cache_store_lookup(lemma, cache, "vts", row)
    if not row:
        # Inflected-form entry → fetch the VTS definition of its base lemma.
        base = _vesum_base_lemma(lemma)
        if base:
            row = _slovnyk_base_row(base, "vts")
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
        "id": "vts",
        "source": "ВТС",
        "source_pill": "ВТС",
        "note": "Великий тлумачний словник сучасної української мови",
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
    # СУМ-11 (Soviet-era dictionary) is intentionally excluded — decolonization
    # decision 2026-06-26. Show clean modern Ukrainian dictionaries: VTS (Великий
    # тлумачний словник) on top, СУМ-20 below — both when available. Inflected-form
    # entries resolve to their base lemma inside each builder.
    vts = _vts_definition_card(lemma, cache)
    sum20 = _sum20_definition_card(lemma, cache)
    return [card for card in (vts, sum20) if card]


def _lookup_key(value: str) -> str:
    """Match Goroh headwords without stress marks or apostrophe variants."""
    normalized = unicodedata.normalize("NFKD", clean_html_entities(str(value or "")))
    normalized = _STRESS_MARK_RE.sub("", normalized)
    normalized = unicodedata.normalize("NFC", normalized)
    normalized = normalized.replace("`", "'").replace("’", "'").replace("ʼ", "'")
    return re.sub(r"\s+", " ", normalized).strip().casefold()


def _etymology_lookup_variants(lemma: str) -> list[str]:
    variants = [lemma.strip(), _lookup_key(lemma)]
    variants.extend(_split_lemma_variants(lemma))
    for variant in list(variants):
        key = _lookup_key(variant)
        if not key or _has_whitespace(key):
            continue
        variants.extend(get_apostrophe_variants(key))
        if key.startswith("в") and len(key) > 2:
            variants.append("у" + key[1:])
        if key.startswith("у") and len(key) > 2:
            variants.append("в" + key[1:])
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
    candidates.extend(_DERIVATIONAL_ETYMOLOGY_BASES.get(key, ()))
    candidates.extend(_ORDINAL_ETYMOLOGY_BASES.get(key, ()))

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
        "text": clean_html_entities(trim_curated_goroh_text(row[0].strip()[:600], lemma)),
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
        for variant in _etymology_lookup_variants(word):
            row = conn.execute(
                "SELECT etymology_text, vol, page FROM esum_etymology WHERE lemma = ? AND etymology_text != '' LIMIT 1",
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
    text = clean_html_entities(row[0].strip()[:600])
    if garbled_esum_entry(word):
        text = clean_html_entities(strip_garbled_tail(text, word))
        cite += " (garbled tail stripped)"
    if has_mojibake_marker(text):
        return None
    if not text:
        return None
    return {"text": text, "source": cite}


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


def _ipa_stressed_syllable_index(ipa: str) -> int | None:
    primary = _IPA_PRIMARY_STRESS_RE.search(ipa)
    if not primary:
        return None
    before_stress = _IPA_STRESS_RE.sub("", ipa[: primary.start()])
    cleaned = _IPA_NON_SYLLABIC_MARK_RE.sub("", before_stress)
    return len(_IPA_VOWEL_RE.findall(cleaned))


def _stress_lemma_vowel(lemma: str, stressed_syllable_index: int) -> str:
    clean = _strip_stress(lemma).strip()
    if not clean or _has_whitespace(clean) or not _UKRAINIAN_WORD_RE.fullmatch(clean):
        return ""
    vowel_positions = [index for index, char in enumerate(clean) if char in _UKRAINIAN_VOWELS]
    if not vowel_positions or stressed_syllable_index >= len(vowel_positions):
        return ""
    position = vowel_positions[stressed_syllable_index]
    return clean[: position + 1] + "\u0301" + clean[position + 1 :]


def _kaikki_stress(lookup: dict[str, dict[str, Any]], lemma: str) -> dict[str, str] | None:
    row = _kaikki_row(lookup, lemma)
    if not row:
        return None
    ipa_values = row.get("ipa")
    if not isinstance(ipa_values, list):
        return None
    clean = _strip_stress(lemma).strip()
    vowel_count = _count_vowels(clean)
    if vowel_count < 1:
        return None
    for value in ipa_values:
        ipa = clean_html_entities(str(value or "")).strip()
        if not ipa:
            continue
        ipa_without_stress = _IPA_STRESS_RE.sub("", _IPA_NON_SYLLABIC_MARK_RE.sub("", ipa))
        ipa_vowel_count = len(_IPA_VOWEL_RE.findall(ipa_without_stress))
        if ipa_vowel_count != vowel_count:
            continue
        stressed_syllable_index = _ipa_stressed_syllable_index(ipa)
        if stressed_syllable_index is None and vowel_count == 1:
            stressed_syllable_index = 0
        if stressed_syllable_index is None:
            continue
        form = _stress_lemma_vowel(clean, stressed_syllable_index)
        if form and _strip_stress(form).casefold() == clean.casefold():
            return {"form": form, "source": KAIKKI_SOURCE, "ipa": ipa}
    return None


def _kaikki_meaning(lookup: dict[str, dict[str, Any]], lemma: str) -> dict[str, object] | None:
    row = _kaikki_row(lookup, lemma)
    if not row:
        return None
    glosses = row.get("glosses")
    if not isinstance(glosses, list):
        return None
    definitions: list[str] = []
    seen: set[str] = set()
    for gloss in glosses:
        text = re.sub(r"\s+", " ", clean_html_entities(str(gloss or "")).strip())
        if not text:
            continue
        key = text.casefold()
        if key in seen:
            continue
        seen.add(key)
        definitions.append(_truncate_text(text, 600))
    if not definitions:
        return None
    return {
        "definitions": definitions[:6],
        "source": KAIKKI_SOURCE,
        "note": "English Wiktionary gloss fallback; direct per-lemma row.",
    }


def _kaikki_etymology_text_is_usable(text: str) -> bool:
    if not text:
        return False
    return not _KAIKKI_GARBLED_ETYMOLOGY_RE.search(text)


def _kaikki_etymology(lookup: dict[str, dict[str, Any]], lemma: str) -> dict | None:
    row = _kaikki_row(lookup, lemma)
    if not row:
        return None
    text = clean_html_entities(str(row.get("etymology_text") or "").strip()[:600])
    if not _kaikki_etymology_text_is_usable(text):
        return None
    return {"text": text, "source": KAIKKI_SOURCE}


def _kaikki_translation(lookup: dict[str, dict[str, Any]], lemma: str) -> dict[str, object] | None:
    """English translation glosses from Wiktionary/kaikki (§11 fallback after dmklinger).

    Form-of / misspelling / spelling-variant meta-glosses are already dropped at
    build time (`build_kaikki_lookup.extract_glosses`), so these are real translations.
    """
    row = _kaikki_row(lookup, lemma)
    if not row:
        return None
    glosses = row.get("glosses")
    if not isinstance(glosses, list):
        return None
    english: list[str] = []
    seen: set[str] = set()
    for gloss in glosses:
        text = clean_html_entities(str(gloss or "")).strip()
        if not text:
            continue
        key = text.casefold()
        if key not in seen:
            seen.add(key)
            english.append(text)
    if not english:
        return None
    return {"en": english[:6], "source": KAIKKI_SOURCE}


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


def _etymology(
    conn: sqlite3.Connection, lemma: str, kaikki_lookup: dict[str, dict[str, Any]] | None = None
) -> dict | None:
    """Cached etymology by direct per-lemma authority order."""
    lookup_word = _lookup_key(_base_lemma(lemma))
    if lookup_word in _COMPOSITIONAL_ETYMOLOGY_EXCLUSIONS:
        return None
    return _source_etymology(conn, lemma, kaikki_lookup)


_GRAC_FREQUENCY_CACHE_DATA: dict[str, Any] | None = None
_GRAC_FREQUENCY_CACHE_DIRTY = False
_CEFR_ESTIMATE_LEVEL_BY_KEY: dict[str, dict[str, Any]] = {}


def _puls_cefr(conn: sqlite3.Connection, lemma: str) -> dict[str, str] | None:
    for variant in _split_lemma_variants(lemma):
        try:
            row = conn.execute(
                "SELECT level, pos, text FROM puls_cefr WHERE word = ? COLLATE NOCASE AND level != '' LIMIT 1",
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


def _load_grac_frequency_cache(path: Path | None = None) -> dict[str, Any]:
    global _GRAC_FREQUENCY_CACHE_DATA
    path = path or GRAC_FREQUENCY_CACHE
    if _GRAC_FREQUENCY_CACHE_DATA is not None:
        return _GRAC_FREQUENCY_CACHE_DATA
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        data = {}
    _GRAC_FREQUENCY_CACHE_DATA = data if isinstance(data, dict) else {}
    return _GRAC_FREQUENCY_CACHE_DATA


def _write_grac_frequency_cache(path: Path | None = None) -> None:
    global _GRAC_FREQUENCY_CACHE_DIRTY
    path = path or GRAC_FREQUENCY_CACHE
    if not _GRAC_FREQUENCY_CACHE_DIRTY or _GRAC_FREQUENCY_CACHE_DATA is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(_GRAC_FREQUENCY_CACHE_DATA, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _GRAC_FREQUENCY_CACHE_DIRTY = False


def _grac_lookup_key(lemma: str) -> str:
    return _strip_stress(_base_lemma(lemma)).strip()


def _grac_word_candidates(word: str) -> list[str]:
    candidates: list[str] = []
    for variant in get_apostrophe_variants(word):
        candidates.append(variant)
        candidates.append(variant.casefold())
    seen: set[str] = set()
    return [c for c in candidates if c and not (c in seen or seen.add(c))]


def _fetch_grac_frequency_batch(words: list[str]) -> dict[str, dict[str, Any] | None]:
    if _phase1_offline_mode():
        return {word: None for word in words}

    candidates_by_word = {word: _grac_word_candidates(word) for word in words}
    candidate_to_words: dict[str, list[str]] = {}
    for word, candidates in candidates_by_word.items():
        for candidate in candidates:
            candidate_to_words.setdefault(candidate, []).append(word)
    if not candidate_to_words:
        return {word: None for word in words}

    pattern = "^(?:" + "|".join(re.escape(candidate) for candidate in candidate_to_words) + ")$"
    try:
        response = requests.get(
            _GRAC_WORDLIST_URL,
            params={
                "corpname": _GRAC_CORPUS,
                "wlattr": "word",
                "wlpat": pattern,
                "wlminfreq": 1,
                "wlmaxitems": max(10, len(candidate_to_words) + 10),
                "format": "json",
            },
            headers={"User-Agent": _SLOVNYK_USER_AGENT},
            timeout=30,
        )
        response.raise_for_status()
        items = response.json().get("Items", [])
    except (requests.RequestException, ValueError):
        return {word: None for word in words}

    best_by_word: dict[str, dict[str, Any] | None] = {word: None for word in words}
    for item in items:
        form = str(item.get("str") or "")
        freq = int(item.get("frq") or 0)
        rel_freq = float(item.get("relfreq") or 0.0)
        for word in candidate_to_words.get(form, []):
            current = best_by_word[word]
            if not current or rel_freq > float(current.get("rel_freq") or 0.0):
                best_by_word[word] = {"word": form, "freq": freq, "rel_freq": rel_freq}
    return best_by_word


def _ensure_grac_frequency_cache(words: list[str]) -> None:
    global _GRAC_FREQUENCY_CACHE_DIRTY
    cache = _load_grac_frequency_cache()
    missing = [word for word in words if word not in cache]
    if _phase1_offline_mode():
        return

    for start in range(0, len(missing), _GRAC_BATCH_SIZE):
        batch = missing[start : start + _GRAC_BATCH_SIZE]
        results = _fetch_grac_frequency_batch(batch)
        for word in batch:
            cache[word] = results.get(word)
        _GRAC_FREQUENCY_CACHE_DIRTY = True
        _write_grac_frequency_cache()


def _prepare_cefr_estimates(conn: sqlite3.Connection, manifest: dict[str, Any]) -> None:
    """Prepare labelled CEFR estimates from GRAC frequency for non-PULS lemmas.

    Mapping rationale: estimates use GRAC relative-frequency quantiles within the
    current Atlas lemmas that lack PULS. Top 20% -> A1, then A2/B1/B2, and the
    lowest positive-frequency 20% -> C1. This keeps very common words out of
    advanced bands without pretending the estimate is authoritative.
    """
    _CEFR_ESTIMATE_LEVEL_BY_KEY.clear()
    words: list[str] = []
    for entry in manifest.get("entries", []):
        lemma = str(entry.get("lemma") or "")
        word = _grac_lookup_key(lemma)
        if not word or _has_whitespace(word) or not _UKRAINIAN_WORD_RE.fullmatch(word):
            continue
        if _puls_cefr(conn, lemma):
            continue
        words.append(word)

    unique_words = sorted(set(words), key=str.casefold)
    _ensure_grac_frequency_cache(unique_words)
    cache = _load_grac_frequency_cache()
    scored: list[tuple[str, float, int, str]] = []
    for word in unique_words:
        row = cache.get(word)
        if not isinstance(row, dict):
            continue
        rel_freq = float(row.get("rel_freq") or 0.0)
        freq = int(row.get("freq") or 0)
        if rel_freq <= 0.0 or freq <= 0:
            continue
        scored.append((word, rel_freq, freq, str(row.get("word") or word)))

    scored.sort(key=lambda item: (-item[1], item[0].casefold()))
    total = len(scored)
    if not total:
        return
    bands = ("A1", "A2", "B1", "B2", "C1")
    for index, (word, rel_freq, freq, grac_word) in enumerate(scored):
        band_index = min(4, int(index * len(bands) / total))
        _CEFR_ESTIMATE_LEVEL_BY_KEY[word] = {
            "level": bands[band_index],
            "rel_freq": rel_freq,
            "freq": freq,
            "grac_word": grac_word,
            "rank": index + 1,
            "total": total,
        }


def _estimated_cefr(lemma: str) -> dict[str, str] | None:
    word = _grac_lookup_key(lemma)
    estimate = _CEFR_ESTIMATE_LEVEL_BY_KEY.get(word)
    if not estimate:
        return None
    level = str(estimate["level"])
    rel_freq = float(estimate["rel_freq"])
    rank = int(estimate["rank"])
    total = int(estimate["total"])
    return {
        "level": level,
        "source": _CEFR_ESTIMATED_SOURCE,
        "text": f"{level} (орієнтовно / estimated; GRAC {rel_freq:.2f}/million, rank {rank}/{total})",
    }


def _cefr(conn: sqlite3.Connection, lemma: str) -> dict[str, str] | None:
    return _puls_cefr(conn, lemma) or _estimated_cefr(lemma)


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
        text = _clean_translation_gloss(text)
        if text:
            out.append(text)
    return out


_BALLA_REVERSE_INDEX: dict[int, dict[str, list[tuple[str, str | None]]]] = {}


def _balla_reverse_headword(word: object) -> str | None:
    headword = re.sub(r"\s+", " ", clean_html_entities(str(word or "")).strip()).casefold()
    if not headword or "~" in headword:
        return None
    if not _BALLA_REVERSE_HEADWORD_RE.fullmatch(headword):
        return None
    return headword


def _balla_reverse_definition_segments(definition: object) -> list[str]:
    text = clean_html_entities(str(definition or ""))
    text = re.sub(r"\([^)]*\)", " ", text)
    segments: list[str] = []
    for segment in re.split(r"\[m\d+\]|\d+\)|[;,]", text):
        cleaned = _BALLA_REVERSE_LEADING_LABEL_RE.sub("", segment).strip()
        if not cleaned or "—" in cleaned or "~" in cleaned or _LATIN_RE.search(cleaned):
            continue
        segments.append(cleaned)
    return segments


def _balla_reverse_candidate_keys(token: str) -> list[tuple[str, str | None]]:
    key = _lookup_key(token)
    if len(key) < 3 or key in _BALLA_REVERSE_STOP_TOKENS:
        return []
    analyses = _vesum_word_analyses(token)
    if not analyses:
        return [(key, None)]
    out: list[tuple[str, str | None]] = []
    seen: set[tuple[str, str | None]] = set()
    for lemma, pos in analyses:
        lemma_key = _lookup_key(lemma)
        if len(lemma_key) < 3 or lemma_key in _BALLA_REVERSE_STOP_TOKENS:
            continue
        item = (lemma_key, pos or None)
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out


def _load_balla_reverse_index(conn: sqlite3.Connection) -> dict[str, list[tuple[str, str | None]]]:
    cache_key = id(conn)
    cached = _BALLA_REVERSE_INDEX.get(cache_key)
    if cached is not None:
        return cached
    index: dict[str, list[tuple[str, str | None]]] = {}
    seen: set[tuple[str, str, str | None]] = set()
    try:
        rows = conn.execute("SELECT word, definition FROM balla_en_uk ORDER BY word").fetchall()
    except sqlite3.OperationalError as exc:
        if _missing_table(exc):
            _BALLA_REVERSE_INDEX[cache_key] = {}
            return {}
        raise
    for word, definition in rows:
        headword = _balla_reverse_headword(word)
        if not headword:
            continue
        for segment in _balla_reverse_definition_segments(definition):
            tokens = _BALLA_REVERSE_UKRAINIAN_TOKEN_RE.findall(segment)
            if len(tokens) != 1:
                continue
            for key, pos in _balla_reverse_candidate_keys(tokens[0]):
                seen_key = (key, headword, pos)
                if seen_key in seen:
                    continue
                seen.add(seen_key)
                index.setdefault(key, []).append((headword, pos))
    _BALLA_REVERSE_INDEX[cache_key] = index
    return index


def _balla_reverse_hint_keys(gloss_hints: object) -> set[str]:
    if not isinstance(gloss_hints, set | list | tuple):
        return set()
    out: set[str] = set()
    for hint in gloss_hints:
        for part in _BALLA_REVERSE_HINT_SPLIT_RE.split(str(hint or "")):
            cleaned = clean_html_entities(part).strip().casefold()
            cleaned = re.sub(r"^(?:to|a|an|the)\s+", "", cleaned)
            cleaned = re.sub(r"\s+", " ", cleaned)
            if _BALLA_REVERSE_HEADWORD_RE.fullmatch(cleaned):
                out.add(cleaned)
    return out


def _surface_gloss_hints(entry: dict[str, Any]) -> set[str]:
    hints: set[str] = set()
    if isinstance(entry.get("gloss"), str) and entry["gloss"].strip():
        hints.add(str(entry["gloss"]))
    normalizations = entry.get("atlas_normalizations")
    if not isinstance(normalizations, list):
        return hints
    for normalization in normalizations:
        if not isinstance(normalization, dict):
            continue
        reason = str(normalization.get("reason") or "")
        pos_match = _BALLA_REVERSE_SOURCE_POS_RE.search(reason)
        source_pos = pos_match.group(1).casefold() if pos_match else ""
        if source_pos.startswith("noun"):
            continue
        hints.update(match.group(1) for match in _BALLA_REVERSE_SURFACE_GLOSS_RE.finditer(reason))
    return hints


def _balla_reverse_translation(
    conn: sqlite3.Connection,
    lemma: str,
    *,
    entry_pos: object = None,
    gloss_hints: object = None,
) -> dict[str, object] | None:
    allowed_headwords = _balla_reverse_hint_keys(gloss_hints)
    if not allowed_headwords:
        return None
    target_pos = _MANIFEST_POS_TO_VESUM_POS.get(_lookup_key(str(entry_pos or "")))
    target_keys = {_lookup_key(variant) for variant in _split_lemma_variants(lemma)}
    target_keys = {key for key in target_keys if key}
    if not target_keys:
        return None

    index = _load_balla_reverse_index(conn)
    english: list[str] = []
    seen: set[str] = set()
    for key in sorted(target_keys):
        for headword, vesum_pos in index.get(key, []):
            if headword not in allowed_headwords:
                continue
            if target_pos and vesum_pos and vesum_pos != target_pos:
                continue
            if headword in seen:
                continue
            seen.add(headword)
            english.append(headword)
            if len(english) > _BALLA_REVERSE_MAX_HEADWORDS:
                return None
    if not english:
        return None
    return {
        "en": english,
        "source": _BALLA_REVERSE_SOURCE,
        "note": (
            "Reverse lookup from an exact Ukrainian token in Балла EN→UK, "
            "validated by the source learner gloss; skipped when ambiguous."
        ),
    }


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


_SLOVNYK_UKRENG_PREFIX_LABELS = {
    "ав",
    "анат",
    "архіт",
    "астр",
    "біол",
    "бот",
    "військ",
    "геогр",
    "геол",
    "гірн",
    "грам",
    "діал",
    "ек",
    "ел",
    "жарт",
    "зоол",
    "інформ",
    "іст",
    "кул",
    "лінгв",
    "мат",
    "мед",
    "мет",
    "мін",
    "мн",
    "мор",
    "муз",
    "перен",
    "побут",
    "поет",
    "політ",
    "розм",
    "спорт",
    "тех",
    "тж",
    "фіз",
    "філол",
    "філос",
    "хім",
    "церк",
}


def _ukreng_prefix_is_label(prefix: str) -> bool:
    words = re.findall(r"[А-Яа-яЄєІіЇїҐґ]+", prefix.casefold())
    return all(word in _SLOVNYK_UKRENG_PREFIX_LABELS for word in words)


def _clean_ukreng_gloss(candidate: str) -> str | None:
    cleaned = clean_html_entities(candidate)
    cleaned = re.sub(r"\b(?:also|fig|figurative|literally|lit)\.?\b", " ", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\(\s*(?:pl|sg|plural|singular)\.?\s*\)", " ", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" \t\r\n.,;:!?()[]{}«»\"“”")
    cleaned = re.sub(r"^(?:to|a|an|the)\s+", "", cleaned, flags=re.IGNORECASE)
    if not cleaned or not _LATIN_RE.search(cleaned) or re.search(r"[А-Яа-яЄєІіЇїҐґ]", cleaned):
        return None
    if len(cleaned.split()) > 5:
        return None
    return cleaned


def _slovnyk_ukreng_glosses(row: dict[str, Any], lemma: str, *, limit: int = 6) -> list[str]:
    text = str(row.get("text") or "")
    if not text:
        return []
    body = _SOURCE_TAIL_RE.sub("", _entry_text_without_headword(text, lemma, str(row.get("word") or "")))
    out: list[str] = []
    seen: set[str] = set()
    for chunk in re.split(r";|\n", body):
        chunk = re.sub(r"^\s*\d+\)?\.?\s*", "", chunk.strip())
        if not chunk:
            continue
        first_latin = _LATIN_RE.search(chunk)
        if not first_latin or not _ukreng_prefix_is_label(chunk[: first_latin.start()]):
            continue
        english_part = chunk[first_latin.start() :]
        first_cyrillic = re.search(r"[А-Яа-яЄєІіЇїҐґ]", english_part)
        if first_cyrillic:
            english_part = english_part[: first_cyrillic.start()]
        english_part = re.split(r"\s+—", english_part, maxsplit=1)[0]
        for candidate in re.split(r",|/|\bor\b", english_part, flags=re.IGNORECASE):
            gloss = _clean_ukreng_gloss(candidate)
            if not gloss:
                continue
            key = gloss.casefold()
            if key in seen:
                continue
            seen.add(key)
            out.append(gloss)
            if len(out) >= limit:
                return out
    return out


def _slovnyk_ukreng_row(lemma: str, cache: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(cache, dict):
        return None
    if _cache_has_lookup(cache, _SLOVNYK_UKRENG_SLUG):
        return _cache_lookup(cache, _SLOVNYK_UKRENG_SLUG)
    lookup_word = _slovnyk_lookup_word(lemma)
    if not lookup_word:
        return None
    try:
        row = _fetch_slovnyk_entry(lemma, lookup_word, _SLOVNYK_UKRENG_SLUG)
    except _SlovnykTransientError:
        return None
    if isinstance(row, dict):
        row["dictionary_label"] = _SLOVNYK_UKRENG_LABEL
    _cache_store_lookup(lemma, cache, _SLOVNYK_UKRENG_SLUG, row)
    return row


def _slovnyk_ukreng_translation(lemma: str, cache: dict[str, Any] | None) -> dict[str, object] | None:
    row = _slovnyk_ukreng_row(lemma, cache)
    if not row:
        return None
    glosses = _slovnyk_ukreng_glosses(row, lemma)
    if not glosses:
        return None
    block: dict[str, object] = {
        "en": glosses,
        "source": _SLOVNYK_UKRENG_SOURCE,
    }
    source_url = str(row.get("source_url") or "").strip()
    if source_url:
        block["source_url"] = source_url
    return block


def _translation(
    conn: sqlite3.Connection,
    lemma: str,
    kaikki_lookup: dict[str, dict[str, Any]] | None = None,
    *,
    entry_pos: object = None,
    gloss_hints: object = None,
    slovnyk_cache: dict[str, Any] | None = None,
) -> dict[str, object] | None:
    """English translations for a Ukrainian lemma (Переклад, §11).

    Primary source is the dmklinger UK→EN dictionary (`dmklinger_uk_en`) — a curated
    bilingual dictionary, preferred for precision. When dmklinger has no entry, fall
    back to Wiktionary/kaikki translation glosses (form-of/misspelling meta-glosses are
    stripped at build time). Балла is EN→UK only, so reverse lookup is used only when an
    exact Ukrainian token resolves to one unique English headword that matches an
    existing learner-gloss hint from the source entry. Returns up to six glosses.
    """
    index = _load_dmklinger_index(conn)
    if index:
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
    kaikki_translation = _kaikki_translation(kaikki_lookup or {}, lemma)
    if kaikki_translation:
        return kaikki_translation
    balla_translation = _balla_reverse_translation(
        conn,
        lemma,
        entry_pos=entry_pos,
        gloss_hints=gloss_hints,
    )
    if balla_translation:
        return balla_translation
    slovnyk_translation = _slovnyk_ukreng_translation(lemma, slovnyk_cache)
    if slovnyk_translation:
        return slovnyk_translation

    for variant in _split_lemma_variants(lemma):
        curated = _CURATED_LEARNER_TRANSLATIONS.get(_lookup_key(variant).casefold())
        if curated:
            return {
                "en": list(curated),
                "source": "curated learner gloss",
            }
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
        source_url = ""
        try:
            su_row = conn.execute(
                "SELECT source_url FROM literary_texts WHERE chunk_id = ? LIMIT 1",
                (str(chunk_id or ""),),
            ).fetchone()
            if su_row:
                source_url = str(su_row[0] or "")
        except sqlite3.OperationalError:
            source_url = ""
        return {
            "text": excerpt,
            "source": _LITERARY_SOURCE,
            "source_label": " · ".join(label_parts) if label_parts else _LITERARY_SOURCE,
            "chunk_id": str(chunk_id or ""),
            "source_url": source_url,
        }
    return None


_WIKI_REFERENCE_CACHE_DATA: dict[str, Any] | None = None
_WIKI_REFERENCE_CACHE_DIRTY = False


def _load_wiki_reference_cache(path: Path | None = None) -> dict[str, Any]:
    global _WIKI_REFERENCE_CACHE_DATA
    path = path or WIKI_REFERENCE_CACHE
    if _WIKI_REFERENCE_CACHE_DATA is not None:
        return _WIKI_REFERENCE_CACHE_DATA
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        data = {}
    _WIKI_REFERENCE_CACHE_DATA = data if isinstance(data, dict) else {}
    return _WIKI_REFERENCE_CACHE_DATA


def _write_wiki_reference_cache(path: Path | None = None) -> None:
    global _WIKI_REFERENCE_CACHE_DIRTY
    path = path or WIKI_REFERENCE_CACHE
    if not _WIKI_REFERENCE_CACHE_DIRTY or _WIKI_REFERENCE_CACHE_DATA is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(_WIKI_REFERENCE_CACHE_DATA, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _WIKI_REFERENCE_CACHE_DIRTY = False


@functools.cache
def query_wikipedia(title: str) -> dict[str, Any] | None:
    """Wrapper around rag.source_query.wikipedia_summary to support unit test mocking.

    Cached: a full-manifest enrich (~2K+ lemmas, many sharing a base form after
    `_base_lemma`/`_strip_stress` reduction) would otherwise fire one live HTTP
    request to uk.wikipedia per lemma. The cache dedupes repeated base forms and
    avoids re-hammering the API within a run (None results are cached too, so a
    missing article is not re-requested). Tests replace the whole function via
    monkeypatch, so the cache does not interfere with mocking.
    """
    if _phase1_offline_mode():
        return None

    try:
        from scripts.rag.source_query import wikipedia_summary

        return wikipedia_summary(title)
    except Exception:
        return None


def _cached_wikipedia_summary(title: str) -> dict[str, Any] | None:
    global _WIKI_REFERENCE_CACHE_DIRTY
    cache = _load_wiki_reference_cache()
    if title in cache:
        cached = cache[title]
        return cached if isinstance(cached, dict) else None
    if _phase1_offline_mode():
        return None

    wiki_data = query_wikipedia(title)
    cache[title] = wiki_data if isinstance(wiki_data, dict) else None
    _WIKI_REFERENCE_CACHE_DIRTY = True
    _write_wiki_reference_cache()
    return wiki_data if isinstance(wiki_data, dict) else None


def _wiki_reference(lemma: str, literary_attestation: dict | None = None) -> dict[str, Any] | None:
    """Fetch uk.wikipedia summary and generate uk.wiktionary and uk.wikisource links."""
    clean_lemma = _strip_stress(_base_lemma(lemma)).strip()
    wiki_data = _cached_wikipedia_summary(clean_lemma)
    if not wiki_data:
        return None

    wiktionary_url = f"https://uk.wiktionary.org/wiki/{quote(clean_lemma)}"
    wikisource_url = f"https://uk.wikisource.org/wiki/{quote(clean_lemma)}" if literary_attestation else None

    return {
        "wikipedia": {
            "title": wiki_data.get("title", ""),
            "summary": wiki_data.get("extract", ""),
            "url": wiki_data.get("url", ""),
        },
        "wiktionary_url": wiktionary_url,
        "wikisource_url": wikisource_url,
        "attribution": "Матеріали з Вікіпедії та Вікісловника, надані на умовах ліцензії CC BY-SA 4.0.",
    }


def _wikipedia_one_line_gloss(raw: object) -> str:
    text = re.sub(r"\s+", " ", clean_html_entities(str(raw or ""))).strip()
    if not text:
        return ""
    sentence = re.split(r"(?<=[.!?])\s+", text, maxsplit=1)[0].strip()
    return sentence[:300].strip(" ;,")


def _proper_noun_wikipedia_meaning(lemma: str) -> dict[str, object] | None:
    clean_lemma = _strip_stress(_base_lemma(lemma)).strip()
    wiki_data = _cached_wikipedia_summary(clean_lemma)
    if not wiki_data:
        return None
    gloss = _wikipedia_one_line_gloss(wiki_data.get("extract"))
    if not gloss:
        return None
    return {"definitions": [gloss], "source": "Вікіпедія"}


def _is_proper_noun_entry(entry: dict[str, Any]) -> bool:
    return "proper noun" in str(entry.get("pos") or "").casefold()


def _single_word_etymology_coverage(manifest: dict) -> tuple[int, int]:
    entries = [
        entry for entry in manifest.get("entries", []) if entry.get("lemma") and not _has_whitespace(entry.get("lemma"))
    ]
    covered = sum(1 for entry in entries if (entry.get("enrichment") or {}).get("etymology"))
    return covered, len(entries)


def enrich_entry(entry, conn, kaikki_lookup, *, has_sum11_flags) -> bool:
    """Enrich a single manifest entry in place (dictionary-grounded).
    Returns True if any enrichment was attached. Extracted from enrich() so the
    same per-lemma enrichment runs on delta lemmas (#3675 P2)."""
    normalized_lemma = strip_acute_stress(str(entry["lemma"]))
    if normalized_lemma != entry["lemma"]:
        entry["lemma"] = normalized_lemma
        entry["url_slug"] = _slug_for_url(normalized_lemma)
    if entry.get("gloss"):
        entry["gloss"] = clean_gloss(str(entry["gloss"]))
    lemma = entry["lemma"]
    base = _base_lemma(lemma)
    entry_pos = entry.get("pos")
    gloss_hints = _surface_gloss_hints(entry)
    fallback_base = _base_lookup_for_entry(lemma, entry_pos)
    slovnyk_cache = _slovnyk_cache(lemma)
    definition_cards = _definition_cards(
        conn,
        lemma,
        has_sum11_flags=has_sum11_flags,
        cache=slovnyk_cache,
    )
    heritage_status = classify_lemma(lemma)
    warning = _warning_slovnyk(lemma, slovnyk_cache) if _is_slovnyk_warning_candidate(entry, heritage_status) else None
    entry["heritage_status"] = _entry_scoped_heritage_status(_merge_slovnyk_warning(heritage_status, warning))
    curated_calque = _curated_calque(lemma, base)
    if curated_calque:
        entry["heritage_status"]["curated_calque"] = curated_calque
        # §6 decolonization moat note (PR1: active-present-participle calques only)
        # Emits native replacement(s) + source citation (Antonenko davydov/p145 + heritage guard)
        # for Atlas page §6 stylistic warning layer. See calque_corrections + issue #3098.
        note_dict = {
            "corrections": list(curated_calque.get("corrections", [])),
            "note": str(curated_calque.get("note", "")),
            "source": list(curated_calque.get("source", [])),
            "citation": "Антоненко-Давидович «Як ми говоримо» (davydov via MCP query_slovnyk_me + p145 prose via get_chunk_context; search_heritage guard applied)",
        }
        if "noteUk" in curated_calque:
            note_dict["noteUk"] = curated_calque["noteUk"]
        entry["heritage_status"]["§6_note"] = note_dict

    reverse_calques = _reverse_calques(lemma, base)
    if reverse_calques:
        entry["heritage_status"]["reverse_calques"] = reverse_calques

    pronunciation = _kaikki_pronunciation(kaikki_lookup, lemma)
    if pronunciation:
        entry["pronunciation"] = pronunciation
    else:
        entry.pop("pronunciation", None)
    sections: dict[str, object] = {}
    synonyms = _synonyms_slovnyk(base, slovnyk_cache, entry_pos=entry_pos)
    if not synonyms and fallback_base:
        synonyms = _synonyms_slovnyk(fallback_base, entry_pos=entry_pos)
        if synonyms:
            synonyms = _with_base_source_label(synonyms, fallback_base)
    if synonyms:
        sections["synonyms"] = synonyms
    antonyms = _antonyms_wiktionary(conn, base, entry_pos=entry_pos)
    if not antonyms and fallback_base:
        antonyms = _antonyms_wiktionary(conn, fallback_base, entry_pos=entry_pos)
        if antonyms:
            antonyms = _with_base_source_label(antonyms, fallback_base)
    if antonyms:
        sections["antonyms"] = antonyms
    idioms = _idioms(conn, lemma, slovnyk_cache)
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
    else:
        kaikki_stress = _kaikki_stress(kaikki_lookup, lemma)
        if kaikki_stress:
            block["stress"] = kaikki_stress
    cefr = _cefr(conn, lemma)
    if cefr:
        block["cefr"] = cefr
    morph = _morphology(base)
    if morph:
        block["morphology"] = morph
    entry["heritage_status"] = _finalize_heritage_status(
        entry["heritage_status"],
        morphology=morph,
        definition_cards=definition_cards,
    )
    meaning = _meaning(conn, lemma, has_sum11_flags=has_sum11_flags, kaikki_lookup=kaikki_lookup)
    if not meaning and fallback_base:
        meaning = _meaning(
            conn,
            fallback_base,
            has_sum11_flags=has_sum11_flags,
            kaikki_lookup=kaikki_lookup,
        )
        if meaning:
            meaning = _with_base_source_label(meaning, fallback_base)
    if _is_proper_noun_entry(entry):
        meaning = _proper_noun_wikipedia_meaning(lemma) or meaning
    if meaning:
        block["meaning"] = meaning
    if definition_cards:
        block["definition_cards"] = definition_cards
    etym = _etymology(conn, base, kaikki_lookup)
    if not etym and fallback_base:
        etym = _etymology(conn, fallback_base, kaikki_lookup)
        if etym:
            etym = _with_base_etymology_label(etym, fallback_base)
    if etym:
        block["etymology"] = etym
    literary = _literary_attestation(conn, lemma)
    if literary:
        block["literary_attestation"] = literary
    translation = _translation(
        conn,
        lemma,
        kaikki_lookup,
        entry_pos=entry_pos,
        gloss_hints=gloss_hints,
        slovnyk_cache=slovnyk_cache,
    )
    if not translation and fallback_base:
        fallback_slovnyk_cache = _slovnyk_cache(fallback_base)
        translation = _translation(
            conn,
            fallback_base,
            kaikki_lookup,
            entry_pos=entry_pos,
            gloss_hints=gloss_hints,
            slovnyk_cache=fallback_slovnyk_cache,
        )
        if translation:
            translation = _with_base_source_label(translation, fallback_base)
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

    wiki_ref = _wiki_reference(lemma, block.get("literary_attestation"))
    if wiki_ref:
        entry["wiki_reference"] = wiki_ref
    else:
        entry.pop("wiki_reference", None)

    return bool(block or sections or pronunciation or wiki_ref)


def enrich() -> tuple[int, int]:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    _normalize_manifest_entries(manifest)
    kaikki_lookup = _load_kaikki_lookup()
    conn = sqlite3.connect(f"file:{SOURCES_DB}?mode=ro", uri=True)
    enriched = 0
    try:
        has_sum11_flags = _sum11_has_flag_columns(conn)
        _prepare_cefr_estimates(conn, manifest)
        for entry in manifest["entries"]:
            if enrich_entry(entry, conn, kaikki_lookup, has_sum11_flags=has_sum11_flags):
                enriched += 1
    finally:
        conn.close()
    fingerprint_payload = write_fingerprint(DEFAULT_FINGERPRINT, root=ROOT)
    manifest["enrichment_generated"] = True
    manifest["manifest_fingerprint"] = {
        "schema_version": fingerprint_payload["schema_version"],
        "fingerprint": fingerprint_payload["fingerprint"],
    }
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
    print(f"enriched {enriched}/{total} lexicon entries from VESUM + СУМ + Горох/ЕСУМ/Вікісловник/kaikki + slovnyk.me")
    print(f"pronunciation {pronunciation_covered}/{total}")
    print(f"single-word etymology {etymology_covered}/{etymology_total}")


if __name__ == "__main__":
    main()
