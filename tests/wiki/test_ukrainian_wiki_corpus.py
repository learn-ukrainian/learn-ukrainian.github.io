from __future__ import annotations

import hashlib
import json
import sqlite3
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from wiki.embedding_manifest import EmbeddingManifest

from wiki import dense_rerank, sources_db, ukrainian_wiki_corpus


class _FakeTokenizer:
    def encode(
        self,
        text: str,
        add_special_tokens: bool = True,
        truncation: bool = True,
        max_length: int | None = None,
    ) -> list[int]:
        tokens = list(range(1, len(text.split()) + 1))
        if max_length is not None:
            limit = max_length - (2 if add_special_tokens else 0)
            tokens = tokens[:limit]
        if add_special_tokens:
            return [0, *tokens, 1]
        return tokens


class _FakeEncoder:
    def encode(self, texts: list[str], batch_size: int = 16, max_length: int = 512) -> np.ndarray:
        vectors: list[np.ndarray] = []
        for text in texts:
            digest = hashlib.sha256(text.encode("utf-8")).digest()
            seed = np.frombuffer(digest * 64, dtype=np.uint8)[: dense_rerank.EMBEDDING_DIMS].astype(np.float32)
            vector = seed / np.clip(np.linalg.norm(seed), 1e-12, None)
            vectors.append(vector.astype(np.float16))
        return np.stack(vectors, axis=0)


def _install_fake_encoder(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_tokenizer = _FakeTokenizer()
    fake_encoder = _FakeEncoder()
    monkeypatch.setattr(dense_rerank, "_TOKENIZER", fake_tokenizer)
    monkeypatch.setattr(dense_rerank, "_get_tokenizer", lambda: fake_tokenizer)
    monkeypatch.setattr(dense_rerank, "_ENCODER", fake_encoder)
    monkeypatch.setattr(dense_rerank, "_get_encoder", lambda: fake_encoder)


def _article_with_registry(
    tmp_path: Path,
    *,
    slug: str = "apostrof",
    text: str,
    source_dir: tuple[str, ...] = ("wiki", "pedagogy", "a1"),
) -> Path:
    article = tmp_path.joinpath(*source_dir) / f"{slug}.md"
    article.parent.mkdir(parents=True, exist_ok=True)
    article.write_text(text, encoding="utf-8")
    article_rel = article.relative_to(tmp_path).as_posix()
    article.with_suffix(".sources.yaml").write_text(
        f"# Source registry for {article_rel}\n"
        "sources:\n"
        "  - id: S1\n"
        "    file: ext-demo\n"
        "    type: external\n",
        encoding="utf-8",
    )
    return article


def _configure_search(
    monkeypatch: pytest.MonkeyPatch,
    conn: sqlite3.Connection,
    manifest_path: Path,
) -> None:
    monkeypatch.setattr(sources_db, "_get_conn", lambda: conn)
    monkeypatch.setattr(sources_db, "_CORPORA", ("ukrainian_wiki",))
    monkeypatch.setattr(
        sources_db,
        "rerank_candidates",
        lambda query, candidates, *, corpus, limit=10: dense_rerank.rerank_candidates(
            query,
            candidates,
            corpus=corpus,
            limit=limit,
            manifest_db=manifest_path,
        ),
    )


def test_schema_creation_adds_table_and_fts(tmp_path: Path) -> None:
    db_path = tmp_path / "sources.db"
    manifest_path = tmp_path / "embeddings" / "manifest.db"

    ukrainian_wiki_corpus.migrate_ukrainian_wiki_corpus(
        db_path=db_path,
        manifest_db=manifest_path,
    )

    conn = sqlite3.connect(db_path)
    try:
        rows = {
            (row[0], row[1])
            for row in conn.execute(
                """
                SELECT type, name
                FROM sqlite_master
                WHERE name IN (
                    'ukrainian_wiki',
                    'ukrainian_wiki_fts',
                    'ukrainian_wiki_ai',
                    'ukrainian_wiki_ad',
                    'ukrainian_wiki_au'
                )
                """
            ).fetchall()
        }
        columns = {
            row[1]
            for row in conn.execute("PRAGMA table_info(ukrainian_wiki)").fetchall()
        }
    finally:
        conn.close()

    assert ("table", "ukrainian_wiki") in rows
    assert ("table", "ukrainian_wiki_fts") in rows
    assert ("trigger", "ukrainian_wiki_ai") in rows
    assert ("trigger", "ukrainian_wiki_ad") in rows
    assert ("trigger", "ukrainian_wiki_au") in rows
    assert {"track", "heading_path", "chunk_index"} <= columns


def test_manifest_registration_reserves_zero_row_shard(tmp_path: Path) -> None:
    manifest_path = tmp_path / "embeddings" / "manifest.db"

    ukrainian_wiki_corpus.ensure_ukrainian_wiki_manifest(manifest_path)

    manifest = EmbeddingManifest(manifest_path)
    try:
        stats = manifest.stats()
        shard_map = manifest.shard_map_for_corpus("ukrainian_wiki")
    finally:
        manifest.close()

    assert stats["corpora"]["ukrainian_wiki"]["shards"] == 1
    assert stats["corpora"]["ukrainian_wiki"]["shard_rows"] == 0
    assert len(shard_map) == 1
    assert next(iter(shard_map.values())).exists()


def test_track_prior_values_favor_a1_a2_and_near_zero_b1_plus() -> None:
    assert sources_db._corpus_prior("a1", "ukrainian_wiki") == pytest.approx(0.95)
    assert sources_db._corpus_prior("a2", "ukrainian_wiki") == pytest.approx(0.90)
    assert sources_db._corpus_prior("b1", "ukrainian_wiki") == pytest.approx(0.05)
    assert sources_db._corpus_prior("c1", "ukrainian_wiki") == pytest.approx(0.02)
    assert sources_db._corpus_prior("a1", "ukrainian_wiki") > sources_db._corpus_prior("b1", "ukrainian_wiki")


def test_search_sources_returns_empty_cleanly_for_reserved_but_empty_corpus(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    db_path = tmp_path / "sources.db"
    manifest_path = tmp_path / "embeddings" / "manifest.db"
    ukrainian_wiki_corpus.migrate_ukrainian_wiki_corpus(
        db_path=db_path,
        manifest_db=manifest_path,
    )

    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    _configure_search(monkeypatch, conn, manifest_path)

    results = sources_db.search_sources("апостроф", track="a1", strategy="modern_dense_section", limit=5)

    assert results == []
    conn.close()


def test_round_trip_insert_and_search_query(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    article = _article_with_registry(
        tmp_path,
        text=(
            "# Апостроф\n\n"
            "Апостроф допомагає зберегти правильну вимову в українській мові [S1]. "
            "У словах типу п'ять і м'ята він відділяє звук й від попереднього приголосного.\n\n"
            "Цей короткий навчальний абзац пояснює правило простою мовою і дає зрозумілі "
            "приклади для початківця.\n"
        ),
    )
    db_path = tmp_path / "sources.db"
    manifest_path = tmp_path / "embeddings" / "manifest.db"

    monkeypatch.setattr(
        ukrainian_wiki_corpus,
        "vesum_batch_lookup",
        lambda words: {word: [{"word": word}] for word in words},
    )
    monkeypatch.setattr(ukrainian_wiki_corpus, "check_russicisms", lambda text, file_path="": [])
    monkeypatch.setattr(ukrainian_wiki_corpus, "pravopys_lookup", lambda term: {"term": term})
    monkeypatch.setattr(ukrainian_wiki_corpus, "search_style_guide", lambda term: [])

    report, inserted = ukrainian_wiki_corpus.ingest_article(
        article,
        db_path=db_path,
        manifest_db=manifest_path,
        min_words=5,
        max_chars=1000,
        min_vesum_coverage=0.5,
    )

    assert report.passed is True
    assert inserted == 2

    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        stored_count = conn.execute("SELECT COUNT(*) FROM ukrainian_wiki").fetchone()[0]
        row = conn.execute(
            """
            SELECT article_slug, article_title, track, heading_path, section_path, chunk_index, word_count, text, gate_report_json
            FROM ukrainian_wiki
            ORDER BY paragraph_start, id
            LIMIT 1
            """
        ).fetchone()
        assert stored_count == 2
        assert row["article_slug"] == "apostrof"
        assert row["article_title"] == "Апостроф"
        assert row["track"] == "a1"
        assert row["heading_path"] == "Апостроф"
        assert row["section_path"] == "Апостроф"
        assert row["chunk_index"] == 1
        assert "Апостроф допомагає" in row["text"]
        assert json.loads(row["gate_report_json"])["passed"] is True

        _configure_search(monkeypatch, conn, manifest_path)
        results = sources_db.search_sources("апостроф", track="a1", strategy="modern_dense_section", limit=5)
    finally:
        conn.close()

    assert len(results) == 1
    assert results[0]["corpus"] == "ukrainian_wiki"
    assert results[0]["title"] == "Апостроф"
    assert "п'ять" in results[0]["text"]


def test_round_trip_insert_preserves_a2_track(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    article = _article_with_registry(
        tmp_path,
        slug="aspect-concept",
        source_dir=("wiki", "grammar", "a2"),
        text=(
            "# Вид дієслова\n\n"
            "Вид дієслова допомагає розрізняти завершену та незавершену дію [S1]. "
            "Для рівня A2 ця тема потрібна, щоб поєднувати часові форми і намір мовця.\n\n"
            "У парах читати і прочитати учень бачить, як змінюється значення результату "
            "та тривалості дії.\n"
        ),
    )
    db_path = tmp_path / "sources.db"
    manifest_path = tmp_path / "embeddings" / "manifest.db"

    monkeypatch.setattr(
        ukrainian_wiki_corpus,
        "vesum_batch_lookup",
        lambda words: {word: [{"word": word}] for word in words},
    )
    monkeypatch.setattr(ukrainian_wiki_corpus, "check_russicisms", lambda text, file_path="": [])
    monkeypatch.setattr(ukrainian_wiki_corpus, "pravopys_lookup", lambda term: {"term": term})
    monkeypatch.setattr(ukrainian_wiki_corpus, "search_style_guide", lambda term: [])

    report, inserted = ukrainian_wiki_corpus.ingest_article(
        article,
        db_path=db_path,
        manifest_db=manifest_path,
        min_words=5,
        max_chars=1000,
        min_vesum_coverage=0.5,
    )

    assert report.passed is True
    assert inserted == 2

    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute(
            "SELECT article_slug, track FROM ukrainian_wiki ORDER BY chunk_index"
        ).fetchall()
    finally:
        conn.close()

    assert rows == [("aspect-concept", "a2"), ("aspect-concept", "a2")]


def test_admission_gate_pass_and_fail(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    good_article = _article_with_registry(
        tmp_path,
        text=(
            "# Апостроф\n\n"
            "Апостроф уживають після губних перед я, ю, є, ї [S1]. "
            "Правило корисне для початківців і подається коротко та чітко.\n"
        ),
    )

    monkeypatch.setattr(
        ukrainian_wiki_corpus,
        "vesum_batch_lookup",
        lambda words: {word: [{"word": word}] for word in words},
    )
    monkeypatch.setattr(ukrainian_wiki_corpus, "check_russicisms", lambda text, file_path="": [])
    monkeypatch.setattr(ukrainian_wiki_corpus, "pravopys_lookup", lambda term: {"term": term})
    monkeypatch.setattr(ukrainian_wiki_corpus, "search_style_guide", lambda term: [])

    passed_report = ukrainian_wiki_corpus.run_admission_gates(good_article, min_vesum_coverage=0.5)

    assert passed_report.passed is True
    assert [result.passed for result in passed_report.results] == [True, True, True, True, True]

    bad_article = tmp_path / "wiki" / "pedagogy" / "a1" / "bad.md"
    bad_article.parent.mkdir(parents=True, exist_ok=True)
    bad_article.write_text("# Погано\n\nПриймати участь корисно [S1].\n", encoding="utf-8")

    monkeypatch.setattr(
        ukrainian_wiki_corpus,
        "vesum_batch_lookup",
        lambda words: {word: [] for word in words},
    )
    monkeypatch.setattr(
        ukrainian_wiki_corpus,
        "check_russicisms",
        lambda text, file_path="": [
            {
                "type": "RUSSICISM_DETECTED",
                "severity": "warning",
                "issue": "Found 1 Russicism(s) in content: 'приймати участь' → брати участь",
                "fix": "Replace Russicisms",
            }
        ],
    )
    monkeypatch.setattr(ukrainian_wiki_corpus, "pravopys_lookup", lambda term: None)
    monkeypatch.setattr(ukrainian_wiki_corpus, "search_style_guide", lambda term: [])

    failed_report = ukrainian_wiki_corpus.run_admission_gates(bad_article, min_vesum_coverage=0.9)

    assert failed_report.passed is False
    assert failed_report.results[0].passed is False
    assert failed_report.results[1].passed is False
    assert failed_report.results[2].passed is False
    assert failed_report.results[4].passed is False


def test_chunk_admission_gate_rejects_short_non_cyrillic_text() -> None:
    report = ukrainian_wiki_corpus.run_chunk_admission_gates("hello", min_chars=50)

    assert report.passed is False
    assert [result.name for result in report.results] == ["utf8", "min_length", "cyrillic"]
    assert report.results[0].passed is True
    assert report.results[1].passed is False
    assert report.results[2].passed is False


def test_batch_ingest_directory_is_idempotent_and_writes_report(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    article_dir = tmp_path / "wiki" / "grammar" / "a2"
    _article_with_registry(
        tmp_path,
        slug="apostrof",
        source_dir=("wiki", "grammar", "a2"),
        text=(
            "# Апостроф\n\n"
            "Апостроф допомагає відділяти звук й від попереднього приголосного в словах "
            "типу п'ять і м'ята [S1]. Це базове правило для початківця.\n"
        ),
    )
    _article_with_registry(
        tmp_path,
        slug="holosni",
        source_dir=("wiki", "grammar", "a2"),
        text=(
            "# Голосні\n\n"
            "Голосні в українській мові формують склад і визначають мелодію мовлення [S1]. "
            "Учень має чітко чути різницю між и та і.\n"
        ),
    )
    _article_with_registry(
        tmp_path,
        slug="pryvitannia",
        source_dir=("wiki", "grammar", "a2"),
        text=(
            "# Привітання\n\n"
            "Фрази добрий день, привіт і дякую потрібні з першого уроку [S1]. "
            "Вони дають учневі прості моделі для контакту.\n"
        ),
    )
    _article_with_registry(
        tmp_path,
        slug="nagolos",
        source_dir=("wiki", "grammar", "a2"),
        text=(
            "# Наголос\n\n"
            "Наголос в українській мові допомагає розрізняти форми слів і підтримує природну "
            "інтонацію речення [S1]. Учень тренує слухання і повторення.\n"
        ),
    )
    _article_with_registry(
        tmp_path,
        slug="kyrylytsia",
        source_dir=("wiki", "grammar", "a2"),
        text=(
            "# Кирилиця\n\n"
            "Українська кирилиця має власні літери, зокрема ґ та ї [S1]. "
            "Це варто показувати з першого дня навчання.\n"
        ),
    )

    db_path = tmp_path / "sources.db"
    manifest_path = tmp_path / "embeddings" / "manifest.db"
    report_path = tmp_path / "ukrainian_wiki_a2_ingest_report.md"

    first_results = ukrainian_wiki_corpus.ingest_articles(
        article_dir,
        db_path=db_path,
        manifest_db=manifest_path,
        report_path=report_path,
        min_words=5,
        max_chars=1000,
        min_chunk_chars=50,
    )
    second_results = ukrainian_wiki_corpus.ingest_articles(
        article_dir,
        db_path=db_path,
        manifest_db=manifest_path,
        report_path=report_path,
        min_words=5,
        max_chars=1000,
        min_chunk_chars=50,
    )

    assert len(first_results) == 5
    assert all(result.failure is None for result in first_results)
    assert [result.track for result in first_results] == ["a2", "a2", "a2", "a2", "a2"]
    assert [result.inserted_chunks for result in first_results] == [1, 1, 1, 1, 1]
    assert [result.inserted_chunks for result in second_results] == [1, 1, 1, 1, 1]

    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        stored_count = conn.execute("SELECT COUNT(*) FROM ukrainian_wiki").fetchone()[0]
        bm25_rows = conn.execute(
            """
            SELECT s.article_slug, bm25(ukrainian_wiki_fts, 5.0, 2.0, 1.0) AS rank
            FROM ukrainian_wiki_fts
            JOIN ukrainian_wiki s ON s.id = ukrainian_wiki_fts.rowid
            WHERE ukrainian_wiki_fts MATCH ?
            ORDER BY rank
            """,
            ("апостроф",),
        ).fetchall()
        _configure_search(monkeypatch, conn, manifest_path)
        results = sources_db.search_sources("наголос", track="a2", strategy="modern_dense_section", limit=5)
    finally:
        conn.close()

    assert stored_count == 5
    assert bm25_rows[0]["article_slug"] == "apostrof"
    assert report_path.exists()
    report_text = report_path.read_text(encoding="utf-8")
    assert "# Ukrainian Wiki A2 Ingest Report" in report_text
    assert "wiki/grammar/a2" in report_text
    assert "Total chunks ingested: 5" in report_text
    assert "`apostrof`" in report_text
    assert len(results) == 1
    assert results[0]["corpus"] == "ukrainian_wiki"
    assert results[0]["title"] == "Наголос"


def test_encode_flag_populates_manifest_units_matching_search_unit_keys(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Regression for the zero-embedding gap: ingest only fills SQLite,
    so ``--encode`` (or ``encode_ukrainian_wiki_corpus``) must populate the
    manifest with unit rows whose keys match the ``ukrainian_wiki:{passage_id}``
    format that ``_search_ukrainian_wiki_candidates`` emits — otherwise the
    dense reranker silently drops every ukrainian_wiki candidate to score 0
    and they lose to every other corpus in the final sort.
    """

    article = _article_with_registry(
        tmp_path,
        slug="kolory",
        text=(
            "# Кольори\n\n"
            "Кольори допомагають описувати предмети довкола нас [S1]. "
            "Червоний, синій, жовтий і зелений — це базова лексика для A1.\n\n"
            "Учень використовує ці слова, щоб говорити про одяг, природу "
            "і прості сцени з повсякденного життя.\n"
        ),
    )
    db_path = tmp_path / "sources.db"
    manifest_path = tmp_path / "embeddings" / "manifest.db"

    monkeypatch.setattr(
        ukrainian_wiki_corpus,
        "vesum_batch_lookup",
        lambda words: {word: [{"word": word}] for word in words},
    )
    monkeypatch.setattr(ukrainian_wiki_corpus, "check_russicisms", lambda text, file_path="": [])
    monkeypatch.setattr(ukrainian_wiki_corpus, "pravopys_lookup", lambda term: {"term": term})
    monkeypatch.setattr(ukrainian_wiki_corpus, "search_style_guide", lambda term: [])
    _install_fake_encoder(monkeypatch)

    report, inserted = ukrainian_wiki_corpus.ingest_article(
        article,
        db_path=db_path,
        manifest_db=manifest_path,
        min_words=5,
        max_chars=1000,
        min_vesum_coverage=0.5,
    )
    assert report.passed is True
    assert inserted >= 1

    manifest = EmbeddingManifest(manifest_path)
    try:
        active_before = manifest.active_units_for_corpus("ukrainian_wiki")
    finally:
        manifest.close()
    assert active_before == [], (
        "ingest alone must not encode — encode step is explicit so MLX is not "
        "triggered unintentionally"
    )

    encode_summary = ukrainian_wiki_corpus.encode_ukrainian_wiki_corpus(
        db_path=db_path,
        manifest_db=manifest_path,
    )
    assert encode_summary["status"] == "encoded"
    assert encode_summary["encoded_units"] == inserted

    passage_ids = _fetch_passage_ids(db_path)
    manifest = EmbeddingManifest(manifest_path)
    try:
        active_after = manifest.active_units_for_corpus("ukrainian_wiki")
    finally:
        manifest.close()

    assert len(active_after) == inserted
    encoded_keys = {row.unit_key for row in active_after}
    expected_keys = {f"ukrainian_wiki:{pid}" for pid in passage_ids}
    assert encoded_keys == expected_keys, (
        "unit_key format must match _search_ukrainian_wiki_candidates so the "
        "dense reranker can look up vectors by unit_key"
    )

    second = ukrainian_wiki_corpus.encode_ukrainian_wiki_corpus(
        db_path=db_path,
        manifest_db=manifest_path,
    )
    assert second["status"] == "up_to_date"
    assert second["encoded_units"] == 0


def _fetch_passage_ids(db_path: Path) -> list[str]:
    conn = sqlite3.connect(db_path)
    try:
        return [row[0] for row in conn.execute("SELECT passage_id FROM ukrainian_wiki ORDER BY id")]
    finally:
        conn.close()


def test_main_cli_encode_flag_wires_ingest_to_manifest(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """--encode on the CLI must trigger encoding after a successful ingest."""

    article = _article_with_registry(
        tmp_path,
        slug="simya",
        text=(
            "# Сім'я\n\n"
            "Сім'я — це найближчі люди поряд з учнем [S1]. "
            "Мама, тато, брат і сестра дають першу лексику для A1.\n\n"
            "Учень описує свою родину простими реченнями.\n"
        ),
    )
    db_path = tmp_path / "sources.db"
    manifest_path = tmp_path / "embeddings" / "manifest.db"

    monkeypatch.setattr(
        ukrainian_wiki_corpus,
        "vesum_batch_lookup",
        lambda words: {word: [{"word": word}] for word in words},
    )
    monkeypatch.setattr(ukrainian_wiki_corpus, "check_russicisms", lambda text, file_path="": [])
    monkeypatch.setattr(ukrainian_wiki_corpus, "pravopys_lookup", lambda term: {"term": term})
    monkeypatch.setattr(ukrainian_wiki_corpus, "search_style_guide", lambda term: [])
    _install_fake_encoder(monkeypatch)

    exit_code = ukrainian_wiki_corpus.main(
        [
            str(article),
            "--db-path",
            str(db_path),
            "--manifest-db",
            str(manifest_path),
            "--min-words",
            "5",
            "--max-chars",
            "1000",
            "--min-vesum-coverage",
            "0.5",
            "--encode",
        ]
    )
    assert exit_code == 0

    manifest = EmbeddingManifest(manifest_path)
    try:
        active = manifest.active_units_for_corpus("ukrainian_wiki")
    finally:
        manifest.close()
    assert len(active) >= 1
    assert all(row.unit_key.startswith("ukrainian_wiki:") for row in active)
