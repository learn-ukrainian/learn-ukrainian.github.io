"""§6.7 B9 proof: a normalizer change leaves no stale key anywhere in lexdata."""

from __future__ import annotations

from contextlib import closing
from dataclasses import replace

from scripts.lexdata import build_store, generation, transforms, verify
from scripts.lexdata.normalize import NORMALIZER_VERSION
from scripts.lib.readonly_sqlite import open_readonly
from tests.lexdata import n2_normalizer
from tests.lexdata._support import FIXTURE_SOURCE, FixtureStage, fixture_binding

MINT_NFC = "м’ята"   # (i) U+2019
BYE = "Бува́й!"      # (ii)
CONTROL = "шуба"          # (iii)

N2 = replace(transforms.PRODUCTION_NORMALIZER, impl=n2_normalizer.normalize_span,
             modules=("tests/lexdata/n2_normalizer.py", "scripts/lexdata/normalize.py"))
assert N2.version == NORMALIZER_VERSION  # deliberately not bumped

STAGE = FixtureStage(
    candidates={"м'ята": [("lex:mint", "eligible"), ("lex:mint-adj", "unknown")],
                "м’ята": [("lex:mint", "eligible"), ("lex:mint-adj", "unknown")],
                "шуба": [("lex:shuba-common", "eligible"), ("lex:shuba-surname", "unknown")],
                "бувай": [("lex:bye", "eligible")]},
)

KEY_COLUMNS = {
    "l1_lex_item": ("key_stressed", "key_unstressed", "key_fold"),
    "l2_link": ("key_stressed", "key_unstressed", "key_fold"),
    "l3_card_input": ("key_stressed", "key_unstressed", "key_fold"),
}


def _leaf(conn, raw_span):
    return conn.execute("SELECT i.item_key, i.row_sha256, l.candidate_set_sha256 FROM l1_lex_item i "
                        "JOIN l2_link l USING (item_id) WHERE i.raw_span = ?", (raw_span,)).fetchone()


def _adjudication(item_key, fingerprint, target):
    return build_store.AdjudicationInput(
        item_key=item_key, target_lexeme_id=target, input_fingerprint=fingerprint,
        evidence={"note": "fixture"}, resolver_version=STAGE.resolver_version, store_fingerprints={},
        seat="fixture-reviewer", model="fixture-model", family="fixture-family", harness="pytest",
        receipt="fixture-receipt", state="admitted")


def _key_values(conn):
    values = set()
    for table, columns in KEY_COLUMNS.items():
        for column in columns:
            values |= {v for (v,) in conn.execute(f"SELECT {column} FROM {table}") if v is not None}
    for (evidence, fingerprints) in conn.execute("SELECT evidence, store_fingerprints FROM l2_adjudication"):
        values |= {evidence, fingerprints}
    return values


def test_normalizer_change_leaves_no_stale_key(harness):
    n1_binding = fixture_binding()
    n2_binding = fixture_binding(N2)

    g0 = harness.build(binding=n1_binding, stage=STAGE)
    with closing(open_readonly(g0.published)) as conn:
        mint_key, mint_row, mint_cands = _leaf(conn, MINT_NFC)
        shuba_key, shuba_row, shuba_cands = _leaf(conn, CONTROL)
    adjudications = [
        _adjudication(mint_key, verify.adjudication_input_fingerprint(mint_row, mint_cands), "lex:mint"),
        _adjudication(shuba_key, verify.adjudication_input_fingerprint(shuba_row, shuba_cands), "lex:shuba-common"),
    ]
    g1 = harness.build(binding=n1_binding, stage=STAGE, adjudications=adjudications)
    assert g1.diff["sources"][FIXTURE_SOURCE]["reused_units"] == 5
    with closing(open_readonly(g1.published)) as conn:
        g1_meta = generation.read_meta(conn)
        g1_keys = {row for row in conn.execute(
            "SELECT raw_span, key_stressed, key_unstressed, key_fold, case_signal FROM l1_lex_item "
            "WHERE refusal_code IS NULL")}
        assert conn.execute("SELECT count(*) FROM l2_adjudication WHERE state = 'admitted'").fetchone() == (2,)
        assert conn.execute("SELECT count(*) FROM l3_card_input WHERE adjudication_id IS NOT NULL").fetchone() == (2,)

    g2 = harness.build(binding=n2_binding, stage=STAGE)
    with closing(open_readonly(g2.published)) as conn:
        g2_meta = generation.read_meta(conn)
        # (a) the transform digest differs through the source hash alone.
        assert g1_meta["l1_transform_digests"][FIXTURE_SOURCE] != g2_meta["l1_transform_digests"][FIXTURE_SOURCE]
        assert g1_meta["normalizer_digest"] != g2_meta["normalizer_digest"]
        assert (g2_meta["normalizer_manifest"]["normalizer"]["version"]
                == g1_meta["normalizer_manifest"]["normalizer"]["version"])
        # (b) no unit was reused, and every re-parse says why.
        diff = g2.diff["sources"][FIXTURE_SOURCE]
        assert diff["reused_units"] == 0
        assert diff["reparse_reasons"] == {"transform_changed": 5}
        # (c) every accepted leaf equals N2 applied independently to raw_span.
        accepted = conn.execute("SELECT raw_span, key_stressed, key_unstressed, key_fold, case_signal "
                                "FROM l1_lex_item WHERE refusal_code IS NULL").fetchall()
        assert accepted
        for raw_span, *stored in accepted:
            expected = n2_normalizer.normalize_span(raw_span)
            assert stored == [expected.key_stressed, expected.key_unstressed, expected.key_fold,
                              expected.case_signal]
        # (d) no G1 key that N2 does not produce survives in any key-bearing column.
        n2_keys = {value for raw_span, *_ in accepted for value in
                   (n2_normalizer.normalize_span(raw_span).key_stressed,
                    n2_normalizer.normalize_span(raw_span).key_unstressed,
                    n2_normalizer.normalize_span(raw_span).key_fold)}
        stale = {value for row in g1_keys for value in row[1:4]} - n2_keys
        assert stale == {"м'ята"}
        assert stale.isdisjoint(_key_values(conn))
        stale_case = {(row[0], row[4]) for row in g1_keys} - {(r[0], r[4]) for r in accepted}
        assert (BYE, "initial_cap") in stale_case
        # (e) the drifted adjudication is invalidated; the control stays admitted.
        states = dict(conn.execute(
            "SELECT i.raw_span, a.state FROM l2_adjudication a JOIN l1_lex_item i ON i.item_key = a.item_key"))
        assert states == {MINT_NFC: "invalidated", CONTROL: "admitted"}
        links = {raw: (status, hold, lexeme) for raw, status, hold, lexeme in conn.execute(
            "SELECT i.raw_span, l.status, l.hold_reason, l.lexeme_id FROM l2_link l JOIN l1_lex_item i USING (item_id)")}
        assert links[MINT_NFC] == ("held", "adjudication_invalidated", None)
        assert links[CONTROL] == ("held", "unknown_competitor", "lex:shuba-common")
        assert g2.diff["adjudications"] == {"admitted": 1, "invalidated": 1}
        assert verify.verify_generation(conn, binding=n2_binding).ok

    # (f) a reader bound to N1 refuses G2 for every query; one bound to N2 opens it.
    n1_view = generation.open_generation(g2.published, binding=n1_binding)
    assert n1_view == generation.Unavailable("normalizer_mismatch", g2.generation)
    n2_view = generation.open_generation(g2.published, binding=n2_binding)
    assert isinstance(n2_view, generation.OpenGeneration)
    n2_view.close()
