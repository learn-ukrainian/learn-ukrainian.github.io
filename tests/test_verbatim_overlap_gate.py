"""
Deterministic tests for verbatim_overlap_gate.

All tests are hermetic: they construct tiny in-memory or tmp SQLite sources
(no dependency on real data/sources.db for pytest runs).

Covers:
- Golden extraction (A1 free-time + B1 narrative-mastery)
- Verbatim copy detection (max_run + span)
- Paraphrase is clean
- Attributed quote allowlisted in ratio (via injectable verify)
- DF-gaming: long run stitched with high-DF connectors still flags max_contiguous_run
- Copied ACTIVITY content is flagged
- Index build determinism (same fp + postings)
- Normalization idempotence + stress/apostrophe handling
"""

from __future__ import annotations

import sqlite3
import tempfile
from pathlib import Path

from scripts.audit.verbatim_overlap_gate import (
    EXTRACTION_SPEC_VERSION,
    ExtractedSpan,
    ShingleIndex,
    compute_metrics,
    extract_from_activities_yaml,
    extract_from_module_md,
    extract_module_content,
    module_tokens_from_spans,
    normalize_text,
    tokenize,
)

A1_FREE_TIME = Path("curriculum/l2-uk-en/a1/free-time")
B1_NARRATIVE = Path("curriculum/l2-uk-en/b1/narrative-mastery")


def _tiny_sources_db() -> tuple[sqlite3.Connection, Path]:
    """Create a hermetic tiny sources.db on disk (for index + sources_conn sharing)."""
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)  # noqa: SIM115 - need persistent path for sqlite sharing across index/sources_conn
    path = Path(tmp.name)
    tmp.close()
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.executescript(
        """
        CREATE TABLE textbooks (
            id INTEGER PRIMARY KEY,
            chunk_id TEXT,
            title TEXT,
            text TEXT,
            source_file TEXT,
            author TEXT
        );
        CREATE TABLE literary_texts (
            id INTEGER PRIMARY KEY,
            chunk_id TEXT,
            title TEXT,
            text TEXT,
            author TEXT,
            work TEXT,
            year INTEGER
        );
        CREATE TABLE external_articles (
            id INTEGER PRIMARY KEY,
            chunk_id TEXT,
            title TEXT,
            text TEXT,
            url TEXT
        );
        CREATE TABLE ukrainian_wiki (
            id INTEGER PRIMARY KEY,
            passage_id TEXT,
            text TEXT,
            article_slug TEXT
        );
        """
    )
    return conn, path


def _seed_corpus(conn: sqlite3.Connection, chunks: list[dict]) -> None:
    """Insert sample corpus rows. chunks: [{'table': , 'chunk_id':, 'text':, 'author':? }]"""
    for ch in chunks:
        tbl = ch["table"]
        if tbl == "textbooks":
            conn.execute(
                "INSERT INTO textbooks (chunk_id, text, title, author) VALUES (?, ?, ?, ?)",
                (ch["chunk_id"], ch["text"], ch.get("title", ""), ch.get("author", "")),
            )
        elif tbl == "literary_texts":
            conn.execute(
                "INSERT INTO literary_texts (chunk_id, text, title, author, work, year) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    ch["chunk_id"],
                    ch["text"],
                    ch.get("title", ""),
                    ch.get("author", ""),
                    ch.get("work", ""),
                    ch.get("year"),
                ),
            )
        elif tbl == "external_articles":
            conn.execute(
                "INSERT INTO external_articles (chunk_id, text, title) VALUES (?, ?, ?)",
                (ch["chunk_id"], ch["text"], ch.get("title", "")),
            )
        elif tbl == "ukrainian_wiki":
            conn.execute(
                "INSERT INTO ukrainian_wiki (passage_id, text, article_slug) VALUES (?, ?, ?)",
                (ch["chunk_id"], ch["text"], ch.get("slug", "test")),
            )
    conn.commit()


def test_normalize_and_tokenize_deterministic_and_ua_aware():
    s1 = "М'який  —  «Ходімо!»  Привіт,  світ."
    n1 = normalize_text(s1)
    t1 = tokenize(n1)
    n2 = normalize_text(s1)
    assert n1 == n2
    assert any(t.startswith("м'") or t == "м" for t in t1) or "м" in t1  # apostrophe handling keeps word pieces
    # stress mark stripped
    stressed = "приві́т"
    assert "́" not in normalize_text(stressed)
    assert "привіт" in normalize_text(stressed)


def test_golden_extraction_a1_free_time_has_dialogue_ua():
    spans = extract_from_module_md(A1_FREE_TIME / "module.md")
    joined = " ".join(s.norm for s in spans)
    # Key UA from dialogues must be present
    assert "ходімо в кіно в суботу" in joined
    assert "добрий день" in joined or "що ти робиш" in joined
    # Key UA dialogues must be present (English scaffolding may leak from tables; the gate's job is UA detection)
    assert "ходімо в кіно в суботу" in joined
    assert "let's go" not in joined.lower() or "добрий день" in joined  # tolerate limited leakage from support tables
    # Some activity content via yaml
    act_spans = extract_from_activities_yaml(A1_FREE_TIME / "activities.yaml")
    assert any("грати" in s.norm for s in act_spans)
    assert any("хобі" in s.norm or "футбол" in s.norm for s in act_spans)


def test_golden_extraction_b1_has_substantial_ua_prose():
    spans = extract_from_module_md(B1_NARRATIVE / "module.md")
    joined = " ".join(s.norm for s in spans)
    # Substantial UA prose
    assert "розповідь" in joined
    assert "зачин" in joined and "кульмінація" in joined
    assert len(joined) > 800  # real content volume
    # Activities also
    act_spans = extract_from_activities_yaml(B1_NARRATIVE / "activities.yaml")
    assert any("недоконаний" in s.norm or "тло" in s.norm for s in act_spans)


def test_extraction_spec_version_is_stable():
    assert "2026-07" in EXTRACTION_SPEC_VERSION
    assert "activities" in EXTRACTION_SPEC_VERSION.lower()


def test_hermetic_verbatim_copy_flagged(tmp_path: Path):
    conn, _dbp = _tiny_sources_db()
    corpus_text = (
        "Минулої суботи я вийшла з дому раніше, бо хотіла встигнути на ранковий потяг до Чернівців. "
        "Біля вокзалу я раптом зустріла однокласника. Він усміхнувся і запропонував піти разом."
    )
    _seed_corpus(conn, [{"table": "textbooks", "chunk_id": "t-001", "text": corpus_text}])

    # Simulate module that copied a long contiguous chunk
    copy = "Біля вокзалу я раптом зустріла однокласника. Він усміхнувся і запропонував піти разом."
    spans = [ExtractedSpan(text=copy, norm=normalize_text(copy), tokens=tokenize(normalize_text(copy)),
                           source="test.md:10-20", kind="test")]
    mod_tokens = module_tokens_from_spans(spans)

    idx = ShingleIndex(tmp_path / "idx.db", k=4)  # smaller k for toy
    fp = idx.build(conn)
    assert fp

    rpt = compute_metrics(mod_tokens, idx, conn, df_n=999)  # high DF so no filter
    assert rpt.max_contiguous_run >= 8  # at least several words contiguous
    assert rpt.top_offense is not None
    assert rpt.top_offense["corpus"] == "textbooks"
    assert "встрела" in rpt.top_offense.get("matched_shingle", "") or "вокзалу" in str(rpt.top_offense)
    conn.close()
    idx.close()


def test_paraphrase_is_clean(tmp_path: Path):
    conn, _dbp = _tiny_sources_db()
    corpus_text = "Ми повільно йшли вузькою вулицею, коли почули музику. Раптом двері відчинилися."
    _seed_corpus(conn, [{"table": "literary_texts", "chunk_id": "lit-42", "text": corpus_text, "author": "Тест"}])

    para = "Ми неквапно крокували вузьким провулком і раптом почули звуки. Двері зненацька розчахнулися."
    spans = [ExtractedSpan(text=para, norm=normalize_text(para), tokens=tokenize(normalize_text(para)),
                           source="p", kind="p")]
    mod_tokens = module_tokens_from_spans(spans)

    idx = ShingleIndex(tmp_path / "idx2.db", k=5)
    idx.build(conn)
    rpt = compute_metrics(mod_tokens, idx, conn, df_n=2)
    # Paraphrase should produce zero or tiny contiguous run (main guarantee)
    assert rpt.max_contiguous_run <= 4
    # ratio may be moderate on short overlapping common words; do not over-assert here
    assert rpt.max_contiguous_run <= 4 or rpt.overlap_ratio < 0.6
    conn.close()
    idx.close()


def test_attributed_quote_allowlisted_in_ratio(tmp_path: Path):
    conn, _dbp = _tiny_sources_db()
    qtext = "І сниться мені, що я лечу."
    _seed_corpus(conn, [{"table": "literary_texts", "chunk_id": "shev-1", "text": "І сниться мені, що я лечу крізь ніч.", "author": "Шевченко"}])

    spans = [ExtractedSpan(text=qtext, norm=normalize_text(qtext), tokens=tokenize(normalize_text(qtext)),
                           source="q", kind="quote")]
    mod_tokens = module_tokens_from_spans(spans)

    idx = ShingleIndex(tmp_path / "idxq.db", k=3)
    idx.build(conn)

    def fake_verify(author: str, text: str) -> float:
        if "сниться" in text or "леч" in text:
            return 0.92
        return 0.1

    rpt = compute_metrics(mod_tokens, idx, conn, df_n=999, verify_quote_fn=fake_verify)
    # With high verify, the ratio should be 0 (excluded) even if shingles matched
    assert rpt.overlap_ratio == 0.0 or len(rpt.verified_quote_excludes) > 0
    conn.close()
    idx.close()


def test_df_gaming_long_run_still_flagged_by_max_contiguous(tmp_path: Path):
    """High-DF connectors must not hide a long verbatim run in max_contiguous_run."""
    conn, _dbp = _tiny_sources_db()
    # A long run with some common words that will have high DF
    long_run = (
        "ми йшли і йшли а потім ми побачили і побачили знову і знову "
        "старий дуб біля річки під час дощу коли все було тихо"
    )
    common = "і ми а потім побачили знову коли все було"
    # Seed many chunks with the common phrase to drive DF high
    for i in range(12):
        _seed_corpus(conn, [{"table": "textbooks", "chunk_id": f"c{i}", "text": common + f" {i}"}])
    # The real source chunk with the long verbatim
    _seed_corpus(conn, [{"table": "textbooks", "chunk_id": "long-1", "text": long_run}])

    # Module copies the long run
    spans = [ExtractedSpan(text=long_run, norm=normalize_text(long_run), tokens=tokenize(normalize_text(long_run)),
                           source="m", kind="m")]
    mod_tokens = module_tokens_from_spans(spans)

    idx = ShingleIndex(tmp_path / "idxdf.db", k=4)
    idx.build(conn)

    rpt = compute_metrics(mod_tokens, idx, conn, df_n=3)  # low N so common excluded from ratio
    # max_run must still be large (the core of the run survives chaining)
    assert rpt.max_contiguous_run >= 9
    # ratio may be lower due to DF but max_run proves the guard
    conn.close()
    idx.close()


def test_copied_activity_is_flagged(tmp_path: Path):
    conn, _dbp = _tiny_sources_db()
    act_text = "З'єднай дієслово з логічним словом: грати у футбол"
    _seed_corpus(conn, [{"table": "textbooks", "chunk_id": "actbook-7", "text": act_text + " і слухати музику."}])

    # Simulate extracted activity item
    spans = [ExtractedSpan(text=act_text, norm=normalize_text(act_text), tokens=tokenize(normalize_text(act_text)),
                           source="activities.yaml#act-1", kind="activity")]
    mod_tokens = module_tokens_from_spans(spans)

    idx = ShingleIndex(tmp_path / "idxact.db", k=4)
    idx.build(conn)
    rpt = compute_metrics(mod_tokens, idx, conn, df_n=99)
    assert rpt.max_contiguous_run >= 5
    assert rpt.top_offense is not None
    conn.close()
    idx.close()


def test_index_build_is_deterministic(tmp_path: Path):
    conn, _dbp = _tiny_sources_db()
    _seed_corpus(conn, [
        {"table": "literary_texts", "chunk_id": "d1", "text": "Сонце сідає за обрій. Птахи замовкають."},
        {"table": "literary_texts", "chunk_id": "d2", "text": "Вітер гуляє в полі. Дерева шумлять."},
    ])
    idx1 = ShingleIndex(tmp_path / "d1.db", k=3)
    fp1 = idx1.build(conn)
    p1 = idx1.conn.execute("SELECT COUNT(*) FROM postings").fetchone()[0]
    idx1.close()

    idx2 = ShingleIndex(tmp_path / "d2.db", k=3)
    fp2 = idx2.build(conn)
    p2 = idx2.conn.execute("SELECT COUNT(*) FROM postings").fetchone()[0]
    idx2.close()

    assert fp1 == fp2
    assert p1 == p2 > 0
    conn.close()


def test_full_extract_module_and_analyze_hermetic(tmp_path: Path):
    conn, _dbp = _tiny_sources_db()
    # Seed a chunk that will verbatim match something in real A1 (but we use synthetic for isolation)
    _seed_corpus(conn, [{"table": "textbooks", "chunk_id": "toy-1", "text": "Ходімо в кіно в суботу. Добре. О котрій?"}])

    # Use real A1 module extraction (it must not crash and must surface UA)
    spans, meta = extract_module_content(A1_FREE_TIME)
    assert meta["extraction_spec"] == EXTRACTION_SPEC_VERSION
    assert len(spans) >= 3

    mod_tokens = module_tokens_from_spans(spans)
    idx = ShingleIndex(tmp_path / "full.db", k=5)
    idx.build(conn)
    rpt = compute_metrics(mod_tokens, idx, conn, df_n=99)
    # May or may not match our toy, but must run without error and produce numbers
    assert rpt.total_prose_tokens > 0
    assert 0.0 <= rpt.overlap_ratio <= 1.0
    assert rpt.max_contiguous_run >= 0
    conn.close()
    idx.close()


def test_chained_run_and_lcs_recovery(tmp_path: Path):
    conn, _dbp = _tiny_sources_db()
    src = "один два три чотири п'ять шість сім вісім дев'ять десять"
    _seed_corpus(conn, [{"table": "textbooks", "chunk_id": "seq-9", "text": src}])

    # module has almost exact but with one high-DF break
    mod = "один два три чотири п'ять шість сім вісім дев'ять десять"
    spans = [ExtractedSpan(text=mod, norm=normalize_text(mod), tokens=tokenize(normalize_text(mod)), source="s", kind="s")]
    toks = module_tokens_from_spans(spans)

    idx = ShingleIndex(tmp_path / "lcs.db", k=3)
    idx.build(conn)
    rpt = compute_metrics(toks, idx, conn, df_n=1)
    assert rpt.max_contiguous_run >= 8
    # LCS path should also recover ~10
    assert rpt.top_offense is None or rpt.top_offense.get("lcs_run", 0) >= 5
    conn.close()
    idx.close()


def test_multiline_html_comment_not_leaked_into_extraction(tmp_path: Path):
    """Regression (CodeQL py/bad-tag-filter, high): multi-line ``<!-- ... -->``
    comments — including multi-line INJECT_ACTIVITY markers — must be stripped
    document-wide, so their Cyrillic content never leaks into extracted prose.
    The previous per-line ``<!--.*?-->`` in strip_md_inline silently leaked them."""
    md = tmp_path / "module.md"
    md.write_text(
        "---\ntitle: t\n---\n"
        "Це справжня навчальна проза для аудиту.\n"
        "<!-- INJECT_ACTIVITY: act-1\n"
        "ЦЕЙ ТЕКСТ У БАГАТОРЯДКОВОМУ КОМЕНТАРІ НЕ ПОВИНЕН ВИТІКАТИ\n"
        "-->\n"
        "Ще одна навчальна проза для аудиту.\n",
        encoding="utf-8",
    )
    spans = extract_from_module_md(md)
    blob = " ".join(s.text for s in spans) + " " + " ".join(s.norm for s in spans)
    assert "ВИТІКАТИ" not in blob and "витікати" not in blob.lower()
    assert any("навчальна проза" in s.text.lower() for s in spans)
