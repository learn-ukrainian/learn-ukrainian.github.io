#!/usr/bin/env python3
"""Run the frozen, judge-free lexical retrieval probe for issue #9233.

Use this to compare textbook chunk retrieval with production section retrieval;
do not use it to select embeddings or judge semantic relevance. It writes only
the query set and generated report under the requested output directory, plus
an ephemeral lemma index under ``--temp-dir``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import re
import resource
import sqlite3
import statistics
import subprocess
import sys
import tempfile
import time
import types
import unicodedata
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.lib.readonly_sqlite import open_readonly as _shared_open_readonly
from scripts.verification.vesum import get_vesum_connection
from scripts.wiki import sources_db

PACK_PATH = ROOT / "curriculum/l2-uk-en/evidence/a1/_requests/sounds-letters-and-hello.pack.yaml"
ARC_PATHS = {level: ROOT / f"curriculum/l2-uk-en/lesson-plans/{level}/_arc.yaml" for level in ("a1", "a2")}
GRAMMAR_SOURCE = ROOT / "docs/epics/fresh-build-a2-arc.md"
GRAMMAR_TEXTBOOK_CHUNK = "11-klas-ukrajinska-mova-avramenko-2019_s0059"
EXPECTED_DESIGN_SHA256 = "6f59c17dd04c3e9e189b521c73a28b392f9aa1fc102f2370a4f48fdd60704e7e"
V5_DESIGN_SHA256 = "84952a41ca3f73865b284e18445b5d14b4320941a3b3fbb8dc386201684ef23d"
STRESS_MARKS = str.maketrans({"\u0301": None, "\u0300": None})
APOSTROPHES = str.maketrans({"’": "'", "ʼ": "'", "ʻ": "'", "՚": "'", "＇": "'"})
TOKEN_RE = re.compile(r"[\w\u0300\u0301]+(?:['’ʼʻ՚＇][\w\u0300\u0301]+)*", re.UNICODE)
CYRILLIC_RE = re.compile(r"[а-яґєії]", re.IGNORECASE)
ENGLISH_STOP = frozenset(
    [
        "a",
        "an",
        "and",
        "are",
        "as",
        "at",
        "be",
        "between",
        "by",
        "for",
        "from",
        "in",
        "is",
        "of",
        "on",
        "or",
        "the",
        "to",
        "with",
    ]
)
UKRAINIAN_STOP = frozenset(
    ["а", "або", "але", "в", "від", "до", "з", "за", "і", "й", "на", "не", "у", "та", "що", "це", "як", "про", "для"]
)

# This source-owned category inventory is taken from the A2 arc rationale;
# VESUM supplies every generated inflected form.
GRAMMAR_TERM_SOURCES = {
    "case": "відмінок",
    "gender": "рід",
    "number": "число",
    "verb": "дієслово",
    "aspect": "вид",
    "tense": "час",
    "mood": "спосіб",
    "sentence": "речення",
}
GRAMMAR_CATEGORY_RE = {
    "case": re.compile(r"\bcase(?:s)?\b|genitive|dative|accusative|instrumental|locative|vocative|nominative", re.I),
    "gender": re.compile(r"\bgender\b", re.I),
    "number": re.compile(r"\bnumber\b|\bplural\b|\bsingular\b", re.I),
    "aspect": re.compile(r"\baspect\b", re.I),
    "tense": re.compile(r"\btense\b|\bpast\b|\bpresent\b|\bfuture\b", re.I),
    "mood": re.compile(r"\bmood\b|\bimperative\b|\bconditional\b", re.I),
    "sentence": re.compile(r"\bsentence\b|\bsyntax\b|\bclause\b", re.I),
    "verb": re.compile(r"\bverb\w*\b|\bconjugat\w*\b|\binfinitive\b", re.I),
}
WORD_FORM_RE = re.compile(r"^[\w'’ʼʻ՚＇-]+$", re.UNICODE)


def normalize_token(value: str) -> str:
    """Fold stress, Unicode variants, and apostrophe variants for both arms."""
    return unicodedata.normalize("NFC", value.translate(STRESS_MARKS).translate(APOSTROPHES)).casefold()


def tokenize(text: str) -> list[str]:
    folded = unicodedata.normalize("NFC", text.translate(STRESS_MARKS).translate(APOSTROPHES))
    return [normalize_token(match.group(0)).strip("'-") for match in TOKEN_RE.finditer(folded)]


def _ro_connect(path: Path) -> sqlite3.Connection:
    connection = _shared_open_readonly(path.resolve())
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA query_only = ON")
    return connection


def _display_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT.resolve()))
    except ValueError:
        return str(path.resolve())


def _get_pack_citations(pack_path: Path) -> list[dict[str, Any]]:
    pack = yaml.safe_load(pack_path.read_text(encoding="utf-8"))
    citations: dict[str, dict[str, Any]] = {}
    for group in ("texts", "exercises"):
        for item in pack.get(group, []) or []:
            source = item.get("source") or {}
            chunk_id = str(source.get("chunk_id") or "").strip()
            if source.get("table") != "textbooks" or not chunk_id:
                continue
            citations.setdefault(
                chunk_id,
                {
                    "chunk_id": chunk_id,
                    "citation_ids": [],
                    "span": item.get("span") or {},
                    "supports": str(item.get("supports") or item.get("pattern") or ""),
                },
            )
            citations[chunk_id]["citation_ids"].append(str(item.get("id", "")))
    return [citations[key] for key in sorted(citations)]


def _get_cited_span(full_text: str, span: dict[str, Any]) -> str:
    """Select the exact first-to-last cited fragment from source text."""
    first_tokens = tokenize(str(span.get("first_words") or ""))
    last_tokens = tokenize(str(span.get("last_words") or ""))
    source_tokens = [
        (normalize_token(match.group(0)), match.start(), match.end()) for match in TOKEN_RE.finditer(full_text)
    ]

    def find_sequence(needle: list[str], after: int = 0) -> tuple[int, int] | None:
        for start in range(after, len(source_tokens) - len(needle) + 1):
            if [item[0] for item in source_tokens[start : start + len(needle)]] == needle:
                return start, start + len(needle) - 1
        return None

    first = find_sequence(first_tokens)
    last = find_sequence(last_tokens, first[0] if first else 0)
    if first and last:
        return full_text[source_tokens[first[0]][1] : source_tokens[last[1]][2]]
    raise ValueError("cited span boundaries do not occur in the cited textbooks chunk")


def _is_content_word(token: str, connection: sqlite3.Connection, *, english: bool = False) -> bool:
    clean = normalize_token(token)
    if len(clean) < 3 or clean in (ENGLISH_STOP if english else UKRAINIAN_STOP):
        return False
    if english:
        return token.isascii() and token.isalpha()
    if not CYRILLIC_RE.search(token):
        return False
    # Keep case at admission: Київ must not become the homograph київ → кий.
    rows = connection.execute(
        "SELECT f.lemma, f.pos, f.tags FROM forms_all f WHERE f.word_form IN (?, ?) AND NOT EXISTS (SELECT 1 FROM form_markers m WHERE m.form_id=f.id AND m.marker IN ('bad','obsc','subst'))",
        (token, clean),
    ).fetchall()
    content_pos = {"noun", "verb", "adj", "adv", "adjective", "participle", "numr"}
    excluded_tags = {"prop", "pron", "arch", "rare", "short"}
    return (
        bool(rows)
        and len({normalize_token(str(row[0])) for row in rows}) == 1
        and all(
            str(row[1]).casefold() in content_pos and not excluded_tags.intersection(str(row[2]).split(":"))
            for row in rows
        )
    )


def _first_paradigm_alternative(token: str, connection: sqlite3.Connection) -> tuple[str, str] | None:
    analyses = connection.execute(
        "SELECT f.lemma FROM forms_all f WHERE f.word_form = ? AND NOT EXISTS (SELECT 1 FROM form_markers m WHERE m.form_id=f.id AND m.marker IN ('bad','obsc','subst')) GROUP BY f.lemma ORDER BY MIN(f.id)",
        (token,),
    ).fetchall()
    if not analyses:
        return None
    source_lemmas = list(dict.fromkeys(normalize_token(str(row[0])) for row in analyses))
    for lemma in source_lemmas:
        if not lemma:
            continue
        forms = connection.execute(
            "SELECT f.word_form FROM forms_all f WHERE f.lemma = ? AND NOT EXISTS (SELECT 1 FROM form_markers m WHERE m.form_id=f.id AND m.marker IN ('bad','obsc','subst')) ORDER BY f.id",
            (lemma,),
        ).fetchall()
        for form in forms:
            candidate = normalize_token(str(form[0]))
            if candidate and candidate != normalize_token(token) and _is_content_word(candidate, connection):
                return candidate, lemma
    return None


def _make_form_mismatch_query(
    span: str, connection: sqlite3.Connection, *, used_queries: set[str] | None = None
) -> dict[str, Any] | None:
    folded = unicodedata.normalize("NFC", span.translate(STRESS_MARKS).translate(APOSTROPHES))
    # Minimal-pair pronunciation drills are marked in the source by dash-
    # separated forms. Their apparent words must not seed a content query.
    drill_ranges = [
        (m.start(), m.end()) for m in re.finditer(r"[а-яґєіїА-ЯҐЄІЇ']+\s*–\s*[а-яґєіїА-ЯҐЄІЇ']+\s*[+–]", folded)
    ]
    selected: list[tuple[str, str, str]] = []
    for match in TOKEN_RE.finditer(folded):
        original = match.group(0)
        if any(start <= match.start() < end for start, end in drill_ranges):
            continue
        # A hyphen-attached syllable is drill/OCR material, not a word.
        if folded[max(0, match.start() - 1) : match.start()] == "-" or folded[match.end() : match.end() + 1] == "-":
            continue
        if not _is_content_word(original, connection):
            continue
        token = normalize_token(original)
        alternative = _first_paradigm_alternative(token, connection)
        if alternative is None:
            continue
        if alternative[0] in {item[1] for item in selected}:
            continue
        selected.append((token, alternative[0], alternative[1]))
    if len(selected) < 2:
        return None
    fallback = None
    for size in range(min(4, len(selected)), 1, -1):
        for group in combinations(selected, size):
            query = " ".join(form for _, form, _ in group)
            fallback = fallback or group
            if query not in (used_queries or set()):
                selected = list(group)
                break
        else:
            continue
        break
    else:
        selected = list(fallback)
    query = " ".join(form for _, form, _ in selected)
    return {
        "query": query,
        "forms": [{"source_form": source, "query_form": form, "lemma": lemma} for source, form, lemma in selected],
        "rule": "2-4 source-span VESUM content words; each replaced by the first different form in its lemma paradigm order",
    }


def _make_english_query(supports: str) -> str:
    tokens = [token for token in tokenize(supports) if _is_content_word(token, None, english=True)]
    return " ".join(tokens[:8])


def _grammar_category(job: str, slug: str) -> str | None:
    value = f"{job} {slug}"
    for category in ("case", "gender", "number", "aspect", "tense", "mood", "sentence", "verb"):
        if GRAMMAR_CATEGORY_RE[category].search(value):
            return category
    return None


def _grammar_forms(base: str, connection: sqlite3.Connection) -> list[str]:
    analyses = connection.execute(
        "SELECT f.lemma FROM forms_all f WHERE f.word_form = ? AND NOT EXISTS (SELECT 1 FROM form_markers m WHERE m.form_id=f.id AND m.marker IN ('bad','obsc','subst')) GROUP BY f.lemma ORDER BY MIN(f.id)",
        (normalize_token(base),),
    ).fetchall()
    lemmas = sorted({normalize_token(str(row[0])) for row in analyses if row[0]})
    if not lemmas:
        return []
    forms: list[str] = []
    for lemma in lemmas:
        rows = connection.execute(
            "SELECT f.word_form FROM forms_all f WHERE f.lemma = ? AND NOT EXISTS (SELECT 1 FROM form_markers m WHERE m.form_id=f.id AND m.marker IN ('bad','obsc','subst')) ORDER BY f.id",
            (lemma,),
        ).fetchall()
        for row in rows:
            form = normalize_token(str(row[0]))
            if form and form not in forms:
                forms.append(form)
            if len(forms) == 3:
                return forms
    return forms


def _first_clean_lemma(token: str, connection: sqlite3.Connection) -> str | None:
    row = connection.execute(
        "SELECT f.lemma FROM forms_all f WHERE f.word_form = ? AND NOT EXISTS (SELECT 1 FROM form_markers m WHERE m.form_id=f.id AND m.marker IN ('bad','obsc','subst')) ORDER BY f.id LIMIT 1",
        (normalize_token(token),),
    ).fetchone()
    return normalize_token(str(row[0])) if row else None


def _case_phrase_from_module(module_path: Path, connection: sqlite3.Connection) -> tuple[str, list[str]] | None:
    if not module_path.is_file():
        return None
    text = module_path.read_text(encoding="utf-8")
    tokens = tokenize(text)
    candidates: list[tuple[tuple[str, str], str]] = []
    nonspecific = {"який", "яка", "яке", "які", "новий", "весь", "цей", "такий"}
    singular_case_forms = {"відмінок", "відмінка", "відмінку", "відмінком", "відмінкові"}
    for index in range(len(tokens) - 1):
        if tokens[index + 1] not in singular_case_forms:
            continue
        adjective_lemma = _first_clean_lemma(tokens[index], connection)
        noun_lemma = _first_clean_lemma(tokens[index + 1], connection)
        if not adjective_lemma or adjective_lemma in nonspecific or noun_lemma != "відмінок":
            continue
        pos = connection.execute(
            "SELECT DISTINCT pos FROM forms_all WHERE word_form = ? ORDER BY id",
            (tokens[index],),
        ).fetchall()
        if not any(str(row[0]).casefold() in {"adj", "adjective"} for row in pos):
            continue
        candidates.append(((adjective_lemma, noun_lemma), " ".join(tokens[index : index + 2])))
    if not candidates:
        return None
    counts = Counter(pair for pair, _ in candidates)
    most_common = counts.most_common()
    if len(most_common) > 1 and most_common[0][1] == most_common[1][1]:
        return None
    selected = most_common[0][0]
    phrase = next(phrase for pair, phrase in candidates if pair == selected)
    return phrase, list(selected)


def _phrase_paradigm_forms(lemmas: list[str], connection: sqlite3.Connection) -> list[str]:
    paradigms: list[list[str]] = []
    for lemma in lemmas:
        rows = connection.execute(
            "SELECT f.word_form FROM forms_all f WHERE f.lemma = ? AND NOT EXISTS (SELECT 1 FROM form_markers m WHERE m.form_id=f.id AND m.marker IN ('bad','obsc','subst')) ORDER BY f.id",
            (lemma,),
        ).fetchall()
        forms = list(dict.fromkeys(normalize_token(str(row[0])) for row in rows))
        paradigms.append(forms)
    if not paradigms or any(not forms for forms in paradigms):
        return []
    output = [" ".join(lemma for lemma in lemmas)]
    alternatives = [[form for form in forms if form != lemma] for lemma, forms in zip(lemmas, paradigms, strict=True)]
    for index in range(2):
        if any(len(forms) <= index for forms in alternatives):
            return []
        output.append(" ".join(forms[index] for forms in alternatives))
    return output


def build_query_set(
    *,
    sources_path: Path,
    vesum_path: Path,
    pack_path: Path = PACK_PATH,
    arc_paths: dict[str, Path] = ARC_PATHS,
    grammar_source: Path = GRAMMAR_SOURCE,
) -> dict[str, Any]:
    """Construct G1/G2 mechanically from the pack, arcs, source text, and VESUM."""
    source_conn = _ro_connect(sources_path)
    with get_vesum_connection(vesum_path) as vesum_conn:
        grammar_source_text = grammar_source.read_text(encoding="utf-8")
        grammar_terms = {}
        grammar_exclusions = {}
        for category, term in GRAMMAR_TERM_SOURCES.items():
            term_source = _display_path(grammar_source)
            if category in {"number", "verb"}:
                row = source_conn.execute(
                    "SELECT text FROM textbooks WHERE chunk_id = ?", (GRAMMAR_TEXTBOOK_CHUNK,)
                ).fetchone()
                term_text = str(row[0]) if row else ""
                term_source = f"textbooks:{GRAMMAR_TEXTBOOK_CHUNK}"
            else:
                term_text = grammar_source_text
            if term not in term_text.casefold():
                grammar_exclusions[category] = "category term absent from its registered source"
                continue
            forms = _grammar_forms(term, vesum_conn)
            if len(forms) < 3:
                grammar_exclusions[category] = "fewer than three clean VESUM paradigm forms"
                continue
            grammar_terms[category] = {"source_text": term, "forms": forms, "source_path": term_source}
        g1: list[dict[str, Any]] = []
        used_queries: set[str] = set()
        citations = _get_pack_citations(pack_path)
        for citation in citations:
            row = source_conn.execute(
                "SELECT chunk_id, text, source_file, subject, parent_section_id FROM textbooks WHERE chunk_id = ? ORDER BY id LIMIT 1",
                (citation["chunk_id"],),
            ).fetchone()
            if row is None:
                raise ValueError(f"pack citation is missing from textbooks: {citation['chunk_id']}")
            span = _get_cited_span(str(row["text"] or ""), citation["span"])
            ua = _make_form_mismatch_query(span, vesum_conn, used_queries=used_queries)
            if ua:
                used_queries.add(ua["query"])
                g1.append(
                    {
                        "id": f"G1-UA-{len(g1) + 1:03d}",
                        "gold_chunk_id": citation["chunk_id"],
                        "citation_ids": citation["citation_ids"],
                        "stratum": "ukrainian_form_mismatch",
                        "query": ua["query"],
                        "forms": ua["forms"],
                        "source_file": str(row["source_file"] or ""),
                        "subject": str(row["subject"] or ""),
                    }
                )
            english = _make_english_query(citation["supports"])
            if english:
                g1.append(
                    {
                        "id": f"G1-EN-{len(g1) + 1:03d}",
                        "gold_chunk_id": citation["chunk_id"],
                        "citation_ids": citation["citation_ids"],
                        "stratum": "english",
                        "query": english,
                        "forms": [],
                        "source_file": str(row["source_file"] or ""),
                        "subject": str(row["subject"] or ""),
                    }
                )
        g2: list[dict[str, Any]] = []
        total_positions = 0
        for level, path in arc_paths.items():
            arc = yaml.safe_load(path.read_text(encoding="utf-8"))
            for position in arc.get("positions", []) or []:
                job = str(position.get("job") or "")
                slug = str(position.get("slug") or "")
                if re.search(r"self-check|checkpoint", f"{job} {slug}", re.I):
                    continue
                total_positions += 1
                category = _grammar_category(job, slug)
                if not category or category not in grammar_terms:
                    continue
                source_text = grammar_terms[category]["source_text"]
                forms = grammar_terms[category]["forms"]
                source_path = grammar_terms[category]["source_path"]
                if category == "case":
                    module_path = ROOT / f"curriculum/l2-uk-en/{level}/{slug}/module.md"
                    case_phrase = _case_phrase_from_module(module_path, vesum_conn)
                    if case_phrase:
                        source_text, case_lemmas = case_phrase
                        source_path = _display_path(module_path)
                        forms = _phrase_paradigm_forms(case_lemmas, vesum_conn)
                        if len(forms) < 3:
                            continue
                g2.append(
                    {
                        "id": f"G2-{level.upper()}-{int(position['position']):03d}",
                        "level": level,
                        "position": int(position["position"]),
                        "slug": slug,
                        "job": job,
                        "category": category,
                        "source_text": source_text,
                        "source_path": source_path,
                        "base_query": forms[0],
                        "inflected_queries": forms[1:3],
                        "forms": forms[:3],
                    }
                )
        result = {
            "schema": "retrieval-probe-9233-queries.v1",
            "design_sha256": EXPECTED_DESIGN_SHA256,
            "source_files": {"pack": _display_path(pack_path), "grammar_terms": _display_path(grammar_source)},
            "g1_rule": "v3 item 1, review fix: 2-4 single-lemma content-POS words; reject proper nouns, pronouns, archaic/rare/short analyses, dash-separated pronunciation drill pairs and hyphen-attached fragments; preserve case at admission; first distinct eligible paradigm form; prefer unused combinations in source order (4, then 3, then 2 words), otherwise retain the first combination; insufficient spans are English-only",
            "g2_rule": "v3 items 2 and 4; non-self-check grammar positions, existing first-match category precedence; source-owned category terms from the A2 arc rationale, plus number/verb from the registered grammar textbook chunk; VESUM base plus first two distinct paradigm forms",
            "g1": g1,
            "g2": g2,
            "g2_term_inventory": grammar_terms,
            "g2_category_exclusions": grammar_exclusions,
            "counts": {
                "g1": len(g1),
                "g1_cited_chunks": len({q["gold_chunk_id"] for q in g1}),
                "g1_ukrainian_form_mismatch": sum(q["stratum"] == "ukrainian_form_mismatch" for q in g1),
                "g1_english": sum(q["stratum"] == "english" for q in g1),
                "g2": len(g2),
                "arc_non_self_check_positions": total_positions,
            },
        }
        source_conn.close()
        return result


def _digest_textbooks(connection: sqlite3.Connection) -> tuple[str, int, int]:
    digest = hashlib.sha256()
    count = 0
    unsectioned = 0
    cursor = connection.execute(
        "SELECT id, chunk_id, title, text, source_file, subject, parent_section_id FROM textbooks ORDER BY id"
    )
    for row in cursor:
        payload = json.dumps(
            [
                row[0],
                *[str(value or "") if index not in (6,) else value for index, value in enumerate(row[1:], start=1)],
            ],
            ensure_ascii=False,
            separators=(",", ":"),
        )
        digest.update(payload.encode("utf-8"))
        digest.update(b"\n")
        count += 1
        unsectioned += row[6] is None
    return digest.hexdigest(), count, unsectioned


def _query_terms(query: str, *, include_short: bool = True) -> list[str]:
    terms = list(dict.fromkeys(tokenize(query)))
    return [term for term in terms if include_short or len(term) >= 3]


def _exact_chunk_search(connection: sqlite3.Connection, query: str, limit: int) -> list[str]:
    terms = _query_terms(query)
    fts_query = sources_db._build_preserving_fts_query(terms)
    if not fts_query:
        return []
    rows = connection.execute(
        "SELECT s.chunk_id FROM textbooks_fts JOIN textbooks s ON s.id = textbooks_fts.rowid WHERE textbooks_fts MATCH ? ORDER BY bm25(textbooks_fts, 5.0, 1.0), s.id LIMIT ?",
        (fts_query, limit),
    ).fetchall()
    return [str(row[0]) for row in rows]


def lemma_expanded_rows(
    rows: list[sqlite3.Row] | list[tuple[Any, ...]], vesum: sqlite3.Connection
) -> tuple[list[tuple[Any, ...]], int]:
    """Shared A1 index contract: id, chunk, title, text, source, subject rows."""
    unique_tokens = {token for row in rows for value in row[2:4] for token in tokenize(str(value or ""))}
    token_lemmas: dict[str, list[str]] = {}
    tokens = sorted(unique_tokens)
    for offset in range(0, len(tokens), 500):
        batch = tokens[offset : offset + 500]
        placeholders = ",".join("?" for _ in batch)
        analyses = vesum.execute(
            f"SELECT f.word_form, f.lemma FROM forms_all f WHERE f.word_form IN ({placeholders}) AND NOT EXISTS (SELECT 1 FROM form_markers m WHERE m.form_id=f.id AND m.marker IN ('bad','obsc','subst')) ORDER BY f.word_form, f.lemma",
            batch,
        ).fetchall()
        for form, lemma in analyses:
            token_lemmas.setdefault(normalize_token(str(form)), []).append(normalize_token(str(lemma)))

    def expand(value: Any) -> str:
        return " ".join(
            lemma for token in tokenize(str(value or "")) for lemma in dict.fromkeys(token_lemmas.get(token, [token]))
        )

    expanded = [(row[0], row[1], expand(row[2]), expand(row[3]), row[4], row[5]) for row in rows]
    return expanded, len(unique_tokens)


def _create_lemma_index(sources_path: Path, vesum_path: Path, temp_dir: Path) -> tuple[Path, dict[str, int | float]]:
    resolved_temp = temp_dir.resolve()
    repo_root = ROOT.resolve()
    if resolved_temp == repo_root or repo_root in resolved_temp.parents:
        raise ValueError("--temp-dir must be outside the repository")
    resolved_temp.mkdir(parents=True, exist_ok=True)
    fd, raw_index_path = tempfile.mkstemp(prefix="retrieval-probe-9233-", suffix=".sqlite3", dir=resolved_temp)
    os.close(fd)
    index_path = Path(raw_index_path)
    started = time.perf_counter()
    source = _ro_connect(sources_path)
    index = None
    try:
        with get_vesum_connection(vesum_path) as vesum:
            index = sqlite3.connect(index_path)
            index.execute("PRAGMA journal_mode = OFF")
            index.execute("PRAGMA synchronous = OFF")
            index.execute(
                "CREATE VIRTUAL TABLE lemma_fts USING fts5(chunk_id UNINDEXED, source_file UNINDEXED, subject UNINDEXED, title_terms, text_terms, tokenize='unicode61')"
            )
            rows = source.execute(
                "SELECT id, chunk_id, title, text, source_file, subject FROM textbooks ORDER BY id"
            ).fetchall()
            expanded, unique_token_count = lemma_expanded_rows(rows, vesum)
            corpus_count = len(expanded)
            for row in expanded:
                index.execute(
                    "INSERT INTO lemma_fts(rowid, chunk_id, source_file, subject, title_terms, text_terms) VALUES (?, ?, ?, ?, ?, ?)",
                    (int(row[0]), str(row[1] or ""), str(row[4] or ""), str(row[5] or ""), row[2], row[3]),
                )
            index.commit()
            index.close()
    except BaseException:
        index_path.unlink(missing_ok=True)
        raise
    finally:
        if index is not None:
            index.close()
        source.close()
    return index_path, {
        "build_seconds": time.perf_counter() - started,
        "size_bytes": index_path.stat().st_size,
        "unique_surface_tokens": unique_token_count,
        "indexed_rows": corpus_count,
    }


def _lemma_query(query: str, vesum: sqlite3.Connection, *, include_short: bool = True) -> list[str]:
    output: list[str] = []
    for token in _query_terms(query, include_short=include_short):
        rows = vesum.execute(
            "SELECT f.lemma FROM forms_all f WHERE f.word_form = ? AND NOT EXISTS (SELECT 1 FROM form_markers m WHERE m.form_id=f.id AND m.marker IN ('bad','obsc','subst')) ORDER BY f.lemma",
            (token,),
        ).fetchall()
        output.extend(normalize_token(str(row[0])) for row in rows)
        if not rows:
            output.append(token)
    return list(dict.fromkeys(output))


def _lemma_search(index_path: Path, query: str, vesum: sqlite3.Connection, limit: int) -> list[str]:
    terms = _lemma_query(query, vesum)
    fts_query = sources_db._build_preserving_fts_query(terms)
    if not fts_query:
        return []
    connection = _shared_open_readonly(index_path.resolve())
    try:
        rows = connection.execute(
            "SELECT chunk_id FROM lemma_fts WHERE lemma_fts MATCH ? ORDER BY bm25(lemma_fts, 0, 0, 0, 5.0, 1.0), rowid LIMIT ?",
            (fts_query, limit),
        ).fetchall()
        return [str(row[0]) for row in rows]
    finally:
        connection.close()


def _production_search(
    query: str,
    track: str,
    source_conn: sqlite3.Connection,
    limit: int = 10,
    *,
    production: types.ModuleType | None = None,
) -> dict[str, int]:
    runtime = production or sources_db
    with runtime.using_connection(source_conn):
        results = runtime.search_sources(query, track=track, limit=limit)
    textbook_results = [row for row in results if row.get("corpus") == "textbook_sections"]
    section_ids = list(
        dict.fromkeys(
            int(str(row.get("chunk_id", ""))[1:])
            for row in textbook_results
            if re.fullmatch(r"S\d+", str(row.get("chunk_id", "")))
        )
    )
    # #9303 adds direct unsectioned chunks in the same corpus. Preserve their
    # actual result rank, including gaps occupied by other corpora.
    member_ranks = {
        str(row["chunk_id"]): rank
        for rank, row in enumerate(results, 1)
        if row.get("corpus") == "textbook_sections" and not re.fullmatch(r"S\d+", str(row.get("chunk_id", "")))
    }
    if not section_ids:
        return member_ranks
    placeholders = ",".join("?" for _ in section_ids)
    rows = source_conn.execute(
        f"SELECT chunk_id, parent_section_id FROM textbooks WHERE parent_section_id IN ({placeholders}) ORDER BY parent_section_id, id",
        section_ids,
    ).fetchall()
    members_by_section: dict[int, list[str]] = defaultdict(list)
    for row in rows:
        members_by_section[int(row[1])].append(str(row[0]))
    for rank, row in enumerate(results, start=1):
        if row.get("corpus") != "textbook_sections" or not re.fullmatch(r"S\d+", str(row.get("chunk_id", ""))):
            continue
        section_id = int(str(row["chunk_id"])[1:])
        for chunk_id in members_by_section.get(section_id, []):
            member_ranks.setdefault(chunk_id, rank)
    return member_ranks


def _rank_metrics(
    queries: list[dict[str, Any]], rankings: dict[str, list[str] | dict[str, int]], arm: str
) -> dict[str, dict[str, float | int]]:
    result: dict[str, dict[str, float | int]] = {}
    for stratum in ("all", "ukrainian_form_mismatch", "english"):
        selected = [q for q in queries if stratum == "all" or q["stratum"] == stratum]
        ranks: list[int | None] = []
        for query in selected:
            ranking = rankings.get(query["id"], [])
            if isinstance(ranking, dict):
                rank = ranking.get(query["gold_chunk_id"])
            else:
                try:
                    rank = ranking.index(query["gold_chunk_id"]) + 1
                except ValueError:
                    rank = None
            ranks.append(rank)
        denominator = len(ranks)
        result[stratum] = {
            "n": denominator,
            "hit_at_20": sum(rank is not None and rank <= 20 for rank in ranks) / denominator if denominator else 0.0,
            "hit_at_100": sum(rank is not None and rank <= 100 for rank in ranks) / denominator if denominator else 0.0,
            "mrr": sum((1 / rank) if rank else 0 for rank in ranks) / denominator if denominator else 0.0,
        }
    return result


def _percentile(values: list[float], percentile: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, round((len(ordered) - 1) * percentile)))
    return ordered[index]


def _production_snapshot(ref: str | None) -> tuple[types.ModuleType, dict[str, str]]:
    """Load an explicitly selected repository search implementation, read-only."""
    revision = subprocess.check_output(
        ["git", "rev-parse", "--verify", f"{ref or 'HEAD'}^{{commit}}"], cwd=ROOT, text=True, timeout=30
    ).strip()
    code = subprocess.check_output(["git", "show", f"{revision}:scripts/wiki/sources_db.py"], cwd=ROOT, timeout=30)
    provenance = {"revision": revision, "source_sha256": hashlib.sha256(code).hexdigest()}
    if ref is None:
        return sources_db, provenance
    module = types.ModuleType("scripts.wiki._probe_production")
    module.__file__ = str(ROOT / "scripts/wiki/sources_db.py")
    module.__package__ = "scripts.wiki"
    exec(compile(code, module.__file__, "exec"), module.__dict__)
    return module, provenance


def _descriptive_gate(
    queries: list[dict[str, Any]], metrics: dict[str, Any], rankings: dict[str, Any], g2: list[dict[str, Any]]
) -> dict[str, Any]:
    better = max(("A0-chunk", "A1-lemma"), key=lambda arm: metrics[arm]["ukrainian_form_mismatch"]["hit_at_20"])
    readings = []
    for stratum in ("ukrainian_form_mismatch", "all"):
        selected = [q for q in queries if stratum == "all" or q["stratum"] == stratum]
        misses = {
            depth: sum(q["gold_chunk_id"] not in rankings[better][q["id"]][:depth] for q in selected)
            for depth in (20, 100)
        }
        readings.append(
            {
                "stratum": stratum,
                "n": len(selected),
                "misses_at_20": misses[20],
                "misses_at_100": misses[100],
                "v2_threshold_met": bool(selected) and misses[100] / len(selected) >= 0.2,
                "any_miss_at_20": bool(misses[20]),
            }
        )
    return {
        "status": "descriptive_only",
        "better_lexical_arm": better,
        "readings": readings,
        "g2_overlap_recoveries": sum(
            pair["arms"]["A1-lemma"]["any_shared_chunk"] and not pair["arms"]["A0-chunk"]["any_shared_chunk"]
            for row in g2
            for pair in row["pairs"]
        ),
        "criterion": "v3 dropped the numeric threshold without specifying a replacement. v5 superseded the Phase 1→2 gate with the hybrid-search goal; neither historical reading authorizes compute. The former G2 OR-clause is descriptive only: identical lemma sets necessarily produce identical queries and overlap; it is never a gate input. G2 judged recall is unmeasured.",
    }


def _g1_bootstrap(queries: list[dict[str, Any]], rankings: dict[str, Any], *, iterations: int = 2000) -> dict[str, Any]:
    """Paired hit@20 gain, clustering every repeated Ukrainian query string."""
    clusters: dict[str, list[int]] = defaultdict(list)
    for query in queries:
        if query["stratum"] == "ukrainian_form_mismatch":
            clusters[query["query"]].append(
                int(query["gold_chunk_id"] in rankings["A1-lemma"][query["id"]][:20])
                - int(query["gold_chunk_id"] in rankings["A0-chunk"][query["id"]][:20])
            )
    if not clusters:
        return {"clusters": 0, "iterations": 0, "gain": None, "ci95": None}
    groups = list(clusters.values())
    rng = random.Random(9233)
    samples = []
    for _ in range(iterations):
        values = [value for group in rng.choices(groups, k=len(groups)) for value in group]
        samples.append(statistics.mean(values))
    return {
        "clusters": len(groups),
        "iterations": iterations,
        "seed": 9233,
        "gain": statistics.mean(value for group in groups for value in group),
        "ci95": [_percentile(samples, 0.025), _percentile(samples, 0.975)],
    }


def run_probe(args: argparse.Namespace) -> dict[str, Any]:
    sources_path = args.sources_db.resolve() if args.sources_db else sources_db._read_db_path()
    vesum_path = (
        args.vesum_db.resolve()
        if args.vesum_db
        else Path(__import__("scripts.rag.config", fromlist=["VESUM_DB_PATH"]).VESUM_DB_PATH)
    )
    query_set_path = args.output_dir / "queries.yaml"
    args.output_dir.mkdir(parents=True, exist_ok=True)
    if query_set_path.exists() and args.regenerate_queries and not args.overwrite_frozen_queries:
        raise ValueError("refusing to overwrite frozen queries.yaml; pass --overwrite-frozen-queries explicitly")
    if query_set_path.exists() and not args.regenerate_queries:
        query_set = yaml.safe_load(query_set_path.read_text(encoding="utf-8"))
        if query_set.get("design_sha256") != EXPECTED_DESIGN_SHA256:
            raise ValueError("existing query set is not bound to the frozen design")
    else:
        previous = yaml.safe_load(query_set_path.read_text(encoding="utf-8")) if query_set_path.exists() else None
        query_set = build_query_set(sources_path=sources_path, vesum_path=vesum_path)
        if previous:
            query_set["previous_query_sha256"] = hashlib.sha256(query_set_path.read_bytes()).hexdigest()
            current = {q["gold_chunk_id"]: q for q in query_set["g1"] if q["stratum"] == "ukrainian_form_mismatch"}
            changes = []
            for old in previous["g1"]:
                if old["stratum"] != "ukrainian_form_mismatch":
                    continue
                new = current.get(old["gold_chunk_id"])
                if new and new["query"] == old["query"]:
                    continue
                changes.append(
                    {
                        "previous_id": old["id"],
                        "gold_chunk_id": old["gold_chunk_id"],
                        "old_query": old["query"],
                        "new_query": new["query"] if new else None,
                        "reason": "strict single-lemma/content-POS, non-proper-noun admission; first eligible alternatives and unused combinations"
                        if new
                        else "fewer than two eligible Ukrainian words after rejecting ambiguous/function/proper/archaic analyses and drill fragments; English-only",
                    }
                )
            query_set["g1_changes"] = changes
        query_set_path.write_text(yaml.safe_dump(query_set, allow_unicode=True, sort_keys=False), encoding="utf-8")
    query_sha = hashlib.sha256(query_set_path.read_bytes()).hexdigest()
    if args.queries_only:
        return {
            "query_set_sha256": query_sha,
            "query_count": len(query_set["g1"]),
            "g1_ukrainian": query_set["counts"]["g1_ukrainian_form_mismatch"],
            "g1_english": query_set["counts"]["g1_english"],
            "g2_positions": len(query_set["g2"]),
            "frozen_only": True,
        }
    source_conn = _ro_connect(sources_path)
    index_path = None
    vesum_conn = None
    try:
        production, production_provenance = _production_snapshot(args.production_ref)
        textbooks_digest, textbook_count, unsectioned_count = _digest_textbooks(source_conn)
        index_path, index_cost = _create_lemma_index(sources_path, vesum_path, args.temp_dir)
        vesum_conn = _ro_connect(vesum_path)
        rankings: dict[str, dict[str, list[str] | dict[str, int]]] = {"A0-prod": {}, "A0-chunk": {}, "A1-lemma": {}}
        before_rankings = {}
        for query in query_set["g1"]:
            rankings["A0-prod"][query["id"]] = _production_search(
                query["query"], "a1", source_conn, limit=10, production=production
            )
            before_rankings[query["id"]] = _production_search(query["query"], "a1", source_conn, limit=10)
            rankings["A0-chunk"][query["id"]] = _exact_chunk_search(source_conn, query["query"], 100)
            rankings["A1-lemma"][query["id"]] = _lemma_search(index_path, query["query"], vesum_conn, 100)
        metrics = {arm: _rank_metrics(query_set["g1"], rankings[arm], arm) for arm in rankings}
        citation_rows = source_conn.execute(
            "SELECT chunk_id, parent_section_id FROM textbooks WHERE chunk_id IN ("
            + ",".join("?" for _ in {q["gold_chunk_id"] for q in query_set["g1"]})
            + ")",
            list(dict.fromkeys(q["gold_chunk_id"] for q in query_set["g1"])),
        ).fetchall()
        unreachable = sum(row[1] is None for row in citation_rows)
        g2_results: list[dict[str, Any]] = []
        query_times: list[float] = []
        for probe in query_set["g2"]:
            qset = [probe["base_query"], *probe["inflected_queries"]]
            arm_hits: dict[str, list[list[str]]] = {}
            for arm in ("A0-chunk", "A1-lemma"):
                hits: list[list[str]] = []
                for text in qset:
                    start = time.perf_counter()
                    result = (
                        _exact_chunk_search(source_conn, text, 20)
                        if arm == "A0-chunk"
                        else _lemma_search(index_path, text, vesum_conn, 20)
                    )
                    elapsed = time.perf_counter() - start
                    if arm == "A1-lemma":
                        query_times.append(elapsed)
                    hits.append(result)
                arm_hits[arm] = hits
            pairs = []
            for inflected_index in (1, 2):
                pair = {}
                for arm in arm_hits:
                    overlap = sorted(set(arm_hits[arm][0]) & set(arm_hits[arm][inflected_index]))
                    pair[arm] = {"top20_overlap": len(overlap), "any_shared_chunk": bool(overlap)}
                pairs.append({"inflected_query": qset[inflected_index], "arms": pair})
            g2_results.append(
                {
                    "id": probe["id"],
                    "level": probe["level"],
                    "position": probe["position"],
                    "category": probe["category"],
                    "base_query": qset[0],
                    "pairs": pairs,
                }
            )
        language_ids = {
            str(row[0])
            for row in source_conn.execute(
                "SELECT DISTINCT source_file FROM textbooks WHERE subject IN ('ukrmova','bukvar') OR source_file LIKE 'ulp-%'"
            )
        }
        language_queries = [
            q
            for q in query_set["g1"]
            if q["source_file"] in language_ids
            or q["subject"] in {"ukrmova", "bukvar"}
            or q["source_file"].startswith("ulp-")
        ]
        language_metrics = {arm: _rank_metrics(language_queries, rankings[arm], arm) for arm in rankings}
        gate = _descriptive_gate(query_set["g1"], metrics, rankings, g2_results)
        before_metrics = _rank_metrics(query_set["g1"], before_rankings, "A0-prod")
        direct_ids = {
            str(row[0]) for row in source_conn.execute("SELECT chunk_id FROM textbooks WHERE parent_section_id IS NULL")
        }
        before_direct = set().union(*(set(r) for r in before_rankings.values())) & direct_ids
        after_direct = set().union(*(set(r) for r in rankings["A0-prod"].values())) & direct_ids
        peak_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        result = {
            "design_sha256": EXPECTED_DESIGN_SHA256,
            "query_set_sha256": query_sha,
            "textbooks": {
                "rows": textbook_count,
                "row_digest_sha256": textbooks_digest,
                "row_digest_order": "id ASC; compact UTF-8 JSON array of id, chunk_id, title, text, source_file, subject, parent_section_id per row, newline-delimited",
                "unsectioned_rows": unsectioned_count,
                "g1_structurally_unreachable": unreachable,
            },
            "a0_prod": {
                "default_limit": 10,
                "before_revision": _production_snapshot(None)[1]["revision"],
                "after": production_provenance,
                "before_metrics": before_metrics,
                "before_direct_chunks": len(before_direct),
                "after_direct_chunks": len(after_direct),
                "ulp_rows": source_conn.execute(
                    "SELECT count(*) FROM textbooks WHERE source_file LIKE 'ulp-%'"
                ).fetchone()[0],
            },
            "g1_bootstrap": _g1_bootstrap(query_set["g1"], rankings),
            "g1_metrics": metrics,
            "language_subset_metrics": {"denominator": len(language_queries), "arms": language_metrics},
            "g2_inflection_probe": {"positions": len(g2_results), "pairs": g2_results},
            "a1_lemma_cost": {
                **index_cost,
                "query_batch_n": min(50, len(query_times)),
                "query_p50_seconds": statistics.median(query_times[:50]) if query_times else 0.0,
                "query_p95_seconds": _percentile(query_times[:50], 0.95),
                "peak_rss_bytes": peak_rss * 1024 if sys.platform != "darwin" else peak_rss,
            },
            "phase2_gate": gate,
        }
        _write_results(args.output_dir / "phase1-results.md", query_set, result)
        return result
    finally:
        if vesum_conn is not None:
            vesum_conn.close()
        source_conn.close()
        if index_path is not None:
            index_path.unlink(missing_ok=True)


def _write_results(path: Path, query_set: dict[str, Any], result: dict[str, Any]) -> None:
    rows = []
    for arm, strata in result["g1_metrics"].items():
        for stratum, metric in strata.items():
            rows.append(
                f"| {arm} | {stratum} | {metric['n']} | {metric['hit_at_20']:.3f} | {metric['hit_at_100']:.3f} | {metric['mrr']:.3f} |"
            )
    language_rows = []
    for arm, strata in result["language_subset_metrics"]["arms"].items():
        metric = strata["all"]
        language_rows.append(
            f"| {arm} | {metric['n']} | {metric['hit_at_20']:.3f} | {metric['hit_at_100']:.3f} | {metric['mrr']:.3f} |"
        )
    inflection_rows = []
    seen_triples = set()
    for probe in result["g2_inflection_probe"]["pairs"]:
        triple = (probe["base_query"], *(pair["inflected_query"] for pair in probe["pairs"]))
        if triple in seen_triples:
            continue
        seen_triples.add(triple)
        for pair in probe["pairs"]:
            for arm, metric in pair["arms"].items():
                inflection_rows.append(
                    f"| {probe['id']} | {probe['base_query']} → {pair['inflected_query']} | {arm} | {metric['top20_overlap']} | {str(metric['any_shared_chunk']).lower()} |"
                )
    cost = result["a1_lemma_cost"]
    gate = result["phase2_gate"]
    gate_rows = [
        f"| {row['stratum']} | {row['n']} | {row['misses_at_100']} | {str(row['v2_threshold_met']).lower()} | {row['misses_at_20']} | {str(row['any_miss_at_20']).lower()} |"
        for row in gate["readings"]
    ]
    changes = [
        f"| {row['previous_id']} | {row['old_query']} | {row['new_query'] or 'English-only'} | {row['reason']} |"
        for row in query_set.get("g1_changes", [])
    ]
    unique_counts = {
        stratum: len({q["query"] for q in query_set["g1"] if stratum == "all" or q["stratum"] == stratum})
        for stratum in ("all", "ukrainian_form_mismatch", "english")
    }
    prod = result["a0_prod"]
    bootstrap = result["g1_bootstrap"]
    text = "\n".join(
        [
            "# #9233 Phase 1 retrieval probe results",
            "",
            "Generated by `scripts/wiki/diagnostics/retrieval_probe_9233.py`; no semantic judging was run.",
            "",
            "Hashes:",
            "",
            f"- Frozen design SHA-256: `{result['design_sha256']}`",
            f"- Query-set SHA-256: `{result['query_set_sha256']}`",
            *[
                f"- {group.upper()} SHA-256 (compact sorted-key UTF-8 JSON): `{hashlib.sha256(json.dumps(query_set[group], ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()}`"
                for group in ("g1", "g2")
            ],
            f"- Superseding v5 design SHA-256: `{V5_DESIGN_SHA256}`",
            "",
            f"G1 denominator: {query_set['counts']['g1_cited_chunks']} unique cited chunk IDs and {len(query_set['g1'])} query records ({query_set['counts']['g1_ukrainian_form_mismatch']} Ukrainian form-mismatch; {query_set['counts']['g1_english']} English). G2 denominator: {len(query_set['g2'])} grammar positions.",
            "",
            f"Textbooks table: {result['textbooks']['rows']} rows; row digest SHA-256 `{result['textbooks']['row_digest_sha256']}` (`{result['textbooks']['row_digest_order']}`); {result['textbooks']['unsectioned_rows']} unsectioned rows (including {prod['ulp_rows']} ULP rows); {result['textbooks']['g1_structurally_unreachable']} cited G1 rows lacked sections before #9303. The database and row digest do not change for this code fix.",
            "",
            "A0-prod uses production `search_sources` at limit 10, maps S{section_id} to member chunk IDs and keeps direct unsectioned chunk IDs from #9303, preserving actual returned result ranks. Its hit@20 and hit@100 are capped by tool depth. Both lexical chunk arms use the whole table without a subject predicate. Dense retrieval is disabled for this judge-free run (SOURCES_MCP_NO_DENSE=1).",
            "",
            f"Before #9303 runtime: `{prod['before_revision']}`. After runtime: `{prod['after']['revision']}`; sources_db.py SHA-256 `{prod['after']['source_sha256']}`. Only that module is loaded from the selected Git snapshot; dependencies remain from the working tree. Before/after A0-prod G1 hit counts: {round(prod['before_metrics']['all']['hit_at_20'] * len(query_set['g1']))}/{len(query_set['g1'])} → {round(result['g1_metrics']['A0-prod']['all']['hit_at_20'] * len(query_set['g1']))}/{len(query_set['g1'])}. Unique unsectioned chunks actually returned across these G1 queries: {prod['before_direct_chunks']} → {prod['after_direct_chunks']} (not a claim that every unsectioned row was retrieved).",
            "",
            f"Unique G1 query strings: {unique_counts['all']} all; {unique_counts['ukrainian_form_mismatch']} Ukrainian; {unique_counts['english']} English. Paired bootstrap for A1-lemma − A0-chunk hit@20: cluster = exact Ukrainian query string, keeping all repeated gold-chunk records together; {bootstrap['clusters']} clusters, {bootstrap['iterations']} resamples, seed 9233, gain {bootstrap['gain']}, 95% interval {bootstrap['ci95']}. Repeated primer spans containing only бачити/чути cannot supply distinct strings under the frozen cited-span rule. This narrow, source-derived sample is not independent held-out semantic proof.",
            "",
            "## G1 query regeneration",
            "",
            query_set["g1_rule"],
            "",
            "Local selection uses read-only VESUM forms_all/POS/tags and form_markers. All selected source and query forms are attested there. Sources MCP attestation is recorded separately for this run; it uses VESUM too and supplies no independent semantic proof. No Ukrainian forms are generated by a language model.",
            "",
            f"Previous query SHA-256: `{query_set.get('previous_query_sha256', 'none')}`. All dropped/replaced Ukrainian queries follow; unchanged records are retained.",
            "",
            "| Previous ID | Previous query | Replacement | Reason |",
            "|---|---|---|---|",
            *changes,
            "",
            "## G1 retrieval metrics",
            "",
            "| Arm | Stratum | n | hit@20 | hit@100 | MRR |",
            "|---|---|---:|---:|---:|---:|",
            *rows,
            "",
            f"Language subset denominator: {result['language_subset_metrics']['denominator']} queries, selected by source identity (`ukrmova`, `bukvar`, ULP source files).",
            "",
            "| Arm | n | hit@20 | hit@100 | MRR |",
            "|---|---:|---:|---:|---:|",
            *language_rows,
            "",
            "## Mechanical G2 inflection probe",
            "",
            f"Each unique term triple is reported once ({len(seen_triples)} triples; first position shown); the complete position inventory remains in queries.yaml. Category counts: {dict(Counter(q['category'] for q in query_set['g2']))}. Excluded categories: {query_set.get('g2_category_exclusions', {})}. Number (число) and verb (дієслово) are grounded in textbooks:{GRAMMAR_TEXTBOOK_CHUNK}; other terms retain their arc-source provenance. The existing first-match category priority is retained: all number/plural/singular jobs also match case first, so number has zero dedicated positions in this arc snapshot. Sentence (речення) also has zero dedicated positions: its jobs match earlier categories first. Both source terms and paradigms remain available. Overlap counts shared chunk IDs, never judged relevance.",
            "",
            "| First position | Pair | Arm | top-20 overlap | any shared chunk |",
            "|---|---|---|---:|---|",
            *inflection_rows,
            "",
            "## A1-lemma cost",
            "",
            f"Index build: {cost['build_seconds']:.3f} s; SQLite index size: {cost['size_bytes']} bytes; unique corpus surface tokens: {cost['unique_surface_tokens']}; indexed rows: {cost['indexed_rows']}; first 50 ordered G2 queries p50/p95: {cost['query_p50_seconds']:.6f}/{cost['query_p95_seconds']:.6f} s (n={cost['query_batch_n']}); peak process RSS: {cost['peak_rss_bytes']} bytes.",
            "",
            "## Phase 2 gate — descriptive only",
            "",
            f"Better lexical arm by Ukrainian G1 hit@20: {gate['better_lexical_arm']}. English is outside the primary contrast; the pooled row is a historical sensitivity reading only.",
            "",
            "| Stratum | n | Outside top 100 | v2 ≥20% met | Misses at 20 | Any-miss reading |",
            "|---|---:|---:|---|---:|---|",
            *gate_rows,
            "",
            gate["criterion"],
            "",
            f"Former G2 overlap OR-clause occurrences: {gate['g2_overlap_recoveries']} position-pairs; descriptive, excluded from both readings.",
            "",
            "Residual: no embedder, reranker, Phase 2 or semantic relevance judging was run. Compute awaits the operator; the accountable driver owns that follow-on decision and independent exact-head code/Ukrainian review. No search recommendation follows from this Phase 1 report.",
            "",
        ]
    )
    path.write_text(text, encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Compare exact-form and VESUM-lemma textbook retrieval against frozen #9233 queries.\n"
            "Use for the judge-free Phase 1 probe; do not use to choose an embedder or judge relevance."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            '  .venv/bin/python scripts/wiki/diagnostics/retrieval_probe_9233.py --temp-dir "$TMPDIR/probe-9233"\n'
            '  .venv/bin/python scripts/wiki/diagnostics/retrieval_probe_9233.py --sources-db data/sources.db --vesum-db data/vesum.db --temp-dir "$TMPDIR/probe-9233"\n'
            "Outputs: generated queries.yaml and phase1-results.md under --output-dir; temporary lemma index under --temp-dir; source databases are read-only.\n"
            "Exit codes: 0 means the probe and report completed; >=1 means invalid input or a retrieval/build failure.\n"
            "Related: frozen #9233 bake-off design v3; scripts/wiki/sources_db.py; issue #9233."
        ),
    )
    parser.add_argument(
        "--sources-db",
        type=Path,
        help="Read-only sources.db path; default is the project active database resolved by sources_db.",
    )
    parser.add_argument(
        "--vesum-db", type=Path, help="Read-only VESUM path; default is the project VESUM database resolver."
    )
    parser.add_argument(
        "--temp-dir",
        type=Path,
        required=True,
        help='Existing or creatable temporary directory outside this repository for the lemma SQLite index; example: "$TMPDIR/probe-9233".',
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "docs/research/retrieval-bakeoff-9233",
        help="Directory for frozen queries and generated results; default: docs/research/retrieval-bakeoff-9233.",
    )
    parser.add_argument(
        "--queries-only",
        action="store_true",
        help="Write/freeze queries.yaml and report its SHA-256 without running any retrieval arm; default: run the full probe.",
    )
    parser.add_argument(
        "--regenerate-queries",
        action="store_true",
        help="Rebuild queries.yaml from the cited pack, arcs, source text, and VESUM before any arm runs; default: reuse the frozen file.",
    )
    parser.add_argument(
        "--overwrite-frozen-queries",
        action="store_true",
        help="Explicitly permit --regenerate-queries to replace an existing frozen queries.yaml; default: refuse.",
    )
    parser.add_argument(
        "--production-ref",
        help="Load scripts/wiki/sources_db.py from this local Git revision for A0-prod, retaining the working-tree runtime as the before baseline; default: current runtime. Other modules stay at the working-tree versions.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = run_probe(args)
    if result.get("frozen_only"):
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    else:
        print(
            json.dumps(
                {
                    "query_set_sha256": result["query_set_sha256"],
                    "textbooks_rows": result["textbooks"]["rows"],
                    "g1": result["g1_metrics"],
                    "phase2_gate": result["phase2_gate"],
                    "a1_lemma_cost": result["a1_lemma_cost"],
                },
                ensure_ascii=False,
                sort_keys=True,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
