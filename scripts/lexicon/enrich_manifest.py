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
- **synonyms** — sense-separated offline mphdict groups from the Ukrainian
  synonym database, preserving their original set boundaries.
- **sections.synonyms / sections.antonyms / sections.idioms** — mphdict synonym
  groups and local dictionary rows (Вікісловник antonyms; Фразеологічний).
- **heritage warning alternatives** — slovnyk.me correction dictionaries
  (Антоненко-Давидович, «Неправильно-правильно», Штепа чужослів).
- **etymology** — offline mphdict ЕСУМ roots, with the source volume/page
  citation and bibliography retained from the dictionary export.

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
from collections.abc import Callable, Sequence
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
from scripts.lexicon.load_relation_candidates import load_approved_synonym_verdicts
from scripts.lexicon.manifest_fingerprint import DEFAULT_FINGERPRINT, write_fingerprint
from scripts.lexicon.manifest_io import (
    GATE_ANNOTATIONS_CARRIED,
    GATE_REJECTED,
    GATE_SKIPPED_OFFLINE,
)
from scripts.lexicon.source_attribution import (
    BALLA_LABEL,
    CORRECTION_DICTIONARIES_LABEL,
    ESUM_LABEL,
    MPHDICT_SYNONYMS_LABEL,
    PHRASEOLOGY_LABEL,
    SLUG_ACADEMIC_LABELS,
    SUM20_ACADEMIC_LABEL,
    SUM20_SHORT_LABEL,
    VTS_ACADEMIC_LABEL,
    VTS_SHORT_LABEL,
    attach_official_url,
    join_academic_source_labels,
    normalize_academic_label,
    official_url_for_slug,
    remap_url_list,
)
from scripts.mphdict import mphdict_etymology, mphdict_synonyms, mphdict_synonyms_available
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

_SLOVNYK_DICT_LABELS: dict[str, str] = dict(SLUG_ACADEMIC_LABELS)
# Synonym slugs are retired from the active cache.  Atlas synonym enrichment
# is mphdict-only; keeping those mirror fetches here would silently continue
# the replaced scraper even though its result is no longer rendered.
_SLOVNYK_LOOKUP_SLUGS = tuple(
    slug for slug in _SLOVNYK_DICT_LABELS if slug not in {"synonyms", "synonyms_karavansky"}
)
_SLOVNYK_SYNONYM_SLUGS = ("synonyms_karavansky", "synonyms")
_SLOVNYK_IDIOM_SLUGS = ("phraseology",)
_SLOVNYK_WARNING_SLUGS = ("davydov", "voloschak", "foreign_shtepa")
_SLOVNYK_UKRENG_SLUG = "ukreng"
_SLOVNYK_UKRENG_LABEL = BALLA_LABEL
_SLOVNYK_UKRENG_SOURCE = BALLA_LABEL
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
    official_urls, mirror_urls = remap_url_list(list(dict.fromkeys(urls)))
    block: dict[str, Any] = {
        "items": items[:24],
        "source": join_academic_source_labels(sources),
    }
    if official_urls:
        block["source_urls"] = official_urls
    if mirror_urls:
        block["mirror_source_urls"] = mirror_urls
    return block


def _synonyms_mphdict(lemma: str) -> dict[str, Any] | None:
    """Return offline mphdict synonym groups without flattening sense boundaries."""
    result = mphdict_synonyms(lemma)
    if not result:
        return None
    synsets = result.get("synsets")
    if not isinstance(synsets, list) or not synsets:
        return None

    lookup_key = _lookup_key(lemma)
    items: list[str] = []
    seen: set[str] = set()
    for synset in synsets:
        if not isinstance(synset, dict):
            continue
        members = synset.get("members")
        if not isinstance(members, list):
            continue
        for member in members:
            if not isinstance(member, dict):
                continue
            member_lemma = str(member.get("lemma") or "").strip()
            if not member_lemma or _lookup_key(member_lemma) == lookup_key:
                continue
            if member_lemma not in seen:
                seen.add(member_lemma)
                items.append(member_lemma)
    if not items:
        return None
    return {
        "items": items[:24],
        "synsets": synsets,
        "source": MPHDICT_SYNONYMS_LABEL,
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

    source_term = _canonical_synonym_term(lemma)
    if not source_term or not _vesum_valid_synonym(source_term):
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
                if not term or term in seen or not _vesum_valid_synonym(term):
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
    item: dict[str, Any] = {
        "text": phrase,
        "phrase": phrase,
        "definition": definition,
        "source": PHRASEOLOGY_LABEL,
    }
    mirror_url = str(row.get("source_url") or "")
    attach_official_url(item, mirror_url=mirror_url, slug="phraseology", word=str(row.get("word") or lemma))
    official_urls, mirror_urls = remap_url_list([mirror_url] if mirror_url else [])
    block: dict[str, Any] = {
        "items": [item],
        "source": PHRASEOLOGY_LABEL,
    }
    if official_urls:
        block["source_urls"] = official_urls
    if mirror_urls:
        block["mirror_source_urls"] = mirror_urls
    return block


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
        "source": CORRECTION_DICTIONARIES_LABEL,
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


# --- «див.» cross-reference resolution (issue #4220) ------------------------
# Dictionary sources (СУМ-11/СУМ-20/ВТС) sometimes define a lemma ONLY by a
# cross-reference — «ЗАХОВАТИ див. заховувати» — so the atlas card ships with no
# usable meaning (58 grow rows deferred as flag:gloss-unresolved in the #4888
# ledger). When a built card's body reduces to a bare «див. X», resolve it ONE
# level deep: fetch X's card from the SAME source and ship X's verbatim body with
# an honest provenance prefix. Fail-closed — chains, missing targets, and any real
# inline text are left untouched (no invented glosses).
_DEFINITION_XREF_RE = re.compile(
    r"^(?P<pre>.*?)\bдив\.\s+(?P<targets>.+?)\s*\.?\s*$",
    flags=re.IGNORECASE | re.DOTALL,
)
_DEFINITION_SAME_AS_RE = re.compile(
    r"\bте\s+саме\s*,?\s+що\s+(?P<target>[А-Яа-яЄєІіЇїҐґ'’ʼ-]+)(?=\s*(?:[.;]|$))",
    flags=re.IGNORECASE,
)
_DEFINITION_ANTONYM_RE = re.compile(
    r"(?:^|[.;])\s*(?P<marker>протилежне|прот\.)\s+(?!до\b)(?P<targets>"
    r"[А-Яа-яЄєІіЇїҐґ'’ʼ-]+(?:\s*,\s*[А-Яа-яЄєІіЇїҐґ'’ʼ-]+){0,2})"
    r"(?=\s*(?:[.;(]|$))",
    flags=re.IGNORECASE,
)
# Grammar abbreviations that may sit between the headword echo and «див.» in a
# cross-reference-only entry (e.g. «ЗАХОВАТИ, док. див. заховувати»); any other
# word before «див.» means the card carries real definitional text → not xref-only.
_XREF_STOPWORDS = frozenset(
    {
        "док",
        "докон",
        "недок",
        "невідм",
        "незм",
        "перех",
        "неперех",
        "безос",
        "розм",
        "заст",
        "діал",
        "ім",
        "прикм",
        "присл",
        "с",
        "ч",
        "ж",
        "і",
        "й",
        "та",
        "чи",
    }
)
# A genuine cross-reference lists at most a few target lemmas; more word-tokens
# after «див.» means a real definition that merely mentions «див.» → leave it.
_XREF_MAX_TARGETS = 3


def _normalise_xref_targets(raw_targets: str) -> list[str]:
    """Normalize the lexical targets shared by the ``див.`` pointer parsers."""
    targets: list[str] = []
    seen: set[str] = set()
    for raw in re.split(r"[,\s;/]+", raw_targets):
        token = re.sub(r"[^А-Яа-яЄєІіЇїҐґ'’ʼ\-]", "", _strip_stress(raw)).strip("-'’ʼ").casefold()
        if not token or token.rstrip(".") in _XREF_STOPWORDS or token in seen:
            continue
        seen.add(token)
        targets.append(token)
    return targets


def _xref_target_lemmas(body: str, lemma: str) -> list[str]:
    """Return the target lemma(s) when ``body`` is ONLY a «див. X» cross-reference.

    A cross-reference-only body is the headword echo (optionally with a grammar
    tag), the literal «див.», then one or more target lemmas — and nothing else.
    Targets come back destressed + casefolded, in source order. Any real
    definitional text before or after «див.» yields ``[]`` (fail-closed)."""
    norm = _strip_stress(str(body or "")).strip()
    if not norm:
        return []
    match = _DEFINITION_XREF_RE.match(norm)
    if not match:
        return []
    pre = re.sub(r"[.,;()«»\"'’ʼ\s]+", " ", match.group("pre")).strip().casefold()
    allowed_echo = {
        _strip_stress(lemma).strip().casefold(),
        _strip_stress(_slovnyk_lookup_word(lemma)).strip().casefold(),
    }
    for token in pre.split():
        if token in allowed_echo or token.rstrip(".") in _XREF_STOPWORDS:
            continue
        return []
    targets = _normalise_xref_targets(match.group("targets"))
    return targets if 0 < len(targets) <= _XREF_MAX_TARGETS else []


def _definition_synonym_targets(body: str, lemma: str) -> list[tuple[str, str]]:
    """Extract high-precision synonym pointers from one definition row.

    This deliberately reuses the #4903 bare-``див.`` parser rather than matching
    every occurrence of that token in prose. ``Те саме, що X`` is likewise
    limited to one lexical target ending at a definition boundary.
    """
    targets = [(target, "див.") for target in _xref_target_lemmas(body, lemma)]
    match = _DEFINITION_SAME_AS_RE.search(_strip_stress(body))
    if match:
        same_as_targets = _normalise_xref_targets(match.group("target"))
        if len(same_as_targets) == 1:
            targets.append((same_as_targets[0], "Те саме, що"))
    return list(dict.fromkeys(targets))


def _definition_antonym_targets(body: str) -> list[tuple[str, str]]:
    """Extract explicit ``протилежне`` / ``прот.`` lemma pointers.

    СУМ-20 and СУМ-11 spell the relation as ``протилежне X``; VTS abbreviates
    it as ``прот. X``. A target is accepted only when it ends at a definition
    boundary, and ``протилежне до`` is deliberately excluded because it is
    ordinary prose rather than a lexicographer's antonym pointer.
    """
    targets: list[tuple[str, str]] = []
    for match in _DEFINITION_ANTONYM_RE.finditer(_strip_stress(body)):
        marker = match.group("marker").casefold()
        pattern = "прот." if marker == "прот." else "протилежне"
        for target in _normalise_xref_targets(match.group("targets")):
            targets.append((target, pattern))
    return list(dict.fromkeys(targets))


def _verb_aspect(word: str) -> str | None:
    """Return ``'perf'`` / ``'imperf'`` when VESUM verb analyses of ``word`` agree
    on one aspect, else ``None`` (non-verb, ambiguous, or unknown)."""
    try:
        rows = verify_word(word)
    except Exception:
        return None
    aspects: set[str] = set()
    for row in rows:
        if str(row.get("pos") or "") != "verb":
            continue
        tags = set(str(row.get("tags") or "").split(":"))
        if "imperf" in tags:
            aspects.add("imperf")
        elif "perf" in tags:
            aspects.add("perf")
    return next(iter(aspects)) if len(aspects) == 1 else None


def _xref_provenance_prefix(lemma: str, target: str) -> str:
    """Honest provenance note prefixed to a resolved «див.» card body. Keeps the
    cross-reference visible; for an aspect pair renders the standard «докон./недок.
    до X» form (the dominant class — perfective lemmas glossed by their
    imperfective)."""
    lemma_aspect = _verb_aspect(lemma)
    target_aspect = _verb_aspect(target)
    if lemma_aspect and target_aspect and lemma_aspect != target_aspect:
        label = "докон." if lemma_aspect == "perf" else "недок."
        return f"({label} до {target} / див. {target}) "
    return f"(див. {target}) "


def _resolve_definition_xref(
    card: dict[str, Any],
    lemma: str,
    fetch_target: Callable[[str], dict[str, Any] | None],
) -> dict[str, Any] | None:
    """One-level «див.» resolution for a built definition card.

    When ``card``'s body is only a «див. X» cross-reference, fetch X's card in the
    SAME source via ``fetch_target`` (which MUST itself skip resolution — that is
    what keeps this exactly one level deep) and return a resolved copy: X's
    verbatim body prefixed with a provenance note. Returns ``None`` — leaving the
    caller's original card in place — when the body is not a bare cross-reference,
    or the target is missing / empty / itself a «див.» (chain). Never invents text."""
    definitions = card.get("definitions") or []
    body = str(definitions[0]) if definitions else ""
    targets = _xref_target_lemmas(body, lemma)
    if not targets:
        return None
    for target in targets:
        resolved_lemma = _vesum_base_lemma(target) or target
        target_card = fetch_target(resolved_lemma)
        if not target_card:
            continue
        target_defs = target_card.get("definitions") or []
        target_body = str(target_defs[0]).strip() if target_defs else ""
        if not target_body or _xref_target_lemmas(target_body, resolved_lemma):
            continue  # target missing/empty or itself a «див.» → refuse the chain
        resolved = dict(card)
        resolved["definitions"] = [f"{_xref_provenance_prefix(lemma, resolved_lemma)}{target_body}"]
        resolved["cross_reference"] = {
            "raw": re.sub(r"\s+", " ", _strip_stress(body)).strip(),
            "target": resolved_lemma,
        }
        return resolved
    return None


def _sum20_in_coverage(lemma: str) -> bool:
    lookup = _slovnyk_lookup_word(lemma)
    if not lookup or _has_whitespace(lookup):
        return False
    return lookup[0].casefold() in _SUM20_COVERED_INITIALS


def _sum20_definition_card(
    lemma: str,
    cache: dict[str, Any] | None = None,
    *,
    resolve_xref: bool = True,
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
    card = {
        "id": "sum20",
        "source": SUM20_ACADEMIC_LABEL,
        "source_pill": SUM20_SHORT_LABEL,
        "note": "сучасний тлумачний словник",
        "definitions": [text],
    }
    mirror_url = str(row.get("source_url") or "")
    attach_official_url(
        card,
        mirror_url=mirror_url,
        slug="newsum",
        word=str(row.get("word") or lookup_word),
    )
    if resolve_xref:
        resolved = _resolve_definition_xref(
            card,
            lemma,
            lambda target: _sum20_definition_card(target, resolve_xref=False),
        )
        if resolved is not None:
            return resolved
    return card


def _vts_definition_card(
    lemma: str,
    cache: dict[str, Any] | None = None,
    *,
    resolve_xref: bool = True,
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
    card = {
        "id": "vts",
        "source": VTS_ACADEMIC_LABEL,
        "source_pill": VTS_SHORT_LABEL,
        "note": "Великий тлумачний словник сучасної української мови",
        "definitions": [text],
    }
    mirror_url = str(row.get("source_url") or "")
    attach_official_url(
        card,
        mirror_url=mirror_url,
        slug="vts",
        word=str(row.get("word") or lookup_word),
    )
    if resolve_xref:
        resolved = _resolve_definition_xref(
            card,
            lemma,
            lambda target: _vts_definition_card(target, resolve_xref=False),
        )
        if resolved is not None:
            return resolved
    return card


def _sum11_definition_card(
    conn: sqlite3.Connection,
    lemma: str,
    *,
    has_sum11_flags: bool,
    resolve_xref: bool = True,
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
        if resolve_xref:
            resolved = _resolve_definition_xref(
                card,
                lemma,
                lambda target: _sum11_definition_card(
                    conn, target, has_sum11_flags=has_sum11_flags, resolve_xref=False
                ),
            )
            if resolved is not None:
                return resolved
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


_SYNONYM_ADDITION_CAP = 8
_ANTONYM_ADDITION_CAP = 8
_HOMONYM_ADDITION_CAP = 8
_PARONYM_ADDITION_CAP = 8


def _canonical_synonym_term(value: object) -> str | None:
    """Return a destressed, apostrophe-normalized Ukrainian synonym candidate."""
    term = _lookup_key(_strip_stress(clean_html_entities(str(value or "")))).strip().casefold()
    return term if term and _UKRAINIAN_WORD_RE.fullmatch(term) else None


def _read_cached_slovnyk_rows(lemma: str) -> dict[str, Any]:
    """Read a pre-existing slovnyk.me cache entry without fetching or writing."""
    cache = _load_slovnyk_cache_file(_slovnyk_cache_path(lemma))
    return cache if isinstance(cache, dict) else {}


def _dictionary_definition_rows(
    conn: sqlite3.Connection,
    lemma: str,
    *,
    has_sum11_flags: bool,
    cache: dict[str, Any] | None = None,
    include_grinchenko: bool = False,
) -> list[dict[str, Any]]:
    """Return local definition rows with the evidence metadata needed for gates.

    Slovnyk.me entries come only from the cache supplied by the caller (or a
    read-only cache read). This helper must never turn synonym extraction into a
    network fetch or a cache/database write.
    """
    cache = cache if cache is not None else _read_cached_slovnyk_rows(lemma)
    rows: list[dict[str, Any]] = []
    for slug, source in (("newsum", "СУМ-20"), ("vts", "ВТС")):
        row = _cache_lookup(cache, slug)
        if not row:
            continue
        text = _definition_body(
            row.get("text"),
            headword=str(row.get("word") or lemma),
            strip_leading_headword=True,
        )
        if text:
            row_payload: dict[str, Any] = {
                "source": SUM20_SHORT_LABEL if source == "СУМ-20" else source,
                "text": text,
                "sovietization_risk": 0,
            }
            mirror_url = str(row.get("source_url") or "")
            if mirror_url:
                attach_official_url(
                    row_payload,
                    mirror_url=mirror_url,
                    slug="newsum" if slug == "newsum" else "vts",
                    word=str(row.get("word") or lemma),
                )
            rows.append(row_payload)

    sum11_fields = "definition, text"
    if has_sum11_flags:
        sum11_fields += ", sovietization_risk, sovietization_keywords"
    try:
        for variant in _split_lemma_variants(lemma):
            for row in conn.execute(
                f"SELECT {sum11_fields} FROM sum11 WHERE word = ? AND definition != ''",
                (variant,),
            ).fetchall():
                risk, _keywords = _sum11_row_flags(row, has_flag_columns=has_sum11_flags)
                text = _definition_body(row[0])
                if text:
                    rows.append(
                        {
                            "source": "СУМ-11",
                            "text": text,
                            "source_url": "",
                            "sovietization_risk": risk,
                        }
                    )
    except sqlite3.Error:
        pass

    if include_grinchenko:
        try:
            for variant in _split_lemma_variants(lemma):
                for definition, _source in conn.execute(
                    "SELECT definition, source FROM grinchenko WHERE word = ? AND definition != ''",
                    (variant,),
                ).fetchall():
                    text = _definition_body(definition)
                    if text:
                        rows.append(
                            {
                                "source": "Грінченко",
                                "text": text,
                                "source_url": "",
                                "sovietization_risk": 0,
                            }
                        )
        except sqlite3.Error:
            pass
    return rows


def _vesum_valid_synonym(term: str) -> bool:
    """Fail closed unless VESUM recognizes the emitted term as its own lemma."""
    try:
        term_key = _lookup_key(term)
        return any(_lookup_key(str(row.get("lemma") or "")) == term_key for row in verify_word(term))
    except Exception:
        return False


def _definition_pointer_relations(
    conn: sqlite3.Connection,
    lemma: str,
    *,
    has_sum11_flags: bool,
    cache: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Vein 1: lexicographer-authored ``Те саме, що`` / ``див.`` relations."""
    relations: list[dict[str, Any]] = []
    for row in _dictionary_definition_rows(
        conn,
        lemma,
        has_sum11_flags=has_sum11_flags,
        cache=cache,
    ):
        for target, pattern in _definition_synonym_targets(str(row["text"]), lemma):
            item = _canonical_synonym_term(target)
            if not item or not _vesum_valid_synonym(item):
                continue
            relation: dict[str, Any] = {
                "item": item,
                "source": row["source"],
                "pattern": pattern,
                "vein": 1,
            }
            if row.get("source_url"):
                relation["source_url"] = row["source_url"]
            relations.append(relation)
    return relations


def _manifest_headwords(manifest: dict[str, Any]) -> dict[str, str]:
    """Map canonical manifest headword variants to their display forms."""
    headwords: dict[str, str] = {}
    for entry in manifest.get("entries", []):
        lemma = str(entry.get("lemma") or "")
        for variant in _split_lemma_variants(lemma):
            term = _canonical_synonym_term(variant)
            if term:
                headwords.setdefault(term, term)
    return headwords


def _manifest_relation_aliases(manifest: dict[str, Any]) -> dict[str, str]:
    """Resolve manifest form aliases to their canonical lemma via route slugs.

    Relation-pair rows retain their source lemmas, while the rendered manifest
    must attach them to canonical Atlas pages.  Form entries carry their target
    route in ``form_of.url_slug``; resolving through that route keeps relation
    rendering aligned with the Atlas alias contract rather than guessing from
    a display string.
    """
    canonical_by_slug: dict[str, str] = {}
    entries = [entry for entry in manifest.get("entries", []) if isinstance(entry, dict)]
    for entry in entries:
        if entry.get("form_of"):
            continue
        lemma = _canonical_synonym_term(entry.get("lemma"))
        slug = str(entry.get("url_slug") or "").strip()
        if lemma and slug:
            canonical_by_slug[slug] = lemma

    aliases: dict[str, str] = {}
    for entry in entries:
        alias = _canonical_synonym_term(entry.get("lemma"))
        if not alias:
            continue
        form_of = entry.get("form_of")
        target: str | None = None
        if isinstance(form_of, dict):
            target = canonical_by_slug.get(str(form_of.get("url_slug") or "").strip())
            target = target or _canonical_synonym_term(form_of.get("lemma"))
        if target is None:
            target = _canonical_synonym_term(entry.get("lemma"))
        if target:
            aliases[alias] = target
    return aliases


def _definition_pointer_relations_by_headword(
    conn: sqlite3.Connection,
    manifest: dict[str, Any],
    *,
    has_sum11_flags: bool,
) -> dict[str, list[dict[str, Any]]]:
    """Precompute pointer relations and safe reciprocal manifest-headword pairs."""
    headwords = _manifest_headwords(manifest)
    by_headword: dict[str, list[dict[str, Any]]] = {}
    for entry in manifest.get("entries", []):
        lemma = str(entry.get("lemma") or "")
        source_key = _canonical_synonym_term(lemma)
        if not source_key:
            continue
        relations = _definition_pointer_relations(
            conn,
            lemma,
            has_sum11_flags=has_sum11_flags,
        )
        if relations:
            by_headword.setdefault(source_key, []).extend(relations)
        for relation in relations:
            target_key = str(relation["item"])
            if target_key not in headwords or not _vesum_valid_synonym(source_key):
                continue
            reciprocal = dict(relation)
            reciprocal["item"] = headwords[source_key]
            reciprocal["direction"] = "reciprocal"
            by_headword.setdefault(target_key, []).append(reciprocal)
    return by_headword


def _definition_antonym_relations(
    conn: sqlite3.Connection,
    lemma: str,
    *,
    has_sum11_flags: bool,
    cache: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Lexicographer-authored antonym pointers, VESUM-gated at both ends."""
    source_term = _canonical_synonym_term(lemma)
    if not source_term or not _vesum_valid_synonym(source_term):
        return []

    relations: list[dict[str, Any]] = []
    for row in _dictionary_definition_rows(
        conn,
        lemma,
        has_sum11_flags=has_sum11_flags,
        cache=cache,
    ):
        for target, pattern in _definition_antonym_targets(str(row["text"])):
            item = _canonical_synonym_term(target)
            if not item or item == source_term or not _vesum_valid_synonym(item):
                continue
            relation: dict[str, Any] = {
                "item": item,
                "source": row["source"],
                "pattern": pattern,
                "vein": 1,
                "gate": {"vesum": "both valid"},
            }
            if row.get("source_url"):
                relation["source_url"] = row["source_url"]
            relations.append(relation)
    return relations


def _definition_antonym_relations_by_headword(
    conn: sqlite3.Connection,
    manifest: dict[str, Any],
    *,
    has_sum11_flags: bool,
) -> dict[str, list[dict[str, Any]]]:
    """Precompute explicit antonym pointers and symmetric manifest-headword pairs."""
    headwords = _manifest_headwords(manifest)
    by_headword: dict[str, list[dict[str, Any]]] = {}
    for entry in manifest.get("entries", []):
        lemma = str(entry.get("lemma") or "")
        source_key = _canonical_synonym_term(lemma)
        if not source_key:
            continue
        relations = _definition_antonym_relations(
            conn,
            lemma,
            has_sum11_flags=has_sum11_flags,
        )
        if relations:
            by_headword.setdefault(source_key, []).extend(relations)
        for relation in relations:
            target_key = str(relation["item"])
            if target_key not in headwords:
                continue
            reciprocal = dict(relation)
            reciprocal["item"] = headwords[source_key]
            reciprocal["direction"] = "reciprocal"
            by_headword.setdefault(target_key, []).append(reciprocal)
    return by_headword


# СУМ-11 encodes lexical homonyms as consecutive, explicitly numbered heads in
# one ``definition`` value (for example ``КОСА́¹ … КОСА́² …``), rather than as
# separate database rows. The source data uses Unicode superscript digits.
# Keep this separate from ordinary sense numbers (``1.``, ``2.``): only a
# superscript immediately following an all-capital headword is a homonym marker.
_HOMONYM_SUPERSCRIPT_TO_INT = {
    "¹": 1,
    "²": 2,
    "³": 3,
    "⁴": 4,
    "⁵": 5,
    "⁶": 6,
    "⁷": 7,
    "⁸": 8,
    "⁹": 9,
}
HOMONYM_DIGIT_RE = re.compile(r"(?P<homonym_no>[¹²³⁴⁵⁶⁷⁸⁹])")
_HOMONYM_HEADWORD_RE = re.compile(
    rf"(?P<surface>(?:[А-ЯҐІЇЄ'’ʼ-][\u0300\u0301]?)+)\s*{HOMONYM_DIGIT_RE.pattern}"
    r"(?=\s*(?:[,.;:—-]|$))"
)
_HOMONYM_NOUN_RE = re.compile(r",\s*(?P<gender>ч|ж|с|мн)\.(?P<body>.*)", flags=re.IGNORECASE | re.DOTALL)
_HOMONYM_POS_RE = re.compile(
    r"\b(?P<marker>прикм|присл|числ|займ|прийм|спол|част|виг|док|недок)\.(?P<body>.*)",
    flags=re.IGNORECASE | re.DOTALL,
)
_HOMONYM_POS_LABELS = {
    "прикм": "прикметник",
    "присл": "прислівник",
    "числ": "числівник",
    "займ": "займенник",
    "прийм": "прийменник",
    "спол": "сполучник",
    "част": "частка",
    "виг": "вигук",
    "док": "дієслово",
    "недок": "дієслово",
}
_HOMONYM_LEADING_QUALIFIERS_RE = re.compile(
    r"^\s*(?:,\s*)?(?:(?:діал|заст|розм|рідко|спец|поет|перен|розмовне|мет)\.\s*)*",
    flags=re.IGNORECASE,
)
_HOMONYM_LEADING_SENSE_NO_RE = re.compile(r"^\s*\d+\s*\.\s*")
_HOMONYM_LEADING_GRAMMAR_RE = re.compile(
    r"^\s*(?:род|дав|знах|ор|місц|клич)\.\s*[А-Яа-яЄєІіЇїҐґ\u0300\u0301]+\.\s*",
    flags=re.IGNORECASE,
)


def _homonym_pos_and_gloss(fragment: str) -> tuple[str, str] | None:
    """Extract a dictionary POS and short first-definition gloss from one block.

    Membership is accepted only when both values are explicit. This deliberately
    declines malformed number runs instead of turning an ordinary polysemous
    sense list into a homonym relation.
    """
    pos = ""
    body = ""
    noun_match = _HOMONYM_NOUN_RE.search(fragment)
    if noun_match:
        gender = noun_match.group("gender").casefold()
        if gender == "мн":
            pos = "іменник, множина"
        else:
            gender_label = {"ч": "чол.", "ж": "жін.", "с": "сер."}[gender]
            pos = f"іменник, {gender_label} р."
        body = noun_match.group("body")
    else:
        pos_match = _HOMONYM_POS_RE.search(fragment)
        if not pos_match:
            # Adjective heads normally use the compact ``-ий, а, е.`` form.
            adjective_match = re.match(r"\s*,\s*[^.]{0,48},\s*[аеєі]\.\s*(?P<body>.*)", fragment)
            if adjective_match:
                pos = "прикметник"
                body = adjective_match.group("body")
            else:
                return None
        else:
            marker = pos_match.group("marker").casefold()
            pos = _HOMONYM_POS_LABELS[marker]
            body = pos_match.group("body")

    # The source can place a register marker before its first sense number
    # (``мет. 1. …``) or a case-government note after it (``1. род. а. …``).
    # Peel only these header conventions, never prose inside the definition.
    for _ in range(3):
        body = _HOMONYM_LEADING_QUALIFIERS_RE.sub("", body)
        body = _HOMONYM_LEADING_SENSE_NO_RE.sub("", body)
        body = _HOMONYM_LEADING_GRAMMAR_RE.sub("", body)
    if not body:
        return None
    gloss = re.split(r"(?<=[.!?])\s+(?=[А-ЯҐІЇЄ])", body, maxsplit=1)[0].strip()
    gloss = _truncate_text(gloss, 180)
    return (pos, gloss) if gloss else None


def _numbered_homonym_members(text: str, surface: str) -> list[dict[str, Any]]:
    """Parse one dictionary article's explicitly numbered same-surface heads."""
    surface_key = _canonical_synonym_term(surface)
    if not surface_key:
        return []
    matches = [
        match
        for match in _HOMONYM_HEADWORD_RE.finditer(text)
        if _canonical_synonym_term(_strip_stress(match.group("surface"))) == surface_key
    ]
    members: list[dict[str, Any]] = []
    seen_numbers: set[int] = set()
    for index, match in enumerate(matches):
        number = _HOMONYM_SUPERSCRIPT_TO_INT[match.group("homonym_no")]
        if number in seen_numbers:
            return []
        seen_numbers.add(number)
        block_end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        pos_and_gloss = _homonym_pos_and_gloss(text[match.end() : block_end])
        if pos_and_gloss is None:
            return []
        pos, gloss = pos_and_gloss
        members.append(
            {
                "word": surface_key,
                "homonym_no": number,
                "gloss": gloss,
                "pos": pos,
            }
        )
    return members if len(members) >= 2 else []


def _homonym_dictionary_rows(
    conn: sqlite3.Connection,
    lemma: str,
    *,
    cache: dict[str, Any] | None = None,
) -> list[dict[str, str]]:
    """Return full local СУМ rows; never fetch or mutate a slovnyk cache.

    Unlike ordinary definition cards, a homonym set cannot be truncated at the
    first 900 characters: later numbered heads are part of the same evidence.
    """
    cache = cache if cache is not None else _read_cached_slovnyk_rows(lemma)
    rows: list[dict[str, str]] = []
    sum20 = _cache_lookup(cache, "newsum")
    if sum20 and sum20.get("text"):
        payload = {
            "source": SUM20_SHORT_LABEL,
            "text": _definition_body(sum20["text"], limit=20_000),
        }
        attach_official_url(
            payload,
            mirror_url=str(sum20.get("source_url") or ""),
            slug="newsum",
            word=str(sum20.get("word") or lemma),
        )
        rows.append(payload)
    try:
        for variant in _split_lemma_variants(lemma):
            for definition, text in conn.execute(
                "SELECT definition, text FROM sum11 WHERE word = ? AND definition != ''",
                (variant,),
            ).fetchall():
                raw = str(definition or text or "")
                if raw:
                    rows.append({"source": "СУМ-11", "text": raw, "source_url": ""})
    except sqlite3.Error:
        pass
    return rows


def _homonym_relations(
    conn: sqlite3.Connection,
    lemma: str,
    *,
    cache: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Emit numbered lexical-homonym siblings, gated by dictionary and VESUM.

    СУМ numbering establishes the semantic set. VESUM does not encode those
    homonym indices, so it can honestly gate only the shared surface as a valid
    lemma; an invented ``two VESUM lemmas`` threshold would reject the recorded
    sets for ``ключ``, ``лист``, and ``стан``.
    """
    source_term = _canonical_synonym_term(lemma)
    if not source_term:
        return []
    best_row: dict[str, str] | None = None
    best_members: list[dict[str, Any]] = []
    for row in _homonym_dictionary_rows(conn, lemma, cache=cache):
        members = _numbered_homonym_members(row["text"], source_term)
        if len(members) > len(best_members):
            best_row = row
            best_members = members
    if not best_row:
        return []
    if not all(_vesum_valid_synonym(str(member["word"])) for member in best_members):
        return []

    # An unnumbered Atlas entry names the lead (lowest-numbered) dictionary
    # head. The relation lists only the other numbered lexical headwords. Use
    # the source with the most complete numbered run: a stale СУМ-20 cache can
    # contain only the first two heads where local СУМ-11 records all of them.
    lead_number = min(int(member["homonym_no"]) for member in best_members)
    relations: list[dict[str, Any]] = []
    for member in best_members:
        if int(member["homonym_no"]) == lead_number:
            continue
        relation: dict[str, Any] = {
            **member,
            "source": best_row["source"],
            "pattern": "numbered homonym headword",
            "vein": 1,
            "gate": {"vesum": "valid lemma"},
        }
        if best_row["source_url"]:
            relation["source_url"] = best_row["source_url"]
        relations.append(relation)
    return relations


def _homonym_relations_by_headword(
    conn: sqlite3.Connection,
    manifest: dict[str, Any],
) -> dict[str, list[dict[str, Any]]]:
    """Precompute each manifest headword's dictionary-numbered homonym set."""
    by_headword: dict[str, list[dict[str, Any]]] = {}
    for entry in manifest.get("entries", []):
        lemma = str(entry.get("lemma") or "")
        source_key = _canonical_synonym_term(lemma)
        if not source_key:
            continue
        relations = _homonym_relations(conn, lemma)
        if relations:
            by_headword[source_key] = relations
    return by_headword


def _paronym_pair_members(value: object) -> list[tuple[str, str]]:
    """Parse semicolon-delimited ``word/word`` pairs from a curated ZNO field."""
    pairs: list[tuple[str, str]] = []
    for raw_pair in str(value or "").split(";"):
        members = [_canonical_synonym_term(member) for member in raw_pair.split("/")]
        if len(members) != 2 or not all(members) or members[0] == members[1]:
            continue
        pairs.append((members[0], members[1]))
    return pairs


def _paronym_cache_distinction(definition: object, target: str) -> str:
    """Return the cache sentence that distinguishes the confusable target."""
    text = re.sub(r"\s+", " ", clean_html_entities(str(definition or ""))).strip()
    if not text:
        return ""
    target_re = re.compile(rf"^\s*{re.escape(target)}\s*[—–-]\s*(.+)", flags=re.IGNORECASE)
    for sentence in re.split(r"(?<=[.!?])\s+", text):
        match = target_re.match(sentence)
        if match:
            return _truncate_text(match.group(1).strip(), 240)
    return _truncate_text(text, 300)


def _paronym_relations(
    conn: sqlite3.Connection,
    lemma: str,
) -> list[dict[str, Any]]:
    """Emit VESUM-gated paronym pairs from ZNO and the existing open cache.

    ZNO pairs are ordered first because they are exam-validated. The cache can
    then supplement a pair with a compact semantic distinction; neither source
    invents a distinction where its raw record does not provide one.
    """
    source_term = _canonical_synonym_term(lemma)
    if not source_term or not _vesum_valid_synonym(source_term):
        return []
    relations: list[dict[str, Any]] = []

    try:
        zno_columns = {
            str(row[1]) for row in conn.execute("PRAGMA table_info(zno_tasks)").fetchall()
        }
        document_columns = {
            str(row[1]) for row in conn.execute("PRAGMA table_info(zno_documents)").fetchall()
        }
        if {"year", "task_no", "task_subtype", "paronym_pair"} <= zno_columns:
            if {"document_id"} <= zno_columns and "url" in document_columns:
                rows = conn.execute(
                    """
                    SELECT t.year, t.task_no, t.paronym_pair, d.url
                    FROM zno_tasks AS t
                    LEFT JOIN zno_documents AS d ON d.id = t.document_id
                    WHERE t.task_subtype = 'paronym' OR trim(t.paronym_pair) != ''
                    """
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT year, task_no, paronym_pair, ''
                    FROM zno_tasks
                    WHERE task_subtype = 'paronym' OR trim(paronym_pair) != ''
                    """
                ).fetchall()
            for year, task_no, pair_text, source_url in rows:
                for first, second in _paronym_pair_members(pair_text):
                    if source_term not in {first, second}:
                        continue
                    other = second if source_term == first else first
                    if not _vesum_valid_synonym(other):
                        continue
                    relation: dict[str, Any] = {
                        "word": other,
                        "source": "ЗНО",
                        "pattern": "exam-tested paronym pair",
                        "vein": 1,
                        "exam_provenance": f"ЗНО {year}, завдання №{task_no}",
                        "gate": {"vesum": "both valid"},
                    }
                    if str(source_url or "").strip():
                        relation["source_url"] = str(source_url)
                    relations.append(relation)
    except sqlite3.Error:
        pass

    try:
        cache_columns = {
            str(row[1]) for row in conn.execute("PRAGMA table_info(paronyms_cache)").fetchall()
        }
        if {"word_a", "word_b", "definition"} <= cache_columns:
            for first_raw, second_raw, definition in conn.execute(
                "SELECT word_a, word_b, definition FROM paronyms_cache"
            ).fetchall():
                first = _canonical_synonym_term(first_raw)
                second = _canonical_synonym_term(second_raw)
                if not first or not second or source_term not in {first, second}:
                    continue
                other = second if source_term == first else first
                if not _vesum_valid_synonym(other):
                    continue
                relation = {
                    "word": other,
                    "distinction": _paronym_cache_distinction(definition, other),
                    "source": "paronyms_cache",
                    "pattern": "cached paronym distinction",
                    "vein": 2,
                    "gate": {"vesum": "both valid"},
                }
                relations.append(relation)
    except sqlite3.Error:
        pass
    return relations


def _paronym_relations_by_headword(
    conn: sqlite3.Connection,
    manifest: dict[str, Any],
) -> dict[str, list[dict[str, Any]]]:
    """Precompute VESUM-gated ZNO/cache paronym pairs for manifest headwords."""
    by_headword: dict[str, list[dict[str, Any]]] = {}
    for entry in manifest.get("entries", []):
        lemma = str(entry.get("lemma") or "")
        source_key = _canonical_synonym_term(lemma)
        if not source_key:
            continue
        relations = _paronym_relations(conn, lemma)
        if relations:
            by_headword[source_key] = relations
    return by_headword


def _corpus_relation_pairs_by_headword(
    conn: sqlite3.Connection,
    manifest: dict[str, Any],
) -> dict[str, dict[str, list[dict[str, Any]]]]:
    """Read VESUM-gated relation-pair corpus facts for Atlas headwords.

    Only explicitly approved corpus rows are eligible for rendering, and both
    recorded lemmas are re-checked here. This makes the Atlas safe if a stale
    or manually edited row no longer satisfies the exact-lemma contract.
    Corpus provenance stays separate from legacy dictionary veins.
    """
    headwords = _manifest_headwords(manifest)
    aliases = _manifest_relation_aliases(manifest)
    by_headword: dict[str, dict[str, list[dict[str, Any]]]] = {}
    try:
        rows = conn.execute(
            """
            SELECT relation, word_a, word_b, gloss_a, gloss_b, source, source_url
            FROM relation_pairs
            WHERE review_status = 'approved'
            ORDER BY relation, word_a, word_b, gloss_a, gloss_b, source
            """
        ).fetchall()
    except sqlite3.Error:
        return by_headword

    for relation_raw, word_a_raw, word_b_raw, gloss_a_raw, gloss_b_raw, source_raw, source_url_raw in rows:
        relation = str(relation_raw or "").strip().casefold()
        if relation not in {"synonym", "antonym", "paronym", "homonym"}:
            continue
        word_a = _canonical_synonym_term(word_a_raw)
        word_b = _canonical_synonym_term(word_b_raw)
        if not word_a or not word_b or not (_vesum_valid_synonym(word_a) and _vesum_valid_synonym(word_b)):
            continue
        word_a = aliases.get(word_a, word_a)
        word_b = aliases.get(word_b, word_b)
        source = f"relation_pairs/{str(source_raw or '').strip()}"
        if source == "relation_pairs/":
            continue
        source_url = str(source_url_raw or "").strip()
        gloss_a = str(gloss_a_raw or "").strip()
        gloss_b = str(gloss_b_raw or "").strip()

        def append(
            headword: str,
            other: str,
            other_gloss: str,
            *,
            corpus_relation: str = relation,
            corpus_source: str = source,
            corpus_source_url: str = source_url,
        ) -> None:
            if headword not in headwords:
                return
            relation_data: dict[str, Any] = {
                "source": corpus_source,
                "pattern": "corpus relation pair",
                "vein": 3,
                "gate": {"vesum": "both valid"},
            }
            if corpus_source_url:
                relation_data["source_url"] = corpus_source_url
            if corpus_relation in {"synonym", "antonym"}:
                relation_data["item"] = other
            elif corpus_relation == "paronym":
                relation_data["word"] = other
                if other_gloss:
                    relation_data["distinction"] = other_gloss
            elif not other_gloss:
                # A homonym needs an independently authored gloss to be useful;
                # do not manufacture a number or a part of speech for the UI.
                return
            else:
                relation_data["word"] = other
                relation_data["gloss"] = other_gloss
            by_headword.setdefault(headword, {}).setdefault(corpus_relation, []).append(relation_data)

        if relation == "homonym" and word_a == word_b:
            for gloss in dict.fromkeys(gloss for gloss in (gloss_a, gloss_b) if gloss):
                append(word_a, word_a, gloss)
            continue
        if word_a == word_b:
            continue
        append(word_a, word_b, gloss_b)
        append(word_b, word_a, gloss_a)
    return by_headword


def _relation_source_label(relation: dict[str, Any], item: str) -> str:
    """Record pair-level provenance in the existing rendered ``source`` field."""
    source = normalize_academic_label(str(relation.get("source") or ""))
    # A relation with no/blank source must not render a leading-colon label.
    label = f"{source}: {relation['pattern']} → {item}" if source else f"{relation['pattern']} → {item}"
    if relation.get("direction"):
        label += " (reciprocal)"
    gate = relation.get("gate")
    if not isinstance(gate, dict):
        return label
    co_attestation = gate.get("co_attestation")
    if isinstance(co_attestation, dict):
        if co_attestation.get("kind") == "definition_mention":
            evidence = f"{co_attestation.get('dictionary')} {co_attestation.get('direction')}"
        else:
            dictionaries = "/".join(str(value) for value in co_attestation.get("dictionaries", []))
            evidence = f"{dictionaries} stem={co_attestation.get('stem')}"
        synset_id = str(gate.get("synset_id") or "")
        synset_note = f"; synset={synset_id}" if synset_id else ""
        label += f" [gate: VESUM both valid; {evidence}{synset_note}]"
    return label


def _append_relation_source_urls(
    merged: dict[str, Any],
    source_urls: list[str],
    relation: dict[str, Any],
) -> None:
    raw = str(relation.get("source_url") or "").strip()
    if not raw:
        return
    official, mirrors = remap_url_list([raw])
    source_urls.extend(url for url in official if url not in source_urls)
    if mirrors:
        mirror_urls = [str(url) for url in merged.get("mirror_source_urls", []) if str(url).strip()]
        mirror_urls.extend(url for url in mirrors if url not in mirror_urls)
        merged["mirror_source_urls"] = list(dict.fromkeys(mirror_urls))


def _merge_synonym_relations(
    existing: dict[str, Any] | None,
    relations: list[dict[str, Any]],
) -> dict[str, Any] | None:
    """Merge the two precision-ordered synonym veins into the rendered schema."""
    merged = dict(existing or {})
    items = [str(item) for item in merged.get("items", []) if str(item).strip()]
    seen = {
        key
        for item in items
        if (key := _canonical_synonym_term(_base_word(item))) is not None
    }
    source_urls = [str(url) for url in merged.get("source_urls", []) if str(url).strip()]
    source_labels: list[str] = []
    additions = 0

    for relation in sorted(relations, key=lambda item: int(item.get("vein") or 99)):
        item = _canonical_synonym_term(relation.get("item"))
        if not item:
            continue
        item_was_present = item in seen
        if not item_was_present:
            if additions >= _SYNONYM_ADDITION_CAP:
                continue
            seen.add(item)
            items.append(item)
            additions += 1
        label = _relation_source_label(relation, item)
        if label not in source_labels:
            source_labels.append(label)
        if relation.get("source_url") and relation["source_url"] not in source_urls:
            _append_relation_source_urls(merged, source_urls, relation)

    if not items:
        return None
    if source_labels:
        original = str(merged.get("source") or "").strip()
        merged["source"] = " + ".join(part for part in (original, *source_labels) if part)
    elif not merged.get("source"):
        merged["source"] = ""
    merged["items"] = items
    if source_urls:
        merged["source_urls"] = list(dict.fromkeys(source_urls))
    else:
        merged.pop("source_urls", None)
    return merged


def _merge_antonym_relations(
    existing: dict[str, Any] | None,
    relations: list[dict[str, Any]],
) -> dict[str, Any] | None:
    """Merge VESUM-gated antonym pointers into the rendered section schema."""
    merged = dict(existing or {})
    items = [str(item) for item in merged.get("items", []) if str(item).strip()]
    seen = {
        key
        for item in items
        if (key := _canonical_synonym_term(_base_word(item))) is not None
    }
    source_urls = [str(url) for url in merged.get("source_urls", []) if str(url).strip()]
    source_labels: list[str] = []
    additions = 0

    for relation in sorted(relations, key=lambda item: int(item.get("vein") or 99)):
        item = _canonical_synonym_term(relation.get("item"))
        if not item:
            continue
        item_was_present = item in seen
        if not item_was_present:
            if additions >= _ANTONYM_ADDITION_CAP:
                continue
            seen.add(item)
            items.append(item)
            additions += 1
        label = _relation_source_label(relation, item)
        if label not in source_labels:
            source_labels.append(label)
        if relation.get("source_url") and relation["source_url"] not in source_urls:
            _append_relation_source_urls(merged, source_urls, relation)

    if not items:
        return None
    if source_labels:
        original = str(merged.get("source") or "").strip()
        merged["source"] = " + ".join(part for part in (original, *source_labels) if part)
    elif not merged.get("source"):
        merged["source"] = ""
    merged["items"] = items
    if source_urls:
        merged["source_urls"] = list(dict.fromkeys(source_urls))
    else:
        merged.pop("source_urls", None)
    return merged


def _are_glosses_similar(g1: str, g2: str) -> bool:
    """Compare two glosses using case-insensitive SequenceMatcher ratio on normalized text and content token Jaccard similarity."""
    def clean(s: str) -> str:
        s = _strip_stress(s).lower()
        # Keep only alphanumeric characters and spaces
        s = "".join(c for c in s if c.isalnum() or c.isspace())
        return " ".join(s.split())

    c1 = clean(g1)
    c2 = clean(g2)
    if not c1 or not c2:
        return False
    if c1 == c2:
        return True

    # Check SequenceMatcher ratio
    from difflib import SequenceMatcher
    ratio = SequenceMatcher(None, c1, c2).ratio()
    if ratio < 0.85:
        return False

    # Check content-token Jaccard similarity
    # A small UA stopword set to be subtracted (grammatical particles, prepositions, conjunctions)
    # Structural words like 'сімейства', 'частина' stay (are NOT in this stopword set).
    ua_stopwords = {
        "і", "та", "й", "у", "в", "на", "за", "з", "із", "зі", "до",
        "для", "про", "без", "від", "через", "під", "над", "перед",
        "по", "при", "як", "що", "це", "о", "об", "а", "але", "чи", "бо"
    }

    t1 = set(c1.split()) - ua_stopwords
    t2 = set(c2.split()) - ua_stopwords

    jaccard = 0.0 if not t1 or not t2 else len(t1 & t2) / len(t1 | t2)
    return jaccard >= 0.5


def _merge_homonym_relations(
    existing: dict[str, Any] | None,
    relations: list[dict[str, Any]],
) -> dict[str, Any] | None:
    """Merge numbered and explicitly glossed corpus homonym relations."""
    # Note: 'existing' is always None in practice, so the seeding loop is omitted.
    merged = dict(existing or {})
    items: list[dict[str, Any]] = []
    seen: set[tuple[str, int | None, str]] = set()

    source_urls = [str(url) for url in merged.get("source_urls", []) if str(url).strip()]
    source_labels: list[str] = []
    additions = 0
    def relation_order(item: dict[str, Any]) -> tuple[int, int, str, str]:
        try:
            number = int(item.get("homonym_no"))
        except (TypeError, ValueError):
            number = 0
        try:
            vein = int(item.get("vein") or 99)
        except (TypeError, ValueError):
            vein = 99
        return (
            vein,
            number,
            str(item.get("gloss") or ""),
            str(item.get("source") or ""),
        )

    for relation in sorted(relations, key=relation_order):
        word = _canonical_synonym_term(relation.get("word"))
        try:
            number = int(relation.get("homonym_no"))
        except (TypeError, ValueError):
            number = None
        gloss = str(relation.get("gloss") or "").strip()
        pos = str(relation.get("pos") or "").strip()
        if not word or not gloss or (number is not None and (number < 1 or not pos)) or (number is None and pos):
            continue
        key = (word, number, gloss)

        # Check if we have already seen a similar gloss for this homonym word
        is_duplicate = False
        for seen_word, _, seen_gloss in seen:
            if seen_word == word and _are_glosses_similar(seen_gloss, gloss):
                is_duplicate = True
                break

        if not is_duplicate:
            if additions >= _HOMONYM_ADDITION_CAP:
                continue
            seen.add(key)
            item = {"word": word, "gloss": gloss}
            if number is not None:
                item["homonym_no"] = number
                item["pos"] = pos
            if relation.get("pattern") == "corpus relation pair":
                item["source"] = normalize_academic_label(str(relation.get("source") or ""))
            items.append(item)
            additions += 1

            label = (
                _relation_source_label(relation, word)
                if relation.get("pattern") == "corpus relation pair"
                else f"{relation['source']}: numbered homonym headwords"
            )
            if label not in source_labels:
                source_labels.append(label)
            if relation.get("source_url") and relation["source_url"] not in source_urls:
                _append_relation_source_urls(merged, source_urls, relation)

    if not items:
        return None
    if source_labels:
        original = str(merged.get("source") or "").strip()
        merged["source"] = " + ".join(part for part in (original, *source_labels) if part)
    elif not merged.get("source"):
        merged["source"] = ""
    merged["items"] = items
    if source_urls:
        merged["source_urls"] = list(dict.fromkeys(source_urls))
    else:
        merged.pop("source_urls", None)
    return merged


def _paronym_relation_source_label(relation: dict[str, Any]) -> str:
    """Record paronym provenance without conflating it with a distinction."""
    exam_provenance = str(relation.get("exam_provenance") or "").strip()
    if exam_provenance:
        return exam_provenance
    return f"{relation['source']}: {relation['pattern']}"


def _merge_paronym_relations(
    existing: dict[str, Any] | None,
    relations: list[dict[str, Any]],
) -> dict[str, Any] | None:
    """Merge ordered paronym pairs into the distinction-bearing rendered schema."""
    merged = dict(existing or {})
    items: list[dict[str, Any]] = []
    item_indexes: dict[str, int] = {}
    for raw_item in merged.get("items", []):
        if not isinstance(raw_item, dict):
            continue
        word = _canonical_synonym_term(raw_item.get("word"))
        if not word or word in item_indexes:
            continue
        item: dict[str, Any] = {"word": word}
        distinction = str(raw_item.get("distinction") or "").strip()
        if distinction:
            item["distinction"] = distinction
        provenance = raw_item.get("exam_provenance", [])
        if isinstance(provenance, str):
            provenance = [provenance]
        if isinstance(provenance, list):
            values = [str(value).strip() for value in provenance if str(value).strip()]
            if values:
                item["exam_provenance"] = list(dict.fromkeys(values))
        item_indexes[word] = len(items)
        items.append(item)

    source_urls = [str(url) for url in merged.get("source_urls", []) if str(url).strip()]
    source_labels: list[str] = []
    additions = 0
    for relation in sorted(
        relations,
        key=lambda item: (int(item.get("vein") or 99), str(item.get("word") or "")),
    ):
        word = _canonical_synonym_term(relation.get("word"))
        if not word:
            continue
        index = item_indexes.get(word)
        if index is None:
            if additions >= _PARONYM_ADDITION_CAP:
                continue
            index = len(items)
            item_indexes[word] = index
            items.append({"word": word})
            additions += 1
        item = items[index]
        distinction = str(relation.get("distinction") or "").strip()
        if distinction and not item.get("distinction"):
            item["distinction"] = distinction
        exam_provenance = str(relation.get("exam_provenance") or "").strip()
        if exam_provenance:
            values = item.setdefault("exam_provenance", [])
            if exam_provenance not in values:
                values.append(exam_provenance)
        label = _paronym_relation_source_label(relation)
        if label not in source_labels:
            source_labels.append(label)
        if relation.get("source_url") and relation["source_url"] not in source_urls:
            _append_relation_source_urls(merged, source_urls, relation)

    if not items:
        return None
    if source_labels:
        original = str(merged.get("source") or "").strip()
        merged["source"] = " + ".join(part for part in (original, *source_labels) if part)
    elif not merged.get("source"):
        merged["source"] = ""
    merged["items"] = items
    if source_urls:
        merged["source_urls"] = list(dict.fromkeys(source_urls))
    else:
        merged.pop("source_urls", None)
    return merged


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


# Decolonization guard (#M-13 / .claude/rules/ukrainian-linguistics.md §1,§6): a Ukrainian etymology
# must never be framed via Russian/Belarusian comparison. "Old East Slavic" / "East Slavic" are the
# correct decolonized terms and contain neither marker, so they pass; a "Compare Russian …" /
# "Belarusian …" Kaikki etymology is rejected (section falls to honestly `uncovered`) rather than
# surfaced with imperial framing.
_KAIKKI_IMPERIAL_COMPARISON_RE = re.compile(
    # English base country names, adjectives, and plurals (Russia/Russian/Russians, Belarus/…),
    r"\b(Russia|Russian|Russians|Belarus|Belarusian|Belarusians|Belorussia|Belorussian|Byelorussia|Byelorussian)\b"
    # plus embedded Cyrillic imperial references (Kaikki etymology prose often embeds them, e.g.
    # рф → "Російська Федерація"). Word-anchored (\b) so it does NOT false-positive on Амвросій
    # (Ambrose) or on legitimate Moscow-referent words (москва/москвич), which carry honest
    # compositional etymologies rather than imperial framing of a Ukrainian concept.
    r"|\b(росі[яюїє]|російськ|росіян|малоросі|рф|білорус)",
    re.IGNORECASE,
)


def _kaikki_etymology_is_decolonized(text: str) -> bool:
    return not _KAIKKI_IMPERIAL_COMPARISON_RE.search(text)


def _kaikki_etymology(lookup: dict[str, dict[str, Any]], lemma: str) -> dict | None:
    row = _kaikki_row(lookup, lemma)
    if not row:
        return None
    text = clean_html_entities(str(row.get("etymology_text") or "").strip()[:600])
    if not _kaikki_etymology_text_is_usable(text):
        return None
    if not _kaikki_etymology_is_decolonized(text):
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


def _mphdict_etymology(lemma: str) -> dict[str, Any] | None:
    """Adapt the rich mphdict root query to the compact Atlas etymology block."""
    result = mphdict_etymology(lemma)
    if not result:
        return None
    roots = result.get("roots")
    if not isinstance(roots, list) or not roots:
        return None
    root = roots[0]
    if not isinstance(root, dict):
        return None
    citation = root.get("citation")
    citation_display = citation.get("display") if isinstance(citation, dict) else ""
    source = ESUM_LABEL
    if citation_display:
        source = f"{source}, {citation_display}"
    etymons = root.get("etymons")
    headword = ""
    etymon_count = 0
    if isinstance(etymons, list):
        etymon_count = len(etymons)
        for etymon in etymons:
            if isinstance(etymon, dict) and etymon.get("is_head"):
                headword = str(etymon.get("stressed") or etymon.get("lemma") or "").strip()
                break
    match = root.get("match")
    direct_headword = isinstance(match, dict) and bool(match.get("is_direct_headword"))
    article_kind = "Стаття ЕСУМ" if direct_headword else "Зіставлення у статті ЕСУМ"
    label = f"{article_kind}: {headword or lemma}; етимонів: {etymon_count}."
    return {
        "text": label,
        "source": source,
        "mphdict_root": {
            "id": root.get("id"),
            "match": root.get("match"),
            "citation": citation,
            "bibliography": root.get("bibliography", []),
        },
    }


def _with_base_etymology_label(etymology: dict, base_form: str) -> dict:
    labeled = dict(etymology)
    source = str(labeled.get("source") or "").strip()
    label = f"etymology of base form {base_form}"
    labeled["source"] = f"{source} ({label})" if source else label
    return labeled


def _etymology(
    conn: sqlite3.Connection, lemma: str, kaikki_lookup: dict[str, dict[str, Any]] | None = None
) -> dict | None:
    """ЕСУМ etymology from offline mphdict (primary, authoritative); falls back to a decolonized,
    source-marked Kaikki/Wiktionary etymology for lemmas mphdict lacks (Option C, #5263). The Горох
    mirror and the legacy ЕСУМ FTS table stay OFF (mirror labels banned; ЕСУМ redundant with mphdict)."""
    lookup_word = _lookup_key(_base_lemma(lemma))
    if lookup_word in _COMPOSITIONAL_ETYMOLOGY_EXCLUSIONS:
        return None
    return _mphdict_etymology(lemma) or _kaikki_etymology(kaikki_lookup or {}, lemma)


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
    "г",
    "гірн",
    "грам",
    "діал",
    "див",
    "док",
    "ек",
    "ел",
    "жарт",
    "збірн",
    "зоол",
    "інформ",
    "іст",
    "комп",
    "кул",
    "лінгв",
    "мат",
    "мед",
    "мет",
    "мін",
    "мн",
    "мор",
    "муз",
    "недок",
    "невідм",
    "перен",
    "побут",
    "поет",
    "політ",
    "прийм",
    "род",
    "розм",
    "с",
    "спец",
    "спорт",
    "тех",
    "текст",
    "тж",
    "тк",
    "фіз",
    "фізіол",
    "філол",
    "філос",
    "хім",
    "церк",
    "відм",
    "в",
    "спол",
    "лит",
}


def _ukreng_strip_aspect_prefix(body: str) -> str:
    """Remove leading imperfective/perfective aspect pair(s) from ukreng body text."""
    return re.sub(
        r"^недок\.\s+.+?,\s+док\.\s+(?:\S+(?:,\s+\S+)*)?\s*",
        "",
        body,
        count=1,
        flags=re.IGNORECASE,
    )


def _ukreng_prefix_lemma_tokens(lemma: str) -> set[str]:
    return {_strip_stress(variant).casefold() for variant in _split_lemma_variants(lemma) if variant}


def _ukreng_prefix_is_label(prefix: str, *, lemma: str = "") -> bool:
    """Return True when Cyrillic text before the English gloss is label-only."""
    cleaned = re.sub(r"\([^)]*\)", " ", prefix)
    if "див." in cleaned.casefold():
        cleaned = re.sub(r"^.*?див\.\s*", " ", cleaned, count=1, flags=re.IGNORECASE)
        cleaned = re.sub(r"^[^—–-]+(?:[—–-]\s*)?", " ", cleaned, count=1)
    cleaned = re.sub(r"^в\s+спол\.\s+\S+(?:\s+як\s*)?", " ", cleaned, flags=re.IGNORECASE)
    words = re.findall(r"[А-Яа-яЄєІіЇїҐґ]+|\d+", cleaned.casefold())
    skip = _ukreng_prefix_lemma_tokens(lemma)
    words = [word for word in words if word not in skip]
    if not words:
        return True
    return all(word in _SLOVNYK_UKRENG_PREFIX_LABELS or word.isdigit() for word in words)


def _slovnyk_ukreng_body_chunks(body: str) -> list[str]:
    """Split ukreng body text into sense-sized chunks in deterministic order."""
    chunks: list[str] = []
    aspect_stripped = _ukreng_strip_aspect_prefix(body)
    for part in re.split(r";|\n", aspect_stripped):
        part = part.strip()
        if not part:
            continue
        for sense in re.split(r"(?<=\))\s*(?=\d+\))", part):
            sense = sense.strip()
            if sense:
                chunks.append(sense)
    return chunks


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
    for chunk in _slovnyk_ukreng_body_chunks(body):
        chunk = re.sub(r"^\s*\d+\)?\.?\s*", "", chunk.strip())
        if not chunk:
            continue
        first_latin = _LATIN_RE.search(chunk)
        if not first_latin or not _ukreng_prefix_is_label(chunk[: first_latin.start()], lemma=lemma):
            continue
        english_part = chunk[first_latin.start() :]
        first_cyrillic = re.search(r"[А-Яа-яЄєІіЇїҐґ]", english_part)
        if first_cyrillic:
            english_part = english_part[: first_cyrillic.start()]
        english_part = re.sub(r"\([^)]*\)", " ", english_part)
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
    mirror_url = str(row.get("source_url") or "").strip()
    attach_official_url(block, mirror_url=mirror_url, slug=_SLOVNYK_UKRENG_SLUG, word=lemma)
    return block


def _entry_has_learner_english_anchor(entry: dict[str, Any]) -> bool:
    gloss = entry.get("gloss")
    if isinstance(gloss, str) and gloss.strip():
        return True
    enrichment = entry.get("enrichment")
    if not isinstance(enrichment, dict):
        return False
    translation = enrichment.get("translation")
    if isinstance(translation, dict):
        terms = translation.get("en")
        if isinstance(terms, list) and any(isinstance(term, str) and term.strip() for term in terms):
            return True
    meaning = enrichment.get("meaning")
    if isinstance(meaning, dict) and meaning.get("source") == KAIKKI_SOURCE:
        definitions = meaning.get("definitions")
        if isinstance(definitions, list) and any(isinstance(item, str) and item.strip() for item in definitions):
            return True
    return False


def _fill_learner_english_anchor_from_slovnyk_cache(
    entry: dict[str, Any],
    lemma: str,
    slovnyk_cache: dict[str, Any] | None,
) -> bool:
    """Fill a missing learner English anchor from a cached slovnyk ukreng row (#4515).

    Offline-safe (#5114): only rows with cached ``text`` are consulted; never
    live-fetch or invent a gloss.
    """
    if _entry_has_learner_english_anchor(entry):
        return False
    row = _cache_lookup(slovnyk_cache, _SLOVNYK_UKRENG_SLUG)
    if not row:
        return False
    glosses = _slovnyk_ukreng_glosses(row, lemma)
    if not glosses:
        return False
    translation: dict[str, object] = {
        "en": glosses,
        "source": _SLOVNYK_UKRENG_SOURCE,
    }
    mirror_url = str(row.get("source_url") or "").strip()
    attach_official_url(translation, mirror_url=mirror_url, slug=_SLOVNYK_UKRENG_SLUG, word=lemma)
    enrichment = entry.get("enrichment")
    if not isinstance(enrichment, dict):
        enrichment = {}
        entry["enrichment"] = enrichment
    enrichment["translation"] = translation
    sources = set(enrichment.get("sources") or [])
    sources.add(_SLOVNYK_UKRENG_SOURCE)
    enrichment["sources"] = sorted(sources)
    return True


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


# --- #5077 preserve-vs-retract section semantics ---------------------------------
# enrich_entry recomputes gated sections from scratch each run. Offline (or after a
# schema-version cache reset, or a transient lookup error) a gate that CANNOT run
# returns empty and silently overwrites the previously-confirmed published section
# (809 stripped + 1,748 shrunk on the 2026-07-13 8,552 go-live). The contract below
# distinguishes THREE outcomes per section so a gate that did not run preserves the
# existing content while a gate that ran keeps its authoritative retractions.


def _section_item_key(item: object) -> str | None:
    """Canonical identity for one rendered section item (string chip or relation dict).

    Synonym/antonym chips are strings, optionally ``"word (qualifier)"``; homonym,
    paronym and idiom items are dicts. The qualifier is stripped so a purely cosmetic
    re-tag (``дорога (діал.)`` -> ``дорога``) is not counted as a lost item. The bare
    term is then run through the same canonicalization as synonym terms
    (``_strip_stress`` then ``_lookup_key`` apostrophe folding + whitespace collapse +
    strip + casefold) so a difference only in stress marks (``мали́й``/``малий``) or
    apostrophe style (``бабу’ся``/``бабу'ся``) never splits one member into two keys.
    """
    if isinstance(item, str):
        return _lookup_key(_strip_stress(_base_word(item))) or None
    if isinstance(item, dict):
        for field in ("word", "target", "lemma", "phrase", "text", "definition"):
            value = item.get(field)
            if isinstance(value, str) and value.strip():
                return _lookup_key(_strip_stress(_base_word(value))) or None
    return None


def _section_item_keys(section: object) -> set[str]:
    if not isinstance(section, dict):
        return set()
    keys: set[str] = set()
    for item in section.get("items") or []:
        key = _section_item_key(item)
        if key:
            keys.add(key)
    return keys


def _section_loses_items(existing: object, new: object) -> bool:
    """True iff a confirmed item present in ``existing`` is absent from ``new``."""
    return bool(_section_item_keys(existing) - _section_item_keys(new))


def _slovnyk_gate_ran(cache: dict[str, Any] | None, slugs: Sequence[str]) -> bool:
    """Whether the slovnyk.me gate for a section depending on ``slugs`` could
    consult its data source this run (#5077).

    Online the live source is always fetched, so the gate ran. Offline it ran only
    if the per-lemma cache already holds at least one of the section's OWN slugs —
    a lemma whose cache is missing every relevant slug (schema reset, never fetched)
    is one the offline gate could NOT consult, so its section must be preserved.

    Per-slug is load-bearing (#5077 review finding 1): a generic ``bool(lookups)``
    treats a partial cache holding only unrelated slugs (e.g. the davydov warning
    slug) as "the synonym gate ran" and lets it retract a section its source was
    never consulted for. The gate ran for a section only when the section's own
    source is present.
    """
    if not _phase1_offline_mode():
        return True
    return any(_cache_has_lookup(cache, slug) for slug in slugs)


def _resolve_gated_section(
    new_section: dict[str, Any] | None,
    existing_section: dict[str, Any] | None,
    *,
    gate_ran: bool,
) -> tuple[dict[str, Any] | None, str | None]:
    """Apply the #5077 preserve-vs-retract contract to one gated section.

    Three explicitly-distinguished outcomes:
      * gate ran, no confirmed item lost   -> ran-and-confirmed: take the new section
        (additions welcome); no provenance marker (default, keeps the diff minimal).
      * gate ran, confirmed item(s) dropped -> ran-and-rejected: the retraction is
        authoritative (for example, a rejected cross-sense legacy relation); take
        the new section (may be ``None`` when everything was retracted); mark ``rejected``.
      * gate did NOT run -> did-not-run: never retract a confirmed item (PRESERVE the
        existing section when the recomputation would drop one), and ALWAYS mark
        ``skipped-offline`` so the audit trail records the non-consultation, not only
        the losses (#5077 review finding 4).

    Returns ``(section_or_None, provenance_or_None)``.
    """
    loses = _section_loses_items(existing_section, new_section)
    if gate_ran:
        return new_section, (GATE_REJECTED if loses else None)
    resolved = existing_section if loses else (new_section or existing_section)
    return resolved, (GATE_SKIPPED_OFFLINE if resolved else None)


# #5121 — antonym pointer ANNOTATIONS (the СУМ-20/ВТС "протилежне → X" source segments
# plus their source_urls) come from the per-lemma slovnyk cache slugs below. Item
# MEMBERSHIP is Вікісловник + local-db and offline-safe, so its gate always runs; the
# annotation augmentation is NOT — an offline run with a cold cache recomputes the same
# items without their published annotation pointers. This is the #5077 preserve contract
# applied one level down, at annotation granularity, with membership left untouched.
_SLOVNYK_ANTONYM_ANNOTATION_SLUGS = ("newsum", "vts")


def _annotation_segment_item(segment: str) -> str | None:
    """Canonical item a rendered pointer-annotation ``source`` segment points at.

    Pointer segments render as ``"<dict>: <pattern> → <item>[ (reciprocal)][ [gate: …]]"``
    (see :func:`_relation_source_label`). The base Вікісловник label carries no ``→`` and
    is not a pointer annotation, so it returns ``None`` — only per-item pointer segments
    are carry-over candidates.
    """
    marker = " → "
    idx = segment.rfind(marker)
    if idx == -1:
        return None
    tail = segment[idx + len(marker) :]
    for cut in (" (reciprocal)", " [gate:"):
        pos = tail.find(cut)
        if pos != -1:
            tail = tail[:pos]
    # Key it exactly as _section_item_keys keys the rendered items so both sides of the
    # membership match normalize identically (base word, stress-stripped, casefolded).
    return _section_item_key(tail.strip())


def _carry_over_pointer_annotations(
    new_section: dict[str, Any] | None,
    baseline_section: dict[str, Any] | None,
    *,
    gate_ran: bool,
) -> tuple[dict[str, Any] | None, str | None]:
    """Carry a baseline section's pointer annotations forward when the annotation
    source could not be consulted this run (#5121).

    Item MEMBERSHIP is untouched — ``new_section`` already holds the offline-safe items
    computed from local sources. Only the secondary annotation layer is restored, and only
    per-item: a baseline pointer segment is carried iff its item survives in ``new_section``
    (match by canonical term), so an item absent from the baseline gains no phantom
    annotation. Returns ``(section, provenance_or_None)``; provenance is ``None`` whenever
    nothing was carried, keeping a normal run's diff minimal.
    """
    if gate_ran or not new_section or not isinstance(baseline_section, dict):
        return new_section, None
    new_keys = _section_item_keys(new_section)
    existing_segments = {
        seg.strip()
        for seg in str(new_section.get("source") or "").split(" + ")
        if seg.strip()
    }
    carried_segments: list[str] = []
    for raw in str(baseline_section.get("source") or "").split(" + "):
        seg = raw.strip()
        if not seg or seg in existing_segments or seg in carried_segments:
            continue
        item_key = _annotation_segment_item(seg)
        if item_key is None or item_key not in new_keys:
            continue  # base label, or a pointer at a non-member item — no phantom carry
        carried_segments.append(seg)
    if not carried_segments:
        return new_section, None
    resolved = dict(new_section)
    base_source = str(resolved.get("source") or "").strip()
    resolved["source"] = " + ".join(part for part in (base_source, *carried_segments) if part)
    # source_urls are per-(dictionary, lemma), shared across a source's items, not per-item;
    # membership is protected so every carried item's source survives — carry the baseline
    # annotation URLs the fresh recompute lacks (its own Вікісловник URL already dedups out).
    urls = [str(url) for url in resolved.get("source_urls", []) if str(url).strip()]
    for raw_url in baseline_section.get("source_urls") or []:
        url = str(raw_url).strip()
        if url and url not in urls:
            urls.append(url)
    if urls:
        resolved["source_urls"] = list(dict.fromkeys(urls))
    return resolved, GATE_ANNOTATIONS_CARRIED


def _ordered_sections(
    sections: dict[str, object], baseline: dict[str, Any]
) -> dict[str, object]:
    """Emit sections in the baseline manifest's key order so a pure-preserve run
    serializes byte-identical to its baseline (#5077 review finding 3).

    The recompute rebuilds ``sections`` in a fixed apply order (synonyms, antonyms,
    homonyms, paronyms, idioms). When the entry already had published sections in a
    different order, that reorder alone produced spurious byte diffs on runs that
    changed nothing. Keys present in the baseline keep the baseline's order; keys new
    to this entry follow in canonical apply order.
    """
    ordered: dict[str, object] = {}
    for name in baseline:
        if name in sections:
            ordered[name] = sections[name]
    for name, value in sections.items():
        if name not in ordered:
            ordered[name] = value
    return ordered


def enrich_entry(
    entry,
    conn,
    kaikki_lookup,
    *,
    has_sum11_flags,
    pointer_synonym_relations: list[dict[str, Any]] | None = None,
    pointer_antonym_relations: list[dict[str, Any]] | None = None,
    pointer_homonym_relations: list[dict[str, Any]] | None = None,
    pointer_paronym_relations: list[dict[str, Any]] | None = None,
) -> bool:
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
    # #5077: the hydrated/published sections are the preserve baseline. Capture them
    # BEFORE recomputing so a gate that did not run can restore its confirmed content
    # instead of silently overwriting it with an offline-empty recomputation.
    existing_sections = entry.get("sections")
    baseline_sections = existing_sections if isinstance(existing_sections, dict) else {}
    # mphdict synonym groups are a local primary source.  A missing database is
    # the only did-not-run state; a present database with no matching set is an
    # authoritative empty result and may retract stale legacy chips.
    synonyms_gate_ran = mphdict_synonyms_available()
    idioms_gate_ran = _slovnyk_gate_ran(slovnyk_cache, _SLOVNYK_IDIOM_SLUGS)
    sections: dict[str, object] = {}
    gate_provenance: dict[str, str] = {}

    def _apply_section(name: str, new_section: dict[str, Any] | None, *, gate_ran: bool) -> None:
        resolved, outcome = _resolve_gated_section(
            new_section, baseline_sections.get(name), gate_ran=gate_ran
        )
        if resolved:
            sections[name] = resolved
        if outcome:
            gate_provenance[name] = outcome

    synonyms = _synonyms_mphdict(base)
    if not synonyms and fallback_base:
        synonyms = _synonyms_mphdict(fallback_base)
        if synonyms:
            synonyms = _with_base_source_label(synonyms, fallback_base)
    _apply_section("synonyms", synonyms, gate_ran=synonyms_gate_ran)
    antonyms = _antonyms_wiktionary(conn, base, entry_pos=entry_pos)
    if not antonyms and fallback_base:
        antonyms = _antonyms_wiktionary(conn, fallback_base, entry_pos=entry_pos)
        if antonyms:
            antonyms = _with_base_source_label(antonyms, fallback_base)
    antonym_relations = (
        pointer_antonym_relations
        if pointer_antonym_relations is not None
        else _definition_antonym_relations(
            conn,
            lemma,
            has_sum11_flags=has_sum11_flags,
            cache=slovnyk_cache,
        )
    )
    antonyms = _merge_antonym_relations(antonyms, antonym_relations)
    # #5121: item membership is Вікісловник + local-db (offline-safe, gate always runs),
    # but the СУМ-20/ВТС pointer ANNOTATIONS ride the per-lemma slovnyk cache. When that
    # cache could not be consulted (offline + no newsum/vts slug), carry the published
    # pointer annotations forward per-item rather than silently dropping them; online or
    # cache-present the fresh recompute wins and nothing is carried.
    antonym_annotation_gate_ran = _slovnyk_gate_ran(
        slovnyk_cache, _SLOVNYK_ANTONYM_ANNOTATION_SLUGS
    )
    antonyms, antonym_annotation_outcome = _carry_over_pointer_annotations(
        antonyms, baseline_sections.get("antonyms"), gate_ran=antonym_annotation_gate_ran
    )
    # Antonyms are Вікісловник + lexicographer-pointer driven (local db); the membership
    # gate always runs, so authoritative local retractions apply even offline (finding 2).
    _apply_section("antonyms", antonyms, gate_ran=True)
    if antonym_annotation_outcome and "antonyms" in sections:
        # Distinct key so the annotation carry-over sits ALONGSIDE the membership outcome
        # and stays invisible to the item-count shrink gate (which reads real section names).
        gate_provenance["antonyms_annotations"] = antonym_annotation_outcome
    homonym_relations = (
        pointer_homonym_relations
        if pointer_homonym_relations is not None
        else _homonym_relations(
            conn,
            lemma,
            cache=slovnyk_cache,
        )
    )
    homonyms = _merge_homonym_relations(None, homonym_relations)
    # Homonyms come from СУМ numbering + approved corpus relation pairs (local db); the
    # gate always runs, so an offline run updates from local data (finding 2).
    _apply_section("homonyms", homonyms, gate_ran=True)
    paronym_relations = (
        pointer_paronym_relations
        if pointer_paronym_relations is not None
        else _paronym_relations(conn, lemma)
    )
    paronyms = _merge_paronym_relations(None, paronym_relations)
    # Paronyms come from local ZNO/cache pairs only (no slovnyk.me), so their gate runs
    # fully offline — retractions here are always authoritative.
    _apply_section("paronyms", paronyms, gate_ran=True)
    idioms = _idioms(conn, lemma, slovnyk_cache)
    _apply_section("idioms", idioms, gate_ran=idioms_gate_ran)
    if sections:
        entry["sections"] = _ordered_sections(sections, baseline_sections)
    else:
        entry.pop("sections", None)
    # gate_provenance is a CURRENT-RUN snapshot: it replaces any prior map wholesale so
    # each field reflects this run's consultation status (rejected / skipped-offline),
    # which is exactly the signal the verify_manifest shrink gate reads. It is not a
    # history log — a section confirmed this run drops its stale prior marker by design
    # (#5077 review finding 4; replacement chosen over a `previous` key for the smaller
    # diff and because the shrink gate only ever consults the current status).
    if gate_provenance:
        entry["gate_provenance"] = gate_provenance
    else:
        entry.pop("gate_provenance", None)
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

    filled_anchor = _fill_learner_english_anchor_from_slovnyk_cache(entry, lemma, slovnyk_cache)

    wiki_ref = _wiki_reference(lemma, block.get("literary_attestation"))
    if wiki_ref:
        entry["wiki_reference"] = wiki_ref
    else:
        entry.pop("wiki_reference", None)

    return bool(block or sections or pronunciation or wiki_ref or filled_anchor)


def enrich() -> tuple[int, int]:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    _normalize_manifest_entries(manifest)
    kaikki_lookup = _load_kaikki_lookup()
    # Reviewed synonym verdicts are first-class corpus facts for the manifest,
    # not an atlas.db-only projection. This import never promotes mined
    # candidates: it writes only YAML ``approved`` verdict rows with dedicated
    # provenance before the read-only enrichment pass.
    load_approved_synonym_verdicts(SOURCES_DB)
    conn = sqlite3.connect(f"file:{SOURCES_DB}?mode=ro", uri=True)
    enriched = 0
    try:
        has_sum11_flags = _sum11_has_flag_columns(conn)
        _prepare_cefr_estimates(conn, manifest)
        pointer_synonym_relations = _definition_pointer_relations_by_headword(
            conn,
            manifest,
            has_sum11_flags=has_sum11_flags,
        )
        pointer_antonym_relations = _definition_antonym_relations_by_headword(
            conn,
            manifest,
            has_sum11_flags=has_sum11_flags,
        )
        pointer_homonym_relations = _homonym_relations_by_headword(conn, manifest)
        pointer_paronym_relations = _paronym_relations_by_headword(conn, manifest)
        corpus_relations = _corpus_relation_pairs_by_headword(conn, manifest)
        for entry in manifest["entries"]:
            entry_key = _canonical_synonym_term(str(entry.get("lemma") or ""))
            corpus_for_entry = corpus_relations.get(entry_key or "", {})
            if enrich_entry(
                entry,
                conn,
                kaikki_lookup,
                has_sum11_flags=has_sum11_flags,
                pointer_synonym_relations=[
                    *pointer_synonym_relations.get(entry_key or "", []),
                    *corpus_for_entry.get("synonym", []),
                ],
                pointer_antonym_relations=[
                    *pointer_antonym_relations.get(entry_key or "", []),
                    *corpus_for_entry.get("antonym", []),
                ],
                pointer_homonym_relations=[
                    *pointer_homonym_relations.get(entry_key or "", []),
                    *corpus_for_entry.get("homonym", []),
                ],
                pointer_paronym_relations=[
                    *pointer_paronym_relations.get(entry_key or "", []),
                    *corpus_for_entry.get("paronym", []),
                ],
            ):
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
