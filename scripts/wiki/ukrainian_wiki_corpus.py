"""Schema, gating, and ingestion helpers for the ``ukrainian_wiki`` corpus."""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
import statistics
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

from audit.checks.cross_file_integrity import extract_ukrainian_words
from audit.checks.russicism_detection import check_russicisms
from rag.rag_batch_verify import vesum_batch_lookup
from rag.source_query import pravopys_lookup

from .config import PROJECT_ROOT
from .embedding_manifest import DEFAULT_MANIFEST_DB, EmbeddingManifest, reserve_corpus_shard
from .quality_gate import _check_citation_registry
from .sources_db import search_style_guide

DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "sources.db"
DEFAULT_REPORT_PATH = PROJECT_ROOT / "data" / "corpus_audit" / "ukrainian_wiki_a1_ingest_report.md"
DEFAULT_MIN_WORDS = 40
DEFAULT_MAX_CHARS = 900
DEFAULT_CHUNK_MIN_CHARS = 50
DEFAULT_VESUM_MIN_COVERAGE = 0.80
UKRAINIAN_WIKI_CORPUS = "ukrainian_wiki"
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")
_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
_HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
_YAML_FRONTMATTER_RE = re.compile(r"\A---\n.*?\n---\n?", re.DOTALL)
_CYRILLIC_RE = re.compile(r"[\u0400-\u04FF]")
_NON_PROSE_PREFIXES = ("|", ">", "-", "*", "1. ", "2. ", "3. ")
_DEFAULT_PRAVOPYS_TERMS = (
    "апостроф",
    "м'який знак",
    "м’який знак",
    "наголос",
    "правопис",
    "літера",
    "буква",
    "голосний",
    "приголосний",
)
_QUOTE_TERM_RE = re.compile(r"'([^']+)'")
UKRAINIAN_WIKI_COLUMN_SPECS = (
    ("track", "TEXT NOT NULL DEFAULT ''"),
    ("heading_path", "TEXT NOT NULL DEFAULT ''"),
    ("chunk_index", "INTEGER NOT NULL DEFAULT 0"),
)

UKRAINIAN_WIKI_SCHEMA = """
CREATE TABLE IF NOT EXISTS ukrainian_wiki (
    id INTEGER PRIMARY KEY,
    passage_id TEXT NOT NULL UNIQUE,
    article_slug TEXT NOT NULL,
    article_title TEXT NOT NULL DEFAULT '',
    article_path TEXT NOT NULL DEFAULT '',
    track TEXT NOT NULL DEFAULT '',
    heading_path TEXT NOT NULL DEFAULT '',
    section_path TEXT NOT NULL DEFAULT '',
    chunk_index INTEGER NOT NULL DEFAULT 0,
    paragraph_start INTEGER NOT NULL DEFAULT 0,
    paragraph_end INTEGER NOT NULL DEFAULT 0,
    word_count INTEGER NOT NULL DEFAULT 0,
    char_count INTEGER NOT NULL DEFAULT 0,
    text TEXT NOT NULL DEFAULT '',
    source_registry_path TEXT NOT NULL DEFAULT '',
    gate_report_json TEXT NOT NULL DEFAULT '',
    inserted_at TEXT NOT NULL DEFAULT ''
);
CREATE VIRTUAL TABLE IF NOT EXISTS ukrainian_wiki_fts USING fts5(
    article_title, section_path, text,
    content='ukrainian_wiki',
    content_rowid='id',
    tokenize='unicode61'
);
CREATE TRIGGER IF NOT EXISTS ukrainian_wiki_ai AFTER INSERT ON ukrainian_wiki BEGIN
    INSERT INTO ukrainian_wiki_fts(rowid, article_title, section_path, text)
    VALUES (new.id, new.article_title, new.section_path, new.text);
END;
CREATE TRIGGER IF NOT EXISTS ukrainian_wiki_ad AFTER DELETE ON ukrainian_wiki BEGIN
    INSERT INTO ukrainian_wiki_fts(ukrainian_wiki_fts, rowid, article_title, section_path, text)
    VALUES ('delete', old.id, old.article_title, old.section_path, old.text);
END;
CREATE TRIGGER IF NOT EXISTS ukrainian_wiki_au AFTER UPDATE ON ukrainian_wiki BEGIN
    INSERT INTO ukrainian_wiki_fts(ukrainian_wiki_fts, rowid, article_title, section_path, text)
    VALUES ('delete', old.id, old.article_title, old.section_path, old.text);
    INSERT INTO ukrainian_wiki_fts(rowid, article_title, section_path, text)
    VALUES (new.id, new.article_title, new.section_path, new.text);
END;
CREATE INDEX IF NOT EXISTS idx_ukrainian_wiki_slug ON ukrainian_wiki(article_slug);
CREATE INDEX IF NOT EXISTS idx_ukrainian_wiki_section ON ukrainian_wiki(article_slug, paragraph_start);
""".strip()


@dataclass(frozen=True)
class Passage:
    passage_id: str
    article_slug: str
    article_title: str
    article_path: str
    track: str
    heading_path: str
    section_path: str
    chunk_index: int
    paragraph_start: int
    paragraph_end: int
    word_count: int
    char_count: int
    text: str
    source_registry_path: str


@dataclass(frozen=True)
class GateResult:
    name: str
    passed: bool
    detail: str
    metadata: dict[str, object]


@dataclass(frozen=True)
class AdmissionReport:
    passed: bool
    results: list[GateResult]

    def to_payload(self) -> dict[str, object]:
        return {
            "passed": self.passed,
            "results": [
                {
                    **asdict(result),
                    "metadata": dict(result.metadata),
                }
                for result in self.results
            ],
        }

    def to_json(self) -> str:
        return json.dumps(self.to_payload(), ensure_ascii=False, sort_keys=True)


@dataclass(frozen=True)
class SkippedPassage:
    passage_id: str
    chunk_index: int
    detail: str
    gate_report: AdmissionReport


@dataclass(frozen=True)
class ArticleIngestResult:
    article_slug: str
    article_title: str
    article_path: str
    track: str
    segmented_chunks: int
    inserted_chunks: int
    skipped_chunks: int
    skipped_passages: list[SkippedPassage]
    failure: str | None = None


@dataclass(frozen=True)
class SmokeQueryMatch:
    rank: int
    article_slug: str
    article_title: str
    track: str
    section_path: str
    source_file: str
    excerpt: str
    final_score: float


@dataclass(frozen=True)
class SmokeQueryResult:
    query: str
    matches: list[SmokeQueryMatch]


def ensure_ukrainian_wiki_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(UKRAINIAN_WIKI_SCHEMA)
    existing = {
        row[1]
        for row in conn.execute("PRAGMA table_info(ukrainian_wiki)").fetchall()
    }
    for column, ddl in UKRAINIAN_WIKI_COLUMN_SPECS:
        if column in existing:
            continue
        conn.execute(f"ALTER TABLE ukrainian_wiki ADD COLUMN {column} {ddl}")


def ensure_ukrainian_wiki_manifest(manifest_db: Path = DEFAULT_MANIFEST_DB) -> int:
    manifest = EmbeddingManifest(manifest_db)
    try:
        return reserve_corpus_shard(manifest, corpus=UKRAINIAN_WIKI_CORPUS)
    finally:
        manifest.close()


def migrate_ukrainian_wiki_corpus(
    *,
    db_path: Path = DEFAULT_DB_PATH,
    manifest_db: Path = DEFAULT_MANIFEST_DB,
) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    try:
        ensure_ukrainian_wiki_schema(conn)
        conn.commit()
    finally:
        conn.close()
    ensure_ukrainian_wiki_manifest(manifest_db)


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _relative_or_absolute(path: Path) -> str:
    try:
        return path.resolve().relative_to(PROJECT_ROOT.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def _strip_non_prose(article_text: str) -> str:
    stripped = _YAML_FRONTMATTER_RE.sub("", article_text, count=1)
    return _HTML_COMMENT_RE.sub("", stripped)


def _section_path(headings: list[str]) -> str:
    return " > ".join(headings)


def _infer_article_title(path: Path, headings: list[str]) -> str:
    if headings:
        return headings[0]
    return path.stem.replace("-", " ").title()


def _infer_track(article_path: Path) -> str:
    return article_path.parent.name.strip().lower() or "a1"


def _report_title(article_root: Path | None, results: list[ArticleIngestResult]) -> str:
    if article_root is not None:
        track = article_root.name.strip().lower()
        if track:
            return f"Ukrainian Wiki {track.upper()} Ingest Report"

    tracks = sorted({result.track for result in results if result.track})
    if len(tracks) == 1:
        return f"Ukrainian Wiki {tracks[0].upper()} Ingest Report"
    return "Ukrainian Wiki Ingest Report"


def _split_overlong_passage(text: str, *, max_chars: int) -> list[str]:
    if len(text) <= max_chars:
        return [text]

    sentences = [sentence.strip() for sentence in _SENTENCE_SPLIT_RE.split(text) if sentence.strip()]
    if len(sentences) <= 1:
        return [text[index:index + max_chars].strip() for index in range(0, len(text), max_chars)]

    chunks: list[str] = []
    current: list[str] = []
    current_len = 0
    for sentence in sentences:
        projected = current_len + len(sentence) + (1 if current else 0)
        if current and projected > max_chars:
            chunks.append(" ".join(current).strip())
            current = [sentence]
            current_len = len(sentence)
            continue
        current.append(sentence)
        current_len = projected
    if current:
        chunks.append(" ".join(current).strip())
    return [chunk for chunk in chunks if chunk]


def segment_article_passages(
    article_path: Path,
    *,
    track: str | None = None,
    min_words: int = DEFAULT_MIN_WORDS,
    max_chars: int = DEFAULT_MAX_CHARS,
) -> list[Passage]:
    raw_text = article_path.read_text(encoding="utf-8")
    article_text = _strip_non_prose(raw_text)
    article_slug = article_path.stem
    article_rel = _relative_or_absolute(article_path)
    registry_rel = _relative_or_absolute(article_path.with_suffix(".sources.yaml"))
    article_track = track or _infer_track(article_path)

    headings: list[str] = []
    paragraphs: list[tuple[int, str, str]] = []
    paragraph_lines: list[str] = []
    paragraph_index = 0
    in_code_fence = False

    def flush_paragraph() -> None:
        nonlocal paragraph_lines, paragraph_index
        if not paragraph_lines:
            return
        paragraph_text = " ".join(line.strip() for line in paragraph_lines if line.strip()).strip()
        paragraph_lines = []
        if not paragraph_text:
            return
        paragraph_index += 1
        paragraphs.append((paragraph_index, _section_path(headings), paragraph_text))

    for line in article_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code_fence = not in_code_fence
            flush_paragraph()
            continue
        if in_code_fence:
            continue
        heading_match = _HEADING_RE.match(stripped)
        if heading_match:
            flush_paragraph()
            level = len(heading_match.group(1))
            title = heading_match.group(2).strip()
            if len(headings) >= level:
                headings[:] = headings[:level - 1]
            headings.append(title)
            continue
        if not stripped:
            flush_paragraph()
            continue
        if stripped.startswith(_NON_PROSE_PREFIXES) or stripped.startswith("!["):
            flush_paragraph()
            continue
        paragraph_lines.append(stripped)
    flush_paragraph()

    article_title = _infer_article_title(article_path, headings[:1])
    passages: list[Passage] = []
    chunk_index = 0
    pointer = 0
    while pointer < len(paragraphs):
        start_idx, section_path, text = paragraphs[pointer]
        end_idx = start_idx
        current_text = text
        current_words = len(current_text.split())

        while (
            current_words < min_words
            and pointer + 1 < len(paragraphs)
            and paragraphs[pointer + 1][1] == section_path
        ):
            next_idx, _, next_text = paragraphs[pointer + 1]
            merged = f"{current_text}\n\n{next_text}"
            if len(merged) > max_chars:
                break
            pointer += 1
            current_text = merged
            end_idx = next_idx
            current_words = len(current_text.split())

        for split_index, chunk in enumerate(_split_overlong_passage(current_text, max_chars=max_chars), start=1):
            chunk_text = chunk.strip()
            if not chunk_text:
                continue
            suffix = "" if split_index == 1 else f"-s{split_index}"
            chunk_index += 1
            passages.append(
                Passage(
                    passage_id=f"{article_slug}:p{start_idx}-{end_idx}{suffix}",
                    article_slug=article_slug,
                    article_title=article_title,
                    article_path=article_rel,
                    track=article_track,
                    heading_path=section_path,
                    section_path=section_path,
                    chunk_index=chunk_index,
                    paragraph_start=start_idx,
                    paragraph_end=end_idx,
                    word_count=len(chunk_text.split()),
                    char_count=len(chunk_text),
                    text=chunk_text,
                    source_registry_path=registry_rel,
                )
            )
        pointer += 1
    return passages


def _chunk_utf8_gate(text: str) -> GateResult:
    try:
        encoded = text.encode("utf-8")
    except UnicodeEncodeError as exc:
        return GateResult(
            name="utf8",
            passed=False,
            detail=str(exc),
            metadata={},
        )
    return GateResult(
        name="utf8",
        passed=True,
        detail="valid UTF-8",
        metadata={"bytes": len(encoded)},
    )


def _chunk_length_gate(text: str, *, min_chars: int) -> GateResult:
    normalized = text.strip()
    char_count = len(normalized)
    passed = bool(normalized) and char_count >= min_chars
    detail = f"{char_count} chars" if passed else f"{char_count} chars < {min_chars}"
    return GateResult(
        name="min_length",
        passed=passed,
        detail=detail,
        metadata={"char_count": char_count, "min_chars": min_chars},
    )


def _chunk_cyrillic_gate(text: str) -> GateResult:
    matches = _CYRILLIC_RE.findall(text)
    return GateResult(
        name="cyrillic",
        passed=bool(matches),
        detail="contains Cyrillic content" if matches else "no Cyrillic codepoints detected",
        metadata={"cyrillic_chars": len(matches)},
    )


def run_chunk_admission_gates(
    text: str,
    *,
    min_chars: int = DEFAULT_CHUNK_MIN_CHARS,
) -> AdmissionReport:
    results = [
        _chunk_utf8_gate(text),
        _chunk_length_gate(text, min_chars=min_chars),
        _chunk_cyrillic_gate(text),
    ]
    return AdmissionReport(passed=all(result.passed for result in results), results=results)


def _vesum_gate(article_text: str, *, min_coverage: float) -> GateResult:
    words = sorted(extract_ukrainian_words(article_text))
    if not words:
        return GateResult(
            name="vesum",
            passed=False,
            detail="no Ukrainian word forms extracted",
            metadata={"total_words": 0, "coverage": 0.0},
        )

    results = vesum_batch_lookup(words)
    hits = sum(1 for word in words if results.get(word))
    coverage = hits / len(words)
    missing = [word for word in words if not results.get(word)]
    return GateResult(
        name="vesum",
        passed=coverage >= min_coverage,
        detail=f"coverage {coverage:.2%} ({hits}/{len(words)})",
        metadata={
            "total_words": len(words),
            "vesum_hits": hits,
            "coverage": round(coverage, 4),
            "missing_words": missing[:20],
        },
    )


def _citation_gate(article_path: Path, article_text: str) -> GateResult:
    issues = _check_citation_registry(article_path, article_text)
    return GateResult(
        name="citation_audit",
        passed=not issues,
        detail="citation registry clean" if not issues else f"{len(issues)} citation issue(s)",
        metadata={"issues": issues},
    )


def _surzhyk_gate(article_text: str, article_path: Path) -> GateResult:
    violations = check_russicisms(article_text, str(article_path))
    return GateResult(
        name="surzhyk_linter",
        passed=not violations,
        detail="no russicism/surzhyk findings" if not violations else violations[0]["issue"],
        metadata={"violations": violations},
    )


def _derive_pravopys_terms(article_text: str, article_title: str, headings: list[str]) -> list[str]:
    haystack = "\n".join([article_title, *headings, article_text[:1200]]).lower()
    return [term for term in _DEFAULT_PRAVOPYS_TERMS if term in haystack]


def _pravopys_gate(article_text: str, article_title: str, headings: list[str]) -> GateResult:
    terms = _derive_pravopys_terms(article_text, article_title, headings)
    if not terms:
        return GateResult(
            name="pravopys_2019",
            passed=True,
            detail="no orthography-sensitive terms detected",
            metadata={"terms": [], "matches": []},
        )

    matches: list[str] = []
    for term in terms:
        result = pravopys_lookup(term)
        if result:
            matches.append(term)
    return GateResult(
        name="pravopys_2019",
        passed=bool(matches),
        detail="matched Pravopys guidance" if matches else "no Pravopys evidence for derived terms",
        metadata={"terms": terms, "matches": matches},
    )


def _antonenko_gate(surzhyk_result: GateResult) -> GateResult:
    suspect_terms = [
        term
        for violation in surzhyk_result.metadata.get("violations", [])
        for term in _QUOTE_TERM_RE.findall(str(violation.get("issue", "")))
    ]
    if not suspect_terms:
        return GateResult(
            name="antonenko_davydovych",
            passed=True,
            detail="no suspect terms to validate",
            metadata={"terms": [], "hits": {}},
        )

    hits: dict[str, int] = {}
    for term in suspect_terms:
        rows = search_style_guide(term)
        if rows:
            hits[term] = len(rows)
    return GateResult(
        name="antonenko_davydovych",
        passed=bool(hits),
        detail="style-guide evidence found" if hits else "suspect terms absent from style guide",
        metadata={"terms": suspect_terms, "hits": hits},
    )


def run_admission_gates(
    article_path: Path,
    *,
    min_vesum_coverage: float = DEFAULT_VESUM_MIN_COVERAGE,
) -> AdmissionReport:
    article_text = article_path.read_text(encoding="utf-8")
    stripped_text = _strip_non_prose(article_text)
    headings = [
        match.group(2).strip()
        for match in _HEADING_RE.finditer(stripped_text)
    ]
    article_title = headings[0] if headings else article_path.stem.replace("-", " ").title()

    citation = _citation_gate(article_path, article_text)
    vesum = _vesum_gate(stripped_text, min_coverage=min_vesum_coverage)
    surzhyk = _surzhyk_gate(stripped_text, article_path)
    pravopys = _pravopys_gate(stripped_text, article_title, headings[:3])
    antonenko = _antonenko_gate(surzhyk)
    results = [citation, vesum, surzhyk, pravopys, antonenko]
    return AdmissionReport(passed=all(result.passed for result in results), results=results)


def _serialize_gate_report(
    *,
    chunk_report: AdmissionReport,
    article_report: AdmissionReport | None = None,
) -> str:
    payload = {
        "passed": chunk_report.passed and (article_report.passed if article_report else True),
        "chunk": chunk_report.to_payload(),
    }
    if article_report is not None:
        payload["article"] = article_report.to_payload()
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)


def _build_insert_payload(
    passages: list[Passage],
    *,
    article_report: AdmissionReport | None = None,
    min_chunk_chars: int = DEFAULT_CHUNK_MIN_CHARS,
) -> tuple[list[tuple], list[SkippedPassage]]:
    payload: list[tuple] = []
    skipped: list[SkippedPassage] = []

    for passage in passages:
        chunk_report = run_chunk_admission_gates(passage.text, min_chars=min_chunk_chars)
        if not chunk_report.passed:
            skipped.append(
                SkippedPassage(
                    passage_id=passage.passage_id,
                    chunk_index=passage.chunk_index,
                    detail="; ".join(result.detail for result in chunk_report.results if not result.passed),
                    gate_report=chunk_report,
                )
            )
            continue
        payload.append(
            (
                passage.passage_id,
                passage.article_slug,
                passage.article_title,
                passage.article_path,
                passage.track,
                passage.heading_path,
                passage.section_path,
                passage.chunk_index,
                passage.paragraph_start,
                passage.paragraph_end,
                passage.word_count,
                passage.char_count,
                passage.text,
                passage.source_registry_path,
                _serialize_gate_report(chunk_report=chunk_report, article_report=article_report),
                _utc_now(),
            )
        )
    return payload, skipped


def _write_passages(
    conn: sqlite3.Connection,
    *,
    article_slug: str,
    payload: list[tuple],
) -> None:
    ensure_ukrainian_wiki_schema(conn)
    conn.execute("BEGIN")
    try:
        conn.execute(
            "DELETE FROM ukrainian_wiki WHERE article_slug = ?",
            (article_slug,),
        )
        if payload:
            conn.executemany(
                """
                INSERT INTO ukrainian_wiki (
                    passage_id, article_slug, article_title, article_path, track, heading_path, section_path,
                    chunk_index, paragraph_start, paragraph_end, word_count, char_count, text,
                    source_registry_path, gate_report_json, inserted_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                payload,
            )
        conn.commit()
    except Exception:
        conn.rollback()
        raise


def ingest_article(
    article_path: Path,
    *,
    db_path: Path = DEFAULT_DB_PATH,
    manifest_db: Path = DEFAULT_MANIFEST_DB,
    min_words: int = DEFAULT_MIN_WORDS,
    max_chars: int = DEFAULT_MAX_CHARS,
    min_chunk_chars: int = DEFAULT_CHUNK_MIN_CHARS,
    min_vesum_coverage: float = DEFAULT_VESUM_MIN_COVERAGE,
) -> tuple[AdmissionReport, int]:
    migrate_ukrainian_wiki_corpus(db_path=db_path, manifest_db=manifest_db)
    report = run_admission_gates(article_path, min_vesum_coverage=min_vesum_coverage)
    if not report.passed:
        return report, 0

    passages = segment_article_passages(article_path, min_words=min_words, max_chars=max_chars)
    payload, _ = _build_insert_payload(
        passages,
        article_report=report,
        min_chunk_chars=min_chunk_chars,
    )

    conn = sqlite3.connect(str(db_path))
    try:
        _write_passages(conn, article_slug=article_path.stem, payload=payload)
    finally:
        conn.close()
    return report, len(payload)


def _collect_article_paths(path: Path) -> list[Path]:
    if path.is_file():
        return [path]
    return sorted(candidate for candidate in path.glob("*.md") if candidate.is_file())


def _suspicious_thresholds(chunk_counts: list[int]) -> tuple[float, float]:
    if len(chunk_counts) < 4:
        return 0.0, float("inf")
    quartiles = statistics.quantiles(sorted(chunk_counts), n=4, method="inclusive")
    q1 = quartiles[0]
    q3 = quartiles[2]
    iqr = q3 - q1
    if iqr == 0:
        return max(0.0, q1 - 1.0), q3 + 1.0
    return max(0.0, q1 - 1.5 * iqr), q3 + 1.5 * iqr


def run_smoke_queries(
    queries: list[str],
    *,
    track: str,
    limit: int = 5,
    db_path: Path = DEFAULT_DB_PATH,
) -> list[SmokeQueryResult]:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    smoke_results: list[SmokeQueryResult] = []
    try:
        for query in queries:
            phrase = query.replace('"', " ").strip()
            rows = conn.execute(
                """
                SELECT
                    s.article_slug,
                    s.article_title,
                    s.track,
                    s.section_path,
                    s.article_path,
                    s.text,
                    bm25(ukrainian_wiki_fts, 5.0, 2.0, 1.0) AS rank
                FROM ukrainian_wiki_fts
                JOIN ukrainian_wiki s ON s.id = ukrainian_wiki_fts.rowid
                WHERE ukrainian_wiki_fts MATCH ?
                  AND s.track = ?
                ORDER BY rank
                LIMIT ?
                """,
                (f'"{phrase}"', track, limit),
            ).fetchall()
            smoke_results.append(
                SmokeQueryResult(
                    query=query,
                    matches=[
                        SmokeQueryMatch(
                            rank=index,
                            article_slug=str(row["article_slug"] or ""),
                            article_title=str(row["article_title"] or ""),
                            track=str(row["track"] or ""),
                            section_path=str(row["section_path"] or ""),
                            source_file=str(row["article_path"] or ""),
                            excerpt=" ".join(str(row["text"] or "").split())[:220].strip(),
                            final_score=float(row["rank"] or 0.0),
                        )
                        for index, row in enumerate(rows, start=1)
                    ],
                )
            )
    finally:
        conn.close()
    return smoke_results


def write_ingest_report(
    results: list[ArticleIngestResult],
    *,
    report_path: Path = DEFAULT_REPORT_PATH,
    article_root: Path | None = None,
    smoke_queries: list[SmokeQueryResult] | None = None,
) -> Path:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    completed = [result for result in results if result.failure is None]
    inserted_counts = [result.inserted_chunks for result in completed]
    low_threshold, high_threshold = _suspicious_thresholds(inserted_counts)
    suspicious_low = {
        result.article_slug
        for result in completed
        if result.inserted_chunks < low_threshold
    }
    suspicious_high = {
        result.article_slug
        for result in completed
        if result.inserted_chunks > high_threshold
    }

    total_segmented = sum(result.segmented_chunks for result in results)
    total_inserted = sum(result.inserted_chunks for result in results)
    total_skipped = sum(result.skipped_chunks for result in results)
    failures = [result for result in results if result.failure is not None]

    lines = [
        f"# {_report_title(article_root, results)}",
        "",
        f"- Generated: {_utc_now()}",
        f"- Source root: {_relative_or_absolute(article_root) if article_root else 'n/a'}",
        f"- Articles scanned: {len(results)}",
        f"- Articles ingested: {len(completed)}",
        f"- Articles failed: {len(failures)}",
        f"- Total segmented chunks: {total_segmented}",
        f"- Total chunks ingested: {total_inserted}",
        f"- Total chunks skipped by admission gate: {total_skipped}",
        "",
        "## Suspicious Chunk Counts",
        "",
        f"- Low threshold: `< {low_threshold:.2f}` chunk(s)",
        f"- High threshold: `> {high_threshold:.2f}` chunk(s)",
        f"- Suspiciously low articles: {', '.join(sorted(suspicious_low)) if suspicious_low else 'none'}",
        f"- Suspiciously high articles: {', '.join(sorted(suspicious_high)) if suspicious_high else 'none'}",
        "",
        "## Per-Article Chunk Counts",
        "",
        "| Article | Track | Inserted | Segmented | Skipped | Notes |",
        "| --- | --- | ---: | ---: | ---: | --- |",
    ]

    for result in sorted(results, key=lambda item: item.article_slug):
        notes: list[str] = []
        if result.failure:
            notes.append(f"ERROR: {result.failure}")
        if result.article_slug in suspicious_low:
            notes.append("suspiciously low")
        if result.article_slug in suspicious_high:
            notes.append("suspiciously high")
        if result.skipped_chunks:
            notes.append(f"{result.skipped_chunks} gate-skipped chunk(s)")
        lines.append(
            f"| `{result.article_slug}` | `{result.track}` | {result.inserted_chunks} | "
            f"{result.segmented_chunks} | {result.skipped_chunks} | {'; '.join(notes) or 'ok'} |"
        )

    skipped_rows = [
        (result.article_slug, skipped)
        for result in sorted(results, key=lambda item: item.article_slug)
        for skipped in result.skipped_passages
    ]
    if skipped_rows:
        lines.extend(
            [
                "",
                "## Skipped Chunks",
                "",
                "| Article | Passage | Chunk Index | Reason |",
                "| --- | --- | ---: | --- |",
            ]
        )
        for article_slug, skipped in skipped_rows:
            lines.append(
                f"| `{article_slug}` | `{skipped.passage_id}` | {skipped.chunk_index} | {skipped.detail} |"
            )

    if failures:
        lines.extend(["", "## Failures", ""])
        for result in failures:
            lines.append(f"- `{result.article_slug}`: {result.failure}")

    if smoke_queries:
        lines.extend(["", "## Smoke Queries", ""])
        for smoke in smoke_queries:
            lines.append(f"### `{smoke.query}`")
            lines.append("")
            if not smoke.matches:
                lines.append("- No `ukrainian_wiki` matches returned.")
                lines.append("")
                continue
            lines.append("| Rank | Article | Track | Section | Score | Source | Excerpt |")
            lines.append("| ---: | --- | --- | --- | ---: | --- | --- |")
            for match in smoke.matches:
                section = match.section_path or "root"
                lines.append(
                    f"| {match.rank} | `{match.article_slug}` ({match.article_title}) | "
                    f"`{match.track or 'unknown'}` | `{section}` | {match.final_score:.4f} | "
                    f"`{match.source_file}` | {match.excerpt} |"
                )
            lines.append("")

    report_path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")
    return report_path


def ingest_articles(
    article_root: Path,
    *,
    db_path: Path = DEFAULT_DB_PATH,
    manifest_db: Path = DEFAULT_MANIFEST_DB,
    report_path: Path = DEFAULT_REPORT_PATH,
    min_words: int = DEFAULT_MIN_WORDS,
    max_chars: int = DEFAULT_MAX_CHARS,
    min_chunk_chars: int = DEFAULT_CHUNK_MIN_CHARS,
) -> list[ArticleIngestResult]:
    migrate_ukrainian_wiki_corpus(db_path=db_path, manifest_db=manifest_db)
    article_paths = _collect_article_paths(article_root)
    conn = sqlite3.connect(str(db_path))
    results: list[ArticleIngestResult] = []
    try:
        ensure_ukrainian_wiki_schema(conn)
        for article_path in article_paths:
            article_slug = article_path.stem
            article_title = article_slug.replace("-", " ").title()
            article_track = _infer_track(article_path)
            try:
                passages = segment_article_passages(
                    article_path,
                    track=article_track,
                    min_words=min_words,
                    max_chars=max_chars,
                )
                if passages:
                    article_title = passages[0].article_title
                payload, skipped = _build_insert_payload(
                    passages,
                    min_chunk_chars=min_chunk_chars,
                )
                _write_passages(conn, article_slug=article_slug, payload=payload)
                results.append(
                    ArticleIngestResult(
                        article_slug=article_slug,
                        article_title=article_title,
                        article_path=_relative_or_absolute(article_path),
                        track=article_track,
                        segmented_chunks=len(passages),
                        inserted_chunks=len(payload),
                        skipped_chunks=len(skipped),
                        skipped_passages=skipped,
                    )
                )
            except UnicodeDecodeError as exc:
                _write_passages(conn, article_slug=article_slug, payload=[])
                results.append(
                    ArticleIngestResult(
                        article_slug=article_slug,
                        article_title=article_title,
                        article_path=_relative_or_absolute(article_path),
                        track=article_track,
                        segmented_chunks=0,
                        inserted_chunks=0,
                        skipped_chunks=0,
                        skipped_passages=[],
                        failure=f"invalid UTF-8 article: {exc}",
                    )
                )
            except Exception as exc:
                _write_passages(conn, article_slug=article_slug, payload=[])
                results.append(
                    ArticleIngestResult(
                        article_slug=article_slug,
                        article_title=article_title,
                        article_path=_relative_or_absolute(article_path),
                        track=article_track,
                        segmented_chunks=0,
                        inserted_chunks=0,
                        skipped_chunks=0,
                        skipped_passages=[],
                        failure=str(exc),
                    )
                )
    finally:
        conn.close()

    write_ingest_report(results, report_path=report_path, article_root=article_root)
    return results


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Ingest compiled wiki markdown into the ukrainian_wiki corpus.")
    parser.add_argument("article", type=Path, help="Path to a compiled wiki markdown article or a directory of articles")
    parser.add_argument("--db-path", type=Path, default=DEFAULT_DB_PATH, help="Override sources.db path")
    parser.add_argument(
        "--manifest-db",
        type=Path,
        default=DEFAULT_MANIFEST_DB,
        help="Override embeddings manifest path",
    )
    parser.add_argument("--report-path", type=Path, default=DEFAULT_REPORT_PATH)
    parser.add_argument("--min-words", type=int, default=DEFAULT_MIN_WORDS)
    parser.add_argument("--max-chars", type=int, default=DEFAULT_MAX_CHARS)
    parser.add_argument("--min-chunk-chars", type=int, default=DEFAULT_CHUNK_MIN_CHARS)
    parser.add_argument("--min-vesum-coverage", type=float, default=DEFAULT_VESUM_MIN_COVERAGE)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.article.is_dir():
        results = ingest_articles(
            args.article,
            db_path=args.db_path,
            manifest_db=args.manifest_db,
            report_path=args.report_path,
            min_words=args.min_words,
            max_chars=args.max_chars,
            min_chunk_chars=args.min_chunk_chars,
        )
        summary = {
            "articles_scanned": len(results),
            "articles_failed": sum(1 for result in results if result.failure),
            "segmented_chunks": sum(result.segmented_chunks for result in results),
            "inserted_chunks": sum(result.inserted_chunks for result in results),
            "skipped_chunks": sum(result.skipped_chunks for result in results),
            "report_path": _relative_or_absolute(args.report_path),
        }
        print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
        return 0 if summary["articles_failed"] == 0 else 1

    report, inserted = ingest_article(
        args.article,
        db_path=args.db_path,
        manifest_db=args.manifest_db,
        min_words=args.min_words,
        max_chars=args.max_chars,
        min_chunk_chars=args.min_chunk_chars,
        min_vesum_coverage=args.min_vesum_coverage,
    )
    print(report.to_json())
    print(f"inserted_passages={inserted}")
    return 0 if report.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
