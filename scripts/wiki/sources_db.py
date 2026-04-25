"""SQLite interface for ALL source content — replaces Qdrant RAG entirely.

FTS5 tables (prose search):
- search_textbooks() — textbook chunks
- search_external() — external articles (ULP, blogs, YouTube)
- search_literary() — literary texts (chronicles, poetry, legal)

Indexed tables (dictionary headword lookup):
- search_definitions() — СУМ-11
- search_etymology() — Грінченко
- search_idioms() — Фразеологічний
- search_synonyms() — Ukrajinet WordNet
- translate_en_uk() — Балла EN→UK
- query_cefr_level() — PULS CEFR
- search_style_guide() — Антоненко-Давидович
- lookup_by_url() — external article URL lookup
"""

import sqlite3
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import yaml

from .channels import rank_external_hits
from .chunking import chunk_text, policy_for
from .dense_rerank import _get_tokenizer, rerank_candidates, rerank_sections
from .query_builder import build_query_buckets

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SOURCES_DB_PATH = PROJECT_ROOT / "data" / "sources.db"
TRACK_PRIORS_PATH = PROJECT_ROOT / "scripts" / "wiki" / "track_priors.yaml"

_conn: sqlite3.Connection | None = None


#: Max wait (ms) for SQLite to acquire a shared read lock when another
#: process holds it (e.g. a concurrent `build_sources_db.py` ingest
#: during #1188 Diasporiana that rebuilt `literary_texts` FTS5 indices
#: while a wiki compile was reading — see 2026-04-18 smoke-test race).
_SQLITE_BUSY_TIMEOUT_MS = 30_000

#: Retry wrapper for `_fts_search` — on `sqlite3.OperationalError`
#: (typically "database is locked"), wait this many seconds and try
#: once more. Two retries total (≈4.5s max extra wait). If it still
#: fails, callers get a loud empty-with-exception instead of silent [].
_FTS_RETRY_DELAYS_S: tuple[float, ...] = (0.5, 4.0)
_CORPORA = (
    "textbook_sections",
    "modern_literary",
    "archaic_literary",
    "external",
    "wikipedia",
    "ukrainian_wiki",
)
_PRIOR_KEY_BY_CORPUS = {
    "textbook_sections": "textbook",
    "modern_literary": "modern_literary",
    "archaic_literary": "archaic_literary",
    "external": "external",
    "wikipedia": "wikipedia",
    "ukrainian_wiki": "ukrainian_wiki",
}


def _load_track_priors() -> dict[str, dict[str, float]]:
    if not TRACK_PRIORS_PATH.exists():
        return {}
    data = yaml.safe_load(TRACK_PRIORS_PATH.read_text(encoding="utf-8")) or {}
    return {
        str(track): {str(corpus): float(weight) for corpus, weight in priors.items()}
        for track, priors in data.items()
        if isinstance(priors, dict)
    }


_TRACK_PRIORS = _load_track_priors()


def _get_conn() -> sqlite3.Connection:
    """Get or create a cached database connection."""
    global _conn
    if _conn is None:
        if not SOURCES_DB_PATH.exists():
            raise FileNotFoundError(
                f"Sources database not found at {SOURCES_DB_PATH}. "
                "Run: .venv/bin/python scripts/wiki/build_sources_db.py"
            )
        _conn = sqlite3.connect(str(SOURCES_DB_PATH), check_same_thread=False)
        _conn.row_factory = sqlite3.Row
        # Concurrent readers must wait for a concurrent writer rather
        # than silently returning empty rowsets — see §race-condition
        # comment on `_SQLITE_BUSY_TIMEOUT_MS` above.
        _conn.execute(f"PRAGMA busy_timeout = {_SQLITE_BUSY_TIMEOUT_MS}")
    return _conn


def _build_fts_query(keywords: set[str], min_len: int = 3) -> str | None:
    """Build FTS5 MATCH query from keywords. Returns None if no valid terms."""
    terms = []
    for kw in keywords:
        if len(kw) < min_len:
            continue
        # Strip FTS5 special characters that break MATCH syntax
        clean = kw.replace('"', '').replace("'", '').replace('/', ' ').strip()
        if len(clean) >= min_len:
            terms.append(f'"{clean}"')
    return " OR ".join(terms) if terms else None


def _is_noise(text: str) -> bool:
    """Detect chunks that are noise — no citable content for wiki articles.

    Catches:
    1. TOC pages — dot leaders (". . . . 154") with section numbers
    2. Publisher/metadata fragments — multiple rnk.com.ua URLs
    """
    # TOC pages: 3+ dot-leader patterns
    if text.count(". . .") >= 3:
        return True

    # Publisher/URL fragments
    return text.count("rnk.com.ua") >= 2


def _kw_score(text: str, title: str, keywords: set[str]) -> int:
    """Count keyword hits using space-padded matching.

    Returns 0 for TOC/noise chunks regardless of keyword matches.
    """
    if _is_noise(text):
        return 0
    searchable = f" {title} {text} ".lower()
    return sum(1 for w in keywords if f" {w} " in searchable)


def _table_columns(table: str) -> set[str]:
    """Return the column names for a SQLite table."""
    try:
        conn = _get_conn()
    except FileNotFoundError:
        return set()
    return {
        row["name"]
        for row in conn.execute(f"PRAGMA table_info({table})").fetchall()
    }


def _build_preserving_fts_query(terms: list[str] | tuple[str, ...]) -> str | None:
    """Build an FTS5 OR query without stripping apostrophes."""
    cleaned_terms: list[str] = []
    for raw in terms:
        term = str(raw or "").replace('"', " ").strip()
        if not term:
            continue
        cleaned_terms.append(f'"{term}"')
    return " OR ".join(cleaned_terms) if cleaned_terms else None


def _bucket_a_plaintext(bucket_a_phrases: list[str]) -> list[str]:
    return [phrase.strip().strip('"') for phrase in bucket_a_phrases if phrase.strip().strip('"')]


def _tokenize_normalized_text(text: str) -> set[str]:
    tokens: set[str] = set()
    for token in _normalize_text(text).replace("/", " ").replace("-", " ").split():
        cleaned = token.strip(".,;:!?\"«»()[]{}")
        if cleaned:
            tokens.add(cleaned)
    return tokens


def _normalize_text(text: str) -> str:
    from .diagnostics.retrieval_playback import normalize_text

    return normalize_text(text)


def _search_sections_fts5(
    bucket_a_phrases: list[str],
    bucket_b_keywords: set[str],
    *,
    track: str,
    max_chunk_candidates: int = 100,
    max_sections: int = 30,
) -> list[dict]:
    """Return section candidates grouped from chunk-level FTS5 hits."""
    try:
        conn = _get_conn()
    except FileNotFoundError:
        return []

    terms = [*_bucket_a_plaintext(bucket_a_phrases), *sorted(bucket_b_keywords)]
    fts_query = _build_preserving_fts_query(terms)
    if not fts_query:
        return []

    extra_where = ["s.parent_section_id IS NOT NULL"]
    extra_params: list[object] = []
    # #1340 (2026-04-20): grade filter intentionally NOT applied here.
    # CEFR (L2 framework) does not map onto Ukrainian school grades
    # (L1 native staging). Grade 5 systematic phonetics is exactly
    # what an adult L2 A1 learner needs — adult metacognition makes
    # grade-5/6 explicit grammar appropriate even when grade-1/2
    # picture-driven primers are not. Dense rerank + per-track priors
    # in track_priors.yaml handle topic relevance; an a-priori grade
    # gate masks corpus coverage we explicitly want.
    # See docs/session-state/2026-04-20-plan-audit-a1a2.md for context.
    # `track` retained in signature for future soft-prior use; do NOT
    # re-add a hard `grade IN (...)` filter without an empirical
    # diagnostic showing dense rerank cannot handle the topic.
    _ = track  # keep parameter live for downstream callers

    rows = conn.execute(
        f"""
        SELECT
            s.id,
            s.chunk_id,
            s.title,
            s.text,
            s.source_file,
            s.grade,
            s.author,
            s.parent_section_id,
            bm25(textbooks_fts, 5.0, 1.0) AS rank
        FROM textbooks_fts
        JOIN textbooks s ON s.id = textbooks_fts.rowid
        WHERE textbooks_fts MATCH ?
          AND {' AND '.join(extra_where)}
        ORDER BY rank
        LIMIT ?
        """,
        (fts_query, *extra_params, max_chunk_candidates),
    ).fetchall()

    if not rows:
        return []

    bucket_a_plain = [_normalize_text(phrase) for phrase in _bucket_a_plaintext(bucket_a_phrases)]
    normalized_bucket_b = {_normalize_text(keyword) for keyword in bucket_b_keywords}

    by_section: dict[int, dict] = defaultdict(lambda: {
        "bucket_a_hits": 0,
        "bucket_b_hits": 0,
        "best_rank": float("inf"),
        "matched_chunk_ids": [],
    })

    for row in rows:
        text = str(row["text"] or "")
        title = str(row["title"] or "")
        searchable = _normalize_text(f"{title}\n{text}")
        tokens = _tokenize_normalized_text(searchable)

        bucket_a_hit = any(phrase in searchable for phrase in bucket_a_plain)
        bucket_b_hit = bool(tokens & normalized_bucket_b)
        if not bucket_a_hit and not bucket_b_hit:
            continue

        section_id = int(row["parent_section_id"])
        aggregated = by_section[section_id]
        aggregated["bucket_a_hits"] += int(bucket_a_hit)
        aggregated["bucket_b_hits"] += int(bucket_b_hit)
        aggregated["best_rank"] = min(float(row["rank"] or 0.0), aggregated["best_rank"])
        aggregated["matched_chunk_ids"].append(str(row["chunk_id"]))

    if not by_section:
        return []

    ranked_sections = sorted(
        (
            {
                "section_id": section_id,
                "bucket_a_hits": data["bucket_a_hits"],
                "bucket_b_hits": data["bucket_b_hits"],
                "section_score": (data["bucket_a_hits"] * 3) + data["bucket_b_hits"],
                "best_rank": data["best_rank"],
                "matched_chunk_ids": data["matched_chunk_ids"],
            }
            for section_id, data in by_section.items()
        ),
        key=lambda row: (
            -int(row["section_score"]),
            float(row["best_rank"]),
            int(row["section_id"]),
        ),
    )[:max_sections]

    section_ids = [int(row["section_id"]) for row in ranked_sections]
    placeholders = ",".join("?" * len(section_ids))
    section_rows = conn.execute(
        f"""
        SELECT
            section_id,
            source_file,
            grade,
            section_title,
            section_number,
            page_start,
            page_end,
            chunk_count,
            full_text
        FROM textbook_sections
        WHERE section_id IN ({placeholders})
        """,
        tuple(section_ids),
    ).fetchall()
    section_meta = {int(row["section_id"]): dict(row) for row in section_rows}

    results: list[dict] = []
    for ranked in ranked_sections:
        meta = section_meta.get(int(ranked["section_id"]))
        if not meta:
            continue
        results.append({
            **meta,
            **ranked,
            "text": meta["full_text"],
            "chunk_id": f"S{meta['section_id']}",
            "corpus": "textbook_sections",
            # Do NOT set "unit_key" here — the dispatcher computes it
            # downstream without the "S" prefix to match the embedding
            # manifest's seeded keys (`textbook_sections:{id}`). Setting
            # it here with the S-prefix would shadow the correct value
            # and break dense rerank lookup. See #1466 regression fix.
            "title": meta["section_title"],
            "source_type": "textbook",
        })
    return results


def _build_dense_query(bucket_a_phrases: list[str], bucket_b_keywords: set[str], fallback: str) -> str:
    dense_query = " ".join(
        [*(phrase.strip().strip('"') for phrase in bucket_a_phrases), *sorted(bucket_b_keywords)]
    ).strip()
    return dense_query or str(fallback)


def _prepare_query(query: str | Path, track: str) -> tuple[list[str], set[str], str]:
    candidate_path = Path(query)
    if candidate_path.exists():
        bucket_a_phrases, bucket_b_keywords = build_query_buckets(candidate_path, track)
        return bucket_a_phrases, bucket_b_keywords, _build_dense_query(
            bucket_a_phrases,
            bucket_b_keywords,
            candidate_path.stem.replace("-", " "),
        )

    raw_query = _normalize_text(str(query))
    bucket_a_phrases: list[str] = []
    if _is_bucket_a_query(raw_query):
        bucket_a_phrases.append(f'"{raw_query}"')
    bucket_b_keywords = _tokenize_normalized_text(raw_query)
    return bucket_a_phrases, bucket_b_keywords, _build_dense_query(
        bucket_a_phrases,
        bucket_b_keywords,
        raw_query,
    )


def _is_bucket_a_query(phrase: str) -> bool:
    words = phrase.split()
    return bool(phrase) and (len(words) >= 3 or len(phrase) >= 10)


def _corpus_prior(track: str, corpus: str) -> float:
    prior_key = _PRIOR_KEY_BY_CORPUS[corpus]
    return float(_TRACK_PRIORS.get(track, {}).get(prior_key, 1.0))


def _fts_terms(bucket_a_phrases: list[str], bucket_b_keywords: set[str]) -> list[str]:
    return [*_bucket_a_plaintext(bucket_a_phrases), *sorted(bucket_b_keywords)]


def _search_literary_candidates(
    bucket_a_phrases: list[str],
    bucket_b_keywords: set[str],
    *,
    corpus: str,
    candidate_k: int,
) -> list[dict]:
    try:
        conn = _get_conn()
    except FileNotFoundError:
        return []

    fts_query = _build_preserving_fts_query(_fts_terms(bucket_a_phrases, bucket_b_keywords))
    if not fts_query:
        return []

    periods = ("modern",) if corpus == "modern_literary" else ("middle_ukrainian", "old_east_slavic")
    placeholders = ",".join("?" * len(periods))
    rows = conn.execute(
        f"""
        SELECT
            s.id,
            s.chunk_id,
            s.title,
            s.text,
            s.source_file,
            s.author,
            s.work,
            s.work_id,
            s.language_period,
            bm25(literary_fts, 5.0, 1.0) AS rank
        FROM literary_fts
        JOIN literary_texts s ON s.id = literary_fts.rowid
        WHERE literary_fts MATCH ?
          AND s.language_period IN ({placeholders})
        ORDER BY rank
        LIMIT ?
        """,
        (fts_query, *periods, candidate_k),
    ).fetchall()

    return [
        {
            "unit_key": f"{corpus}:{row['chunk_id']}",
            "corpus": corpus,
            "source_type": "literary",
            "chunk_id": str(row["chunk_id"] or ""),
            "title": str(row["title"] or ""),
            "text": str(row["text"] or ""),
            "full_text": str(row["text"] or ""),
            "source_file": str(row["source_file"] or ""),
            "parent_key": str(row["work_id"] or row["source_file"] or ""),
            "author": str(row["author"] or ""),
            "work": str(row["work"] or ""),
            "language_period": str(row["language_period"] or ""),
            "fts_score": float(row["rank"] or 0.0),
            "row_id": int(row["id"]),
        }
        for row in rows
    ]


def _search_external_candidates(
    bucket_a_phrases: list[str],
    bucket_b_keywords: set[str],
    *,
    candidate_k: int,
) -> list[dict]:
    try:
        conn = _get_conn()
    except FileNotFoundError:
        return []

    fts_query = _build_preserving_fts_query(_fts_terms(bucket_a_phrases, bucket_b_keywords))
    if not fts_query:
        return []

    rows = conn.execute(
        """
        SELECT
            s.id,
            s.chunk_id,
            s.title,
            s.text,
            s.source_file,
            s.url,
            s.domain,
            s.speaker,
            bm25(external_fts, 5.0, 1.0) AS rank
        FROM external_fts
        JOIN external_articles s ON s.id = external_fts.rowid
        WHERE external_fts MATCH ?
        ORDER BY rank
        LIMIT ?
        """,
        (fts_query, candidate_k),
    ).fetchall()

    return [
        {
            "unit_key": f"external:{row['chunk_id'] or row['id']}",
            "corpus": "external",
            "source_type": "external",
            "chunk_id": str(row["chunk_id"] or ""),
            "title": str(row["title"] or ""),
            "text": str(row["text"] or ""),
            "full_text": str(row["text"] or ""),
            "source_file": str(row["source_file"] or ""),
            "parent_key": str(row["source_file"] or ""),
            "url": str(row["url"] or ""),
            "source_name": str(row["domain"] or row["source_file"] or ""),
            "speaker": str(row["speaker"] or ""),
            "fts_score": float(row["rank"] or 0.0),
        }
        for row in rows
    ]


def _search_wikipedia_candidates(
    bucket_a_phrases: list[str],
    bucket_b_keywords: set[str],
    *,
    candidate_k: int,
) -> list[dict]:
    try:
        conn = _get_conn()
    except FileNotFoundError:
        return []

    fts_query = _build_preserving_fts_query(_fts_terms(bucket_a_phrases, bucket_b_keywords))
    if not fts_query:
        return []

    rows = conn.execute(
        """
        SELECT
            s.id,
            s.title,
            s.url,
            s.text,
            bm25(wikipedia_fts, 5.0, 1.0) AS rank
        FROM wikipedia_fts
        JOIN wikipedia s ON s.id = wikipedia_fts.rowid
        WHERE wikipedia_fts MATCH ?
        ORDER BY rank
        LIMIT ?
        """,
        (fts_query, candidate_k),
    ).fetchall()

    candidates: list[dict] = []
    policy = policy_for("wikipedia")
    tokenizer = _get_tokenizer()
    for row in rows:
        title = str(row["title"] or "")
        full_text = str(row["text"] or "")
        for piece in chunk_text(full_text, policy=policy, tokenizer=tokenizer):
            unit_key = (
                f"wikipedia:{title}:chunk_{piece.chunk_index}"
                if piece.extra_metadata
                else f"wikipedia:{title}"
            )
            candidates.append(
                {
                    "unit_key": unit_key,
                    "corpus": "wikipedia",
                    "source_type": "wikipedia",
                    "title": title,
                    "text": piece.text,
                    "full_text": piece.text,
                    "parent_key": title,
                    "url": str(row["url"] or ""),
                    "chunk_index": piece.chunk_index,
                    "source_name": "Wikipedia",
                    "fts_score": float(row["rank"] or 0.0),
                }
            )
    return candidates


def _search_ukrainian_wiki_candidates(
    bucket_a_phrases: list[str],
    bucket_b_keywords: set[str],
    *,
    candidate_k: int,
) -> list[dict]:
    try:
        conn = _get_conn()
    except FileNotFoundError:
        return []

    fts_query = _build_preserving_fts_query(_fts_terms(bucket_a_phrases, bucket_b_keywords))
    if not fts_query:
        return []

    try:
        tables = {
            str(row["name"])
            for row in conn.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type IN ('table', 'view')
                  AND name IN ('ukrainian_wiki', 'ukrainian_wiki_fts')
                """
            ).fetchall()
        }
    except (sqlite3.Error, SystemError):
        return []
    if {"ukrainian_wiki", "ukrainian_wiki_fts"} - tables:
        return []

    try:
        rows = conn.execute(
            """
            SELECT
                s.id,
                s.passage_id,
                s.article_slug,
                s.article_title,
                s.article_path,
                s.track,
                s.section_path,
                s.paragraph_start,
                s.paragraph_end,
                s.word_count,
                s.char_count,
                s.text,
                bm25(ukrainian_wiki_fts, 5.0, 2.0, 1.0) AS rank
            FROM ukrainian_wiki_fts
            JOIN ukrainian_wiki s ON s.id = ukrainian_wiki_fts.rowid
            WHERE ukrainian_wiki_fts MATCH ?
            ORDER BY rank
            LIMIT ?
            """,
            (fts_query, candidate_k),
        ).fetchall()
    except (sqlite3.Error, SystemError):
        return []

    return [
        {
            "unit_key": f"ukrainian_wiki:{row['passage_id']}",
            "corpus": "ukrainian_wiki",
            "source_type": "ukrainian_wiki",
            "chunk_id": str(row["passage_id"] or ""),
            "title": str(row["article_title"] or ""),
            "text": str(row["text"] or ""),
            "full_text": str(row["text"] or ""),
            "source_file": str(row["article_path"] or ""),
            "parent_key": str(row["article_slug"] or ""),
            "track": str(row["track"] or ""),
            "section_path": str(row["section_path"] or ""),
            "paragraph_start": int(row["paragraph_start"] or 0),
            "paragraph_end": int(row["paragraph_end"] or 0),
            "word_count": int(row["word_count"] or 0),
            "char_count": int(row["char_count"] or 0),
            "source_name": "Ukrainian wiki",
            "fts_score": float(row["rank"] or 0.0),
            "row_id": int(row["id"]),
        }
        for row in rows
    ]


def _dispatch_corpus_search(
    corpus: str,
    *,
    bucket_a_phrases: list[str],
    bucket_b_keywords: set[str],
    dense_query: str,
    track: str,
    candidate_k_per_corpus: int,
) -> list[dict]:
    if corpus == "textbook_sections":
        candidates = _search_sections_fts5(
            bucket_a_phrases,
            bucket_b_keywords,
            track=track,
            max_sections=candidate_k_per_corpus,
            max_chunk_candidates=max(candidate_k_per_corpus * 4, candidate_k_per_corpus),
        )
        for candidate in candidates:
            candidate["corpus"] = corpus
            candidate["unit_key"] = candidate.get("unit_key") or f"textbook_sections:{int(candidate['section_id'])}"
            candidate["parent_key"] = str(candidate.get("source_file", ""))
            candidate["fts_score"] = float(candidate.get("best_rank", 0.0) or 0.0)
    elif corpus in {"modern_literary", "archaic_literary"}:
        candidates = _search_literary_candidates(
            bucket_a_phrases,
            bucket_b_keywords,
            corpus=corpus,
            candidate_k=candidate_k_per_corpus,
        )
    elif corpus == "external":
        candidates = _search_external_candidates(
            bucket_a_phrases,
            bucket_b_keywords,
            candidate_k=candidate_k_per_corpus,
        )
    elif corpus == "wikipedia":
        candidates = _search_wikipedia_candidates(
            bucket_a_phrases,
            bucket_b_keywords,
            candidate_k=candidate_k_per_corpus,
        )
    elif corpus == "ukrainian_wiki":
        candidates = _search_ukrainian_wiki_candidates(
            bucket_a_phrases,
            bucket_b_keywords,
            candidate_k=candidate_k_per_corpus,
        )
    else:
        return []

    reranked = rerank_candidates(
        dense_query,
        candidates,
        corpus=corpus,
        limit=candidate_k_per_corpus,
    )
    prior = _corpus_prior(track, corpus)
    for row in reranked:
        row["prior_weight"] = prior
        row["final_score"] = float(row.get("dense_score", 0.0)) * prior
    return reranked


def _expand_literary_neighbors(match: dict) -> dict:
    try:
        conn = _get_conn()
    except FileNotFoundError:
        return match

    parent_key = str(match.get("parent_key", "")).strip()
    chunk_id = str(match.get("chunk_id", "")).strip()
    rows = conn.execute(
        """
        SELECT id, chunk_id, text
        FROM literary_texts
        WHERE work_id = ? OR source_file = ?
        ORDER BY id
        """,
        (parent_key, parent_key),
    ).fetchall()
    if not rows:
        return match

    target_index = next(
        (
            index
            for index, row in enumerate(rows)
            if str(row["chunk_id"] or "") == chunk_id
        ),
        None,
    )
    if target_index is None:
        return match

    start = max(0, target_index - 1)
    end = min(len(rows), target_index + 2)
    context_rows = rows[start:end]
    full_text = "\n\n".join(str(row["text"] or "") for row in context_rows if str(row["text"] or "").strip())
    return {
        **match,
        "full_text": full_text or str(match.get("full_text", "")),
        "context_unit_keys": [f"{match['corpus']}:{row['chunk_id']}" for row in context_rows],
    }


def _expand_wikipedia_neighbors(match: dict) -> dict:
    try:
        conn = _get_conn()
    except FileNotFoundError:
        return match

    title = str(match.get("parent_key", "")).strip()
    row = conn.execute(
        "SELECT text FROM wikipedia WHERE title = ? LIMIT 1",
        (title,),
    ).fetchone()
    if row is None:
        return match

    pieces = list(
        chunk_text(
            str(row["text"] or ""),
            policy=policy_for("wikipedia"),
            tokenizer=_get_tokenizer(),
        )
    )
    chunk_index = int(match.get("chunk_index", 0))
    context = pieces[max(0, chunk_index - 1):chunk_index + 2]
    if not context:
        return match

    return {
        **match,
        "full_text": "\n\n".join(piece.text for piece in context),
        "context_unit_keys": [
            f"wikipedia:{title}:chunk_{piece.chunk_index}"
            if piece.extra_metadata
            else f"wikipedia:{title}"
            for piece in context
        ],
    }


def _expand_ukrainian_wiki_neighbors(match: dict) -> dict:
    try:
        conn = _get_conn()
    except FileNotFoundError:
        return match

    article_slug = str(match.get("parent_key", "")).strip()
    start_paragraph = int(match.get("paragraph_start", 0))
    end_paragraph = int(match.get("paragraph_end", 0))
    try:
        rows = conn.execute(
            """
            SELECT passage_id, text
            FROM ukrainian_wiki
            WHERE article_slug = ?
              AND paragraph_start <= ?
              AND paragraph_end >= ?
            ORDER BY paragraph_start, id
            """,
            (article_slug, end_paragraph + 1, start_paragraph - 1),
        ).fetchall()
    except (sqlite3.Error, SystemError):
        return match
    if not rows:
        return match

    context_rows = [row for row in rows if str(row["text"] or "").strip()]
    if not context_rows:
        return match

    return {
        **match,
        "full_text": "\n\n".join(str(row["text"] or "") for row in context_rows),
        "context_unit_keys": [f"ukrainian_wiki:{row['passage_id']}" for row in context_rows],
    }


def _expand_neighbor_context(match: dict) -> dict:
    corpus = str(match.get("corpus", ""))
    if corpus in {"modern_literary", "archaic_literary"}:
        return _expand_literary_neighbors(match)
    if corpus == "wikipedia":
        return _expand_wikipedia_neighbors(match)
    if corpus == "ukrainian_wiki":
        return _expand_ukrainian_wiki_neighbors(match)
    return match


def _apply_context_cap(track: str, matches: list[dict]) -> list[dict]:
    from .enrichment import SOURCE_CHAR_CAPS

    char_cap = int(SOURCE_CHAR_CAPS.get(track, 110_000))
    total = 0
    selected: list[dict] = []
    seen_contexts: set[tuple] = set()

    for match in matches:
        full_text = str(match.get("full_text") or match.get("text") or "")
        if not full_text.strip():
            continue
        context_key = (
            str(match.get("corpus", "")),
            str(match.get("parent_key", "")),
            tuple(match.get("context_unit_keys", []) or [str(match.get("unit_key", ""))]),
        )
        if context_key in seen_contexts:
            continue

        if not selected and len(full_text) > char_cap:
            trimmed = {**match, "full_text": full_text[:char_cap], "text": full_text[:char_cap]}
            selected.append(trimmed)
            break

        if total + len(full_text) > char_cap:
            continue

        selected.append({**match, "text": full_text})
        total += len(full_text)
        seen_contexts.add(context_key)

    return selected


def _search_archaic_metadata(
    bucket_a_phrases: list[str],
    bucket_b_keywords: set[str],
    *,
    limit: int,
) -> list[dict]:
    candidates = _search_literary_candidates(
        bucket_a_phrases,
        bucket_b_keywords,
        corpus="archaic_literary",
        candidate_k=limit,
    )
    return [
        {
            **candidate,
            "dense_score": 0.0,
            "prior_weight": 1.0,
            "final_score": 0.0,
        }
        for candidate in candidates[:limit]
    ]


def search_sources(
    query: str | Path,
    *,
    track: str,
    strategy: str = "unified_dense",
    limit: int = 10,
    candidate_k_per_corpus: int = 30,
) -> list[dict]:
    """Unified source search entry point for compile-layer retrieval."""
    if strategy == "archaic_metadata":
        bucket_a_phrases, bucket_b_keywords, _ = _prepare_query(query, track)
        return _apply_context_cap(
            track,
            _search_archaic_metadata(
                bucket_a_phrases,
                bucket_b_keywords,
                limit=limit,
            ),
        )
    if strategy == "modern_dense_section":
        strategy = "unified_dense"
    if strategy != "unified_dense":
        raise ValueError(f"Unsupported search_sources strategy: {strategy}")

    bucket_a_phrases, bucket_b_keywords, dense_query = _prepare_query(query, track)
    if not dense_query.strip():
        return []

    with ThreadPoolExecutor(max_workers=len(_CORPORA)) as executor:
        futures = [
            executor.submit(
                _dispatch_corpus_search,
                corpus,
                bucket_a_phrases=bucket_a_phrases,
                bucket_b_keywords=bucket_b_keywords,
                dense_query=dense_query,
                track=track,
                candidate_k_per_corpus=candidate_k_per_corpus,
            )
            for corpus in _CORPORA
        ]
        merged: list[dict] = []
        for future in futures:
            merged.extend(future.result())

    merged.sort(
        key=lambda row: (
            -float(row.get("final_score", 0.0)),
            -float(row.get("dense_score", 0.0)),
            float(row.get("fts_score", row.get("rank", 0.0)) or 0.0),
            str(row.get("unit_key", "")),
        )
    )
    expanded = [_expand_neighbor_context(match) for match in merged[:max(limit * 3, limit)]]
    capped = _apply_context_cap(track, expanded)
    return capped[:limit]


# ── FTS5 search functions (prose) ───────────────────────────────


# Track→grade mapping was REMOVED in #1340 (2026-04-20). See
# `docs/architecture/adr/adr-007-no-hard-grade-filter-for-cefr-retrieval.md`
# for the full rationale, alternatives considered, and verification
# strategy. Short version: CEFR L2 levels and Ukrainian L1 school
# grades are orthogonal scaffolding systems — dense rerank (#1348)
# is the source of truth for topic relevance, not a hard SQL gate.
#
# DO NOT re-introduce a hard `WHERE grade IN (...)` filter without
# updating ADR-007 first. Soft priors at the rerank layer are fine.


def _fts_search(fts_table: str, data_table: str,
                keywords: set[str], max_total: int,
                extra_cols: str = "",
                min_text_len: int = 300,
                extra_where: str = "",
                extra_params: tuple = ()) -> list[dict]:
    """Generic FTS5 search across any prose table.

    Args:
        min_text_len: Minimum text length to include (default 300).
            Filters noise: TOC pages, captions, exercise headers,
            publisher fragments, OCR artifacts. 300 chars ≈ 2 sentences
            of real content — below that, chunks rarely contain
            anything the wiki compiler can cite.
            Set to 0 to disable.

    Race-safe: retries on `sqlite3.OperationalError` (typically
    "database is locked") per `_FTS_RETRY_DELAYS_S`. If all retries
    exhaust the error propagates — caller can decide policy. See
    2026-04-18 smoke-test note on `_SQLITE_BUSY_TIMEOUT_MS`.
    """
    try:
        conn = _get_conn()
    except FileNotFoundError:
        return []

    fts_query = _build_fts_query(keywords)
    if not fts_query:
        return []

    cols = f"s.*, bm25({fts_table}, 5.0, 1.0) AS rank"
    if extra_cols:
        cols = f"s.*, {extra_cols}, bm25({fts_table}, 5.0, 1.0) AS rank"

    # Filter out short/noise chunks (TOC pages, captions, exercise headers)
    length_filter = f"AND length(s.text) >= {min_text_len}" if min_text_len > 0 else ""

    sql = f"""SELECT {cols}
            FROM {fts_table}
            JOIN {data_table} s ON s.id = {fts_table}.rowid
            WHERE {fts_table} MATCH ?
            {length_filter}
            {extra_where}
            ORDER BY rank
            LIMIT ?"""
    params = (fts_query, *extra_params, max_total)

    attempt_delays: tuple[float, ...] = (0.0, *_FTS_RETRY_DELAYS_S)
    last_exc: sqlite3.OperationalError | None = None
    for attempt_delay in attempt_delays:
        if attempt_delay > 0:
            import sys as _sys
            import time as _time
            print(
                f"  ⚠️  FTS5 query on {fts_table} retrying in "
                f"{attempt_delay}s (DB lock / FTS rebuild race)",
                file=_sys.stderr,
            )
            _time.sleep(attempt_delay)
        try:
            rows = conn.execute(sql, params).fetchall()
            return [dict(row) for row in rows]
        except sqlite3.OperationalError as exc:
            last_exc = exc
            continue
    # All retries exhausted
    assert last_exc is not None
    raise last_exc


def search_textbooks(
    ukr_keywords: set[str],
    max_total: int = 40,
    *,
    track: str | None = None,
) -> list[dict]:
    """Deprecated chunk-level FTS5 textbook search kept for backward compatibility.

    Filters out TOC pages and short noise chunks before returning.
    Requests extra rows from FTS5 to compensate for filtered-out noise.

    `track`: accepted for backward compatibility with existing callers;
    the value is no longer consulted. This function is deprecated; use
    `search_sources` for new code.
    """
    _ = track  # accepted for backward compatibility; ignored
    extra_where = ""
    extra_params: tuple = ()
    # Request 2x to compensate for filtered TOC/noise chunks
    rows = _fts_search(
        "textbooks_fts", "textbooks", ukr_keywords, max_total * 2,
        extra_where=extra_where, extra_params=extra_params,
    )
    results = []
    for r in rows:
        text = r.get("text", "")
        if _is_noise(text):
            continue
        r["_kw_score"] = _kw_score(text, r.get("title", ""), ukr_keywords)
        r["source_type"] = "textbook"
        r["section_title"] = r.get("title", "")
        results.append(r)
        if len(results) >= max_total:
            break
    return results


def search_external(
    ukr_keywords: set[str],
    max_total: int = 10,
    exclude_urls: set[str] | None = None,
    *,
    channel: str | None = None,
    register: str | None = None,
    decolonization: str | None = None,
    min_quality_tier: int | None = None,
    track: str | None = None,
) -> list[dict]:
    """Search external articles via FTS5."""
    try:
        conn = _get_conn()
    except FileNotFoundError:
        return []

    fts_query = _build_fts_query(ukr_keywords)
    if not fts_query:
        return []

    columns = _table_columns("external_articles")
    where = ["external_fts MATCH ?"]
    params: list[object] = [fts_query]
    if channel:
        if "channel_id" not in columns:
            return []
        where.append("s.channel_id = ?")
        params.append(channel)
    if register:
        if "register_tag" not in columns:
            return []
        where.append("s.register_tag = ?")
        params.append(register)
    if decolonization:
        if "decolonization_tag" not in columns:
            return []
        where.append("s.decolonization_tag = ?")
        params.append(decolonization)
    if min_quality_tier is not None:
        if "quality_tier" not in columns:
            return []
        where.append("COALESCE(s.quality_tier, 99) <= ?")
        params.append(int(min_quality_tier))

    # ``max_total * 15`` cushion (was * 5) so the Python-side affinity +
    # quality re-ranker has a deeper candidate pool to work with. With * 5,
    # high-affinity chunks with weaker BM25 scores were being truncated
    # before reaching ``rank_external_hits``. Gemini review #354 (#1324)
    # item 8.
    rows = conn.execute(
        f"""SELECT s.*, bm25(external_fts) AS rank
            FROM external_fts
            JOIN external_articles s ON s.id = external_fts.rowid
            WHERE {' AND '.join(where)}
            ORDER BY rank
            LIMIT ?""",
        (*params, max_total * 15),
    ).fetchall()

    skip = exclude_urls or set()
    results: list[dict] = []
    seen_chunk_ids: set[str] = set()
    channels: dict[str, dict] = {}
    try:
        from .channels import load_channels

        channels = load_channels()
    except Exception:
        channels = {}

    for row in rows:
        r = dict(row)
        url = str(r.get("url", "")).strip()
        if url in skip:
            continue
        chunk_id = str(r.get("chunk_id", "")).strip()
        if chunk_id and chunk_id in seen_chunk_ids:
            continue
        if chunk_id:
            seen_chunk_ids.add(chunk_id)

        source_file = str(r.get("source_file", "")).strip()
        channel_meta = channels.get(source_file, {})
        channel_id = str(r.get("channel_id", "") or source_file).strip()
        quality_tier = int(r.get("quality_tier", channel_meta.get("quality_tier", 2)) or 2)
        speaker = str(r.get("speaker", "") or channel_meta.get("host", "")).strip()
        register_tag = str(r.get("register_tag", "") or channel_meta.get("register_tag", "")).strip()
        decolonization_tag = str(
            r.get("decolonization_tag", "") or channel_meta.get("decolonization_tag", "")
        ).strip()
        channel_name = str(channel_meta.get("name", "")).strip()

        r["_kw_score"] = _kw_score(r.get("text", ""), r.get("title", ""), ukr_keywords)
        r["source_type"] = "external"
        r["channel_id"] = channel_id
        r["speaker"] = speaker
        r["register_tag"] = register_tag
        r["decolonization_tag"] = decolonization_tag
        r["quality_tier"] = quality_tier
        r["source_name"] = channel_name or r.get("domain", r.get("source_file", ""))
        r["text"] = r.get("text", "")[:6000]
        r["fts_score"] = float(r.get("rank", 0.0) or 0.0)
        r["adjusted_score"] = r["fts_score"]
        results.append(r)

    if track:
        results = rank_external_hits(
            results,
            track=track,
            apply_quality_without_track=False,
        )

    return results[:max_total]


def search_literary(ukr_keywords: set[str], max_total: int = 20) -> list[dict]:
    """Deprecated chunk-level literary FTS5 search kept for backward compatibility."""
    rows = _fts_search("literary_fts", "literary_texts", ukr_keywords, max_total)
    for r in rows:
        r["_kw_score"] = _kw_score(r.get("text", ""), r.get("title", ""), ukr_keywords)
        r["source_type"] = "literary"
    return rows


def search_wikipedia(ukr_keywords: set[str], max_total: int = 10) -> list[dict]:
    """Search Wikipedia articles via FTS5."""
    try:
        conn = _get_conn()
        # Check if wikipedia table exists
        tables = [r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='wikipedia'"
        ).fetchall()]
        if "wikipedia" not in tables:
            return []
    except (FileNotFoundError, Exception):
        return []

    rows = _fts_search("wikipedia_fts", "wikipedia", ukr_keywords, max_total)
    for r in rows:
        r["_kw_score"] = _kw_score(r.get("text", ""), r.get("title", ""), ukr_keywords)
        r["source_type"] = "wikipedia"
        r["source_name"] = "Wikipedia"
        r["text"] = r.get("text", "")[:5000]
    return rows


# ── Dictionary lookup functions (indexed tables) ────────────────


def _dict_lookup(table: str, word: str, limit: int = 10) -> list[dict]:
    """Generic headword lookup on an indexed dictionary table."""
    try:
        conn = _get_conn()
    except FileNotFoundError:
        return []

    # Exact match first, then prefix match
    rows = conn.execute(
        f"SELECT * FROM {table} WHERE word = ? COLLATE NOCASE LIMIT ?",
        (word, limit),
    ).fetchall()

    if not rows:
        rows = conn.execute(
            f"SELECT * FROM {table} WHERE word LIKE ? COLLATE NOCASE LIMIT ?",
            (f"{word}%", limit),
        ).fetchall()

    return [dict(r) for r in rows]


def search_definitions(word: str, limit: int = 10) -> list[dict]:
    """Look up word in СУМ-11 (Ukrainian explanatory dictionary)."""
    return _dict_lookup("sum11", word, limit)


def search_etymology(word: str, limit: int = 10) -> list[dict]:
    """Look up word in Грінченко (historical dictionary)."""
    return _dict_lookup("grinchenko", word, limit)


def translate_en_uk(word: str, limit: int = 10) -> list[dict]:
    """Look up English→Ukrainian translation in Балла."""
    return _dict_lookup("balla_en_uk", word, limit)


def search_idioms(word: str, limit: int = 10) -> list[dict]:
    """Look up idioms/expressions in Фразеологічний."""
    return _dict_lookup("frazeolohichnyi", word, limit)


def search_synonyms(word: str, limit: int = 20) -> list[dict]:
    """Look up synonyms in Ukrajinet WordNet."""
    try:
        conn = _get_conn()
    except FileNotFoundError:
        return []

    # Search in the 'words' field (comma-separated synset members)
    rows = conn.execute(
        "SELECT * FROM ukrajinet WHERE words LIKE ? COLLATE NOCASE LIMIT ?",
        (f"%{word}%", limit),
    ).fetchall()
    return [dict(r) for r in rows]


def query_cefr_level(word: str, limit: int = 5) -> list[dict]:
    """Look up CEFR level for a word in PULS vocabulary."""
    return _dict_lookup("puls_cefr", word, limit=limit)


def search_style_guide(word: str, limit: int = 5) -> list[dict]:
    """Look up calques/Russianisms in Антоненко-Давидович style guide."""
    return _dict_lookup("style_guide", word, limit)


def lookup_by_url(url: str) -> dict | None:
    """Look up an external article by URL. Handles www/non-www variants."""
    try:
        conn = _get_conn()
    except FileNotFoundError:
        return None

    normalized = url.replace("://www.", "://")
    row = conn.execute(
        "SELECT * FROM external_articles WHERE url = ? OR url_normalized = ? LIMIT 1",
        (url, normalized),
    ).fetchone()
    return dict(row) if row else None


def source_count(table: str | None = None) -> int:
    """Return entry count for a table, or total across all tables."""
    try:
        conn = _get_conn()
    except FileNotFoundError:
        return 0

    if table:
        return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]

    tables = [
        "textbooks", "external_articles", "literary_texts",
        "sum11", "grinchenko", "balla_en_uk", "dmklinger_uk_en",
        "ukrajinet", "wiktionary", "frazeolohichnyi", "puls_cefr", "style_guide",
    ]
    return sum(
        conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        for t in tables
    )


def list_tables() -> dict[str, int]:
    """Return {table_name: count} for all content tables."""
    try:
        conn = _get_conn()
    except FileNotFoundError:
        return {}

    tables = [
        "textbooks", "external_articles", "literary_texts",
        "sum11", "grinchenko", "balla_en_uk", "dmklinger_uk_en",
        "ukrajinet", "wiktionary", "frazeolohichnyi", "puls_cefr", "style_guide",
    ]
    return {
        t: conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        for t in tables
    }
