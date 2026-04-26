"""Regression tests for the citation-shift bug (#1591).

Before the fix, ``_build_sources_registry`` deduplicated source chunks by file
attribution after ``_format_sources`` had already labeled them positionally for
the writer. Body citations were issued against the pre-dedup positions; the
registry was renumbered against the post-dedup positions; alignment broke
wherever duplicates were dropped.

These tests:
  1. demonstrate the alignment requirement
  2. exercise ``_dedup_sources_by_attribution`` directly
  3. simulate the original failure mode and assert the fix prevents it
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from wiki.compiler import (
    _build_sources_registry,
    _dedup_sources_by_attribution,
    _format_sources,
    compile_article,
)
from wiki.sources_schema import extract_short_citation_ids


def _stub_attr(file_name: str) -> dict:
    """Build the attribution dict returned for a recognized chunk."""
    return {"file": file_name, "title": "", "type": "textbook"}


@pytest.fixture
def patch_resolve_chunk_attribution():
    """Patch ``resolve_chunk_attribution`` to a deterministic in-memory map."""
    with patch("wiki.compiler.resolve_chunk_attribution") as mock:

        def _resolve(chunk_id, corpus):
            # Strip a trailing "-<digits>" so "fileA-1" and "fileA-2" resolve
            # to the same file "fileA", simulating duplicate chunks.
            base = re.sub(r"-\d+$", "", str(chunk_id))
            return _stub_attr(base)

        mock.side_effect = _resolve
        yield mock


def _make_sources(chunk_ids: list[str]) -> list[dict]:
    """Build minimal source dicts with explicit chunk_ids."""
    return [
        {"chunk_id": cid, "text": f"Source body for {cid}.", "source_type": "textbook"}
        for cid in chunk_ids
    ]


def test_dedup_collapses_chunks_from_same_file(patch_resolve_chunk_attribution):
    """Chunks resolving to the same file collapse to one entry."""
    sources = _make_sources(["fileA-1", "fileB-1", "fileA-2", "fileC-1"])
    deduped = _dedup_sources_by_attribution(sources)
    deduped_ids = [s["chunk_id"] for s in deduped]
    assert deduped_ids == ["fileA-1", "fileB-1", "fileC-1"]


def test_dedup_preserves_prompt_position_order(patch_resolve_chunk_attribution):
    """Surviving chunks keep input order, guaranteeing position alignment."""
    sources = _make_sources(["x-1", "y-1", "x-2", "z-1", "y-2", "z-2"])
    deduped = _dedup_sources_by_attribution(sources)
    assert [s["chunk_id"] for s in deduped] == ["x-1", "y-1", "z-1"]


def test_dedup_drops_chunks_without_attribution(patch_resolve_chunk_attribution):
    """Chunks resolving to an empty file_name are dropped."""

    def _resolve(chunk_id, corpus):
        if not chunk_id:
            return _stub_attr("")
        base = re.sub(r"-\d+$", "", str(chunk_id))
        return _stub_attr(base)

    patch_resolve_chunk_attribution.side_effect = _resolve
    sources = _make_sources(["fileA-1", "", "fileB-1"])
    deduped = _dedup_sources_by_attribution(sources)
    assert [s["chunk_id"] for s in deduped] == ["fileA-1", "fileB-1"]


def test_format_sources_uses_post_dedup_list(patch_resolve_chunk_attribution):
    """``_format_sources`` labels only the deduped source set."""
    sources = _make_sources(["fileA-1", "fileB-1", "fileA-2", "fileC-1"])
    deduped = _dedup_sources_by_attribution(sources)
    formatted = _format_sources(deduped)
    cite_instructions = re.findall(r"cite this source as `\[S(\d+)\]`", formatted)
    assert cite_instructions == ["1", "2", "3"]


def test_compile_article_passes_same_deduped_sources_to_prompt_and_registry(
    tmp_path,
    patch_resolve_chunk_attribution,
):
    """``compile_article`` is the entry point that must align both call sites."""
    sources = _make_sources(["fileA-1", "fileB-1", "fileA-2", "fileC-1"])
    wiki_dir = tmp_path / "wiki"

    with (
        patch("wiki.compiler.WIKI_DIR", wiki_dir),
        patch("wiki.compiler.is_compiled", return_value=False),
        patch("wiki.compiler.mark_compiled"),
        patch("wiki.compiler._build_prompt", return_value="prompt") as build_prompt,
        patch("wiki.compiler._call_writer", return_value="# Topic\n\n[S1] [S2] [S3]\n"),
        patch("wiki.compiler._write_article_bundle_atomic") as write_bundle,
    ):
        result = compile_article(
            topic="Topic",
            slug="slug",
            domain="domain",
            sources=sources,
        )

    assert result == wiki_dir / "domain" / "slug.md"
    prompt_ids = [source["chunk_id"] for source in build_prompt.call_args.kwargs["sources"]]
    registry_ids = [source["chunk_id"] for source in write_bundle.call_args.kwargs["sources"]]
    assert prompt_ids == registry_ids == ["fileA-1", "fileB-1", "fileC-1"]


def test_registry_aligned_with_body_when_input_is_prededuped(
    tmp_path,
    patch_resolve_chunk_attribution,
):
    """Prededuped input keeps body citations and registry IDs aligned."""
    sources = _make_sources(["fileA-1", "fileB-1", "fileA-2", "fileC-1"])
    deduped = _dedup_sources_by_attribution(sources)

    article_text = "# Topic\n\nSome prose [S1] and more prose [S2] and conclusion [S3].\n"
    article_path = tmp_path / "wiki" / "domain" / "slug.md"
    article_path.parent.mkdir(parents=True)

    registry = _build_sources_registry(
        article_path,
        deduped,
        article_text,
        force=True,
    )
    assert registry is not None
    registry_ids = sorted(s.id for s in registry.sources)
    cited = sorted(set(extract_short_citation_ids(article_text)))
    assert registry_ids == cited == ["S1", "S2", "S3"]


def test_old_failure_mode_reproduced_without_prededup(
    tmp_path,
    patch_resolve_chunk_attribution,
):
    """REGRESSION: bypassing upstream dedup recreates the orphan failure."""
    sources = _make_sources(["fileA-1", "fileB-1", "fileA-2", "fileC-1"])
    article_text = "# Topic\n[S1] [S2] [S3] [S4]\n"
    article_path = tmp_path / "wiki" / "domain" / "slug.md"
    article_path.parent.mkdir(parents=True)

    registry = _build_sources_registry(
        article_path,
        sources,
        article_text,
        force=True,
    )
    assert registry is not None
    registry_ids = {s.id for s in registry.sources}
    cited = set(extract_short_citation_ids(article_text))
    assert len(registry_ids) == 3
    assert "S4" in cited
    assert "S4" not in registry_ids
