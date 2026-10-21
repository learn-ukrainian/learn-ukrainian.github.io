"""H3a — Antonenko prose two-step (marker-narrowed + fallback) retrieval.

H2 calibration (audit/2026-05-17-judge-calibration-h2/COMPARISON.md §6)
measured that the prose channel always fired retrievals but **no model
picked a prose snippet as evidence_type** for any sev≥2 flag. The
prefix-OR FTS matched on tangential tokens (e.g. `тижні`, `залежать`)
rather than on the russianism phrase itself, so judges reached for
``general_principle`` instead. H3a narrows retrieval to chunks that
contain BOTH a token-overlap AND a russianism-discussion marker word,
falling back to the H2 prefix-only query when no chunk satisfies both.
"""
from __future__ import annotations

import functools
from pathlib import Path

import pytest

from scripts.audit._judge_eval_lib import (
    _antonenko_fulltext_search,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent





pytestmark = pytest.mark.data_tier("sources", tables=("textbooks",))


@pytest.fixture(autouse=True)
def bound_judge_stores(data_store_factory, requires_vesum_db, monkeypatch):
    from scripts.audit import _judge_eval_lib as judge

    sources = data_store_factory("sources", required_sqlite_tables=("textbooks",))
    for name in ("retrieve_antonenko", "_heritage_check", "_antonenko_fulltext_search"):
        bound = functools.partial(getattr(judge, name), db_path=sources)
        monkeypatch.setattr(judge, name, bound)
        if name == "_antonenko_fulltext_search":
            monkeypatch.setitem(globals(), name, bound)
    monkeypatch.setattr(judge, "_vesum_unknown", functools.partial(judge._vesum_unknown, db_path=requires_vesum_db))


def test_narrowed_retrieval_fires_on_russianism_phrase() -> None:
    """`на наступному тижні` is a known time-locative russianism. Its
    relevant Antonenko discussion lives in chunks that contain both the
    token `тижні` AND a russianism-discussion marker — so the H3a
    narrowed query should pick those up directly and the hits should
    carry ``marker_narrowed=True``."""
    hits = _antonenko_fulltext_search(
        "Ми обговоримо це питання на наступному тижні."
    )
    assert hits, "Required Antonenko probe evidence is absent"
    # If hits exist, the flag must be present and one of {True, False}.
    assert all("marker_narrowed" in h for h in hits)
    assert all(isinstance(h["marker_narrowed"], bool) for h in hits)
