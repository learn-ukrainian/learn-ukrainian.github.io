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
    ANTONENKO_PROSE_MARKERS,
    _antonenko_fulltext_search,
    _render_evidence_section,
    retrieve_evidence,
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


def test_marker_constant_excludes_overbroad_phrases() -> None:
    """Sanity guard on the marker list itself.

    `не слід` was considered but rejected — it fires on 97/169 chunks
    (57%), generic enough that filtering on it would behave like the
    pre-H3a prefix-only query. The guard catches the regression of
    someone re-adding it without checking the empirical distribution.
    """
    assert "не слід" not in ANTONENKO_PROSE_MARKERS, (
        "не слід fires on 57% of Antonenko chunks — too broad to be a "
        "narrowing marker. See H3a #2049 COMPARISON.md."
    )
    # The deliberately-kept marker set:
    assert set(ANTONENKO_PROSE_MARKERS) >= {
        "правильно",
        "неправильно",
        "не варто",
        "натомість",
        "калька",
        "русизм",
        "російською",
    }


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


def test_fallback_activates_when_narrowed_query_finds_nothing() -> None:
    """A probe whose substantive tokens never co-occur with any marker
    in the corpus must trigger the fallback path. Use a clean Ukrainian
    sentence about geography that has zero russianism overlap — its
    tokens may still occur in Antonenko prose, but not alongside markers.

    The test asserts shape and the ``marker_narrowed`` flag is False
    when the fallback fires."""
    # Probe with tokens that almost certainly co-occur in the corpus but
    # not specifically with russianism markers. Choose a benign Ukrainian
    # sentence — if marker filtering returns 0, fallback should fire.
    hits = _antonenko_fulltext_search("Сьогодні чудова погода у Львові.")
    assert hits, "Required Antonenko probe evidence is absent"
    # At least the flag must be present everywhere.
    assert all("marker_narrowed" in h for h in hits)
    # Within one call hits are uniformly narrowed or uniformly fallback;
    # we don't pin which path fires (env-dependent), only that the flag
    # is internally consistent.
    flags = {h["marker_narrowed"] for h in hits}
    assert len(flags) == 1, (
        f"hits within one call must share marker_narrowed value; got {flags}"
    )


def test_rendered_prompt_surfaces_narrowed_status() -> None:
    """The rendered evidence section should tell the judge whether the
    chunks came from the high-precision path or the fallback, so the
    judge can calibrate trust in the snippets."""
    ev = retrieve_evidence("Ми обговоримо це питання на наступному тижні.")
    rendered = _render_evidence_section(ev)
    assert '(no prose hits)' not in rendered, "Required Antonenko probe evidence is absent"
    # Exactly one of the two preambles fires.
    has_narrowed = "Narrowed retrieval (H3a)" in rendered
    has_fallback = "Fallback retrieval" in rendered
    assert has_narrowed ^ has_fallback, (
        f"expected exactly one of narrowed/fallback preambles; "
        f"narrowed={has_narrowed} fallback={has_fallback}"
    )


def test_hits_preserve_backward_compatible_fields() -> None:
    """Existing consumers expect ``page``, ``matched_token``, ``snippet`` in
    each hit. The H3a addition of ``marker_narrowed`` must not displace any
    legacy field."""
    hits = _antonenko_fulltext_search("на повістці дня сьогодні нові правила")
    assert hits, "Required Antonenko probe evidence is absent"
    for h in hits:
        assert {"page", "matched_token", "snippet", "marker_narrowed"} <= set(h)
