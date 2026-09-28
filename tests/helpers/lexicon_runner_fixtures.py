"""PR1 runner slice lookup that does not rewrite sealed fixtures (#9001)."""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.lexicon.runner.generate_pr1_fixture import resolve_sources_slice


def sources_slice(dest_dir: Path) -> Path:
    """Sources sqlite for runner tests.

    Builds the gitignored slice into ``dest_dir`` when the checkout does not
    already have one. Never writes under ``tests/fixtures/``.
    """
    return resolve_sources_slice(dest_dir)


@pytest.fixture(autouse=True)
def lexicon_slovnyk_offline(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep a runner-slice test off slovnyk.me and GRAC (#9001).

    The sealed-fixture generator sets ``LEXICON_SLOVNYK_OFFLINE`` only while it
    writes. Enrichment on the СУМ-20 slice has to set it too: a cold cache
    otherwise opens a socket, and the socket guard fails the test.
    """
    monkeypatch.setenv("LEXICON_SLOVNYK_OFFLINE", "1")
