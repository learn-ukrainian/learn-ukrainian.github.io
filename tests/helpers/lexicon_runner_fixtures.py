"""PR1 runner slice lookup that does not rewrite sealed fixtures (#9001)."""

from __future__ import annotations

import json
from contextlib import closing
from pathlib import Path

import pytest

from scripts.lexicon.runner.generate_pr1_fixture import resolve_sources_slice
from scripts.lib.readonly_sqlite import open_readonly
from tests.helpers.sum20_store import bind_empty_sum20_store, seed_sum20_rows


def sources_slice(dest_dir: Path) -> Path:
    """Sources sqlite for runner tests.

    Builds the gitignored slice into ``dest_dir`` when the checkout does not
    already have one. Never writes under ``tests/fixtures/``.
    """
    return resolve_sources_slice(dest_dir)


@pytest.fixture(autouse=True)
def lexicon_slovnyk_offline(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Keep a runner-slice test off slovnyk.me and GRAC (#9001).

    The sealed-fixture generator sets ``LEXICON_SLOVNYK_OFFLINE`` only while it
    writes. Enrichment on the СУМ-20 slice has to set it too: a cold cache
    otherwise opens a socket, and the socket guard fails the test.
    """
    monkeypatch.setenv("LEXICON_SLOVNYK_OFFLINE", "1")
    canonical = bind_empty_sum20_store(monkeypatch, tmp_path)
    with closing(open_readonly(sources_slice(tmp_path / "canonical_inputs"))) as conn:
        documents = {lemma: json.loads(document) for lemma, document in conn.execute("SELECT lemma, document FROM slovnyk_cache")}
    seed_sum20_rows(canonical, documents)
