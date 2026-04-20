"""Schema, gating, and ingestion helpers for the ``ukrainian_wiki`` corpus."""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
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
DEFAULT_MIN_WORDS = 40
DEFAULT_MAX_CHARS = 900
DEFAULT_VESUM_MIN_COVERAGE = 0.80
UKRAINIAN_WIKI_CORPUS = "ukrainian_wiki"
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")
_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
_HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
_YAML_FRONTMATTER_RE = re.compile(r"\A---\n.*?\n---\n?", re.DOTALL)
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

UKRAINIAN_WIKI_SCHEMA = """
CREATE TABLE IF NOT EXISTS ukrainian_wiki (
    id INTEGER PRIMARY KEY,
    passage_id TEXT NOT NULL UNIQUE,
    article_slug TEXT NOT NULL,
    article_title TEXT NOT NULL DEFAULT '',
    article_path TEXT NOT NULL DEFAULT '',
    section_path TEXT NOT NULL DEFAULT '',
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
    section_path: str
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

    def to_json(self) -> str:
        return json.dumps(
            {
                "passed": self.passed,
                "results": [
                    {
                        **asdict(result),
                        "metadata": dict(result.metadata),
                    }
                    for result in self.results
                ],
            },
            ensure_ascii=False,
            sort_keys=True,
        )


def ensure_ukrainian_wiki_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(UKRAINIAN_WIKI_SCHEMA)


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
    min_words: int = DEFAULT_MIN_WORDS,
    max_chars: int = DEFAULT_MAX_CHARS,
) -> list[Passage]:
    raw_text = article_path.read_text(encoding="utf-8")
    article_text = _strip_non_prose(raw_text)
    article_slug = article_path.stem
    article_rel = _relative_or_absolute(article_path)
    registry_rel = _relative_or_absolute(article_path.with_suffix(".sources.yaml"))

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
            passages.append(
                Passage(
                    passage_id=f"{article_slug}:p{start_idx}-{end_idx}{suffix}",
                    article_slug=article_slug,
                    article_title=article_title,
                    article_path=article_rel,
                    section_path=section_path,
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


def ingest_article(
    article_path: Path,
    *,
    db_path: Path = DEFAULT_DB_PATH,
    manifest_db: Path = DEFAULT_MANIFEST_DB,
    min_words: int = DEFAULT_MIN_WORDS,
    max_chars: int = DEFAULT_MAX_CHARS,
    min_vesum_coverage: float = DEFAULT_VESUM_MIN_COVERAGE,
) -> tuple[AdmissionReport, int]:
    migrate_ukrainian_wiki_corpus(db_path=db_path, manifest_db=manifest_db)
    report = run_admission_gates(article_path, min_vesum_coverage=min_vesum_coverage)
    if not report.passed:
        return report, 0

    passages = segment_article_passages(article_path, min_words=min_words, max_chars=max_chars)
    payload = [
        (
            passage.passage_id,
            passage.article_slug,
            passage.article_title,
            passage.article_path,
            passage.section_path,
            passage.paragraph_start,
            passage.paragraph_end,
            passage.word_count,
            passage.char_count,
            passage.text,
            passage.source_registry_path,
            report.to_json(),
            _utc_now(),
        )
        for passage in passages
    ]

    conn = sqlite3.connect(str(db_path))
    try:
        ensure_ukrainian_wiki_schema(conn)
        conn.execute("BEGIN")
        conn.execute(
            "DELETE FROM ukrainian_wiki WHERE article_slug = ?",
            (article_path.stem,),
        )
        conn.executemany(
            """
            INSERT INTO ukrainian_wiki (
                passage_id, article_slug, article_title, article_path, section_path,
                paragraph_start, paragraph_end, word_count, char_count, text,
                source_registry_path, gate_report_json, inserted_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            payload,
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
    return report, len(passages)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Ingest a compiled wiki article into the ukrainian_wiki corpus.")
    parser.add_argument("article", type=Path, help="Path to the compiled wiki markdown article")
    parser.add_argument("--db-path", type=Path, default=DEFAULT_DB_PATH, help="Override sources.db path")
    parser.add_argument(
        "--manifest-db",
        type=Path,
        default=DEFAULT_MANIFEST_DB,
        help="Override embeddings manifest path",
    )
    parser.add_argument("--min-words", type=int, default=DEFAULT_MIN_WORDS)
    parser.add_argument("--max-chars", type=int, default=DEFAULT_MAX_CHARS)
    parser.add_argument("--min-vesum-coverage", type=float, default=DEFAULT_VESUM_MIN_COVERAGE)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    report, inserted = ingest_article(
        args.article,
        db_path=args.db_path,
        manifest_db=args.manifest_db,
        min_words=args.min_words,
        max_chars=args.max_chars,
        min_vesum_coverage=args.min_vesum_coverage,
    )
    print(report.to_json())
    print(f"inserted_passages={inserted}")
    return 0 if report.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
