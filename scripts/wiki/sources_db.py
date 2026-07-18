"""SQLite interface for ALL source content — replaces Qdrant RAG entirely.

FTS5 tables (prose search):
- search_textbooks() — textbook chunks
- search_external() — external articles (ULP, blogs, YouTube)
- search_literary() — literary texts (chronicles, poetry, legal)

Indexed tables (dictionary headword lookup):
- search_definitions() — СУМ-11
- search_grinchenko_1907() — Грінченко
- search_esum() — ЕСУМ etymological dictionary
- search_idioms() — Фразеологічний
- search_synonyms() — Ukrajinet WordNet
- translate_en_uk() — Балла EN→UK
- query_cefr_level() — PULS CEFR
- search_style_guide() — Антоненко-Давидович
- search_slovnyk_me() — curated slovnyk.me verification snapshots / live lookup
- search_heritage() — merged Ukrainian heritage-defense lookup
- lookup_by_url() — external article URL lookup
"""

import hashlib
import json
import sqlite3
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import yaml

from scripts.lexicon.esum_garbled import (
    garbled_esum_entry,
    has_mojibake_marker,
    strip_garbled_tail,
    trim_curated_goroh_text,
)

from . import slovnyk_me
from .channels import rank_external_hits
from .chunking import chunk_text, policy_for
from .dense_rerank import _get_tokenizer, rerank_candidates, rerank_sections
from .query_builder import build_query_buckets
from .sum20_official import (
    PARSER_VERSION as SUM20_PARSER_VERSION,
)
from .sum20_official import (
    SUM20_ATTRIBUTION_LABEL,
    SUM20_SOURCE_ID,
    normalize_sum20_lookup,
)
from .textbook_subjects import normalize_subject_slug

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SOURCES_DB_PATH = PROJECT_ROOT / "data" / "sources.db"
TRACK_PRIORS_PATH = PROJECT_ROOT / "scripts" / "wiki" / "track_priors.yaml"
# Per-component path length limit is ~255 bytes on macOS HFS+/APFS and most
# Linux filesystems. Long Cyrillic plan-topic concatenations (>1 KB) trigger
# OSError "File name too long" inside Path.exists(). Caller fallbacks can
# swallow that and falsely mark plan references as corpus_missing (#1901).
_MAX_PATH_PROBE_BYTES = 255

_conn: sqlite3.Connection | None = None


# ── ULIF DictUA cache -------------------------------------------------

ULIF_DICTUA_SOURCE_ID = "ulif_dictua"
ULIF_DICTUA_OFFICIAL_URL = "https://lcorp.ulif.org.ua/dictua"
ULIF_DICTUA_ATTRIBUTION_LABEL = (
    "«Словники України» (Український мовно-інформаційний фонд НАН України)"
)
ULIF_DICTUA_SECTION_KINDS = ("paradigm", "synonyms", "antonyms", "phraseology")

# DictUA is a live ASP.NET source.  The source DB stores the parsed material
# and its exact HTML separately: keeping only the parsed JSON made cache rows
# impossible to audit or re-parse after a parser upgrade.
ULIF_DICTUA_SCHEMA = """
CREATE TABLE IF NOT EXISTS ulif_dictua_raw_responses (
    response_sha256 TEXT PRIMARY KEY,
    body BLOB NOT NULL,
    content_type TEXT NOT NULL DEFAULT 'text/html; charset=utf-8',
    stored_at TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS ulif_dictua_entries (
    id INTEGER PRIMARY KEY,
    normalized_query TEXT NOT NULL UNIQUE,
    canonical_headword TEXT NOT NULL DEFAULT '',
    raw_response_ref TEXT NOT NULL DEFAULT '',
    retrieved_at TEXT NOT NULL DEFAULT '',
    response_sha256 TEXT NOT NULL DEFAULT '',
    parser_version TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL CHECK (status IN ('ok', 'not_found', 'transient_error', 'parse_error'))
);
CREATE INDEX IF NOT EXISTS idx_ulif_dictua_entries_status
    ON ulif_dictua_entries(status, normalized_query);

CREATE TABLE IF NOT EXISTS ulif_dictua_sections (
    id INTEGER PRIMARY KEY,
    entry_id INTEGER NOT NULL REFERENCES ulif_dictua_entries(id) ON DELETE CASCADE,
    kind TEXT NOT NULL CHECK (kind IN ('paradigm', 'synonyms', 'antonyms', 'phraseology')),
    source_order INTEGER NOT NULL CHECK (source_order >= 0),
    sense_or_group_id TEXT NOT NULL DEFAULT '',
    payload_json TEXT NOT NULL,
    UNIQUE(entry_id, kind, source_order)
);
CREATE INDEX IF NOT EXISTS idx_ulif_dictua_sections_entry_kind_order
    ON ulif_dictua_sections(entry_id, kind, source_order);
"""


def normalize_ulif_dictua_query(word: str) -> str:
    """Return DictUA's stable, case-insensitive cache key for *word*."""
    return " ".join(word.split()).casefold()


def ensure_ulif_dictua_schema(conn: sqlite3.Connection) -> None:
    """Create the live DictUA cache schema on new and legacy sources DBs."""
    conn.execute("PRAGMA foreign_keys=ON")
    conn.executescript(ULIF_DICTUA_SCHEMA)


def _ulif_dictua_conn(
    db_path: str | Path | None = None,
    *,
    create: bool = False,
) -> sqlite3.Connection | None:
    """Open a dedicated connection and ensure the DictUA cache schema exists."""
    path = Path(db_path) if db_path is not None else SOURCES_DB_PATH
    if not path.exists():
        if not create:
            return None
        path.parent.mkdir(parents=True, exist_ok=True)
    conn = _open_conn(path)
    ensure_ulif_dictua_schema(conn)
    conn.commit()
    return conn


def _ulif_dictua_payloads(payload: object) -> list[dict]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        return [payload]
    return []


def _ulif_dictua_provenance(row: sqlite3.Row) -> dict:
    return {
        "source_id": ULIF_DICTUA_SOURCE_ID,
        "official_url": ULIF_DICTUA_OFFICIAL_URL,
        "attribution_label": ULIF_DICTUA_ATTRIBUTION_LABEL,
        "retrieved_at": row["retrieved_at"],
        "content_sha256": row["response_sha256"],
        "parser_version": row["parser_version"],
        "status": row["status"],
    }


def _materialize_ulif_dictua_entry(
    conn: sqlite3.Connection,
    entry: sqlite3.Row,
) -> dict:
    """Hydrate one DictUA entry without flattening its relation groups."""
    section_rows = conn.execute(
        """
        SELECT kind, source_order, sense_or_group_id, payload_json
        FROM ulif_dictua_sections
        WHERE entry_id = ?
        ORDER BY kind, source_order
        """,
        (entry["id"],),
    ).fetchall()
    sections: dict[str, list[dict]] = {}
    for row in section_rows:
        try:
            payload = json.loads(row["payload_json"])
        except json.JSONDecodeError:
            payload = {"raw_payload_json": row["payload_json"]}
        if not isinstance(payload, dict):
            payload = {"value": payload}
        payload.setdefault("source_order", row["source_order"])
        payload.setdefault("sense_or_group_id", row["sense_or_group_id"])
        sections.setdefault(row["kind"], []).append(payload)

    materialized_sections: dict[str, object] = {}
    for kind, payloads in sections.items():
        # Paradigms are one structured table; relation kinds deliberately
        # remain ordered groups rather than a bag of individual words.
        materialized_sections[kind] = payloads[0] if kind == "paradigm" else payloads

    word = entry["canonical_headword"] or entry["normalized_query"]
    section_summary = ", ".join(materialized_sections) or "entry"
    definition = f"Official DictUA {section_summary} for {word}."

    return {
        "word": word,
        "canonical_headword": entry["canonical_headword"],
        "normalized_query": entry["normalized_query"],
        # These conventional dictionary keys keep ULIF rows consumable by
        # existing dictionary renderers without replacing their nested data.
        "source": ULIF_DICTUA_ATTRIBUTION_LABEL,
        "definition": definition,
        "text": definition,
        "raw_response_ref": entry["raw_response_ref"],
        "sections": materialized_sections,
        **_ulif_dictua_provenance(entry),
    }


def get_ulif_dictua_entry(
    word: str,
    *,
    db_path: str | Path | None = None,
) -> dict | None:
    """Return a cached, materialized DictUA lookup for *word*, if present."""
    normalized = normalize_ulif_dictua_query(word)
    if not normalized:
        return None
    conn = _ulif_dictua_conn(db_path)
    if conn is None:
        return None
    try:
        entry = conn.execute(
            "SELECT * FROM ulif_dictua_entries WHERE normalized_query = ?",
            (normalized,),
        ).fetchone()
        return _materialize_ulif_dictua_entry(conn, entry) if entry else None
    finally:
        conn.close()


def resolve_ulif_dictua_raw_response(
    raw_response_ref: str,
    *,
    db_path: str | Path | None = None,
) -> bytes | None:
    """Resolve a ``sha256:<digest>`` raw-response reference from the cache."""
    digest = raw_response_ref.removeprefix("sha256:")
    if len(digest) != 64:
        return None
    conn = _ulif_dictua_conn(db_path)
    if conn is None:
        return None
    try:
        row = conn.execute(
            "SELECT body FROM ulif_dictua_raw_responses WHERE response_sha256 = ?",
            (digest,),
        ).fetchone()
        return bytes(row["body"]) if row else None
    finally:
        conn.close()


def store_ulif_dictua_entry(
    *,
    word: str,
    canonical_headword: str,
    sections: dict[str, object],
    raw_responses: dict[str, str | bytes],
    retrieved_at: str,
    parser_version: str,
    status: str,
    db_path: str | Path | None = None,
) -> dict | None:
    """Persist one complete DictUA response and return its materialized form.

    Transient failures are intentionally never persisted: a network outage is
    not evidence that a Ukrainian word does not exist.
    """
    if status == "transient_error":
        return None
    if status not in {"ok", "not_found", "parse_error"}:
        raise ValueError(f"Unsupported DictUA cache status: {status}")
    normalized = normalize_ulif_dictua_query(word)
    if not normalized:
        return None

    conn = _ulif_dictua_conn(db_path, create=True)
    assert conn is not None
    try:
        raw_refs: dict[str, str] = {}
        for kind, response in sorted(raw_responses.items()):
            if kind not in ULIF_DICTUA_SECTION_KINDS:
                continue
            body = response.encode("utf-8") if isinstance(response, str) else response
            digest = hashlib.sha256(body).hexdigest()
            conn.execute(
                """
                INSERT OR IGNORE INTO ulif_dictua_raw_responses
                    (response_sha256, body, stored_at)
                VALUES (?, ?, ?)
                """,
                (digest, body, retrieved_at),
            )
            raw_refs[kind] = f"sha256:{digest}"

        manifest = json.dumps(raw_refs, ensure_ascii=False, sort_keys=True).encode("utf-8")
        response_sha256 = hashlib.sha256(manifest).hexdigest()
        conn.execute(
            """
            INSERT OR IGNORE INTO ulif_dictua_raw_responses
                (response_sha256, body, content_type, stored_at)
            VALUES (?, ?, 'application/json', ?)
            """,
            (response_sha256, manifest, retrieved_at),
        )
        raw_response_ref = f"sha256:{response_sha256}"

        conn.execute(
            """
            INSERT INTO ulif_dictua_entries
                (normalized_query, canonical_headword, raw_response_ref,
                 retrieved_at, response_sha256, parser_version, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(normalized_query) DO UPDATE SET
                canonical_headword = excluded.canonical_headword,
                raw_response_ref = excluded.raw_response_ref,
                retrieved_at = excluded.retrieved_at,
                response_sha256 = excluded.response_sha256,
                parser_version = excluded.parser_version,
                status = excluded.status
            """,
            (
                normalized,
                canonical_headword,
                raw_response_ref,
                retrieved_at,
                response_sha256,
                parser_version,
                status,
            ),
        )
        entry = conn.execute(
            "SELECT * FROM ulif_dictua_entries WHERE normalized_query = ?",
            (normalized,),
        ).fetchone()
        assert entry is not None
        conn.execute("DELETE FROM ulif_dictua_sections WHERE entry_id = ?", (entry["id"],))
        if status in {"ok", "parse_error"}:
            for kind in ULIF_DICTUA_SECTION_KINDS:
                for source_order, payload in enumerate(_ulif_dictua_payloads(sections.get(kind))):
                    payload.setdefault("source_order", source_order)
                    payload.setdefault("sense_or_group_id", f"{kind}:{source_order + 1}")
                    raw_ref = raw_refs.get(kind)
                    if raw_ref:
                        payload.setdefault("raw_response_ref", raw_ref)
                    conn.execute(
                        """
                        INSERT INTO ulif_dictua_sections
                            (entry_id, kind, source_order, sense_or_group_id, payload_json)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (
                            entry["id"],
                            kind,
                            source_order,
                            str(payload["sense_or_group_id"]),
                            json.dumps(payload, ensure_ascii=False, sort_keys=True),
                        ),
                    )
        conn.commit()
        return _materialize_ulif_dictua_entry(conn, entry)
    finally:
        conn.close()


def extract_ulif_dictua_snapshot(
    db_path: str | Path,
) -> tuple[list[tuple], list[tuple], list[tuple]]:
    """Read cache rows for an atomic sources.db rebuild, tolerating legacy DBs."""
    path = Path(db_path)
    if not path.exists():
        return [], [], []
    conn: sqlite3.Connection | None = None
    try:
        conn = _open_conn(path)
        raw_rows = list(conn.execute(
            """
            SELECT response_sha256, body, content_type, stored_at
            FROM ulif_dictua_raw_responses
            ORDER BY response_sha256
            """
        ))
        entry_rows = list(conn.execute(
            """
            SELECT id, normalized_query, canonical_headword, raw_response_ref,
                   retrieved_at, response_sha256, parser_version, status
            FROM ulif_dictua_entries
            ORDER BY id
            """
        ))
        section_rows = list(conn.execute(
            """
            SELECT id, entry_id, kind, source_order, sense_or_group_id, payload_json
            FROM ulif_dictua_sections
            ORDER BY id
            """
        ))
        return raw_rows, entry_rows, section_rows
    except sqlite3.Error:
        return [], [], []
    finally:
        if conn is not None:
            conn.close()


def restore_ulif_dictua_snapshot(
    conn: sqlite3.Connection,
    raw_rows: list[tuple],
    entry_rows: list[tuple],
    section_rows: list[tuple],
) -> None:
    """Restore DictUA cache rows in foreign-key-safe dependency order."""
    ensure_ulif_dictua_schema(conn)
    if raw_rows:
        conn.executemany(
            """
            INSERT OR IGNORE INTO ulif_dictua_raw_responses
                (response_sha256, body, content_type, stored_at)
            VALUES (?, ?, ?, ?)
            """,
            raw_rows,
        )
    if entry_rows:
        conn.executemany(
            """
            INSERT OR IGNORE INTO ulif_dictua_entries
                (id, normalized_query, canonical_headword, raw_response_ref,
                 retrieved_at, response_sha256, parser_version, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            entry_rows,
        )
    if section_rows:
        conn.executemany(
            """
            INSERT OR IGNORE INTO ulif_dictua_sections
                (id, entry_id, kind, source_order, sense_or_group_id, payload_json)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            section_rows,
        )


def search_ulif_dictua_sections(
    word: str,
    kind: str,
    *,
    limit: int = 20,
    db_path: str | Path | None = None,
) -> list[dict]:
    """Return an ordered, structured DictUA relation result for a cached word."""
    if kind not in ULIF_DICTUA_SECTION_KINDS or limit < 1:
        return []
    record = get_ulif_dictua_entry(word, db_path=db_path)
    if not record or record["status"] != "ok" or not record["sections"].get(kind):
        return []
    record["matched_section"] = kind
    # Keep the original nested group payload in metadata instead of reducing
    # relations to an unattributed comma-separated word list.
    return [record]


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


def _open_conn(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    # Concurrent readers must wait for a concurrent writer rather
    # than silently returning empty rowsets — see §race-condition
    # comment on `_SQLITE_BUSY_TIMEOUT_MS` above.
    conn.execute(f"PRAGMA busy_timeout = {_SQLITE_BUSY_TIMEOUT_MS}")
    return conn


def _get_conn() -> sqlite3.Connection:
    """Get or create a cached database connection."""
    global _conn
    if _conn is None:
        if not SOURCES_DB_PATH.exists():
            raise FileNotFoundError(
                f"Sources database not found at {SOURCES_DB_PATH}. "
                "Run: .venv/bin/python scripts/wiki/build_sources_db.py"
            )
        _conn = _open_conn(SOURCES_DB_PATH)
    return _conn


def _get_conn_for(db_path: str | Path | None = None) -> sqlite3.Connection:
    if db_path is None:
        return _get_conn()
    source_db = Path(db_path)
    if not source_db.exists():
        raise FileNotFoundError(
            f"Sources database not found at {source_db}. "
            "Run: .venv/bin/python scripts/wiki/build_sources_db.py"
        )
    return _open_conn(source_db)


def _close_if_temporary(conn: sqlite3.Connection, db_path: str | Path | None) -> None:
    if db_path is not None:
        conn.close()


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


def _table_columns(table: str, db_path: str | Path | None = None) -> set[str]:
    """Return the column names for a SQLite table."""
    conn = None
    try:
        conn = _get_conn_for(db_path)
    except FileNotFoundError:
        return set()
    try:
        return {
            row["name"]
            for row in conn.execute(f"PRAGMA table_info({table})").fetchall()
        }
    finally:
        _close_if_temporary(conn, db_path)


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
    is_path = False
    if isinstance(query, Path) or len(str(query).encode("utf-8")) <= _MAX_PATH_PROBE_BYTES:
        try:
            is_path = candidate_path.exists()
        except OSError:
            is_path = False
    if is_path:
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
            s.source_url,
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
            "source_url": str(row["source_url"] or ""),
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

    candidates: list[dict] = []
    policy = policy_for("external")
    tokenizer = _get_tokenizer()
    for row in rows:
        parent_id = str(row["chunk_id"] or row["id"])
        full_text = str(row["text"] or "")
        for piece in chunk_text(full_text, policy=policy, tokenizer=tokenizer):
            unit_key = (
                f"external:{parent_id}:chunk_{piece.chunk_index}"
                if piece.extra_metadata
                else f"external:{parent_id}"
            )
            candidates.append({
                "unit_key": unit_key,
                "corpus": "external",
                "source_type": "external",
                "chunk_id": str(row["chunk_id"] or ""),
                "title": str(row["title"] or ""),
                "text": piece.text,
                "full_text": piece.text,
                "source_file": str(row["source_file"] or ""),
                "parent_key": str(row["source_file"] or ""),
                "url": str(row["url"] or ""),
                "source_name": str(row["domain"] or row["source_file"] or ""),
                "speaker": str(row["speaker"] or ""),
                "chunk_index": piece.chunk_index,
                "parent_unit_key": f"external:{parent_id}",
                "fts_score": float(row["rank"] or 0.0),
            })
    return candidates


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


def _expand_to_chunk_candidates(
    parent_candidates: list[dict],
    *,
    corpus: str,
    parent_id_field: str,
    text_field: str = "text",
) -> list[dict]:
    """Fan out each parent-level candidate into chunk-level
    candidates whose ``unit_key``s match the manifest written by
    ``load_corpus_units``.

    Each input candidate's ``parent_id_field`` (e.g. ``section_id``)
    plus the corpus name forms the parent unit_key; the chunker
    appends ``:chunk_N`` only when the policy actually splits the
    text into multiple pieces. Single-chunk pieces preserve the
    original parent unit_key so short sections / articles stay
    identifiable by their natural id.

    Codex review (msg #459): textbook and external candidate paths
    were emitting parent ``unit_key``s after step 1 chunked the
    manifest entries — every chunked unit got a dense rerank miss
    + zero score. This helper fixes that uniformly.
    """

    policy = policy_for(corpus)
    tokenizer = _get_tokenizer()
    expanded: list[dict] = []
    for parent in parent_candidates:
        parent_id_value = parent.get(parent_id_field)
        if parent_id_value is None:
            continue
        parent_unit_key = f"{corpus}:{parent_id_value}"
        full_text = str(parent.get(text_field, "") or "")
        if not full_text:
            continue
        pieces = list(chunk_text(full_text, policy=policy, tokenizer=tokenizer))
        if not pieces:
            continue
        for piece in pieces:
            unit_key = (
                f"{parent_unit_key}:chunk_{piece.chunk_index}"
                if piece.extra_metadata
                else parent_unit_key
            )
            expanded.append({
                **parent,
                "corpus": corpus,
                "unit_key": unit_key,
                "parent_unit_key": parent_unit_key,
                "parent_key": str(parent.get("source_file") or parent.get("parent_key", "")),
                "text": piece.text,
                "full_text": piece.text,
                "chunk_index": piece.chunk_index,
                "fts_score": float(
                    parent.get("fts_score") or parent.get("best_rank", 0.0) or 0.0
                ),
            })
    return expanded


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
        section_candidates = _search_sections_fts5(
            bucket_a_phrases,
            bucket_b_keywords,
            track=track,
            max_sections=candidate_k_per_corpus,
            max_chunk_candidates=max(candidate_k_per_corpus * 4, candidate_k_per_corpus),
        )
        # Each FTS5-matched section's full_text is fanned out into
        # chunk-level candidates whose unit_keys match the manifest
        # entries written by load_corpus_units. Without this, the
        # dense rerank lookup misses every chunked section's
        # sub-units and zeroes out the score (Codex msg #459).
        candidates = _expand_to_chunk_candidates(
            section_candidates,
            corpus="textbook_sections",
            parent_id_field="section_id",
        )
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
    require_textbook_section = strategy == "modern_dense_section"
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
    if require_textbook_section and not any(
        match.get("corpus") == "textbook_sections" for match in capped
    ):
        textbook_section = next(
            (match for match in expanded if match.get("corpus") == "textbook_sections"),
            None,
        )
        if textbook_section is None:
            raw_textbook_section = next(
                (match for match in merged if match.get("corpus") == "textbook_sections"),
                None,
            )
            if raw_textbook_section is not None:
                textbook_section = _expand_neighbor_context(raw_textbook_section)
        if textbook_section is not None:
            capped = [
                textbook_section,
                *[
                    match
                    for match in capped
                    if match.get("corpus") != "textbook_sections"
                    or match.get("unit_key") != textbook_section.get("unit_key")
                ],
            ]
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
    subject: str | None = None,
) -> list[dict]:
    """Deprecated chunk-level FTS5 textbook search kept for backward compatibility.

    Filters out TOC pages and short noise chunks before returning.
    Requests extra rows from FTS5 to compensate for filtered-out noise.

    `track`: accepted for backward compatibility with existing callers;
    the value is no longer consulted. `subject` filters against the
    canonical `textbooks.subject` slug. This function is deprecated; use
    `search_sources` for new code.
    """
    _ = track  # accepted for backward compatibility; ignored
    extra_where = ""
    extra_params: tuple = ()
    if subject:
        normalized_subject = normalize_subject_slug(subject)
        if normalized_subject is None:
            return []
        if "subject" not in _table_columns("textbooks"):
            raise sqlite3.OperationalError(
                "textbooks.subject column missing; run "
                "scripts/migrations/2026-07-06-add-subject-to-textbooks.py"
            )
        extra_where = "AND s.subject = ?"
        extra_params = (normalized_subject,)
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


def _dict_lookup(
    table: str,
    word: str,
    limit: int = 10,
    *,
    db_path: str | Path | None = None,
) -> list[dict]:
    """Generic headword lookup on an indexed dictionary table."""
    conn = None
    try:
        conn = _get_conn_for(db_path)
    except FileNotFoundError:
        return []

    try:
        # Exact match first, then prefix match
        try:
            rows = conn.execute(
                f"SELECT * FROM {table} WHERE word = ? COLLATE NOCASE LIMIT ?",
                (word, limit),
            ).fetchall()
            if not rows:
                rows = conn.execute(
                    f"SELECT * FROM {table} WHERE word LIKE ? COLLATE NOCASE LIMIT ?",
                    (f"{word}%", limit),
                ).fetchall()
        except sqlite3.OperationalError:
            return []

        return [dict(r) for r in rows]
    finally:
        _close_if_temporary(conn, db_path)


def _batch_dict_lookup(
    table: str,
    words: list[str],
    limit: int = 1,
    *,
    db_path: str | Path | None = None,
) -> dict[str, list[dict]]:
    """Look up many dictionary headwords without issuing one query per word.

    This is the batch counterpart to :func:`_dict_lookup`: exact headwords
    take precedence and unmatched requests then use its prefix fallback.  A
    chunk is deliberately much smaller than SQLite's conservative 999
    placeholder limit, so callers can batch the MCP tool's 500-word cap
    safely on older SQLite builds too.
    """
    requested = list(dict.fromkeys(str(word) for word in words if str(word).strip()))
    results: dict[str, list[dict]] = {word: [] for word in requested}
    if not requested:
        return results

    conn = None
    try:
        conn = _get_conn_for(db_path)
    except FileNotFoundError:
        return results

    try:
        for start in range(0, len(requested), 400):
            chunk = requested[start:start + 400]
            values = ", ".join("(?)" for _ in chunk)
            rows = conn.execute(
                f"""
                WITH requested(word) AS (VALUES {values}),
                ranked AS (
                    SELECT
                        requested.word AS requested_word,
                        dictionary.*,
                        ROW_NUMBER() OVER (
                            PARTITION BY requested.word
                            ORDER BY dictionary.word COLLATE NOCASE
                        ) AS result_order
                    FROM requested
                    JOIN {table} AS dictionary
                      ON dictionary.word = requested.word COLLATE NOCASE
                )
                SELECT * FROM ranked
                WHERE result_order <= ?
                """,
                (*chunk, limit),
            ).fetchall()
            for row in rows:
                item = dict(row)
                requested_word = item.pop("requested_word")
                item.pop("result_order", None)
                results[requested_word].append(item)

            missing = [word for word in chunk if not results[word]]
            if not missing:
                continue

            prefix_values = ", ".join("(?)" for _ in missing)
            rows = conn.execute(
                f"""
                WITH requested(word) AS (VALUES {prefix_values})
                SELECT requested.word AS requested_word, dictionary.*
                FROM requested
                JOIN {table} AS dictionary
                  ON dictionary.id = (
                    SELECT candidate.id
                    FROM {table} AS candidate
                    WHERE candidate.word LIKE requested.word || '%' COLLATE NOCASE
                    ORDER BY candidate.word COLLATE NOCASE
                    LIMIT 1
                  )
                """,
                missing,
            ).fetchall()
            for row in rows:
                item = dict(row)
                requested_word = item.pop("requested_word")
                results[requested_word].append(item)
    except sqlite3.OperationalError:
        return results
    finally:
        _close_if_temporary(conn, db_path)

    return results


def search_definitions(
    word: str,
    limit: int = 10,
    *,
    db_path: str | Path | None = None,
) -> list[dict]:
    """Look up word in СУМ-11 (Ukrainian explanatory dictionary)."""
    return _dict_lookup("sum11", word, limit, db_path=db_path)


def search_definitions_batch(
    words: list[str],
    *,
    db_path: str | Path | None = None,
) -> dict[str, list[dict]]:
    """Return the best СУМ-11 hit for each requested word in batched SQL."""
    return _batch_dict_lookup("sum11", words, limit=1, db_path=db_path)


def search_grinchenko_1907(
    word: str,
    limit: int = 10,
    *,
    db_path: str | Path | None = None,
) -> list[dict]:
    """Look up word in Грінченко (historical dictionary)."""
    return _dict_lookup("grinchenko", word, limit, db_path=db_path)


def search_grinchenko_batch(
    words: list[str],
    *,
    db_path: str | Path | None = None,
) -> dict[str, list[dict]]:
    """Return the best Грінченко hit for each requested word in batched SQL."""
    return _batch_dict_lookup("grinchenko", words, limit=1, db_path=db_path)


def search_balla_en_uk_batch(
    words: list[str],
    *,
    db_path: str | Path | None = None,
) -> dict[str, list[dict]]:
    """Return the best Балла EN→UK hit for each requested English headword."""
    return _batch_dict_lookup("balla_en_uk", words, limit=1, db_path=db_path)


def search_dmklinger_uk_en_batch(
    words: list[str],
    *,
    db_path: str | Path | None = None,
) -> dict[str, list[dict]]:
    """Batch-lookup dmklinger UK→EN by stress-normalized exact headword.

    ``dmklinger_uk_en`` stores stressed headwords (e.g. ``робо́та``). Plain
    equality therefore misses almost everything; strip U+0301 on both sides
    and match case-insensitively in 400-row chunks (same budget as
    :func:`_batch_dict_lookup`).
    """
    requested = list(dict.fromkeys(str(word) for word in words if str(word).strip()))
    results: dict[str, list[dict]] = {word: [] for word in requested}
    if not requested:
        return results

    conn = None
    try:
        conn = _get_conn_for(db_path)
    except FileNotFoundError:
        return results

    try:
        if not _table_columns("dmklinger_uk_en", db_path):
            return results
        for start in range(0, len(requested), 400):
            chunk = requested[start:start + 400]
            # Query keys are stress-stripped so callers can pass either form.
            plain_keys = [_strip_combining_acute(word) for word in chunk]
            values = ", ".join("(?)" for _ in plain_keys)
            rows = conn.execute(
                f"""
                WITH requested(word) AS (VALUES {values}),
                ranked AS (
                    SELECT
                        requested.word AS requested_word,
                        dictionary.*,
                        ROW_NUMBER() OVER (
                            PARTITION BY requested.word
                            ORDER BY dictionary.word COLLATE NOCASE
                        ) AS result_order
                    FROM requested
                    JOIN dmklinger_uk_en AS dictionary
                      ON replace(dictionary.word, char(0x301), '')
                         = requested.word COLLATE NOCASE
                )
                SELECT * FROM ranked
                WHERE result_order <= 1
                """,
                plain_keys,
            ).fetchall()
            by_plain: dict[str, list[dict]] = {key: [] for key in plain_keys}
            for row in rows:
                item = dict(row)
                plain = item.pop("requested_word")
                item.pop("result_order", None)
                by_plain.setdefault(plain, []).append(item)
            for original, plain in zip(chunk, plain_keys, strict=True):
                results[original] = list(by_plain.get(plain, []))
    except sqlite3.OperationalError:
        return results
    finally:
        _close_if_temporary(conn, db_path)

    return results


def search_esum_batch(
    words: list[str],
    *,
    db_path: str | Path | None = None,
) -> dict[str, list[dict]]:
    """Exact-lemma ЕСУМ meta hits for many words (no FTS body scan)."""
    requested = list(dict.fromkeys(str(word) for word in words if str(word).strip()))
    results: dict[str, list[dict]] = {word: [] for word in requested}
    if not requested:
        return results

    conn = None
    try:
        conn = _get_conn_for(db_path)
    except FileNotFoundError:
        return results

    try:
        if not _table_columns("esum_etymology_meta", db_path):
            return results
        for start in range(0, len(requested), 400):
            chunk = requested[start:start + 400]
            values = ", ".join("(?)" for _ in chunk)
            rows = conn.execute(
                f"""
                WITH requested(word) AS (VALUES {values}),
                ranked AS (
                    SELECT
                        requested.word AS requested_word,
                        meta.id,
                        meta.lemma,
                        meta.etymology_text,
                        meta.cognates,
                        meta.vol,
                        meta.page,
                        meta.source,
                        ROW_NUMBER() OVER (
                            PARTITION BY requested.word
                            ORDER BY meta.vol, meta.page, meta.lemma
                        ) AS result_order
                    FROM requested
                    JOIN esum_etymology_meta AS meta
                      ON meta.lemma = requested.word COLLATE NOCASE
                )
                SELECT * FROM ranked
                WHERE result_order <= 1
                """,
                chunk,
            ).fetchall()
            for row in rows:
                item = dict(row)
                requested_word = item.pop("requested_word")
                item.pop("result_order", None)
                results[requested_word].append(item)
    except sqlite3.OperationalError:
        return results
    finally:
        _close_if_temporary(conn, db_path)

    return results


def search_slovnyk_me_entries_batch(
    words: list[str],
    *,
    db_path: str | Path | None = None,
) -> dict[str, list[dict]]:
    """Exact ``normalized_word`` hits on curated slovnyk.me entries (batched).

    Missing table → empty hits (production sources.db may not ship the table).
    Overlap-blocked dictionaries are excluded, matching single-word search.
    """
    requested = list(dict.fromkeys(str(word) for word in words if str(word).strip()))
    results: dict[str, list[dict]] = {word: [] for word in requested}
    if not requested:
        return results

    conn = None
    try:
        conn = _get_conn_for(db_path)
    except FileNotFoundError:
        return results

    try:
        if not _table_columns("slovnyk_me_entries", db_path):
            return results
        blocked = tuple(slovnyk_me.OVERLAP_BLOCKED_DICTS)
        block_filter = ""
        block_params: list[object] = []
        if blocked:
            block_filter = (
                f" AND dictionary.dictionary_slug NOT IN "
                f"({','.join('?' for _ in blocked)})"
            )
            block_params = list(blocked)

        for start in range(0, len(requested), 400):
            chunk = requested[start:start + 400]
            normalized = [slovnyk_me.normalize_word(word) for word in chunk]
            # Map normalized form back to original request keys (first wins).
            originals_by_norm: dict[str, list[str]] = {}
            for original, norm in zip(chunk, normalized, strict=True):
                if not norm:
                    continue
                originals_by_norm.setdefault(norm, []).append(original)
            norms = list(originals_by_norm)
            if not norms:
                continue
            values = ", ".join("(?)" for _ in norms)
            rows = conn.execute(
                f"""
                WITH requested(word) AS (VALUES {values}),
                ranked AS (
                    SELECT
                        requested.word AS requested_word,
                        dictionary.*,
                        ROW_NUMBER() OVER (
                            PARTITION BY requested.word
                            ORDER BY dictionary.id
                        ) AS result_order
                    FROM requested
                    JOIN slovnyk_me_entries AS dictionary
                      ON dictionary.normalized_word = requested.word
                    WHERE 1=1{block_filter}
                )
                SELECT * FROM ranked
                WHERE result_order <= 1
                """,
                (*norms, *block_params),
            ).fetchall()
            by_norm: dict[str, list[dict]] = {norm: [] for norm in norms}
            for row in rows:
                item = dict(row)
                norm = item.pop("requested_word")
                item.pop("result_order", None)
                by_norm.setdefault(norm, []).append(
                    _normalize_slovnyk_row(item, norm)
                )
            for norm, originals in originals_by_norm.items():
                hits = by_norm.get(norm, [])
                for original in originals:
                    results[original] = list(hits)
    except sqlite3.OperationalError:
        return results
    finally:
        _close_if_temporary(conn, db_path)

    return results


def _strip_combining_acute(value: str) -> str:
    """Remove U+0301 combining acute from a dictionary headword or query."""
    return value.replace("\u0301", "")


def _escape_fts5_phrase(term: str) -> str:
    """Build a safe FTS5 phrase query for a user-supplied term."""
    cleaned = term.replace('"', " ").strip()
    if not cleaned:
        return ""
    return f'"{cleaned}"'


def _outside_loaded_esum_volume(query: str, volume: int | None) -> bool:
    """Avoid misleading body-text hits for headwords outside staged volumes."""
    if volume != 1:
        return False
    normalized = query.strip().lower()
    if not normalized or not normalized.replace("'", "").replace("’", "").isalpha():
        return False
    return not normalized.startswith(("а", "б", "в", "г", "ґ"))


def _single_loaded_esum_volume(conn: sqlite3.Connection) -> int | None:
    rows = conn.execute(
        "SELECT DISTINCT vol FROM esum_etymology_meta ORDER BY vol LIMIT 2"
    ).fetchall()
    if len(rows) == 1:
        return int(rows[0]["vol"])
    return None


def _goroh_override_for_esum(conn: sqlite3.Connection, lemma: str) -> dict[str, str] | None:
    if not garbled_esum_entry(lemma):
        return None
    try:
        row = conn.execute(
            """
            SELECT etymology_text, source_url
            FROM goroh_etymology
            WHERE requested_lemma = ? AND etymology_text != ''
            LIMIT 1
            """,
            (lemma,),
        ).fetchone()
    except sqlite3.OperationalError:
        return None
    if not row or not row["etymology_text"]:
        return None
    return {
        "etymology_text": trim_curated_goroh_text(row["etymology_text"], lemma),
        "source": "Горох (за ЕСУМ)",
        "source_url": row["source_url"],
    }


def _clean_garbled_esum_results(conn: sqlite3.Connection, rows: list[dict]) -> list[dict]:
    cleaned: list[dict] = []
    for row in rows:
        lemma = str(row.get("lemma") or "")
        if not garbled_esum_entry(lemma):
            if has_mojibake_marker(str(row.get("etymology_text") or "")):
                continue
            cleaned.append(row)
            continue
        item = dict(row)
        override = _goroh_override_for_esum(conn, lemma)
        if override:
            item.update(override)
        else:
            item["etymology_text"] = strip_garbled_tail(str(item.get("etymology_text") or ""), lemma)
            if has_mojibake_marker(str(item.get("etymology_text") or "")):
                continue
            item["source"] = f"{item.get('source') or 'ЕСУМ'} (garbled tail stripped)"
        cleaned.append(item)
    return cleaned


def search_esum(
    query: str,
    volume: int | None = None,
    limit: int = 5,
    *,
    db_path: str | Path | None = None,
) -> list[dict]:
    """Search ЕСУМ etymology entries.

    Exact lemma matches are returned first, followed by FTS5 body matches.
    Volume can be restricted for staged ingestion; #1662 loads volume 1 only.
    """
    conn = None
    try:
        conn = _get_conn_for(db_path)
    except FileNotFoundError:
        return []

    try:
        if not _table_columns("esum_etymology", db_path) or not _table_columns(
            "esum_etymology_meta", db_path
        ):
            return []
        loaded_volume = volume if volume is not None else _single_loaded_esum_volume(conn)
        if _outside_loaded_esum_volume(query, loaded_volume):
            return []

        limit = max(1, min(limit, 20))
        params: list[object] = [query]
        vol_filter = ""
        if volume is not None:
            vol_filter = " AND vol = ?"
            params.append(volume)

        exact_rows = conn.execute(
            f"""
            SELECT id AS rowid, lemma, etymology_text, cognates, vol, page, source
            FROM esum_etymology_meta
            WHERE lemma = ? COLLATE NOCASE{vol_filter}
            ORDER BY vol, page, lemma
            LIMIT ?
            """,
            (*params, limit),
        ).fetchall()

        results = [dict(row) for row in exact_rows]
        seen = {row["rowid"] for row in results}
        remaining = limit - len(results)
        fts_query = _escape_fts5_phrase(query)
        if remaining <= 0 or not fts_query:
            return _clean_garbled_esum_results(conn, results)

        fts_params: list[object] = [fts_query]
        fts_vol_filter = ""
        if volume is not None:
            fts_vol_filter = " AND vol = ?"
            fts_params.append(volume)
        fts_params.append(remaining + len(seen))

        fts_rows = conn.execute(
            f"""
            SELECT rowid, lemma, etymology_text, cognates, vol, page
            FROM esum_etymology
            WHERE esum_etymology MATCH ?{fts_vol_filter}
            ORDER BY rank
            LIMIT ?
            """,
            tuple(fts_params),
        ).fetchall()
        for row in fts_rows:
            item = dict(row)
            if item["rowid"] in seen:
                continue
            item["source"] = "ЕСУМ"
            results.append(item)
            if len(results) >= limit:
                break
        return _clean_garbled_esum_results(conn, results)
    finally:
        _close_if_temporary(conn, db_path)


def translate_en_uk(
    word: str,
    limit: int = 10,
    *,
    db_path: str | Path | None = None,
) -> list[dict]:
    """Look up English→Ukrainian translation in Балла."""
    return _dict_lookup("balla_en_uk", word, limit, db_path=db_path)


def search_idioms(word: str, limit: int = 10) -> list[dict]:
    """Look up idioms, preferring structured official DictUA results."""
    ulif_results = search_ulif_dictua_sections(word, "phraseology", limit=limit)
    fallback = _dict_lookup("frazeolohichnyi", word, limit)
    return (ulif_results + fallback)[:limit]


def search_synonyms(word: str, limit: int = 20) -> list[dict]:
    """Look up synonyms, preferring structured official DictUA results."""
    ulif_results = search_ulif_dictua_sections(word, "synonyms", limit=limit)
    try:
        conn = _get_conn()
    except FileNotFoundError:
        return ulif_results

    # Search in the 'words' field (comma-separated synset members)
    try:
        rows = conn.execute(
            "SELECT * FROM ukrajinet WHERE words LIKE ? COLLATE NOCASE LIMIT ?",
            (f"%{word}%", limit),
        ).fetchall()
    except sqlite3.OperationalError:
        return ulif_results
    return (ulif_results + [dict(r) for r in rows])[:limit]


def query_cefr_level(
    word: str,
    limit: int = 5,
    *,
    db_path: str | Path | None = None,
) -> list[dict]:
    """Look up CEFR level for a word in PULS vocabulary."""
    return _dict_lookup("puls_cefr", word, limit=limit, db_path=db_path)


def query_cefr_levels(
    words: list[str],
    *,
    db_path: str | Path | None = None,
) -> dict[str, list[dict]]:
    """Return the best PULS CEFR hit for each requested word in batched SQL."""
    return _batch_dict_lookup("puls_cefr", words, limit=1, db_path=db_path)


def search_style_guide(
    word: str,
    limit: int = 5,
    *,
    db_path: str | Path | None = None,
) -> list[dict]:
    """Look up calques/Russianisms in Антоненко-Давидович style guide."""
    return _dict_lookup("style_guide", word, limit, db_path=db_path)


def search_ua_gec_errors(
    query: str,
    *,
    tag_filter: list[str] | None = None,
    limit: int = 10,
    require_native_author: bool = False,
) -> list[dict]:
    """Look up russianisms/calques in UA-GEC corpus."""
    try:
        conn = _get_conn()
    except FileNotFoundError:
        return []

    # error_type exists in BOTH the FTS table (f) and the data table (m), so
    # every non-FTS predicate must carry its table alias — an unqualified
    # `error_type IN (...)` raises "ambiguous column name". Build each clause
    # already-qualified instead of prefixing the whole WHERE with `f.` (which
    # only attached to the first clause and left the rest ambiguous).
    where_clauses = ["f.ua_gec_errors_fts MATCH ?"]
    params = [query]

    if tag_filter:
        placeholders = ",".join("?" for _ in tag_filter)
        where_clauses.append(f"m.error_type IN ({placeholders})")
        params.extend(tag_filter)

    if require_native_author:
        where_clauses.append("m.is_native = 1")

    where_stmt = " AND ".join(where_clauses)

    sql = f"""
        SELECT m.error, m.correct, m.error_type, m.doc_id, m.is_native, m.source_lang
        FROM ua_gec_errors_fts f
        JOIN ua_gec_errors m ON f.rowid = m.id
        WHERE {where_stmt}
        ORDER BY f.rank
        LIMIT ?
    """
    params.append(limit)

    rows = conn.execute(sql, tuple(params)).fetchall()
    return [dict(r) for r in rows]


def _normalize_slovnyk_row(row: dict, query: str) -> dict:
    row = dict(row)
    row["is_modern"] = bool(row.get("is_modern"))
    row["is_dialect"] = bool(row.get("is_dialect"))
    row["is_russianism"] = bool(row.get("is_russianism"))
    row["sovietization_risk"] = int(row.get("sovietization_risk") or 0)
    row["score"] = float(row.get("score") or slovnyk_me.score_slovnyk_row(row, query))
    row.setdefault("source", "slovnyk.me")
    return row


def _resolved_slovnyk_dicts(dictionaries: list[str] | tuple[str, ...] | None) -> list[str]:
    if not dictionaries:
        return []
    resolved: list[str] = []
    for slug in dictionaries:
        canonical = slovnyk_me.resolve_dict_slug(slug)
        if canonical in slovnyk_me.OVERLAP_BLOCKED_DICTS:
            continue
        if canonical not in resolved:
            resolved.append(canonical)
    return resolved


def _search_slovnyk_me_db(
    query: str,
    *,
    limit: int,
    dictionaries: list[str] | tuple[str, ...] | None,
    db_path: str | Path | None = None,
) -> list[dict]:
    conn = None
    try:
        conn = _get_conn_for(db_path)
    except FileNotFoundError:
        return []
    try:
        if not _table_columns("slovnyk_me_entries", db_path):
            return []

        variants = slovnyk_me.query_variants(query)
        normalized_variants = [slovnyk_me.normalize_word(variant) for variant in variants]
        dicts = _resolved_slovnyk_dicts(dictionaries)

        dict_filter = ""
        dict_params: list[object] = []
        if dicts:
            dict_filter = f" AND dictionary_slug IN ({','.join('?' for _ in dicts)})"
            dict_params = [*dicts]
        elif dictionaries:
            return []
        else:
            blocked = tuple(slovnyk_me.OVERLAP_BLOCKED_DICTS)
            dict_filter = f" AND dictionary_slug NOT IN ({','.join('?' for _ in blocked)})"
            dict_params = [*blocked]

        seen_ids: set[int] = set()
        rows: list[dict] = []

        def add_fetched(fetched: list[sqlite3.Row]) -> None:
            for fetched_row in fetched:
                item = dict(fetched_row)
                row_id = int(item["id"])
                if row_id in seen_ids:
                    continue
                seen_ids.add(row_id)
                rows.append(_normalize_slovnyk_row(item, query))

        placeholders = ",".join("?" for _ in normalized_variants)
        exact = conn.execute(
            f"""
            SELECT *
            FROM slovnyk_me_entries
            WHERE normalized_word IN ({placeholders}){dict_filter}
            LIMIT ?
            """,
            (*normalized_variants, *dict_params, limit),
        ).fetchall()
        add_fetched(exact)

        if len(rows) < limit:
            prefix_where = " OR ".join("normalized_word LIKE ?" for _ in normalized_variants)
            prefix_params = [f"{variant}%" for variant in normalized_variants]
            prefix = conn.execute(
                f"""
                SELECT *
                FROM slovnyk_me_entries
                WHERE ({prefix_where}){dict_filter}
                LIMIT ?
                """,
                (*prefix_params, *dict_params, limit),
            ).fetchall()
            add_fetched(prefix)

        if len(rows) < limit and _table_columns("slovnyk_me_entries_fts", db_path):
            fts_query = _escape_fts5_phrase(query)
            if fts_query:
                try:
                    fts = conn.execute(
                        f"""
                        SELECT e.*, bm25(slovnyk_me_entries_fts) AS fts_rank
                        FROM slovnyk_me_entries_fts
                        JOIN slovnyk_me_entries e ON e.id = slovnyk_me_entries_fts.rowid
                        WHERE slovnyk_me_entries_fts MATCH ?{dict_filter}
                        ORDER BY fts_rank
                        LIMIT ?
                        """,
                        (fts_query, *dict_params, limit),
                    ).fetchall()
                    add_fetched(fts)
                except sqlite3.OperationalError:
                    pass

        rows.sort(key=lambda row: row["score"], reverse=True)
        return rows[:limit]
    finally:
        _close_if_temporary(conn, db_path)


def search_slovnyk_me(
    query: str,
    limit: int = 10,
    dictionaries: list[str] | tuple[str, ...] | None = None,
    *,
    live: bool = False,
    db_path: str | Path | None = None,
) -> list[dict]:
    """Search curated slovnyk.me rows, optionally falling back to live direct pages.

    `live=True` fetches only /dict/{slug}/{word} pages for the explicit query
    and known variants. It does not call slovnyk.me /search and does not crawl
    sitemaps.
    """
    limit = max(1, min(limit, 20))
    rows = _search_slovnyk_me_db(
        query,
        limit=limit,
        dictionaries=dictionaries,
        db_path=db_path,
    )
    if len(rows) >= limit or not live:
        return rows[:limit]

    live_rows = [
        _normalize_slovnyk_row(row, query)
        for row in slovnyk_me.fetch_entries(
            query,
            dictionaries=dictionaries,
            limit=limit - len(rows),
        )
    ]
    seen = {
        (row.get("dictionary_slug", ""), row.get("source_url", ""))
        for row in rows
    }
    for row in live_rows:
        key = (row.get("dictionary_slug", ""), row.get("source_url", ""))
        if key not in seen:
            seen.add(key)
            rows.append(row)
    rows.sort(key=lambda row: row["score"], reverse=True)
    return rows[:limit]


def _json_object(value: object) -> dict[str, object]:
    try:
        decoded = yaml.safe_load(str(value or "{}"))
    except yaml.YAMLError:
        return {}
    return decoded if isinstance(decoded, dict) else {}


def _json_string_list(value: object) -> list[str]:
    try:
        decoded = yaml.safe_load(str(value or "[]"))
    except yaml.YAMLError:
        return []
    return [str(item) for item in decoded] if isinstance(decoded, list) else []


def query_sum20(query: str, *, db_path: str | Path | None = None) -> list[dict]:
    """Return every exact-matching article from the offline official СУМ-20 collection.

    The collection is populated only by ``sum20_official_ingest.py``.  This
    reader deliberately has no live fallback, so its returned provenance is
    always the official stored ``wordid`` record.
    """
    normalized_lookup_key = normalize_sum20_lookup(query)
    if not normalized_lookup_key or not _table_columns("sum20_articles", db_path):
        return []
    conn = _get_conn_for(db_path)
    try:
        articles = conn.execute(
            """
            SELECT *
            FROM sum20_articles
            WHERE normalized_lookup_key = ?
            ORDER BY wordid
            """,
            (normalized_lookup_key,),
        ).fetchall()
        records: list[dict] = []
        for article in articles:
            article_id = int(article["id"])
            senses = [
                {
                    "sense_order": int(sense["sense_order"]),
                    "definition": str(sense["definition"]),
                    "register_labels": _json_string_list(sense["register_labels"]),
                }
                for sense in conn.execute(
                    """
                    SELECT sense_order, definition, register_labels
                    FROM sum20_senses
                    WHERE article_id = ?
                    ORDER BY sense_order
                    """,
                    (article_id,),
                ).fetchall()
            ]
            citations = [
                {
                    "sense_ref": int(citation["sense_ref"]),
                    "order": int(citation["order"]),
                    "citation_text": str(citation["citation_text"]),
                    "parsed_bib_fields": _json_object(citation["parsed_bib_fields"]),
                }
                for citation in conn.execute(
                    """
                    SELECT sense_ref, "order", citation_text, parsed_bib_fields
                    FROM sum20_citations
                    WHERE article_id = ?
                    ORDER BY "order"
                    """,
                    (article_id,),
                ).fetchall()
            ]
            records.append(
                {
                    "source_id": SUM20_SOURCE_ID,
                    "source_record_id": str(article["wordid"]),
                    "headword": str(article["headword"]),
                    "stressed_headword": str(article["stressed_headword"]),
                    "pos": str(article["pos"]),
                    "grammar": str(article["grammar"]),
                    "article_text": str(article["article_text"]),
                    "senses": senses,
                    "citations": citations,
                    "official_url": str(article["official_url"]),
                    "retrieved_at": str(article["fetched_at"]),
                    "content_sha256": str(article["content_sha256"]),
                    "parser_version": str(article["parser_version"] or SUM20_PARSER_VERSION),
                    "status": "ok",
                    "attribution_label": SUM20_ATTRIBUTION_LABEL,
                }
            )
        return records
    finally:
        _close_if_temporary(conn, db_path)


def _heritage_text(hit: dict) -> str:
    return str(
        hit.get("definition")
        or hit.get("etymology_text")
        or hit.get("snippet")
        or hit.get("text")
        or ""
    )


def search_heritage(
    query: str,
    limit: int = 10,
    *,
    include_live_slovnyk: bool = False,
    db_path: str | Path | None = None,
) -> list[dict]:
    """Merge heritage-defense evidence for a Ukrainian headword.

    Sources are deliberately kept separate: this calls the existing
    Грінченко, ЕСУМ, slovnyk.me, and style-guide lookup functions rather
    than re-ingesting those dictionaries into a combined table.
    """
    limit = max(1, min(limit, 20))
    rows: list[dict] = []

    for hit in search_grinchenko_1907(query, limit=5, db_path=db_path):
        text = _heritage_text(hit)
        rows.append({
            "query": query,
            "source_family": "grinchenko",
            "source": hit.get("source", "Грінченко"),
            "word": hit.get("word", ""),
            "text": text,
            "classification": "pre_soviet_ukrainian_attestation",
            "is_authentic_ukrainian": True,
            "is_russianism": False,
            "is_modern": False,
            "is_dialect": "діал" in text.lower(),
            "sovietization_risk": 0,
            "evidence_tags": ["pre_soviet", "lexicographic"],
            "score": 96.0,
        })

    for hit in search_esum(query, limit=5, db_path=db_path):
        text = _heritage_text(hit)
        cognates = str(hit.get("cognates", ""))
        tags = ["etymology"]
        score = 92.0
        if "псл" in text.lower() or "псл" in cognates.lower():
            tags.append("proto_slavic")
            score += 5.0
        rows.append({
            "query": query,
            "source_family": "esum",
            "source": hit.get("source", "ЕСУМ"),
            "word": hit.get("lemma", ""),
            "text": text,
            "classification": "etymological_attestation",
            "is_authentic_ukrainian": True,
            "is_russianism": False,
            "is_modern": False,
            "is_dialect": False,
            "sovietization_risk": 0,
            "evidence_tags": tags,
            "score": score,
        })

    for hit in search_slovnyk_me(
        query,
        limit=limit,
        dictionaries=slovnyk_me.HERITAGE_SLOVNYK_ME_DICTS,
        live=include_live_slovnyk,
        db_path=db_path,
    ):
        is_russianism = bool(hit.get("is_russianism"))
        is_dialect = bool(hit.get("is_dialect"))
        is_modern = bool(hit.get("is_modern"))
        if is_russianism:
            classification = "potential_russianism_or_calque"
            score = 25.0
        elif is_dialect:
            classification = "regional_or_historical_ukrainian_attestation"
            score = 88.0
        elif is_modern:
            classification = "modern_ukrainian_attestation"
            score = 82.0
        else:
            classification = "dictionary_attestation"
            score = 72.0
        score -= 5.0 * int(hit.get("sovietization_risk") or 0)
        rows.append({
            "query": query,
            "source_family": "slovnyk_me",
            "source": hit.get("dictionary_label", "slovnyk.me"),
            "word": hit.get("word", ""),
            "text": _heritage_text(hit),
            "url": hit.get("source_url", ""),
            "classification": classification,
            "is_authentic_ukrainian": not is_russianism,
            "is_russianism": is_russianism,
            "is_modern": is_modern,
            "is_dialect": is_dialect,
            "sovietization_risk": int(hit.get("sovietization_risk") or 0),
            "sovietization_keywords": hit.get("sovietization_keywords", ""),
            "evidence_tags": [tag for tag, present in {
                "modern": is_modern,
                "regional_or_historical": is_dialect,
                "possible_russianism": is_russianism,
                "slovnyk_me": True,
            }.items() if present],
            "score": score,
        })

    for hit in search_style_guide(query, limit=3, db_path=db_path):
        rows.append({
            "query": query,
            "source_family": "style_guide",
            "source": hit.get("source", "Антоненко-Давидович"),
            "word": hit.get("word", ""),
            "text": _heritage_text(hit),
            "classification": "potential_russianism_or_calque",
            "is_authentic_ukrainian": False,
            "is_russianism": True,
            "is_modern": False,
            "is_dialect": False,
            "sovietization_risk": 0,
            "evidence_tags": ["style_warning", "possible_russianism"],
            "score": 20.0,
        })

    rows.sort(key=lambda row: row["score"], reverse=True)
    return rows[:limit]


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
