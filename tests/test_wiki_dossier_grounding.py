"""Tests for dossier-grounded wiki compilation prompts."""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

pytestmark = pytest.mark.reads_content

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "scripts"))


def test_load_dossier_text_returns_none_for_missing_path(tmp_path, monkeypatch):
    from wiki import sources

    monkeypatch.setattr(sources, "PROJECT_ROOT", tmp_path)

    assert sources.load_dossier_text("bio", "missing") is None


def test_load_dossier_text_returns_existing_dossier(tmp_path, monkeypatch):
    from wiki import sources

    dossier_path = tmp_path / "docs" / "research" / "bio" / "demo.md"
    dossier_path.parent.mkdir(parents=True)
    dossier_path.write_text("# Demo dossier\n\nVerified fact.\n", encoding="utf-8")
    monkeypatch.setattr(sources, "PROJECT_ROOT", tmp_path)

    assert sources.load_dossier_text("bio", "demo") == (
        "# Demo dossier\n\nVerified fact.\n"
    )


def test_extract_dossier_cited_chunk_ids_preserves_order_and_dedups():
    from wiki.compiler import _extract_dossier_cited_chunk_ids

    dossier_text = """
§4 cites ЕУ `feaa5fa7_c0619`, Чижевський wave4-chyzhevsky-istoriia-lit_c0163,
and Попович 2971c499_c0635. Duplicate feaa5fa7_c0619 stays single.
This prose mentions S1 and source_c123, but only exact cNNNN chunk IDs count.
"""

    assert _extract_dossier_cited_chunk_ids(dossier_text) == [
        "feaa5fa7_c0619",
        "wave4-chyzhevsky-istoriia-lit_c0163",
        "2971c499_c0635",
    ]


def test_seed_sources_from_dossier_fetches_only_missing_explicit_chunk_ids():
    from wiki.compiler import _seed_sources_from_dossier

    retrieved = [{"chunk_id": "feaa5fa7_c0620", "text": "Already retrieved."}]
    fetched = {
        "feaa5fa7_c0619": {"chunk_id": "feaa5fa7_c0619", "text": "ЕУ c0619"},
        "wave4-chyzhevsky-istoriia-lit_c0163": {
            "chunk_id": "wave4-chyzhevsky-istoriia-lit_c0163",
            "text": "Чижевський c0163",
        },
        "2971c499_c0635": {"chunk_id": "2971c499_c0635", "text": "Попович c0635"},
    }
    dossier_text = """
Retrieved duplicate: feaa5fa7_c0620.
Missing: feaa5fa7_c0619; wave4-chyzhevsky-istoriia-lit_c0163; 2971c499_c0635.
Unsupported prose without a chunk ID must not widen the registry.
"""

    with patch(
        "wiki.compiler._fetch_chunks_by_chunk_id",
        side_effect=lambda ids: [fetched[chunk_id] for chunk_id in ids],
    ) as fetch:
        seeded = _seed_sources_from_dossier(retrieved, dossier_text)

    fetch.assert_called_once_with([
        "feaa5fa7_c0619",
        "wave4-chyzhevsky-istoriia-lit_c0163",
        "2971c499_c0635",
    ])
    assert [source["chunk_id"] for source in seeded] == [
        "feaa5fa7_c0620",
        "feaa5fa7_c0619",
        "wave4-chyzhevsky-istoriia-lit_c0163",
        "2971c499_c0635",
    ]


def test_fetch_chunks_by_chunk_id_with_conn_reads_literary_rows_in_requested_order():
    from wiki.compiler import _fetch_chunks_by_chunk_id_with_conn

    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute(
        """
        CREATE TABLE literary_texts (
            id INTEGER PRIMARY KEY,
            chunk_id TEXT,
            title TEXT,
            text TEXT,
            source_file TEXT,
            source_url TEXT,
            author TEXT,
            work TEXT,
            work_id TEXT,
            year INTEGER,
            genre TEXT,
            language_period TEXT
        )
        """
    )
    conn.executemany(
        """
        INSERT INTO literary_texts
        (chunk_id, title, text, source_file, source_url, author, work, work_id, year, genre, language_period)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                "feaa5fa7_c0619",
                "Енциклопедія українознавства",
                "Дружинний епос не зберігся.",
                "entsyklopediia-ukrainoznavstva",
                "https://example.com/entsyklopediia-ukrainoznavstva",
                "ЕУ",
                "ЕУ",
                "eu",
                1955,
                "encyclopedia",
                "modern",
            ),
            (
                "wave4-chyzhevsky-istoriia-lit_c0163",
                "Історія української літератури",
                "Документальний ланцюг XVI-XVII ст.",
                "chyzhevsky-istoriia-lit",
                "https://example.com/chyzhevsky-istoriia-lit",
                "Дмитро Чижевський",
                "Історія української літератури",
                "chyzhevsky",
                1956,
                "monograph",
                "modern",
            ),
        ],
    )

    chunks = _fetch_chunks_by_chunk_id_with_conn(
        conn,
        [
            "wave4-chyzhevsky-istoriia-lit_c0163",
            "missing_c0001",
            "feaa5fa7_c0619",
        ],
    )

    assert [chunk["chunk_id"] for chunk in chunks] == [
        "wave4-chyzhevsky-istoriia-lit_c0163",
        "feaa5fa7_c0619",
    ]
    assert chunks[0]["source_type"] == "literary"
    assert chunks[0]["author"] == "Дмитро Чижевський"


def test_dossier_seeded_chunks_reach_assembled_sources_registry(tmp_path):
    from wiki.compiler import (
        _build_sources_registry,
        _dedup_sources_by_attribution,
        _seed_sources_from_dossier,
    )

    retrieved = [{"chunk_id": "retrieved_c0001", "text": "Already retrieved."}]
    fetched = {
        "feaa5fa7_c0619": {"chunk_id": "feaa5fa7_c0619", "text": "ЕУ c0619"},
        "wave4-chyzhevsky-istoriia-lit_c0163": {
            "chunk_id": "wave4-chyzhevsky-istoriia-lit_c0163",
            "text": "Чижевський c0163",
        },
        "2971c499_c0635": {"chunk_id": "2971c499_c0635", "text": "Попович c0635"},
    }
    dossier_text = "feaa5fa7_c0619 wave4-chyzhevsky-istoriia-lit_c0163 2971c499_c0635"
    article_path = tmp_path / "wiki" / "folk" / "bylyny.md"
    article_path.parent.mkdir(parents=True)
    article_text = "# Билини\n\nПерший факт [S1]. Другий [S2]. Третій [S3]. Четвертий [S4].\n"

    def _attr(chunk_id: str, corpus: str) -> dict[str, str]:
        return {
            "file": str(chunk_id),
            "type": "literary",
            "title": str(chunk_id),
        }

    with (
        patch(
            "wiki.compiler._fetch_chunks_by_chunk_id",
            side_effect=lambda ids: [fetched[chunk_id] for chunk_id in ids],
        ),
        patch("wiki.compiler.resolve_chunk_attribution", side_effect=_attr),
    ):
        seeded = _seed_sources_from_dossier(retrieved, dossier_text)
        deduped = _dedup_sources_by_attribution(seeded)
        registry = _build_sources_registry(article_path, deduped, article_text, force=True)

    assert registry is not None
    assert [entry.file for entry in registry.sources] == [
        "retrieved_c0001",
        "feaa5fa7_c0619",
        "wave4-chyzhevsky-istoriia-lit_c0163",
        "2971c499_c0635",
    ]


def test_cmd_compile_one_dossier_only_proceeds_when_no_discovery():
    """A slug with a dossier but no discovery file compiles dossier-only.

    New seminar topics (folk broad-scope, bio new-130) have a verified dossier
    but no discovery file. The compile must proceed grounded on the dossier
    rather than bailing at the discovery gate.
    """
    from wiki.compile import cmd_compile_one

    with (
        patch("wiki.compile._get_domain", return_value="ritual"),
        patch("wiki.compile._compiled_article_is_ready", return_value=False),
        patch(
            "wiki.compile.gather_discovery_sources",
            return_value={"error": "No discovery file for folk/demo"},
        ),
        patch(
            "wiki.compile.enrich_sources",
            return_value=[{"chunk_id": "stub", "text": "x"}],
        ) as enrich,
        patch("wiki.compile._slug_to_topic", return_value="Демо"),
        patch("wiki.compile.load_dossier_text", return_value="# Демо\n\nVerified."),
        patch("wiki.compile.compile_article", return_value=None) as compile_article,
        patch("wiki.state.is_compiled", return_value=False),
    ):
        assert cmd_compile_one("folk", "demo", dry_run=True) is True

    # The dossier-only path hands enrich_sources an empty sources_info ...
    assert enrich.call_args.args[2] == {}
    # ... and still injects the dossier as the authoritative grounding tier.
    assert compile_article.call_args.kwargs["dossier_text"] == "# Демо\n\nVerified."


def test_cmd_compile_one_fails_when_no_discovery_and_no_dossier():
    """The discovery gate still hard-fails when there is ALSO no dossier."""
    from wiki.compile import cmd_compile_one

    with (
        patch("wiki.compile._get_domain", return_value="ritual"),
        patch("wiki.compile._compiled_article_is_ready", return_value=False),
        patch(
            "wiki.compile.gather_discovery_sources",
            return_value={"error": "No discovery file for folk/ghost"},
        ),
        patch("wiki.compile.load_dossier_text", return_value=None),
        patch("wiki.compile.compile_article") as compile_article,
        patch("wiki.state.is_compiled", return_value=False),
    ):
        assert cmd_compile_one("folk", "ghost", dry_run=True) is False

    compile_article.assert_not_called()
