"""Import probes must leave the next resolver fixture on the live module."""

import importlib
import sys

import pytest

from tests.curriculum.resolver import test_requirement_evidence_ids as evidence_tests
from tests.curriculum.resolver.evidence_helpers import receipt_sources  # noqa: F401
from tests.test_launch_reenrich_venv_preflight import (
    test_source_query_goroh_translate_importable_without_bs4 as import_probe,
)


@pytest.mark.parametrize("cached", [True, False], ids=["cached", "not-cached"])
def test_pravopys_receipt_after_no_bs4_import_probe(tmp_path, monkeypatch, cached):
    parent = importlib.import_module("scripts.rag")
    original = importlib.import_module("scripts.rag.source_query")
    # Restore the package too if the probe regresses and leaves a fresh copy.
    monkeypatch.setattr(parent, "source_query", original)
    monkeypatch.setitem(sys.modules, "scripts.rag.source_query", original)
    if not cached:
        monkeypatch.delattr(parent, "source_query")
        monkeypatch.delitem(sys.modules, "scripts.rag.source_query")

    import_probe()
    if not cached:
        assert "scripts.rag.source_query" not in sys.modules
        assert not hasattr(parent, "source_query")

    def no_network(*args, **kwargs):
        raise AssertionError("Pravopys fixture reached the live network lookup")

    live = importlib.import_module("scripts.rag.source_query")
    monkeypatch.setattr(live, "_get", no_network)
    # Reproduce the *next* test's fixture setup, after the eviction/re-import.
    evidence_tests.pravopys_fixture.__wrapped__(monkeypatch)
    evidence_tests.test_real_fixture_id_passes_record_publication_read_and_status(tmp_path, "pravopys")
    if cached:
        assert live is original
    assert parent.source_query is live
