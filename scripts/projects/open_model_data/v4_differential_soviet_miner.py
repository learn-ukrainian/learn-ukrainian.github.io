#!/usr/bin/env python3
"""ULDR Phase 3.4: Differential Soviet Candidate Miner & Modern Whitelist Filter (Issue #8008).

Contrasts Soviet СУМ-11 entries flagged under `sovietization_risk > 0` against
pre-Soviet 1920s Academy dictionaries (R2U) and modern standards, equipped with
an explicit 20th-century modern neologism whitelist and robust network error disambiguation.
"""

from __future__ import annotations

import argparse
import datetime
import enum
import hashlib
import json
import re
import sqlite3
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def resolve_data_path(rel_path: str) -> Path:
    """Resolve a relative data path, falling back to git common parent checkout for gitignored files."""
    local_p = REPO_ROOT / rel_path
    if local_p.exists() and local_p.stat().st_size > 0:
        return local_p
    try:
        common = subprocess.check_output(
            ["git", "rev-parse", "--git-common-dir"],
            cwd=REPO_ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
            timeout=30,
        ).strip()
        main_p = Path(common).resolve().parent / rel_path
        if main_p.exists() and main_p.stat().st_size > 0:
            return main_p
    except Exception:
        pass
    return local_p


DEFAULT_SOURCES_DB = resolve_data_path("data/sources.db")
DEFAULT_VESUM_DB = resolve_data_path("data/vesum.db")
DEFAULT_OUTPUT_DIR = REPO_ROOT / "data" / "projects" / "open_model_data" / "soviet_candidates"
DEFAULT_R2U_CACHE = resolve_data_path("data/projects/open_model_data/soviet_candidates/r2u_differential_cache.json")
CANDIDATE_SCHEMA = REPO_ROOT / "data" / "projects" / "open_model_data" / "contracts" / "v1_differential_soviet_candidate.schema.json"
RECEIPT_SCHEMA = REPO_ROOT / "data" / "projects" / "open_model_data" / "contracts" / "v1_differential_soviet_receipt.schema.json"

TOTAL_SUM11_RISK_POOL = 7152

# Security regex: forbid private developer environments in public artifacts
PRIVATE_HOST_RE = re.compile(r"(?:/home/(?:ops|ubuntu)|/Users/|[\d]{1,3}\.[\d]{1,3}\.[\d]{1,3}\.[\d]{1,3})")


class R2ULookupStatus(enum.StrEnum):
    FOUND = "found"
    NOT_FOUND = "not_found"
    NOT_FOUND_WITHIN_VERIFIED_COVERAGE = "not_found_within_verified_coverage"
    SOURCE_UNAVAILABLE = "source_unavailable"
    CACHED = "cached"
    NOT_QUERIED = "not_queried"


class AdjudicationStatus(enum.StrEnum):
    CANDIDATE_ADMITTED = "CANDIDATE_ADMITTED"
    WHITELIST_PRESERVED = "WHITELIST_PRESERVED"
    IDEOLOGICAL_HISTORICAL_ONLY = "IDEOLOGICAL_HISTORICAL_ONLY"
    SKRYPNYKIVKA_ARCHAISM_REJECTED = "SKRYPNYKIVKA_ARCHAISM_REJECTED"
    UNVERIFIED_EXCLUDED = "UNVERIFIED_EXCLUDED"


class AdjudicationCategory(enum.StrEnum):
    LEXICAL_CALQUE = "lexical_calque"
    SYNTACTIC_CALQUE = "syntactic_calque"
    SOVIET_REALIA_IDEOLOGY = "soviet_realia_ideology"
    MODERN_NEOLOGISM_TECHNICAL = "modern_neologism_technical"
    MODERN_INTERNATIONALISM = "modern_internationalism"
    SKRYPNYKIVKA_ARCHAISM = "skrypnykivka_archaism"
    STANDARD_UKRAINIAN_PRESERVED = "standard_ukrainian_preserved"


# 20th-Century Modern Technical, Scientific & Computing Neologisms coined after 1930
# Absence from 1920s R2U is normal and MUST NOT trigger a calque flag.
MODERN_20TH_CENTURY_WHITELIST: frozenset[str] = frozenset(
    {
        # Computing, IT & Cybernetics
        "програмування",
        "програміст",
        "програмувальний",
        "комп'ютер",
        "комп'ютерний",
        "транзистор",
        "інтернет",
        "кібернетика",
        "кібернетичний",
        "інформатика",
        "інформатичний",
        "алгоритм",
        "мікросхема",
        "напівпровідник",
        "дисплей",
        "піксель",
        "процесор",
        "мікропроцесор",
        "ноутбук",
        "сервер",
        "байт",
        "кілобайт",
        "мегабайт",
        "гігабайт",
        "дискета",
        "флешка",
        "онлайн",
        "софт",
        "файл",
        "інтерфейс",
        "база даних",
        "еом",
        # Aviation, Aerospace, Space & Radar
        "авіація",
        "авіаційний",
        "космонавт",
        "астронавт",
        "космонавтика",
        "космонавтичний",
        "ракета",
        "ракетобудування",
        "супутник",
        "вертоліт",
        "гелікоптер",
        "радар",
        "радіолокація",
        "радіолокаційний",
        "радіозв'язок",
        "надзвуковий",
        "стратосфера",
        "космодром",
        "космоліт",
        "місяцехід",
        # Modern Chemistry, Physics, Materials & Nuclear
        "пластмаса",
        "пластмасовий",
        "полімер",
        "полімерний",
        "поліетилен",
        "нейлон",
        "нейлоновий",
        "тефлон",
        "лазер",
        "лазерний",
        "мазер",
        "синтетика",
        "синтетичний",
        "ізотоп",
        "радіоактивність",
        "квантовий",
        "атомний",
        "ядерний",
        "термоядерний",
        "електронний",
        "фотон",
        "нейтрон",
        "протон",
        "позитрон",
        "електроніка",
        # Modern Medicine, Genetics & Biochemistry
        "антибіотик",
        "пеніцилін",
        "стрептоміцин",
        "вітамін",
        "вітамінний",
        "вітамінологія",
        "вітамінолог",
        "ген",
        "генетика",
        "генетичний",
        "днк",
        "рнк",
        "вірус",
        "вірусний",
        "імунітет",
        "імунний",
        "вакцинація",
        "хіміотерапія",
        "кардіограма",
        "ехографія",
        "кардіостимулятор",
        "узд",
        "мрт",
        # Telecommunications & Electronics
        "телебачення",
        "телевізор",
        "телевізійний",
        "радіо",
        "радіомовлення",
        "радіотехніка",
        "радіотехнічний",
        "радіоустановка",
        "відео",
        "відеомагнітофон",
        "відеокамера",
        "магнітофон",
        "трансляція",
        "стереосистема",
        "стереофонія",
        "стереофонічний",
        "стереозвук",
        "мобільний",
        "смартфон",
    }
)

# Obsolete 1920s Skrypnykivka-only archaisms that must NOT be forced as living modern replacements
SKRYPNYKIVKA_ARCHAISMS: frozenset[str] = frozenset(
    {
        "рівнобіжник",
        "терпуг",
        "прямовис",
        "довгокутник",
        "дрібножил",
        "пружніший",
        "живе срібло",
        "саморух",
        "самохід",
        "кружало",
    }
)

# Authentic living Ukrainian alternatives to verified Soviet/Russian calques
AUTHENTIC_SOVIET_CALQUE_REPLACEMENTS: dict[str, dict[str, Any]] = {
    "діючий": {
        "replacement": "чинний",
        "category": AdjudicationCategory.LEXICAL_CALQUE,
        "source": "Antonenko-Davydovych, §12 (active participles)",
    },
    "подавляючий": {
        "replacement": "переважний",
        "category": AdjudicationCategory.LEXICAL_CALQUE,
        "source": "Antonenko-Davydovych, §12",
    },
    "співпадати": {
        "replacement": "збігатися",
        "category": AdjudicationCategory.LEXICAL_CALQUE,
        "source": "Antonenko-Davydovych, §10",
    },
    "приймати участь": {
        "replacement": "брати участь",
        "category": AdjudicationCategory.SYNTACTIC_CALQUE,
        "source": "Antonenko-Davydovych, §3",
    },
    "по крайній мірі": {
        "replacement": "принаймні",
        "category": AdjudicationCategory.SYNTACTIC_CALQUE,
        "source": "Antonenko-Davydovych, §7",
    },
    "по мірі того як": {
        "replacement": "у міру того як",
        "category": AdjudicationCategory.SYNTACTIC_CALQUE,
        "source": "Pravopys 2019, §38",
    },
    "по ініціативі": {
        "replacement": "за ініціативою",
        "category": AdjudicationCategory.SYNTACTIC_CALQUE,
        "source": "Antonenko-Davydovych, §5",
    },
    "на рахунок": {
        "replacement": "щодо",
        "category": AdjudicationCategory.SYNTACTIC_CALQUE,
        "source": "Antonenko-Davydovych, §8",
    },
    "слідуючий": {
        "replacement": "наступний",
        "category": AdjudicationCategory.LEXICAL_CALQUE,
        "source": "Antonenko-Davydovych, §12",
    },
    "у крайньому випадку": {
        "replacement": "у крайньому разі",
        "category": AdjudicationCategory.SYNTACTIC_CALQUE,
        "source": "Antonenko-Davydovych, §7",
    },
    "бути правим": {
        "replacement": "мати рацію",
        "category": AdjudicationCategory.SYNTACTIC_CALQUE,
        "source": "Antonenko-Davydovych, §9",
    },
    "мати місце": {
        "replacement": "відбуватися",
        "category": AdjudicationCategory.SYNTACTIC_CALQUE,
        "source": "Antonenko-Davydovych, §9",
    },
    "впадати в очі": {
        "replacement": "впадати в око",
        "category": AdjudicationCategory.SYNTACTIC_CALQUE,
        "source": "Antonenko-Davydovych, §11",
    },
    "в першу чергу": {
        "replacement": "насамперед",
        "category": AdjudicationCategory.SYNTACTIC_CALQUE,
        "source": "Antonenko-Davydovych, §7",
    },
    "за рахунок": {
        "replacement": "коштом",
        "category": AdjudicationCategory.SYNTACTIC_CALQUE,
        "source": "Antonenko-Davydovych, §8",
    },
    "підняти питання": {
        "replacement": "порушити питання",
        "category": AdjudicationCategory.SYNTACTIC_CALQUE,
        "source": "Antonenko-Davydovych, §9",
    },
    "пануючий": {
        "replacement": "панівний",
        "category": AdjudicationCategory.LEXICAL_CALQUE,
        "source": "Antonenko-Davydovych, §12",
    },
    "правлячий": {
        "replacement": "панівний",
        "category": AdjudicationCategory.LEXICAL_CALQUE,
        "source": "Antonenko-Davydovych, §12",
    },
    "відстаючий": {
        "replacement": "відсталий",
        "category": AdjudicationCategory.LEXICAL_CALQUE,
        "source": "Antonenko-Davydovych, §12",
    },
    "відживаючий": {
        "replacement": "віджилий",
        "category": AdjudicationCategory.LEXICAL_CALQUE,
        "source": "Antonenko-Davydovych, §12",
    },
    "домінуючий": {
        "replacement": "домінантний",
        "category": AdjudicationCategory.LEXICAL_CALQUE,
        "source": "Antonenko-Davydovych, §12",
    },
    "надихаючий": {
        "replacement": "надихальний",
        "category": AdjudicationCategory.LEXICAL_CALQUE,
        "source": "Antonenko-Davydovych, §12",
    },
    "організуючий": {
        "replacement": "організаційний",
        "category": AdjudicationCategory.LEXICAL_CALQUE,
        "source": "Antonenko-Davydovych, §12",
    },
    "підростаючий": {
        "replacement": "підрослий",
        "category": AdjudicationCategory.LEXICAL_CALQUE,
        "source": "Antonenko-Davydovych, §12",
    },
    "підпорядковуючий": {
        "replacement": "підпорядковувальний",
        "category": AdjudicationCategory.LEXICAL_CALQUE,
        "source": "Antonenko-Davydovych, §12",
    },
    "перетворюючий": {
        "replacement": "перетворювальний",
        "category": AdjudicationCategory.LEXICAL_CALQUE,
        "source": "Antonenko-Davydovych, §12",
    },
    "життєстверджуючий": {
        "replacement": "життєствердний",
        "category": AdjudicationCategory.LEXICAL_CALQUE,
        "source": "Antonenko-Davydovych, §12",
    },
    "принижуючий": {
        "replacement": "принизливий",
        "category": AdjudicationCategory.LEXICAL_CALQUE,
        "source": "Antonenko-Davydovych, §12",
    },
    "спрямовуючий": {
        "replacement": "спрямовувальний",
        "category": AdjudicationCategory.LEXICAL_CALQUE,
        "source": "Antonenko-Davydovych, §12",
    },
    "стримуючий": {
        "replacement": "стримувальний",
        "category": AdjudicationCategory.LEXICAL_CALQUE,
        "source": "Antonenko-Davydovych, §12",
    },
    "хвилюючий": {
        "replacement": "хвилювальний",
        "category": AdjudicationCategory.LEXICAL_CALQUE,
        "source": "Antonenko-Davydovych, §12",
    },
}

# Soviet historical ideological terms / realia (not language calques, but historical political realia)
SOVIET_IDEOLOGICAL_REALIA_KEYWORDS: frozenset[str] = frozenset(
    {
        "комсомол",
        "колгосп",
        "радгосп",
        "партком",
        "райком",
        "обком",
        "політрук",
        "жовтеня",
        "стахановець",
        "п'ятирічка",
        "соцзмагання",
        "більшовик",
        "чекіст",
        "кдб",
        "вчк",
        "гулаг",
        "неп",
        "продрозверстка",
        "лікнеп",
    }
)


@dataclass(frozen=True)
class Sum11RiskEntry:
    id: int
    word: str
    definition: str
    text: str
    sovietization_risk: int
    sovietization_keywords: list[str]


def clean_word(text: str) -> str:
    """Normalize lemma text for dictionary and whitelist lookups."""
    return re.sub(r"[\u0300-\u036f]", "", text.strip().lower())


def is_neologism_whitelisted(word: str) -> bool:
    """Determine if a word is an attested 20th-century modern neologism/internationalism.

    Strict matching only: exact lemma, hyphenated compound component, or strict stem prefix
    (>= 7 chars). Loose infix substring matching is forbidden to prevent false positives
    on older vocabulary (e.g. автомобільний matching мобільний, стереотип matching стерео).
    """
    norm = clean_word(word)
    if norm in MODERN_20TH_CENTURY_WHITELIST:
        return True
    if any(part in MODERN_20TH_CENTURY_WHITELIST for part in norm.split("-")):
        return True
    return any(len(item) >= 7 and norm.startswith(item) for item in MODERN_20TH_CENTURY_WHITELIST)


def is_skrypnykivka_archaism(word: str) -> bool:
    """Detect obsolete 1920s Skrypnykivka-only archaisms that must not be forced."""
    norm = clean_word(word)
    return norm in SKRYPNYKIVKA_ARCHAISMS


def is_soviet_ideological_realia(word: str, keywords: list[str]) -> bool:
    """Identify historical Soviet ideological realia."""
    norm = clean_word(word)
    if any(k in norm for k in SOVIET_IDEOLOGICAL_REALIA_KEYWORDS):
        return True
    return any(k in {"ленін", "маркс", "кпрс", "вкп", "срср", "комсомол", "більшов"} for k in keywords) and any(
        term in norm for term in {"парт", "ком", "рад", "радян", "соц", "жовт", "колект"}
    )


def query_r2u_safe(
    word: str,
    *,
    cache_entries: dict[str, Any] | None = None,
    allow_network: bool = True,
) -> tuple[R2ULookupStatus, list[str]]:
    """Query R2U with network vs absence disambiguation.

    Returns (status, list of translation lemmas).
    Differentiates SOURCE_UNAVAILABLE from NOT_FOUND_WITHIN_VERIFIED_COVERAGE.
    Never treats a network timeout or error as missing word proof.
    """
    norm = clean_word(word)
    if cache_entries is not None and norm in cache_entries:
        entry = cache_entries[norm]
        raw_status = entry.get("status", "found")
        try:
            status = R2ULookupStatus(raw_status)
        except ValueError:
            status = R2ULookupStatus.FOUND
        translations = entry.get("translations", [])
        return status, translations

    if not allow_network:
        return R2ULookupStatus.NOT_QUERIED, []

    # Try using canonical r2u_translate_with_status from scripts.rag.source_query or rag.source_query
    try:
        try:
            from scripts.rag.source_query import r2u_translate_with_status
        except ImportError:
            from rag.source_query import r2u_translate_with_status

        sq_status, entries = r2u_translate_with_status(norm)
        if sq_status.value == R2ULookupStatus.FOUND.value:
            translations = [e.get("translation", "") for e in entries if e.get("translation")]
            res_status = R2ULookupStatus.FOUND
            res_trans = translations[:10]
        elif sq_status.value == R2ULookupStatus.SOURCE_UNAVAILABLE.value:
            res_status = R2ULookupStatus.SOURCE_UNAVAILABLE
            res_trans = []
        else:
            res_status = R2ULookupStatus.NOT_FOUND_WITHIN_VERIFIED_COVERAGE
            res_trans = []

        if cache_entries is not None and res_status != R2ULookupStatus.SOURCE_UNAVAILABLE:
            cache_entries[norm] = {
                "status": res_status.value,
                "translations": [t[:120].strip() for t in res_trans[:5]],
            }
        return res_status, res_trans
    except Exception:
        pass

    # Bounded fallback query
    import urllib.error
    import urllib.request

    url = f"https://r2u.org.ua/s?w={urllib.request.quote(norm)}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "ULDR-Phase3-Miner/1.0"})
        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status != 200:
                return R2ULookupStatus.SOURCE_UNAVAILABLE, []
            html = response.read().decode("utf-8", errors="replace")
            matches = re.findall(r'<td class="result_row[^"]*">(.*?)</td>', html, re.DOTALL)
            translations = []
            for match in matches:
                clean = re.sub(r"<[^>]+>", " ", match)
                words = re.findall(r"[а-яіїєґА-ЯІЇЄҐ']+", clean)
                translations.extend(words)
            if translations:
                res_status = R2ULookupStatus.FOUND
                res_trans = translations[:10]
            else:
                res_status = R2ULookupStatus.NOT_FOUND_WITHIN_VERIFIED_COVERAGE
                res_trans = []
            if cache_entries is not None:
                cache_entries[norm] = {
                    "status": res_status.value,
                    "translations": [t[:120].strip() for t in res_trans[:5]],
                }
            return res_status, res_trans
    except (urllib.error.URLError, TimeoutError, OSError):
        # Strict disambiguation: network failure is NEVER absence
        return R2ULookupStatus.SOURCE_UNAVAILABLE, []


def verify_in_vesum(lemma: str, cursor: sqlite3.Cursor | None) -> bool:
    """Verify living standard Ukrainian attestation in VESUM forms_all.

    Fails closed: requires an active sqlite3 cursor to vesum.db with forms_all table.
    """
    if cursor is None:
        raise RuntimeError(
            "VESUM database cursor required for attestation verification. "
            "Cannot certify authentic Ukrainian replacements without data/vesum.db."
        )
    norm = clean_word(lemma)
    # If multi-word phrase, check all constituent content words (length > 1)
    words = [w for w in norm.split() if len(w) > 1]
    if len(words) > 1:
        for w in words:
            cursor.execute("SELECT 1 FROM forms_all WHERE lemma = ? LIMIT 1", (w,))
            if cursor.fetchone():
                continue
            cursor.execute("SELECT 1 FROM forms_all WHERE word_form = ? LIMIT 1", (w,))
            if not cursor.fetchone():
                return False
        return True
    cursor.execute("SELECT 1 FROM forms_all WHERE lemma = ? LIMIT 1", (norm,))
    if cursor.fetchone():
        return True
    cursor.execute("SELECT 1 FROM forms_all WHERE word_form = ? LIMIT 1", (norm,))
    return cursor.fetchone() is not None


def adjudicate_sum11_entry(
    entry: Sum11RiskEntry,
    vesum_cursor: sqlite3.Cursor | None,
    r2u_cache: dict[str, Any] | None = None,
    *,
    allow_network: bool = True,
) -> dict[str, Any]:
    """Adjudicate a single sum11 entry flagged with sovietization_risk > 0."""
    norm = clean_word(entry.word)
    keywords = [k.strip().lower() for k in entry.sovietization_keywords if k.strip()]

    # 1. Check Neologism & Internationalism Whitelist (Zero false calques on modern tech)
    if is_neologism_whitelisted(norm):
        r2u_status, _ = query_r2u_safe(norm, cache_entries=r2u_cache, allow_network=allow_network)
        return {
            "schema_version": "v1_differential_soviet_candidate",
            "candidate_id": f"soviet.cand.{hashlib.sha256(f'sum11:{entry.id}:{norm}'.encode()).hexdigest()[:16]}",
            "sum11_id": entry.id,
            "word": entry.word,
            "sovietization_risk": entry.sovietization_risk,
            "sovietization_keywords": keywords,
            "status": AdjudicationStatus.WHITELIST_PRESERVED.value,
            "adjudication_category": AdjudicationCategory.MODERN_NEOLOGISM_TECHNICAL.value,
            "authentic_alternatives": [],
            "is_neologism_whitelisted": True,
            "vesum_attested": verify_in_vesum(norm, vesum_cursor),
            "r2u_lookup_status": r2u_status.value,
        }

    # 2. Check Known Authentic Soviet Calque Replacements (Antonenko-Davydovych / Living Standard)
    if norm in AUTHENTIC_SOVIET_CALQUE_REPLACEMENTS:
        calque_info = AUTHENTIC_SOVIET_CALQUE_REPLACEMENTS[norm]
        rep = calque_info["replacement"]
        r2u_status, _ = query_r2u_safe(norm, cache_entries=r2u_cache, allow_network=allow_network)
        return {
            "schema_version": "v1_differential_soviet_candidate",
            "candidate_id": f"soviet.cand.{hashlib.sha256(f'sum11:{entry.id}:{norm}'.encode()).hexdigest()[:16]}",
            "sum11_id": entry.id,
            "word": entry.word,
            "sovietization_risk": entry.sovietization_risk,
            "sovietization_keywords": keywords,
            "status": AdjudicationStatus.CANDIDATE_ADMITTED.value,
            "adjudication_category": calque_info["category"].value,
            "authentic_alternatives": [
                {
                    "term": rep,
                    "source": calque_info["source"],
                    "vesum_attested": verify_in_vesum(rep, vesum_cursor),
                    "is_modern_standard": True,
                }
            ],
            "is_neologism_whitelisted": False,
            "vesum_attested": verify_in_vesum(norm, vesum_cursor),
            "r2u_lookup_status": r2u_status.value,
        }

    # 3. Check Skrypnykivka-only archaisms (reject obsolete 1920s purisms)
    if is_skrypnykivka_archaism(norm):
        r2u_status, _ = query_r2u_safe(norm, cache_entries=r2u_cache, allow_network=allow_network)
        return {
            "schema_version": "v1_differential_soviet_candidate",
            "candidate_id": f"soviet.cand.{hashlib.sha256(f'sum11:{entry.id}:{norm}'.encode()).hexdigest()[:16]}",
            "sum11_id": entry.id,
            "word": entry.word,
            "sovietization_risk": entry.sovietization_risk,
            "sovietization_keywords": keywords,
            "status": AdjudicationStatus.SKRYPNYKIVKA_ARCHAISM_REJECTED.value,
            "adjudication_category": AdjudicationCategory.SKRYPNYKIVKA_ARCHAISM.value,
            "authentic_alternatives": [],
            "is_neologism_whitelisted": False,
            "vesum_attested": verify_in_vesum(norm, vesum_cursor),
            "r2u_lookup_status": r2u_status.value,
        }

    # 4. Check Historical Soviet Ideological Realia (Not calques, but historical political realia)
    if is_soviet_ideological_realia(norm, keywords):
        r2u_status, _ = query_r2u_safe(norm, cache_entries=r2u_cache, allow_network=allow_network)
        return {
            "schema_version": "v1_differential_soviet_candidate",
            "candidate_id": f"soviet.cand.{hashlib.sha256(f'sum11:{entry.id}:{norm}'.encode()).hexdigest()[:16]}",
            "sum11_id": entry.id,
            "word": entry.word,
            "sovietization_risk": entry.sovietization_risk,
            "sovietization_keywords": keywords,
            "status": AdjudicationStatus.IDEOLOGICAL_HISTORICAL_ONLY.value,
            "adjudication_category": AdjudicationCategory.SOVIET_REALIA_IDEOLOGY.value,
            "authentic_alternatives": [],
            "is_neologism_whitelisted": False,
            "vesum_attested": verify_in_vesum(norm, vesum_cursor),
            "r2u_lookup_status": r2u_status.value,
        }

    # 5. Default Standard Living Ukrainian (Flagged only by incidental quote in СУМ-11)
    return {
        "schema_version": "v1_differential_soviet_candidate",
        "candidate_id": f"soviet.cand.{hashlib.sha256(f'sum11:{entry.id}:{norm}'.encode()).hexdigest()[:16]}",
        "sum11_id": entry.id,
        "word": entry.word,
        "sovietization_risk": entry.sovietization_risk,
        "sovietization_keywords": keywords,
        "status": AdjudicationStatus.WHITELIST_PRESERVED.value,
        "adjudication_category": AdjudicationCategory.STANDARD_UKRAINIAN_PRESERVED.value,
        "authentic_alternatives": [],
        "is_neologism_whitelisted": False,
        "vesum_attested": verify_in_vesum(norm, vesum_cursor),
        "r2u_lookup_status": R2ULookupStatus.NOT_QUERIED.value,
    }


def validate_no_private_host_paths(data: Any) -> None:
    """Ensure no metal paths or host usernames exist in committed structures."""
    serialized = json.dumps(data, ensure_ascii=False)
    match = PRIVATE_HOST_RE.search(serialized)
    if match:
        raise ValueError(f"OPSEC violation: private path detected in data: {match.group(0)}")


def build_differential_receipt(
    candidates: list[dict[str, Any]],
    output_dir: Path,
) -> dict[str, Any]:
    """Generate deterministic, hash-only public receipt."""
    admitted = sum(1 for c in candidates if c["status"] == AdjudicationStatus.CANDIDATE_ADMITTED.value)
    neologisms = sum(1 for c in candidates if c["is_neologism_whitelisted"])
    ideological = sum(1 for c in candidates if c["status"] == AdjudicationStatus.IDEOLOGICAL_HISTORICAL_ONLY.value)
    archaisms = sum(1 for c in candidates if c["status"] == AdjudicationStatus.SKRYPNYKIVKA_ARCHAISM_REJECTED.value)

    # Invariant checks
    false_calques = sum(1 for c in candidates if c["is_neologism_whitelisted"] and c["status"] == AdjudicationStatus.CANDIDATE_ADMITTED.value)
    if false_calques != 0:
        raise ValueError(f"Invariant violation: {false_calques} false calque flags on whitelisted neologisms!")

    timeout_as_missing = sum(1 for c in candidates if c["r2u_lookup_status"] == R2ULookupStatus.SOURCE_UNAVAILABLE.value and c["status"] == AdjudicationStatus.CANDIDATE_ADMITTED.value)
    if timeout_as_missing != 0:
        raise ValueError(f"Invariant violation: {timeout_as_missing} network timeouts treated as missing word proof!")

    discovery_candidates = [
        c for c in candidates
        if not (c["status"] == AdjudicationStatus.WHITELIST_PRESERVED.value and c["adjudication_category"] == AdjudicationCategory.STANDARD_UKRAINIAN_PRESERVED.value)
    ]

    queried_candidates = sum(1 for c in discovery_candidates if c["r2u_lookup_status"] != R2ULookupStatus.NOT_QUERIED.value)
    if len(discovery_candidates) > 0 and queried_candidates == 0:
        raise ValueError("Invariant violation: zero discovery candidates had R2U differential queries performed!")

    all_alternatives = [alt for c in candidates for alt in c.get("authentic_alternatives", [])]
    if not all_alternatives:
        raise ValueError("Invariant violation: no authentic alternatives found to verify VESUM attestation!")
    unattested = [alt["term"] for alt in all_alternatives if not alt.get("vesum_attested")]
    if unattested:
        raise ValueError(f"Invariant violation: authentic alternatives lack VESUM attestation: {unattested}")
    all_vesum_attested = len(unattested) == 0

    receipt_bytes = hashlib.sha256(json.dumps(candidates, sort_keys=True).encode()).hexdigest()
    receipt_id = f"receipt.soviet_miner.{receipt_bytes[:16]}"

    index_filename = "differential_soviet_candidates.jsonl"
    index_lines = [json.dumps(c, ensure_ascii=False, separators=(",", ":")) for c in discovery_candidates]
    index_content = "\n".join(index_lines) + ("\n" if index_lines else "")
    index_sha = hashlib.sha256(index_content.encode()).hexdigest()

    manifest_filename = "differential_soviet_manifest.json"
    manifest_data = {
        "manifest_version": "v1_differential_soviet_manifest",
        "receipt_id": receipt_id,
        "entry_count": len(discovery_candidates),
        "index_file": index_filename,
        "index_sha256": index_sha,
    }
    manifest_content = json.dumps(manifest_data, indent=2, sort_keys=True) + "\n"
    manifest_sha = hashlib.sha256(manifest_content.encode("utf-8")).hexdigest()

    receipt = {
        "schema_version": "v1_differential_soviet_receipt",
        "receipt_id": receipt_id,
        "issue": 8008,
        "epic": 6321,
        "generated_at": datetime.datetime.now(datetime.UTC).isoformat(),
        "sum11_risk_pool": {
            "total_entries": TOTAL_SUM11_RISK_POOL,
            "risk_1_count": 6397,
            "risk_2_count": 755,
        },
        "whitelists": {
            "neologism_whitelist_count": len(MODERN_20TH_CENTURY_WHITELIST),
            "skrypnykivka_archaism_count": len(SKRYPNYKIVKA_ARCHAISMS),
        },
        "counts": {
            "candidates_admitted": admitted,
            "neologisms_preserved": neologisms,
            "ideological_realia_tagged": ideological,
            "archaisms_rejected": archaisms,
            "false_calque_flags_on_whitelist": 0,
            "network_timeouts_as_missing_words": 0,
        },
        "invariants": {
            "zero_false_calque_on_neologisms": bool(false_calques == 0),
            "zero_network_errors_as_missing_word": bool(timeout_as_missing == 0),
            "all_replacements_vesum_attested": bool(all_vesum_attested),
            "no_private_host_paths": True,
        },
        "files": {
            "candidates_index": {
                "filename": index_filename,
                "sha256": index_sha,
                "line_count": len(discovery_candidates),
            },
            "candidates_manifest": {
                "filename": manifest_filename,
                "sha256": manifest_sha,
            },
        },
    }

    validate_no_private_host_paths(receipt)
    return receipt, index_content, manifest_content, manifest_data


def run_miner(
    sources_db_path: Path,
    vesum_db_path: Path,
    output_dir: Path,
    *,
    verify_only: bool = False,
    allow_network: bool = True,
) -> int:
    """Run Phase 3.4 differential Soviet candidate miner."""
    output_dir.mkdir(parents=True, exist_ok=True)
    receipt_path = output_dir / "differential_soviet_receipt.json"
    index_path = output_dir / "differential_soviet_candidates.jsonl"
    manifest_path = output_dir / "differential_soviet_manifest.json"

    if verify_only:
        if not receipt_path.exists() or not index_path.exists() or not manifest_path.exists():
            print(f"Error: Required files missing for --verify-only in {output_dir}")
            return 1
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        validate_no_private_host_paths(receipt)

        # Verify index hash and line count
        content = index_path.read_text(encoding="utf-8")
        current_index_sha = hashlib.sha256(content.encode("utf-8")).hexdigest()
        expected_index_sha = receipt["files"]["candidates_index"]["sha256"]
        if current_index_sha != expected_index_sha:
            print(f"Error: Hash mismatch for {index_path.name}: {current_index_sha} != {expected_index_sha}")
            return 1

        actual_line_count = len([line for line in content.splitlines() if line.strip()])
        expected_line_count = receipt["files"]["candidates_index"]["line_count"]
        if actual_line_count != expected_line_count:
            print(f"Error: Line count mismatch for {index_path.name}: {actual_line_count} != {expected_line_count}")
            return 1

        # Verify manifest hash and contents
        manifest_text = manifest_path.read_text(encoding="utf-8")
        current_manifest_sha = hashlib.sha256(manifest_text.encode("utf-8")).hexdigest()
        expected_manifest_sha = receipt["files"]["candidates_manifest"]["sha256"]
        if current_manifest_sha != expected_manifest_sha:
            print(f"Error: Hash mismatch for {manifest_path.name}: {current_manifest_sha} != {expected_manifest_sha}")
            return 1

        manifest = json.loads(manifest_text)
        validate_no_private_host_paths(manifest)
        if manifest.get("index_sha256") != expected_index_sha:
            print(f"Error: Manifest index_sha256 mismatch: {manifest.get('index_sha256')} != {expected_index_sha}")
            return 1
        if manifest.get("entry_count") != expected_line_count:
            print(f"Error: Manifest entry_count mismatch: {manifest.get('entry_count')} != {expected_line_count}")
            return 1
        if manifest.get("receipt_id") != receipt["receipt_id"]:
            print(f"Error: Manifest receipt_id mismatch: {manifest.get('receipt_id')} != {receipt['receipt_id']}")
            return 1

        for inv_k, inv_v in receipt.get("invariants", {}).items():
            if inv_v is not True:
                print(f"Error: Invariant {inv_k} is not True in receipt")
                return 1

        print("✓ Differential Soviet candidate receipt and manifest verified clean.")
        return 0

    # Ingest from sources.db sum11
    if not sources_db_path.exists():
        print(f"Error: sources.db not found at {sources_db_path}")
        return 1

    if not vesum_db_path.exists():
        print(f"Error: vesum.db not found at {vesum_db_path}. Living standard attestation requires vesum.db.")
        return 1

    # Load R2U differential cache if available
    cache_path = output_dir / "r2u_differential_cache.json"
    r2u_cache: dict[str, Any] = {}
    if cache_path.exists():
        try:
            r2u_cache = json.loads(cache_path.read_text(encoding="utf-8"))
        except Exception:
            r2u_cache = {}
    elif DEFAULT_R2U_CACHE.exists():
        try:
            r2u_cache = json.loads(DEFAULT_R2U_CACHE.read_text(encoding="utf-8"))
        except Exception:
            r2u_cache = {}

    conn = sqlite3.connect(f"file:{sources_db_path.resolve()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    vesum_conn = sqlite3.connect(f"file:{vesum_db_path.resolve()}?mode=ro", uri=True)
    vesum_cursor = vesum_conn.cursor()

    try:
        rows = cursor.execute(
            "SELECT id, word, definition, text, sovietization_risk, sovietization_keywords "
            "FROM sum11 WHERE sovietization_risk > 0 ORDER BY id"
        ).fetchall()
        print(f"Ingested {len(rows)} entries with sovietization_risk > 0 from sum11.")

        candidates = []
        for r in rows:
            entry = Sum11RiskEntry(
                id=r["id"],
                word=r["word"],
                definition=r["definition"],
                text=r["text"],
                sovietization_risk=r["sovietization_risk"],
                sovietization_keywords=r["sovietization_keywords"].split(",") if r["sovietization_keywords"] else [],
            )
            candidate = adjudicate_sum11_entry(
                entry,
                vesum_cursor,
                r2u_cache=r2u_cache,
                allow_network=allow_network,
            )
            candidates.append(candidate)

        receipt, index_content, manifest_content, _manifest_data = build_differential_receipt(candidates, output_dir)

        index_path.write_text(index_content, encoding="utf-8")
        manifest_path.write_text(manifest_content, encoding="utf-8")
        receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if r2u_cache:
            cache_path.write_text(json.dumps(r2u_cache, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")

        print(f"Successfully processed {len(candidates)} entries.")
        print(f"  Admitted candidates: {receipt['counts']['candidates_admitted']}")
        print(f"  Preserved neologisms: {receipt['counts']['neologisms_preserved']}")
        print(f"  Tagged Soviet realia: {receipt['counts']['ideological_realia_tagged']}")
        print(f"  Rejected archaisms: {receipt['counts']['archaisms_rejected']}")
        print(f"  Receipt: {receipt_path.name}")
        return 0
    finally:
        conn.close()
        vesum_conn.close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Mine and adjudicate differential Soviet candidates from СУМ-11.")
    parser.add_argument("--sources-db", type=Path, default=DEFAULT_SOURCES_DB, help="Path to sources.db")
    parser.add_argument("--vesum-db", type=Path, default=DEFAULT_VESUM_DB, help="Path to vesum.db")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR, help="Output directory")
    parser.add_argument("--verify-only", action="store_true", help="Verify receipt and hashes without re-mining")
    parser.add_argument("--no-network", action="store_true", help="Disable live network queries; rely only on local cache")
    args = parser.parse_args(argv)

    return run_miner(
        sources_db_path=args.sources_db,
        vesum_db_path=args.vesum_db,
        output_dir=args.output_dir,
        verify_only=args.verify_only,
        allow_network=not args.no_network,
    )


if __name__ == "__main__":
    sys.exit(main())
