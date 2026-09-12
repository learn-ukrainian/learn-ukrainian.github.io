#!/usr/bin/env python3
"""Ukrainian Linguistic Decolonization & Reasoning (ULDR) Dataset Generator (#7922).

Mines calque and Russianism replacement clusters from curated human holdings
(LanguageTool, style guides, textbooks, UA-GEC), verifies inflectional validity
in VESUM, extracts living school curriculum citations from genuine MESU Grade 1-11 textbooks,
and synthesizes normative SFT reasoning trajectories and contrastive DPO preference pairs.

Zero LLM authoring: 100% deterministic rule-based processing.
Zero private leakage: Strictly filters non-redistributable sources (ULP, Ohoiko, private lessons).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sqlite3
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import jsonschema

REPO_ROOT = Path(__file__).resolve().parents[3]


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


CONTRACTS_DIR = REPO_ROOT / "data" / "projects" / "open_model_data" / "contracts"
TRAJECTORY_SCHEMA_PATH = CONTRACTS_DIR / "v1_decolonization_trajectory.schema.json"
DPO_PAIR_SCHEMA_PATH = CONTRACTS_DIR / "v1_decolonization_dpo_pair.schema.json"
MAX_SHARD_BYTES: int = 1_800_000

DEFAULT_SOURCES_DB = resolve_data_path("data/sources.db")
DEFAULT_VESUM_DB = resolve_data_path("data/vesum.db")
DEFAULT_LT_REPLACEMENTS = resolve_data_path("data/lt_replacements.json")
DEFAULT_HERITAGE_PAIRS = resolve_data_path("data/lexicon/heritage_pairs.yaml")
DEFAULT_HERITAGE_OVERLAY = resolve_data_path("data/lexicon/heritage_pairs.wave1-calque.yaml")

_ACUTE_RE = re.compile(r"[\u0301\u0300]")
_EDGE_PUNCT_RE = re.compile(r"^[\"'«»„”“,.:;!?…\s]+|[\"'«»„”“,.:;!?…\s]+$")
_CYRILLIC_TOKEN_RE = re.compile(r"^[А-Яа-яЄєІіЇїҐґ'’ʼ\s-]+$")

# Calque pattern classification regexes
_ACTIVE_PARTICIPLE_RE = re.compile(r"(?:[юуяа]ч[иі][йяехм]|ючись|ячись)$", re.IGNORECASE)
_PREFIX_OBEZ_RE = re.compile(r"^обез", re.IGNORECASE)
_PREFIX_SO_RE = re.compile(r"^со[пткхчшщс]", re.IGNORECASE)

# Real MESU school subjects and author display mappings
SUBJECT_DISPLAY_NAMES: dict[str, str] = {
    "ukrmova": "Українська мова",
    "ukrlit": "Українська література",
    "istoriya": "Історія України",
    "vsesvitnia": "Всесвітня історія",
    "biolohiya": "Біологія",
    "heohrafiya": "Географія",
    "fizyka": "Фізика",
    "khimiya": "Хімія",
    "matematyka": "Математика",
    "algebra": "Алгебра",
    "heometriya": "Геометрія",
    "ya_doslidzhuiu_svit": "Я досліджую світ",
    "pravoznavstvo": "Правознавство",
    "astronomiya": "Астрономія",
    "pryroda": "Природознавство",
    "informatyka": "Інформатика",
    "tekhnolohiyi": "Технології",
    "bukvar": "Буквар",
    "zarlit": "Зарубіжна література",
    "mystetstvo": "Мистецтво",
}

AUTHOR_DISPLAY_NAMES: dict[str, str] = {
    "glazova": "О. Глазова",
    "avramenko": "О. Авраменко",
    "zabolotnyi": "О. Заболотний",
    "pometun": "О. Пометун",
    "vlasov": "В. Власов",
    "zaharijchuk": "М. Захарійчук",
    "bilenko": "О. Біленко",
    "onishchuk": "І. Оніщук",
    "hyshkina": "О. Гісем",
}

RESTRICTED_SOURCE_SUBSTRINGS = (
    "ulp-",
    "ohoiko",
    "private-teacher",
    "pohribnyi",
    "antonenko",
)

RESTRICTED_AUTHORS = (
    "ukrainian lessons podcast",
    "anna ohoiko",
    "private_teacher_lesson",
    "borys antonenko-davydovych",
    "mykola pohribnyi",
)

ALLOWED_GRADES = ("1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11")

PRIVATE_PATH_PATTERNS = [
    re.compile(r"/(?:home|Users|tmp|var/tmp|workspace|root)/[a-zA-Z0-9_.-]+", re.IGNORECASE),
    re.compile(r"[A-Z]:\\[a-zA-Z0-9_.-]+", re.IGNORECASE),
]

RESTRICTED_SOURCE_PATTERNS = [
    re.compile(r"ulp-", re.IGNORECASE),
    re.compile(r"ukrainian\s*lessons", re.IGNORECASE),
    re.compile(r"ohoiko", re.IGNORECASE),
    re.compile(r"private[-_]teacher", re.IGNORECASE),
]


def strip_accents(s: str) -> str:
    """Remove combining acute and grave stress marks."""
    return _ACUTE_RE.sub("", s)


def normalize_text(s: str) -> str:
    """Normalize whitespace and strip edge quotation marks and punctuation."""
    clean = strip_accents(s).strip()
    return _EDGE_PUNCT_RE.sub("", clean).strip()


def compute_id(prefix: str, key: str) -> str:
    """Generate a deterministic content-addressed identifier."""
    h = hashlib.sha256(key.strip().lower().encode("utf-8")).hexdigest()[:16]
    return f"{prefix}.decolonize.{h}"


@dataclass
class CalqueCandidate:
    target_term: str
    suggestions: list[str]
    source_tag: str
    provenance_note: str | None = None
    curated_evidence: list[str] | None = None


def load_calque_candidates(
    lt_path: Path,
    sources_db_path: Path,
) -> list[CalqueCandidate]:
    """Mine candidate calques and Russianisms from curated human holdings."""
    candidates_map: dict[str, CalqueCandidate] = {}

    # 1. High-priority curated calques & phrasal calques from calque_corrections.py
    try:
        from scripts.lexicon.calque_corrections import (
            CURATED_CALQUES,
            LEXICALISED_SAFE,
            PHRASAL_CALQUES,
            SENSE_RESTRICTED_CALQUES,
        )

        safe_set = {normalize_text(w).lower() for w in LEXICALISED_SAFE}
        polysemes_set = {normalize_text(w).lower() for w in SENSE_RESTRICTED_CALQUES}

        for term, meta in CURATED_CALQUES.items():
            norm_term = normalize_text(term).lower()
            if norm_term in safe_set or norm_term in polysemes_set:
                continue
            corrs = meta.get("corrections", [])
            if isinstance(corrs, list) and corrs:
                clean_corrs = [normalize_text(c) for c in corrs if normalize_text(c)]
                note = str(meta.get("note", ""))
                evidence = [str(e) for e in meta.get("evidence", [])]
                candidates_map[norm_term] = CalqueCandidate(
                    target_term=norm_term,
                    suggestions=clean_corrs,
                    source_tag="curated_calques",
                    provenance_note=note,
                    curated_evidence=evidence,
                )

        for term, meta in PHRASAL_CALQUES.items():
            norm_term = normalize_text(term).lower()
            corrs = meta.get("corrections", [])
            if isinstance(corrs, list) and corrs:
                clean_corrs = [normalize_text(c) for c in corrs if normalize_text(c)]
                note = str(meta.get("note", ""))
                evidence = [str(e) for e in meta.get("evidence", [])]
                if norm_term not in candidates_map:
                    candidates_map[norm_term] = CalqueCandidate(
                        target_term=norm_term,
                        suggestions=clean_corrs,
                        source_tag="phrasal_calques",
                        provenance_note=note,
                        curated_evidence=evidence,
                    )
    except Exception:
        safe_set = set()
        polysemes_set = set()

    # 2. UA-GEC F/Calque human-annotated errors
    if sources_db_path.is_file():
        conn = sqlite3.connect(str(sources_db_path))
        try:
            cur = conn.cursor()
            rows = cur.execute(
                "SELECT error, correct FROM ua_gec_errors WHERE error_type = 'F/Calque' AND is_native = 1"
            ).fetchall()
            for err, corr in rows:
                norm_err = normalize_text(err).lower()
                norm_corr = normalize_text(corr)
                if not norm_err or not norm_corr:
                    continue
                if norm_err in safe_set or norm_err in polysemes_set:
                    continue
                if norm_err == norm_corr.lower():
                    continue
                if not _CYRILLIC_TOKEN_RE.match(norm_err) or not _CYRILLIC_TOKEN_RE.match(norm_corr):
                    continue
                if norm_err not in candidates_map:
                    candidates_map[norm_err] = CalqueCandidate(
                        target_term=norm_err,
                        suggestions=[norm_corr],
                        source_tag="ua_gec_calque",
                        provenance_note="Корпус граматичних та лексичних помилок UA-GEC (F/Calque).",
                    )
        finally:
            conn.close()

    # 3. LanguageTool Replacements (bulk curated dictionary)
    if lt_path.is_file():
        with lt_path.open("r", encoding="utf-8") as f:
            lt_data = json.load(f)
        for term, item in lt_data.items():
            norm_term = normalize_text(term).lower()
            if norm_term in safe_set or norm_term in polysemes_set:
                continue
            if not _CYRILLIC_TOKEN_RE.match(norm_term):
                continue
            suggestions = item.get("suggestions", [])
            clean_suggs = [
                normalize_text(s)
                for s in suggestions
                if normalize_text(s)
                and normalize_text(s).lower() != norm_term
                and _CYRILLIC_TOKEN_RE.match(normalize_text(s))
            ]
            if not clean_suggs:
                continue
            if norm_term not in candidates_map:
                candidates_map[norm_term] = CalqueCandidate(
                    target_term=norm_term,
                    suggestions=clean_suggs,
                    source_tag="lt_replacements",
                    provenance_note=f"База лексичних замін LanguageTool ({item.get('source', 'curated')}).",
                )

    return list(candidates_map.values())


def get_vesum_counts(
    lemmas: list[str],
    vesum_db_path: Path,
    conn: sqlite3.Connection | None = None,
) -> dict[str, int]:
    """Query local VESUM database for paradigm form counts across all constituent words."""
    counts: dict[str, int] = {}
    if not vesum_db_path.is_file():
        return {lemma: 0 for lemma in lemmas}
    close_conn = False
    if conn is None:
        conn = sqlite3.connect(f"file:{vesum_db_path.resolve()}?mode=ro", uri=True)
        close_conn = True
    try:
        cur = conn.cursor()
        for lemma in lemmas:
            words = [w.strip() for w in lemma.split() if w.strip()]
            if not words:
                counts[lemma] = 0
                continue
            # Check every constituent word in the phrase
            word_counts: list[int] = []
            for w in words:
                norm_w = re.sub(r"[\u0300\u0301]", "", w).strip().lower()
                row = cur.execute("SELECT count(*) FROM forms WHERE lemma = ?", (norm_w,)).fetchone()
                word_counts.append(row[0] if row else 0)
            # If any word in the phrase is absent from VESUM, the phrase has 0 attested paradigm
            counts[lemma] = min(word_counts) if word_counts else 0
    finally:
        if close_conn:
            conn.close()
    return counts


def _has_textbooks_fts(conn: sqlite3.Connection) -> bool:
    """Check whether textbooks_fts virtual table exists in the connected database."""
    try:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='textbooks_fts'")
        return cur.fetchone() is not None
    except Exception:
        return False


def find_textbook_attestation(
    lemma: str,
    sources_db_path: Path,
    conn: sqlite3.Connection | None = None,
) -> dict[str, Any] | None:
    """Search genuine MESU Grade 1-11 textbooks in sources.db for living school citations.

    Strictly requires:
    - Full-phrase matching (multi-word phrases must appear in entirety, not just first word)
    - School grades 1-11 only

    Strictly excludes:
    - Private/non-redistributable sources (ULP podcast, Anna Ohoiko, private lessons)
    - Reference manuals without grades (Pohribnyi, Antonenko-Davydovych prose)
    - Chunks with non-school grades (empty, university)
    """
    if not sources_db_path.is_file():
        return None
    close_conn = False
    if conn is None:
        conn = sqlite3.connect(f"file:{sources_db_path.resolve()}?mode=ro", uri=True)
        close_conn = True
    try:
        cur = conn.cursor()
        words = [w.strip() for w in lemma.split() if w.strip()]
        if not words:
            return None
        clean_phrase = " ".join(words).lower()
        if len(clean_phrase) < 3:
            return None

        grade_placeholders = ",".join("?" for _ in ALLOWED_GRADES)
        rows: list[Any] = []

        if _has_textbooks_fts(conn):
            try:
                escaped_phrase = clean_phrase.replace('"', '""')
                fts_query = f"""
                    SELECT t.title, t.grade, t.subject, t.author, t.text, t.source_file
                    FROM textbooks_fts f
                    JOIN textbooks t ON t.id = f.rowid
                    WHERE textbooks_fts MATCH ?
                      AND t.grade IN ({grade_placeholders})
                    ORDER BY CAST(t.grade AS INTEGER) ASC
                    LIMIT 20
                """
                rows = cur.execute(fts_query, (f'"{escaped_phrase}"', *ALLOWED_GRADES)).fetchall()
            except sqlite3.OperationalError:
                rows = []
        else:
            variants = list(dict.fromkeys([clean_phrase, clean_phrase.capitalize(), clean_phrase.title()]))
            like_clauses = " OR ".join("text LIKE ?" for _ in variants)
            query = f"""
                SELECT title, grade, subject, author, text, source_file
                FROM textbooks
                WHERE ({like_clauses})
                  AND grade IN ({grade_placeholders})
                ORDER BY CAST(grade AS INTEGER) ASC
                LIMIT 20
            """
            params = [f"%{v}%" for v in variants] + list(ALLOWED_GRADES)
            rows = cur.execute(query, params).fetchall()

        for row in rows:
            title, grade, subject, author, text, src_file = row
            src_lower = (src_file or "").lower()
            author_lower = (author or "").lower()

            if any(r in src_lower for r in RESTRICTED_SOURCE_SUBSTRINGS):
                continue
            if any(r in author_lower for r in RESTRICTED_AUTHORS):
                continue

            # Strict phrase verification: all words must appear together in text
            text_lower = text.lower()
            if clean_phrase not in text_lower:
                continue

            sentences = [s.strip() for s in text.split(".") if clean_phrase in s.lower()]
            if not sentences:
                continue
            snippet = re.sub(r"\s+", " ", sentences[0]).strip()
            if len(snippet) > 160:
                snippet = snippet[:157] + "..."

            display_subject = SUBJECT_DISPLAY_NAMES.get(subject, subject)
            display_author = AUTHOR_DISPLAY_NAMES.get(author, author.title() if author else "")

            return {
                "title": title,
                "grade": int(grade) if str(grade).isdigit() else grade,
                "subject": display_subject,
                "author": display_author,
                "snippet": snippet,
                "source_file": src_file,
            }
    finally:
        if close_conn:
            conn.close()
    return None


def find_dictionary_attestation(
    lemma: str,
    sources_db_path: Path,
    conn: sqlite3.Connection | None = None,
) -> str | None:
    """Check historical (Grinchenko) and academic (SUM-11) dictionary presence in sources.db."""
    if not sources_db_path.is_file():
        return None
    close_conn = False
    if conn is None:
        conn = sqlite3.connect(f"file:{sources_db_path.resolve()}?mode=ro", uri=True)
        close_conn = True
    try:
        cur = conn.cursor()
        words = [w.strip() for w in lemma.split() if w.strip()]
        if not words:
            return None

        if len(words) == 1:
            word = words[0].lower()
            row_g = cur.execute("SELECT 1 FROM grinchenko WHERE word = ? LIMIT 1", (word,)).fetchone()
            if row_g:
                return "Історичний словник української мови Б. Грінченка (1907–1909); верифіковано у ВЕСУМ"
            row_s = cur.execute("SELECT 1 FROM sum11 WHERE word = ? LIMIT 1", (word,)).fetchone()
            if row_s:
                return "Академічний Словник української мови в 11 томах (СУМ-11); верифіковано у ВЕСУМ"
        else:
            # Multi-word phrase: verify if full phrase appears in SUM-11 or Grinchenko definitions
            phrase = " ".join(words).lower()
            row_s = cur.execute("SELECT 1 FROM sum11 WHERE definition LIKE ? LIMIT 1", (f"%{phrase}%",)).fetchone()
            if row_s:
                return (
                    "Академічний Словник української мови (СУМ-11, контекстне вживання фраземи); верифіковано у ВЕСУМ"
                )
            row_g = cur.execute("SELECT 1 FROM grinchenko WHERE definition LIKE ? LIMIT 1", (f"%{phrase}%",)).fetchone()
            if row_g:
                return "Історичний словник української мови Б. Грінченка (контекстне вживання фраземи); верифіковано у ВЕСУМ"
    finally:
        if close_conn:
            conn.close()
    return None


def classify_calque_type(target_term: str) -> tuple[str, str, str]:
    """Classify the calque formation pattern and generate morphemic diagnostic descriptions."""
    term_lower = target_term.lower()

    if _ACTIVE_PARTICIPLE_RE.search(term_lower):
        return (
            "active_participle",
            f"Штучне вживання активного дієприкметника теперішнього часу на «-чий» у слові «{target_term}». В українській мові активні дієприкметники теперішнього часу не утворюють живої продуктивної парадигми.",
            "Українська мова послуговується віддієслівними іменниками (на -ач, -ник, -альник), описовими підрядними зворотами (той, що; та, що) або питомими прикметниками.",
        )
    elif _PREFIX_OBEZ_RE.match(term_lower):
        return (
            "prefixal_calque",
            f"Слово «{target_term}» містить невластивий українському словотвору здвоєний префікс «обез-», скопійований з російської мови.",
            "Питомим українським словотвірним префіксом для вираження позбавлення або втрати ознаки є «зне-» / «зня-» або «без-».",
        )
    elif _PREFIX_SO_RE.match(term_lower):
        return (
            "prefixal_calque",
            f"Слово «{target_term}» використовує префікс «со-», що є прямою фонетико-морфологічною калькою російського префікса.",
            "В українській словотвірній системі значення сумісності або взаємодії виражається питомим префіксом «спів-» або прийменником «разом з».",
        )
    elif " " in term_lower:
        return (
            "phrasal_calque",
            f"Зворот «{target_term}» побудований шляхом буквального послівного перекладу російської синтаксичної або прийменникової конструкції.",
            "Питома українська синтаксична традиція використовує усталені фразеологічні еквіваленти або прислівники з відмінним керуванням.",
        )
    else:
        return (
            "lexical_calque",
            f"Лексема «{target_term}» є штучним лексичним запозиченням (росіянізмом), що витісняє автентичне українське поняття.",
            "Питома лексична система української мови має закорінену в народній мові та класичній літературі власну лексему.",
        )


def is_positive_citation(lemma: str, citation: str) -> bool:
    """Return True if citation positively recommends or attests lemma, and does not frame it as an error/calque."""
    if not lemma or not citation:
        return False

    lem = lemma.strip().lower()
    cit_lower = citation.lower().strip()

    lem_pat = rf"(?<![а-яіїєґa-z0-9]){re.escape(lem)}(?![а-яіїєґa-z0-9])"
    if not re.search(lem_pat, cit_lower):
        return False

    raw_clauses = re.split(
        r"[.!?;\n]+|,\s*(?=(?:not\b|never\b|don't\b|do\s+not\b|avoid\b|use\b|prefer\b|choose\b|adopt\b|а\s+не\b|але\s+не\b|та\s+не\b|і\s+не\b|й\s+не\b|ані\b|не\b|вжива\w*|пишіть\w*|кажіть\w*|обирайте\w*|використову\w*|уника\w*|замість\b|натомість\b|на\s+відміну\s+від\b|instead\s+of\b|rather\s+than\b|but\b|проте\b|однак\b|але\b))",
        cit_lower,
    )
    clauses = [c.strip() for c in raw_clauses if c.strip()]
    lem_clauses = [c for c in clauses if re.search(lem_pat, c)]
    if not lem_clauses:
        return False

    pos_pred_re = re.compile(
        r"\b(?:правильн\w*|норм\w*|питом\w*|стандарт\w*|чинн\w*|літературн\w*|автентичн\w*)\b",
        re.IGNORECASE,
    )
    neg_pred_re = re.compile(
        r"\b(?:кальк\w*|помилк\w*|неправильн\w*|суржик\w*|росіянізм\w*|не\s+рекоменд\w*|уника\w*|штучн\w*)\b",
        re.IGNORECASE,
    )

    # Pass 1: evaluate whether any clause explicitly rejects lemma or whether lemma is in a rejected role
    for c in lem_clauses:
        # Negated replacement: "do not replace <A> with <B>" -> B is prohibited/rejected
        m_neg_replace = re.search(
            r"\b(?:do\s+not|don't|never|not)\s+(?:\w+\s+)*replace\s+(.+?)\s+(?:with|by)\s+([^;.!?\n]+)",
            c,
        )
        if m_neg_replace:
            b_text = m_neg_replace.group(2)
            if re.search(lem_pat, b_text):
                return False

        # Affirmative replacement: "replace <A> with <B>" -> A is replaced/rejected
        m_replace = re.search(r"\breplace\s+(.+?)\s+(?:with|by)\s+([^;.!?\n]+)", c)
        if m_replace and not re.search(r"\b(?:do\s+not|don't|never|not)\s+(?:\w+\s+)*replace\b", c):
            a_text = m_replace.group(1)
            b_text = m_replace.group(2)
            if re.search(lem_pat, a_text) and not re.search(lem_pat, b_text):
                return False

        # Negated / affirmative "замініть <A> на <B>"
        m_neg_zamin = re.search(
            r"\b(?:не\s+(?:\w+\s+)?(?:замінюйте|замінювати|варто\s+замінювати|слід\s+замінювати))\s+(.+?)\s+на\s+([^;.!?\n]+)",
            c,
        )
        if m_neg_zamin:
            b_text = m_neg_zamin.group(2)
            if re.search(lem_pat, b_text):
                return False

        m_zamin = re.search(r"\b(?:замініть|замінити)\s+(.+?)\s+на\s+([^;.!?\n]+)", c)
        if m_zamin and not re.search(r"\bне\b", c):
            a_text = m_zamin.group(1)
            b_text = m_zamin.group(2)
            if re.search(lem_pat, a_text) and not re.search(lem_pat, b_text):
                return False

        # Substitute
        m_subst = re.search(r"\bsubstitute\s+(.+?)\s+for\s+([^;.!?\n]+)", c)
        if m_subst:
            b_text = m_subst.group(1)
            a_text = m_subst.group(2)
            if re.search(r"\b(?:do\s+not|don't|never|not)\b", c):
                if re.search(lem_pat, b_text):
                    return False
            else:
                if re.search(lem_pat, a_text) and not re.search(lem_pat, b_text):
                    return False

        # "замість <A> [вживайте] <B>" -> A is rejected
        m_zamist = re.search(
            r"(?:замість|натомість)\s+(.+?)\s*(?:[,;:—–-]|(?:\s+(?:вжива\w*|використову\w*|краще|варто|слід|обирай\w*|беріть|треба)))\s*([^;.!?\n]+)",
            c,
        )
        if m_zamist:
            a_text = m_zamist.group(1)
            b_text = m_zamist.group(2)
            if re.search(r"\bне\b", c):
                if re.search(lem_pat, b_text):
                    return False
            else:
                if re.search(lem_pat, a_text) and not re.search(lem_pat, b_text):
                    return False

        # Instead of / rather than / замість
        m_inv_zamist = re.search(
            r"([^:;.!?\n]+?)\s+(?:замість|натомість|на\s+відміну\s+від|rather\s+than|instead\s+of)\s+([^;.!?\n]+)",
            c,
        )
        if m_inv_zamist:
            b_text = m_inv_zamist.group(1).strip()
            a_text = m_inv_zamist.group(2).strip()
            if b_text:
                has_b_neg = bool(re.search(r"\b(?:never|not|don't|do\s+not|avoid|не|уникати)\b", b_text))
                if has_b_neg:
                    if re.search(lem_pat, b_text):
                        return False
                else:
                    if re.search(lem_pat, a_text) and not re.search(lem_pat, b_text):
                        return False

        # <B> (а не <A>) or <B>, not <A>
        m_ane = re.search(
            r"(?<!\bdo\s)(?<!\bdon't\s)(?<!\bnever\s)(?:,\s*|\s*\()(?:а\s+не|not)\s+([^)\n,;.!?]+)\)?",
            c,
        )
        if m_ane:
            a_text = m_ane.group(1)
            if re.search(lem_pat, a_text):
                return False

        # <A> — <B> dash construction
        c_body = re.sub(r"^[\w\-]+:\s*", "", c)
        dash_parts = [p.strip() for p in re.split(r"\s*(?:—|–|→)\s*", c_body) if p.strip()]
        if len(dash_parts) >= 2:
            a_text = dash_parts[0]
            b_text = dash_parts[-1]
            if neg_pred_re.search(b_text) and re.search(lem_pat, a_text):
                return False
            elif pos_pred_re.search(b_text):
                pass
            elif re.search(lem_pat, a_text) and not re.search(lem_pat, b_text):
                return False

        # General clause-level negative patterns
        clause_neg_patterns = [
            rf"\b(?:do\s+not|don't|never)\s+(?:\w+\s+)*(?:use|prefer|choose|adopt)\s+(?:(?!\binstead\s+of\b|\brather\s+than\b|\bзамість\b)[^;.!?\n])*{lem_pat}",
            rf"\b(?:avoid|stop)\s+(?:\w+\s+)*{lem_pat}",
            rf"\b(?:not|never|don't|do\s+not|а\s+не|але\s+не|та\s+не|і\s+не|не|ані)\s+[«\"']?{lem_pat}\b",
            rf"{lem_pat}\s+(?:is\s+)?(?:not|n't|never)\s+(?:correct|recommended|standard|valid|appropriate|preferred|the\s+norm)",
            rf"{lem_pat}\s+(?:is\s+)?(?:incorrect|deprecated|a\s+calque|calque|avoided|an\s+error|wrong|unacceptable)",
            rf"\b(?:not|n't)\s+(?:recommended|correct|standard|valid|appropriate)\s*(?:to\s+use|:)?\s*[^;.!?\n]*{lem_pat}",
            rf"\b(?:incorrect|deprecated|calque|wrong|error)\s*[:—–-]?\s*[^;.!?\n]*{lem_pat}",
            rf"(?:не\s+(?:\w+\s+)?(?:вживати|вживайте|вживається|варто|слід|можна|рекомендовано|радимо|доцільно))\s+(?:слово|форму|варіант|термін)?\s*[«\"']?{lem_pat}",
            rf"{lem_pat}\s*[:—–-]?\s*(?:—|-|–|є|це|\b)\s*(?:не\s+(?:є\s+)?(?:правильн\w*|норм\w*|питом\w*|стандарт\w*|чинн\w*|літературн\w*|рекоменд\w*|вжива\w*))",
            rf"{lem_pat}\s*[:—–-]?\s*(?:—|-|–|є|це|\b)\s*(?:кальк\w*|помилк\w*|неправильн\w*|суржик\w*|росіянізм\w*|не\s+рекоменд\w*|уника\w*)",
            rf"(?:уника(?:ти|йте|тиме|тимуть))\s+(?:слово|форму|варіант|термін)?\s*[«\"']?{lem_pat}",
            rf"(?:помилков\w*|неправильн\w*|кальк\w*|суржик\w*|росіянізм\w*)\s*[:—–-]?\s*(?:як-от|зокрема)?\s*[«\"']?{lem_pat}",
        ]
        for pat in clause_neg_patterns:
            if re.search(pat, c):
                return False

    # Pass 2: check whether any clause positively recommends lemma
    for c in lem_clauses:
        # Affirmative replacement: "replace <A> with <B>" -> B is recommended
        m_replace = re.search(r"\breplace\s+(.+?)\s+(?:with|by)\s+([^;.!?\n]+)", c)
        if m_replace and not re.search(r"\b(?:do\s+not|don't|never|not)\s+(?:\w+\s+)*replace\b", c):
            b_text = m_replace.group(2)
            if re.search(lem_pat, b_text):
                return True

        # Affirmative "замініть <A> на <B>" -> B is recommended
        m_zamin = re.search(r"\b(?:замініть|замінити)\s+(.+?)\s+на\s+([^;.!?\n]+)", c)
        if m_zamin and not re.search(r"\bне\b", c):
            b_text = m_zamin.group(2)
            if re.search(lem_pat, b_text):
                return True

        # Affirmative substitute <B> for <A> -> B is recommended
        m_subst = re.search(r"\bsubstitute\s+(.+?)\s+for\s+([^;.!?\n]+)", c)
        if m_subst and not re.search(r"\b(?:do\s+not|don't|never|not)\b", c):
            b_text = m_subst.group(1)
            if re.search(lem_pat, b_text):
                return True

        # "замість <A> [вживайте] <B>" -> B is recommended
        m_zamist = re.search(
            r"(?:замість|натомість)\s+(.+?)\s*(?:[,;:—–-]|(?:\s+(?:вжива\w*|використову\w*|краще|варто|слід|обирай\w*|беріть|треба)))\s*([^;.!?\n]+)",
            c,
        )
        if m_zamist and not re.search(r"\bне\b", c):
            b_text = m_zamist.group(2)
            if re.search(lem_pat, b_text):
                return True

        # "<B> замість <A>"
        m_inv_zamist = re.search(
            r"([^:;.!?\n]+?)\s+(?:замість|натомість|на\s+відміну\s+від|rather\s+than|instead\s+of)\s+([^;.!?\n]+)",
            c,
        )
        if m_inv_zamist:
            b_text = m_inv_zamist.group(1).strip()
            a_text = m_inv_zamist.group(2).strip()
            if b_text:
                has_b_neg = bool(re.search(r"\b(?:never|not|don't|do\s+not|avoid|не|уникати)\b", b_text))
                if has_b_neg:
                    if re.search(lem_pat, a_text):
                        return True
                else:
                    if re.search(lem_pat, b_text):
                        return True

        # "<B> (а не <A>)" or "<B>, not <A>" -> B is recommended
        m_ane = re.search(
            r"(?<!\bdo\s)(?<!\bdon't\s)(?<!\bnever\s)(?:,\s*|\s*\()(?:а\s+не|not)\s+([^)\n,;.!?]+)\)?",
            c,
        )
        if m_ane:
            b_text = c[: m_ane.start()]
            if re.search(lem_pat, b_text):
                return True

        # "<A> — <B>" -> B is recommended, or A is recommended if B is a positive predicate
        c_body = re.sub(r"^[\w\-]+:\s*", "", c)
        dash_parts = [p.strip() for p in re.split(r"\s*(?:—|–|→)\s*", c_body) if p.strip()]
        if len(dash_parts) >= 2:
            a_text = dash_parts[0]
            b_text = dash_parts[-1]
            if (pos_pred_re.search(b_text) and re.search(lem_pat, a_text)) or (
                not neg_pred_re.search(b_text) and re.search(lem_pat, b_text)
            ):
                return True

        # Clause-level positive patterns
        clause_pos_patterns = [
            # English
            rf"\b(?:use|prefer|recommended|correct|standard|valid|appropriate)\s+[^;.!?\n]*{lem_pat}",
            rf"{lem_pat}\s+(?:is\s+)?(?:recommended|correct|standard|valid|appropriate|the\s+standard|preferred)",
            rf"(?:living\s+standard|normative|standard)\s*[:—–-]?\s*[^;.!?\n]*{lem_pat}",
            # Ukrainian
            rf"(?:правильн\w*|краще|варто|слід|рекоменд\w*|радимо|доцільно|доречно|потрібно|необхідно|нормативн\w*)\s+[^;.!?\n]*{lem_pat}",
            rf"(?:вжива\w*|пишіть|кажіть|говоріть|використову\w*|обирайте|надавайте\s+перевагу)\s+[^;.!?\n]*{lem_pat}",
            rf"(?:слово|термін|форма|варіант)?\s*[«\"'\s]?{lem_pat}[»\"'\s]?\s*(?:—|-|–|є|це)\s*(?:це\s+)?(?:питом\w*|автентичн\w*|нормативн\w*|правильн\w*|чинн\w*|літературн\w*)(?:\s+\w+)?(?:\s+(?:відповідник\w*|стандарт\w*|варіант\w*|слово\w*|форма\w*|норм\w*))?",
            rf"(?:питом\w*|автентичн\w*|нормативн\w*|правильн\w*|чинн\w*|літературн\w*|живий\s+стандарт)\s+[^;.!?\n]*{lem_pat}",
        ]
        for pat in clause_pos_patterns:
            if re.search(pat, c):
                return True

    return False


def synthesize_trajectory_and_dpo(
    candidate: CalqueCandidate,
    vesum_counts: dict[str, int],
    textbook_attestations: dict[str, dict[str, Any] | None],
    dict_attestations: dict[str, str | None],
) -> tuple[dict[str, Any], dict[str, Any]] | None:
    """Synthesize an SFT reasoning trajectory and a contrastive DPO pair conforming to schemas."""
    target_term = candidate.target_term
    suggestions = candidate.suggestions

    verified_alts = [s for s in suggestions if vesum_counts.get(s, 0) > 0]
    if not verified_alts:
        return None

    traj_id = compute_id("traj", target_term)
    dpo_id = compute_id("dpo", target_term)

    vesum_attestation = []
    for s in suggestions:
        count = vesum_counts.get(s, 0)
        vesum_attestation.append(
            {
                "lemma": s,
                "vesum_forms_count": count,
                "is_standard_attested": count > 0,
            }
        )

    spectrum_alts = []
    prov_tag = candidate.source_tag
    prov_note = candidate.provenance_note
    prov_suffix = f" (джерело: {prov_tag}"
    if prov_note:
        prov_suffix += f", {prov_note}"
    prov_suffix += ")"

    for s in verified_alts:
        tb = textbook_attestations.get(s)
        dict_att = dict_attestations.get(s)
        matching_curated = [ev for ev in (candidate.curated_evidence or []) if is_positive_citation(s, ev)]
        if tb:
            evidence = f"Підручник МОН «{tb['subject']}» {tb['grade']} клас ({tb['author']}); цитата: «{tb['snippet']}»{prov_suffix}"
            tier = "living_standard"
        elif matching_curated:
            evidence = f"{'; '.join(matching_curated[:2])}{prov_suffix}"
            tier = "living_standard"
        elif dict_att:
            evidence = f"{dict_att}{prov_suffix}"
            tier = "classical_regional" if "Грінченка" in dict_att else "living_standard"
        else:
            evidence = (
                f"Словозмінна парадигма зафіксована у словниковій базі ВЕСУМ ({vesum_counts[s]} словоформ); "
                f"без прямого шкільного підручникового чи словникового контексту{prov_suffix}"
            )
            tier = "technical_compound" if ("-" in s or len(s.split()) > 1) else "classical_regional"

        spectrum_alts.append(
            {
                "lemma": s,
                "register_tier": tier,
                "evidence_source": evidence,
            }
        )

    for s in suggestions:
        if vesum_counts.get(s, 0) == 0:
            spectrum_alts.append(
                {
                    "lemma": s,
                    "register_tier": "purist_neologism",
                    "evidence_source": f"Відсутній у ВЕСУМ (0 словоформ); пуристичний або діаспорний неологізм{prov_suffix}",
                }
            )

    # Ensure there is at least one verified living standard alternative with addressable evidence.
    # If no living standard alternative exists with verified textbook, dictionary, or curated evidence,
    # refuse normative synthesis to avoid teaching unsupported living-standard claims.
    living_candidates = [alt for alt in spectrum_alts if alt["register_tier"] == "living_standard"]
    if not living_candidates:
        return None

    primary_alt_info = living_candidates[0]
    primary_alt = primary_alt_info["lemma"]
    primary_evidence = primary_alt_info["evidence_source"]

    calque_category, source_formation_desc, equiv_mechanism_desc = classify_calque_type(target_term)

    morphemic_breakdown = {
        "source_formation": source_formation_desc,
        "ukrainian_equivalent_mechanism": equiv_mechanism_desc,
    }

    if calque_category == "active_participle":
        historical_note = (
            f"В українській літературній мові активні дієприкметники теперішнього часу на -уч-/-яч- (як-от «{target_term}») "
            "є нетиповими; граматична норма надає перевагу описовим конструкціям, віддієслівним прикметникам або дієсловам."
        )
    elif calque_category == "prefixal_calque":
        historical_note = (
            f"Префіксальна словотвірна модель у формі «{target_term}» не відповідає питомій українській дериваційній нормі; "
            "нормативні порадники радять уживати безпрефіксні варіанти або форми з питомими префіксами."
        )
    elif calque_category == "phrasal_calque":
        historical_note = (
            f"Словосполучення «{target_term}» відтворює синтаксичну кальку чужомовного звороту; "
            "українська синтаксична норма вимагає природних безприйменникових або питомих прийменникових конструкцій."
        )
    else:
        historical_note = (
            f"Форма «{target_term}» кваліфікується як калькований або нерекомендований варіант у сучасних "
            "довідниках з культури мови та лексикографічних джерелах."
        )

    if prov_note:
        historical_note = f"{prov_note}. {historical_note}"

    lexicographical_context = {
        "historical_suppression_note": historical_note,
        "restoration_era": (
            "Сучасна українська мовна стандартизація, чинний Правопис 2019, праці Бориса Антоненка-Давидовича, "
            "Олени Курило та стандарти Національної комісії зі стандартів державної мови."
        ),
    }

    reasoning_steps = [
        f"1. Етимологія та словотвірна діагностика: Визначено дериваційну проблему форми «{target_term}» ({calque_category}). {source_formation_desc}",
        f"2. Питома словотвірна модель: Відновлено природний словотвірний механізм. {equiv_mechanism_desc}",
        f"3. Морфологічна верифікація за словником ВЕСУМ: Рекомендований варіант «{primary_alt}» має повну словозмінну парадигму ({vesum_counts[primary_alt]} словоформ у базі даних).",
        f"4. Реєстрове узгодження та контекст уживання: Варіант «{primary_alt}» належить до нормативного живого стандарту (living_standard). Підтверджено джерелом: {primary_evidence}.",
        f"5. Нормативний висновок і практична рекомендація: Слід уникати калькованої форми «{target_term}», послідовно вживаючи питоме «{primary_alt}».",
    ]

    final_response = (
        f"Правильно вживати «{primary_alt}». Вживання форми «{target_term}» є типовою калькою з російської мови. "
        f"{equiv_mechanism_desc} "
        f"Питоме українське слово «{primary_alt}» відповідає чинній мовній нормі та має повну парадигму словозміни "
        f"у морфологічній базі ВЕСУМ ({vesum_counts[primary_alt]} словоформ). "
        f"Нормативне засвідчення: {primary_evidence}."
    )

    query = f"Як правильно сказати або написати українською: «{target_term}» чи «{primary_alt}»?"

    trajectory = {
        "schema_version": "v1_decolonization_trajectory",
        "trajectory_id": traj_id,
        "query": query,
        "target_term": target_term,
        "is_calque_or_russianism": True,
        "morphemic_breakdown": morphemic_breakdown,
        "lexicographical_context": lexicographical_context,
        "vesum_attestation": vesum_attestation,
        "register_spectrum": {
            "primary_living_standard": primary_alt,
            "alternatives": spectrum_alts,
        },
        "reasoning_steps": reasoning_steps,
        "final_response": final_response,
    }

    rejected_response = (
        f"Можна вживати як «{target_term}», так і «{primary_alt}». Обидва варіанти зустрічаються в текстах і є "
        f"рівноправними синонімами в сучасній мові, тому вибір залежить лише від уподобань автора."
    )

    dpo_pair = {
        "schema_version": "v1_decolonization_dpo_pair",
        "pair_id": dpo_id,
        "prompt": query,
        "chosen": final_response,
        "rejected": rejected_response,
        "metadata": {
            "target_term": target_term,
            "rejected_flaw": "soviet_lexicography_acceptance",
            "primary_alternative": primary_alt,
            "vesum_verified": True,
        },
    }

    return trajectory, dpo_pair


def scan_generated_files(file_paths: list[Path]) -> tuple[bool, bool, list[str]]:
    """Scan generated files for private host paths and restricted private source leaks."""
    violations: list[str] = []
    has_private_paths = False
    has_restricted_sources = False

    for fp in file_paths:
        if not fp.is_file():
            continue
        with fp.open("r", encoding="utf-8") as f:
            for line_no, line in enumerate(f, 1):
                for pat in PRIVATE_PATH_PATTERNS:
                    if pat.search(line):
                        has_private_paths = True
                        violations.append(f"{fp.name}:{line_no}: private host path: {line[:80]}...")
                for pat in RESTRICTED_SOURCE_PATTERNS:
                    if pat.search(line):
                        has_restricted_sources = True
                        violations.append(f"{fp.name}:{line_no}: restricted private source leak: {line[:80]}...")

    return not has_private_paths, not has_restricted_sources, violations


def get_partition_for_term(term: str, train_ratio: float = 0.8) -> str:
    """Deterministically partition a calque term into 'train' or 'held_out'."""
    norm = normalize_text(term).lower()
    digest = hashlib.sha256(f"uldr_partition_v1:{norm}".encode()).hexdigest()
    ratio_val = int(digest[:8], 16) / 0xFFFFFFFF
    return "train" if ratio_val < train_ratio else "held_out"


def generate_pipeline(
    lt_replacements_path: Path,
    sources_db_path: Path,
    vesum_db_path: Path,
    out_dir: Path,
    limit: int | None = 1200,
    records_per_shard: int = 400,
    train_ratio: float = 0.8,
    verify_schema: bool = True,
    max_shard_bytes: int = MAX_SHARD_BYTES,
) -> dict[str, Any]:
    """Execute the ULDR dataset generation pipeline with partitioning, sharding, and manifest receipts."""
    out_dir.mkdir(parents=True, exist_ok=True)
    # Clean prior JSONL files in out_dir to prevent orphan shards
    for stale_file in out_dir.glob("decolonization_*.jsonl"):
        stale_file.unlink()

    traj_validator = None
    dpo_validator = None
    if verify_schema:
        with TRAJECTORY_SCHEMA_PATH.open("r", encoding="utf-8") as f:
            traj_schema = json.load(f)
            jsonschema.Draft202012Validator.check_schema(traj_schema)
            traj_validator = jsonschema.Draft202012Validator(traj_schema)
        with DPO_PAIR_SCHEMA_PATH.open("r", encoding="utf-8") as f:
            dpo_schema = json.load(f)
            jsonschema.Draft202012Validator.check_schema(dpo_schema)
            dpo_validator = jsonschema.Draft202012Validator(dpo_schema)

    candidates = load_calque_candidates(lt_replacements_path, sources_db_path)

    total_trajs = 0
    vesum_verification_count = 0
    textbook_attestation_count = 0
    dict_attestation_count = 0
    generated_shards: list[dict[str, Any]] = []

    partitions = ("train", "held_out")
    partition_state: dict[str, dict[str, Any]] = {
        p: {
            "shard_idx": 1,
            "current_shard_count": 0,
            "current_t_bytes": 0,
            "current_d_bytes": 0,
            "total_count": 0,
            "traj_fh": None,
            "dpo_fh": None,
            "current_t_path": None,
            "current_d_path": None,
            "terms": set(),
        }
        for p in partitions
    }

    def open_shard(part: str, idx: int) -> tuple[Any, Any, Path, Path]:
        t_path = out_dir / f"decolonization_trajectories_{part}_part{idx:03d}.jsonl"
        d_path = out_dir / f"decolonization_dpo_pairs_{part}_part{idx:03d}.jsonl"
        return t_path.open("w", encoding="utf-8"), d_path.open("w", encoding="utf-8"), t_path, d_path

    # Reuse persistent read-only SQLite connections across candidate iterations
    conn_sources: sqlite3.Connection | None = None
    conn_vesum: sqlite3.Connection | None = None
    if sources_db_path.is_file():
        conn_sources = sqlite3.connect(f"file:{sources_db_path.resolve()}?mode=ro", uri=True)
    if vesum_db_path.is_file():
        conn_vesum = sqlite3.connect(f"file:{vesum_db_path.resolve()}?mode=ro", uri=True)

    try:
        for candidate in candidates:
            if limit is not None and total_trajs >= limit:
                break

            suggestions = candidate.suggestions
            vesum_counts = get_vesum_counts(suggestions, vesum_db_path, conn=conn_vesum)
            tb_attestations = {}
            dict_attestations = {}
            has_tb = False
            has_dict = False
            for s in suggestions:
                if vesum_counts.get(s, 0) > 0:
                    tb = find_textbook_attestation(s, sources_db_path, conn=conn_sources)
                    tb_attestations[s] = tb
                    if tb:
                        has_tb = True
                    dict_att = find_dictionary_attestation(s, sources_db_path, conn=conn_sources)
                    dict_attestations[s] = dict_att
                    if dict_att:
                        has_dict = True

            record = synthesize_trajectory_and_dpo(
                candidate,
                vesum_counts,
                tb_attestations,
                dict_attestations,
            )
            if not record:
                continue

            trajectory, dpo_pair = record

            if verify_schema:
                assert traj_validator is not None
                assert dpo_validator is not None
                traj_validator.validate(trajectory)
                dpo_validator.validate(dpo_pair)

            part = get_partition_for_term(candidate.target_term, train_ratio)
            pstate = partition_state[part]

            if pstate["traj_fh"] is None:
                pstate["traj_fh"], pstate["dpo_fh"], pstate["current_t_path"], pstate["current_d_path"] = open_shard(
                    part, pstate["shard_idx"]
                )

            t_line = json.dumps(trajectory, ensure_ascii=False) + "\n"
            d_line = json.dumps(dpo_pair, ensure_ascii=False) + "\n"
            t_bytes = len(t_line.encode("utf-8"))
            d_bytes = len(d_line.encode("utf-8"))

            if pstate["current_shard_count"] > 0 and (
                pstate["current_shard_count"] >= records_per_shard
                or pstate["current_t_bytes"] + t_bytes > max_shard_bytes
                or pstate["current_d_bytes"] + d_bytes > max_shard_bytes
            ):
                pstate["traj_fh"].close()
                pstate["dpo_fh"].close()
                cur_t = pstate["current_t_path"]
                cur_d = pstate["current_d_path"]
                assert cur_t is not None and cur_d is not None
                generated_shards.append(
                    {
                        "shard_index": pstate["shard_idx"],
                        "partition": part,
                        "trajectories_file": cur_t.name,
                        "trajectories_bytes": cur_t.stat().st_size,
                        "trajectories_sha256": hashlib.sha256(cur_t.read_bytes()).hexdigest(),
                        "dpo_pairs_file": cur_d.name,
                        "dpo_pairs_bytes": cur_d.stat().st_size,
                        "dpo_pairs_sha256": hashlib.sha256(cur_d.read_bytes()).hexdigest(),
                        "records_count": pstate["current_shard_count"],
                    }
                )
                pstate["shard_idx"] += 1
                pstate["current_shard_count"] = 0
                pstate["current_t_bytes"] = 0
                pstate["current_d_bytes"] = 0
                pstate["traj_fh"], pstate["dpo_fh"], pstate["current_t_path"], pstate["current_d_path"] = open_shard(
                    part, pstate["shard_idx"]
                )

            pstate["traj_fh"].write(t_line)
            pstate["dpo_fh"].write(d_line)
            pstate["current_shard_count"] += 1
            pstate["current_t_bytes"] += t_bytes
            pstate["current_d_bytes"] += d_bytes
            pstate["total_count"] += 1
            pstate["terms"].add(candidate.target_term)

            total_trajs += 1
            if any(v["is_standard_attested"] for v in trajectory.get("vesum_attestation", [])):
                vesum_verification_count += 1
            if has_tb:
                textbook_attestation_count += 1
            if has_dict:
                dict_attestation_count += 1

        for part in partitions:
            pstate = partition_state[part]
            if pstate["traj_fh"] and not pstate["traj_fh"].closed:
                pstate["traj_fh"].close()
                pstate["dpo_fh"].close()
                cur_t = pstate["current_t_path"]
                cur_d = pstate["current_d_path"]
                if pstate["current_shard_count"] > 0:
                    assert cur_t is not None and cur_d is not None
                    generated_shards.append(
                        {
                            "shard_index": pstate["shard_idx"],
                            "partition": part,
                            "trajectories_file": cur_t.name,
                            "trajectories_bytes": cur_t.stat().st_size,
                            "trajectories_sha256": hashlib.sha256(cur_t.read_bytes()).hexdigest(),
                            "dpo_pairs_file": cur_d.name,
                            "dpo_pairs_bytes": cur_d.stat().st_size,
                            "dpo_pairs_sha256": hashlib.sha256(cur_d.read_bytes()).hexdigest(),
                            "records_count": pstate["current_shard_count"],
                        }
                    )
    finally:
        for pstate in partition_state.values():
            if pstate["traj_fh"] and not pstate["traj_fh"].closed:
                pstate["traj_fh"].close()
            if pstate["dpo_fh"] and not pstate["dpo_fh"].closed:
                pstate["dpo_fh"].close()
        if conn_sources is not None:
            conn_sources.close()
        if conn_vesum is not None:
            conn_vesum.close()

    # Verify partition isolation (firewall)
    train_terms = partition_state["train"]["terms"]
    held_out_terms = partition_state["held_out"]["terms"]
    overlap = train_terms.intersection(held_out_terms)
    if overlap:
        raise RuntimeError(f"Contamination detected! Train and held-out partitions overlap on terms: {overlap}")

    # Active private path and restricted source scan
    shard_paths = []
    for s in generated_shards:
        shard_paths.append(out_dir / s["trajectories_file"])
        shard_paths.append(out_dir / s["dpo_pairs_file"])

    zero_paths, zero_restricted, violations = scan_generated_files(shard_paths)
    if violations:
        raise RuntimeError("Private content leak detected in generated dataset:\n" + "\n".join(violations))

    manifest = {
        "dataset_name": "Ukrainian Linguistic Decolonization & Reasoning (ULDR)",
        "schema_version": "v1",
        "total_trajectories": total_trajs,
        "total_dpo_pairs": total_trajs,
        "partition_counts": {
            "train": partition_state["train"]["total_count"],
            "held_out": partition_state["held_out"]["total_count"],
        },
        "partition_firewall": {
            "verified_partition_isolation": True,
            "train_held_out_overlap_count": len(overlap),
            "train_ratio_target": train_ratio,
        },
        "quality_metrics": {
            "vesum_verification_count": vesum_verification_count,
            "vesum_verification_denominator": total_trajs,
            "vesum_verification_rate": (round(vesum_verification_count / total_trajs, 4) if total_trajs > 0 else 0.0),
            "textbook_attestation_rate": (
                round(textbook_attestation_count / total_trajs, 4) if total_trajs > 0 else 0.0
            ),
            "textbook_attestation_count": textbook_attestation_count,
            "dictionary_attestation_rate": (round(dict_attestation_count / total_trajs, 4) if total_trajs > 0 else 0.0),
            "dictionary_attestation_count": dict_attestation_count,
            "zero_private_paths": zero_paths,
            "zero_restricted_sources": zero_restricted,
        },
        "shards": generated_shards,
    }

    manifest_path = out_dir / "decolonization_manifest.json"
    with manifest_path.open("w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
        f.write("\n")

    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="ULDR Dataset Generator Pipeline")
    parser.add_argument("--lt-replacements", type=Path, default=DEFAULT_LT_REPLACEMENTS)
    parser.add_argument("--sources-db", type=Path, default=DEFAULT_SOURCES_DB)
    parser.add_argument("--vesum-db", type=Path, default=DEFAULT_VESUM_DB)
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=REPO_ROOT / "data" / "projects" / "open_model_data" / "decolonization" / "generated",
    )
    parser.add_argument("--limit", type=int, default=1200)
    parser.add_argument("--records-per-shard", type=int, default=400)
    parser.add_argument("--train-ratio", type=float, default=0.8)
    parser.add_argument("--no-verify-schema", action="store_true", default=False)

    args = parser.parse_args()
    manifest = generate_pipeline(
        lt_replacements_path=args.lt_replacements,
        sources_db_path=args.sources_db,
        vesum_db_path=args.vesum_db,
        out_dir=args.out_dir,
        limit=args.limit,
        records_per_shard=args.records_per_shard,
        train_ratio=args.train_ratio,
        verify_schema=not args.no_verify_schema,
    )
    print(
        f"Generated {manifest['total_trajectories']} trajectories and {manifest['total_dpo_pairs']} DPO pairs "
        f"across {len(manifest['shards'])} shard(s)."
    )
    print(f"Partition counts: {manifest['partition_counts']}")
    print(
        f"Partition firewall: verified_isolation={manifest['partition_firewall']['verified_partition_isolation']}, "
        f"overlap={manifest['partition_firewall']['train_held_out_overlap_count']}"
    )
    print(f"Textbook attestation rate: {manifest['quality_metrics']['textbook_attestation_rate']:.2%}")
    print(f"Dictionary attestation rate: {manifest['quality_metrics']['dictionary_attestation_rate']:.2%}")
    print(f"Zero private paths: {manifest['quality_metrics']['zero_private_paths']}")
    print(f"Zero restricted sources: {manifest['quality_metrics']['zero_restricted_sources']}")
    print(f"Receipt written to {args.out_dir / 'decolonization_manifest.json'}")


if __name__ == "__main__":
    main()
