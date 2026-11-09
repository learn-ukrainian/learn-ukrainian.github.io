"""verify.py catches each class of corrupted generation (design r3 §8 invariants)."""

from __future__ import annotations

import shutil
from contextlib import closing

import pytest

from scripts.lexdata import verify
from scripts.lib.readonly_sqlite import open_readonly
from tests.lexdata._support import FixtureStage, fixture_binding, mutate_sqlite

pytestmark = pytest.mark.usefixtures("local_fs")

STAGE = FixtureStage(candidates={"шуба": [("lex:a", "eligible")], "бувай": [("lex:b", "eligible"),
                                                                              ("lex:c", "unknown")]})


@pytest.fixture
def published_copy(harness, tmp_path):
    result = harness.build(stage=STAGE)
    copy = tmp_path / "copy.db"
    shutil.copyfile(result.published, copy)
    return copy


def _verify(path, binding=None):
    with closing(open_readonly(path)) as conn:
        return verify.verify_generation(conn, binding=binding or fixture_binding(), expect_status="published")


def test_clean_generation_has_no_violations(published_copy) -> None:
    report = _verify(published_copy)
    assert report.ok, report.receipt()
    assert report.counts["leaves"] == 7 and report.counts["refused_leaves"] == 1
    assert report.counts["link_status"] == {"exact": 1, "held": 1, "refused": 1, "split": 1, "unmatched": 3}
    assert "шуба" not in report.receipt_json()  # counts only, no lexical text


@pytest.mark.parametrize("sql,violation", [
    ("UPDATE l1_lex_item SET key_fold = 'шубa' WHERE raw_span = 'шуба'", "l1_accepted_key_invalid"),
    ("UPDATE l1_lex_item SET key_fold = 'стара' WHERE raw_span = 'шуба'", "l1_key_not_derived_by_bound_normalizer"),
    ("UPDATE l1_lex_item SET key_fold = 'стара' WHERE raw_span = 'шуба'", "l1_row_sha256_mismatch"),
    ("UPDATE l1_lex_item SET key_fold = 'стара' WHERE raw_span = 'шуба'", "l2_link_key_differs_from_leaf"),
    ("UPDATE l1_lex_item SET case_signal = 'mixed' WHERE raw_span = 'шуба'", "l1_key_not_derived_by_bound_normalizer"),
    ("UPDATE l1_lex_item SET rights_class = 'other' WHERE raw_span = 'шуба'", "l1_row_sha256_mismatch"),
    ("UPDATE l1_source_unit SET l1_transform_digest = '" + "0" * 64 + "'", "l1_unit_transform_digest_mismatch"),
    ("UPDATE l1_unit_input SET l0_row_fingerprint = '" + "0" * 64 + "'", "l1_unit_input_fingerprint_mismatch"),
    ("UPDATE l1_unit_disposition SET disposition = 'refused:made_up'", "l1_unit_disposition_invalid"),
    ("UPDATE l2_link SET lexeme_id = 'lex:z' WHERE status = 'unmatched'", "l2_lexeme_without_resolution"),
    ("UPDATE l2_link SET status = 'exact', lexeme_id = 'lex:b', hold_reason = NULL WHERE status = 'held'",
     "l2_exact_not_single_eligible"),
    ("UPDATE l2_link SET candidate_set_sha256 = '" + "1" * 64 + "' WHERE status = 'exact'",
     "l2_candidate_hash_mismatch"),
    ("DELETE FROM l2_candidate WHERE lexeme_id = 'lex:a'", "l2_exact_not_single_eligible"),
    ("UPDATE meta SET normalizer_digest = '" + "2" * 64 + "'", "meta_normalizer_digest_differs_from_verifier"),
    ("UPDATE meta SET input_manifest_sha256 = 'x'", "meta_input_manifest_sha256_mismatch"),
])
def test_corruption_is_detected(published_copy, sql, violation) -> None:
    mutate_sqlite(published_copy, sql)
    report = _verify(published_copy)
    assert not report.ok
    assert report.violations[violation] >= 1, report.receipt()


def test_split_needs_two_children(published_copy) -> None:
    mutate_sqlite(published_copy, "PRAGMA foreign_keys=OFF")
    mutate_sqlite(published_copy, "UPDATE l1_lex_item SET parent_item_id = NULL, member_index = NULL "
                                  "WHERE raw_span = 'у'")
    report = _verify(published_copy)
    assert report.violations["l2_split_without_two_children"] == 1
    assert report.violations["l1_row_sha256_mismatch"] == 1  # the member binding is in the row hash
