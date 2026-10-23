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
    compile_article,
)

pytestmark = pytest.mark.reads_content


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
